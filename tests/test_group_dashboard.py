import json
import sqlite3
import unittest
from pathlib import Path

from group_dashboard import (
    build_group_dashboard_payload,
    build_market_dimensions,
    build_segment_cards,
    load_e7x_product_evaluation,
    merge_sales_payloads,
)

ROOT = Path(__file__).resolve().parents[1]


class GroupDashboardTest(unittest.TestCase):
    def test_deploy_publishes_e7x_evaluation_into_persistent_data_volume(self):
        deploy_script = (ROOT / "scripts" / "deploy.sh").read_text(encoding="utf-8")
        self.assertIn("data/e7x_product_evaluation_2026-06.json", deploy_script)
        self.assertIn("mmn-app:/app/data/e7x_product_evaluation_2026-06.json", deploy_script)

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("create table social_trend_snapshots (org_id text, edition text, keyword text, result_json text, created_at text)")
        self.conn.execute("create table vertical_rank_assets (org_id text, edition text, platform text, period text, own_model text, competitor_model text, positive_rank integer, negative_rank integer, updated_at text)")

    def tearDown(self):
        self.conn.close()

    def test_segment_cards_use_real_period_totals(self):
        payload = {"items": [
            {"rank_type": "ev", "period_start": "2026-05-01", "rank": 1, "series_name": "A", "brand_name": "其他", "sales_volume": 100},
            {"rank_type": "ev", "period_start": "2026-06-01", "rank": 1, "series_name": "B", "brand_name": "智己", "sales_volume": 120},
            {"rank_type": "mid_suv", "period_start": "2026-06-01", "rank": 2, "series_name": "探岳", "brand_name": "大众", "sales_volume": 90},
            {"rank_type": "mid_suv", "period_start": "2026-06-01", "rank": 3, "series_name": "途观L", "brand_name": "大众", "sales_volume": 80},
        ]}
        card = next(item for item in build_segment_cards(payload) if item["key"] == "ev")
        self.assertEqual(card["top10Sales"], 120)
        self.assertEqual(card["previousTop10Sales"], 100)
        self.assertEqual(card["changeRate"], 0.2)
        self.assertEqual(card["saicTop10"][0]["brand"], "智己")
        suv = next(item for item in build_segment_cards(payload) if item["key"] == "mid_suv")
        self.assertEqual([item["model"] for item in suv["saicTop10"]], ["途观L"])

    def test_sales_snapshots_merge_without_duplicate_records(self):
        merged = merge_sales_payloads([
            {"items": [{"record_id": "a", "rank_type": "ev", "sales_volume": 100}]},
            {"items": [{"record_id": "a", "rank_type": "ev", "sales_volume": 100}, {"record_id": "b", "rank_type": "ev", "sales_volume": 120}]},
        ])
        self.assertEqual(len(merged["items"]), 2)

    def test_market_dimensions_separate_energy_and_body_classes(self):
        dimensions = build_market_dimensions({"items": []})
        self.assertEqual([item["label"] for item in dimensions], ["能源形式", "轿车级别", "SUV 级别", "MPV 级别"])
        energy = dimensions[0]["items"]
        self.assertEqual([item["label"] for item in energy], ["纯电", "插电式混动", "增程式", "燃油"])
        self.assertEqual(energy[-1]["status"], "missing")

    def test_payload_keeps_missing_voice_empty_and_uses_vertical_signal(self):
        social = {"items": [{"heat": 12}], "platforms": [{"contentCount": 1}], "commentInsights": {"total": 3}, "confidenceLabel": "中"}
        self.conn.execute("insert into social_trend_snapshots values (?,?,?,?,?)", ("local", "china", "奥迪E7X", json.dumps(social), "2026-07-15T08:00:00Z"))
        self.conn.execute("insert into vertical_rank_assets values (?,?,?,?,?,?,?,?,?)", ("local", "china", "懂车帝", "2026.07.09", "奥迪E7X", "竞品A", 2, 12, "2026-07-15T08:00:00Z"))
        result = build_group_dashboard_payload(self.conn, {"items": []})
        e7x = next(item for item in result["launches"] if item["model"] == "奥迪E7X")
        mg4 = next(item for item in result["launches"] if item["model"] == "MG4")
        self.assertEqual(e7x["voice"]["contentCount"], 1)
        self.assertEqual(e7x["voc"]["positiveTop10"], 1)
        self.assertIsNone(mg4["voice"]["contentCount"])
        self.assertEqual(result["kpis"]["voiceReadyModels"], 1)

    def test_e7x_product_evaluation_preserves_workbook_metrics_and_ranks(self):
        result = load_e7x_product_evaluation()
        own = next(item for item in result["models"] if item["isOwn"])
        self.assertEqual(result["source"]["period"], "2026.06.01—2026.06.30")
        self.assertEqual(own["voice"], 235579)
        self.assertEqual(own["engagement"], 2169813)
        self.assertEqual(own["voiceRank"], 4)
        self.assertEqual(own["engagementRank"], 3)
        self.assertEqual(own["overallNsrRank"], 2)
        self.assertEqual(own["verticalNsrRank"], 1)
        self.assertEqual(result["validVerticalModels"], 4)

    def test_e7x_attribute_delta_is_computed_without_inventing_sample_size(self):
        result = load_e7x_product_evaluation()
        cost = next(item for item in result["attributes"] if item["attribute"] == "用车成本")
        self.assertEqual(cost["deltaVsAverage"], -0.1249)
        self.assertNotIn("sampleSize", cost)

    def test_payload_exposes_e7x_product_view(self):
        result = build_group_dashboard_payload(self.conn, {"items": []})
        self.assertEqual(result["productEvaluation"]["ownModel"], "奥迪E7X")
        self.assertEqual(result["productEvaluation"]["positioning"]["energyRankKey"], "ev")
        self.assertEqual(len(result["productEvaluation"]["models"]), 5)


if __name__ == "__main__":
    unittest.main()
