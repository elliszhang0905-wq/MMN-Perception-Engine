import json
import sqlite3
import unittest
from pathlib import Path

from group_dashboard import (
    build_group_dashboard_payload,
    build_market_dimensions,
    build_segment_cards,
    parse_cpca_ice_market,
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

    def test_fuel_card_derives_saic_entry_from_overall_top10_when_independent_rank_is_missing(self):
        payload = {"items": [
            {"rank_type": "series", "period_start": "2026-06-01", "rank": 1, "series_name": "星愿", "brand_name": "吉利银河", "sales_volume": 33000},
            {"rank_type": "series", "period_start": "2026-06-01", "rank": 9, "series_name": "凯美瑞", "brand_name": "丰田", "sales_volume": 17114},
            {"rank_type": "series", "period_start": "2026-06-01", "rank": 10, "series_name": "朗逸", "brand_name": "大众", "sales_volume": 15444},
            {"rank_type": "new_energy", "period_start": "2026-06-01", "rank": 1, "series_name": "星愿", "brand_name": "吉利银河", "sales_volume": 33000},
        ]}

        card = next(item for item in build_segment_cards(payload) if item["key"] == "fuel")

        self.assertEqual(card["status"], "available")
        self.assertEqual(card["dataBasis"], "overall_top10_minus_new_energy")
        self.assertEqual(card["top10Sales"], 32558)
        self.assertEqual(card["saicTop10"], [{
            "rank": 10,
            "model": "朗逸",
            "brand": "大众",
            "sales": 15444,
        }])
        self.assertIn("全国总榜 Top10", card["scopeNote"])

    def test_fuel_card_prefers_independent_rank_when_it_is_available(self):
        payload = {"items": [
            {"rank_type": "fuel", "period_start": "2026-06-01", "rank": 1, "series_name": "朗逸", "brand_name": "大众", "sales_volume": 15444},
            {"rank_type": "series", "period_start": "2026-06-01", "rank": 10, "series_name": "朗逸", "brand_name": "大众", "sales_volume": 15444},
            {"rank_type": "new_energy", "period_start": "2026-06-01", "rank": 1, "series_name": "星愿", "brand_name": "吉利银河", "sales_volume": 33000},
        ]}

        card = next(item for item in build_segment_cards(payload) if item["key"] == "fuel")

        self.assertEqual(card["dataBasis"], "independent_rank")
        self.assertEqual(card["saicTop10"][0]["rank"], 1)

    def test_fuel_card_does_not_compare_months_with_different_data_basis(self):
        payload = {"items": [
            {"rank_type": "series", "period_start": "2026-05-01", "rank": 1, "series_name": "朗逸", "brand_name": "大众", "sales_volume": 100},
            {"rank_type": "new_energy", "period_start": "2026-05-01", "rank": 1, "series_name": "星愿", "brand_name": "吉利银河", "sales_volume": 90},
            {"rank_type": "fuel", "period_start": "2026-06-01", "rank": 1, "series_name": "朗逸", "brand_name": "大众", "sales_volume": 200},
        ]}

        card = next(item for item in build_segment_cards(payload) if item["key"] == "fuel")

        self.assertEqual(card["dataBasis"], "independent_rank")
        self.assertEqual(card["previousDataBasis"], "overall_top10_minus_new_energy")
        self.assertTrue(card["comparisonBasisChanged"])
        self.assertIsNone(card["changeRate"])

    def test_fuel_card_marks_reverse_switch_to_derived_basis(self):
        payload = {"items": [
            {"rank_type": "fuel", "period_start": "2026-05-01", "rank": 1, "series_name": "朗逸", "brand_name": "大众", "sales_volume": 100},
            {"rank_type": "series", "period_start": "2026-06-01", "rank": 1, "series_name": "朗逸", "brand_name": "大众", "sales_volume": 200},
            {"rank_type": "new_energy", "period_start": "2026-06-01", "rank": 1, "series_name": "星愿", "brand_name": "吉利银河", "sales_volume": 180},
        ]}

        card = next(item for item in build_segment_cards(payload) if item["key"] == "fuel")

        self.assertEqual(card["dataBasis"], "overall_top10_minus_new_energy")
        self.assertEqual(card["previousDataBasis"], "independent_rank")
        self.assertTrue(card["comparisonBasisChanged"])
        self.assertIsNone(card["changeRate"])

    def test_cpca_ice_market_uses_retail_volume_and_keeps_saic_overall_rank_separate(self):
        cpca = [
            {"category": "整体市场", "dataList": []},
            {"category": "", "dataList": []},
            {"category": "", "dataList": [
                {"月份": "2026-5月", "ICE": [86.2828, 55.9863, 39.0, 37.1], "NEV": [135.2027, 95.017, 61.0, 62.9]},
                {"月份": "2026-6月", "ICE": [87.5515, 59.5171, 37.1, 37.2], "NEV": [148.1452, 100.6753, 62.9, 62.8]},
            ]},
        ]
        sales = {"items": [
            {"rank_type": "series", "period_start": "2026-06-01", "rank": 1, "series_name": "星愿", "brand_name": "吉利银河", "sales_volume": 33000},
            {"rank_type": "series", "period_start": "2026-06-01", "rank": 10, "series_name": "朗逸", "brand_name": "大众", "sales_volume": 15444},
            {"rank_type": "new_energy", "period_start": "2026-06-01", "rank": 1, "series_name": "星愿", "brand_name": "吉利银河", "sales_volume": 33000},
        ]}

        parsed = parse_cpca_ice_market(cpca)
        result = build_group_dashboard_payload(self.conn, sales, fuel_market=parsed)
        fuel = next(item for item in result["marketDimensions"][0]["items"] if item["key"] == "fuel")

        self.assertEqual(parsed["latestPeriod"], "2026-06")
        self.assertEqual(parsed["retailSales"], 595171)
        self.assertEqual(parsed["previousRetailSales"], 559863)
        self.assertEqual(parsed["retailShare"], 0.372)
        self.assertEqual(parsed["changeRate"], 0.0631)
        self.assertEqual(fuel["dataBasis"], "cpca_ice_retail_market")
        self.assertEqual(fuel["marketSales"], 595171)
        self.assertEqual(fuel["changeRate"], 0.0631)
        self.assertEqual(fuel["saicRankBasis"], "dongchedi_national_overall_top10")
        self.assertEqual(fuel["saicRankPeriod"], "2026-06")
        self.assertFalse(fuel["sourceStale"])
        self.assertEqual(fuel["saicTop10"][0]["model"], "朗逸")

    def test_cpca_ice_market_rejects_nonconsecutive_or_out_of_range_rows(self):
        nonconsecutive = [{"dataList": [
            {"月份": "2026-4月", "ICE": [80, 50, 40, 38]},
            {"月份": "2026-6月", "ICE": [88, 60, 37, 37]},
        ]}]
        invalid_share = [{"dataList": [
            {"月份": "2026-5月", "ICE": [80, 50, 40, 38]},
            {"月份": "2026-6月", "ICE": [88, 60, 37, 137]},
        ]}]

        self.assertIsNone(parse_cpca_ice_market(nonconsecutive))
        self.assertIsNone(parse_cpca_ice_market(invalid_share))

    def test_cpca_market_period_does_not_overwrite_dongchedi_rank_period(self):
        cpca = parse_cpca_ice_market([{"dataList": [
            {"月份": "2026-6月", "ICE": [88, 60, 37, 37]},
            {"月份": "2026-7月", "ICE": [90, 62, 36, 36]},
        ]}])
        sales = {"items": [
            {"rank_type": "series", "period_start": "2026-06-01", "rank": 10, "series_name": "朗逸", "brand_name": "大众", "sales_volume": 15444},
            {"rank_type": "new_energy", "period_start": "2026-06-01", "rank": 1, "series_name": "星愿", "brand_name": "吉利银河", "sales_volume": 33000},
        ]}

        result = build_group_dashboard_payload(self.conn, sales, fuel_market=cpca)
        fuel = next(item for item in result["marketDimensions"][0]["items"] if item["key"] == "fuel")

        self.assertEqual(fuel["latestPeriod"], "2026-07")
        self.assertEqual(fuel["saicRankPeriod"], "2026-06")

    def test_cpca_market_does_not_claim_a_dongchedi_rank_when_rank_data_is_missing(self):
        cpca = parse_cpca_ice_market([{"dataList": [
            {"月份": "2026-5月", "ICE": [86, 56, 39, 37]},
            {"月份": "2026-6月", "ICE": [88, 60, 37, 37]},
        ]}])

        result = build_group_dashboard_payload(self.conn, {"items": []}, fuel_market=cpca)
        fuel = next(item for item in result["marketDimensions"][0]["items"] if item["key"] == "fuel")

        self.assertEqual(fuel["saicRankBasis"], "missing")
        self.assertEqual(fuel["saicRankPeriod"], "")
        self.assertIn("暂未接入", fuel["scopeNote"])

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
        self.assertTrue(any("燃油采用乘联会 ICE 零售整体市场" in item for item in result["methodology"]))


if __name__ == "__main__":
    unittest.main()
