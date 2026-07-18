import json
import tempfile
import unittest
from pathlib import Path
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

    def test_verified_cycle_is_persisted_without_removing_other_manual_records(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(server, "DATA_DIR", Path(temporary)):
            first = server.sales_warning_cycle_packet("MG4", "2026-04-24", "2026-07-17", "5828")["facts"]
            second = server.sales_warning_cycle_packet("奥迪E7X", "2026-05-29", "2026-07-17", "25846")["facts"]
            server.save_sales_warning_cycle(first, "2026-07-16T19:39:18+00:00")
            server.save_sales_warning_cycle(second, "2026-07-16T19:39:53+00:00")
            stored = server.load_sales_warning_cycles()

        self.assertEqual(set(stored), {"5828", "25846"})
        self.assertEqual(stored["5828"]["launchDate"], "2026-04-24")
        self.assertEqual(stored["25846"]["status"], "verified")

    def test_sales_history_is_read_only_and_starts_at_launch_month(self):
        warning = {"saicModels": [{"seriesId": 25846, "model": "奥迪E7X"}]}
        cycles = {"25846": {"launchDate": "2026-05-29", "status": "verified"}}
        history = {
            "latestPeriod": "2026-06",
            "windowPeriods": ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"],
            "sourceLabel": "懂车帝月销量榜",
            "sourceUrl": "https://www.dongchedi.com/sales",
            "vehicles": {"25846": {"months": [
                {"period": "2026-04", "sales": 99, "rank": 50},
                {"period": "2026-05", "sales": 1200, "rank": 20, "segmentTop3AverageSales": 18000,
                 "segmentTop3Vehicles": [{"model": "车型A", "sales": 20000, "rank": 1}]},
                {"period": "2026-06", "sales": 4017, "rank": 9, "segmentTop3AverageSales": 19500},
            ]}},
        }

        server.attach_sales_warning_history(warning, cycles, history)

        sales_history = warning["saicModels"][0]["salesHistory"]
        self.assertEqual([month["period"] for month in sales_history["months"]], ["2026-05", "2026-06"])
        self.assertEqual(sales_history["scopeLabel"], "上市后 2 个月")
        self.assertEqual(sales_history["status"], "available")
        self.assertEqual(sales_history["months"][0]["segmentTop3AverageSales"], 18000)
        self.assertEqual(sales_history["months"][0]["segmentTop3Vehicles"][0]["model"], "车型A")
        self.assertEqual(cycles["25846"]["launchDate"], "2026-05-29")

    def test_sales_history_reports_missing_month_without_zero_padding(self):
        warning = {"saicModels": [{"seriesId": "25058", "model": "奥迪E5 Sportback"}]}
        cycles = {"25058": {"launchDate": "2025-09-16", "status": "verified"}}
        history = {
            "latestPeriod": "2026-06",
            "windowPeriods": ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"],
            "vehicles": {"25058": {"months": [
                {"period": "2026-01", "sales": 420, "rank": 49},
                {"period": "2026-03", "sales": 510, "rank": 45},
            ]}},
        }

        server.attach_sales_warning_history(warning, cycles, history)

        sales_history = warning["saicModels"][0]["salesHistory"]
        self.assertEqual([month["sales"] for month in sales_history["months"]], [420, 510])
        self.assertEqual(sales_history["status"], "partial")
        self.assertIn("2026-02", sales_history["missingPeriods"])


if __name__ == "__main__":
    unittest.main()
