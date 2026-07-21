"""Evidence-bounded, three-way advisory service for the selling-point cockpit.

Deterministic code owns evidence normalization, readiness, aggregation, cache,
and publication gates. Model channels only produce independent suggestions.
"""

from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
import json
import sqlite3
import uuid

from mmn_model_governance import evidence_packet_fingerprint


EVIDENCE_CATEGORIES = (
    "market_fact",
    "user_perception",
    "competitor_performance",
    "product_capability",
    "communication_content",
)
EVIDENCE_STATUSES = frozenset({"verified", "partial", "conflict", "missing"})
REVIEW_ROLES = ("reasoning_lead", "business_editor", "evidence_auditor")
VERDICTS = frozenset({"amplify", "optimize_expression", "repair", "supplement_evidence", "hold", "manual_review"})
PUBLIC_REVIEW_LABELS = ("独立建议一", "独立建议二", "独立建议三")
REQUIRED_REVIEW_TEXT = ("summary", "rationale", "recommendedAction", "uncertainty")


def utcnow():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def init_schema(conn):
    conn.executescript(
        """
        create table if not exists selling_point_advisory_runs (
          id text primary key,
          org_id text not null,
          user_id text not null,
          context_key text not null,
          evidence_fingerprint text not null,
          status text not null,
          payload_json text not null,
          created_at text not null,
          updated_at text not null
        );
        create unique index if not exists idx_selling_point_advisory_cache
          on selling_point_advisory_runs(org_id, context_key, evidence_fingerprint);
        create index if not exists idx_selling_point_advisory_latest
          on selling_point_advisory_runs(org_id, context_key, updated_at desc);
        create table if not exists selling_point_advisory_manual_reviews (
          id text primary key,
          run_id text not null,
          org_id text not null,
          user_id text not null,
          reason text not null,
          original_json text not null,
          decision_json text not null,
          created_at text not null
        );
        """
    )
    conn.commit()


def _text(value, limit=1200):
    return str(value or "").strip()[:limit]


def _string_list(value, limit=20):
    return list(dict.fromkeys(_text(item, 400) for item in (value or []) if _text(item, 400)))[:limit]


def _normalize_evidence_item(raw, category):
    item = raw if isinstance(raw, dict) else {}
    status = _text(item.get("status"), 30).lower()
    if status not in EVIDENCE_STATUSES:
        status = "missing"
    evidence_id = _text(item.get("evidenceId") or item.get("id"), 200) or "evidence-%s" % category
    return {
        "evidenceId": evidence_id,
        "category": category,
        "fact": _text(item.get("fact")),
        "status": status,
        "impact": _text(item.get("impact")),
        "sourceRefs": _string_list(item.get("sourceRefs")),
        "timeRange": _text(item.get("timeRange"), 240),
        "sampleScope": _text(item.get("sampleScope"), 500),
        "limitations": _text(item.get("limitations"), 800),
    }


def build_locked_evidence_packet(request_context):
    request_context = request_context if isinstance(request_context, dict) else {}
    raw_packet = request_context.get("evidencePacket") if isinstance(request_context.get("evidencePacket"), dict) else {}
    raw_items = raw_packet.get("items") if isinstance(raw_packet.get("items"), list) else []
    by_category = {}
    for raw in raw_items:
        category = _text((raw or {}).get("category"), 80) if isinstance(raw, dict) else ""
        if category in EVIDENCE_CATEGORIES and category not in by_category:
            by_category[category] = raw
    items = [_normalize_evidence_item(by_category.get(category), category) for category in EVIDENCE_CATEGORIES]
    packet = {
        "edition": "global" if request_context.get("edition") == "global" else "china",
        "brand": _text(request_context.get("brand"), 160),
        "model": _text(request_context.get("model"), 160),
        "competitor": _text(request_context.get("competitor"), 160),
        "label": _text(request_context.get("label"), 160),
        "tCycle": {
            "phase": _text((request_context.get("tCycle") or {}).get("phase"), 120),
            "display": _text((request_context.get("tCycle") or {}).get("display"), 120),
        },
        "items": items,
        "conflicts": _string_list(raw_packet.get("conflicts")),
        "gaps": _string_list(raw_packet.get("gaps")),
        "windowCoverage": raw_packet.get("windowCoverage") if isinstance(raw_packet.get("windowCoverage"), (int, float)) else None,
        "updatedAt": _text(raw_packet.get("updatedAt"), 100),
    }
    packet["fingerprint"] = evidence_packet_fingerprint(packet)
    return packet


