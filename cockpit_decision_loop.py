"""Decision-cockpit execution rules that remain traceable to validated evidence."""

from __future__ import annotations

import math


_ACTION_BY_CATEGORY = {
    "repair": "疑虑修复",
    "seize": "对比占位",
    "amplify": "资产放大",
}

_SCENARIO_BY_LABEL = {
    "用车场景": "真实通勤与周末出行场景",
    "动力与操控": "城市道路与长途驾驶实测",
    "空间": "家庭多人出行空间实测",
    "舒适性": "长途乘坐舒适体验",
    "内饰": "座舱质感与日常使用细节",
    "配置": "高频配置价值清单",
    "外观": "城市生活方式与设计细节",
    "智能座舱": "高频车机与语音交互实测",
    "品牌口碑": "真实车主长期口碑",
    "辅助/自动驾驶": "高频驾驶辅助场景实测",
    "价格": "购车决策与权益解释",
    "质量": "长期可靠性与问题澄清",
    "用户服务": "交付与售后服务体验",
    "用车成本": "真实能耗与补能账本",
    "安全": "真实安全场景与权威测试解释",
}

_STRATEGY_OPTIONS_BY_CATEGORY = {
    "repair": (
        ("evidence_clarify", "事实澄清", "事实澄清", "权威事实与真实使用澄清"),
        ("scenario_reassure", "场景释疑", "场景释疑", "高频使用场景回应"),
        ("owner_reassure", "口碑修复", "口碑修复", "真实车主长期体验复核"),
    ),
    "seize": (
        ("comparison_occupy", "对比占位", "对比占位", None),
        ("scenario_compete", "场景对比切入", "场景对比", "同级真实使用场景对比"),
        ("search_answer", "对比搜索承接", "搜索承接", "对比搜索问答与购买理由解释"),
    ),
    "amplify": (
        ("asset_amplify", "资产放大", "资产放大", None),
        ("benchmark_extend", "标杆延展", "标杆延展", "标杆能力拆解与同级对照"),
        ("word_of_mouth_expand", "口碑扩散", "口碑扩散", "真实车主口碑与使用反馈"),
    ),
}


def _number(value, default=0.0):
    try:
        value = float(value)
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default


def _priority_platform(label, signals):
    grouped = {}
    for signal in signals or []:
        if signal.get("label") != label:
            continue
        platform = str(signal.get("platform") or "").strip()
        if not platform:
            continue
        bucket = grouped.setdefault(platform, {"volume": 0.0, "interaction": 0.0})
        bucket["volume"] += max(0.0, _number(signal.get("volume")))
        bucket["interaction"] += max(0.0, _number(signal.get("interaction")))
    if not grouped:
        return "待补充平台"
    return max(
        grouped,
        key=lambda platform: (
            math.log1p(grouped[platform]["volume"]) + math.log1p(grouped[platform]["interaction"]),
            grouped[platform]["interaction"],
            grouped[platform]["volume"],
            platform,
        ),
    )


def _strategy_options(category, label, platform, competitor_model, default_scenario):
    options = []
    for option_id, title, action, scenario in _STRATEGY_OPTIONS_BY_CATEGORY[category]:
        options.append({
            "id": option_id,
            "title": title,
            "action": action,
            "competitorModel": competitor_model,
            "platform": platform,
            "contentScenario": scenario or default_scenario,
            "description": f"围绕{label}，以{title}推进{competitor_model}相关传播。",
        })
    return options


def derive_execution_recommendations(opportunities, market_signals):
    """Create next-step actions only for dual-model-validated opportunity labels."""
    recommendations = []
    for opportunity in opportunities or []:
        if opportunity.get("evidenceStatus") != "aligned":
            continue
        category = str(opportunity.get("category") or "")
        if category not in _ACTION_BY_CATEGORY:
            continue
        label = str(opportunity.get("label") or "").strip()
        if not label:
            continue
        evidence_ids = [str(item) for item in opportunity.get("commonEvidenceIds") or [] if str(item)]
        if not evidence_ids:
            continue
        competitor_model = str(opportunity.get("leadCompetitorModel") or "待补充竞品").strip()
        platform = _priority_platform(label, market_signals)
        default_scenario = _SCENARIO_BY_LABEL.get(label, f"{label}真实使用场景")
        options = _strategy_options(category, label, platform, competitor_model, default_scenario)
        recommended_option = options[0]
        recommendations.append({
            "label": label,
            "category": category,
            "categoryLabel": opportunity.get("categoryLabel") or _ACTION_BY_CATEGORY[category],
            "competitorModel": competitor_model,
            "platform": platform,
            "action": recommended_option["action"],
            "contentScenario": recommended_option["contentScenario"],
            "evidenceIds": evidence_ids,
            "opportunityScore": _number(opportunity.get("opportunityScore")),
            "recommendedOptionId": recommended_option["id"],
            "options": options,
        })
    return sorted(recommendations, key=lambda item: (-item["opportunityScore"], item["label"]))
