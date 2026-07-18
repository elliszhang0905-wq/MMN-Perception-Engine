"""Versioned MMN evaluation policy.

Numeric dimensions measure output quality. Hard gates protect evidence and
product boundaries and therefore always override the numeric score.
"""

RUBRIC_VERSION = "mmn-eval-v0.1"

TASK_TYPES = frozenset({
    "strategy",
    "opportunity_map",
    "social_evidence",
    "content_strategy",
    "brief",
    "vehicle_configuration",
})

STATEMENT_TYPES = frozenset({"fact", "inference", "hypothesis", "unknown", "recommendation"})

DIMENSIONS = {
    "evidence": {"weight": 30, "label": "证据真实性与可追溯性"},
    "reasoning": {"weight": 25, "label": "洞察与证据一致性"},
    "actionability": {"weight": 20, "label": "策略可执行性"},
    "fit": {"weight": 15, "label": "品牌车型与场景适配"},
    "uncertainty": {"weight": 10, "label": "不确定性与边界表达"},
}

THRESHOLDS = {"pass": 80, "human_review": 65}

HARD_GATES = {
    "fabricated_fact": "输出包含当前证据无法支持的事实声明",
    "unknown_evidence": "输出引用了不存在的证据 ID",
    "missing_as_zero": "输出把缺失值或未知值写成了 0",
    "incomplete_model_validation": "任务要求的多模型复核未完整完成",
    "vehicle_validation_incomplete": "车型配置未完成 Qwen、DeepSeek、Kimi 三模型共同证据复核",
    "platform_signal_overreach": "仅凭平台传播指标推导购买需求或转化结论",
    "source_independence_missing": "可执行机会缺少独立来源组合",
    "statement_types_missing": "策略输出未区分事实、推断、假设和未知",
}
