import runpy
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = runpy.run_path(str(ROOT / "scripts" / "refresh_sales_warning_history.py"))


class SalesWarningHistoryRefreshTest(unittest.TestCase):
    def test_segment_top3_reference_uses_ranked_market_average(self):
        rows = [
            {"rank": 3, "series_id": 3, "series_name": "车型C", "count": 100},
            {"rank": 1, "series_id": 1, "series_name": "车型A", "count": 400},
            {"rank": 4, "series_id": 4, "series_name": "车型D", "count": 50},
            {"rank": 2, "series_id": 2, "series_name": "车型B", "count": 250},
        ]

        reference = SCRIPT["segment_top3_reference"](rows)

        self.assertEqual(reference["averageSales"], 250)
        self.assertEqual([item["model"] for item in reference["vehicles"]], ["车型A", "车型B", "车型C"])

    def test_segment_top3_reference_rejects_incomplete_market(self):
        with self.assertRaisesRegex(RuntimeError, "不足3款车型"):
            SCRIPT["segment_top3_reference"]([{"rank": 1, "count": 10}, {"rank": 2, "count": 5}])


if __name__ == "__main__":
    unittest.main()
