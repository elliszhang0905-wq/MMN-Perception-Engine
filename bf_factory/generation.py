"""BF内部策略判断和可组合章节生成。"""

from .extraction import PROFILE_RULES


SEED_SECTION_INTENTS = {
    "STORE_VISIT": [
        "PROJECT_BACKGROUND", "CORE_VALUE", "TARGET_AUDIENCE", "CONTENT_DIRECTION",
        "CREATOR_ASSIGNMENT", "STORE_VISIT_SCRIPT", "STATIC_EXPERIENCE", "CTA",
        "RISK_CONTROL", "DELIVERY",
    ],
    "CLOUD_REVIEW": [
        "PROJECT_BACKGROUND", "CORE_ARGUMENT", "FACT_SUPPORT", "TOPIC_MATRIX",
        "CREATOR_ASSIGNMENT", "VOICEOVER_LOGIC", "MATERIAL_RETURN", "RISK_CONTROL", "DELIVERY",
    ],
    "HIGH_END_PHOTOGRAPHY": [
        "PROJECT_BACKGROUND", "VISUAL_TONE", "PRODUCT_POINT_DISTRIBUTION",
        "CREATOR_ASSIGNMENT", "SCENE_PLAN", "SHOT_LIST", "VEHICLE_LOGISTICS",
        "MATERIAL_RETURN", "RISK_CONTROL", "DELIVERY",
    ],
    "PRODUCT_INTERPRETATION": [
        "PROJECT_BACKGROUND", "PRODUCT_POINT_DISTRIBUTION", "TARGET_AUDIENCE",
        "COMPETITOR_COMPARISON", "CONTENT_DIRECTION", "RISK_CONTROL", "DELIVERY",
    ],
    "COMPETITOR_ATTACK_DEFENSE": [
        "PROJECT_BACKGROUND", "CORE_ARGUMENT", "COMPETITOR_COMPARISON", "FACT_SUPPORT",
        "CONTENT_DIRECTION", "RISK_CONTROL", "DELIVERY",
    ],
    "EXECUTION_GUIDE": [
        "PROJECT_BACKGROUND", "SHOT_LIST", "VEHICLE_LOGISTICS", "DYNAMIC_MATERIAL_CAPTURE",
        "MATERIAL_RETURN", "RISK_CONTROL", "DELIVERY",
    ],
}

SECTION_TITLES = {
    "INTERNAL_STRATEGY": "内部策略判断",
    "PROJECT_BACKGROUND": "项目背景",
    "CORE_VALUE": "核心价值目标",
    "TARGET_AUDIENCE": "车型定位与目标人群",
    "CONTENT_DIRECTION": "内容方向",
    "CREATOR_ASSIGNMENT": "达人类型与任务分工",
    "STORE_VISIT_SCRIPT": "探店脚本框架",
    "STATIC_EXPERIENCE": "静态体验重点",
    "CTA": "到店CTA与评论区引导",
    "CORE_ARGUMENT": "核心论点",
    "FACT_SUPPORT": "数据与事实支撑",
    "TOPIC_MATRIX": "话题矩阵与详细拆解",
    "VOICEOVER_LOGIC": "口播逻辑",
    "VISUAL_TONE": "视觉调性",
    "PRODUCT_POINT_DISTRIBUTION": "产品点分发",
    "SCENE_PLAN": "场景建议",
    "SHOT_LIST": "镜头语言与必拍镜头",
    "VEHICLE_LOGISTICS": "车务流程",
    "MATERIAL_RETURN": "素材使用与回传",
    "FEMALE_EXPERIENCE": "女性用户体验任务",
    "COMPETITOR_COMPARISON": "竞品同场景对比",
    "DYNAMIC_MATERIAL_CAPTURE": "动态素材采集",
    "COMMENT_GUIDANCE": "评论区讨论方向",
    "RISK_CONTROL": "禁止表达与审核风险",
    "DELIVERY": "交付要求",
    "SOURCE_APPENDIX": "来源与策略推断说明",
}


