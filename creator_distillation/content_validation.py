"""Evidence-gated Qwen + DeepSeek validation for creator positioning and content DNA."""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from .opinion_judgment import _provider_call


CLAIM_SCHEMA = {
    "account_positioning": {
        "domain": "account_positioning", "label": "账号定位",
        "values": {
            "expert_education": "专家科普", "product_review": "产品评测",
            "news_commentary": "行业评论", "usage_advice": "使用建议",
            "lifestyle": "生活方式", "entertainment": "娱乐内容",
            "mixed": "混合定位", "unknown": "证据不足",
        },
    },
    "topic_focus": {
        "domain": "content_dna", "label": "核心选题",
        "values": {
            "technical_education": "技术科普", "product_review": "产品评测",
            "usage_advice": "使用建议", "industry_commentary": "行业评论",
            "lifestyle": "生活方式", "mixed": "混合选题", "unknown": "证据不足",
        },
    },
    "narrative_structure": {
        "domain": "content_dna", "label": "叙事结构",
        "values": {
            "question_answer": "问答解释", "problem_explanation": "问题拆解",
            "comparison_review": "对比评测", "demonstration": "演示验证",
            "interview": "访谈对话", "mixed": "混合结构", "unknown": "证据不足",
        },
    },
    "expression_style": {
        "domain": "content_dna", "label": "表达方式",
        "values": {
            "professional": "专业严谨", "conversational": "口语交流",
            "emotional": "情绪表达", "humorous": "幽默表达",
            "promotional": "推广表达", "mixed": "混合表达", "unknown": "证据不足",
        },
    },
    "visual_style": {
        "domain": "visual_conclusion", "label": "视觉形态",
        "values": {
            "talking_head": "人物口播", "product_demonstration": "产品演示",
            "presentation": "图文讲解", "interview": "访谈对话",
            "montage": "多镜头剪辑", "mixed": "混合视觉", "unknown": "证据不足",
        },
    },
    "shot_structure": {
        "domain": "visual_conclusion", "label": "镜头结构",
        "values": {
            "single_scene": "单场景", "multi_scene": "多场景",
            "chaptered": "章节化", "mixed": "混合镜头", "unknown": "证据不足",
        },
    },
}

VISUAL_TYPES = {"ocr", "shot", "visual_summary", "visual_structure"}


def _prompt(creator, assets, evidence):
    schema = {key: sorted(item["values"]) for key, item in CLAIM_SCHEMA.items()}
    packet = [{"evidenceId": row["id"], "sourceId": row.get("source_id"),
               "type": row.get("evidence_type"),
               "visualProvider": (row.get("provenance") or {}).get("provider"),
               "quote": str(row.get("quote_text") or "")[:500]}
              for row in evidence[:160]]
    samples = [{"sourceId": row.get("source_id"), "title": row.get("title")}
               for row in assets[:30]]
    return (
        "独立审计达人内容。只能使用给定claimKey和verdict，只能引用输入中的evidenceId；"
        "没有直接证据就不输出该claimKey，不得根据账号名称补造定位。"
        "visual_style和shot_structure只能引用type为ocr/shot/visual_summary/visual_structure的证据，"
        "并且必须同时引用visualProvider=qwen和visualProvider=kimi的独立观察证据。"
        "输出JSON：{\"claims\":[{\"claimKey\":...,\"verdict\":...,\"confidence\":0-1,"
        "\"evidenceIds\":[...],\"rationale\":...}]}。\n"
        f"达人基础字段：{json.dumps(creator, ensure_ascii=False)}\n"
        f"允许分类：{json.dumps(schema, ensure_ascii=False)}\n"
        f"作品：{json.dumps(samples, ensure_ascii=False)}\n"
        f"内容证据：{json.dumps(packet, ensure_ascii=False)}"
    )


