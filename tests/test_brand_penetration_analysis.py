import json
import unittest
from unittest.mock import patch

import server
from brand_penetration_analysis import analysis_messages, build_evidence_packet, fuse_reviews


class BrandPenetrationAnalysisTest(unittest.TestCase):
    def result(self):
        return {
            "keyword": "智己",
            "modelComparisons": [
                {"model": "智己", "role": "own"},
                {"model": "理想", "role": "competitor"},
            ],
            "verifiedComparisonItems": [
                {"id": "own-1", "brandName": "智己", "platform": "weibo", "text": "智己发布新车", "sentiment": "positive", "heat": 80},
                {"id": "peer-1", "brandName": "理想", "platform": "douyin", "text": "理想强化家庭场景", "sentiment": "neutral", "heat": 60},
            ],
        }

    def test_packet_is_deterministic_and_brand_scoped(self):
        first = build_evidence_packet(self.result(), {"start": "2026-07-01", "end": "2026-07-22"})
        second = build_evidence_packet(self.result(), {"start": "2026-07-01", "end": "2026-07-22"})
        self.assertEqual(first["status"], "ready")
        self.assertEqual(first["fingerprint"], second["fingerprint"])
        self.assertEqual(first["brandEvidenceIds"], {"智己": ["own-1"], "理想": ["peer-1"]})

    def test_three_reviews_receive_the_same_packet_without_peer_answers(self):
        packet = build_evidence_packet(self.result())
        messages = analysis_messages(packet)
        self.assertEqual(json.loads(messages[-1]["content"])["fingerprint"], packet["fingerprint"])
        self.assertNotIn("其他模型结论", messages[-1]["content"])

    def review(self, conclusion="智己形成新车传播主线", direction="differentiate", evidence=None):
        evidence = evidence or ["own-1"]
        common_brand = {
            "status": "ready", "judgement": "strengthening", "primaryIntent": "product_launch",
            "actionDirection": direction, "conclusion": conclusion, "communicationTheme": "新车体验传播",
            "representativeAction": "发布新车内容", "opportunity": "放大产品体验", "risk": "样本覆盖有限",
            "recommendedAction": "强化差异化体验内容", "leadingIndicator": "体验内容互动率",
            "resultIndicator": "品牌关联内容占比", "stopCondition": "连续两周未增长", "uncertainty": "仅限公开传播样本",
            "evidenceIds": evidence, "confidence": .8,
        }
        pair = {
            "ownBrand": "智己", "competitor": "理想", "status": "ready", "relationship": "direct_competition",
            "pressure": "medium", "actionDirection": direction, "cognitionOverlap": "都在争夺家庭智能认知",
            "competitorIntent": "强化家庭场景", "ownAdvantage": "驾控体验更鲜明", "ownGap": "家庭场景表达较弱",
            "threat": "对方场景认知更集中", "opportunity": "用差异化体验拉开距离",
            "recommendedAction": "以双车场景对比强化差异", "leadingIndicator": "对比内容互动率",
            "resultIndicator": "差异化认知提及率", "stopCondition": "连续两周提及率未增长", "uncertainty": "缺少购买意愿证据",
            "evidenceIds": ["own-1", "peer-1"], "confidence": .8,
        }
        own = {"brand": "智己", **common_brand}
        peer = {"brand": "理想", **common_brand, "conclusion": "理想强化家庭场景传播", "evidenceIds": ["peer-1"]}
        return {"brandConclusions": [own, peer], "pairwiseConclusions": [pair]}

    def test_only_three_way_enum_consensus_publishes_one_neutral_conclusion(self):
        packet = build_evidence_packet(self.result())
        fused = fuse_reviews({role: self.review() for role in ("review_1", "review_2", "review_3")}, packet)
        self.assertEqual(fused["validation"]["status"], "aligned")
        self.assertEqual(fused["brandConclusions"][0]["status"], "aligned")
        self.assertEqual(fused["pairwiseConclusions"][0]["commonEvidenceIds"], ["own-1", "peer-1"])
        self.assertNotIn("qwen", json.dumps(fused, ensure_ascii=False).lower())

    def test_disagreement_and_missing_review_fail_closed(self):
        packet = build_evidence_packet(self.result())
        conflicted = fuse_reviews({"review_1": self.review(), "review_2": self.review(direction="defend"), "review_3": self.review()}, packet)
        self.assertEqual(conflicted["brandConclusions"][0]["status"], "manual_required")
        degraded = fuse_reviews({"review_1": self.review(), "review_2": self.review()}, packet, {"review_3": "internal"})
        self.assertEqual(degraded["validation"]["status"], "degraded")
        self.assertNotIn("internal", json.dumps(degraded, ensure_ascii=False))

    def test_one_invalid_brand_row_does_not_discard_other_valid_rows(self):
        packet = build_evidence_packet(self.result())
        partial = self.review()
        partial["brandConclusions"][1]["judgement"] = "unsupported_value"
        fused = fuse_reviews({
            "review_1": partial,
            "review_2": self.review(),
            "review_3": self.review(),
        }, packet)
        self.assertEqual(fused["brandConclusions"][0]["status"], "aligned")
        self.assertEqual(fused["brandConclusions"][1]["status"], "degraded")
        self.assertEqual(fused["pairwiseConclusions"][0]["status"], "aligned")
        self.assertEqual(fused["validation"]["independentReviews"][0]["status"], "partial")

    def test_server_runs_three_independent_calls_on_identical_fingerprint(self):
        fingerprints = []

        def runner(_provider, messages):
            fingerprints.append(json.loads(messages[-1]["content"])["fingerprint"])
            return self.review()

        fused = server.run_brand_penetration_conclusions(self.result(), provider_runner=runner)
        self.assertEqual(len(fingerprints), 3)
        self.assertEqual(len(set(fingerprints)), 1)
        self.assertEqual(fused["validation"]["status"], "aligned")

    def test_server_retries_structurally_incomplete_brand_review(self):
        calls = {"qwen": 0, "deepseek": 0, "kimi": 0}

        def runner(provider, _messages):
            calls[provider] += 1
            review = self.review()
            if provider == "kimi" and calls[provider] == 1:
                review["pairwiseConclusions"] = []
            return review

        fused = server.run_brand_penetration_conclusions(self.result(), provider_runner=runner)

        self.assertEqual(calls, {"qwen": 1, "deepseek": 1, "kimi": 2})
        self.assertEqual(fused["validation"]["status"], "aligned")
        self.assertTrue(all(
            row["status"] == "completed"
            for row in fused["validation"]["independentReviews"]
        ))

    def test_server_uses_deep_kimi_for_full_brand_decision(self):
        with patch.object(server, "call_qwen", return_value=self.review()), \
             patch.object(server, "call_deepseek", return_value=self.review()), \
             patch.object(server, "call_kimi", return_value=self.review()) as kimi:
            fused = server.run_brand_penetration_conclusions(self.result())

        self.assertEqual(fused["validation"]["status"], "aligned")
        self.assertEqual(kimi.call_args.kwargs["profile"], "deep")

    def test_legacy_snapshot_is_normalized_without_claiming_three_review_completion(self):
        legacy = {
            "primaryBrand": "智己", "verifiedCount": 2,
            "brandResults": {
                "智己": {"items": [{"id": "own-1", "text": "智己发布新车", "sentiment": "positive", "heat": 80}]},
                "理想": {"items": [{"id": "peer-1", "text": "理想强化家庭场景", "sentiment": "neutral", "heat": 60}]},
            },
        }
        prepared = server.prepare_brand_penetration_snapshot(legacy)
        self.assertEqual(len(prepared["verifiedComparisonItems"]), 2)
        self.assertEqual([row["role"] for row in prepared["modelComparisons"]], ["own", "competitor"])
        self.assertNotIn("threeFlagships", prepared["qa"])

    def test_brand_center_keeps_five_competitors(self):
        body = server._normalize_social_trend_body({
            "keyword": "智己", "centerType": "brand_penetration",
            "competitors": ["理想", "蔚来", "小米", "问界", "零跑"],
        })
        self.assertEqual(len(body["competitors"]), 5)


if __name__ == "__main__":
    unittest.main()
