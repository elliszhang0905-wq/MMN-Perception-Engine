"""Central model-routing and validation contract for MMN decision surfaces.

The contract deliberately separates deterministic facts from model judgment.
Models never call one another: the MMN orchestrator gives independent reviewers
the same evidence packet and applies deterministic publication gates.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from copy import deepcopy
from datetime import datetime, timezone


GOVERNANCE_VERSION = "mmn-model-governance-v1.0"

MODEL_ROLES = {
    "fact_owner": {"provider": "deterministic", "purpose": "锁定事实、指标和规则计算"},
    "reasoning_lead": {"provider": "deepseek", "purpose": "策略推理、反事实和压力测试"},
    "business_editor": {"provider": "qwen", "purpose": "中文业务表达、结构完整性和交付检查"},
    "evidence_auditor": {"provider": "kimi", "purpose": "长证据审计、争议升级和发布前裁决"},
}

TASK_ROUTER_POLICIES = {
    "strategy_reasoning": {
        "primary": "deepseek", "reviewer": "qwen", "auditor": "kimi",
        "auditorMode": "on_conflict", "label": "MMN策略推理模型",
    },
    "content_delivery": {
        "primary": "qwen", "reviewer": "", "auditor": "kimi",
        "auditorMode": "long_context_only", "label": "MMN中文交付快速模型",
    },
    "fact_explanation": {
        "primary": "rag", "reviewer": "qwen", "auditor": "kimi",
        "auditorMode": "source_dispute_only", "label": "MMN事实解释模型",
    },
    "vehicle_configuration_fact": {
        "primary": "rag", "reviewer": "qwen+deepseek+kimi", "auditor": "kimi",
        "auditorMode": "always", "label": "MMN汽车配置三模型验证",
    },
    "data_summary": {
        "primary": "qwen", "reviewer": "", "auditor": "",
        "auditorMode": "not_default", "label": "MMN标签摘要快速模型",
    },
    "fast_strategy": {
        "primary": "deepseek", "reviewer": "qwen", "auditor": "kimi",
        "auditorMode": "on_conflict", "label": "MMN快速策略",
    },
    "complex_strategy": {
        "primary": "deepseek", "reviewer": "qwen", "auditor": "kimi",
        "auditorMode": "on_conflict_or_final_publish", "label": "MMN深度策略",
    },
}

INDEPENDENCE_PROTOCOL = {
    "sameEvidencePacket": True,
    "blindIndependentFirstPass": True,
    "modelsMayCallEachOther": False,
    "modelsMaySeePeerOutputBeforeFirstPass": False,
    "structuredOutputRequired": True,
    "commonEvidenceRequired": True,
    "orchestratorOwnsAggregation": True,
    "failureRule": "任一必需复核缺失、证据不共同或置信度不足时，不发布最终结论并进入人工复核。",
}

STATE_TRANSITIONS = {
    "draft": ("insufficient_evidence", "evidence_ready"),
    "insufficient_evidence": ("evidence_ready", "manual_required"),
    "evidence_ready": ("reviewing", "published"),
    "reviewing": ("aligned", "manual_required", "degraded"),
    "aligned": ("published", "reviewing"),
    "manual_required": ("reviewing", "published"),
    "degraded": ("reviewing", "manual_required"),
    "published": ("reviewing",),
}

RUNTIME_GUARDRAILS = {
    "timeoutsSeconds": {"fast": 60, "deep": 120, "evidenceAudit": 180},
    "cacheTtlSeconds": 900,
    "maxConcurrentProviders": 3,
    "maxAuditorCallsPerDecision": 1,
    "perDecisionBudgetUnits": 6,
    "dailyBudgetUnits": 1000,
    "degradationOrder": ["reuse_fingerprint_cache", "return_evidence_only", "manual_required"],
    "neverDegradeTo": ["invented_agreement", "model_memory_as_fact", "silent_provider_substitution"],
}

EVAL_CONTRACT = {
    "releaseGate": "offline_final_output",
    "metrics": {
        "factualAccuracy": {"minimum": 0.98, "owner": "deterministic_fact_layer"},
        "evidenceCoverage": {"minimum": 1.0, "owner": "publication_gate"},
        "unsupportedClaimRate": {"maximum": 0.0, "owner": "publication_gate"},
        "strategyExecutability": {"minimum": 0.80, "owner": "human_eval"},
        "conflictRecall": {"minimum": 0.90, "owner": "cross_validation"},
        "humanOverrideRate": {"monitorOnly": True, "owner": "product_manager"},
        "p95FirstResultSeconds": {"maximum": 8.0, "owner": "runtime"},
        "p95FinalReviewSeconds": {"maximum": 180.0, "owner": "runtime"},
        "costUnitsPerAcceptedDecision": {"maximum": 6.0, "owner": "runtime"},
    },
    "humanFinalAuthority": True,
}

EXPERIMENT_CONTRACT = {
    "name": "cockpit-risk-adaptive-2plus1",
    "control": "current_dual_review",
    "treatment": "risk_adaptive_dual_plus_auditor",
    "allocation": {"control": 50, "treatment": 50},
    "minimumDecisionsPerArm": 100,
    "primaryMetric": "humanAcceptedWithoutRewriteRate",
    "guardrails": [
        "unsupportedClaimRate",
        "p95FirstResultSeconds",
        "p95FinalReviewSeconds",
        "costUnitsPerAcceptedDecision",
    ],
    "stopConditions": [
        "出现无证据发布",
        "人工改判率较对照组上升超过5个百分点",
        "单个已接受决策成本超过预算上限",
    ],
}


def _surface(*, label, risk, fact_owner, default_mode, primary_role, reviewer_roles,
             auditor_mode, escalation_triggers, publication_gate, budget_units, eval_focus):
    return {
        "label": label,
        "risk": risk,
        "factOwner": fact_owner,
        "defaultMode": default_mode,
        "primaryRole": primary_role,
        "reviewerRoles": list(reviewer_roles),
        "auditorMode": auditor_mode,
        "escalationTriggers": list(escalation_triggers),
        "publicationGate": publication_gate,
        "budgetUnits": budget_units,
        "evalFocus": list(eval_focus),
    }


COCKPIT_SURFACE_POLICIES = {
    "brief": _surface(
        label="高管摘要", risk="critical", fact_owner="deterministic_fact_layer",
        default_mode="dual_async", primary_role="reasoning_lead", reviewer_roles=("business_editor",),
        auditor_mode="on_conflict", escalation_triggers=("review_conflict", "confidence_below_0_70", "executive_publish"),
        publication_gate="dual_aligned_or_audited", budget_units=5,
        eval_focus=("factualAccuracy", "evidenceCoverage", "strategyExecutability"),
    ),
    "implication": _surface(
        label="集团影响", risk="high", fact_owner="deterministic_fact_layer",
        default_mode="dual_async", primary_role="reasoning_lead", reviewer_roles=("business_editor",),
        auditor_mode="on_conflict", escalation_triggers=("review_conflict", "confidence_below_0_65", "cross_brand_claim"),
        publication_gate="dual_aligned_or_audited", budget_units=5,
        eval_focus=("evidenceCoverage", "strategyExecutability", "conflictRecall"),
    ),
    "warning": _surface(
        label="销量预警", risk="critical", fact_owner="deterministic_sales_rules",
        default_mode="deterministic_plus_dual_qa", primary_role="fact_owner", reviewer_roles=("business_editor", "reasoning_lead"),
        auditor_mode="dispute_only", escalation_triggers=("review_conflict", "threshold_dispute", "source_mismatch"),
        publication_gate="deterministic_facts_and_dual_qa", budget_units=4,
        eval_focus=("factualAccuracy", "unsupportedClaimRate", "conflictRecall"),
    ),
    "market": _surface(
        label="赛道环境", risk="medium", fact_owner="deterministic_market_metrics",
        default_mode="single_summary", primary_role="business_editor", reviewer_roles=(),
        auditor_mode="not_default", escalation_triggers=("high_stakes", "review_conflict", "source_mismatch"),
        publication_gate="deterministic_facts", budget_units=2,
        eval_focus=("factualAccuracy", "evidenceCoverage"),
    ),
    "policy": _surface(
        label="政策环境", risk="critical", fact_owner="reviewed_policy_rule_engine",
        default_mode="triple_parallel", primary_role="reasoning_lead", reviewer_roles=("business_editor", "evidence_auditor"),
        auditor_mode="always", escalation_triggers=("always",),
        publication_gate="three_independent_common_evidence", budget_units=6,
        eval_focus=("factualAccuracy", "evidenceCoverage", "unsupportedClaimRate", "conflictRecall"),
    ),
    "competitive": _surface(
        label="传播势能", risk="high", fact_owner="traceable_content_evidence",
        default_mode="dual_async", primary_role="business_editor", reviewer_roles=("reasoning_lead",),
        auditor_mode="long_context_or_conflict", escalation_triggers=("long_context", "review_conflict", "confidence_below_0_65"),
        publication_gate="dual_aligned_or_audited", budget_units=5,
        eval_focus=("evidenceCoverage", "strategyExecutability"),
    ),
    "platform": _surface(
        label="平台阵地", risk="medium", fact_owner="deterministic_platform_metrics",
        default_mode="single_summary", primary_role="business_editor", reviewer_roles=(),
        auditor_mode="not_default", escalation_triggers=("high_stakes", "cross_platform_conflict"),
        publication_gate="deterministic_facts", budget_units=2,
        eval_focus=("factualAccuracy", "evidenceCoverage"),
    ),
    "attribute": _surface(
        label="产品用户之声", risk="high", fact_owner="traceable_voice_evidence",
        default_mode="dual_async", primary_role="business_editor", reviewer_roles=("reasoning_lead",),
        auditor_mode="long_context_or_conflict", escalation_triggers=("long_context", "review_conflict", "confidence_below_0_65"),
        publication_gate="dual_aligned_or_audited", budget_units=5,
        eval_focus=("evidenceCoverage", "unsupportedClaimRate", "strategyExecutability"),
    ),
}


def runtime_guardrails():
    """Return runtime limits with environment overrides, without exposing secrets."""
    result = deepcopy(RUNTIME_GUARDRAILS)
    overrides = {
        "cacheTtlSeconds": ("MMN_MODEL_GOVERNANCE_CACHE_TTL", 60, 86400),
        "perDecisionBudgetUnits": ("MMN_MODEL_DECISION_BUDGET_UNITS", 1, 20),
        "dailyBudgetUnits": ("MMN_MODEL_DAILY_BUDGET_UNITS", 1, 100000),
    }
    for key, (env_key, minimum, maximum) in overrides.items():
        try:
            value = int(os.getenv(env_key, result[key]))
        except (TypeError, ValueError):
            continue
        result[key] = max(minimum, min(maximum, value))
    return result


def assign_experiment_arm(subject_key):
    digest = hashlib.sha256(str(subject_key or "local").encode("utf-8")).hexdigest()
    return "control" if int(digest[:8], 16) % 100 < 50 else "treatment"


def _triggered(policy, context):
    context = context or {}
    triggers = set(policy["escalationTriggers"])
    confidence = float(context.get("confidence", 1.0) or 0.0)
    return bool(
        "always" in triggers
        or ("review_conflict" in triggers and context.get("conflict") is True)
        or ("high_stakes" in triggers and context.get("highStakes") is True)
        or ("long_context" in triggers and (context.get("longContext") is True or int(context.get("evidenceCount", 0) or 0) > 8))
        or ("source_mismatch" in triggers and context.get("sourceMismatch") is True)
        or ("threshold_dispute" in triggers and context.get("thresholdDispute") is True)
        or ("cross_platform_conflict" in triggers and context.get("crossPlatformConflict") is True)
        or ("cross_brand_claim" in triggers and context.get("crossBrandClaim") is True)
        or ("executive_publish" in triggers and context.get("publishFinal") is True)
        or ("confidence_below_0_70" in triggers and confidence < 0.70)
        or ("confidence_below_0_65" in triggers and confidence < 0.65)
    )


def resolve_surface_route(surface, context=None):
    if surface not in COCKPIT_SURFACE_POLICIES:
        raise KeyError("未知的决策驾驶舱板块")
    context = context or {}
    policy = deepcopy(COCKPIT_SURFACE_POLICIES[surface])
    evidence_count = max(0, int(context.get("evidenceCount", 0) or 0))
    auditor_required = policy["auditorMode"] == "always" or _triggered(policy, context)
    roles = [policy["primaryRole"], *policy["reviewerRoles"]]
    if auditor_required and "evidence_auditor" not in roles:
        roles.append("evidence_auditor")
    roles = list(dict.fromkeys(roles))
    budget = runtime_guardrails()["perDecisionBudgetUnits"]
    reasons = [f"板块风险={policy['risk']}", f"默认模式={policy['defaultMode']}"]
    if auditor_required:
        reasons.append("命中证据审计升级条件")
    if evidence_count == 0:
        state = "insufficient_evidence"
        reasons.append("没有可追溯证据")
    elif context.get("providerUnavailable"):
        state = "degraded"
        reasons.append("必需能力暂不可用")
    elif context.get("conflict") is True:
        state = "reviewing" if auditor_required else "manual_required"
        reasons.append("独立判断存在冲突")
    else:
        state = str(context.get("state") or "evidence_ready")
    estimated_units = min(budget, max(0, policy["budgetUnits"]))
    return {
        "contractVersion": GOVERNANCE_VERSION,
        "surface": surface,
        "surfaceLabel": policy["label"],
        "risk": policy["risk"],
        "factOwner": policy["factOwner"],
        "mode": policy["defaultMode"],
        "roles": roles,
        "auditorRequired": auditor_required,
        "publicationGate": policy["publicationGate"],
        "state": state,
        "estimatedBudgetUnits": estimated_units,
        "decisionReasons": reasons,
    }


def transition_state(current, target):
    if current == target:
        return target
    if target not in STATE_TRANSITIONS.get(current, ()):
        raise ValueError(f"不允许的模型治理状态转换：{current} -> {target}")
    return target


def evidence_packet_fingerprint(payload):
    encoded = json.dumps(payload or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_governance_trace(surface, evidence_packet, context=None):
    route = resolve_surface_route(surface, {**(context or {}), "evidenceCount": len((evidence_packet or {}).get("evidenceIds") or [])})
    return {
        "traceId": str(uuid.uuid4()),
        "contractVersion": GOVERNANCE_VERSION,
        "surface": surface,
        "packetFingerprint": evidence_packet_fingerprint(evidence_packet),
        "route": route,
        "createdAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "requiredObservability": [
            "route_reason", "evidence_ids", "provider_status", "latency_ms", "cache_hit",
            "budget_units", "conflict_status", "human_override", "final_state",
        ],
    }


def internal_model_governance_contract():
    return {
        "version": GOVERNANCE_VERSION,
        "modelRoles": deepcopy(MODEL_ROLES),
        "taskRouter": deepcopy(TASK_ROUTER_POLICIES),
        "independenceProtocol": deepcopy(INDEPENDENCE_PROTOCOL),
        "states": deepcopy(STATE_TRANSITIONS),
        "runtime": runtime_guardrails(),
        "eval": deepcopy(EVAL_CONTRACT),
        "experiment": deepcopy(EXPERIMENT_CONTRACT),
        "cockpitSurfaces": deepcopy(COCKPIT_SURFACE_POLICIES),
    }


def public_model_governance_contract():
    """Neutral external contract: no provider or vendor names are exposed."""
    surfaces = {}
    for key, policy in COCKPIT_SURFACE_POLICIES.items():
        surfaces[key] = {
            "label": policy["label"],
            "risk": policy["risk"],
            "factOwner": policy["factOwner"],
            "mode": policy["defaultMode"],
            "publicationGate": policy["publicationGate"],
            "escalationEnabled": policy["auditorMode"] != "not_default",
            "evalFocus": list(policy["evalFocus"]),
        }
    return {
        "version": GOVERNANCE_VERSION,
        "orchestration": "independent_evidence_gated",
        "modelsMayCallEachOther": False,
        "humanFinalAuthority": True,
        "states": list(STATE_TRANSITIONS),
        "surfaces": surfaces,
        "runtime": runtime_guardrails(),
        "eval": deepcopy(EVAL_CONTRACT),
        "experiment": deepcopy(EXPERIMENT_CONTRACT),
    }


def cockpit_governance_snapshot(dashboard_payload, subject_key="local"):
    payload = dashboard_payload or {}
    executive = payload.get("executiveBrief") or {}
    warning = (payload.get("salesWarnings") or {}).get("dualModelReview") or {}
    policy = payload.get("policyIntelligence") or {}
    policy_evidence = sum(
        len(((item.get("vehicleImpact") or {}).get("policyEffects") or []))
        for item in (policy.get("models") or [])
    )
    evidence_counts = {
        "brief": len((executive.get("facts") or {})),
        "implication": len(executive.get("brandImplications") or []),
        "warning": len((payload.get("salesWarnings") or {}).get("saicModels") or []),
        "market": len(payload.get("marketDimensions") or []),
        "policy": policy_evidence,
        "competitive": len(((payload.get("productEvaluation") or {}).get("models") or [])),
        "platform": len(((payload.get("productEvaluation") or {}).get("platforms") or [])),
        "attribute": len(((payload.get("productEvaluation") or {}).get("attributes") or [])),
    }
    observed_states = {
        "brief": "aligned" if executive.get("status") == "verified" else "reviewing",
        "warning": "aligned" if warning.get("status") == "verified" else "reviewing",
    }
    surfaces = {}
    for key in COCKPIT_SURFACE_POLICIES:
        route = resolve_surface_route(key, {
            "evidenceCount": evidence_counts[key],
            "state": observed_states.get(key, "evidence_ready"),
        })
        route.pop("roles", None)
        surfaces[key] = route
    return {
        "version": GOVERNANCE_VERSION,
        "experimentArm": assign_experiment_arm(subject_key),
        "orchestration": "independent_evidence_gated",
        "modelsMayCallEachOther": False,
        "surfaces": surfaces,
    }