def _context_key(packet):
    fields = [packet.get("edition"), packet.get("brand"), packet.get("model"), packet.get("competitor"), packet.get("label"), (packet.get("tCycle") or {}).get("phase"), (packet.get("tCycle") or {}).get("display")]
    return evidence_packet_fingerprint(fields)


def calculate_readiness(packet):
    items = packet.get("items") or []
    verified = sum(item.get("status") == "verified" for item in items)
    conflicts = sum(item.get("status") == "conflict" for item in items)
    missing = sum(item.get("status") == "missing" for item in items)
    if verified == len(EVIDENCE_CATEGORIES) and not conflicts and not missing:
        level = "high"
    elif verified >= 4 and not conflicts and not missing:
        level = "medium"
    else:
        level = "low"
    reasons = []
    if verified < len(EVIDENCE_CATEGORIES):
        reasons.append("%d/%d类证据已验证" % (verified, len(EVIDENCE_CATEGORIES)))
    if conflicts:
        reasons.append("存在%d项来源冲突" % conflicts)
    if missing:
        names = [item["category"] for item in items if item.get("status") == "missing"]
        reasons.append("缺少%s" % "、".join(names))
    reason = "；".join(reasons) or "五类证据已验证且当前无来源冲突"
    return {
        "level": level,
        "verifiedCount": verified,
        "totalCount": len(EVIDENCE_CATEGORIES),
        "conflictCount": conflicts,
        "missingCount": missing,
        "reason": reason,
    }


def advisory_messages(packet):
    system = (
        "你是MMN卖点机会的独立建议通道。只能使用用户消息中的锁定证据包，不得修改NSR、销量、日期、样本量、T周期或竞品事实，"
        "不得读取或猜测并行通道的答案，不得把建议写成事实或Learning。只输出一个JSON对象，字段必须完整："
        "state(completed)、verdict(amplify|optimize_expression|repair|supplement_evidence|hold|manual_review)、summary、rationale、"
        "recommendedAction、uncertainty、citedEvidenceIds。每项判断必须引用输入中真实evidenceId；证据冲突或不足时应保守输出。"
        "客户可见文字不得出现模型、供应商、插件或数据服务名称。"
    )
    locked = deepcopy(packet)
    return [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(locked, ensure_ascii=False, sort_keys=True, separators=(",", ":"))}]


