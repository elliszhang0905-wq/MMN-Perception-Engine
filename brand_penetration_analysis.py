"""Evidence-locked brand and pairwise conclusions for the brand penetration center."""

from __future__ import annotations

import hashlib
import json
import re


REVIEW_ROLES = ("review_1", "review_2", "review_3")
PUBLIC_ROLE_LABELS = ("独立复核A", "独立复核B", "独立复核C")
BRAND_JUDGEMENTS = {"strengthening", "stable", "fragmented", "risk_dominated", "insufficient"}
PRIMARY_INTENTS = {
    "product_launch", "technology", "user_experience", "promotion",
    "brand_discussion", "risk_response", "mixed", "insufficient",
}
ACTION_DIRECTIONS = {"amplify", "differentiate", "defend", "monitor", "insufficient"}
PAIR_RELATIONSHIPS = {"direct_competition", "partial_overlap", "complementary", "unclear"}
PRESSURE_LEVELS = {"high", "medium", "low", "unclear"}
_CJK_RE = re.compile(r"[\u3400-\u9fff]")
_PROVIDER_RE = re.compile(r"qwen|deepseek|kimi|通义|千问|深度求索|月之暗面", re.IGNORECASE)


def _clean_text(value, limit=600):
    return str(value or "").strip()[:limit]


def _unique(values):
    result = []
    for value in values or []:
        text = _clean_text(value, 120)
        if text and text not in result:
            result.append(text)
    return result


def _fingerprint(payload):
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_evidence_packet(result, date_window=None):
    """Freeze one public-evidence packet shared by all three blind reviews."""
    result = dict(result or {})
    comparisons = [dict(row) for row in result.get("modelComparisons") or [] if row.get("model")]
    own = next((row for row in comparisons if row.get("role") == "own"), comparisons[0] if comparisons else {})
    own_brand = _clean_text(own.get("model") or result.get("keyword"), 120)
    competitors = _unique(row.get("model") for row in comparisons if row.get("role") == "competitor")
    brands = _unique([own_brand, *competitors])
    rows = []
    for item in result.get("verifiedComparisonItems") or []:
        evidence_id = _clean_text(item.get("id") or item.get("canonicalContentId"), 160)
        brand = _clean_text(item.get("brandName") or item.get("normalizedModel") or item.get("keyword"), 120)
        if not evidence_id or brand not in brands:
            continue
        rows.append({
            "id": evidence_id,
            "brand": brand,
            "platform": _clean_text(item.get("platformLabel") or item.get("platform"), 60),
            "text": _clean_text(item.get("text"), 320),
            "sentiment": _clean_text(item.get("sentiment"), 40),
            "heat": item.get("heat"),
            "sourceUrl": _clean_text(item.get("sourceUrl"), 500),
        })
    rows = sorted({row["id"]: row for row in rows}.values(), key=lambda row: row["id"])
    brand_evidence_ids = {
        brand: [row["id"] for row in rows if row["brand"] == brand]
        for brand in brands
    }
    scope = {
        "ownBrand": own_brand,
        "competitors": competitors,
        "brands": brands,
        "dateWindow": dict(date_window or result.get("dateWindow") or {}),
        "platforms": sorted({row["platform"] for row in rows if row["platform"]}),
        "evidence": rows,
        "brandEvidenceIds": brand_evidence_ids,
        "boundary": "公开传播证据只能支撑品牌传播判断，不证明市场渗透、购买意愿或销售因果。",
    }
    scope["status"] = "ready" if own_brand and competitors and rows else "insufficient_evidence"
    scope["fingerprint"] = _fingerprint(scope)
    return scope


