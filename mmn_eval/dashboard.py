"""Dashboard-facing MMN Eval report and human-review services."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from .runner import evaluate_dataset, load_jsonl


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.getenv("MMN_DATA_ROOT", str(ROOT / "data"))).expanduser().resolve()
OUTPUT_ROOT = Path(os.getenv("MMN_OUTPUT_ROOT", str(ROOT / "output"))).expanduser().resolve()
DEFAULT_CASES_PATH = Path(
    os.getenv("MMN_EVAL_CASES_PATH", str(DATA_ROOT / "eval" / "mmn_eval_seed_v0.1.jsonl"))
).expanduser().resolve()
DEFAULT_OUTPUTS_PATH = Path(
    os.getenv("MMN_EVAL_OUTPUTS_PATH", str(DATA_ROOT / "eval" / "mmn_eval_seed_outputs_v0.1.jsonl"))
).expanduser().resolve()
DEFAULT_REPORT_PATH = Path(
    os.getenv("MMN_EVAL_REPORT_PATH", str(OUTPUT_ROOT / "mmn-eval-seed-report.json"))
).expanduser().resolve()
DEFAULT_REVIEWS_PATH = Path(
    os.getenv("MMN_EVAL_REVIEWS_PATH", str(DATA_ROOT / "eval" / "mmn_eval_human_reviews.json"))
).expanduser().resolve()

_REVIEWS_LOCK = Lock()


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json_atomic(path, payload):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(f"{target.suffix}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def _load_reviews(path):
    target = Path(path)
    if not target.exists():
        return []
    payload = _read_json(target)
    if not isinstance(payload, list):
        raise ValueError("MMN Eval 人工复核记录必须是 JSON 数组")
    return [item for item in payload if isinstance(item, dict)]


def _case_lookup(cases_path):
    return {item["id"]: item for item in load_jsonl(cases_path)}


def _review_progress(results, review_by_case):
    review_case_ids = [item["caseId"] for item in results if item.get("verdict") == "human_review"]
    resolved = sum(1 for case_id in review_case_ids if case_id in review_by_case)
    return {"total": len(review_case_ids), "resolved": resolved, "pending": len(review_case_ids) - resolved}


def _comparison_payload(report):
    if report.get("reportType") != "comparison":
        return None
    return {
        "releaseVerdict": report.get("releaseVerdict"),
        "baseline": report.get("baseline"),
        "candidate": report.get("candidate"),
        "regressions": report.get("regressions") or [],
        "fixedCases": report.get("fixedCases") or [],
        "caseComparisons": report.get("caseComparisons") or [],
    }


def load_dashboard_payload(
    report_path=DEFAULT_REPORT_PATH,
    cases_path=DEFAULT_CASES_PATH,
    reviews_path=DEFAULT_REVIEWS_PATH,
    *,
    outputs_path=DEFAULT_OUTPUTS_PATH,
    org_id="local",
):
    if not Path(report_path).exists():
        report = evaluate_dataset(
            load_jsonl(cases_path),
            load_jsonl(outputs_path),
            run_name="seed-v0.1",
        )
        _write_json_atomic(report_path, report)
    report = _read_json(report_path)
    cases_by_id = _case_lookup(cases_path)
    org_reviews = [item for item in _load_reviews(reviews_path) if item.get("orgId") == org_id]
    review_by_case = {item.get("caseId"): item for item in org_reviews if item.get("caseId")}
    dashboard_cases = []
    for result in report.get("results") or report.get("candidate", {}).get("results") or []:
        case_id = result.get("caseId")
        case = cases_by_id.get(case_id, {})
        dashboard_cases.append(
            {
                **result,
                "question": str(case.get("input", {}).get("question") or ""),
                "tags": list(case.get("tags") or []),
                "humanDecision": review_by_case.get(case_id),
            }
        )
    source_kind = "seed_fixture" if str(report.get("runName") or "").startswith("seed") else "evaluation_report"
    return {
        "report": report,
        "cases": dashboard_cases,
        "comparison": _comparison_payload(report),
        "reviewProgress": _review_progress(dashboard_cases, review_by_case),
        "sourceKind": source_kind,
        "reviews": org_reviews,
    }


def run_seed_dashboard(
    cases_path=DEFAULT_CASES_PATH,
    outputs_path=DEFAULT_OUTPUTS_PATH,
    report_path=DEFAULT_REPORT_PATH,
    reviews_path=DEFAULT_REVIEWS_PATH,
    *,
    org_id="local",
):
    report = evaluate_dataset(
        load_jsonl(cases_path),
        load_jsonl(outputs_path),
        run_name="seed-v0.1",
    )
    _write_json_atomic(report_path, report)
    return load_dashboard_payload(
        report_path,
        cases_path,
        reviews_path,
        outputs_path=outputs_path,
        org_id=org_id,
    )


def save_human_review(
    case_id,
    decision,
    note,
    report_path=DEFAULT_REPORT_PATH,
    reviews_path=DEFAULT_REVIEWS_PATH,
    *,
    org_id="local",
    reviewer="local-human",
):
    case_id = str(case_id or "").strip()
    decision = str(decision or "").strip()
    note = str(note or "").strip()
    if decision not in {"approved", "rejected"}:
        raise ValueError("人工结论必须是 approved 或 rejected")
    if decision == "rejected" and not note:
        raise ValueError("驳回时请填写人工依据")
    report = _read_json(report_path)
    results = report.get("results") or report.get("candidate", {}).get("results") or []
    result_by_id = {item.get("caseId"): item for item in results}
    if case_id not in result_by_id or result_by_id[case_id].get("verdict") != "human_review":
        raise ValueError("该案例不在人工复核队列")
    review = {
        "orgId": str(org_id or "local"),
        "caseId": case_id,
        "decision": decision,
        "note": note,
        "reviewer": str(reviewer or "local-human"),
        "decidedAt": datetime.now(timezone.utc).isoformat(),
        "rubricVersion": report.get("rubricVersion"),
        "runName": report.get("runName") or "candidate",
    }
    with _REVIEWS_LOCK:
        reviews = _load_reviews(reviews_path)
        reviews = [
            item
            for item in reviews
            if not (item.get("orgId") == review["orgId"] and item.get("caseId") == case_id)
        ]
        reviews.append(review)
        _write_json_atomic(reviews_path, reviews)
    return {"ok": True, "review": review}
