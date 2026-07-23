import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cover_prompt import (
    REVIEW_SLOTS,
    build_cover_evidence_packet,
    fuse_reviews,
    normalize_review,
)
import server


class CoverPromptContractTest(unittest.TestCase):
    def setUp(self):
        self.video = {
            "itemId": "video-1",
            "sourceUrl": "https://www.douyin.com/video/video-1",
            "evidenceFingerprint": "video-evidence-fp",
            "keyframes": [{"text": "银色轿车位于画面中央，低机位三分之四前视角", "evidenceId": "V:shot:1"}],
            "visualSegments": [{"text": "背景为蓝黑渐变摄影棚", "evidenceId": "V:visual:1"}],
            "ocrSegments": [{"text": "驾控新境", "evidenceId": "V:ocr:1"}],
        }

    def output(self, packet, *, style="商业汽车摄影"):
        return {
            "subject": "银色轿车",
            "action": "静止展示",
            "scene": "蓝黑渐变摄影棚",
            "composition": "低机位三分之四前视角，主体居中",
            "lighting": "冷色轮廓光",
            "color": "银色与蓝黑色",
            "material": "金属车漆与玻璃",
            "ocrText": ["驾控新境"],
            "layout": ["标题位于上方", "车辆居中"],
            "style": style,
            "aspectRatio": "16:9",
            "negativePrompt": ["错误车标", "多余文字", "车身变形"],
            "limitations": [],
            "confidence": 0.88,
            "evidenceRefs": packet["evidenceRefs"],
            "evidenceFingerprint": packet["evidenceFingerprint"],
        }

    def test_same_frozen_packet_is_fused_to_one_public_prompt(self):
        packet = build_cover_evidence_packet(self.video)
        outputs = {slot: self.output(packet) for slot in REVIEW_SLOTS}
        result = fuse_reviews(packet, outputs)
        self.assertEqual(result["status"], "verified")
        self.assertIn("银色轿车", result["finalPrompt"]["prompt"])
        self.assertEqual({row["label"] for row in result["runs"]}, {
            "MMN独立分析 1", "MMN独立分析 2", "MMN独立分析 3",
        })
        self.assertNotIn("provider", str(result).lower())

    def test_missing_visual_evidence_is_limited_and_never_generates_prompt(self):
        packet = build_cover_evidence_packet({
            "itemId": "video-2", "sourceUrl": "https://www.douyin.com/video/video-2",
            "evidenceFingerprint": "fp", "keyframes": [], "visualSegments": [], "ocrSegments": [],
        })
        result = fuse_reviews(packet, {})
        self.assertEqual(packet["status"], "limited")
        self.assertEqual(result["status"], "limited")
        self.assertIsNone(result["finalPrompt"])

    def test_foreign_evidence_reference_is_rejected(self):
        packet = build_cover_evidence_packet(self.video)
        value = self.output(packet)
        value["evidenceRefs"] = ["V:other:1"]
        with self.assertRaises(ValueError):
            normalize_review(value, packet)

    def test_three_way_disagreement_requires_manual_review(self):
        packet = build_cover_evidence_packet(self.video)
        outputs = {
            REVIEW_SLOTS[0]: self.output(packet, style="商业汽车摄影"),
            REVIEW_SLOTS[1]: self.output(packet, style="未来主义海报"),
            REVIEW_SLOTS[2]: self.output(packet, style="写实电影剧照"),
        }
        result = fuse_reviews(packet, outputs)
        self.assertEqual(result["status"], "manual_required")
        self.assertIsNone(result["finalPrompt"])
        self.assertIn("style", result["disagreements"])

    def test_one_failed_review_never_publishes_two_model_result(self):
        packet = build_cover_evidence_packet(self.video)
        result = fuse_reviews(packet, {
            REVIEW_SLOTS[0]: self.output(packet),
            REVIEW_SLOTS[1]: self.output(packet),
        }, {REVIEW_SLOTS[2]: "timeout"})
        self.assertEqual(result["status"], "incomplete")
        self.assertIsNone(result["finalPrompt"])

    def test_server_sends_identical_frozen_packet_and_persists_three_private_runs(self):
        packet = build_cover_evidence_packet(self.video)
        captured = []

        def provider_runner(provider, messages):
            received = json.loads(messages[-1]["content"])
            captured.append((provider, messages[-1]["content"]))
            return json.dumps(self.output(received), ensure_ascii=False)

        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "mmn.db"):
            result = server.run_cover_prompt_reviews(
                "video-job-1", packet, provider_runner=provider_runner,
            )
            with server.db() as conn:
                rows = conn.execute(
                    "select provider_key,evidence_fingerprint,status from douyin_cover_prompt_runs"
                ).fetchall()
        self.assertEqual(result["status"], "verified")
        self.assertEqual(len(captured), 3)
        self.assertEqual(len({body for _, body in captured}), 1)
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row["evidence_fingerprint"] == packet["evidenceFingerprint"] for row in rows))

    def test_customer_ui_requests_and_renders_neutral_cover_prompt(self):
        root = Path(__file__).resolve().parents[1]
        source = (root / "douyin-hot-demo.js").read_text(encoding="utf-8")
        self.assertIn("generateCoverPrompt:true", source)
        self.assertIn("封面图像 Prompt", source)
        self.assertIn("正向 Prompt", source)
        self.assertNotIn("qwen", source.lower())
        self.assertNotIn("deepseek", source.lower())
        self.assertNotIn("kimi", source.lower())

    def test_cover_prompt_has_an_independent_default_off_release_gate(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MMN_DOUYIN_COVER_PROMPT_ENABLED", None)
            self.assertFalse(server.cover_prompt_enabled())
        with patch.dict(os.environ, {"MMN_DOUYIN_COVER_PROMPT_ENABLED": "true"}):
            self.assertTrue(server.cover_prompt_enabled())


if __name__ == "__main__":
    unittest.main()
