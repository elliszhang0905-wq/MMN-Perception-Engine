"""Evidence-locked three-provider attribution reasoning and persistence."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import uuid


PROVIDERS = ("qwen", "deepseek", "kimi")
PUBLIC_ROLES = {"qwen": "独立复核A", "deepseek": "独立复核B", "kimi": "独立复核C"}
VERDICTS = {"market_demand_gap", "awareness_gap", "downstream_funnel_break", "mixed", "insufficient"}
BREAKPOINTS = {"market_capacity", "segment_sales", "voice", "lead", "order", "unknown"}
REQUIRED_EVIDENCE_IDS = (
    "segment_market_capacity",
    "segment_vehicle_sales",
    "product_voice",
    "lead_achievement",
    "order_achievement",
)


E7X_LEAD_EVIDENCE = {
    "source": "E7X上市流量表现指标统计表",
    "period": "2026-06-16—2026-06-30",
    "leadTarget": 143758,
    "leadActual": 169212,
    "leadRate": 1.177,
    "orderTarget": 2000,
    "orderActual": 1293,
    "orderRate": 0.646,
    "boundary": "订单达成率是实际订单相对目标订单，不是同批线索真实转化率。",
}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_schema(conn):
    conn.executescript(
        """
        create table if not exists attribution_reasoning_runs (
            id text primary key,
            org_id text not null,
            edition text not null default 'china',
            model text not null,
            evidence_fingerprint text not null,
            evidence_packet_json text not null,
            provider_outputs_json text not null default '{}',
            provider_errors_json text not null default '{}',
            arbitration_json text not null default '{}',
            status text not null,
            created_at text not null,
            updated_at text not null
        );
        create index if not exists idx_attribution_reasoning_scope
        on attribution_reasoning_runs(org_id, edition, model, updated_at desc);
        """
    )


def build_evidence_packet(group_payload, model="奥迪E7X"):
    warnings = ((group_payload or {}).get("salesWarnings") or {}).get("saicModels") or []
    warning = next((item for item in warnings if str(item.get("model") or "").strip() == model), None)
    evaluation = (group_payload or {}).get("productEvaluation") or {}
    models = [item for item in evaluation.get("models") or [] if item.get("voice") is not None]
    product = next((item for item in models if str(item.get("model") or "").strip() == model), None)
    lead = E7X_LEAD_EVIDENCE if model == "奥迪E7X" else None
    if not warning or not product or not lead:
        return {
            "model": model,
            "status": "insufficient_evidence",
            "evidenceIds": [],
            "missing": [name for name, value in (("细分市场销量", warning), ("声量", product), ("线索与订单", lead)) if not value],
        }
    period = (((group_payload or {}).get("salesWarnings") or {}).get("source") or {}).get("period") or ""
    evidence = [
        {
            "id": "segment_market_capacity",
            "label": "细分市场容量",
            "facts": {"period": period, "segment": warning.get("segmentLabel"), "marketSales": warning.get("marketSales")},
            "boundary": "当前使用同口径单月实际销量描述市场规模，不替代长期市场容量预测。",
        },
        {
            "id": "segment_vehicle_sales",
            "label": "细分市场销量分析",
            "facts": {
                "sales": warning.get("sales"), "rank": warning.get("rank"), "marketShare": warning.get("marketShare"),
                "benchmark": warning.get("benchmark"), "performanceRate": warning.get("performanceRate"),
            },
            "boundary": "销量预警是相对头部竞品基准的表现，不单独证明需求或传播因果。",
        },
        {
            "id": "product_voice",
            "label": "声量分析",
            "facts": {
                "period": (evaluation.get("source") or {}).get("period"), "voice": product.get("voice"),
                "voiceRank": product.get("voiceRank"), "comparisonCount": len(models),
                "overallNsr": product.get("overallNsr"), "overallNsrRank": product.get("overallNsrRank"),
            },
            "boundary": "声量与净喜好度属于传播和认知证据，不等于市场需求、线索或销量。",
        },
        {
            "id": "lead_achievement",
            "label": "线索分析",
            "facts": {key: lead[key] for key in ("source", "period", "leadTarget", "leadActual", "leadRate")},
            "boundary": "当前缺少平台、内容、地区和统一线索ID，不能做内容级归因。",
        },
        {
            "id": "order_achievement",
            "label": "订单达成率",
            "facts": {key: lead[key] for key in ("period", "orderTarget", "orderActual", "orderRate")},
            "boundary": lead["boundary"],
        },
    ]
    packet = {
        "model": model,
        "status": "ready",
        "evidenceIds": list(REQUIRED_EVIDENCE_IDS),
        "evidence": evidence,
        "reasoningPath": [item["label"] for item in evidence],
        "causalBoundary": "跨域指标只能定位断点与提出待验证解释；三路一致也不构成因果证明。",
    }
    packet["fingerprint"] = hashlib.sha256(
        json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return packet


def normalize_provider_output(provider, payload, allowed_evidence_ids):
    if not isinstance(payload, dict):
        raise ValueError("未返回结构化研判")
    verdict = str(payload.get("verdict") or "").strip()
    breakpoint = str(payload.get("primaryBreak") or "").strip()
    if verdict not in VERDICTS or breakpoint not in BREAKPOINTS:
        raise ValueError("研判枚举无效")
    evidence_ids = sorted({str(item).strip() for item in payload.get("evidenceIds") or [] if str(item).strip()})
    allowed = set(allowed_evidence_ids or [])
    if set(evidence_ids) != allowed:
        raise ValueError("未完整引用锁定证据")
    try:
        confidence = float(payload.get("confidence"))
    except (TypeError, ValueError):
        raise ValueError("置信度无效")
    if not 0 <= confidence <= 1:
        raise ValueError("置信度超出范围")
    required_text = ("conclusion", "counterEvidence", "stopCondition", "causalBoundary")
    text_values = {key: str(payload.get(key) or "").strip() for key in required_text}
    if any(not value for value in text_values.values()):
        raise ValueError("研判字段不完整")
    alternatives = [str(item).strip() for item in payload.get("alternativeExplanations") or [] if str(item).strip()]
    actions = []
    for item in payload.get("nextActions") or []:
        if not isinstance(item, dict):
            continue
        row = {key: str(item.get(key) or "").strip() for key in ("priority", "action", "metric", "stopCondition")}
        if all(row.values()):
            actions.append(row)
    if not alternatives or not actions:
        raise ValueError("缺少替代解释或验证动作")
    return {
        "provider": provider,
        "verdict": verdict,
        "primaryBreak": breakpoint,
        **text_values,
        "alternativeExplanations": alternatives[:6],
        "nextActions": actions[:6],
        "evidenceIds": evidence_ids,
        "confidence": round(confidence, 4),
    }


def arbitrate(provider_outputs, allowed_evidence_ids, provider_errors=None):
    outputs = dict(provider_outputs or {})
    errors = dict(provider_errors or {})
    normalized = {}
    reasons = []
    for provider in PROVIDERS:
        if provider not in outputs:
            reasons.append("三路独立复核未全部完成")
            continue
        try:
            normalized[provider] = normalize_provider_output(provider, outputs[provider], allowed_evidence_ids)
        except ValueError as exc:
            errors[provider] = str(exc)
            reasons.append(str(exc))
    if len(normalized) != len(PROVIDERS):
        return {"status": "incomplete", "providers": normalized, "providerErrors": errors, "reasons": list(dict.fromkeys(reasons)), "commonEvidenceIds": [], "finalConclusion": None}
    items = list(normalized.values())
    common = set(items[0]["evidenceIds"])
    for item in items[1:]:
        common &= set(item["evidenceIds"])
    verdicts = {item["verdict"] for item in items}
    breakpoints = {item["primaryBreak"] for item in items}
    minimum_confidence = min(item["confidence"] for item in items)
    if common != set(allowed_evidence_ids or []):
        reasons.append("三路没有共同引用完整证据链")
    if len(verdicts) != 1:
        reasons.append("三路对问题性质判断不一致")
    if len(breakpoints) != 1:
        reasons.append("三路对主要断点判断不一致")
    if minimum_confidence < 0.6:
        reasons.append("至少一路置信度低于0.6")
    if reasons:
        return {"status": "manual_required", "providers": normalized, "providerErrors": errors, "reasons": list(dict.fromkeys(reasons)), "commonEvidenceIds": sorted(common), "finalConclusion": None}
    selected = sorted(items, key=lambda item: item["confidence"])[1]
    final = {key: value for key, value in selected.items() if key != "provider"}
    final["confidence"] = minimum_confidence
    final["evidenceIds"] = sorted(common)
    final["agreement"] = "three_independent_reviews"
    return {"status": "aligned", "providers": normalized, "providerErrors": errors, "reasons": [], "commonEvidenceIds": sorted(common), "finalConclusion": final}


def save_run(conn, *, org_id, edition, model, packet, provider_outputs, provider_errors, arbitration):
    init_schema(conn)
    stamp = _now()
    run_id = str(uuid.uuid4())
    conn.execute(
        "insert into attribution_reasoning_runs (id,org_id,edition,model,evidence_fingerprint,evidence_packet_json,provider_outputs_json,provider_errors_json,arbitration_json,status,created_at,updated_at) values (?,?,?,?,?,?,?,?,?,?,?,?)",
        (run_id, org_id or "local", edition or "china", model, packet.get("fingerprint") or "", json.dumps(packet, ensure_ascii=False), json.dumps(provider_outputs, ensure_ascii=False), json.dumps(provider_errors, ensure_ascii=False), json.dumps(arbitration, ensure_ascii=False), arbitration.get("status") or "incomplete", stamp, stamp),
    )
    conn.commit()
    return load_run(conn, run_id=run_id, org_id=org_id)


def load_run(conn, *, run_id="", org_id="local", edition="china", model=""):
    init_schema(conn)
    if run_id:
        row = conn.execute("select * from attribution_reasoning_runs where id=? and org_id=?", (run_id, org_id or "local")).fetchone()
    else:
        row = conn.execute("select * from attribution_reasoning_runs where org_id=? and edition=? and model=? order by updated_at desc limit 1", (org_id or "local", edition or "china", model)).fetchone()
    if not row:
        return None
    data = dict(row)
    packet = json.loads(data.pop("evidence_packet_json") or "{}")
    outputs = json.loads(data.pop("provider_outputs_json") or "{}")
    errors = json.loads(data.pop("provider_errors_json") or "{}")
    arbitration = json.loads(data.pop("arbitration_json") or "{}")
    return public_run({**data, "evidencePacket": packet, "providerOutputs": outputs, "providerErrors": errors, "arbitration": arbitration})


def public_run(run):
    arbitration = dict(run.get("arbitration") or {})
    provider_details = arbitration.pop("providers", {}) or {}
    public_providers = []
    for provider in PROVIDERS:
        detail = provider_details.get(provider)
        error = (run.get("providerErrors") or {}).get(provider)
        public_providers.append({
            "role": PUBLIC_ROLES[provider],
            "status": "completed" if detail else ("failed" if error else "pending"),
            "review": _public_value({key: value for key, value in (detail or {}).items() if key != "provider"}) if detail else None,
        })
    return {
        "id": run.get("id"),
        "model": run.get("model"),
        "status": run.get("status"),
        "evidenceFingerprint": run.get("evidence_fingerprint"),
        "evidencePacket": run.get("evidencePacket"),
        "providers": public_providers,
        "arbitration": _public_value(arbitration),
        "createdAt": run.get("created_at"),
        "updatedAt": run.get("updated_at"),
    }


def _public_value(value):
    if isinstance(value, dict):
        return {key: _public_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_public_value(item) for item in value]
    if isinstance(value, str):
        for provider in PROVIDERS:
            value = value.replace(provider, "独立复核").replace(provider.title(), "独立复核")
    return value
