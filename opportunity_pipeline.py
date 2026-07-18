"""Evidence-first opportunity-map primitives.

The module is deliberately free of HTTP-server and model-provider state so the
alignment, scoring, and cross-validation rules can be tested without network
access or API keys.
"""

from __future__ import annotations

import ipaddress
import hashlib
import math
import re
import socket
from urllib.parse import urlparse


UNIFIED_LABELS = (
    "用车场景", "动力与操控", "空间", "舒适性", "内饰", "配置", "外观",
    "智能座舱", "品牌口碑", "辅助/自动驾驶", "价格", "质量", "用户服务",
    "用车成本", "安全",
)

_LABEL_ALIASES = {
    "用车场景": ("用车场景", "场景", "通勤", "出行"),
    "动力与操控": ("动力", "操控", "底盘", "悬架", "加速", "制动", "转向", "四驱"),
    "空间": ("空间", "轴距", "后排", "腿部空间", "储物"),
    "舒适性": ("舒适", "座椅", "通风", "加热", "按摩", "nvh", "静谧"),
    "内饰": ("内饰", "材质", "皮革", "饰板", "座舱材质"),
    "配置": ("配置", "天幕", "氛围灯", "音响"),
    "外观": ("外观", "造型", "车身", "灯光", "灯组", "轮胎", "轮毂", "22英寸", "22寸"),
    "智能座舱": ("智能座舱", "座舱智能", "车机", "多屏", "语音", "互联", "导航"),
    "品牌口碑": ("品牌", "口碑", "信任"),
    "辅助/自动驾驶": ("辅助驾驶", "自动驾驶", "智驾", "adas", "领航", "泊车"),
    "价格": ("价格", "售价", "权益", "优惠"),
    "质量": ("质量", "可靠", "耐久"),
    "用户服务": ("服务", "售后", "交付", "客服"),
    "用车成本": ("用车成本", "能耗", "电耗", "油耗", "保养成本", "补能"),
    "安全": ("安全", "碰撞", "气囊", "车身安全", "电池安全"),
}


def _text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def align_fact_label(text):
    """Map a fact to one stable display label, preserving ambiguity."""
    value = _text(text).lower()
    matched = [label for label, aliases in _LABEL_ALIASES.items() if any(alias.lower() in value for alias in aliases)]
    if len(matched) == 1:
        return {"label": matched[0], "status": "aligned"}
    if len(matched) > 1:
        return {"label": None, "labels": matched, "status": "ambiguous"}
    return {"label": None, "labels": [], "status": "unmatched"}


def extract_document_version_conflicts(filename, segments):
    """Compare version candidates from file name and extracted cover text."""
    source_text = " ".join(_text(item.get("text") if isinstance(item, dict) else item) for item in (segments or []))
    name = _text(filename)
    candidates = []
    for value in re.findall(r"(?i)\bV\s*\d{6,8}\b", name + " " + source_text):
        candidates.append(value.replace(" ", "").upper())
    for value in re.findall(r"(?i)\bVer\.?\s*\d{6,8}\b", source_text):
        candidates.append(re.sub(r"\s+", "", value).replace("VER.", "Ver.").replace("VER", "Ver"))
    unique = list(dict.fromkeys(candidates))
    return {
        "status": "manual_required" if len(unique) > 1 else "aligned",
        "candidates": unique,
        "reason": "文件名与封面/正文版本不一致" if len(unique) > 1 else "",
    }


def _finite(value, default=0.0):
    try:
        value = float(value)
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def heat_scores(rows):
    """Return log-normalized heat, using volume and interaction equally."""
    totals = {}
    for row in rows or []:
        label = row.get("label")
        if not label:
            continue
        bucket = totals.setdefault(label, {"volume": 0.0, "interaction": 0.0})
        bucket["volume"] += max(0.0, _finite(row.get("volume")))
        bucket["interaction"] += max(0.0, _finite(row.get("interaction")))
    max_volume = max((item["volume"] for item in totals.values()), default=0.0)
    max_interaction = max((item["interaction"] for item in totals.values()), default=0.0)
    output = {}
    for label, item in totals.items():
        volume = math.log1p(item["volume"])
        interaction = math.log1p(item["interaction"])
        volume_max = math.log1p(max_volume)
        interaction_max = math.log1p(max_interaction)
        v = volume / volume_max if volume_max else 0.0
        i = interaction / interaction_max if interaction_max else 0.0
        output[label] = round((v + i) / 2, 6)
    return output


