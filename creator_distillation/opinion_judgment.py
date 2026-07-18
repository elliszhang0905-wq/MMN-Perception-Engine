"""Turn traceable comment evidence into scoped, reviewable MMN opinion judgments."""

import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .media_processing import _config_value


ISSUES = {
    "tire_matching": ("轮胎匹配", ("轮胎", "胎宽", "255", "245", "275", "285", "滚阻")),
    "chassis_handling": ("底盘与操控", ("底盘", "悬架", "减震", "操控", "转向", "滤振", "侧倾")),
    "safety": ("安全与安全余量", ("安全", "刹车", "制动", "失控", "碰撞", "气囊", "安全余量")),
    "price_value": ("价格与价值感", ("价格", "贵", "便宜", "性价比", "降价", "优惠", "值不值")),
    "battery_range": ("续航与电池", ("续航", "电池", "里程", "掉电", "虚标", "达成率")),
    "charging": ("补能体验", ("充电", "快充", "补能", "充电桩")),
    "energy_efficiency": ("能耗", ("能耗", "油耗", "电耗", "省油", "省电")),
    "space": ("空间", ("空间", "后排", "后备箱", "头部空间", "腿部空间")),
    "comfort": ("舒适性", ("舒适", "座椅", "晕车", "噪音", "隔音", "颠", "震动")),
    "intelligent_cabin": ("智能座舱", ("车机", "座舱", "语音", "屏幕", "智能化", "系统")),
    "driver_assistance": ("辅助驾驶", ("智驾", "辅助驾驶", "自动驾驶", "NOA", "泊车", "AEB")),
    "quality_reliability": ("质量与可靠性", ("质量", "故障", "异响", "坏了", "可靠", "耐用", "做工")),
    "after_sales": ("售后与服务", ("售后", "维修", "保养", "服务", "4s", "交付")),
    "appearance": ("外观设计", ("外观", "设计", "造型", "好看", "丑", "颜值")),
}

NOISE_PATTERNS = (
    r"^\s*$", r"^\d{1,6}$", r"^@\S+\s*(总结|概括|分析).*$",
    r"(加微|私信.*报价|互关|回关|刷赞|代购|进群)",
)
POSITIVE = ("好", "不错", "喜欢", "满意", "稳", "舒服", "值", "合理", "清楚", "专业")
NEGATIVE = ("差", "不行", "担心", "危险", "贵", "异响", "虚标", "失望", "问题", "不合理", "窄")
CORRECTION = ("不是", "其实", "应该", "准确", "澄清", "不能单独", "单位是", "举个例子", "取决于")
PURCHASE = ("买", "不买", "下单", "退订", "劝退", "种草", "选车", "值不值", "考虑")
VEHICLE_BRANDS = ("小米", "蔚来", "理想", "问界", "特斯拉", "智界", "享界", "尊界", "极氪", "领克",
                  "比亚迪", "腾势", "小鹏", "宝马", "奔驰", "奥迪", "大众", "丰田", "本田", "日产",
                  "吉利", "长安", "奇瑞", "零跑")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _metadata(item):
    provenance = item.get("provenance") or {}
    return provenance.get("metadata") or item.get("metadata") or {}


def _vehicle_entities(text):
    entities = []
    for value in re.findall(r"#([^#\[\]]{2,30})", text):
        value = value.strip()
        if any(brand.lower() in value.lower() for brand in VEHICLE_BRANDS):
            entities.append(value)
    brand_pattern = "|".join(map(re.escape, VEHICLE_BRANDS))
    entities.extend(re.findall(rf"(?:{brand_pattern})[A-Za-z0-9-]{{1,12}}", text, re.I))
    return list(dict.fromkeys(entities))[:5]


