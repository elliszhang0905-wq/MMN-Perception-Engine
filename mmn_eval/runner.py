"""Dataset execution and paired regression reports for MMN Eval."""

import json
from collections import Counter
from pathlib import Path

from .contracts import normalize_case, normalize_output
from .rubric import DIMENSIONS, RUBRIC_VERSION
from .scorer import score_case


VERDICT_RANK = {"fail": 0, "human_review": 1, "pass": 2}
MATERIAL_SCORE_DROP = 5.0


def load_jsonl(path):
    path = Path(path)
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path.name}:{line_number}: invalid JSON: {exc.msg}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"{path.name}:{line_number}: each JSONL row must be an object")
            rows.append(row)
    return rows


def _index_unique(rows, key, label):
    index = {}
    for row in rows:
        item_key = row[key]
        if item_key in index:
            raise ValueError(f"duplicate {label}: {item_key}")
        index[item_key] = row
    return index


def _summary(results):
    verdict_counts = Counter(item["verdict"] for item in results)
    gate_counts = Counter(name for item in results for name in item["hardGateFailures"])
    scores = [item["score"] for item in results if item["score"] is not None]
    dimension_values = {
        name: [item["dimensions"][name] for item in results if item["dimensions"][name] is not None]
        for name in DIMENSIONS
    }
    return {
        "evaluated": len(results),
        "pass": verdict_counts["pass"],
        "humanReview": verdict_counts["human_review"],
        "fail": verdict_counts["fail"],
        "averageScore": round(sum(scores) / len(scores), 2) if scores else None,
        "averageDimensionCoverage": round(
            sum(item["dimensionCoverage"] for item in results) / len(results), 3
        ) if results else None,
        "hardGateFailures": dict(sorted(gate_counts.items())),
        "dimensionAverages": {
            name: round(sum(values) / len(values), 3) if values else None
            for name, values in dimension_values.items()
        },
    }


def evaluate_dataset(raw_cases, raw_outputs, run_name="candidate"):
    cases = [normalize_case(item) for item in raw_cases]
    outputs = [normalize_output(item) for item in raw_outputs]
    case_by_id = _index_unique(cases, "id", "case ID")
    output_by_id = _index_unique(outputs, "caseId", "output caseId")
    missing_case_ids = sorted(set(case_by_id) - set(output_by_id))
    extra_output_case_ids = sorted(set(output_by_id) - set(case_by_id))
    results = [
        score_case(case_by_id[case_id], output_by_id[case_id])
        for case_id in sorted(set(case_by_id) & set(output_by_id))
    ]
    human_review_queue = [
        {
            "caseId": item["caseId"],
            "taskType": item["taskType"],
            "score": item["score"],
            "reasons": item["humanReviewReasons"],
        }
        for item in results
        if item["verdict"] == "human_review"
    ]
    if missing_case_ids or extra_output_case_ids or any(item["verdict"] == "fail" for item in results):
        release_verdict = "fail"
    elif human_review_queue:
        release_verdict = "human_review"
    else:
        release_verdict = "pass"
    return {
        "reportType": "single_run",
        "rubricVersion": RUBRIC_VERSION,
        "runName": run_name,
        "releaseVerdict": release_verdict,
        "summary": _summary(results),
        "missingCaseIds": missing_case_ids,
        "extraOutputCaseIds": extra_output_case_ids,
        "humanReviewQueue": human_review_queue,
        "results": results,
    }


