import json
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from group_dashboard import (
    _baas_price_view,
    build_group_dashboard_payload,
    build_market_dimensions,
    build_sales_warning_demo,
    sales_warning_methodology,
    build_segment_cards,
    parse_cpca_ice_market,
    load_e7x_product_evaluation,
    load_sales_warning,
    _latest_sales_warning_observed_path,
    merge_sales_payloads,
)

ROOT = Path(__file__).resolve().parents[1]


class GroupDashboardTest(unittest.TestCase):
    def test_e7x_loader_resolves_the_canonical_asset_at_call_time(self):
        canonical = ROOT / "data" / "modules" / "product_evaluation" / "e7x_product_evaluation_2026-06.json"
        with patch("group_dashboard.module_path", return_value=canonical) as resolver:
            result = load_e7x_product_evaluation()
        resolver.assert_called_once_with(
            "product_evaluation",
            "e7x_product_evaluation_2026-06.json",
            legacy=("e7x_product_evaluation_2026-06.json",),
        )
        self.assertEqual(result["status"], "available")
        self.assertEqual(len(result["dataset"]["rows"]), 207)

    def test_baas_price_view_covers_all_three_nio_brands(self):
        cases = (
            ("蔚来ET5", "蔚来", "29.80-31.60万", 10.8, "19.00-20.80万（BaaS后）"),
            ("乐道L60", "乐道", "19.28万", 5.7, "13.58万（BaaS后）"),
            ("乐道L80", "乐道", "24.28万", 8.6, "15.68万（BaaS后）"),
            ("乐道L90", "ONVO", "26.58万", 8.6, "17.98万（BaaS后）"),
            ("firefly萤火虫", "萤火虫", "11.98-12.58万", 4.0, "7.98-8.58万（BaaS后）"),
        )

        for model, manufacturer, dealer_price, discount, expected in cases:
            with self.subTest(model=model):
                view = _baas_price_view(model, manufacturer, dealer_price, "dongchedi_dealer_price")
                self.assertTrue(view["baasApplied"])
                self.assertEqual(view["baasDiscountWan"], discount)
                self.assertEqual(view["priceDisplay"], expected)
                self.assertEqual(view["dealerPriceDisplay"], dealer_price)
                self.assertEqual(view["priceSource"], "dongchedi_dealer_price_baas_adjusted")

        regular = _baas_price_view("Model 3", "特斯拉", "23.55-33.95万", "dongchedi_dealer_price")
        self.assertFalse(regular["baasApplied"])
        self.assertEqual(regular["priceDisplay"], "23.55-33.95万")
        self.assertEqual(regular["startPriceWan"], 23.55)

    def test_sales_warning_automatically_selects_latest_period_monitoring_list(self):
        with TemporaryDirectory() as tmp:
            directory = Path(tmp)
            (directory / "sales_warning_observed_2026-06.json").write_text("{}", encoding="utf-8")
            latest = directory / "sales_warning_observed_2026-07.json"
            latest.write_text("{}", encoding="utf-8")

            self.assertEqual(_latest_sales_warning_observed_path(directory), latest)

    def test_sales_warning_methodology_uses_current_full_segment_contract(self):
        warning = {
            "mode": "full_segment_market",
            "summary": {"method": "排除本品后的同细分市场销量前3名竞品中位数"},
            "thresholds": {"redRatio": 0.25, "yellowRatio": 0.5, "greenRatio": 0.8},
        }

        text = sales_warning_methodology(warning)

        self.assertIn("前3名竞品中位数", text)
        self.assertIn("25%", text)
        self.assertIn("50%", text)
        self.assertIn("80%", text)
        self.assertNotIn("前5名", text)
        self.assertNotIn("有效起售价", text)

    def test_full_segment_warning_dataset_replaces_single_segment_demo_when_verified_file_exists(self):
        dataset = {
            "schema_version": "1.0",
            "source": "dongchedi_authenticated_browser",
            "price_contract": {
                "provider": "懂车帝",
                "field": "dealer_price",
                "required_flag": "has_dealer_price=true",
                "fallback": "none",
            },
            "period": "2026-06",
            "captured_at": "2026-07-16T14:00:00+00:00",
            "complete": True,
            "thresholds": {"red_ratio": 0.8, "green_ratio": 1.2},
            "market_count": 2,
            "quality_issues": [],
            "saic_vehicles": [
                {
                    "series_id": 2,
                    "series_name": "上汽车甲",
                    "manufacturer": "上汽集团",
                    "sales_volume": 3000,
                    "price": "20-30万",
                    "body_type": "轿车",
                    "size_class": "中型车",
                    "energy_type": "纯电动",
                    "energy_group": "新能源",
                    "segment_key": "中型车|新能源",
                    "segment_total_sales": 12000,
                    "segment_model_count": 2,
                    "segment_median_sales": 6000,
                    "segment_rank": 2,
                    "competitor_pool_rule": "同尺寸×新能源（纯电动、增程式、插电式混动），仅排除本品",
                    "competitor_pool_count": 1,
                    "competitor_pool": [
                        {"series_id": 1, "series_name": "竞品甲", "manufacturer": "竞品厂商", "sales_volume": 9000, "price": "21-31万"},
                    ],
                    "red_line_sales": 4800,
                    "green_line_sales": 7200,
                    "performance_ratio": 0.5,
                    "warning_level": "red",
                    "quality_status": "verified",
                },
                {
                    "series_id": 4,
                    "series_name": "上汽SUV甲",
                    "manufacturer": "上汽大众",
                    "sales_volume": 6000,
                    "price": "25-35万",
                    "body_type": "SUV",
                    "size_class": "中型SUV",
                    "energy_type": "插电式混动",
                    "energy_group": "新能源",
                    "segment_key": "中型SUV|新能源",
                    "segment_total_sales": 6000,
                    "segment_model_count": 1,
                    "segment_median_sales": 6000,
                    "segment_rank": 1,
                    "red_line_sales": 4800,
                    "green_line_sales": 7200,
                    "performance_ratio": 1.0,
                    "warning_level": "yellow",
                    "quality_status": "verified",
                },
            ],
        }
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "sales_warning_latest.json"
            path.write_text(json.dumps(dataset, ensure_ascii=False), encoding="utf-8")

            result = load_sales_warning(path=path)

        sedan = next(item for item in result["saicModels"] if item["seriesId"] == 2)
        suv = next(item for item in result["saicModels"] if item["seriesId"] == 4)
        self.assertEqual(result["mode"], "full_segment_market")
        self.assertEqual(result["source"]["period"], "2026-06")
        self.assertEqual(result["summary"]["saicModelCount"], 2)
        self.assertEqual(sedan["segmentLabel"], "中型车 · 新能源")
        self.assertEqual(sedan["energyType"], "纯电动")
        self.assertEqual(sedan["segmentEnergyType"], "新能源")
        self.assertEqual(sedan["marketSales"], 12000)
        self.assertEqual(sedan["benchmark"], 6000)
        self.assertEqual(sedan["peerCount"], 1)
        self.assertEqual(sedan["peerBasis"], "同尺寸×新能源（纯电动、增程式、插电式混动），仅排除本品")
        self.assertEqual([item["model"] for item in sedan["benchmarkAuditPeers"]], ["竞品甲"])
        self.assertEqual(sedan["rank"], 2)
        self.assertEqual(sedan["level"], "red")
        self.assertEqual(suv["marketSales"], 6000)
        self.assertEqual(suv["level"], "yellow")

    def test_full_segment_exposes_top3_and_three_distinct_median_near_peers_for_policy_comparison(self):
        source_path = ROOT / "data" / "dongchedi_sales" / "sales_warning_latest.json"
        raw = json.loads(source_path.read_text(encoding="utf-8"))
        raw_own = next(item for item in raw["saic_vehicles"] if item["series_name"] == "智己LS8")
        top_ids = {item["series_id"] for item in raw_own["benchmark_pool"]}
        expected_median = sorted(
            (item for item in raw_own["competitor_pool"] if item["series_id"] not in top_ids),
            key=lambda item: (abs(item["sales_volume"] - raw_own["segment_median_sales"]), -item["sales_volume"], item["series_name"]),
        )[:3]

        result = load_sales_warning(path=source_path)
        own = next(item for item in result["saicModels"] if item["model"] == "智己LS8")

        self.assertEqual([item["role"] for item in own["comparisonPeers"][:3]], ["top3"] * 3)
        self.assertEqual(
            [item["model"] for item in own["comparisonPeers"][:3]],
            [item["series_name"] for item in raw_own["benchmark_pool"]],
        )
        self.assertEqual(
            [item["model"] for item in own["medianPeers"]],
            [item["series_name"] for item in expected_median],
        )
        self.assertTrue(all(item["startPriceWan"] > 0 for item in own["comparisonPeers"]))
        self.assertEqual(own["salesMedian"], raw_own["segment_median_sales"])
        self.assertEqual(len(own["benchmarkAuditPeers"]) + 1, own["marketModelCount"])
        self.assertTrue(all(item["startPriceWan"] > 0 for item in own["benchmarkAuditPeers"]))
        self.assertTrue(all(
            item["priceSource"] in {"dongchedi_dealer_price", "dongchedi_dealer_price_baas_adjusted"}
            for item in own["benchmarkAuditPeers"]
        ))
        self.assertTrue(all(item["role"] == "market" for item in own["benchmarkAuditPeers"]))

    def test_all_nio_brand_models_in_all_segment_markets_use_baas_price(self):
        source_path = ROOT / "data" / "dongchedi_sales" / "sales_warning_latest.json"
        result = load_sales_warning(path=source_path)
        affected = [
            peer
            for market in result["saicModels"]
            for peer in market["benchmarkAuditPeers"]
            if peer["manufacturer"] in {"蔚来", "乐道", "萤火虫", "NIO", "ONVO", "firefly"}
        ]

        self.assertEqual(
            {item["model"] for item in affected},
            {
                "乐道L60",
                "乐道L80",
                "乐道L90",
                "蔚来EC6",
                "蔚来ES6",
                "蔚来ES8",
                "蔚来ES9",
                "蔚来ET5",
                "蔚来ET5T",
                "蔚来ET7",
            },
        )
        self.assertTrue(all(item["baasApplied"] for item in affected))
        self.assertTrue(all("BaaS后" in item["priceDisplay"] for item in affected))
        for item in affected:
            self.assertAlmostEqual(
                item["dealerStartPriceWan"] - item["baasDiscountWan"],
                item["startPriceWan"],
                places=2,
            )
        prices = {item["model"]: item["priceDisplay"] for item in affected}
        self.assertEqual(prices["蔚来ET5"], "19.00-20.80万（BaaS后）")
        self.assertEqual(prices["蔚来ET5T"], "19.00-20.80万（BaaS后）")
        self.assertEqual(prices["蔚来ET7"], "32.00-35.00万（BaaS后）")

    def test_incomplete_full_segment_file_falls_back_to_verified_focal_observations(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "sales_warning_latest.json"
            path.write_text('{"complete":false,"period":"2026-06"}', encoding="utf-8")

            result = load_sales_warning(path=path)

        self.assertEqual(result["mode"], "observed_focal_models")
        self.assertEqual(len(result["saicModels"]), 8)
        self.assertEqual(result["summary"]["calculableModelCount"], 2)

    def test_e7x_start_price_uses_dongchedi_dealer_quote(self):
        result = load_sales_warning()
        e7x = next(item for item in result["saicModels"] if item["model"] == "奥迪E7X")

        self.assertEqual(e7x["vehicleStartPriceWan"], 26.98)
        self.assertEqual(e7x["vehicleStartPriceSource"], "dongchedi_dealer_price")
        self.assertEqual(e7x["priceDisplay"], "26.98-35.98万")

    def test_full_segment_rejects_non_dealer_price_contract(self):
        dataset = {
            "schema_version": "1.0",
            "source": "dongchedi_public_rank_api",
            "period": "2026-06",
            "complete": True,
            "thresholds": {"red_ratio": 0.25, "yellow_ratio": 0.5, "green_ratio": 0.8},
            "price_contract": {"provider": "懂车帝", "field": "price", "fallback": "manual"},
            "saic_vehicles": [],
        }
        with TemporaryDirectory() as tmp:
            observed_path = Path(tmp) / "observed.json"
            observed_path.write_text(json.dumps({
                "source": "dongchedi_user_verified_observations",
                "period": "2026-06",
                "vehicles": [],
            }, ensure_ascii=False), encoding="utf-8")
            full_path = Path(tmp) / "full.json"
            full_path.write_text(json.dumps(dataset, ensure_ascii=False), encoding="utf-8")

            result = load_sales_warning(path=full_path, observed_path=observed_path)

        self.assertEqual(result["mode"], "observed_focal_models")
        self.assertEqual(result["saicModels"], [])

    def test_observed_warning_preserves_verified_exact_market_metrics(self):
        with TemporaryDirectory() as tmp:
            result = load_sales_warning(path=Path(tmp) / "missing_full_market.json")
        e5 = next(item for item in result["saicModels"] if item["model"] == "奥迪E5 Sportback")
        z7 = next(item for item in result["saicModels"] if item["model"] == "尚界Z7")
        e7 = next(item for item in result["saicModels"] if item["model"] == "别克至境E7")

        self.assertEqual((e5["marketSales"], e5["marketModelCount"], e5["benchmark"]), (54665, 20, 1815.0))
        self.assertEqual(e5["marketShare"], 0.0049)
        self.assertEqual(e5["performanceRate"], 0.1488)
        self.assertEqual(e5["level"], "red")
        self.assertEqual((z7["marketSales"], z7["marketModelCount"], z7["benchmark"]), (49784, 23, 370.0))
        self.assertEqual(z7["marketShare"], 0.1265)
        self.assertEqual(z7["level"], "green")
        self.assertIsNone(e7["marketSales"])
        self.assertEqual(e7["sales"], 5555)

    def test_deploy_publishes_e7x_evaluation_into_persistent_data_volume(self):
        deploy_script = (ROOT / "scripts" / "deploy.sh").read_text(encoding="utf-8")
        self.assertIn("data/modules/product_evaluation/e7x_product_evaluation_2026-06.json", deploy_script)
        self.assertIn("mmn-app:/app/data/modules/product_evaluation/e7x_product_evaluation_2026-06.json", deploy_script)
        self.assertIn("data/imports/raw/product_evaluation", deploy_script)
        self.assertIn("data/sales_warning_demo_2026-06.json", deploy_script)
        self.assertIn("mmn-app:/app/data/sales_warning_demo_2026-06.json", deploy_script)
        self.assertIn("sales_warning_observed_????-??.json", deploy_script)
        self.assertIn('"mmn-app:/app/$observed_file"', deploy_script)
        self.assertIn("data/dongchedi_sales/sales_warning_history.json", deploy_script)
        self.assertIn("mmn-app:/app/data/dongchedi_sales/sales_warning_history.json", deploy_script)
        self.assertIn("保留服务器已有车型上市日期，不用版本文件覆盖", deploy_script)
        self.assertIn("restart mmn-app mmn-scheduler", deploy_script)
        self.assertIn('APP_HEALTH" == "healthy', deploy_script)

    def test_sales_warning_demo_uses_full_dongchedi_segment_without_price_filter(self):
        result = build_sales_warning_demo()
        e5 = next(item for item in result["saicModels"] if item["model"] == "奥迪E5 Sportback")
        et5t = next(item for item in result["ranking"] if item["model"] == "蔚来ET5T")

        self.assertEqual(result["summary"]["marketSales"], 104449)
        self.assertEqual(result["summary"]["modelCount"], 43)
        self.assertEqual(result["summary"]["levelRules"]["green"], "表现率≥80%")
        self.assertIn("黄色、红色", result["summary"]["levelRules"]["warningDefinition"])
        self.assertEqual(et5t["effectivePriceMin"], 19.8)
        self.assertEqual(et5t["priceRule"], "车电分离口径 -10万")
        self.assertEqual(e5["sales"], 270)
        self.assertEqual(e5["level"], "red")
        self.assertEqual(len(e5["benchmarkPeers"]), 3)
        self.assertEqual(e5["peerBasis"], "懂车帝同细分市场全量（仅排除本品）")
        self.assertEqual(e5["peerCount"], 42)
        self.assertEqual(len(e5["benchmarkAuditPeers"]), 42)
        self.assertNotIn("奥迪E5 Sportback", [item["model"] for item in e5["benchmarkAuditPeers"]])
        self.assertNotIn("有效起售价", result["summary"]["method"])
        self.assertLess(e5["performanceRate"], 0.25)
        self.assertEqual(e5["yellowLine"], round(e5["benchmark"] * 0.5))
        self.assertEqual(e5["redLine"], round(e5["benchmark"] * 0.25))

    def test_sales_warning_demo_only_alerts_saic_models_and_exposes_workflow(self):
        result = build_sales_warning_demo()
        names = {item["model"] for item in result["saicModels"]}

        self.assertIn("尚界Z7", names)
        self.assertIn("飞凡F7", names)
        self.assertIn("五菱星光EV", names)
        self.assertNotIn("小米SU7", names)
        self.assertTrue(all(item["workflow"]["closeCriteria"] for item in result["saicModels"]))

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("create table social_trend_snapshots (org_id text, edition text, keyword text, result_json text, created_at text)")
        self.conn.execute("create table vertical_rank_assets (org_id text, edition text, platform text, period text, own_model text, competitor_model text, positive_rank integer, negative_rank integer, compare_share real, source_file text, updated_at text)")
        self.conn.execute("create table model_router_decisions (edition text, project_json text, created_at text, updated_at text)")

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
        self.conn.execute("insert into vertical_rank_assets values (?,?,?,?,?,?,?,?,?,?,?)", ("local", "china", "懂车帝", "2026.07.09", "奥迪E7X", "竞品A", 2, 12, 0.13, "上汽集团八车周对比次数正反向排名.xlsx", "2026-07-15T08:00:00Z"))
        result = build_group_dashboard_payload(self.conn, {"items": []})
        e7x = next(item for item in result["launches"] if item["model"] == "奥迪E7X")
        mg4 = next(item for item in result["launches"] if item["model"] == "MG4")
        self.assertEqual(e7x["voice"]["contentCount"], 1)
        self.assertEqual(e7x["voc"]["positiveTop10"], 1)
        self.assertIsNone(mg4["voice"]["contentCount"])
        self.assertEqual(result["kpis"]["voiceReadyModels"], 1)

    def test_sales_warning_monitors_only_latest_dongchedi_table_own_models_and_ignores_spaces(self):
        rows = [
            ("local", "china", "懂车帝", "2026.07.09", "奥迪 E5 Sportback", "小米SU7", 1, 3, 0.16, "上汽集团十二车周对比次数正反向排名.xlsx", "2026-07-16T08:00:00Z"),
            ("local", "china", "懂车帝", "2026.07.09", "MG 4", "海豚", 2, 4, 0.11, "上汽集团十二车周对比次数正反向排名.xlsx", "2026-07-16T08:00:00Z"),
            ("local", "china", "懂车帝", "2026.07.02", "飞凡F7", "小鹏P7", 1, 1, 0.10, "旧表.xlsx", "2026-07-15T08:00:00Z"),
        ]
        self.conn.executemany("insert into vertical_rank_assets values (?,?,?,?,?,?,?,?,?,?,?)", rows)

        result = build_group_dashboard_payload(self.conn, {"items": []})
        warning = result["salesWarnings"]
        names = {item["model"] for item in warning["saicModels"]}

        self.assertEqual(warning["monitoring"]["models"], ["奥迪E5 Sportback", "MG4"])
        self.assertEqual(warning["summary"]["trackedModelCount"], 2)
        self.assertEqual(names, {"奥迪E5 Sportback", "MG4"})
        self.assertEqual(warning["summary"]["salesReadyModelCount"], 2)
        self.assertEqual(warning["summary"]["calculableModelCount"], 2)
        self.assertEqual(warning["summary"]["pendingModelCount"], 0)
        self.assertNotIn("飞凡F7", names)
        e5 = next(item for item in warning["saicModels"] if item["model"] == "奥迪E5 Sportback")
        self.assertEqual(e5["comparisonSignal"]["activeCompetitor"], "小米SU7")
        self.assertEqual(e5["comparisonSignal"]["reverseCompetitor"], "小米SU7")

    def test_sales_warning_prefills_latest_mmn_database_cycle_and_leaves_missing_models_manual(self):
        self.conn.executemany("insert into vertical_rank_assets values (?,?,?,?,?,?,?,?,?,?,?)", [
            ("local", "china", "懂车帝", "2026.07.09", "奥迪E7X", "Model Y", 1, 2, 0.15, "上汽集团八车周对比次数正反向排名.xlsx", "2026-07-16T08:00:00Z"),
            ("local", "china", "懂车帝", "2026.07.09", "奥迪E5 Sportback", "小米SU7", 1, 2, 0.15, "上汽集团八车周对比次数正反向排名.xlsx", "2026-07-16T08:00:00Z"),
        ])
        self.conn.executemany("insert into model_router_decisions values (?,?,?,?)", [
            ("china", json.dumps({"model": "AUDI E7X", "stage": "上市中", "_org_id": "local"}), "2026-07-15T19:50:48Z", "2026-07-15T19:50:48Z"),
            ("china", json.dumps({"model": "奥迪 E7X", "stage": "销售转化（T+31～T+90）", "_org_id": "local"}), "2026-07-15T22:52:25Z", "2026-07-15T22:52:25Z"),
        ])

        result = build_group_dashboard_payload(self.conn, {"items": []})
        e7x = next(item for item in result["salesWarnings"]["saicModels"] if item["model"] == "奥迪E7X")
        e5 = next(item for item in result["salesWarnings"]["saicModels"] if item["model"] == "奥迪E5 Sportback")

        self.assertEqual(e7x["cycle"], "T+31～T+90")
        self.assertEqual(e7x["cycleStage"], "销售转化（T+31～T+90）")
        self.assertEqual(e7x["cycleSource"], "MMN数据库")
        self.assertNotIn("cycle", e5)
        self.assertEqual(result["salesWarnings"]["cycleLookup"]["databaseMatchedCount"], 1)

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
        self.assertEqual(len(result["dataset"]["rows"]), 207)
        self.assertEqual(len(result["dataset"]["summaryHeat"]["奥迪E7X"]["platformVolume"]), 9)
        self.assertEqual(len(result["dataset"]["summaryPlatformNsr"]["奥迪E7X"]), 7)
        self.assertEqual(result["dataset"]["importQuality"]["attributeNsrSources"], ["全网", "垂媒车主口碑", "抖音"])
        self.assertRegex(result["sourceAsset"]["sha256"], r"^[0-9a-f]{64}$")

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
        self.assertEqual(result["salesWarnings"]["segment"]["id"], "dynamic-by-selected-vehicle")
        self.assertTrue(any("燃油采用乘联会 ICE 零售整体市场" in item for item in result["methodology"]))


if __name__ == "__main__":
    unittest.main()
