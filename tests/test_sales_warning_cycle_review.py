import json
import unittest
from unittest.mock import patch

import server


def approved_review(messages, **_kwargs):
    payload = json.loads(messages[-1]["content"])
    facts = payload["lockedFacts"]
    return json.dumps({
        "approved": True,
        "factsFingerprint": payload["factsFingerprint"],
        **{key: facts[key] for key in (
            "model", "launchDate", "assessmentDate", "dayOffset", "tLabel",
            "phaseKey", "phaseLabel", "phaseRange",
        )},
        "issues": [],
    }, ensure_ascii=False)


class SalesWarningCycleReviewTest(unittest.TestCase):
    def test_mmn_cycle_uses_natural_day_offset_and_conversion_phase(self):
        packet = server.sales_warning_cycle_packet(
            "奥迪E7X", "2026-05-29", "2026-07-17", series_id="3902"
        )
        self.assertEqual(packet["facts"]["dayOffset"], 49)
        self.assertEqual(packet["facts"]["tLabel"], "T+49")
        self.assertEqual(packet["facts"]["phaseLabel"], "销售转化期")
        self.assertEqual(packet["facts"]["phaseRange"], "T+31～T+90")

    def test_phase_boundaries_match_the_existing_mmn_t_cycle(self):
        self.assertEqual(
            server.sales_warning_cycle_packet("车型A", "2026-05-29", "2026-06-28")["facts"]["phaseKey"],
            "amplify",
        )
        self.assertEqual(
            server.sales_warning_cycle_packet("车型A", "2026-05-29", "2026-06-29")["facts"]["phaseKey"],
            "conversion",
        )
        self.assertEqual(
            server.sales_warning_cycle_packet("车型A", "2026-05-29", "2026-08-28")["facts"]["phaseKey"],
            "validation",
        )

    def test_dual_flagship_review_publishes_only_exact_consensus(self):
        with patch.object(server, "call_qwen", side_effect=approved_review), patch.object(
            server, "call_deepseek", side_effect=approved_review
        ):
            result = server.run_sales_warning_cycle_dual_review(
                "奥迪E7X", "2026-05-29", "2026-07-17", "3902"
            )
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["conclusion"]["phaseLabel"], "销售转化期")
        self.assertEqual(result["providerChecks"], {"flagshipA": "verified", "flagshipB": "verified"})

    def test_one_model_failure_keeps_the_cycle_private(self):
        with patch.object(server, "call_qwen", side_effect=approved_review), patch.object(
            server, "call_deepseek", side_effect=RuntimeError("timeout")
        ):
            result = server.run_sales_warning_cycle_dual_review(
                "奥迪E7X", "2026-05-29", "2026-07-17", "3902"
            )
        self.assertEqual(result["status"], "pending_review")
        self.assertIsNone(result["conclusion"])

    def test_invalid_launch_date_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "正式上市日期"):
            server.sales_warning_cycle_packet("奥迪E7X", "2026-02-30", "2026-07-17")


if __name__ == "__main__":
    unittest.main()