def _parse_review(raw):
    if isinstance(raw, dict):
        return deepcopy(raw)
    if isinstance(raw, str):
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`").removeprefix("json").strip()
        try:
            value = json.loads(text)
            return value if isinstance(value, dict) else {}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {}
    return {}


def normalize_review(raw, allowed_evidence_ids, fingerprint):
    item = _parse_review(raw)
    verdict = _text(item.get("verdict"), 80).lower()
    citations = _string_list(item.get("citedEvidenceIds"))
    allowed = set(allowed_evidence_ids)
    valid = (
        _text(item.get("state"), 30).lower() == "completed"
        and verdict in VERDICTS
        and all(_text(item.get(field)) for field in REQUIRED_REVIEW_TEXT)
        and bool(citations)
        and set(citations).issubset(allowed)
    )
    if not valid:
        raise ValueError("建议结果未通过结构或证据引用校验")
    return {
        "state": "completed",
        "verdict": verdict,
        "summary": _text(item.get("summary"), 500),
        "rationale": _text(item.get("rationale"), 900),
        "recommendedAction": _text(item.get("recommendedAction"), 600),
        "uncertainty": _text(item.get("uncertainty"), 600),
        "citedEvidenceIds": citations,
        "evidenceFingerprint": fingerprint,
    }


def _public_error(error):
    text = _text(error, 300)
    for forbidden in ("qwen", "deepseek", "kimi", "openai", "dashscope", "moonshot"):
        text = text.replace(forbidden, "建议通道").replace(forbidden.upper(), "建议通道")
    return text or "建议通道未完成"


def aggregate_reviews(reviews_by_role, errors_by_role, packet, readiness):
    ordered = [reviews_by_role[role] for role in REVIEW_ROLES if role in reviews_by_role]
    if errors_by_role or len(ordered) != len(REVIEW_ROLES):
        status = "degraded"
        alignment = "degraded"
    elif readiness["level"] == "low":
        status = "insufficient_evidence"
        alignment = "insufficient"
    else:
        verdict_counts = Counter(item["verdict"] for item in ordered)
        evidence_sets = [set(item["citedEvidenceIds"]) for item in ordered]
        common_ids = sorted(set.intersection(*evidence_sets)) if evidence_sets else []
        all_same = len(verdict_counts) == 1
        if all_same and common_ids:
            status, alignment = "aligned", "aligned"
        elif common_ids and max(verdict_counts.values(), default=0) >= 2:
            status, alignment = "partially_aligned", "partial"
        else:
            status, alignment = "manual_required", "divergent"
    evidence_sets = [set(item["citedEvidenceIds"]) for item in ordered]
    common_ids = sorted(set.intersection(*evidence_sets)) if len(evidence_sets) == len(REVIEW_ROLES) else []
    verdicts = list(dict.fromkeys(item["verdict"] for item in ordered))
    common_judgment = ordered[0]["summary"] if status == "aligned" and ordered else ("三路均不支持在当前证据条件下直接放大" if ordered and all(item["verdict"] in {"repair", "supplement_evidence", "hold", "manual_review", "optimize_expression"} for item in ordered) else "尚未形成可发布共同判断")
    disagreements = [] if len(verdicts) <= 1 else ["建议方向存在分歧：%s" % "、".join(verdicts)]
    if errors_by_role:
        disagreements.append("%d路建议未完成" % len(errors_by_role))
    recommendation = ordered[0]["recommendedAction"] if status == "aligned" and ordered else ("请先补齐或裁决关键证据，再决定营销动作" if readiness["level"] == "low" else "请查看分歧并由管理者确认下一步")
    next_action = "带入营销动作" if status == "aligned" else ("创建补证任务" if status == "insufficient_evidence" else "重试失败通道" if status == "degraded" else "进入人工裁决")
    can_enter = status == "aligned" and readiness["level"] in {"high", "medium"} and ordered[0]["verdict"] in {"amplify", "optimize_expression"}
    return status, {
        "alignment": alignment,
        "commonJudgment": common_judgment,
        "disagreements": disagreements,
        "recommendation": recommendation,
        "nextAction": next_action,
        "citedEvidenceIds": common_ids,
    }, can_enter


def _load_payload(row, cached=False):
    if row is None:
        return None
    payload = json.loads(row["payload_json"] or "{}")
    payload["status"] = row["status"]
    payload["cached"] = bool(cached)
    return payload


def get_run(conn, run_id, org_id):
    row = conn.execute("select * from selling_point_advisory_runs where id=? and org_id=?", (str(run_id), str(org_id))).fetchone()
    return _load_payload(row)


def latest_run(conn, request_context, org_id):
    packet = build_locked_evidence_packet(request_context)
    expected_fingerprint = _text((request_context or {}).get("evidenceFingerprint"), 128) or packet["fingerprint"]
    row = conn.execute(
        "select * from selling_point_advisory_runs where org_id=? and context_key=? order by updated_at desc limit 1",
        (str(org_id), _context_key(packet)),
    ).fetchone()
    payload = _load_payload(row, cached=True)
    if payload and payload.get("evidenceFingerprint") != expected_fingerprint:
        payload["status"] = "stale"
        payload["canEnterMarketingAction"] = False
    return payload


def run_advisory(conn, request_context, *, org_id, user_id, role_runner, force=False):
    init_schema(conn)
    packet = build_locked_evidence_packet(request_context)
    context_key = _context_key(packet)
    existing_row = conn.execute(
        "select * from selling_point_advisory_runs where org_id=? and context_key=? and evidence_fingerprint=? limit 1",
        (str(org_id), context_key, packet["fingerprint"]),
    ).fetchone()
    existing_payload = _load_payload(existing_row) if existing_row else None
    if existing_row and existing_row["status"] != "stale" and not force:
        return _load_payload(existing_row, cached=True)
    now = utcnow()
    old_rows = conn.execute(
        "select id, payload_json from selling_point_advisory_runs where org_id=? and context_key=? and evidence_fingerprint<>? and status<>'stale'",
        (str(org_id), context_key, packet["fingerprint"]),
    ).fetchall()
    for old in old_rows:
        old_payload = json.loads(old["payload_json"] or "{}")
        old_payload["status"] = "stale"
        old_payload["canEnterMarketingAction"] = False
        conn.execute("update selling_point_advisory_runs set status='stale', payload_json=?, updated_at=? where id=?", (json.dumps(old_payload, ensure_ascii=False), now, old["id"]))
    messages = advisory_messages(packet)
    allowed_ids = [item["evidenceId"] for item in packet["items"]]

    def run_one(role):
        raw = role_runner(role, deepcopy(messages))
        return normalize_review(raw, allowed_ids, packet["fingerprint"])

    reviews_by_role, errors_by_role = {}, {}
    if existing_payload and existing_row["status"] == "degraded":
        for review in existing_payload.get("reviews") or []:
            try:
                role = REVIEW_ROLES[int(review.get("reviewId")) - 1]
            except (TypeError, ValueError, IndexError):
                continue
            reviews_by_role[role] = {key: deepcopy(value) for key, value in review.items() if key not in {"reviewId", "label"}}
    roles_to_run = [role for role in REVIEW_ROLES if role not in reviews_by_role]
    if force and existing_row and existing_row["status"] != "stale" and not roles_to_run:
        return _load_payload(existing_row, cached=True)
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {role: executor.submit(run_one, role) for role in roles_to_run}
        for role, future in futures.items():
            try:
                reviews_by_role[role] = future.result()
            except Exception as exc:
                errors_by_role[role] = _public_error(exc)
    readiness = calculate_readiness(packet)
    status, synthesis, can_enter = aggregate_reviews(reviews_by_role, errors_by_role, packet, readiness)
    reviews = []
    channel_errors = []
    for index, role in enumerate(REVIEW_ROLES):
        if role in reviews_by_role:
            reviews.append({"reviewId": str(index + 1), "label": PUBLIC_REVIEW_LABELS[index], **reviews_by_role[role]})
        else:
            channel_errors.append({"reviewId": str(index + 1), "label": PUBLIC_REVIEW_LABELS[index], "state": "failed", "error": errors_by_role.get(role, "建议通道未完成")})
    run_id = existing_row["id"] if existing_row else uuid.uuid4().hex
    payload = {
        "runId": run_id,
        "status": status,
        "evidenceFingerprint": packet["fingerprint"],
        "evidencePacket": packet,
        "reviews": reviews,
        "channelErrors": channel_errors,
        "completedCount": len(reviews),
        "synthesis": synthesis,
        "readiness": readiness,
        "canEnterMarketingAction": can_enter,
        "cached": False,
        "updatedAt": now,
    }
    if existing_row:
        conn.execute(
            "update selling_point_advisory_runs set user_id=?, status=?, payload_json=?, updated_at=? where id=? and org_id=?",
            (str(user_id), status, json.dumps(payload, ensure_ascii=False), now, run_id, str(org_id)),
        )
    else:
        conn.execute(
            "insert into selling_point_advisory_runs(id,org_id,user_id,context_key,evidence_fingerprint,status,payload_json,created_at,updated_at) values(?,?,?,?,?,?,?,?,?)",
            (run_id, str(org_id), str(user_id), context_key, packet["fingerprint"], status, json.dumps(payload, ensure_ascii=False), now, now),
        )
    conn.commit()
    return payload


def record_manual_review(conn, run_id, *, org_id, user_id, reason, decision):
    current = get_run(conn, run_id, org_id)
    if not current:
        raise ValueError("未找到当前组织的卖点建议记录")
    reason = _text(reason, 1000)
    decision = decision if isinstance(decision, dict) else {}
    if not reason or not decision:
        raise ValueError("人工裁决必须填写原因和裁决结果")
    now = utcnow()
    audit = {
        "operator": _text(user_id, 200),
        "reviewedAt": now,
        "reason": reason,
        "originalStatus": current.get("status"),
        "originalSynthesis": current.get("synthesis"),
        "decision": deepcopy(decision),
    }
    updated = deepcopy(current)
    updated["manualReview"] = audit
    updated["status"] = "manual_required" if decision.get("verdict") == "manual_review" else current.get("status")
    updated["canEnterMarketingAction"] = bool(decision.get("canEnterMarketingAction") is True and current.get("readiness", {}).get("level") != "low")
    updated["updatedAt"] = now
    conn.execute(
        "insert into selling_point_advisory_manual_reviews(id,run_id,org_id,user_id,reason,original_json,decision_json,created_at) values(?,?,?,?,?,?,?,?)",
        (uuid.uuid4().hex, str(run_id), str(org_id), str(user_id), reason, json.dumps(current, ensure_ascii=False), json.dumps(decision, ensure_ascii=False), now),
    )
    conn.execute(
        "update selling_point_advisory_runs set status=?, payload_json=?, updated_at=? where id=? and org_id=?",
        (updated["status"], json.dumps(updated, ensure_ascii=False), now, str(run_id), str(org_id)),
    )
    conn.commit()
    return updated
