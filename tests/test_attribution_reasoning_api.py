from pathlib import Path
import json
import unittest

import server
from attribution_reasoning import REQUIRED_EVIDENCE_IDS


ROOT = Path(__file__).resolve().parents[1]


class AttributionReasoningApiTest(unittest.TestCase):
    def test_routes_and_schema_are_wired(self):
        source = (ROOT / "server.py").read_text(encoding="utf-8")
        self.assertIn('parsed.path == "/api/attribution-reasoning"', source)
        self.assertIn('parsed.path == "/api/attribution-reasoning/run"', source)
        self.assertIn("init_attribution_reasoning_schema(conn)", source)
        self.assertIn("/api/attribution-reasoning/run", server.TRIAL_POST_ALLOWED_PATHS)

    def test_runner_calls_all_three_independently_on_same_packet(self):
        calls = []

        def provider_runner(provider, messages):
            packet = json.loads(messages[1]["content"])
            calls.append((provider, packet["fingerprint"], tuple(packet["evidenceIds"])))
            return json.dumps({
                "verdict": "downstream_funnel_break",
                "primaryBreak": "order",
                "conclusion": "线索进入后、订单形成前是当前主要断点",
                "counterEvidence": "声量认知质量较好，曝光不足不是唯一解释",
                "alternativeExplanations": ["销售承接", "价格金融"],
                "nextActions": [{"priority": "P0", "action": "打通线索订单ID", "metric": "有效线索订单率", "stopCondition": "两周无改善则停止"}],
                "stopCondition": "连续两周无改善",
                "causalBoundary": "三路一致不等于因果",
                "evidenceIds": list(REQUIRED_EVIDENCE_IDS),
                "confidence": .82,
            }, ensure_ascii=False)

        payload = {
            "salesWarnings": {"source": {"period": "2026-06"}, "saicModels": [{"model": "奥迪E7X", "segmentLabel": "中大型SUV · 新能源", "marketSales": 87746, "sales": 4017, "rank": 5, "marketShare": .0458, "benchmark": 15165, "performanceRate": .2649}]},
            "productEvaluation": {"source": {"period": "2026.06.01—2026.06.30"}, "models": [{"model": "奥迪E7X", "voice": 235579, "voiceRank": 4, "overallNsr": .7513, "overallNsrRank": 2}]},
        }
        packet, outputs, errors, arbitration = server.run_attribution_reasoning(payload, provider_runner=provider_runner)
        self.assertEqual({item[0] for item in calls}, {"qwen", "deepseek", "kimi"})
        self.assertEqual(len({item[1] for item in calls}), 1)
        self.assertEqual(len({item[2] for item in calls}), 1)
        self.assertEqual(arbitration["status"], "aligned")
        self.assertFalse(errors)
        self.assertEqual(set(outputs), {"qwen", "deepseek", "kimi"})
        self.assertEqual(packet["fingerprint"], calls[0][1])


if __name__ == "__main__":
    unittest.main()