def analysis_messages(packet):
    """Build the identical source-locked prompt used by every independent review."""
    system = (
        "你是MMN品牌传播独立复核角色。只能使用输入中的冻结证据，不得补充外部事实，不得把传播关联写成市场渗透或销售因果。"
        "你不知道其他复核角色的结论。必须覆盖输入中每个brands和每个competitors，只输出一个合法JSON对象。"
        "brandConclusions每项字段：brand、status(ready|insufficient_evidence)、"
        "judgement(strengthening|stable|fragmented|risk_dominated|insufficient)、"
        "primaryIntent(product_launch|technology|user_experience|promotion|brand_discussion|risk_response|mixed|insufficient)、"
        "actionDirection(amplify|differentiate|defend|monitor|insufficient)、conclusion、communicationTheme、"
        "representativeAction、opportunity、risk、recommendedAction、leadingIndicator、resultIndicator、"
        "stopCondition、uncertainty、evidenceIds、confidence(0-1)。"
        "pairwiseConclusions每项字段：ownBrand、competitor、status(ready|insufficient_evidence)、"
        "relationship(direct_competition|partial_overlap|complementary|unclear)、pressure(high|medium|low|unclear)、"
        "actionDirection(amplify|differentiate|defend|monitor|insufficient)、cognitionOverlap、competitorIntent、"
        "ownAdvantage、ownGap、threat、opportunity、recommendedAction、leadingIndicator、resultIndicator、"
        "stopCondition、uncertainty、evidenceIds、confidence(0-1)。"
        "ready结论必须引用合法evidenceIds；证据不足时必须返回insufficient_evidence，不得用通用建议填充。"
        "每个自然语言字段最多40个汉字，使用短句，避免重复证据原文。"
        "所有客户可见自然语言使用简体中文，不得出现模型或技术供应商名称。"
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(packet, ensure_ascii=False)},
    ]


def _confidence(value):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("置信度无效") from exc
    if not 0 <= number <= 1:
        raise ValueError("置信度超出范围")
    return round(number, 4)


def _customer_text(row, fields):
    result = {}
    for field in fields:
        value = _clean_text(row.get(field))
        if not value or not _CJK_RE.search(value) or _PROVIDER_RE.search(value):
            raise ValueError(f"{field}缺失或不符合客户语言规则")
        result[field] = value
    return result


def _evidence_ids(row, allowed_ids):
    values = sorted(set(_unique(row.get("evidenceIds"))))
    if not values or not set(values).issubset(set(allowed_ids)):
        raise ValueError("结论引用了缺失或越界证据")
    return values


def _normalize_brand_row(row, brand, packet):
    if not isinstance(row, dict) or _clean_text(row.get("brand"), 120) != brand:
        raise ValueError(f"{brand}品牌结论缺失")
    status = _clean_text(row.get("status"), 60)
    allowed_ids = packet["brandEvidenceIds"].get(brand) or []
    if status == "insufficient_evidence":
        return {"brand": brand, "status": status, "evidenceIds": [], "confidence": 0.0}
    if status != "ready":
        raise ValueError(f"{brand}品牌结论状态无效")
    judgement = _clean_text(row.get("judgement"), 60)
    primary_intent = _clean_text(row.get("primaryIntent"), 60)
    action_direction = _clean_text(row.get("actionDirection"), 60)
    if judgement not in BRAND_JUDGEMENTS or primary_intent not in PRIMARY_INTENTS or action_direction not in ACTION_DIRECTIONS:
        raise ValueError(f"{brand}品牌结论枚举无效")
    text_fields = (
        "conclusion", "communicationTheme", "representativeAction", "opportunity", "risk",
        "recommendedAction", "leadingIndicator", "resultIndicator", "stopCondition", "uncertainty",
    )
    return {
        "brand": brand, "status": "ready", "judgement": judgement,
        "primaryIntent": primary_intent, "actionDirection": action_direction,
        **_customer_text(row, text_fields),
        "evidenceIds": _evidence_ids(row, allowed_ids),
        "confidence": _confidence(row.get("confidence")),
    }


