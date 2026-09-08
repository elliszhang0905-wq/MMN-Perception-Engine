import json
from pathlib import Path
import unittest

from brand_penetration_analysis import fuse_reviews


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "brand_review_v4_cases.json"


class BrandReviewV3BaselineReproductionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {
            case["caseId"]: case
            for case in json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        }

    def test_fixture_contract_is_bounded_and_gold_is_explicitly_unavailable(self):
        self.assertEqual(len(self.cases), 2)
        for case in self.cases.values():
            self.assertEqual(set(case), {"caseId", "sourceKind", "packet", "reviews", "expected"})
            self.assertIn(case["sourceKind"], {"synthetic", "historical_redacted"})
            self.assertEqual(set(case["reviews"]), {"review_1", "review_2", "review_3"})
            self.assertEqual(case["expected"]["goldHumanLabel"]["status"], "unavailable")
            self.assertEqual(case["packet"]["boundary"], "纯合成复现证据，不代表任何真实品牌、平台或市场事实。")

    def test_v3_action_direction_only_disagreement_drops_claim_text(self):
        case = self.cases["synthetic-action-direction-only-disagreement"]
        source_rows = [
            case["reviews"][role]["brandConclusions"][0]
            for role in ("review_1", "review_2", "review_3")
        ]
        without_direction = [
            {key: value for key, value in row.items() if key != "actionDirection"}
            for row in source_rows
        ]
        self.assertEqual(without_direction[0], without_direction[1])
        self.assertEqual(without_direction[1], without_direction[2])
        self.assertEqual(
            [row["actionDirection"] for row in source_rows],
            ["monitor", "monitor", "amplify"],
        )

        result = fuse_reviews(case["reviews"], case["packet"])
        claim = result["brandConclusions"][0]

        self.assertEqual(result["schemaVersion"], case["expected"]["schemaVersion"])
        self.assertEqual(result["validation"]["status"], case["expected"]["validationStatus"])
        self.assertEqual(claim["status"], case["expected"]["claims"][0]["status"])
        self.assertTrue(any("actionDirection" in reason for reason in claim["reasons"]))
        self.assertNotIn("conclusion", claim)
        self.assertNotIn("recommendedAction", claim)

    def test_v3_can_publish_ungrounded_text_from_median_confidence_review(self):
        case = self.cases["synthetic-median-confidence-ungrounded-text"]
        expected_claim = case["expected"]["claims"][0]

        result = fuse_reviews(case["reviews"], case["packet"])
        claim = result["brandConclusions"][0]

        self.assertEqual(result["validation"]["status"], case["expected"]["validationStatus"])
        self.assertEqual(claim["status"], expected_claim["status"])
        self.assertEqual(claim["conclusion"], expected_claim["selectedConclusion"])
        self.assertNotIn("全国", case["packet"]["evidence"][0]["text"])
        self.assertEqual(expected_claim["groundingStatus"], "unsupported_by_packet")


if __name__ == "__main__":
    unittest.main()