def normalize_market_signals(rows):
    normalized = []
    for row in rows or []:
        raw = row.get("label") or row.get("attribute") or row.get("tag") or ""
        aligned = align_fact_label(raw)
        item = dict(row)
        item.update(aligned)
        item["nsr"] = _finite(row.get("nsr"))
        item["volume"] = max(0.0, _finite(row.get("volume")))
        item["interaction"] = max(0.0, _finite(row.get("interaction")))
        normalized.append(item)
    return normalized


def cross_validate_model_analyses(analyses, evidence_ids):
    evidence_ids = set(evidence_ids or [])
    by_provider = {provider: {item.get("label"): item for item in (items or []) if item.get("label")} for provider, items in (analyses or {}).items()}
    labels = sorted(set().union(*(items.keys() for items in by_provider.values())))
    consensus, manual = [], []
    for label in labels:
        qwen = by_provider.get("qwen", {}).get(label)
        deepseek = by_provider.get("deepseek", {}).get(label)
        reasons = []
        if label not in UNIFIED_LABELS:
            reasons.append("标签不在MMN统一标签中")
        if not qwen or not deepseek:
            reasons.append("双模型未同时返回该标签")
        if qwen and deepseek and qwen.get("direction") != deepseek.get("direction"):
            reasons.append("方向冲突")
        if qwen and deepseek and abs(_finite(qwen.get("factStrength")) - _finite(deepseek.get("factStrength"))) > 0.2:
            reasons.append("事实强度差异超过0.2")
        if qwen and deepseek and not (set(qwen.get("evidenceIds") or []) & set(deepseek.get("evidenceIds") or [])):
            reasons.append("双模型缺少共同证据")
        for item in (qwen, deepseek):
            if item and not item.get("evidenceIds"):
                reasons.append("模型未引用可核验证据")
            if item and not set(item.get("evidenceIds") or []).issubset(evidence_ids):
                reasons.append("引用了不存在的证据")
            if item and _finite(item.get("confidence"), 0.0) < 0.6:
                reasons.append("模型置信度不足")
        if reasons:
            manual.append({"label": label, "reasons": list(dict.fromkeys(reasons))})
            continue
        consensus.append({
            "label": label,
            "factStrength": round((_finite(qwen.get("factStrength")) + _finite(deepseek.get("factStrength"))) / 2, 6),
            "direction": qwen.get("direction"),
            "evidenceIds": sorted(set(qwen.get("evidenceIds") or []) | set(deepseek.get("evidenceIds") or [])),
            "commonEvidenceIds": sorted(set(qwen.get("evidenceIds") or []) & set(deepseek.get("evidenceIds") or [])),
            "confidence": round(min(_finite(qwen.get("confidence")), _finite(deepseek.get("confidence"))), 6),
            "evidenceStatus": "aligned",
        })
    return {"status": "manual_required" if manual else "aligned", "items": consensus, "manualItems": manual}


