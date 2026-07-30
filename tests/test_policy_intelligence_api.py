from pathlib import Path
import json
import sqlite3
import unittest
from unittest.mock import patch

from server import (
    TRIAL_POST_ALLOWED_PATHS,
    run_policy_strategy_validation,
    trusted_policy_vehicle_profile,
    validate_policy_vehicle_inputs,
)


ROOT = Path(__file__).resolve().parents[1]


class PolicyIntelligenceApiContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = (ROOT / "server.py").read_text(encoding="utf-8")

    def test_server_initializes_policy_domain_without_inlining_schema(self):
        self.assertIn("from policy_intelligence import (", self.server)
        self.assertIn("init_policy_schema(conn)", self.server)
        self.assertIn("seed_policy_mvp(conn", self.server)
        self.assertNotIn("create table if not exists policy_records", self.server)

    def test_login_does_not_seed_or_rewrite_business_data(self):
        login_route = self.server.split('parsed.path == "/api/login"', 1)[1].split(
            "scheduled_refresh_paths = {", 1
        )[0]
        cloud_login_route = login_route.split(
            'if cloud_login_required():\n                    raise ValueError',
            1,
        )[0]
        self.assertNotIn('seed_policy_mvp(conn, org_id=org_id, edition="china")', cloud_login_route)
        self.assertNotIn("ensure_legacy_vertical_claim(org_id)", cloud_login_route)
        self.assertNotIn("insert into organizations", cloud_login_route)
        self.assertNotIn("insert into users", cloud_login_route)

    def test_dashboard_and_policy_list_get_routes_are_registered(self):
        self.assertIn('parsed.path == "/api/policy-intelligence/dashboard"', self.server)
        self.assertIn('parsed.path == "/api/policy-intelligence/policies"', self.server)
        self.assertIn('engineDisplacementL', self.server)

    def test_mutating_workflow_routes_are_admin_gated_by_default(self):
        for route in (
            "/api/policy-intelligence/fetch",
            "/api/policy-intelligence/import-source",
            "/api/policy-intelligence/parse",
            "/api/policy-intelligence/review",
            "/api/policy-intelligence/evaluate",
        ):
            self.assertIn('parsed.path == "%s"' % route, self.server)
        self.assertFalse(any(path.startswith("/api/policy-intelligence/") for path in TRIAL_POST_ALLOWED_PATHS))

    def test_policy_preview_is_not_persisted_without_explicit_request(self):
        analyze_route = self.server.split('parsed.path == "/api/policy-intelligence/analyze"', 1)[1].split(
            'parsed.path == "/api/policy-intelligence/evaluate"', 1
        )[0]
        self.assertIn('persist = body.get("persist") is True', analyze_route)
        self.assertIn("if persist:", analyze_route)

    def test_policy_model_gateway_is_source_locked_and_json_only(self):
        self.assertIn("def policy_model_gateway(messages):", self.server)
        gateway = self.server.split("def policy_model_gateway(messages):", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("不得补写", gateway)
        self.assertIn("JSON", gateway)

    def test_group_dashboard_uses_selected_sales_warning_market_as_policy_comparison_pool(self):
        group_route = self.server.split('parsed.path == "/api/group-dashboard-demo"', 1)[1].split(
            'parsed.path == "/api/global-sales-marquee"', 1
        )[0]
        self.assertIn('q.get("policy_model"', group_route)
        self.assertIn("build_sales_warning_policy_profiles(", group_route)
        self.assertIn("selected_warning,", group_route)
        self.assertIn('"role": policy_profile["role"]', group_route)
        self.assertIn('payload["salesWarnings"].get("saicModels", [])', group_route)
        self.assertIn('payload["salesWarnings"].get("monitoring", {}).get("models", [])', group_route)
        self.assertIn('"salesReference": policy_profile["salesReference"]', group_route)
        self.assertNotIn("蔚来ES6", group_route)
        self.assertNotIn("理想L6", group_route)
        self.assertIn('q.get("policy_model", [""])', group_route)
        self.assertIn("else (warning_models[0] if warning_models else {})", group_route)
        self.assertNotIn('q.get("policy_model", ["奥迪E7X"])', group_route)

    def test_regional_strategy_runs_three_flagship_providers_on_same_evidence(self):
        calls = []

        def provider_runner(provider, messages):
            calls.append((provider, messages))
            is_summary = "最终归纳" in messages[0]["content"]
            if is_summary:
                return json.dumps({"selectedProvider": "qwen"}, ensure_ascii=False)
            return json.dumps({
                "policyJudgement": "conditional",
                "strategyDirection": "convert",
                "conclusion": "%s认为上海存在条件式政策机会" % provider,
                "targetAudience": "满足置换条件的价格敏感用户",
                "action": "制作政策资格解释和补贴计算内容",
                "leadingIndicator": "权益内容点击率",
                "conversionIndicator": "有效置换线索率",
                "stopCondition": "连续两周有效线索不增长",
                "uncertainty": "个人资格尚未确认",
                "evidenceIds": ["policy-1"],
                "confidence": .8,
            }, ensure_ascii=False)

        result = run_policy_strategy_validation({
            "vehicleImpact": {
                "model": "尚界Z7",
                "region": "上海",
                "profile": {"purchaseScenario": "置换更新", "energyType": "纯电动"},
                "maxConditionalBenefit": 24726,
                "maxVerifiedBenefit": 0,
                "evidenceStatus": "conditional_eligibility",
                "causalBoundary": "规则影响链，不代表已验证销量因果",
                "policyEffects": [{
                    "policyId": "policy-1",
                    "policyName": "置换更新补贴",
                    "sourceQuote": "补贴金额最高1.5万元",
                }],
            },
            "opportunities": [],
        }, provider_runner=provider_runner)
        self.assertEqual(result["status"], "aligned")
        self.assertEqual({provider for provider, _ in calls}, {"qwen", "deepseek", "kimi"})
        self.assertEqual([provider for provider, _ in calls].count("qwen"), 2)
        self.assertIn("最终归纳", calls[-1][1][0]["content"])
        self.assertTrue(all("上海" in messages[1]["content"] for _, messages in calls))
        self.assertEqual(result["finalStrategy"]["evidenceIds"], ["policy-1"])
        self.assertEqual(result["finalStrategy"]["conclusion"], "qwen认为上海存在条件式政策机会")
        self.assertEqual(result["finalStrategy"]["summaryRole"], "MMN最终归纳")
        self.assertEqual(result["finalStrategy"]["modelAgreement"], "三方政策判断与策略方向一致")

    def test_policy_get_and_post_inputs_share_bounded_validation(self):
        self.assertEqual(validate_policy_vehicle_inputs("219800", "置换更新", ""), (219800.0, "置换更新", None))
        for invalid_price in (0, -1, "nan", "inf", 10000001):
            with self.subTest(price=invalid_price), self.assertRaises(ValueError):
                validate_policy_vehicle_inputs(invalid_price, "置换更新")
        with self.assertRaises(ValueError):
            validate_policy_vehicle_inputs(219800, "随便看看")
        with self.assertRaises(ValueError):
            validate_policy_vehicle_inputs(219800, "置换更新", "inf")

    def test_regional_strategy_retries_only_the_failed_independent_reviewer(self):
        calls = []

        def provider_runner(provider, messages):
            calls.append(provider)
            if provider == "kimi" and calls.count("kimi") == 1:
                raise TimeoutError("temporary timeout")
            if "最终归纳" in messages[0]["content"]:
                return json.dumps({"selectedProvider": "qwen"}, ensure_ascii=False)
            return json.dumps({
                "policyJudgement": "conditional",
                "strategyDirection": "convert",
                "conclusion": "上海存在条件式政策机会",
                "targetAudience": "满足置换条件的价格敏感用户",
                "action": "制作政策资格解释和补贴计算内容",
                "leadingIndicator": "权益内容点击率",
                "conversionIndicator": "有效置换线索率",
                "stopCondition": "连续两周有效线索不增长",
                "uncertainty": "个人资格尚未确认",
                "evidenceIds": ["policy-1"],
                "confidence": .8,
            }, ensure_ascii=False)

        result = run_policy_strategy_validation({
            "vehicleImpact": {
                "model": "智己LS6",
                "region": "上海",
                "profile": {"purchaseScenario": "置换更新", "energyType": "增程式/纯电动"},
                "policyEffects": [{"policyId": "policy-1", "policyName": "置换更新补贴"}],
            },
            "opportunities": [],
        }, provider_runner=provider_runner)

        self.assertEqual(result["status"], "aligned")
        self.assertEqual(calls.count("deepseek"), 1)
        self.assertEqual(calls.count("kimi"), 2)
        self.assertEqual(calls.count("qwen"), 2)

    def test_final_qwen_selection_cannot_rewrite_strategy_fields(self):
        def provider_runner(provider, messages):
            if "最终归纳" in messages[0]["content"]:
                return json.dumps({
                    "selectedProvider": "qwen",
                    "action": "无条件大规模投放",
                    "uncertainty": "无",
                }, ensure_ascii=False)
            return json.dumps({
                "policyJudgement": "conditional",
                "strategyDirection": "convert",
                "conclusion": "%s认为上海存在条件式政策机会" % provider,
                "targetAudience": "满足置换条件的价格敏感用户",
                "action": "仅向完成资格核验的人群解释政策",
                "leadingIndicator": "资格核验完成率",
                "conversionIndicator": "有效置换线索率",
                "stopCondition": "资格证据不足时停止投放",
                "uncertainty": "个人资格尚未确认",
                "evidenceIds": ["policy-1"],
                "confidence": .8,
            }, ensure_ascii=False)

        result = run_policy_strategy_validation({
            "vehicleImpact": {
                "model": "智己LS6",
                "region": "上海",
                "profile": {"purchaseScenario": "置换更新"},
                "policyEffects": [{"policyId": "policy-1"}],
            },
            "opportunities": [],
        }, provider_runner=provider_runner)

        self.assertEqual(result["status"], "manual_required")
        self.assertIsNone(result["finalStrategy"])
        self.assertIn("只能选择", result["reasons"][0])

    def test_final_strategy_exposes_only_three_provider_common_evidence(self):
        def provider_runner(provider, messages):
            if "最终归纳" in messages[0]["content"]:
                return json.dumps({"selectedProvider": "qwen"}, ensure_ascii=False)
            return json.dumps({
                "policyJudgement": "conditional",
                "strategyDirection": "convert",
                "conclusion": "上海存在条件式政策机会",
                "targetAudience": "满足置换条件的人群",
                "action": "解释资格并引导核验",
                "leadingIndicator": "资格核验完成率",
                "conversionIndicator": "有效置换线索率",
                "stopCondition": "证据不足时停止",
                "uncertainty": "个人资格尚未确认",
                "evidenceIds": ["p1", "p2"] if provider == "qwen" else ["p1"],
                "confidence": .8,
            }, ensure_ascii=False)

        result = run_policy_strategy_validation({
            "vehicleImpact": {
                "model": "智己LS6",
                "region": "上海",
                "profile": {"purchaseScenario": "置换更新"},
                "policyEffects": [{"policyId": "p1"}, {"policyId": "p2"}],
            },
            "opportunities": [],
        }, provider_runner=provider_runner)

        self.assertEqual(result["status"], "aligned")
        self.assertEqual(result["commonEvidenceIds"], ["p1"])
        self.assertEqual(result["finalStrategy"]["evidenceIds"], ["p1"])

    def test_policy_routes_do_not_fabricate_vehicle_profile_defaults(self):
        get_route = self.server.split('parsed.path == "/api/policy-intelligence/dashboard"', 1)[1].split(
            'parsed.path == "/api/policy-intelligence/policies"', 1
        )[0]
        post_route = self.server.split('parsed.path == "/api/policy-intelligence/analyze"', 1)[1].split(
            'parsed.path == "/api/policy-intelligence/evaluate"', 1
        )[0]
        for route in (get_route, post_route):
            self.assertNotIn('or "奥迪E7X"', route)
            self.assertNotIn('or "新能源"', route)
            self.assertNotIn('or "SUV"', route)
            self.assertNotIn("280000", route)
            self.assertIn("trusted_policy_vehicle_profile(", route)

    def test_unknown_model_cannot_spoof_a_complete_profile(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute(
            "create table vertical_rank_assets (org_id text, edition text, platform text, "
            "period text, own_model text, competitor_model text, positive_rank integer, "
            "negative_rank integer, compare_share real, source_file text, updated_at text)"
        )
        conn.execute(
            "insert into vertical_rank_assets values (?,?,?,?,?,?,?,?,?,?,?)",
            (
                "tenant-a", "china", "懂车帝", "2026.07.23", "智己LS6", "理想i6",
                1, 2, .12, "微信图片_智己LS6.png", "2026-07-23T13:40:11Z",
            ),
        )
        try:
            trusted = trusted_policy_vehicle_profile(
                conn, "tenant-a", "china", "智己LS6", "置换更新"
            )
            unknown = trusted_policy_vehicle_profile(
                conn, "tenant-a", "china", "完全不存在的车型", "置换更新"
            )
        finally:
            conn.close()

        self.assertEqual(trusted["model"], "智己LS6")
        self.assertGreater(trusted["price"], 0)
        self.assertTrue(trusted["energyType"])
        self.assertIsNone(unknown["price"])
        self.assertEqual(unknown["energyType"], "")
        self.assertEqual(unknown["bodyType"], "")

    def test_trusted_vehicle_profile_preserves_source_period_for_energy_provenance(self):
        warning = {
            "model": "智己LS6",
            "vehicleStartPriceWan": 18.99,
            "energyType": "增程式/纯电动",
            "bodyType": "SUV",
            "salesHistory": {"latestPeriod": "2026-06"},
        }
        with patch("server.trusted_policy_warning_models", return_value=[warning]):
            profile = trusted_policy_vehicle_profile(
                None, "tenant-a", "china", "智己LS6", "置换更新"
            )

        self.assertEqual(profile["energyAsOf"], "2026-06")
        self.assertEqual(profile["priceAsOf"], "2026-06")

    def test_missing_selected_policy_model_does_not_fail_the_group_dashboard(self):
        group_route = self.server.split('parsed.path == "/api/group-dashboard-demo"', 1)[1].split(
            'parsed.path == "/api/global-sales-marquee"', 1
        )[0]
        self.assertNotIn('raise ValueError("所选车型未进入当前销量预警监测清单', group_route)
        self.assertIn('availability = "available" if policy_profiles else "selected_model_unavailable"', group_route)
        self.assertIn('"availability": availability', group_route)


if __name__ == "__main__":
    unittest.main()