def cross_validate_content_models(outputs, allowed_ids, visual_ids, required_domains,
                                  visual_provider_ids=None):
    enforce_visual_providers = visual_provider_ids is not None
    visual_provider_ids = visual_provider_ids or {}
    providers = {name: value for name, value in outputs.items() if isinstance(value, dict)}
    errors = {name: str(value) for name, value in outputs.items() if not isinstance(value, dict)}
    empty_domains = {domain: {"status": "manual_required", "claims": [], "reasons": []}
                     for domain in required_domains}
    if set(providers) != {"qwen", "deepseek"}:
        reason = "Qwen 与 DeepSeek 未全部完成，内容结论不得发布"
        for item in empty_domains.values(): item["reasons"].append(reason)
        return {"status": "manual_required", "completedProviders": sorted(providers),
                "providerErrors": errors, "commonEvidenceIds": [], "validatedClaims": [],
                "domains": empty_domains, "reasons": [reason], "modelOutputs": providers}

    indexed = {}
    for provider, payload in providers.items():
        indexed[provider] = {str(item.get("claimKey")): item for item in payload.get("claims") or []
                             if str(item.get("claimKey")) in CLAIM_SCHEMA}
    validated, common_all, reasons = [], set(), []
    domains = {domain: {"status": "manual_required", "claims": [], "reasons": []}
               for domain in required_domains}
    for key in sorted(set(indexed["qwen"]) & set(indexed["deepseek"])):
        schema, left, right = CLAIM_SCHEMA[key], indexed["qwen"][key], indexed["deepseek"][key]
        if schema["domain"] not in required_domains:
            continue
        left_value, right_value = str(left.get("verdict")), str(right.get("verdict"))
        permitted = set(schema["values"])
        domain_allowed = visual_ids if schema["domain"] == "visual_conclusion" else allowed_ids
        left_ids = set(map(str, left.get("evidenceIds") or [])) & domain_allowed
        right_ids = set(map(str, right.get("evidenceIds") or [])) & domain_allowed
        common = sorted(left_ids & right_ids)
        try: confidence = min(float(left.get("confidence") or 0), float(right.get("confidence") or 0))
        except (TypeError, ValueError): confidence = 0
        visual_providers_complete = True
        if schema["domain"] == "visual_conclusion" and enforce_visual_providers:
            visual_providers_complete = all(
                set(common) & set(visual_provider_ids.get(provider) or set())
                for provider in ("qwen", "kimi")
            )
        if (left_value != right_value or left_value not in permitted or not common or confidence < .6
                or not visual_providers_complete):
            reason = f"{schema['label']}：分类、共同证据或置信度未达门槛"
            reasons.append(reason); domains[schema["domain"]]["reasons"].append(reason)
            continue
        claim = {"claimKey": key, "domain": schema["domain"], "label": schema["label"],
                 "verdict": left_value, "verdictLabel": schema["values"][left_value],
                 "statementType": "inference", "confidence": round(confidence, 3),
                 "evidenceIds": common}
        validated.append(claim); common_all.update(common); domains[schema["domain"]]["claims"].append(claim)
    for domain, item in domains.items():
        if item["claims"]: item["status"] = "aligned"
        else:
            reason = f"{domain} 没有形成双模型共同证据结论"
            item["reasons"].append(reason); reasons.append(reason)
    status = "aligned" if domains and all(item["status"] == "aligned" for item in domains.values()) else "manual_required"
    return {"status": status, "completedProviders": ["qwen", "deepseek"],
            "providerErrors": errors, "commonEvidenceIds": sorted(common_all),
            "validatedClaims": validated, "domains": domains,
            "reasons": list(dict.fromkeys(reasons)), "modelOutputs": providers}


def build_creator_content_validation(creator, assets, evidence, model_runner=None, use_models=True):
    usable = [row for row in evidence if row.get("id") and row.get("evidence_type") != "comment"
              and str(row.get("quote_text") or "").strip()]
    allowed_ids = {str(row["id"]) for row in usable}
    visual_ids = {str(row["id"]) for row in usable if row.get("evidence_type") in VISUAL_TYPES}
    visual_provider_ids = {}
    for row in usable:
        provider = str((row.get("provenance") or {}).get("provider") or "")
        if provider in {"qwen", "kimi"} and str(row["id"]) in visual_ids:
            visual_provider_ids.setdefault(provider, set()).add(str(row["id"]))
    required_domains = ["account_positioning", "content_dna"]
    if visual_ids: required_domains.append("visual_conclusion")
    outputs = {}
    if use_models and usable:
        runner, prompt = model_runner or _provider_call, _prompt(creator, assets, usable)
        with ThreadPoolExecutor(max_workers=2) as pool:
            pending = {pool.submit(runner, provider, prompt): provider for provider in ("qwen", "deepseek")}
            for future in as_completed(pending):
                provider = pending[future]
                try: outputs[provider] = future.result()
                except Exception as exc: outputs[provider] = f"{type(exc).__name__}: {exc}"
    validation = cross_validate_content_models(
        outputs, allowed_ids, visual_ids, required_domains, visual_provider_ids)
    validation["visualAuditBasis"] = "text_audit_of_independently_extracted_visual_evidence"
    validation["limitations"] = [
        "双模型一致不等于事实，所有结论仍是可回溯证据支持的推断",
        "视觉结论只有在独立视觉模型提取完成后才进入本门禁",
    ]
    return validation