def clean_comment_evidence(evidence):
    """Filter noise and count at most one opinion from each user per issue."""
    cleaned, rejected = [], Counter()
    seen = set()
    for item in evidence:
        text = re.sub(r"\s+", " ", str(item.get("quote_text") or item.get("quote") or "")).strip()
        if len(text) < 2 or any(re.search(pattern, text, re.I) for pattern in NOISE_PATTERNS):
            rejected["noise"] += 1
            continue
        meta = _metadata(item)
        user_id = str(meta.get("userId") or meta.get("user_id") or item.get("comment_id") or item.get("id") or "")
        normalized = re.sub(r"[^\w\u4e00-\u9fff]+", "", text).lower()
        dedupe_key = (user_id, normalized)
        if dedupe_key in seen:
            rejected["duplicate"] += 1
            continue
        seen.add(dedupe_key)
        issue_keys = [key for key, (_, terms) in ISSUES.items() if any(term.lower() in text.lower() for term in terms)]
        if not issue_keys:
            rejected["non_automotive_issue"] += 1
            continue
        likes = meta.get("likes")
        try:
            likes = max(0, int(likes or 0))
        except (TypeError, ValueError):
            likes = 0
        stance = "question" if ("?" in text or "？" in text or any(x in text for x in ("吗", "是不是", "为什么", "怎么"))) else "neutral"
        if any(word in text for word in CORRECTION):
            stance = "correction"
        elif sum(word in text for word in NEGATIVE) > sum(word in text for word in POSITIVE):
            stance = "concern"
        elif any(word in text for word in POSITIVE):
            stance = "praise"
        cleaned.append({
            "evidenceId": str(item.get("id") or item.get("comment_id") or ""),
            "commentId": str(item.get("comment_id") or item.get("id") or ""),
            "sourceId": str(item.get("source_id") or ""), "userId": user_id, "text": text,
            "likes": likes, "importanceWeight": round(1 + math.log1p(likes) / 10, 3),
            "issueKeys": issue_keys, "stance": stance,
            "vehicleEntities": _vehicle_entities(text),
            "purchaseImpact": "explicit" if any(word in text for word in PURCHASE) else "not_explicit",
            "authorRole": "expert_correction" if stance == "correction" and len(text) >= 35 else "audience",
        })
    return cleaned, dict(rejected)


def build_issue_signals(comments):
    groups = defaultdict(list)
    for item in comments:
        for issue_key in item["issueKeys"]:
            groups[issue_key].append(item)
    signals = []
    for key, items in groups.items():
        unique = {}
        for item in sorted(items, key=lambda row: (row["likes"], len(row["text"])), reverse=True):
            unique.setdefault(item["userId"], item)
        rows = list(unique.values())
        stance_counts = Counter(row["stance"] for row in rows)
        sources = sorted({row["sourceId"] for row in rows if row["sourceId"]})
        evidence_ids = [row["evidenceId"] for row in rows if row["evidenceId"]]
        dominant = stance_counts.most_common(1)[0][0] if stance_counts else "neutral"
        signals.append({
            "issueKey": key, "label": ISSUES[key][0], "opinionCount": len(rows),
            "workCount": len(sources), "sourceIds": sources, "stanceCounts": dict(stance_counts),
            "dominantStance": dominant,
            "purchaseImpactCount": sum(row["purchaseImpact"] == "explicit" for row in rows),
            "correctionCount": stance_counts.get("correction", 0),
            "vehicleEntities": [name for name, _ in Counter(
                entity for row in rows for entity in row.get("vehicleEntities") or []
            ).most_common(5)],
            "importanceScore": round(sum(row["importanceWeight"] for row in rows), 3),
            "evidenceIds": evidence_ids,
            "representativeEvidence": [{"evidenceId": row["evidenceId"], "quote": row["text"],
                                         "stance": row["stance"], "likes": row["likes"]} for row in rows[:3]],
        })
    return sorted(signals, key=lambda row: (row["opinionCount"], row["importanceScore"]), reverse=True)


def _scope(work_count):
    if work_count >= 3:
        return "platform_candidate", "跨至少 3 条作品重复出现，仅代表该达人受众中的平台级候选信号"
    return "content_signal", "仅在少量作品中出现，不能外推为达人整体、平台或市场舆情"


