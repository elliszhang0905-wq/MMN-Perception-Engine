"""Evidence-gated content defense for the Douyin ranking dashboard.

This module is provider-agnostic. Acquisition adapters may contribute evidence,
but only the three independent MMN strategy reviews can publish a defense card.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import uuid
from datetime import datetime, timezone

from opportunity_pipeline import UNIFIED_LABELS


PROVIDERS = ("qwen", "deepseek", "kimi")
EVIDENCE_TYPES = {"V", "C", "N", "W", "L"}
PUBLISHABLE_JUDGMENTS = {"strong_defense", "weak_defense"}
STRONG_LABEL = "强势属性防线"
WEAK_LABEL = "弱势属性防线"
OBSERVATION_LABEL = "观察与补证"


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _text(value, limit=1600):
    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def public_failure_reason(value):
    """Keep acquisition failures useful without exposing implementation vendors."""
    text = _text(value, 500)
    if "AllocationQuota.FreeTierOnly" in text:
        return (
            "当前分析能力的可用额度已耗尽，且仅允许使用免费额度；"
            "请联系管理员补充额度或调整额度策略后重试。"
        )
    return re.sub(
        (
            r"(?i)(?:"
            r"qwen(?:[/_-]?[a-z0-9.]+)*|"
            r"deepseek(?:[/_-]?[a-z0-9.]+)*|"
            r"kimi(?:[/_-]?[a-z0-9.]+)*|"
            r"tikhub|playwright|dashscope|provider|通义千问|千问|百炼"
            r")"
        ),
        "证据能力",
        text,
    )


def _number(value, default=0.0):
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default


def _json(value, fallback):
    try:
        parsed = json.loads(value) if isinstance(value, str) else value
    except (TypeError, ValueError, json.JSONDecodeError):
        parsed = fallback
    return parsed


def init_schema(conn):
    conn.executescript("""
    create table if not exists douyin_content_defense_jobs (
      id text primary key,
      org_id text not null,
      edition text not null,
      view_key text not null,
      range_key text not null,
      item_id text not null,
      item_fingerprint text not null,
      request_json text not null default '{}',
      status text not null,
      stage text not null,
      progress integer not null default 0,
      message text not null default '',
      error text not null default '',
      result_json text not null default '{}',
      created_at text not null,
      updated_at text not null,
      completed_at text,
      unique(org_id, edition, item_id, item_fingerprint)
    );
    create index if not exists idx_douyin_content_defense_scope
      on douyin_content_defense_jobs(org_id, edition, view_key, range_key, updated_at desc);
    create table if not exists douyin_content_defense_cache (
      cache_key text primary key,
      content_id text not null,
      media_fingerprint text not null,
      evidence_json text not null default '[]',
      diagnostics_json text not null default '{}',
      created_at text not null,
      updated_at text not null
    );
    """)


def content_fingerprint(item):
    stable = {
        "itemId": _text(item.get("itemId") or item.get("id"), 160),
        "title": _text(item.get("title")),
        "sourceUrl": _text(item.get("sourceUrl"), 1200),
        "playCount": _number(item.get("playCount")),
        "commentCount": _number(item.get("commentCount")),
        "shareCount": _number(item.get("shareCount")),
        "collectCount": _number(item.get("collectCount")),
    }
    return hashlib.sha256(json.dumps(stable, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def media_fingerprint(item):
    value = "|".join((
        _text(item.get("itemId") or item.get("id"), 160),
        _text(item.get("sourceUrl"), 1200),
        _text(item.get("coverUrl"), 1200),
        str(int(_number(item.get("duration")))),
    ))
    return hashlib.sha256(value.encode()).hexdigest()


def evidence_id(kind, content_id, subtype, payload, timestamp_ms=None):
    digest = hashlib.sha1(
        json.dumps([kind, content_id, subtype, payload, timestamp_ms], ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()[:16]
    return f"{kind}:{digest}"


def normalize_evidence(kind, *, content_id, source_url="", subtype="", quote="", status="available",
                       fetched_at="", timestamp_ms=None, fingerprint="", payload=None, failure_reason=""):
    if kind not in EVIDENCE_TYPES:
        raise ValueError("未知内容防线证据类型。")
    status = status if status in {"available", "unavailable", "failed"} else "failed"
    normalized_payload = payload if isinstance(payload, dict) else {}
    item = {
        "type": kind,
        "contentId": _text(content_id, 160),
        "sourceUrl": _text(source_url, 1200),
        "fetchedAt": _text(fetched_at, 80) or utcnow(),
        "timestampMs": int(timestamp_ms) if isinstance(timestamp_ms, (int, float)) and timestamp_ms >= 0 else None,
        "mediaFingerprint": _text(fingerprint, 128),
        "subtype": _text(subtype, 80),
        "quote": _text(quote, 2400),
        "status": status,
        "failureReason": public_failure_reason(failure_reason),
        "payload": normalized_payload,
    }
    item["evidenceId"] = evidence_id(kind, item["contentId"], item["subtype"], item["quote"] or item["payload"], item["timestampMs"])
    return item


def normalize_media_evidence(item, raw_evidence, errors=None, fetched_at=""):
    """Convert existing creator-media output to V evidence with explicit failure rows."""
    content_id = _text(item.get("itemId") or item.get("id"), 160)
    source_url = _text(item.get("sourceUrl"), 1200)
    fingerprint = media_fingerprint(item)
    output = [normalize_evidence(
        "V", content_id=content_id, source_url=source_url, subtype="ranking_title",
        quote=item.get("title"), fetched_at=fetched_at, fingerprint=fingerprint,
        payload={"rank": item.get("rank"), "metrics": {key: item.get(key) for key in (
            "playCount", "likeCount", "commentCount", "shareCount", "collectCount")}},
    )]
    subtype_map = {
        "transcript": "transcript", "subtitle": "transcript", "ocr": "ocr",
        "visual_summary": "visual_summary", "visual_structure": "visual_structure", "shot": "key_shot",
    }
    for raw in raw_evidence or []:
        if not isinstance(raw, dict):
            continue
        subtype = subtype_map.get(str(raw.get("evidence_type") or "").lower())
        if not subtype:
            continue
        provenance = raw.get("provenance") if isinstance(raw.get("provenance"), dict) else {}
        output.append(normalize_evidence(
            "V", content_id=content_id, source_url=source_url, subtype=subtype,
            quote=raw.get("quote_text"), fetched_at=provenance.get("fetchTime") or fetched_at,
            timestamp_ms=raw.get("start_ms"), fingerprint=fingerprint,
            payload={"confidence": _number(raw.get("confidence")), "availability": provenance.get("availability")},
        ))
    for error in errors or []:
        lowered = str(error).lower()
        subtype = "ocr" if "ocr" in lowered else "transcript" if "转写" in str(error) else "visual"
        output.append(normalize_evidence(
            "V", content_id=content_id, source_url=source_url, subtype=subtype,
            status="failed", fetched_at=fetched_at, fingerprint=fingerprint, failure_reason=error,
        ))
    if len(output) == 1:
        output.append(normalize_evidence(
            "V", content_id=content_id, source_url=source_url, subtype="media_body",
            status="unavailable", fetched_at=fetched_at, fingerprint=fingerprint,
            failure_reason="视频本体、字幕、OCR与关键镜头均未取得；系统仅读取了榜单标题和指标。",
        ))
    return output


def normalize_comment_evidence(item, comments, fetched_at=""):
    content_id = _text(item.get("itemId") or item.get("id"), 160)
    output = []
    for index, comment in enumerate(comments or []):
        row = comment if isinstance(comment, dict) else {"text": comment}
        quote = _text(row.get("text") or row.get("content"), 1000)
        if not quote:
            continue
        output.append(normalize_evidence(
            "C", content_id=content_id, source_url=item.get("sourceUrl"), subtype="comment",
            quote=quote, fetched_at=row.get("fetchedAt") or fetched_at,
            payload={"commentId": _text(row.get("commentId") or row.get("id") or index, 160),
                     "likes": _number(row.get("likeCount") or row.get("likes")),
                     "sentiment": _text(row.get("sentiment"), 40)},
        ))
    if not output:
        output.append(normalize_evidence(
            "C", content_id=content_id, source_url=item.get("sourceUrl"), subtype="comments",
            status="unavailable", fetched_at=fetched_at,
            failure_reason="当前榜单项未取得可追溯评论样本，不能形成评论舆情结论。",
        ))
    return output


def normalize_nsr_evidence(item, rows, model):
    content_id = _text(item.get("itemId") or item.get("id"), 160)
    output = []
    for row in rows or []:
        if not isinstance(row, dict) or _text(row.get("model"), 160) != _text(model, 160):
            continue
        attribute = _text(row.get("attribute") or row.get("label"), 80)
        if attribute not in UNIFIED_LABELS:
            continue
        own = _number(row.get("nsr"), None)
        delta = _number(row.get("competitorDelta"), None)
        if own is None or delta is None:
            continue
        output.append(normalize_evidence(
            "N", content_id=content_id, subtype="attribute_nsr", quote=f"{attribute} NSR {own:.3f}，竞品差值 {delta:+.3f}",
            payload={"model": model, "attribute": attribute, "nsr": own, "competitorDelta": delta,
                     "volume": _number(row.get("volume")), "source": _text(row.get("source"), 160)},
        ))
    return output


def normalize_whitepaper_evidence(item, whitepaper, model):
    content_id = _text(item.get("itemId") or item.get("id"), 160)
    capabilities = whitepaper.get("capabilities") or [] if isinstance(whitepaper, dict) else []
    output = []
    for capability in capabilities:
        if not isinstance(capability, dict):
            continue
        attribute = _text(capability.get("label"), 80)
        quote = _text(capability.get("quote"), 1200)
        try:
            page = int(capability.get("page"))
        except (TypeError, ValueError):
            continue
        if attribute not in UNIFIED_LABELS or not quote or page <= 0:
            continue
        output.append(normalize_evidence(
            "W", content_id=content_id, subtype="product_fact", quote=quote,
            payload={"model": model, "attribute": attribute, "page": page,
                     "claim": _text(capability.get("claim"), 500), "filename": _text(whitepaper.get("filename"), 300)},
        ))
    return output


def normalize_lead_evidence(item, leads):
    content_id = _text(item.get("itemId") or item.get("id"), 160)
    output = []
    for row in leads or []:
        if not isinstance(row, dict) or _text(row.get("contentId"), 160) != content_id:
            continue
        traceable = bool(row.get("exposureId") and row.get("attribute") and row.get("leadAction"))
        output.append(normalize_evidence(
            "L", content_id=content_id, subtype="lead_validation",
            quote=_text(row.get("summary") or row.get("leadAction"), 500),
            status="available" if traceable else "unavailable",
            failure_reason="缺少内容曝光、属性标签与线索行为的可追踪关联，不能用于因果判断。" if not traceable else "",
            payload={"traceableAssociation": traceable, "exposureId": row.get("exposureId"),
                     "attribute": row.get("attribute"), "leadAction": row.get("leadAction")},
        ))
    if not output:
        output.append(normalize_evidence(
            "L", content_id=content_id, subtype="lead_validation", status="unavailable",
            failure_reason="当前没有内容曝光、属性标签与线索行为的可追踪关联；线索不参与因果判断。",
        ))
    return output


def build_evidence_package(item, *, media=None, media_errors=None, comments=None, nsr_rows=None,
                           whitepaper=None, leads=None, model="奥迪E7X", fetched_at=""):
    evidence = []
    evidence.extend(normalize_media_evidence(item, media or [], media_errors or [], fetched_at))
    evidence.extend(normalize_comment_evidence(item, comments or [], fetched_at))
    evidence.extend(normalize_nsr_evidence(item, nsr_rows or [], model))
    evidence.extend(normalize_whitepaper_evidence(item, whitepaper or {}, model))
    evidence.extend(normalize_lead_evidence(item, leads or []))
    by_id = {row["evidenceId"]: row for row in evidence}
    return {
        "contentId": _text(item.get("itemId") or item.get("id"), 160),
        "sourceUrl": _text(item.get("sourceUrl"), 1200),
        "title": _text(item.get("title")),
        "model": _text(model, 160),
        "mediaFingerprint": media_fingerprint(item),
        "capturedAt": _text(fetched_at, 80) or utcnow(),
        "ranking": {key: item.get(key) for key in ("rank", "playCount", "likeCount", "commentCount", "shareCount", "collectCount")},
        "evidence": list(by_id.values()),
    }


def strategy_messages(package):
    available = [row for row in package.get("evidence") or [] if row.get("status") == "available"]
    system = (
        "你是MMN内容防线独立策略质检员。只能依据同一证据包判断热点内容、车型真实属性NSR与白皮书事实的关系；"
        "不得用常识补齐，不得把热度、评论NSR或时间相关性写成需求、销量或线索因果。"
        "只返回JSON对象：attribute、judgementType(strong_defense|weak_defense|observation)、hotClaim、contentProposition、"
        "titleStructure、requiredProof(string数组)、commentChallenges(string数组)、forbiddenClaims(string数组)、"
        "kpis(string数组)、evidenceIds(string数组)、confidence(0-1)、reason。"
        "强势属性必须同时引用V/N/W证据且N竞品差值为正；弱势属性不得伪装为强势；缺证据只能observation。"
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": json.dumps({
        "contentId": package.get("contentId"), "title": package.get("title"), "model": package.get("model"),
        "ranking": package.get("ranking"), "evidence": available,
    }, ensure_ascii=False)}]


def normalize_review(value, evidence_by_id):
    value = _json(value, {})
    value = value if isinstance(value, dict) else {}
    judgement = _text(value.get("judgementType"), 40)
    if judgement not in PUBLISHABLE_JUDGMENTS | {"observation"}:
        judgement = "observation"
    evidence_ids = sorted({str(row) for row in value.get("evidenceIds") or [] if str(row) in evidence_by_id})
    return {
        "attribute": _text(value.get("attribute"), 80),
        "judgementType": judgement,
        "hotClaim": _text(value.get("hotClaim"), 500),
        "contentProposition": _text(value.get("contentProposition"), 500),
        "titleStructure": _text(value.get("titleStructure"), 500),
        "requiredProof": [_text(row, 500) for row in value.get("requiredProof") or [] if _text(row, 500)][:8],
        "commentChallenges": [_text(row, 500) for row in value.get("commentChallenges") or [] if _text(row, 500)][:8],
        "forbiddenClaims": [_text(row, 500) for row in value.get("forbiddenClaims") or [] if _text(row, 500)][:8],
        "kpis": [_text(row, 200) for row in value.get("kpis") or [] if _text(row, 200)][:8],
        "evidenceIds": evidence_ids,
        "confidence": max(0.0, min(1.0, _number(value.get("confidence")))),
        "reason": _text(value.get("reason"), 800),
    }


def cross_validate_reviews(package, reviews, errors=None):
    evidence_by_id = {row["evidenceId"]: row for row in package.get("evidence") or []}
    normalized = {provider: normalize_review((reviews or {}).get(provider), evidence_by_id) for provider in PROVIDERS if provider in (reviews or {})}
    errors = {key: _text(value, 500) for key, value in (errors or {}).items() if value}
    reasons = []
    if errors or set(normalized) != set(PROVIDERS):
        reasons.append("三重交叉质检未完整返回")
    attributes = {row.get("attribute") for row in normalized.values() if row.get("attribute")}
    judgements = {row.get("judgementType") for row in normalized.values()}
    if len(attributes) != 1 or next(iter(attributes), "") not in UNIFIED_LABELS:
        reasons.append("三重质检未共同确认同一NSR属性")
    if len(judgements) != 1:
        reasons.append("三重质检对防线类型存在分歧")
    confidence = min((row.get("confidence", 0) for row in normalized.values()), default=0)
    if confidence < .7:
        reasons.append("三重质检最低置信度不足0.7")
    common_ids = set(evidence_by_id)
    for row in normalized.values():
        common_ids &= set(row.get("evidenceIds") or [])
    common_available = {key for key in common_ids if evidence_by_id[key].get("status") == "available"}
    common_types = {evidence_by_id[key].get("type") for key in common_available}
    judgement = next(iter(judgements), "observation") if len(judgements) == 1 else "observation"
    attribute = next(iter(attributes), "") if len(attributes) == 1 else ""
    attribute_ids = {key for key in common_available if (evidence_by_id[key].get("payload") or {}).get("attribute") == attribute or evidence_by_id[key].get("type") in {"V", "C", "L"}}
    attribute_types = {evidence_by_id[key].get("type") for key in attribute_ids}
    required = {"V", "N", "W"}
    if not required.issubset(attribute_types):
        reasons.append("共同证据未同时覆盖真实视频、属性NSR与白皮书事实")
    real_video_ids = {key for key in attribute_ids if evidence_by_id[key].get("type") == "V" and
                      evidence_by_id[key].get("subtype") in {
                          "transcript", "ocr", "visual_summary", "visual_structure", "key_shot"}}
    if not real_video_ids:
        reasons.append("仅有榜单标题或视频不可读，缺少真实视频本体证据")
    nsr_rows = [evidence_by_id[key] for key in attribute_ids if evidence_by_id[key].get("type") == "N"]
    deltas = [_number((row.get("payload") or {}).get("competitorDelta"), None) for row in nsr_rows]
    deltas = [value for value in deltas if value is not None]
    if judgement == "strong_defense" and (not deltas or max(deltas) <= 0):
        reasons.append("弱势或缺少竞品差值的属性不能发布为强势防线")
    if judgement == "weak_defense" and deltas and min(deltas) >= 0:
        reasons.append("非弱势属性不能发布为弱势防线")
    status = "published" if not reasons and judgement in PUBLISHABLE_JUDGMENTS else "manual_required"
    seed = next(iter(normalized.values()), {})
    card = None
    if status == "published":
        nsr = nsr_rows[0].get("payload") or {}
        card = {
            "contentId": package.get("contentId"), "hotClaim": seed.get("hotClaim") or package.get("title"),
            "attribute": attribute, "attributeNsr": nsr.get("nsr"), "competitorDelta": nsr.get("competitorDelta"),
            "jointEvidenceIds": sorted(attribute_ids), "judgementType": judgement,
            "judgementLabel": STRONG_LABEL if judgement == "strong_defense" else WEAK_LABEL,
            "contentProposition": seed.get("contentProposition"), "titleStructure": seed.get("titleStructure"),
            "requiredProof": seed.get("requiredProof"), "commentChallenges": seed.get("commentChallenges"),
            "forbiddenClaims": seed.get("forbiddenClaims"), "kpis": seed.get("kpis"),
            "qualityStatus": "三重交叉质检通过", "disagreements": [],
            "causalBoundary": "热度、评论NSR与时间相关性不等于市场需求、销量或线索因果；线索仅用于可追踪结果校验。",
        }
    quality_checks = [
        {"check": index + 1, "status": "completed", "attribute": row.get("attribute"),
         "judgementType": row.get("judgementType"), "confidence": row.get("confidence"),
         "evidenceIds": row.get("evidenceIds")}
        for index, row in enumerate(normalized.values())
    ]
    return {
        "status": status, "outputLabel": "MMN多模态策略输出", "qualityLabel": "三重交叉质检",
        "providersComplete": set(normalized) == set(PROVIDERS) and not errors,
        "qualityChecks": quality_checks, "failedCheckCount": len(errors), "commonEvidenceIds": sorted(common_available),
        "commonEvidenceTypes": sorted(common_types), "reasons": list(dict.fromkeys(reasons)), "card": card,
        "fallback": None if card else {"judgementLabel": OBSERVATION_LABEL, "recommendation": "保留观察并补齐共同V/N/W证据后再发布内容防线。"},
    }


def create_job(conn, *, org_id, edition, view, range_key, item, request=None, force=False):
    init_schema(conn)
    fingerprint = content_fingerprint(item)
    existing = conn.execute("""
      select * from douyin_content_defense_jobs
      where org_id=? and edition=? and item_id=? and item_fingerprint=?
    """, (org_id, edition, _text(item.get("itemId") or item.get("id"), 160), fingerprint)).fetchone()
    if existing and not force:
        return job_payload(existing), False
    job_id = existing["id"] if existing else uuid.uuid4().hex
    stamp = utcnow()
    values = (job_id, org_id, edition, view, range_key, _text(item.get("itemId") or item.get("id"), 160), fingerprint,
              json.dumps({**(request or {}), "item": item}, ensure_ascii=False), "queued", "queued", 0,
              "已进入内容证据整理队列", "", "{}", stamp, stamp, None)
    conn.execute("""
      insert into douyin_content_defense_jobs
      (id,org_id,edition,view_key,range_key,item_id,item_fingerprint,request_json,status,stage,progress,message,error,result_json,created_at,updated_at,completed_at)
      values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
      on conflict(id) do update set request_json=excluded.request_json,status='queued',stage='queued',progress=0,
        message=excluded.message,error='',result_json='{}',updated_at=excluded.updated_at,completed_at=null
    """, values)
    conn.commit()
    return get_job(conn, job_id, org_id), True


def update_job(conn, job_id, *, status=None, stage=None, progress=None, message=None, error=None, result=None):
    current = conn.execute("select * from douyin_content_defense_jobs where id=?", (job_id,)).fetchone()
    if not current:
        raise ValueError("内容防线任务不存在。")
    final_status = status or current["status"]
    stamp = utcnow()
    conn.execute("""
      update douyin_content_defense_jobs set status=?,stage=?,progress=?,message=?,error=?,result_json=?,updated_at=?,completed_at=? where id=?
    """, (final_status, stage or current["stage"], int(progress if progress is not None else current["progress"]),
          message if message is not None else current["message"], error if error is not None else current["error"],
          json.dumps(result, ensure_ascii=False) if result is not None else current["result_json"], stamp,
          stamp if final_status in {"completed", "failed", "manual_required"} else current["completed_at"], job_id))
    conn.commit()
    return get_job(conn, job_id)


def job_payload(row):
    if not row:
        return None
    return {
        "jobId": row["id"], "status": row["status"], "stage": row["stage"], "progress": row["progress"],
        "message": row["message"], "error": row["error"], "itemId": row["item_id"],
        "view": row["view_key"], "range": row["range_key"], "result": _json(row["result_json"], {}),
        "createdAt": row["created_at"], "updatedAt": row["updated_at"], "completedAt": row["completed_at"],
    }


def get_job(conn, job_id, org_id=None):
    init_schema(conn)
    sql, params = "select * from douyin_content_defense_jobs where id=?", [job_id]
    if org_id:
        sql, params = sql + " and org_id=?", [job_id, org_id]
    return job_payload(conn.execute(sql, params).fetchone())


def list_jobs(conn, *, org_id, edition, view, range_key):
    init_schema(conn)
    rows = conn.execute("""
      select * from douyin_content_defense_jobs where org_id=? and edition=? and view_key=? and range_key=?
      order by updated_at desc
    """, (org_id, edition, view, range_key)).fetchall()
    return [job_payload(row) for row in rows]


def cache_key(item):
    return hashlib.sha256(f"content-defense-v1|{media_fingerprint(item)}".encode()).hexdigest()


def load_media_cache(conn, item):
    init_schema(conn)
    row = conn.execute("select * from douyin_content_defense_cache where cache_key=?", (cache_key(item),)).fetchone()
    if not row:
        return None
    return {"evidence": _json(row["evidence_json"], []), "diagnostics": _json(row["diagnostics_json"], {}), "cacheHit": True}


def save_media_cache(conn, item, evidence, diagnostics):
    init_schema(conn)
    stamp = utcnow()
    conn.execute("""
      insert into douyin_content_defense_cache(cache_key,content_id,media_fingerprint,evidence_json,diagnostics_json,created_at,updated_at)
      values(?,?,?,?,?,?,?) on conflict(cache_key) do update set evidence_json=excluded.evidence_json,
        diagnostics_json=excluded.diagnostics_json,updated_at=excluded.updated_at
    """, (cache_key(item), _text(item.get("itemId") or item.get("id"), 160), media_fingerprint(item),
          json.dumps(evidence or [], ensure_ascii=False), json.dumps(diagnostics or {}, ensure_ascii=False), stamp, stamp))
    conn.commit()
