import json
import tempfile
import unittest
from pathlib import Path

from mmn_eval.contracts import normalize_case, normalize_output
from mmn_eval.runner import compare_runs, evaluate_dataset, load_jsonl, render_markdown


def eval_case(case_id="case-1"):
    return {
        "id": case_id,
        "taskType": "strategy",
        "input": {
            "evidence": [
                {"id": "official-1", "sourceGroup": "official"},
                {"id": "owner-1", "sourceGroup": "owner-study"},
            ],
        },
        "expected": {
            "requiredProviders": ["qwen", "deepseek"],
            "requiredStatementTypes": ["fact", "inference", "hypothesis", "unknown"],
            "minimumIndependentSources": 2,
        },
    }


def eval_output(case_id="case-1", score=0.9):
    return {
        "caseId": case_id,
        "claims": [
            {"statementType": "fact", "text": "官方资料确认产品能力。", "evidenceIds": ["official-1"]},
            {"statementType": "inference", "text": "该能力可能改善体验。", "evidenceIds": ["official-1", "owner-1"]},
            {"statementType": "hypothesis", "text": "目标用户可能提高考虑度。", "evidenceIds": ["owner-1"]},
            {"statementType": "unknown", "text": "当前缺少成交数据。", "evidenceIds": []},
        ],
        "dimensions": {name: score for name in ("evidence", "reasoning", "actionability", "fit", "uncertainty")},
        "modelValidation": {"completedProviders": ["qwen", "deepseek"], "commonEvidenceIds": ["official-1"]},
        "flags": {},
        "metadata": {"promptVersion": "v1", "gradingSource": "independent_judge"},
    }


class MmnEvalRunnerTest(unittest.TestCase):
    def test_jsonl_loader_reports_invalid_line_number(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "cases.jsonl"
            path.write_text('{"id":"ok"}\nnot-json\n', encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "cases.jsonl:2"):
                load_jsonl(path)

    def test_dataset_evaluation_reports_missing_and_extra_outputs(self):
        report = evaluate_dataset(
            [eval_case("case-1"), eval_case("case-2")],
            [eval_output("case-1"), eval_output("extra-case")],
            run_name="candidate",
        )

        self.assertEqual(report["missingCaseIds"], ["case-2"])
        self.assertEqual(report["extraOutputCaseIds"], ["extra-case"])
        self.assertEqual(report["summary"]["evaluated"], 1)
        self.assertEqual(report["summary"]["pass"], 1)
        self.assertEqual(report["releaseVerdict"], "fail")

    def test_extra_output_case_fails_a_strict_release_run(self):
        report = evaluate_dataset(
            [eval_case("case-1")],
            [eval_output("case-1"), eval_output("extra-case")],
            run_name="candidate",
        )

        self.assertEqual(report["missingCaseIds"], [])
        self.assertEqual(report["extraOutputCaseIds"], ["extra-case"])
        self.assertEqual(report["releaseVerdict"], "fail")

    def test_comparison_marks_new_hard_gate_failure_as_regression(self):
        baseline = eval_output(score=0.82)
        candidate = eval_output(score=0.95)
        candidate["flags"]["fabricatedFact"] = True

        report = compare_runs([eval_case()], [baseline], [candidate])

        self.assertEqual(report["releaseVerdict"], "regression")
        self.assertEqual(report["regressions"][0]["caseId"], "case-1")
        self.assertIn("fabricated_fact", report["regressions"][0]["newHardGateFailures"])

    def test_missing_candidate_case_is_a_regression(self):
        report = compare_runs([eval_case()], [eval_output()], [])

        self.assertEqual(report["missingCandidateCaseIds"], ["case-1"])
        self.assertEqual(report["releaseVerdict"], "regression")

    def test_incomplete_baseline_fails_comparison_contract(self):
        report = compare_runs([eval_case()], [], [eval_output()])

        self.assertEqual(report["missingBaselineCaseIds"], ["case-1"])
        self.assertEqual(report["releaseVerdict"], "fail")

    def test_comparison_reports_fixed_failures_and_score_delta(self):
        baseline = eval_output(score=0.6)
        candidate = eval_output(score=0.85)

        report = compare_runs([eval_case()], [baseline], [candidate])

        self.assertEqual(report["releaseVerdict"], "pass")
        self.assertEqual(report["fixedCases"], ["case-1"])
        self.assertEqual(report["caseComparisons"][0]["scoreDelta"], 25.0)

    def test_markdown_report_includes_human_review_queue(self):
        report = evaluate_dataset([eval_case()], [eval_output(score=0.7)], run_name="candidate")

        markdown = render_markdown(report)

        self.assertIn("MMN Eval", markdown)
        self.assertIn("人工复核队列", markdown)
        self.assertIn("case-1", markdown)

    def test_seed_dataset_is_valid_and_covers_required_failure_modes(self):
        cases = [normalize_case(item) for item in load_jsonl(Path("data/eval/mmn_eval_seed_v0.1.jsonl"))]
        outputs = [normalize_output(item) for item in load_jsonl(Path("data/eval/mmn_eval_seed_outputs_v0.1.jsonl"))]

        self.assertGreaterEqual(len(cases), 10)
        self.assertEqual({case["id"] for case in cases}, {output["caseId"] for output in outputs})
        self.assertIn("vehicle_configuration", {case["taskType"] for case in cases})
        flags = {name for output in outputs for name, active in output["flags"].items() if active}
        self.assertTrue({"fabricatedFact", "missingAsZero", "platformSignalOverreach"}.issubset(flags))

        report = evaluate_dataset(cases, outputs, run_name="seed")
        self.assertGreater(report["summary"]["pass"], 0)
        self.assertGreater(report["summary"]["humanReview"], 0)
        self.assertGreater(report["summary"]["fail"], 0)


if __name__ == "__main__":
    unittest.main()
