import copy
import json
import unittest
from io import BytesIO
from threading import Barrier
from urllib.error import HTTPError
from unittest.mock import patch

import server


def _result(items):
    return {
        "keyword": "智己",
        "items": [item for item in items if item.get("brandName") == "智己"],
        "comparisonItems": copy.deepcopy(items),
        "modelComparisons": [
            {"model": "智己", "role": "own", "contentCount": 1, "heat": 80, "positiveRate": 100, "riskCount": 0},
            {"model": "零跑", "role": "competitor", "contentCount": 2, "heat": 120, "positiveRate": 50, "riskCount": 0},
        ],
        "collectionStatus": {"status": "complete"},
        "qa": {},
    }


def _review(messages, *, fail_ids=(), brand_overrides=None):
    payload = json.loads(messages[-1]["content"])
    rows = []
    for item in payload["evidence"]:
        if item["id"] in fail_ids:
            continue
        brand = (brand_overrides or {}).get(item["id"], item["expectedBrand"])
        rows.append({
            "id": item["id"],
            "sentiment": item["sentiment"],
            "relevant": brand == item["expectedBrand"],
            "brandName": brand,
            "modelName": "",
            "matrixContent": True,
            "reason": "test",
        })
    return {"items": rows, "strategyConclusion": "test", "risks": []}