def _normalize_pair_row(row, own_brand, competitor, packet):
    if (not isinstance(row, dict) or _clean_text(row.get("ownBrand"), 120) != own_brand
            or _clean_text(row.get("competitor"), 120) != competitor):
        raise ValueError(f"{own_brand}与{competitor}竞争结论缺失")
    status = _clean_text(row.get("status"), 60)
    own_ids = set(packet["brandEvidenceIds"].get(own_brand) or [])
    competitor_ids = set(packet["brandEvidenceIds"].get(competitor) or [])
    if status == "insufficient_evidence":
        return {"ownBrand": own_brand, "competitor": competitor, "status": status, "evidenceIds": [], "confidence": 0.0}
    if status != "ready":
        raise ValueError(f"{own_brand}与{competitor}竞争结论状态无效")
    relationship = _clean_text(row.get("relationship"), 60)
    pressure = _clean_text(row.get("pressure"), 60)
    action_direction = _clean_text(row.get("actionDirection"), 60)
    if relationship not in PAIR_RELATIONSHIPS or pressure not in PRESSURE_LEVELS or action_direction not in ACTION_DIRECTIONS:
        raise ValueError(f"{own_brand}与{competitor}竞争结论枚举无效")
    evidence_ids = _evidence_ids(row, own_ids | competitor_ids)
    if not own_ids.intersection(evidence_ids) or not competitor_ids.intersection(evidence_ids):
        raise ValueError(f"{own_brand}与{competitor}结论未同时引用双方证据")
    text_fields = (
        "cognitionOverlap", "competitorIntent", "ownAdvantage", "ownGap", "threat", "opportunity",
        "recommendedAction", "leadingIndicator", "resultIndicator", "stopCondition", "uncertainty",
    )
    return {
        "ownBrand": own_brand, "competitor": competitor, "status": "ready",
        "relationship": relationship, "pressure": pressure, "actionDirection": action_direction,
        **_customer_text(row, text_fields), "evidenceIds": evidence_ids,
        "confidence": _confidence(row.get("confidence")),
    }


def normalize_review(payload, packet):
    if not isinstance(payload, dict):
        raise ValueError("未返回结构化品牌结论")
    brand_rows = {str(row.get("brand") or "").strip(): row for row in payload.get("brandConclusions") or [] if isinstance(row, dict)}
    pair_rows = {str(row.get("competitor") or "").strip(): row for row in payload.get("pairwiseConclusions") or [] if isinstance(row, dict)}
    own_brand = packet["ownBrand"]
    return {
        "brandConclusions": [_normalize_brand_row(brand_rows.get(brand), brand, packet) for brand in packet["brands"]],
        "pairwiseConclusions": [_normalize_pair_row(pair_rows.get(competitor), own_brand, competitor, packet) for competitor in packet["competitors"]],
    }


def _status_row(identity, status, reasons, common_ids=None):
    return {**identity, "status": status, "reasons": list(dict.fromkeys(reasons)), "commonEvidenceIds": sorted(common_ids or [])}


def _fuse_rows(rows, identity, enum_fields):
    if len(rows) != len(REVIEW_ROLES):
        return _status_row(identity, "degraded", ["三路独立复核未全部完成"])
    if any(row.get("status") == "insufficient_evidence" for row in rows):
        return _status_row(identity, "insufficient_evidence", ["至少一路复核判定证据不足"])
    common_ids = set(rows[0]["evidenceIds"])
    for row in rows[1:]:
        common_ids &= set(row["evidenceIds"])
    reasons = []
    if not common_ids:
        reasons.append("三路结论没有共同引用的有效证据")
    for field in enum_fields:
        if len({row.get(field) for row in rows}) != 1:
            reasons.append(f"三路复核的{field}判断不一致")
    if min(row["confidence"] for row in rows) < 0.6:
        reasons.append("至少一路复核置信度低于0.6")
    if reasons:
        return _status_row(identity, "manual_required", reasons, common_ids)
    selected = sorted(rows, key=lambda row: row["confidence"])[1]
    final = {key: value for key, value in selected.items() if key not in {"status", "evidenceIds", "confidence"}}
    return {
        **identity, **final, "status": "aligned", "reasons": [],
        "commonEvidenceIds": sorted(common_ids), "evidenceCount": len(common_ids),
        "confidence": min(row["confidence"] for row in rows),
    }


