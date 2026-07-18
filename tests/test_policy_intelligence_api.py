from pathlib import Path
import json
import unittest

from server import run_policy_strategy_validation, validate_policy_vehicle_inputs


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
        trial_block = self.server.split("trial_post_allowed = {", 1)[1].split("}", 1)[0]
        self.assertNotIn("/api/policy-intelligence/", trial_block)

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

    def test_regional_strategy_runs_three_flagship_providers_on_same_evidence(self):
        calls = []

        def provider_runner(provider, messages):
            calls.append((provider, messages))
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
        self.assertTrue(all("上海" in messages[1]["content"] for _, messages in calls))
        self.assertEqual(result["finalStrategy"]["evidenceIds"], ["policy-1"])

    def test_policy_get_and_post_inputs_share_bounded_validation(self):
        self.assertEqual(validate_policy_vehicle_inputs("219800", "置换更新", ""), (219800.0, "置换更新", None))
        for invalid_price in (0, -1, "nan", "inf", 10000001):
            with self.subTest(price=invalid_price), self.assertRaises(ValueError):
                validate_policy_vehicle_inputs(invalid_price, "置换更新")
        with self.assertRaises(ValueError):
            validate_policy_vehicle_inputs(219800, "随便看看")
        with self.assertRaises(ValueError):
            validate_policy_vehicle_inputs(219800, "置换更新", "inf")


if __name__ == "__main__":
    unittest.main()