class SocialTrendDualModelGateTest(unittest.TestCase):
    def test_curated_comparison_evidence_bounds_model_review_without_changing_full_metrics(self):
        items = [
            {"id": f"item-{index}", "brandName": "智己", "text": f"智己证据{index}", "sentiment": "positive"}
            for index in range(30)
        ]
        payload = _result(items)
        payload["comparisonEvidence"] = copy.deepcopy(items[:5])

        with patch.object(server, "qwen_config", return_value={"configured": True}), \
             patch.object(server, "deepseek_config", return_value={"configured": True}), \
             patch.object(server, "kimi_config", return_value={"configured": True}), \
             patch.object(server, "call_qwen", side_effect=lambda messages, **_kwargs: _review(messages)), \
             patch.object(server, "call_deepseek", side_effect=lambda messages, **_kwargs: _review(messages)), \
             patch.object(server, "call_kimi", side_effect=lambda messages, **_kwargs: _review(messages)), \
             patch.object(server, "parse_json_object", side_effect=lambda value: value):
            result = server.validate_social_trends_with_models(payload)

        self.assertEqual(result["qa"]["threeFlagships"]["reviewedEvidenceCount"], 5)
        self.assertEqual(len(result["verifiedComparisonItems"]), 5)
        self.assertEqual(result["modelComparisons"][0]["contentCount"], 1)

    def test_three_reviewers_run_in_parallel_for_each_evidence_batch(self):
        items = [{"id": "own-1", "brandName": "智己", "text": "智己LS9发布", "sentiment": "positive"}]
        rendezvous = Barrier(3)

        def reviewer(messages, **_kwargs):
            rendezvous.wait(timeout=1)
            return _review(messages)

        with patch.object(server, "qwen_config", return_value={"configured": True}), \
             patch.object(server, "deepseek_config", return_value={"configured": True}), \
             patch.object(server, "kimi_config", return_value={"configured": True}), \
             patch.object(server, "call_qwen", side_effect=reviewer), \
             patch.object(server, "call_deepseek", side_effect=reviewer), \
             patch.object(server, "call_kimi", side_effect=reviewer), \
             patch.object(server, "parse_json_object", side_effect=lambda value: value):
            result = server.validate_social_trends_with_models(_result(items))

        self.assertEqual(result["qa"]["threeFlagships"]["status"], "aligned")

    def test_all_comparison_items_are_reviewed_and_only_common_brand_evidence_is_published(self):
        items = [
            {"id": "own-1", "brandName": "智己", "text": "智己LS9发布", "sentiment": "positive"},
            {"id": "peer-1", "brandName": "零跑", "text": "零跑B01上市", "sentiment": "positive"},
            {"id": "mixed-1", "brandName": "零跑", "text": "零跑、理想L6、智己LS9同日发布", "sentiment": "neutral"},
        ]

        def qwen(messages, **_kwargs):
            return _review(messages, brand_overrides={"mixed-1": "多品牌"})

        def deepseek(messages, **_kwargs):
            return _review(messages, brand_overrides={"mixed-1": "多品牌"})

        with patch.object(server, "qwen_config", return_value={"configured": True}), \
             patch.object(server, "deepseek_config", return_value={"configured": True}), \
             patch.object(server, "kimi_config", return_value={"configured": True}), \
             patch.object(server, "call_qwen", side_effect=qwen), \
             patch.object(server, "call_deepseek", side_effect=deepseek), \
             patch.object(server, "call_kimi", side_effect=lambda messages, **_kwargs: _review(messages, brand_overrides={"mixed-1": "多品牌"})), \
             patch.object(server, "parse_json_object", side_effect=lambda value: value):
            result = server.validate_social_trends_with_models(_result(items))

        self.assertEqual(result["qa"]["threeFlagships"]["status"], "disagreement")
        self.assertEqual(result["qa"]["threeFlagships"]["reviewedEvidenceCount"], 3)
        self.assertEqual(set(result["qa"]["threeFlagships"]["verifiedEvidenceIds"]), {"own-1", "peer-1"})
        self.assertEqual({item["id"] for item in result["verifiedComparisonItems"]}, {"own-1", "peer-1"})
        self.assertEqual(result["unifiedInsight"]["publicationStatus"], "conditional")
        self.assertIn("1 条证据存在分歧", result["unifiedInsight"]["limitations"][0])
        self.assertEqual(result["unifiedInsight"]["scopeType"], "own_vs_competitors")
        self.assertEqual(result["unifiedInsight"]["models"], ["智己", "零跑"])
        self.assertNotIn("qwen", json.dumps(result["unifiedInsight"], ensure_ascii=False).lower())

    def test_incomplete_provider_output_blocks_all_publication(self):
        items = [{"id": f"item-{index}", "brandName": "零跑", "text": "零跑B01上市", "sentiment": "positive"} for index in range(25)]

        def incomplete_qwen(messages, **_kwargs):
            payload = json.loads(messages[-1]["content"])
            return _review(messages, fail_ids={payload["evidence"][0]["id"]})

        with patch.object(server, "qwen_config", return_value={"configured": True}), \
             patch.object(server, "deepseek_config", return_value={"configured": True}), \
             patch.object(server, "kimi_config", return_value={"configured": True}), \
             patch.object(server, "call_qwen", side_effect=incomplete_qwen), \
             patch.object(server, "call_deepseek", side_effect=lambda messages, **_kwargs: _review(messages)), \
             patch.object(server, "call_kimi", side_effect=lambda messages, **_kwargs: _review(messages)), \
             patch.object(server, "parse_json_object", side_effect=lambda value: value):
            result = server.validate_social_trends_with_models(_result(items))

        self.assertEqual(result["qa"]["threeFlagships"]["status"], "insufficient_evidence")
        self.assertEqual(result["verifiedComparisonItems"], [])
        self.assertIn("返回不完整", result["qa"]["threeFlagships"]["errors"]["reviewer_1"])
        self.assertEqual(result["unifiedInsight"]["publicationStatus"], "withheld")

    def test_partial_collection_cannot_be_masked_by_aligned_models(self):
        items = [{"id": "own-1", "brandName": "智己", "text": "智己LS9发布", "sentiment": "positive"}]
        payload = _result(items)
        payload["collectionStatus"] = {"status": "partial", "reason": "safety_limit"}
        with patch.object(server, "qwen_config", return_value={"configured": True}), \
             patch.object(server, "deepseek_config", return_value={"configured": True}), \
             patch.object(server, "kimi_config", return_value={"configured": True}), \
             patch.object(server, "call_qwen", side_effect=lambda messages, **_kwargs: _review(messages)), \
             patch.object(server, "call_deepseek", side_effect=lambda messages, **_kwargs: _review(messages)), \
             patch.object(server, "call_kimi", side_effect=lambda messages, **_kwargs: _review(messages)), \
             patch.object(server, "parse_json_object", side_effect=lambda value: value):
            result = server.validate_social_trends_with_models(payload)
        self.assertEqual(result["qa"]["threeFlagships"]["status"], "conditional")
        self.assertEqual(result["unifiedInsight"]["publicationStatus"], "conditional")

    def test_qwen_free_tier_rejection_exposes_provider_code_and_action(self):
        payload = json.dumps({"error": {
            "code": "AllocationQuota.FreeTierOnly",
            "message": "Free quota exhausted",
        }}).encode("utf-8")
        rejection = HTTPError("https://dashscope.test/chat/completions", 403, "Forbidden", {}, BytesIO(payload))
        config = {"configured": True, "base_url": "https://dashscope.test", "model": "qwen-plus"}

        with patch.object(server, "qwen_config", return_value=config), \
             patch.object(server, "env_value", return_value="test-key"), \
             patch.object(server, "urlopen", side_effect=rejection):
            with self.assertRaisesRegex(ValueError, "AllocationQuota.FreeTierOnly.*关闭该模型的开关"):
                server.call_qwen([{"role": "user", "content": "test"}], profile="fast")


if __name__ == "__main__":
    unittest.main()
