"""Strict input contracts for MMN evaluation datasets and candidate outputs."""

from copy import deepcopy
from math import isfinite

from .rubric import DIMENSIONS, STATEMENT_TYPES, TASK_TYPES


ALLOWED_FLAGS = frozenset({"fabricatedFact", "missingAsZero", "platformSignalOverreach"})
GRADING_SOURCES = frozenset({"human", "independent_judge", "synthetic_fixture"})


class ContractError(ValueError):
    """Raised when an evaluation artifact violates its public contract."""


def _require_mapping(value, path):
    if not isinstance(value, dict):
        raise ContractError(f"{path} must be an object")
    return value


def _require_text(value, path):
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"{path} must be a non-empty string")
    return value.strip()


def _normalize_string_list(value, path):
    if not isinstance(value, list):
        raise ContractError(f"{path} must be an array")
    normalized = []
    for index, item in enumerate(value):
        normalized.append(_require_text(item, f"{path}[{index}]"))
    if len(normalized) != len(set(normalized)):
        raise ContractError(f"{path} contains duplicate values")
    return normalized


def _normalize_evidence(value):
    if value is None:
        return []
    if not isinstance(value, list):
        raise ContractError("input.evidence must be an array")
    normalized = []
    ids = set()
    for index, item in enumerate(value):
        evidence = deepcopy(_require_mapping(item, f"input.evidence[{index}]"))
        evidence_id = _require_text(evidence.get("id"), f"input.evidence[{index}].id")
        if evidence_id in ids:
            raise ContractError("input.evidence contains duplicate evidence IDs")
        ids.add(evidence_id)
        evidence["id"] = evidence_id
        normalized.append(evidence)
    return normalized


def _normalize_expected(value):
    expected = deepcopy(_require_mapping(value, "expected"))
    expected["requiredProviders"] = _normalize_string_list(
        expected.get("requiredProviders", []), "expected.requiredProviders"
    )
    statement_types = _normalize_string_list(
        expected.get("requiredStatementTypes", []), "expected.requiredStatementTypes"
    )
    unsupported = sorted(set(statement_types) - STATEMENT_TYPES)
    if unsupported:
        raise ContractError(f"expected.requiredStatementTypes contains unsupported values: {unsupported}")
    expected["requiredStatementTypes"] = statement_types
    minimum_sources = expected.get("minimumIndependentSources")
    if minimum_sources is not None:
        if isinstance(minimum_sources, bool) or not isinstance(minimum_sources, int) or minimum_sources < 1:
            raise ContractError("expected.minimumIndependentSources must be a positive integer")
    return expected


def normalize_case(raw):
    case = deepcopy(_require_mapping(raw, "case"))
    case_id = _require_text(case.get("id"), "id")
    task_type = _require_text(case.get("taskType"), "taskType")
    if task_type not in TASK_TYPES:
        raise ContractError(f"taskType is not supported: {task_type}")
    input_payload = deepcopy(_require_mapping(case.get("input"), "input"))
    expected = _normalize_expected(case.get("expected"))
    input_payload["evidence"] = _normalize_evidence(input_payload.get("evidence"))
    if expected.get("minimumIndependentSources"):
        for index, evidence in enumerate(input_payload["evidence"]):
            evidence["sourceGroup"] = _require_text(
                evidence.get("sourceGroup"), f"input.evidence[{index}].sourceGroup"
            )
    tags = _normalize_string_list(case.get("tags", []), "tags")
    return {
        **case,
        "id": case_id,
        "taskType": task_type,
        "input": input_payload,
        "expected": expected,
        "tags": tags,
    }


def _normalize_claims(value):
    if not isinstance(value, list):
        raise ContractError("claims must be an array")
    normalized = []
    for index, item in enumerate(value):
        path = f"claims[{index}]"
        claim = deepcopy(_require_mapping(item, path))
        statement_type = _require_text(claim.get("statementType"), f"{path}.statementType")
        if statement_type not in STATEMENT_TYPES:
            raise ContractError(f"{path}.statementType is not supported: {statement_type}")
        claim["statementType"] = statement_type
        claim["text"] = _require_text(claim.get("text"), f"{path}.text")
        claim["evidenceIds"] = _normalize_string_list(claim.get("evidenceIds"), f"{path}.evidenceIds")
        normalized.append(claim)
    return normalized


def _normalize_dimensions(value):
    dimensions = deepcopy(_require_mapping(value, "dimensions"))
    normalized = {}
    for name, score in dimensions.items():
        if name not in DIMENSIONS:
            raise ContractError(f"dimensions.{name} is not supported")
        if score is None:
            normalized[name] = None
            continue
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not isfinite(score) or not 0 <= score <= 1:
            raise ContractError(f"dimensions.{name} must be null or a number between 0 and 1")
        normalized[name] = float(score)
    return normalized


def _normalize_model_validation(value):
    validation = deepcopy(_require_mapping(value, "modelValidation"))
    validation["completedProviders"] = _normalize_string_list(
        validation.get("completedProviders", []), "modelValidation.completedProviders"
    )
    validation["commonEvidenceIds"] = _normalize_string_list(
        validation.get("commonEvidenceIds", []), "modelValidation.commonEvidenceIds"
    )
    return validation


def _normalize_flags(value):
    flags = deepcopy(_require_mapping(value, "flags"))
    normalized = {}
    for name, active in flags.items():
        if name not in ALLOWED_FLAGS:
            raise ContractError(f"flags.{name} is not supported")
        if not isinstance(active, bool):
            raise ContractError(f"flags.{name} must be a boolean")
        normalized[name] = active
    return normalized


def _normalize_metadata(value, dimensions):
    metadata = deepcopy(_require_mapping(value, "metadata"))
    grading_source = metadata.get("gradingSource")
    if any(score is not None for score in dimensions.values()):
        grading_source = _require_text(grading_source, "metadata.gradingSource")
        if grading_source not in GRADING_SOURCES:
            raise ContractError(f"metadata.gradingSource is not supported: {grading_source}")
        metadata["gradingSource"] = grading_source
    elif grading_source is not None and grading_source not in GRADING_SOURCES:
        raise ContractError(f"metadata.gradingSource is not supported: {grading_source}")
    return metadata


def normalize_output(raw):
    output = deepcopy(_require_mapping(raw, "output"))
    dimensions = _normalize_dimensions(output.get("dimensions"))
    return {
        **output,
        "caseId": _require_text(output.get("caseId"), "caseId"),
        "claims": _normalize_claims(output.get("claims")),
        "dimensions": dimensions,
        "modelValidation": _normalize_model_validation(output.get("modelValidation", {})),
        "flags": _normalize_flags(output.get("flags", {})),
        "metadata": _normalize_metadata(output.get("metadata", {}), dimensions),
    }
