import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import server


class SalesWarningReviewTest(unittest.TestCase):
    def valid_review(self, packet):
        return json.dumps(
            {
                "approved": True,
                "factsFingerprint": packet["fingerprint"],
                "reviewedModelIds": packet["reviewedModelIds"],
                "warningIds": packet["warningIds"],
                "issues": [],
            },
            ensure_ascii=False,
        )

    def test_packet_locks_segment_prices_thresholds_and_all_saic_models(self):
        packet = server.sales_warning_evidence_packet()
        facts = packet["facts"]
        e5 = next(item for item in facts["saicModels"] if item["model"] == "奥迪E5 Sportback")

        self.assertEqual(facts["summary"]["marketSales"], 104449)
        self.assertEqual(facts["summary"]["levelRules"]["yellow"], "25%≤表现率＜80%")
        self.assertEqual(facts["segment"]["energyType"], "纯电动")
        self.assertEqual(e5["sales"], 270)
        self.assertEqual(e5["level"], "red")
        self.assertEqual(set(packet["reviewedModelIds"]), {item["model"] for item in facts["saicModels"]})
        self.assertEqual(set(packet["warningIds"]), {item["model"] for item in facts["saicModels"] if item["level"] != "green"})
        self.assertEqual(len(packet["reviewedModelIds"]), 9)
        self.assertEqual(len(packet["warningIds"]), facts["summary"]["warningCount"])
        self.assertTrue(all(item["peerCount"] == facts["summary"]["modelCount"] - 1 for item in facts["saicModels"]))
        self.assertTrue(all(len(item["benchmarkAuditPeers"]) == item["peerCount"] for item in facts["saicModels"]))
        self.assertEqual(len(packet["fingerprint"]), 64)

    def test_review_requires_exact_fingerprint_all_models_and_no_issues(self):
        packet = server.sales_warning_evidence_packet()
        valid = json.loads(self.valid_review(packet))
        self.assertTrue(server.normalize_sales_warning_review(json.dumps(valid, ensure_ascii=False), packet))
        for mutation in (
            {"factsFingerprint": "wrong"},
            {"reviewedModelIds": ["奥迪E5 Sportback"]},
            {"warningIds": ["奥迪E5 Sportback"]},
            {"issues": ["竞品池不一致"]},
            {"approved": False},
        ):
            self.assertFalse(server.normalize_sales_warning_review(json.dumps({**valid, **mutation}, ensure_ascii=False), packet))
        self.assertFalse(server.normalize_sales_warning_review("", packet))

    def test_full_segment_packet_locks_each_models_own_market_and_dynamic_thresholds(self):
        warning = {
            "mode": "full_segment_market",
            "source": {"period": "2026-06", "complete": True},
            "segment": {"id": "dynamic-by-selected-vehicle"},
            "summary": {"levelRules": {"red": "表现率＜80%", "yellow": "80%≤表现率≤120%", "green": "表现率＞120%"}},
            "thresholds": {"redRatio": 0.8, "greenRatio": 1.2},
            "qualityIssues": [],
            "saicModels": [{
                "seriesId": 2,
                "model": "上汽车甲",
                "brand": "上汽集团",
                "bodyType": "轿车",
                "sizeClass": "中型车",
                "energyType": "纯电动",
                "segmentKey": "轿车|中型车|纯电动",
                "marketSales": 12000,
                "marketModelCount": 2,
                "sales": 3000,
                "rank": 2,
                "benchmark": 6000,
                "performanceRate": 0.5,
                "redLine": 4800,
                "greenLine": 7200,
                "level": "red",
                "qualityStatus": "verified",
            }],
        }

        packet = server.sales_warning_evidence_packet(warning)
        facts = packet["facts"]
        item = facts["saicModels"][0]

        self.assertEqual(facts["thresholds"], {"redRatio": 0.8, "greenRatio": 1.2})
        self.assertEqual(item["segmentKey"], "轿车|中型车|纯电动")
        self.assertEqual(item["marketSales"], 12000)
        self.assertEqual(item["marketModelCount"], 2)
        self.assertEqual(item["greenLine"], 7200)

    def test_management_conclusion_is_published_only_when_both_models_pass(self):
        packet = server.sales_warning_evidence_packet()
        response = self.valid_review(packet)
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(server, "sales_warning_review_cache_path", return_value=Path(tmp) / "review.json"), \
             patch.object(server, "call_qwen", return_value=response), \
             patch.object(server, "call_deepseek", return_value=response):
            state = server.run_sales_warning_dual_review(packet)
        self.assertEqual(state["status"], "verified")
        self.assertTrue(state["managementConclusionPublished"])
        self.assertEqual(state["providerChecks"], {"flagshipA": "verified", "flagshipB": "verified"})

    def test_one_model_failure_keeps_management_conclusion_private(self):
        packet = server.sales_warning_evidence_packet()
        response = self.valid_review(packet)
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(server, "sales_warning_review_cache_path", return_value=Path(tmp) / "review.json"), \
             patch.object(server, "call_qwen", return_value=response), \
             patch.object(server, "call_deepseek", side_effect=RuntimeError("provider detail")):
            state = server.run_sales_warning_dual_review(packet)
        self.assertEqual(state["status"], "pending_review")
        self.assertFalse(state["managementConclusionPublished"])
        self.assertNotIn("provider detail", json.dumps(state, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