def build_competitor_product_summaries(source_results, competitor_facts, validation):
    """Expose one evidence-backed product strength per NSR label and competitor."""
    facts_by_id = {
        str(fact.get("id") or ""): fact
        for fact in (competitor_facts or [])
        if fact.get("id")
    }
    strengths_by_model = {}
    for item in validation.get("items") or []:
        label = _text(item.get("label"))
        if label not in UNIFIED_LABELS or item.get("evidenceStatus") != "aligned":
            continue
        fact_strength = _finite(item.get("factStrength"))
        for evidence_id in item.get("commonEvidenceIds") or []:
            fact = facts_by_id.get(str(evidence_id))
            if not fact or fact.get("alignmentStatus") != "aligned" or fact.get("label") != label:
                continue
            model = _text(fact.get("sourceModel") or fact.get("model"))
            if not model:
                continue
            source_url = _text(fact.get("sourceUrl") or (fact.get("evidence") or {}).get("sourceRef"))
            candidate = {
                "label": label,
                "claim": _text(fact.get("claim") or fact.get("value")),
                "factStrength": round(fact_strength, 6),
                "confidence": round(_finite(fact.get("confidence")), 6),
                "sourceUrl": source_url,
                "evidenceId": str(evidence_id),
            }
            bucket = strengths_by_model.setdefault(model, {})
            current = bucket.get(label)
            rank = (candidate["factStrength"], candidate["confidence"], len(candidate["claim"]))
            current_rank = (current["factStrength"], current["confidence"], len(current["claim"])) if current else None
            if current is None or rank > current_rank:
                bucket[label] = candidate
    summaries = []
    for source in source_results or []:
        item = dict(source)
        model = _text(item.get("model"))
        verified = item.get("status") == "verified"
        strengths = list(strengths_by_model.get(model, {}).values()) if verified else []
        item["coreProductStrengths"] = sorted(
            strengths,
            key=lambda strength: (-strength["factStrength"], strength["label"], strength["claim"]),
        )
        summaries.append(item)
    return summaries


def build_opportunity_map(rows, validated=False):
    result = []
    for row in rows or []:
        item = dict(row)
        map_x = max(-1.0, min(1.0, _finite(item.get("competitorLead"), _finite(item.get("competitorPressure")))))
        map_y = max(1.0, min(5.0, _finite(item.get("purchaseImpact"), 3.0)))
        item.update({"mapX": round(map_x, 6), "mapY": round(map_y, 6)})
        if not validated or item.get("evidenceStatus") != "aligned":
            item.update({"category": "manual_required", "categoryLabel": "待人工确认", "opportunityScore": None})
            result.append(item)
            continue
        fact = min(1.0, max(0.0, _finite(item.get("factStrength"))))
        recognition = min(1.0, max(0.0, _finite(item.get("recognition"))))
        heat = min(1.0, max(0.0, _finite(item.get("heat"))))
        pressure = min(1.0, max(0.0, _finite(item.get("competitorPressure"))))
        realization_gap = max(0.0, fact - (0.65 * recognition + 0.35 * heat))
        score = round(100 * (0.55 * realization_gap + 0.25 * pressure + 0.20 * heat), 1)
        if item.get("direction") == "repair" or item.get("negativeNsr") is True:
            category = "repair"
        elif fact >= 0.7 and (recognition < 0.65 or heat < 0.55 or pressure >= 0.25):
            category = "seize"
        else:
            category = "amplify"
        item.update({"category": category, "categoryLabel": {"repair": "优先修复", "seize": "抢占空位", "amplify": "持续放大"}[category], "opportunityScore": score})
        result.append(item)
    return sorted(result, key=lambda row: row.get("opportunityScore") if row.get("opportunityScore") is not None else -1, reverse=True)


def _is_private_ip(address):
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved or ip.is_unspecified


def _is_macos_fake_proxy_ip(address):
    try:
        return ipaddress.ip_address(address) in ipaddress.ip_network("198.18.0.0/15")
    except ValueError:
        return False


def is_public_official_url(url, allowed_domains=None, resolver=socket.getaddrinfo):
    try:
        parsed = urlparse(str(url or ""))
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        if parsed.port and parsed.port not in {80, 443}:
            return False
        host = parsed.hostname.rstrip(".").lower()
        if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
            return False
        if allowed_domains:
            allowed = {str(item).lower().lstrip(".") for item in allowed_domains}
            if not any(host == domain or host.endswith("." + domain) for domain in allowed):
                return False
        try:
            literal = ipaddress.ip_address(host)
            return not _is_private_ip(str(literal))
        except ValueError:
            pass
        addresses = {item[4][0] for item in resolver(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)}
        return bool(addresses) and all(
            not _is_private_ip(address) or (parsed.scheme == "https" and _is_macos_fake_proxy_ip(address))
            for address in addresses
        )
    except (ValueError, OSError, socket.gaierror):
        return False


