import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import server


class ExecutiveBriefReviewTest(unittest.TestCase):
    def valid_review(self, packet):
        return json.dumps(
            {
                "approved": True,
                "summary": packet["candidate"],
                "factsFingerprint": packet["fingerprint"],
                "evidenceIds": ["retail", "wholesale", "nev_retail", "nev_penetration"],
                "inferenceIds": ["retail_pressure", "wholesale_pressure", "nev_resilience", "penetration_buffer"],
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
            {"actionIds": ["p1"]},
            {"vehicleActionIds": ["audi-e7x"]},
            {"issues": ["措辞越界"]},
        ):
            candidate = {**valid, **mutation}
            self.assertFalse(server.normalize_executive_brief_review(json.dumps(candidate, ensure_ascii=False), packet))

    def test_summary_is_published_only_when_both_models_pass(self):
        packet = server.executive_brief_evidence_packet()
        response = self.valid_review(packet)
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(server, "executive_brief_cache_path", return_value=Path(tmp) / "review.json"), \
             patch.object(server, "call_qwen", return_value=response), \
             patch.object(server, "call_deepseek", return_value=response):
            state = server.run_executive_brief_dual_review(packet)
        self.assertEqual(state["status"], "verified")
        self.assertEqual(state["summary"], packet["candidate"])
        self.assertEqual(len(state["actions"]), 3)
        self.assertEqual(len(state["vehicleActions"]), 9)
        self.assertEqual(state["providerChecks"], {"qwen": "verified", "deepseek": "verified"})

    def test_model_failure_keeps_summary_private(self):
        packet = server.executive_brief_evidence_packet()
        response = self.valid_review(packet)
        with tempfile.TemporaryDirectory() as tmp, \
             patch.object(server, "executive_brief_cache_path", return_value=Path(tmp) / "review.json"), \
             patch.object(server, "call_qwen", return_value=response), \
             patch.object(server, "call_deepseek", side_effect=RuntimeError("secret provider detail")):
            state = server.run_executive_brief_dual_review(packet)
        self.assertEqual(state["status"], "pending_review")
        self.assertEqual(state["summary"], "")
        self.assertEqual(state["actions"], [])
        self.assertEqual(state["vehicleActions"], [])
        self.assertNotIn("secret provider detail", json.dumps(state, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
