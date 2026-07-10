"""BF结构化知识本体和边界校验。"""

from copy import deepcopy
from datetime import datetime, timezone


BF_LAYER_NAMES = ("strategy", "product", "content", "execution", "risk", "materials")

BF_BRIEF_JSON_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://mmn.local/schemas/bf-brief-v1.json",
    "title": "MMN BF Structured Brief",
    "type": "object",
    "required": [
        "schemaVersion",
        "document",
        "classification",
        "summary",
        *BF_LAYER_NAMES,
        "tags",
        "provenance",
        "extraction",
    ],
    "properties": {
        "schemaVersion": {"const": "1.0.0"},
        "document": {"type": "object"},
        "classification": {
            "type": "object",
            "required": ["bfType", "confidence", "reasons", "contentIntents"],
        },
        "summary": {"type": "string"},
        "strategy": {"type": "object"},
        "product": {"type": "object"},
        "content": {"type": "object"},
        "execution": {"type": "object"},
        "risk": {"type": "object"},
        "materials": {"type": "array"},
        "tags": {"type": "object"},
        "provenance": {"type": "object"},
        "extraction": {"type": "object"},
    },
}


_EMPTY_BRIEF = {
    "schemaVersion": "1.0.0",
    "document": {
        "documentId": "",
        "projectId": "",
        "clientKey": "",
        "fileName": "",
        "mimeType": "",
        "checksum": "",
        "pageCount": None,
        "uploadedAt": "",
    },
    "classification": {
        "bfType": "CUSTOM",
        "bfTypeLabel": "待识别BF",
        "confidence": 0.0,
        "reasons": [],
        "contentIntents": [],
    },
    "summary": "",
    "strategy": {
        "bfName": "",
        "bfType": "CUSTOM",
        "brand": "",
        "model": "",
        "competitors": [],
        "projectBackground": "",
        "projectStage": "",
        "communicationGoals": [],
        "coreStrategyJudgment": "",
        "currentCommunicationProblem": "",
        "finalContentDirection": "",
        "targetAudience": [],
        "userPainPoints": [],
        "userBenefits": [],
    },
    "product": {
        "coreSellingPoints": [],
        "productPointCategories": [],
        "mustSay": [],
        "optionalSay": [],
        "avoidLeadingWith": [],
        "parameters": [],
        "officialClaims": [],
        "competitorClaims": [],
        "evidenceSources": [],
    },
    "content": {
        "contentTypes": [],
        "contentDirections": [],
        "topicDirections": [],
        "topicMatrix": [],
        "creatorAssignments": [],
        "creatorTypes": [],
        "scriptFramework": [],
        "openingRequirement": "",
        "middleStructure": [],
        "endingCta": "",
        "titleSuggestions": [],
        "voiceoverDirections": [],
        "cameraLanguage": [],
        "mustShoot": [],
        "mustExpose": [],
        "commentGuidance": [],
    },
    "execution": {
        "locationRequirements": [],
        "stylingRequirements": [],
        "equipmentRequirements": [],
        "weatherRequirements": [],
        "vehicleReceivingProcess": [],
        "vehicleInspectionChecklist": [],
        "vehicleCleaningRequirements": [],
        "plateAndBadgeRequirements": [],
        "configurationConfirmation": [],
        "lightAndLogoRequirements": [],
        "interiorScreenRequirements": [],
        "roadShootingRequirements": [],
        "staticMaterialRequirements": [],
        "dynamicMaterialRequirements": [],
        "materialReturnRequirements": [],
        "reshootRules": [],
        "deliveryFormats": [],
        "publishingSchedule": [],
        "executionChecklist": [],
    },
    "risk": {
        "prohibitedExpressions": [],
        "expressionRedLines": [],
        "platformReviewRisks": [],
        "trafficSafetyRisks": [],
        "legalRisks": [],
        "brandToneRisks": [],
        "aiToneRisks": [],
        "exaggerationRisks": [],
        "competitorAttackRisks": [],
        "priceBenefitLimitations": [],
        "isAdasAllowed": None,
        "isDynamicDrivingAllowed": None,
        "isPriceAllowed": None,
        "isCompetitorNameAllowed": None,
        "riskChecklist": [],
    },
    "materials": [],
    "tags": {
        "bfTypes": [],
        "brands": [],
        "models": [],
        "competitors": [],
        "projectStages": [],
        "communicationGoals": [],
        "creatorTypes": [],
        "contentFormats": [],
        "sellingPoints": [],
        "userPainPoints": [],
        "topicDirections": [],
        "shootingScenes": [],
        "conversionGoals": [],
        "reviewRisks": [],
        "materialTypes": [],
        "sampleGrade": "NORMAL",
    },
    "provenance": {},
    "extraction": {
        "parserVersion": "mmn-bf-p0",
        "extractedAt": "",
        "modelTrace": [],
        "warnings": [],
    },
}


def new_brief_payload(project_id="", client_key="", file_name=""):
    payload = deepcopy(_EMPTY_BRIEF)
    payload["document"].update(
        {
            "projectId": str(project_id or ""),
            "clientKey": str(client_key or ""),
            "fileName": str(file_name or ""),
        }
    )
    payload["extraction"]["extractedAt"] = datetime.now(timezone.utc).isoformat()
    return payload

def validate_brief_payload(payload):
    if not isinstance(payload, dict):
        raise ValueError("BF结构化结果必须是JSON对象")
    missing = [key for key in BF_BRIEF_JSON_SCHEMA["required"] if key not in payload]
    if missing:
        raise ValueError("BF结构化结果缺少字段: " + ", ".join(missing))
    for layer in ("document", "classification", "strategy", "product", "content", "execution", "risk", "tags", "provenance", "extraction"):
        if not isinstance(payload.get(layer), dict):
            raise ValueError(f"{layer}必须是JSON对象")
    if not isinstance(payload.get("materials"), list):
        raise ValueError("materials必须是数组")
    classification = payload["classification"]
    if not str(classification.get("bfType") or "").strip():
        raise ValueError("classification.bfType不能为空")
    if not isinstance(classification.get("contentIntents"), list):
        raise ValueError("classification.contentIntents必须是数组")
    grade = payload["tags"].get("sampleGrade", "NORMAL")
    if grade not in {"NORMAL", "QUALITY", "NEGATIVE", "DISABLED"}:
        raise ValueError("未知样本等级")
    return payload
