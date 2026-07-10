"""BF范式识别、A-F字段抽取和自动标签。"""

import re
from urllib.parse import urlparse

from .schema import new_brief_payload, validate_brief_payload


PROFILE_RULES = {
    "STORE_VISIT": {
        "label": "探店BF",
        "keywords": ("探店", "门店", "到店", "展车", "静态体验", "用户第一视角", "到店CTA"),
    },
    "CLOUD_REVIEW": {
        "label": "云评/口播BF",
        "keywords": ("云评", "口播", "核心论点", "销量解读", "话题矩阵", "观点输出", "汽车营销号"),
    },
    "HIGH_END_PHOTOGRAPHY": {
        "label": "高质感摄影BF",
        "keywords": ("高质感摄影", "视觉大片", "Lifestyle拍摄", "镜头语言", "必拍镜头", "车务流程", "素材回传"),
    },
    "STATIC_SHOOT": {
        "label": "静态实拍",
        "keywords": ("静态实拍", "外观实拍", "内饰实拍", "产品细节", "静态素材", "固定机位", "车辆静态"),
    },
    "DYNAMIC_SHOOT": {
        "label": "动态实拍",
        "keywords": ("动态实拍", "路跑", "跟车", "追车", "车身姿态", "动态性能", "合规道路"),
    },
    "CHASSIS_SHOOT": {
        "label": "底盘实拍",
        "keywords": ("底盘实拍", "底盘结构", "举升机", "悬架细节", "底盘全貌", "护板", "制动结构"),
    },
    "PRODUCT_INTERPRETATION": {
        "label": "产品解读BF",
        "keywords": ("产品解读", "核心卖点", "智舱", "智驾", "底盘", "安全", "补能", "用户利益转译"),
    },
    "COMPETITOR_ATTACK_DEFENSE": {
        "label": "竞品攻防BF",
        "keywords": ("竞品攻防", "竞品对比", "竞品压制", "差异化表达", "竞品名称", "对比口径"),
    },
    "EXECUTION_GUIDE": {
        "label": "执行规范BF",
        "keywords": ("执行规范", "拍摄注意事项", "车辆接收", "车况确认", "素材回传", "审核红线", "补拍"),
    },
}

INTENT_RULES = {
    "PROJECT_BACKGROUND": ("项目背景", "传播背景", "项目阶段"),
    "TARGET_AUDIENCE": ("目标用户", "目标人群", "TA"),
    "STORE_VISIT_SCRIPT": ("探店", "门店", "静态体验", "到店"),
    "VOICEOVER_LOGIC": ("口播", "云评", "核心论点", "观点"),
    "VISUAL_TONE": ("视觉调性", "视觉大片", "高质感", "Lifestyle"),
    "SHOT_LIST": ("镜头语言", "必拍镜头", "镜头"),
    "FEMALE_EXPERIENCE": ("女性", "女用户", "女性体感"),
    "COMPETITOR_COMPARISON": ("竞品对比", "核心竞品", "同场景对比"),
    "DYNAMIC_MATERIAL_CAPTURE": ("动态实拍", "动态路跑", "动态素材", "路跑素材", "动态试驾", "跟车"),
    "STATIC_EXPERIENCE": ("静态实拍", "静态体验", "静态素材", "外观实拍", "内饰实拍"),
    "CHASSIS_DETAIL_CAPTURE": ("底盘实拍", "底盘结构", "举升机", "悬架细节", "底盘全貌"),
    "CTA": ("CTA", "到店转化", "到店引导"),
    "RISK_CONTROL": ("禁止表达", "红线", "风险", "不得"),
    "MATERIAL_RETURN": ("素材回传", "交付格式", "素材上传"),
}


def classify_bf_profile(segments):
    text = "\n".join(str(item.get("text") or "") for item in segments)
    normalized = text.lower()
    scores = {
        code: sum(1 for keyword in rule["keywords"] if keyword.lower() in normalized)
        for code, rule in PROFILE_RULES.items()
    }
    intents = [
        code for code, keywords in INTENT_RULES.items()
        if any(keyword.lower() in normalized for keyword in keywords)
    ]
    explicit = next(
        (
            code for code, rule in PROFILE_RULES.items()
            if rule["label"].lower() in normalized
            or (code == "HIGH_END_PHOTOGRAPHY" and "高质感摄影" in text)
            or (code == "STORE_VISIT" and "探店bf" in normalized)
            or (code == "CLOUD_REVIEW" and ("云评bf" in normalized or "口播bf" in normalized))
        ),
        None,
    )
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    top_code, top_score = ranked[0]
    second_score = ranked[1][1]
    mixed_signal = sum(
        intent in intents
        for intent in ("FEMALE_EXPERIENCE", "COMPETITOR_COMPARISON", "DYNAMIC_MATERIAL_CAPTURE", "CHASSIS_DETAIL_CAPTURE", "STORE_VISIT_SCRIPT", "VOICEOVER_LOGIC", "VISUAL_TONE")
    ) >= 3
    if explicit:
        primary = explicit
    elif top_score >= 4 and top_score >= second_score + 2 and not mixed_signal:
        primary = top_code
    else:
        primary = "CUSTOM"
    confidence = min(0.98, 0.42 + top_score * 0.08) if primary != "CUSTOM" else min(0.82, 0.45 + len(intents) * 0.04)
    labels = []
    for intent, label in (
        ("FEMALE_EXPERIENCE", "女性体验"),
        ("COMPETITOR_COMPARISON", "竞品对比"),
        ("DYNAMIC_MATERIAL_CAPTURE", "动态素材"),
        ("STORE_VISIT_SCRIPT", "探店"),
        ("VOICEOVER_LOGIC", "口播"),
        ("VISUAL_TONE", "视觉"),
    ):
        if intent in intents:
            labels.append(label)
    suggested_name = PROFILE_RULES.get(primary, {}).get("label") or ("+".join(labels[:3]) + "商业化内容BF" if labels else "自定义商业化内容BF")
    reasons = [f"{PROFILE_RULES[code]['label']}关键词命中{score}项" for code, score in ranked if score]
    return {
        "primaryCode": primary,
        "primaryLabel": PROFILE_RULES.get(primary, {}).get("label", "自定义BF"),
        "suggestedName": suggested_name,
        "confidence": round(confidence, 2),
        "contentIntents": intents,
        "scores": scores,
        "reasons": reasons or ["已识别为自定义BF需求"],
    }


