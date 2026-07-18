import unittest

from mmn_eval.contracts import ContractError, normalize_case, normalize_output
from mmn_eval.rubric import DIMENSIONS, HARD_GATES, RUBRIC_VERSION, THRESHOLDS


class MmnEvalContractsTest(unittest.TestCase):
    def test_case_requires_id_task_type_input_and_expected(self):
        for raw in (
            {},
            {"id": "case-1"},
            {"id": "case-1", "taskType": "strategy"},
            {"id": "case-1", "taskType": "strategy", "input": {}},
        ):
            with self.subTest(raw=raw), self.assertRaises(ContractError):
                normalize_case(raw)

    def test_case_rejects_unknown_task_type_and_duplicate_evidence_ids(self):
        with self.assertRaisesRegex(ContractError, "taskType"):
            normalize_case({"id": "case-1", "taskType": "credo_script", "input": {}, "expected": {}})

        with self.assertRaisesRegex(ContractError, "evidence"):
            normalize_case({
                "id": "case-1",
                "taskType": "strategy",
                "input": {"evidence": [{"id": "e-1"}, {"id": "e-1"}]},
                "expected": {},
            })

    def test_case_expected_validation_requirements_are_strictly_typed(self):
        base = {"id": "case-1", "taskType": "strategy", "input": {}, "expected": {}}
        for expected, message in (
            ({"requiredProviders": "qwen"}, "requiredProviders"),
            ({"requiredStatementTypes": ["opinion"]}, "requiredStatementTypes"),
            ({"minimumIndependentSources": True}, "minimumIndependentSources"),
        ):
            with self.subTest(expected=expected), self.assertRaisesRegex(ContractError, message):
                normalize_case({**base, "expected": expected})

    def test_independent_source_gate_requires_explicit_source_groups(self):
        with self.assertRaisesRegex(ContractError, "sourceGroup"):
            normalize_case({
                "id": "case-1",
                "taskType": "strategy",
                "input": {"evidence": [{"id": "e-1"}, {"id": "e-2"}]},
                "expected": {"minimumIndependentSources": 2},
            })

    def test_missing_dimension_score_remains_none(self):
        output = normalize_output({
            "caseId": "case-1",
            "claims": [],
            "dimensions": {"evidence": None},
        })

        self.assertIsNone(output["dimensions"]["evidence"])
        self.assertNotIn("strategy", output["dimensions"])

    def test_dimension_score_must_be_between_zero_and_one(self):
        for score in (-0.01, 1.01, "0.8", True):
            with self.subTest(score=score), self.assertRaisesRegex(ContractError, "dimensions.evidence"):
                normalize_output({
                    "caseId": "case-1",
                    "claims": [],
                    "dimensions": {"evidence": score},
                })

    def test_model_validation_lists_and_flags_are_strictly_typed(self):
        with self.assertRaisesRegex(ContractError, "completedProviders"):
            normalize_output({
                "caseId": "case-1",
                "claims": [],
                "dimensions": {},
                "modelValidation": {"completedProviders": "qwen"},
            })

        with self.assertRaisesRegex(ContractError, "flags.fabricatedFact"):
            normalize_output({
                "caseId": "case-1",
                "claims": [],
                "dimensions": {},
                "flags": {"fabricatedFact": "false"},
            })

    def test_dimension_scores_require_independent_grading_provenance(self):
        with self.assertRaisesRegex(ContractError, "gradingSource"):
            normalize_output({
                "caseId": "case-1",
                "claims": [],
                "dimensions": {"evidence": 0.9},
                "metadata": {"promptVersion": "candidate-v1"},
            })

        output = normalize_output({
            "caseId": "case-1",
            "claims": [],
            "dimensions": {"evidence": 0.9},
            "metadata": {"gradingSource": "independent_judge"},
        })
        self.assertEqual(output["metadata"]["gradingSource"], "independent_judge")

    def test_claim_requires_statement_type_text_and_evidence_ids(self):
        with self.assertRaisesRegex(ContractError, r"claims\[0\]"):
            normalize_output({
                "caseId": "case-1",
                "claims": [{"statementType": "fact", "text": "续航为700公里"}],
                "dimensions": {},
            })

    def test_rubric_is_versioned_and_weights_total_one_hundred(self):
        self.assertEqual(RUBRIC_VERSION, "mmn-eval-v0.1")
        self.assertEqual(sum(item["weight"] for item in DIMENSIONS.values()), 100)
        self.assertEqual(THRESHOLDS, {"pass": 80, "human_review": 65})
        self.assertIn("fabricated_fact", HARD_GATES)
        self.assertIn("missing_as_zero", HARD_GATES)
        self.assertIn("platform_signal_overreach", HARD_GATES)


if __name__ == "__main__":
    unittest.main()
