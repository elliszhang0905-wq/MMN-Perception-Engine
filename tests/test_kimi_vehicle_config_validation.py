import json
import unittest
from io import BytesIO
from urllib.error import HTTPError
from unittest.mock import patch

import server


class KimiVehicleConfigValidationTest(unittest.TestCase):
    def test_vehicle_configuration_is_routed_separately_from_general_facts(self):
        self.assertEqual(
            server.infer_mmn_task_type("对比两款车的电池、续航和智驾配置"),
            "vehicle_configuration_fact",
        )
        self.assertEqual(server.infer_mmn_task_type("本月销量是多少"), "fact_explanation")

    def test_kimi_uses_its_own_key_and_flagship_model_configuration(self):
        with patch.dict(
            server.os.environ,
            {
                "KIMI_API_KEY": "test-key",
                "KIMI_BASE_URL": "https://example.test/v1",
                "KIMI_MODEL": "kimi-fast",
                "KIMI_DEEP_MODEL": "kimi-flagship",
            },
            clear=False,
        ):
            config = server.kimi_config("deep")
        self.assertTrue(config["configured"])
        self.assertEqual(config["model"], "kimi-flagship")
        self.assertEqual(config["base_url"], "https://example.test/v1")

    def test_kimi_deep_default_tracks_current_flagship(self):
        with patch.dict(
            server.os.environ,
            {"KIMI_API_KEY": "test-key", "KIMI_MODEL": "", "KIMI_DEEP_MODEL": ""},
            clear=False,
        ):
            self.assertEqual(server.kimi_model_for("deep"), "kimi-k2.6")

    def test_kimi_free_tier_rejection_exposes_actual_model_and_action(self):
        payload = json.dumps({"error": {
            "code": "AllocationQuota.FreeTierOnly",
            "message": "Free quota exhausted",
        }}).encode("utf-8")
        rejection = HTTPError("https://dashscope.test/chat/completions", 403, "Forbidden", {}, BytesIO(payload))
        config = {
            "configured": True,
            "base_url": "https://dashscope.test",
            "model": "kimi-flagship",
        }

        with patch.object(server, "kimi_config", return_value=config), \
             patch.object(server, "env_value", return_value="test-key"), \
             patch.object(server, "urlopen", side_effect=rejection):
            with self.assertRaisesRegex(
                ValueError,
                "AllocationQuota.FreeTierOnly.*kimi-flagship.*仅使用免费额度",
            ):
                server.call_kimi([{"role": "user", "content": "test"}], profile="deep")

    def test_vehicle_configuration_requires_all_three_models_on_common_evidence(self):
        outputs = {
            provider: {
                "verdict": "supported",
                "evidenceIds": ["ref-1"],
                "confidence": 0.9,
                "issues": [],
            }
            for provider in ("qwen", "deepseek", "kimi")
        }
        result = server.cross_validate_vehicle_config_reviews(outputs, ["ref-1"], {})
        self.assertEqual(result["status"], "aligned")
        self.assertEqual(result["label"], "三模型一致")
        self.assertEqual(result["commonEvidenceIds"], ["ref-1"])

        outputs.pop("kimi")
        result = server.cross_validate_vehicle_config_reviews(outputs, ["ref-1"], {"kimi": "timeout"})
        self.assertEqual(result["status"], "needs_human_review")
        self.assertIn("三模型未全部完成", result["reasons"])

    def test_vehicle_configuration_calls_kimi_flagship_profile(self):
        with patch.object(server, "call_kimi", return_value="ok") as call_kimi:
            output = server.call_provider(
                "kimi",
                [{"role": "user", "content": "test"}],
                "vehicle_configuration_fact",
                "fast",
                reviewer=True,
            )
        self.assertEqual(output, "ok")
        self.assertEqual(call_kimi.call_args.kwargs["profile"], "deep")


if __name__ == "__main__":
    unittest.main()
