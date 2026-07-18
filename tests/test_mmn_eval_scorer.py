import unittest

from mmn_eval.scorer import score_case


def base_case(task_type="strategy"):
    providers = ["qwen", "deepseek"]
    if task_type == "vehicle_configuration":
        providers.append("kimi")
    return {
        "id": "case-1",
        "taskType": task_type,
        "input": {
            "evidence": [
                {"id": "official-1", "sourceGroup": "official", "sourceType": "product"},
                {"id": "owner-1", "sourceGroup": "owner-study", "sourceType": "experience"},
            ],
        },
        "expected": {
            "requiredProviders": providers,
            "requiredStatementTypes": ["fact", "inference", "hypothesis", "unknown"],
            "minimumIndependentSources": 2,
        },
    }


def base_output(score=0.9, task_type="strategy"):
    providers = ["qwen", "deepseek"]
    if task_type == "vehicle_configuration":
        providers.append("kimi")
    return {
        "caseId": "case-1",
        "claims": [
            {"statementType": "fact", "text": "官方资料确认当前配置。", "evidenceIds": ["official-1"]},
            {"statementType": "inference", "text": "该配置可能改善家庭使用体验。", "evidenceIds": ["official-1", "owner-1"]},
            {"statementType": "hypothesis", "text": "目标家庭用户可能因此提高考虑度。", "evidenceIds": ["owner-1"]},
            {"statementType": "unknown", "text": "当前缺少真实到店转化数据。", "evidenceIds": []},
        ],
        "dimensions": {
            "evidence": score,
            "reasoning": score,
            "actionability": score,
            "fit": score,
            "uncertainty": score,
        },
        "modelValidation": {
            "completedProviders": providers,
            "commonEvidenceIds": ["official-1"],
        },
        "flags": {},
        "metadata": {"gradingSource": "independent_judge"},
    }


class MmnEvalScorerTest(unittest.TestCase):
    def test_fabricated_fact_fails_even_with_high_dimension_scores(self):
        output = base_output()
        output["flags"]["fabricatedFact"] = True

        result = score_case(base_case(), output)

        self.assertEqual(result["score"], 90.0)
        self.assertEqual(result["verdict"], "fail")
        self.assertIn("fabricated_fact", result["hardGateFailures"])

    def test_unknown_evidence_and_missing_as_zero_are_hard_failures(self):
        output = base_output()
        output["claims"][0]["evidenceIds"] = ["invented-1"]
        output["flags"]["missingAsZero"] = True

        result = score_case(base_case(), output)

        self.assertIn("unknown_evidence", result["hardGateFailures"])
        self.assertIn("missing_as_zero", result["hardGateFailures"])

    def test_platform_signal_cannot_independently_prove_purchase_or_conversion(self):
        output = base_output()
        output["flags"]["platformSignalOverreach"] = True

        result = score_case(base_case(), output)

        self.assertEqual(result["verdict"], "fail")
        self.assertIn("platform_signal_overreach", result["hardGateFailures"])

    def test_strategy_requires_declared_statement_types_and_two_model_validation(self):
        output = base_output()
        output["claims"] = output["claims"][:2]
        output["modelValidation"]["completedProviders"] = ["qwen"]

        result = score_case(base_case(), output)

        self.assertIn("statement_types_missing", result["hardGateFailures"])
        self.assertIn("incomplete_model_validation", result["hardGateFailures"])

    def test_vehicle_configuration_requires_three_models_and_common_evidence(self):
        output = base_output(task_type="vehicle_configuration")
        output["modelValidation"] = {
            "completedProviders": ["qwen", "deepseek"],
            "commonEvidenceIds": [],
        }

        result = score_case(base_case("vehicle_configuration"), output)

        self.assertEqual(result["verdict"], "fail")
        self.assertIn("vehicle_validation_incomplete", result["hardGateFailures"])

    def test_executable_strategy_requires_independent_sources(self):
        output = base_output()
        for claim in output["claims"]:
            claim["evidenceIds"] = ["official-1"] if claim["statementType"] != "unknown" else []

        result = score_case(base_case(), output)

        self.assertIn("source_independence_missing", result["hardGateFailures"])

    def test_numeric_thresholds_assign_pass_review_and_fail(self):
        self.assertEqual(score_case(base_case(), base_output(0.8))["verdict"], "pass")
        self.assertEqual(score_case(base_case(), base_output(0.79))["verdict"], "human_review")
        self.assertEqual(score_case(base_case(), base_output(0.65))["verdict"], "human_review")
        self.assertEqual(score_case(base_case(), base_output(0.64))["verdict"], "fail")

    def test_missing_dimension_is_not_scored_as_zero_and_routes_to_human(self):
        output = base_output(0.9)
        output["dimensions"]["fit"] = None

        result = score_case(base_case(), output)

        self.assertEqual(result["score"], 90.0)
        self.assertEqual(result["dimensionCoverage"], 0.85)
        self.assertEqual(result["verdict"], "human_review")
        self.assertIn("评分维度不完整：fit", result["humanReviewReasons"])


if __name__ == "__main__":
    unittest.main()