def _extract_json(text):
    value = str(text or "").strip()
    value = re.sub(r"^```(?:json)?\s*|\s*```$", "", value, flags=re.I | re.S)
    start, end = value.find("{"), value.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("模型未返回 JSON 对象")
    return json.loads(value[start:end + 1])


def _provider_call(provider, prompt):
    if provider == "qwen":
        key = _config_value("DASHSCOPE_API_KEY")
        base = _config_value("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        model = _config_value("QWEN_MODEL", "qwen-plus")
    else:
        key = _config_value("DEEPSEEK_API_KEY")
        base = _config_value("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        model = _config_value("DEEPSEEK_MODEL", "deepseek-chat")
    if not key:
        raise RuntimeError(f"未配置 {provider} API Key")
    body = {"model": model, "temperature": 0.1, "messages": [
        {"role": "system", "content": "你是MMN汽车舆情证据审计模型。只能引用输入证据ID，不得补造事实，只输出JSON。"},
        {"role": "user", "content": prompt},
    ]}
    request = Request(base.rstrip("/") + "/chat/completions",
                      data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                      headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return _extract_json(payload["choices"][0]["message"]["content"])
    except HTTPError as exc:
        raise RuntimeError(f"{provider} HTTP {exc.code}") from exc
    except (URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{provider} 调用失败: {type(exc).__name__}") from exc


def _model_prompt(comments, signals):
    allowed = [{"key": key, "label": value[0]} for key, value in ISSUES.items()]
    compact = [{"evidenceId": row["evidenceId"], "sourceId": row["sourceId"], "text": row["text"]}
               for row in comments[:120]]
    return """独立判断下列汽车评论。按给定issueKey聚类；direction只能是concern/praise/question/correction/mixed；
statementType只能是fact/inference/hypothesis/unknown。每个议题必须引用直接支持的evidenceIds。
输出 {\"issues\":[{\"issueKey\":...,\"direction\":...,\"statementType\":...,\"conclusion\":...,\"purchaseImpact\":...,\"correction\":...,\"confidence\":0-1,\"evidenceIds\":[...]}]}。
可用议题：%s\n规则信号：%s\n证据：%s""" % (
        json.dumps(allowed, ensure_ascii=False), json.dumps(signals[:8], ensure_ascii=False),
        json.dumps(compact, ensure_ascii=False))


def cross_validate_model_judgments(outputs, allowed_evidence_ids):
    providers = {name: value for name, value in outputs.items() if isinstance(value, dict)}
    errors = {name: str(value) for name, value in outputs.items() if not isinstance(value, dict)}
    if set(providers) != {"qwen", "deepseek"}:
        return {"status": "manual_required", "completedProviders": sorted(providers),
                "providerErrors": errors, "commonEvidenceIds": [], "alignedIssues": [],
                "reasons": ["Qwen 与 DeepSeek 未全部完成，不能发布模型判断"]}
    indexed = {}
    for provider, payload in providers.items():
        indexed[provider] = {str(item.get("issueKey")): item for item in payload.get("issues") or []
                             if str(item.get("issueKey")) in ISSUES}
    aligned, common_all, reasons = [], set(), []
    for key in sorted(set(indexed["qwen"]) & set(indexed["deepseek"])):
        left, right = indexed["qwen"][key], indexed["deepseek"][key]
        left_ids = set(map(str, left.get("evidenceIds") or [])) & allowed_evidence_ids
        right_ids = set(map(str, right.get("evidenceIds") or [])) & allowed_evidence_ids
        common = sorted(left_ids & right_ids)
        directions = {str(left.get("direction")), str(right.get("direction"))}
        confidence = min(float(left.get("confidence") or 0), float(right.get("confidence") or 0))
        if len(directions) != 1 or not common or confidence < .6:
            reasons.append(f"{ISSUES[key][0]}：模型方向、共同证据或置信度未达门槛")
            continue
        common_all.update(common)
        aligned.append({
            "issueKey": key, "label": ISSUES[key][0], "direction": directions.pop(),
            "statementType": "inference", "confidence": round(confidence, 3), "evidenceIds": common,
            "conclusion": str(left.get("conclusion") or right.get("conclusion") or "").strip(),
            "purchaseImpact": str(left.get("purchaseImpact") or right.get("purchaseImpact") or "未明确"),
            "correction": str(left.get("correction") or right.get("correction") or "").strip(),
        })
    status = "aligned" if aligned else "manual_required"
    if not aligned:
        reasons.append("没有形成可由两模型共同证据支持的议题判断")
    return {"status": status, "completedProviders": ["qwen", "deepseek"], "providerErrors": errors,
            "commonEvidenceIds": sorted(common_all), "alignedIssues": aligned,
            "reasons": list(dict.fromkeys(reasons))}


def build_opinion_judgment(evidence, asset_count=0, model_runner=None, use_models=True):
    comments, rejected = clean_comment_evidence(evidence)
    signals = build_issue_signals(comments)
    works = sorted({row["sourceId"] for row in comments if row["sourceId"]})
    scope, scope_note = _scope(len(works))
    allowed_ids = {row["evidenceId"] for row in comments if row["evidenceId"]}
    outputs = {}
    if use_models and comments:
        runner = model_runner or _provider_call
        prompt = _model_prompt(comments, signals)
        with ThreadPoolExecutor(max_workers=2) as pool:
            pending = {pool.submit(runner, provider, prompt): provider for provider in ("qwen", "deepseek")}
            for future in as_completed(pending):
                provider = pending[future]
                try:
                    outputs[provider] = future.result()
                except Exception as exc:
                    outputs[provider] = f"{type(exc).__name__}: {exc}"
    validation = cross_validate_model_judgments(outputs, allowed_ids) if use_models else {
        "status": "manual_required", "completedProviders": [], "providerErrors": {},
        "commonEvidenceIds": [], "alignedIssues": [], "reasons": ["模型校验未执行"]}
    valid_count, raw_count = len(comments), len(evidence)
    coverage = round(len(works) / max(1, int(asset_count or len(works) or 1)), 3)
    top = (validation.get("alignedIssues") or signals or [{}])[0]
    if validation["status"] == "aligned":
        summary = (f"在已分析的 {valid_count} 条有效汽车评论、{len(works)} 条作品中，"
                   f"{top.get('label')}是当前最明确的受众议题；判断范围为“{scope_note}”。")
    elif signals:
        summary = (f"评论中已识别到“{top.get('label')}”信号，但尚未通过 Qwen+DeepSeek 共同证据门禁，"
                   "当前仅作为待复核线索展示。")
    else:
        summary = "当前评论中没有足够的汽车议题证据，不能形成 MMN 舆情判断。"
    digest = hashlib.sha256("|".join(sorted(allowed_ids)).encode("utf-8")).hexdigest()[:16]
    return {
        "schemaVersion": "mmn-opinion-v1", "generatedAt": _now(), "inputDigest": digest,
        "status": validation["status"], "scope": scope, "scopeNote": scope_note,
        "summary": summary, "issueSignals": signals[:10], "judgments": validation.get("alignedIssues") or [],
        "professionalCorrections": [row for row in signals if row.get("correctionCount")],
        "completeness": {"rawCommentCount": raw_count, "validAutomotiveCommentCount": valid_count,
                         "uniqueUserCount": len({row["userId"] for row in comments}),
                         "worksCovered": len(works), "creatorAssetCount": int(asset_count or 0),
                         "workCoverage": coverage, "rejected": rejected},
        "modelValidation": validation,
        "statementBoundary": {"fact": "可回溯原始评论与作品", "inference": "双模型共同证据支持的议题判断",
                              "hypothesis": "尚需跨达人或跨平台验证", "unknown": "证据不足或模型分歧"},
        "limitations": ["点赞只影响议题重要度，不增加意见票数", "同一用户在同一议题最多计一票",
                        "单达人数据不能直接发布为全平台或全市场舆情"],
    }