def extract_brief(segments, document):
    profile = classify_bf_profile(segments)
    payload = new_brief_payload(
        project_id=document.get("projectId", ""),
        client_key=document.get("clientKey", ""),
        file_name=document.get("fileName", ""),
    )
    payload["document"].update(document)
    payload["classification"].update(
        {
            "bfType": profile["primaryCode"],
            "bfTypeLabel": profile["primaryLabel"],
            "confidence": profile["confidence"],
            "reasons": profile["reasons"],
            "contentIntents": profile["contentIntents"],
        }
    )
    payload["strategy"]["bfType"] = profile["primaryCode"]
    payload["summary"] = "；".join(_lines(segments)[:3])[:500]

    mapping = {
        "/strategy/bfName": ("strategy", "bfName", ("BF名称", "Brief名称", "项目名称"), False),
        "/strategy/brand": ("strategy", "brand", ("品牌",), False),
        "/strategy/model": ("strategy", "model", ("车型",), False),
        "/strategy/competitors": ("strategy", "competitors", ("竞品", "核心竞品"), True),
        "/strategy/projectStage": ("strategy", "projectStage", ("项目阶段", "传播阶段"), False),
        "/strategy/communicationGoals": ("strategy", "communicationGoals", ("传播目标",), True),
        "/strategy/targetAudience": ("strategy", "targetAudience", ("目标用户", "目标人群", "TA"), True),
        "/strategy/userPainPoints": ("strategy", "userPainPoints", ("用户痛点",), True),
        "/strategy/userBenefits": ("strategy", "userBenefits", ("用户利益点", "用户利益"), True),
        "/product/coreSellingPoints": ("product", "coreSellingPoints", ("核心产品卖点", "核心卖点"), True),
        "/product/mustSay": ("product", "mustSay", ("必须表达", "必须露出"), True),
        "/content/contentDirections": ("content", "contentDirections", ("内容方向",), True),
        "/content/topicDirections": ("content", "topicDirections", ("话题方向",), True),
        "/content/scriptFramework": ("content", "scriptFramework", ("脚本框架",), True),
        "/execution/deliveryFormats": ("execution", "deliveryFormats", ("交付格式",), True),
    }
    for pointer, (group, key, labels, multiple) in mapping.items():
        value, source = _find_label_value(segments, labels)
        if not value:
            continue
        payload[group][key] = _split_terms(value) if multiple else value
        payload["provenance"][pointer] = [_citation(document, source)]

    if not payload["strategy"]["bfName"]:
        payload["strategy"]["bfName"] = profile["suggestedName"]
    execution_lines = _matching_lines(segments, ("拍摄", "车辆", "车务", "素材", "交付", "回传", "补拍"))
    payload["execution"]["executionChecklist"] = [
        {"item": line, "priority": "MUST", "owner": "", "status": "PENDING", "sourceRefs": []}
        for line, _ in execution_lines
    ]
    dynamic = [(line, item) for line, item in execution_lines if any(keyword in line for keyword in ("动态", "路跑", "试驾"))]
    payload["execution"]["dynamicMaterialRequirements"] = [line for line, _ in dynamic]
    if dynamic:
        payload["provenance"]["/execution/dynamicMaterialRequirements"] = [_citation(document, item) for _, item in dynamic]

    risk_lines = _matching_lines(segments, ("禁止", "不得", "红线", "风险", "不允许"))
    payload["risk"]["prohibitedExpressions"] = [line for line, _ in risk_lines]
    payload["risk"]["expressionRedLines"] = [line for line, _ in risk_lines]
    if risk_lines:
        payload["provenance"]["/risk/prohibitedExpressions"] = [_citation(document, item) for _, item in risk_lines]
    price_value, price_source = _find_label_value(segments, ("是否允许聊价格", "允许聊价格"))
    if price_value:
        payload["risk"]["isPriceAllowed"] = _parse_bool(price_value)
        payload["provenance"]["/risk/isPriceAllowed"] = [_citation(document, price_source)]

    payload["materials"] = _extract_materials(segments, document, payload["provenance"])
    payload["tags"] = build_tags(payload)
    validate_brief_payload(payload)
    return payload