def _fact_id(*parts):
    return "fact_" + hashlib.sha1("|".join(_text(part) for part in parts).encode("utf-8")).hexdigest()[:16]


def _fact_items_from_segments(segments, *, source_id, source_type, source_ref, model="", version=""):
    facts = []
    for segment_index, segment in enumerate(segments or [], 1):
        text = _text(segment.get("text") if isinstance(segment, dict) else segment)
        if not text:
            continue
        # Keep short, independently citable claims instead of sending a whole
        # page/slide as one opaque model context.
        claims = [part.strip() for part in re.split(r"[。；;！？!?\n]", text) if part.strip()]
        for claim_index, claim in enumerate(claims, 1):
            aligned = align_fact_label(claim)
            evidence = {"sourceId": source_id, "sourceType": source_type, "sourceRef": source_ref, "excerpt": claim[:500]}
            for key in ("pageNo", "slideNo", "paragraphNo", "locator"):
                if isinstance(segment, dict) and segment.get(key) is not None:
                    evidence[key] = segment[key]
            facts.append({
                "id": _fact_id(source_id, segment_index, claim_index, claim),
                "label": aligned.get("label"),
                "labels": aligned.get("labels", []),
                "alignmentStatus": aligned["status"],
                "claim": claim,
                "value": claim,
                "model": model,
                "version": version,
                "evidence": evidence,
                "confidence": 0.85 if aligned["status"] == "aligned" else 0.45,
            })
    return facts


def build_product_document(parsed, *, document_id, filename, sha256, brand="", model="", version="", role="own_product"):
    """Convert the shared BF parser result to versioned product evidence."""
    segments = parsed.get("segments") if isinstance(parsed, dict) else []
    conflict = extract_document_version_conflicts(filename, segments)
    candidates = conflict.get("candidates") or []
    effective_version = version or (candidates[0] if len(candidates) == 1 else "")
    facts = _fact_items_from_segments(
        segments,
        source_id=document_id,
        source_type=role,
        source_ref=filename,
        model=model,
        version=effective_version,
    )
    manual = []
    if conflict["status"] != "aligned":
        manual.append({"type": "version_conflict", **conflict})
    ambiguous = [fact for fact in facts if fact["alignmentStatus"] == "ambiguous"]
    unmatched = [fact for fact in facts if fact["alignmentStatus"] == "unmatched"]
    manual.extend({"type": "fact_alignment", "claim": fact["claim"], "labels": fact.get("labels", [])} for fact in ambiguous[:80])
    if unmatched:
        manual.append({"type": "fact_alignment_summary", "status": "unmatched", "count": len(unmatched), "reason": "部分文本未能唯一归入统一标签，请按需补充标签"})
    return {
        "documentId": document_id,
        "role": role,
        "brand": _text(brand),
        "model": _text(model),
        "version": effective_version,
        "filename": filename,
        "sha256": sha256,
        "pageCount": max((int(item.get("pageNo") or 0) for item in segments if isinstance(item, dict)), default=0),
        "facts": facts,
        "warnings": list(parsed.get("warnings") or []) if isinstance(parsed, dict) else [],
        "manualReviewItems": manual,
        "status": "manual_required" if manual else "parsed",
    }


def build_official_page_evidence(html, *, source_id, url, brand="", model="", version=""):
    """Extract plain product claims from a verified official HTML snapshot."""
    text = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", str(html or ""))
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"&(?:nbsp|amp|lt|gt);", " ", text)
    claims = [part.strip() for part in re.split(r"[。；;！？!?\n]", re.sub(r"\s+", " ", text)) if part.strip()]
    facts = _fact_items_from_segments(
        [{"text": claim, "locator": {"sourceUrl": url}} for claim in claims],
        source_id=source_id,
        source_type="competitor_official",
        source_ref=url,
        model=model,
        version=version,
    )
    return {"sourceId": source_id, "sourceType": "competitor_official", "url": url, "brand": brand, "model": model, "version": version, "facts": facts}