def compose_section_plan(payload, learned_profile=None):
    classification = payload.get("classification") or {}
    profile = str(classification.get("bfType") or "CUSTOM")
    if learned_profile and learned_profile.get("section_intents"):
        base = list(learned_profile["section_intents"])
    else:
        base = list(SEED_SECTION_INTENTS.get(profile, ["PROJECT_BACKGROUND", "TARGET_AUDIENCE", "CONTENT_DIRECTION", "CREATOR_ASSIGNMENT"]))
    requested = list(classification.get("contentIntents") or [])
    intent_aliases = {
        "STORE_VISIT_SCRIPT": "STORE_VISIT_SCRIPT",
        "VOICEOVER_LOGIC": "VOICEOVER_LOGIC",
        "VISUAL_TONE": "VISUAL_TONE",
        "SHOT_LIST": "SHOT_LIST",
        "FEMALE_EXPERIENCE": "FEMALE_EXPERIENCE",
        "COMPETITOR_COMPARISON": "COMPETITOR_COMPARISON",
        "DYNAMIC_MATERIAL_CAPTURE": "DYNAMIC_MATERIAL_CAPTURE",
        "STATIC_EXPERIENCE": "STATIC_EXPERIENCE",
        "CTA": "CTA",
        "RISK_CONTROL": "RISK_CONTROL",
        "MATERIAL_RETURN": "MATERIAL_RETURN",
        "COMMENT_GUIDANCE": "COMMENT_GUIDANCE",
    }
    for intent in requested:
        mapped = intent_aliases.get(intent)
        if mapped and mapped not in base:
            insert_at = base.index("RISK_CONTROL") if "RISK_CONTROL" in base else len(base)
            base.insert(insert_at, mapped)
    for required in ("RISK_CONTROL", "DELIVERY", "SOURCE_APPENDIX"):
        if required not in base:
            base.append(required)
    intents = ["INTERNAL_STRATEGY", *base]
    return [
        {
            "intent": intent,
            "title": SECTION_TITLES.get(intent, intent.replace("_", " ").title()),
            "visibility": "INTERNAL" if intent == "INTERNAL_STRATEGY" else "DELIVERABLE",
            "origin": "LEARNED_PROFILE" if learned_profile and intent in learned_profile.get("section_intents", []) else "COMPOSED",
        }
        for intent in _unique(intents)
    ]


def generate_internal_strategy(payload, retrieval_context):
    strategy = payload.get("strategy") or {}
    product = payload.get("product") or {}
    content = payload.get("content") or {}
    execution = payload.get("execution") or {}
    risk = payload.get("risk") or {}
    selling_points = product.get("coreSellingPoints") or ["核心产品价值"]
    competitors = strategy.get("competitors") or []
    goals = strategy.get("communicationGoals") or ["认知建立"]
    audience = strategy.get("targetAudience") or ["目标用户"]
    profile = str((payload.get("classification") or {}).get("bfType") or "CUSTOM")
    creator_role = {
        "STORE_VISIT": "把产品卖点转成可观察、可体验、可到店验证的内容证据",
        "CLOUD_REVIEW": "用事实和清晰观点完成议题解释，避免复述品牌通稿",
        "HIGH_END_PHOTOGRAPHY": "用场景、镜头和产品细节建立品牌质感与车型记忆",
    }.get(profile, "围绕目标用户完成事实解释、场景体验和内容转化任务")
    evidence_refs = []
    for item in retrieval_context or []:
        source = item.get("source") or item.get("id") or item.get("title")
        if source and source not in evidence_refs:
            evidence_refs.append(str(source))
    return {
        "currentCommunicationProblem": strategy.get("currentCommunicationProblem") or f"{strategy.get('model') or '当前车型'}需要把分散卖点收束为用户能够复述的购买理由",
        "bestAngle": strategy.get("coreStrategyJudgment") or f"优先用{'、'.join(selling_points[:2])}回应{' / '.join(audience[:2])}的真实使用问题",
        "avoidLeadingWith": product.get("avoidLeadingWith") or ["缺少事实或体验证据的参数堆砌"],
        "competitorPressure": f"核心压力来自{'、'.join(competitors[:3])}对同类用户场景和心智位置的争夺" if competitors else "当前资料未给出明确竞品，需避免自行扩展竞品攻击结论",
        "creatorRole": creator_role,
        "finalDirection": strategy.get("finalContentDirection") or f"最终指向{'、'.join(goals[:2])}",
        "riskAvoidance": risk.get("prohibitedExpressions") or ["避免绝对化、无来源参数和未经授权的价格权益表达"],
        "executionMusts": [item.get("item") for item in execution.get("executionChecklist") or [] if item.get("item")] or execution.get("dynamicMaterialRequirements") or ["所有必须表达内容都要对应可执行镜头或口播任务"],
        "evidenceRefs": evidence_refs,
        "judgmentOrigin": "MMN_STRATEGY_INFERENCE",
    }