def build_tags(payload):
    classification = payload.get("classification") or {}
    strategy = payload.get("strategy") or {}
    product = payload.get("product") or {}
    content = payload.get("content") or {}
    execution = payload.get("execution") or {}
    risk = payload.get("risk") or {}
    materials = payload.get("materials") or []
    return {
        "bfTypes": _unique([classification.get("bfType")]),
        "brands": _unique([strategy.get("brand")]),
        "models": _unique([strategy.get("model")]),
        "competitors": _unique(strategy.get("competitors") or []),
        "projectStages": _unique([strategy.get("projectStage")]),
        "communicationGoals": _unique(strategy.get("communicationGoals") or []),
        "creatorTypes": _unique(content.get("creatorTypes") or []),
        "contentFormats": _unique((content.get("contentTypes") or []) + (classification.get("contentIntents") or [])),
        "sellingPoints": _unique(product.get("coreSellingPoints") or []),
        "userPainPoints": _unique(strategy.get("userPainPoints") or []),
        "topicDirections": _unique(content.get("topicDirections") or []),
        "shootingScenes": _unique(execution.get("locationRequirements") or []),
        "conversionGoals": _unique(strategy.get("communicationGoals") or []),
        "reviewRisks": _unique(risk.get("expressionRedLines") or []),
        "materialTypes": _unique([item.get("materialType") for item in materials]),
        "sampleGrade": str((payload.get("tags") or {}).get("sampleGrade") or "NORMAL"),
    }


def _find_label_value(segments, labels):
    for item in segments:
        for line in str(item.get("text") or "").splitlines():
            for label in labels:
                match = re.match(rf"^\s*[-•]?\s*{re.escape(label)}\s*[:：]\s*(.+?)\s*$", line, re.I)
                if match:
                    return match.group(1).strip(), item
    return "", None


def _matching_lines(segments, keywords):
    rows = []
    for item in segments:
        for line in str(item.get("text") or "").splitlines():
            clean = re.sub(r"^\s*[-•]\s*", "", line).strip()
            if clean and any(keyword in clean for keyword in keywords):
                rows.append((clean, item))
    return rows


def _extract_materials(segments, document, provenance):
    materials = []
    for item in segments:
        for match in re.finditer(r"https?://[^\s，。；;]+", str(item.get("text") or "")):
            url = match.group(0).rstrip(").,，。")
            host = urlparse(url).netloc.lower()
            material_type = "BAIDU_NETDISK" if "pan.baidu" in host else "DOUYIN" if "douyin" in host else "BILIBILI" if "bilibili" in host else "OFFICIAL_DOCUMENT"
            materials.append({"materialType": material_type, "name": host or "外部资料", "url": url, "purpose": "", "permissionNote": "", "extractionCode": "", "isPublic": None})
            provenance.setdefault(f"/materials/{len(materials)-1}/url", []).append(_citation(document, item))
    return materials


def _citation(document, segment):
    segment = segment or {}
    page = segment.get("pageNo") or segment.get("slideNo")
    paragraph = segment.get("paragraphNo")
    sheet = segment.get("sheetName")
    cell_range = segment.get("cellRange")
    if sheet:
        locator = f"工作表{sheet}/{cell_range or '内容区'}"
    elif page and paragraph:
        locator = f"第{page}页/段落{paragraph}"
    elif page:
        locator = f"第{page}页"
    elif paragraph:
        locator = f"段落{paragraph}"
    else:
        locator = json_locator(segment.get("locator") or {})
    return {
        "originType": "EXTRACTED",
        "sourceDocumentId": str(document.get("documentId") or ""),
        "sourceSegmentId": str(segment.get("id") or ""),
        "sourceLocator": locator,
        "sourceFieldPath": "",
        "excerpt": str(segment.get("text") or "")[:240],
        "confidence": 0.82,
        "isManual": False,
    }


def json_locator(locator):
    if not locator:
        return "来源位置待确认"
    return "/".join(f"{key}={value}" for key, value in locator.items())


def _lines(segments):
    rows = []
    for item in segments:
        rows.extend(line.strip() for line in str(item.get("text") or "").splitlines() if line.strip())
    return rows


def _split_terms(value):
    return _unique(re.split(r"[、,，/|｜;；]+", str(value or "")))


def _unique(values):
    result = []
    for value in values or []:
        clean = str(value or "").strip()
        if clean and clean not in result:
            result.append(clean)
    return result


def _parse_bool(value):
    text = str(value or "").strip().lower()
    if text in {"是", "允许", "可以", "true", "yes", "1"}:
        return True
    if text in {"否", "不允许", "不可以", "false", "no", "0"}:
        return False
    return None
