import json
import tempfile
import unittest
from pathlib import Path

from mmn_eval.dashboard import load_dashboard_payload, run_seed_dashboard, save_human_review


class MmnEvalDashboardTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.report_path = self.root / "report.json"
        self.cases_path = self.root / "cases.jsonl"
        self.outputs_path = self.root / "outputs.jsonl"
        self.reviews_path = self.root / "reviews.json"
        self.cases = [
            {
                "id": "review-case",
                "taskType": "brief",
                "input": {"question": "生成家庭长途场景内容Brief。", "evidence": []},
                "expected": {
                    "requiredProviders": [],
                    "requiredStatementTypes": [],
                    "minimumIndependentSources": 1,
                },
                "tags": ["human_review"],
            },
            {
                "id": "pass-case",
                "taskType": "strategy",
                "input": {"question": "形成可执行策略。", "evidence": []},
                "expected": {
                    "requiredProviders": [],
                    "requiredStatementTypes": [],
                    "minimumIndependentSources": 1,
                },
                "tags": ["happy_path"],
            },
        ]
        self.report = {
            "reportType": "single_run",
            "rubricVersion": "mmn-eval-v0.1",
            "runName": "seed-v0.1",
            "releaseVerdict": "human_review",
            "summary": {
                "evaluated": 2,
                "pass": 1,
                "humanReview": 1,
                "fail": 0,
                "averageScore": 84.5,
                "averageDimensionCoverage": 0.95,
                "hardGateFailures": {},
                "dimensionAverages": {
                    "evidence": 0.9,
                    "reasoning": 0.84,
                    "actionability": 0.82,
                    "fit": 0.79,
                    "uncertainty": 0.86,
                },
            },
            "missingCaseIds": [],
            "extraOutputCaseIds": [],
            "humanReviewQueue": [
                {"caseId": "review-case", "taskType": "brief", "score": 79.0, "reasons": ["总分处于人工复核区间"]}
            ],
            "results": [
                {
                    "caseId": "review-case",
                    "taskType": "brief",
                    "score": 79.0,
                    "verdict": "human_review",
                    "hardGateFailures": [],
                    "hardGateMessages": [],
                    "dimensions": {"evidence": 0.8, "reasoning": 0.8, "actionability": 0.78, "fit": 0.76, "uncertainty": 0.82},
                    "dimensionCoverage": 1.0,
                    "humanReviewReasons": ["总分处于人工复核区间"],
                },
                {
                    "caseId": "pass-case",
                    "taskType": "strategy",
                    "score": 90.0,
                    "verdict": "pass",
                    "hardGateFailures": [],
                    "hardGateMessages": [],
                    "dimensions": {"evidence": 1.0, "reasoning": 0.88, "actionability": 0.86, "fit": 0.82, "uncertainty": 0.9},
                    "dimensionCoverage": 1.0,
                    "humanReviewReasons": [],
                },
            ],
        }
        self.report_path.write_text(json.dumps(self.report, ensure_ascii=False), encoding="utf-8")
        self.cases_path.write_text(
            "\n".join(json.dumps(item, ensure_ascii=False) for item in self.cases) + "\n",
            encoding="utf-8",
        )

    def tearDown(self):
        self.temp.cleanup()

    def test_dashboard_payload_exposes_real_summary_cases_and_pending_reviews(self):
        payload = load_dashboard_payload(
            self.report_path,
            self.cases_path,
            self.reviews_path,
            org_id="org-a",
        )
        self.assertEqual(payload["report"]["summary"]["evaluated"], 2)
        self.assertEqual(payload["reviewProgress"], {"total": 1, "resolved": 0, "pending": 1})
        self.assertEqual(payload["cases"][0]["question"], "生成家庭长途场景内容Brief。")
        self.assertIsNone(payload["comparison"])
        self.assertEqual(payload["sourceKind"], "seed_fixture")

    def test_human_review_is_saved_and_returned_only_for_same_org(self):
        saved = save_human_review(
            "review-case",
            "approved",
            "证据链可用，补充阶段适配说明后入库。",
            self.report_path,
            self.reviews_path,
            org_id="org-a",
            reviewer="ellis@example.com",
        )
        self.assertEqual(saved["review"]["decision"], "approved")
        self.assertEqual(saved["review"]["reviewer"], "ellis@example.com")
        own = load_dashboard_payload(self.report_path, self.cases_path, self.reviews_path, org_id="org-a")
        other = load_dashboard_payload(self.report_path, self.cases_path, self.reviews_path, org_id="org-b")
        self.assertEqual(own["reviewProgress"], {"total": 1, "resolved": 1, "pending": 0})
        self.assertEqual(own["cases"][0]["humanDecision"]["decision"], "approved")
        self.assertIsNone(other["cases"][0]["humanDecision"])

    def test_rejected_review_requires_a_reason(self):
        with self.assertRaisesRegex(ValueError, "驳回时请填写人工依据"):
            save_human_review(
                "review-case",
                "rejected",
                "",
                self.report_path,
                self.reviews_path,
                org_id="org-a",
                reviewer="ellis@example.com",
            )

    def test_non_review_case_cannot_be_manually_overridden(self):
        with self.assertRaisesRegex(ValueError, "不在人工复核队列"):
            save_human_review(
                "pass-case",
                "rejected",
                "不应允许覆盖自动通过结果。",
                self.report_path,
                self.reviews_path,
                org_id="org-a",
                reviewer="ellis@example.com",
            )

    def test_unknown_decision_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "人工结论必须是 approved 或 rejected"):
            save_human_review(
                "review-case",
                "maybe",
                "",
                self.report_path,
                self.reviews_path,
                org_id="org-a",
                reviewer="ellis@example.com",
            )

    def test_seed_run_rebuilds_report_and_preserves_review_progress(self):
        outputs = [
            {
                "caseId": "review-case",
                "claims": [],
                "modelValidation": {"completedProviders": [], "commonEvidenceIds": []},
                "dimensions": {"evidence": 0.8, "reasoning": 0.8, "actionability": 0.78, "fit": 0.76, "uncertainty": 0.82},
                "flags": {},
                "metadata": {"gradingSource": "synthetic_fixture"},
            },
            {
                "caseId": "pass-case",
                "claims": [],
                "modelValidation": {"completedProviders": [], "commonEvidenceIds": []},
                "dimensions": {"evidence": 1.0, "reasoning": 0.88, "actionability": 0.86, "fit": 0.82, "uncertainty": 0.9},
                "flags": {},
                "metadata": {"gradingSource": "synthetic_fixture"},
            },
        ]
        self.outputs_path.write_text(
            "\n".join(json.dumps(item, ensure_ascii=False) for item in outputs) + "\n",
            encoding="utf-8",
        )
        payload = run_seed_dashboard(
            self.cases_path,
            self.outputs_path,
            self.report_path,
            self.reviews_path,
            org_id="org-a",
        )
        self.assertTrue(self.report_path.exists())
        self.assertEqual(payload["report"]["summary"]["evaluated"], 2)
        self.assertEqual(payload["report"]["runName"], "seed-v0.1")


if __name__ == "__main__":
    unittest.main()
