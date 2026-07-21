import sqlite3
import unittest

from attribution_reasoning import (
    REQUIRED_EVIDENCE_IDS,
    arbitrate,
    build_evidence_packet,
    init_schema,
    load_run,
    save_run,
)


def dashboard_payload():
    return {
        "salesWarnings": {
            "source": {"period": "2026-06"},
            "saicModels": [{"model": "奥迪E7X", "segmentLabel": "中大型SUV · 新能源", "marketSales": 87746, "sales": 4017, "rank": 5, "marketShare": .0458, "benchmark": 15165, "performanceRate": .2649}],
        },
        "productEvaluation": {
            "source": {"period": "2026.06.01—2026.06.30"},
            "models": [{"model": "奥迪E7X", "voice": 235579, "voiceRank": 4, "overallNsr": .7513, "overallNsrRank": 2}, {"model": "竞品", "voice": 500000}],
        },
    }


def review(provider, verdict="downstream_funnel_break", primary="order", confidence=.8):
    return {
        "verdict": verdict,
        "primaryBreak": primary,
        "conclusion": "%s：线索后到订单前是当前主要断点" % provider,
        "counterEvidence": "声量认知质量较好，不能把订单不足直接归因于曝光",
        "alternativeExplanations": ["销售承接差异", "价格金融变化"],
        "nextActions": [{"priority": "P0", "action": "打通线索与订单ID", "metric": "有效线索到订单率", "stopCondition": "两周无改善则复核"}],
        "stopCondition": "连续两周订单承接无改善",
        "causalBoundary": "相关性不等于因果",
        "evidenceIds": list(REQUIRED_EVIDENCE_IDS),
        "confidence": confidence,
    }


class AttributionReasoningTest(unittest.TestCase):
    def test_packet_locks_full_reasoning_path_and_fingerprint(self):
        first = build_evidence_packet(dashboard_payload())
        second = build_evidence_packet(dashboard_payload())
        self.assertEqual(first["status"], "ready")
        self.assertEqual(first["evidenceIds"], list(REQUIRED_EVIDENCE_IDS))
        self.assertEqual(first["fingerprint"], second["fingerprint"])
        self.assertIn("三路一致也不构成因果证明", first["causalBoundary"])

    def test_missing_model_evidence_fails_closed(self):
        packet = build_evidence_packet({}, "其他车型")
        self.assertEqual(packet["status"], "insufficient_evidence")
        self.assertFalse(packet["evidenceIds"])

    def test_three_complete_common_reviews_publish(self):
        result = arbitrate({provider: review(provider) for provider in ("qwen", "deepseek", "kimi")}, REQUIRED_EVIDENCE_IDS)
        self.assertEqual(result["status"], "aligned")
        self.assertEqual(result["finalConclusion"]["primaryBreak"], "order")
        self.assertEqual(result["commonEvidenceIds"], sorted(REQUIRED_EVIDENCE_IDS))

    def test_failure_or_conflict_never_publishes(self):
        incomplete = arbitrate({"qwen": review("qwen"), "deepseek": review("deepseek")}, REQUIRED_EVIDENCE_IDS, {"kimi": "timeout"})
        self.assertEqual(incomplete["status"], "incomplete")
        self.assertIsNone(incomplete["finalConclusion"])
        conflict = arbitrate({"qwen": review("qwen"), "deepseek": review("deepseek", primary="voice"), "kimi": review("kimi")}, REQUIRED_EVIDENCE_IDS)
        self.assertEqual(conflict["status"], "manual_required")
        self.assertIsNone(conflict["finalConclusion"])

    def test_persistence_survives_new_connection_and_hides_provider_names(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        init_schema(conn)
        packet = build_evidence_packet(dashboard_payload())
        outputs = {provider: review(provider) for provider in ("qwen", "deepseek", "kimi")}
        result = arbitrate(outputs, packet["evidenceIds"])
        saved = save_run(conn, org_id="local", edition="china", model="奥迪E7X", packet=packet, provider_outputs=outputs, provider_errors={}, arbitration=result)
        loaded = load_run(conn, org_id="local", edition="china", model="奥迪E7X")
        self.assertEqual(saved["id"], loaded["id"])
        self.assertEqual([item["role"] for item in loaded["providers"]], ["独立复核A", "独立复核B", "独立复核C"])
        self.assertNotIn("qwen", str(loaded))


if __name__ == "__main__":
    unittest.main()