def render_adaptive_brief(payload, internal_strategy, section_plan):
    title = (payload.get("strategy") or {}).get("bfName") or "MMN商业化内容BF"
    markdown = [f"# {title}", "", f"> BF范式：{_profile_label(payload)}｜结构由MMN按任务意图动态编排"]
    sections = []
    for index, item in enumerate(section_plan, 1):
        intent = item["intent"]
        body = _render_section(intent, payload, internal_strategy)
        section = {**item, "order": index, "body": body}
        sections.append(section)
        markdown.extend(["", f"## {index}. {item['title']}", "", body])
    return {"title": title, "sections": sections, "markdown": "\n".join(markdown).strip() + "\n"}


def _render_section(intent, payload, internal):
    strategy = payload.get("strategy") or {}
    product = payload.get("product") or {}
    content = payload.get("content") or {}
    execution = payload.get("execution") or {}
    risk = payload.get("risk") or {}
    if intent == "INTERNAL_STRATEGY":
        return "\n".join(
            [
                "> 仅供MMN内部策略判断，默认不作为达人交付正文。",
                f"- 当前传播问题：{internal['currentCommunicationProblem']}",
                f"- 最适合打什么：{internal['bestAngle']}",
                f"- 不建议主打：{_inline(internal['avoidLeadingWith'])}",
                f"- 竞品压力：{internal['competitorPressure']}",
                f"- 达人角色：{internal['creatorRole']}",
                f"- 最终指向：{internal['finalDirection']}",
                f"- 风险规避：{_inline(internal['riskAvoidance'])}",
                f"- 执行必进项：{_inline(internal['executionMusts'])}",
                "- 判断性质：策略推断（需结合引用来源和人工复核）",
            ]
        )
    if intent == "PROJECT_BACKGROUND":
        return _bullets([
            f"品牌/车型：{strategy.get('brand') or '待确认'} / {strategy.get('model') or '待确认'}",
            f"项目阶段：{strategy.get('projectStage') or '待确认'}",
            f"项目背景：{strategy.get('projectBackground') or internal['currentCommunicationProblem']}",
            f"传播目标：{_inline(strategy.get('communicationGoals'))}",
        ])
    if intent in {"CORE_VALUE", "CORE_ARGUMENT"}:
        return _bullets([f"核心策略判断：{internal['bestAngle']}", f"内容最终指向：{internal['finalDirection']}", f"核心卖点：{_inline(product.get('coreSellingPoints'))}"])
    if intent == "TARGET_AUDIENCE":
        return _bullets([f"目标人群：{_inline(strategy.get('targetAudience'))}", f"用户痛点：{_inline(strategy.get('userPainPoints'))}", f"用户利益：{_inline(strategy.get('userBenefits'))}"])
    if intent == "CONTENT_DIRECTION":
        return _bullets((content.get("contentDirections") or [internal["bestAngle"]]) + [f"达人内容角色：{internal['creatorRole']}"])
    if intent == "CREATOR_ASSIGNMENT":
        assignments = content.get("creatorAssignments") or []
        if assignments:
            return _bullets([f"{item.get('creatorType') or '达人'}：{item.get('task') or ''}" for item in assignments])
        return _bullets([internal["creatorRole"], "按达人专业能力分配事实解释、场景体验和转化承接任务"])
    if intent == "STORE_VISIT_SCRIPT":
        return _numbered(content.get("scriptFramework") or ["从用户真实问题进入", "完成静态体验和核心卖点验证", "给出适合人群和到店理由", "以明确CTA收尾"])
    if intent == "STATIC_EXPERIENCE":
        return _bullets((content.get("mustShoot") or product.get("mustSay") or product.get("coreSellingPoints") or ["逐项确认静态体验任务"]))
    if intent == "CTA":
        return _bullets([content.get("endingCta") or "引导用户到官方渠道了解车型、活动或预约体验", _inline(content.get("commentGuidance")) or "评论区围绕真实体验问题展开，不制造虚假咨询"])
    if intent == "FACT_SUPPORT":
        parameters = product.get("parameters") or []
        return _bullets([f"{item.get('name')}: {item.get('value')} {item.get('unit') or ''}" for item in parameters] or product.get("evidenceSources") or ["所有数据和事实必须绑定原始资料来源"])
    if intent == "TOPIC_MATRIX":
        topics = content.get("topicMatrix") or []
        return _bullets([f"{item.get('topic')}: {item.get('coreArgument')}" for item in topics] or content.get("topicDirections") or ["根据传播问题拆分话题、论点、达人和证据"])
    if intent == "VOICEOVER_LOGIC":
        return _numbered(content.get("middleStructure") or ["提出用户正在讨论的问题", "给出清晰判断", "用事实或体验支撑", "转译为用户利益", "回到车型定位和行动建议"])
    if intent == "VISUAL_TONE":
        return _bullets(content.get("cameraLanguage") or ["以品牌调性、用户生活方式和产品细节共同建立视觉记忆", "避免无意义空镜和与车型定位冲突的过度滤镜"])
    if intent == "PRODUCT_POINT_DISTRIBUTION":
        return _bullets([f"{point}：必须转译为用户能够感知的场景和镜头" for point in product.get("coreSellingPoints") or ["核心产品点待确认"]])
    if intent == "SCENE_PLAN":
        return _bullets(execution.get("locationRequirements") or ["场景必须同时服务车型定位、产品表达和达人风格"])
    if intent == "SHOT_LIST":
        return _bullets(content.get("mustShoot") or ["建立全景、中景、产品特写和人车关系四层镜头清单"])
    if intent == "VEHICLE_LOGISTICS":
        return _numbered((execution.get("vehicleReceivingProcess") or []) + (execution.get("vehicleInspectionChecklist") or []) or ["车辆接收与配置确认", "车况、清洁、车牌、铭牌检查", "灯光和内饰屏幕检查", "拍摄结束后素材与车辆交接"])
    if intent == "MATERIAL_RETURN":
        return _bullets((execution.get("materialReturnRequirements") or []) + (execution.get("deliveryFormats") or []) or ["按约定目录和命名规则回传原片、成片和可编辑工程文件"])
    if intent == "FEMALE_EXPERIENCE":
        return _bullets(["从真实女性用户的上下车、坐姿、视野、储物、通勤和安全感问题进入", "避免将女性体验简化为颜色、外观或刻板标签", f"重点验证：{_inline(product.get('coreSellingPoints'))}"])
    if intent == "COMPETITOR_COMPARISON":
        return _bullets([f"对比对象：{_inline(strategy.get('competitors'))}", "只在同预算、同场景、同用户问题下对比", "对比结论必须绑定官方资料或可复核体验，不做情绪化攻击"])
    if intent == "DYNAMIC_MATERIAL_CAPTURE":
        return _bullets(execution.get("dynamicMaterialRequirements") or ["明确合规道路、驾驶人员、车速、机位和交通安全边界", "动态素材必须记录车型配置与拍摄条件"])
    if intent == "COMMENT_GUIDANCE":
        return _bullets(content.get("commentGuidance") or ["引导用户讨论真实使用场景和选车问题", "禁止虚构车主身份、成交价格或未经证实的故障结论"])
    if intent == "RISK_CONTROL":
        return _bullets((risk.get("prohibitedExpressions") or []) + (risk.get("platformReviewRisks") or []) or internal["riskAvoidance"])
    if intent == "DELIVERY":
        return _bullets((execution.get("deliveryFormats") or ["交付格式、数量、时长和审核节点需在执行前确认"]) + (execution.get("publishingSchedule") or []) + (execution.get("reshootRules") or []))
    if intent == "SOURCE_APPENDIX":
        locators = _source_locators(payload)
        return _bullets([f"引用位置：{item}" for item in locators] + ["未绑定原始来源的策略内容统一标记为“策略推断”，正式交付前需人工确认"])
    return _bullets(["该章节由MMN根据新型BF内容意图生成，需在编辑器中确认章节名称和执行口径"])


def _source_locators(payload):
    values = []
    for citations in (payload.get("provenance") or {}).values():
        for citation in citations or []:
            locator = citation.get("sourceLocator")
            if locator and locator not in values:
                values.append(locator)
    return values[:20]


def _profile_label(payload):
    classification = payload.get("classification") or {}
    code = classification.get("bfType") or "CUSTOM"
    return classification.get("bfTypeLabel") or PROFILE_RULES.get(code, {}).get("label") or "自定义BF"


def _bullets(values):
    clean = [str(value).strip() for value in values or [] if str(value or "").strip()]
    return "\n".join(f"- {value}" for value in clean) if clean else "- 待根据项目资料补充"


def _numbered(values):
    clean = [str(value).strip() for value in values or [] if str(value or "").strip()]
    return "\n".join(f"{index}. {value}" for index, value in enumerate(clean, 1)) if clean else "1. 待根据项目资料补充"


def _inline(values):
    if isinstance(values, str):
        return values.strip()
    return "、".join(str(value).strip() for value in values or [] if str(value or "").strip()) or "待确认"


def _unique(values):
    result = []
    for value in values:
        if value not in result:
            result.append(value)
    return result
