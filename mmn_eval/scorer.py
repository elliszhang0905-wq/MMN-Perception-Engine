"""Deterministic hard gates and weighted scoring for MMN Eval."""

from .contracts import normalize_case, normalize_output
from .rubric import DIMENSIONS, HARD_GATES, RUBRIC_VERSION, THRESHOLDS


def _ordered_unique(values):
    return list(dict.fromkeys(values))


def _evidence_index(case):
    return {item["id"]: item for item in case["input"]["evidence"]}


def _cited_evidence_ids(output):
    return {
        evidence_id
        for claim in output["claims"]
        for evidence_id in claim["evidenceIds"]
    }


def _hard_gate_failures(case, output):
    failures = []
    flags = output["flags"]
    evidence_by_id = _evidence_index(case)
    allowed_evidence_ids = set(evidence_by_id)
    cited_evidence_ids = _cited_evidence_ids(output)

    if flags.get("fabricatedFact") or any(
        claim["statementType"] == "fact" and not claim["evidenceIds"]
        for claim in output["claims"]
    ):
        failures.append("fabricated_fact")
    if cited_evidence_ids - allowed_evidence_ids:
        failures.append("unknown_evidence")
    if flags.get("missingAsZero"):
        failures.append("missing_as_zero")
    if flags.get("platformSignalOverreach"):
        failures.append("platform_signal_overreach")

    expected = case["expected"]
    required_types = set(expected.get("requiredStatementTypes") or [])
    actual_types = {claim["statementType"] for claim in output["claims"]}
    if required_types - actual_types:
        failures.append("statement_types_missing")

    required_providers = set(expected.get("requiredProviders") or [])
    completed_providers = set(output["modelValidation"].get("completedProviders") or [])
    common_evidence_ids = set(output["modelValidation"].get("commonEvidenceIds") or [])
    provider_validation_complete = required_providers.issubset(completed_providers)
    common_evidence_valid = bool(common_evidence_ids) and common_evidence_ids.issubset(allowed_evidence_ids)
    if case["taskType"] == "vehicle_configuration":
        vehicle_providers = {"qwen", "deepseek", "kimi"}
        if not vehicle_providers.issubset(completed_providers) or not common_evidence_valid:
            failures.append("vehicle_validation_incomplete")
    elif required_providers and (not provider_validation_complete or not common_evidence_valid):
        failures.append("incomplete_model_validation")

    minimum_sources = expected.get("minimumIndependentSources")
    if minimum_sources:
        source_groups = {
            evidence_by_id[evidence_id]["sourceGroup"]
            for evidence_id in cited_evidence_ids & allowed_evidence_ids
        }
        if len(source_groups) < minimum_sources:
            failures.append("source_independence_missing")

    return _ordered_unique(failures)


def _dimension_result(output):
    observed_weight = 0
    weighted_score = 0.0
    missing = []
    values = {}
    for name, definition in DIMENSIONS.items():
        value = output["dimensions"].get(name)
        values[name] = value
        if value is None:
            missing.append(name)
            continue
        weight = definition["weight"]
        observed_weight += weight
        weighted_score += value * weight
    score = round(weighted_score / observed_weight * 100, 2) if observed_weight else None
    return values, score, round(observed_weight / 100, 2), missing


def score_case(raw_case, raw_output):
    case = normalize_case(raw_case)
    output = normalize_output(raw_output)
    if output["caseId"] != case["id"]:
        raise ValueError(f"output caseId {output['caseId']} does not match case {case['id']}")

    hard_gate_failures = _hard_gate_failures(case, output)
    dimensions, score, coverage, missing_dimensions = _dimension_result(output)
    human_review_reasons = [f"评分维度不完整：{name}" for name in missing_dimensions]

    if hard_gate_failures:
        verdict = "fail"
    elif missing_dimensions or score is None:
        verdict = "human_review"
    elif score >= THRESHOLDS["pass"]:
        verdict = "pass"
    elif score >= THRESHOLDS["human_review"]:
        verdict = "human_review"
        human_review_reasons.append("总分处于人工复核区间")
    else:
        verdict = "fail"

    return {
        "caseId": case["id"],
        "taskType": case["taskType"],
        "rubricVersion": RUBRIC_VERSION,
        "score": score,
        "verdict": verdict,
        "hardGateFailures": hard_gate_failures,
        "hardGateMessages": [HARD_GATES[name] for name in hard_gate_failures],
        "dimensions": dimensions,
        "dimensionCoverage": coverage,
        "humanReviewReasons": _ordered_unique(human_review_reasons),
    }