def fuse_reviews(provider_outputs, packet, provider_errors=None):
    normalized, failures, partials = {}, [], []
    for role in REVIEW_ROLES:
        payload = (provider_outputs or {}).get(role)
        if not isinstance(payload, dict):
            print(f"[brand-penetration] {role} output rejected: 未返回结构化品牌结论", flush=True)
            failures.append(role)
            continue
        brand_source = {
            str(row.get("brand") or "").strip(): row
            for row in payload.get("brandConclusions") or [] if isinstance(row, dict)
        }
        pair_source = {
            str(row.get("competitor") or "").strip(): row
            for row in payload.get("pairwiseConclusions") or [] if isinstance(row, dict)
        }
        brand_rows, pair_rows, row_failures = [], [], []
        for brand in packet.get("brands") or []:
            try:
                brand_rows.append(_normalize_brand_row(brand_source.get(brand), brand, packet))
            except ValueError as exc:
                print(f"[brand-penetration] {role} brand row rejected: {exc}", flush=True)
                brand_rows.append(None)
                row_failures.append(brand)
        for competitor in packet.get("competitors") or []:
            try:
                pair_rows.append(_normalize_pair_row(pair_source.get(competitor), packet.get("ownBrand"), competitor, packet))
            except ValueError as exc:
                print(f"[brand-penetration] {role} pair row rejected: {exc}", flush=True)
                pair_rows.append(None)
                row_failures.append(competitor)
        normalized[role] = {"brandConclusions": brand_rows, "pairwiseConclusions": pair_rows}
        if row_failures:
            partials.append(role)
    brand_conclusions = []
    for index, brand in enumerate(packet.get("brands") or []):
        rows = [
            normalized[role]["brandConclusions"][index] for role in REVIEW_ROLES
            if role in normalized and normalized[role]["brandConclusions"][index] is not None
        ]
        brand_conclusions.append(_fuse_rows(rows, {"brand": brand, "role": "own" if brand == packet.get("ownBrand") else "competitor"}, ("judgement", "primaryIntent", "actionDirection")))
    pairwise = []
    for index, competitor in enumerate(packet.get("competitors") or []):
        rows = [
            normalized[role]["pairwiseConclusions"][index] for role in REVIEW_ROLES
            if role in normalized and normalized[role]["pairwiseConclusions"][index] is not None
        ]
        pairwise.append(_fuse_rows(rows, {"ownBrand": packet.get("ownBrand"), "competitor": competitor}, ("relationship", "pressure", "actionDirection")))
    statuses = {row["status"] for row in [*brand_conclusions, *pairwise]}
    overall = ("degraded" if "degraded" in statuses else "manual_required" if "manual_required" in statuses
               else "insufficient_evidence" if "insufficient_evidence" in statuses else "aligned")
    validation_reasons = []
    if failures or partials or provider_errors:
        validation_reasons.append("存在未完成的独立复核")
    if overall == "manual_required":
        validation_reasons.append("部分品牌或逐竞品判断存在分歧，需人工复核")
    elif overall == "insufficient_evidence":
        validation_reasons.append("部分品牌或逐竞品判断证据不足")
    return {
        "schemaVersion": "brand-penetration-analysis-v3",
        "evidenceFingerprint": packet.get("fingerprint"),
        "brandConclusions": brand_conclusions,
        "pairwiseConclusions": pairwise,
        "validation": {
            "status": overall,
            "reasons": validation_reasons,
            "independentReviews": [
                {"role": label, "status": "failed" if role in failures else "partial" if role in partials else "completed"}
                for role, label in zip(REVIEW_ROLES, PUBLIC_ROLE_LABELS)
            ],
        },
        "boundary": packet.get("boundary"),
    }
