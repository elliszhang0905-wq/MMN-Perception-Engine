import copy
import json
import unittest
from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import patch

import server


def _result(items):
    return {
        "keyword": "智己",
        "items": [item for item in items if item.get("brandName") == "智己"],
        "comparisonItems": copy.deepcopy(items),
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
             patch.object(server, "call_qwen", side_effect=qwen), \
             patch.object(server, "call_deepseek", side_effect=deepseek), \
             patch.object(server, "parse_json_object", side_effect=lambda value: value):
            result = server.validate_social_trends_with_models(_result(items))

        self.assertEqual(result["qa"]["dualModel"]["status"], "aligned")
        self.assertEqual(result["qa"]["dualModel"]["reviewedEvidenceCount"], 3)
        self.assertEqual(set(result["qa"]["dualModel"]["verifiedEvidenceIds"]), {"own-1", "peer-1"})
        self.assertEqual({item["id"] for item in result["verifiedComparisonItems"]}, {"own-1", "peer-1"})

    def test_incomplete_provider_output_blocks_all_publication(self):
        items = [{"id": f"item-{index}", "brandName": "零跑", "text": "零跑B01上市", "sentiment": "positive"} for index in range(25)]

        def incomplete_qwen(messages, **_kwargs):
            payload = json.loads(messages[-1]["content"])
            return _review(messages, fail_ids={payload["evidence"][0]["id"]})

        with patch.object(server, "qwen_config", return_value={"configured": True}), \
             patch.object(server, "deepseek_config", return_value={"configured": True}), \
             patch.object(server, "call_qwen", side_effect=incomplete_qwen), \
             patch.object(server, "call_deepseek", side_effect=lambda messages, **_kwargs: _review(messages)), \
             patch.object(server, "parse_json_object", side_effect=lambda value: value):
            result = server.validate_social_trends_with_models(_result(items))

        self.assertEqual(result["qa"]["dualModel"]["status"], "manual_required")
        self.assertEqual(result["verifiedComparisonItems"], [])
        self.assertIn("返回不完整", result["qa"]["dualModel"]["errors"]["qwen"])

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
