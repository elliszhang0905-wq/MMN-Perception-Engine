import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import server


class ExecutiveBriefReviewTest(unittest.TestCase):
    def setUp(self):
        self.data_directory = tempfile.TemporaryDirectory()
        self.data_patch = patch.object(server, "DATA_DIR", Path(self.data_directory.name))
        self.data_patch.start()

    def tearDown(self):
        self.data_patch.stop()
        self.data_directory.cleanup()

    def valid_review(self, packet):
        return json.dumps(
            {
                "approved": True,
                "summary": packet["candidate"],
                "factsFingerprint": packet["fingerprint"],
                "evidenceIds": ["retail", "wholesale", "nev_retail", "nev_penetration"],
                "inferenceIds": ["retail_pressure", "wholesale_pressure", "nev_resilience", "penetration_buffer"],
                "brandImplicationIds": [item["id"] for item in packet["brandImplications"]],
                "actionIds": ["p1", "p2", "p3"],
                "vehicleActionIds": [item["id"] for item in packet["vehicleActions"]],
                "issues": [],
            },
            ensure_ascii=False,
        )

    def test_packet_locks_fact_values_and_reverse_calculated_priors(self):
        packet = server.executive_brief_evidence_packet()
        facts = {item["id"]: item for item in packet["facts"]}
        self.assertEqual(facts["retail"]["value"], 44.3)
        self.assertEqual(facts["retail"]["priorValue"], 52.1)
        self.assertEqual(facts["wholesale"]["priorValue"], 51.2)
        self.assertEqual(facts["nev_retail"]["priorValue"], 30.4)
        self.assertEqual(facts["nev_penetration"]["value"], 63.1)
        self.assertEqual(len(packet["inferences"]), 4)
        self.assertEqual([item["id"] for item in packet["actions"]], ["p1", "p2", "p3"])
        self.assertEqual(len(packet["vehicleActions"]), 9)
        self.assertEqual(len(packet["brandImplications"]), 9)
        consulting = packet["brandImplications"][0]["consultingOutput"]
        self.assertEqual(
            consulting["quality"]["sections"],
            ["Executive Conclusion", "Key Findings", "Evidence", "Strategic Implication", "Action Recommendation"],
        )
        self.assertTrue(consulting["quality"]["passed"])
        self.assertTrue(consulting["quality"]["mecePassed"])
        self.assertEqual([item["id"] for item in consulting["evidence"]], ["E1", "E2", "E3"])
        self.assertEqual(next(item for item in packet["vehicleActions"] if item.get("selected"))["model"], "奥迪E7X")
        self.assertEqual(len(packet["fingerprint"]), 64)

    def test_review_requires_exact_summary_fingerprint_and_all_evidence(self):
        packet = server.executive_brief_evidence_packet()
        valid = json.loads(self.valid_review(packet))
        self.assertTrue(server.normalize_executive_brief_review(json.dumps(valid, ensure_ascii=False), packet))
        for mutation in (
            {"summary": "改写后的摘要"},
            {"factsFingerprint": "wrong"},
            {"evidenceIds": ["retail"]},
            {"inferenceIds": ["retail_pressure"]},
            {"brandImplicationIds": ["im"]},
            {"actionIds": ["p1"]},
            {"vehicleActionIds": ["audi-e7x"]},
            {"issues": ["措辞越界"]},
        ):
            candidate = {**valid, **mutation}
            self.assertFalse(server.normalize_executive_brief_review(json.dumps(candidate, ensure_ascii=False), packet))

    def test_summary_is_published_only_when_all_three_models_pass(self):
        packet = server.executive_brief_evidence_packet()
        response = self.valid_review(packet)
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(server, "executive_brief_cache_path", return_value=Path(tmp) / "review.json"), \
             patch.object(server, "call_qwen", return_value=response), \
             patch.object(server, "call_deepseek", return_value=response), \
             patch.object(server, "call_kimi", return_value=response):
            state = server.run_executive_brief_triple_review(packet)
        self.assertEqual(state["status"], "verified")
        self.assertEqual(state["summary"], packet["candidate"])
        self.assertEqual(len(state["actions"]), 3)
        self.assertEqual(len(state["vehicleActions"]), 9)
        self.assertEqual(len(state["brandImplications"]), 9)
        self.assertEqual(
            state["providerChecks"],
            {"flagshipA": "verified", "flagshipB": "verified", "flagshipC": "verified"},
        )
        self.assertTrue(state["reviewCompleted"])

    def test_model_failure_keeps_summary_private(self):
        packet = server.executive_brief_evidence_packet()
        response = self.valid_review(packet)
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(server, "executive_brief_cache_path", return_value=Path(tmp) / "review.json"), \
             patch.object(server, "call_qwen", return_value=response), \
             patch.object(server, "call_deepseek", side_effect=RuntimeError("secret provider detail")), \
             patch.object(server, "call_kimi", return_value=response):
            state = server.run_executive_brief_triple_review(packet)
        self.assertEqual(state["status"], "pending_review")
        self.assertEqual(state["summary"], "")
        self.assertEqual(state["actions"], [])
        self.assertEqual(state["vehicleActions"], [])
        self.assertEqual(state["brandImplications"], [])
        self.assertEqual(state["statusLabel"], "三路旗舰模型交叉验证未通过 · 暂不发布")
        self.assertTrue(state["reviewCompleted"])
        self.assertNotIn("secret provider detail", json.dumps(state, ensure_ascii=False))

    def test_new_weekly_batch_rebuilds_summary_and_starts_review_for_same_batch(self):
        payload = {
            "facts": [
                {"id": "retail", "label": "乘用车零售", "value": 50.0, "unit": "万辆", "yoy": -0.10},
                {"id": "wholesale", "label": "乘用车厂商批发", "value": 48.0, "unit": "万辆", "yoy": -0.12},
                {"id": "nev_retail", "label": "新能源零售", "value": 33.0, "unit": "万辆", "yoy": 0.05},
                {"id": "nev_penetration", "label": "新能源零售渗透率", "value": 66.0, "unit": "%"},
            ],
            "source": {
                "label": "中国汽车流通协会乘用车市场信息联席分会《车市扫描(20260713-0719)》",
                "url": "https://www.cpcaauto.com/newslist.php?types=csjd&id=next",
                "period": "截至2026年7月19日 · 7月月内累计",
                "metricPeriod": "2026年7月1—19日",
                "metricBasis": "month_to_date",
                "naturalWeekPeriod": "2026年7月13—19日",
                "naturalWeekEndDate": "2026-07-19",
            },
            "publishedAt": "2026-07-22 16:00:00",
        }
        captured = {}

        def enqueue(packet, force=False):
            captured["packet"] = packet
            captured["force"] = force
            return True

        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(server, "DATA_DIR", Path(tmp)), \
             patch.object(server, "enqueue_executive_brief_review", side_effect=enqueue):
            result = server.run_weekly_group_dashboard_refresh(payload)

        packet = captured["packet"]
        self.assertEqual(result["status"], "published")
        self.assertTrue(result["reviewStarted"])
        self.assertTrue(captured["force"])
        self.assertEqual(packet["batchId"], result["batchId"])
        self.assertEqual(packet["source"]["naturalWeekPeriod"], "2026年7月13—19日")
        self.assertIn("乘用车零售同比-10%", packet["candidate"])
        self.assertEqual(packet["inferences"][3]["detail"], "新能源零售渗透率为66.0%")


if __name__ == "__main__":
    unittest.main()