def compare_runs(raw_cases, raw_baseline_outputs, raw_candidate_outputs):
    baseline = evaluate_dataset(raw_cases, raw_baseline_outputs, run_name="baseline")
    candidate = evaluate_dataset(raw_cases, raw_candidate_outputs, run_name="candidate")
    baseline_by_id = {item["caseId"]: item for item in baseline["results"]}
    candidate_by_id = {item["caseId"]: item for item in candidate["results"]}
    comparisons = []
    regressions = []
    fixed_cases = []
    for case_id in sorted(set(baseline_by_id) & set(candidate_by_id)):
        before = baseline_by_id[case_id]
        after = candidate_by_id[case_id]
        score_delta = None
        if before["score"] is not None and after["score"] is not None:
            score_delta = round(after["score"] - before["score"], 2)
        new_gates = sorted(set(after["hardGateFailures"]) - set(before["hardGateFailures"]))
        fixed_gates = sorted(set(before["hardGateFailures"]) - set(after["hardGateFailures"]))
        verdict_regressed = VERDICT_RANK[after["verdict"]] < VERDICT_RANK[before["verdict"]]
        material_score_drop = score_delta is not None and score_delta <= -MATERIAL_SCORE_DROP
        comparison = {
            "caseId": case_id,
            "baselineVerdict": before["verdict"],
            "candidateVerdict": after["verdict"],
            "baselineScore": before["score"],
            "candidateScore": after["score"],
            "scoreDelta": score_delta,
            "newHardGateFailures": new_gates,
            "fixedHardGateFailures": fixed_gates,
            "regression": bool(new_gates or verdict_regressed or material_score_drop),
        }
        comparisons.append(comparison)
        if comparison["regression"]:
            regressions.append(comparison)
        if VERDICT_RANK[after["verdict"]] > VERDICT_RANK[before["verdict"]] or fixed_gates:
            fixed_cases.append(case_id)

    missing_baseline_case_ids = baseline["missingCaseIds"]
    missing_candidate_case_ids = candidate["missingCaseIds"]
    baseline_contract_invalid = bool(missing_baseline_case_ids or baseline["extraOutputCaseIds"])
    if baseline_contract_invalid:
        release_verdict = "fail"
    elif regressions or missing_candidate_case_ids:
        release_verdict = "regression"
    elif candidate["releaseVerdict"] == "human_review":
        release_verdict = "human_review"
    elif candidate["releaseVerdict"] == "fail":
        release_verdict = "fail"
    else:
        release_verdict = "pass"
    return {
        "reportType": "comparison",
        "rubricVersion": RUBRIC_VERSION,
        "releaseVerdict": release_verdict,
        "baseline": baseline,
        "candidate": candidate,
        "missingBaselineCaseIds": missing_baseline_case_ids,
        "missingCandidateCaseIds": missing_candidate_case_ids,
        "caseComparisons": comparisons,
        "regressions": regressions,
        "fixedCases": fixed_cases,
        "humanReviewQueue": candidate["humanReviewQueue"],
    }


def render_markdown(report):
    if report["reportType"] == "comparison":
        summary = report["candidate"]["summary"]
        title = "# MMN Eval 版本对比报告"
    else:
        summary = report["summary"]
        title = "# MMN Eval 运行报告"
    lines = [
        title,
        "",
        f"- Rubric：`{report['rubricVersion']}`",
        f"- 发布判断：`{report['releaseVerdict']}`",
        f"- 已评测：{summary['evaluated']}",
        f"- 通过 / 人工复核 / 失败：{summary['pass']} / {summary['humanReview']} / {summary['fail']}",
        f"- 平均分：{summary['averageScore'] if summary['averageScore'] is not None else '缺失'}",
        "",
        "## 人工复核队列",
        "",
    ]
    queue = report.get("humanReviewQueue") or []
    if queue:
        for item in queue:
            reasons = "；".join(item["reasons"]) or "总分处于人工复核区间"
            lines.append(f"- `{item['caseId']}`（{item['taskType']}，{item['score']}分）：{reasons}")
    else:
        lines.append("- 无")
    if report["reportType"] == "comparison":
        lines.extend(["", "## 回归", ""])
        if report["regressions"]:
            for item in report["regressions"]:
                lines.append(
                    f"- `{item['caseId']}`：{item['baselineVerdict']} → {item['candidateVerdict']}，"
                    f"分数变化 {item['scoreDelta']}"
                )
        else:
            lines.append("- 无")
    return "\n".join(lines) + "\n"
