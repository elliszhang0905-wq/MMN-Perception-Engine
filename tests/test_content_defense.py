import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from content_defense import (
    build_evidence_package,
    create_job,
    cross_validate_reviews,
    get_job,
    init_schema,
    load_media_cache,
    save_media_cache,
)
import server
from douyin_hot_entities import save_rank_snapshot


class ContentDefenseTest(unittest.TestCase):
    def setUp(self):
        self.item = {
            "itemId": "video-1", "title": "E7X底盘连续弯道表现",
            "sourceUrl": "https://www.douyin.com/video/1234567890",
            "coverUrl": "https://example.com/cover.jpg", "rank": 1,
            "playCount": 900000, "likeCount": 30000, "commentCount": 900,
            "shareCount": 1200, "collectCount": 800,
        }
        self.media = [{
            "source_id": "video-1", "evidence_type": "shot", "start_ms": 1200,
            "quote_text": "车辆连续通过弯道，画面展示车身姿态变化",
            "confidence": .85, "provenance": {"availability": "available", "fetchTime": "2026-07-20T00:00:00Z"},
        }]
        self.nsr = [{
            "model": "奥迪E7X", "attribute": "动力与操控", "nsr": .897,
            "competitorDelta": .214, "volume": 235579, "source": "真实产品评价源表",
        }]
        self.whitepaper = {"filename": "E7X.pdf", "capabilities": [{
            "label": "动力与操控", "claim": "底盘能力事实", "quote": "底盘控制系统可协同调节车辆动态表现", "page": 63,
        }]}

    def package(self, **overrides):
        values = {"media": self.media, "nsr_rows": self.nsr, "whitepaper": self.whitepaper,
                  "comments": [{"id": "c1", "text": "连续弯稳定吗", "sentiment": "疑问"}],
                  "leads": [], "model": "奥迪E7X"}
        values.update(overrides)
        return build_evidence_package(self.item, **values)

    def reviews(self, package, *, judgement="strong_defense", attribute="动力与操控", ids=None):
        ids = ids or [row["evidenceId"] for row in package["evidence"] if row["status"] == "available"]
        row = {"attribute": attribute, "judgementType": judgement, "hotClaim": "弯道稳定性是否可信",
               "contentProposition": "用连续弯实拍解释底盘控制", "titleStructure": "质疑 + 连续镜头 + 产品机制",
               "requiredProof": ["连续弯关键镜头", "白皮书页码原文"], "commentChallenges": ["是否经过剪辑"],
               "forbiddenClaims": ["热度证明市场需求", "必然提升销量"], "kpis": ["完整播放率", "属性正向评论率"],
               "evidenceIds": ids, "confidence": .86, "reason": "共同证据完整"}
        return {name: dict(row) for name in ("qwen", "deepseek", "kimi")}

    def test_complete_three_review_common_evidence_publishes_strong_defense(self):
        package = self.package()
        result = cross_validate_reviews(package, self.reviews(package))
        self.assertEqual(result["status"], "published")
        self.assertEqual(result["card"]["judgementLabel"], "强势属性防线")
        self.assertEqual(result["card"]["attribute"], "动力与操控")
        self.assertEqual(len(result["qualityChecks"]), 3)
        self.assertNotIn("qwen", json.dumps(result, ensure_ascii=False).lower())

    def test_partial_review_failure_requires_human_confirmation(self):
        package = self.package()
        reviews = self.reviews(package)
        reviews.pop("kimi")
        result = cross_validate_reviews(package, reviews, {"kimi": "timeout"})
        self.assertEqual(result["status"], "manual_required")
        self.assertIn("三重交叉质检未完整返回", result["reasons"])
        self.assertIsNone(result["card"])

    def test_disjoint_common_evidence_blocks_publication(self):
        package = self.package()
        reviews = self.reviews(package)
        w_id = next(row["evidenceId"] for row in package["evidence"] if row["type"] == "W")
        reviews["kimi"]["evidenceIds"] = [row for row in reviews["kimi"]["evidenceIds"] if row != w_id]
        result = cross_validate_reviews(package, reviews)
        self.assertEqual(result["status"], "manual_required")
        self.assertIn("共同证据未同时覆盖真实视频、属性NSR与白皮书事实", result["reasons"])

    def test_unreadable_video_degrades_instead_of_claiming_full_video(self):
        package = self.package(media=[], media_errors=["video-1 视觉: Download multimodal file timed out"])
        result = cross_validate_reviews(package, self.reviews(package))
        self.assertEqual(result["status"], "manual_required")
        self.assertIn("仅有榜单标题或视频不可读，缺少真实视频本体证据", result["reasons"])
        failed = [row for row in package["evidence"] if row["type"] == "V" and row["status"] == "failed"]
        self.assertTrue(failed)

    def test_whitepaper_missing_attribute_blocks_defense(self):
        package = self.package(whitepaper={"filename": "E7X.pdf", "capabilities": [{
            "label": "外观", "claim": "造型", "quote": "竖向主动进气格栅", "page": 8,
        }]})
        result = cross_validate_reviews(package, self.reviews(package))
        self.assertEqual(result["status"], "manual_required")
        self.assertIsNone(result["card"])

    def test_negative_competitor_delta_cannot_masquerade_as_strong(self):
        weak_nsr = [{**self.nsr[0], "competitorDelta": -.12}]
        package = self.package(nsr_rows=weak_nsr)
        result = cross_validate_reviews(package, self.reviews(package, judgement="strong_defense"))
        self.assertEqual(result["status"], "manual_required")
        self.assertIn("弱势或缺少竞品差值的属性不能发布为强势防线", result["reasons"])
        weak = cross_validate_reviews(package, self.reviews(package, judgement="weak_defense"))
        self.assertEqual(weak["status"], "published")
        self.assertEqual(weak["card"]["judgementLabel"], "弱势属性防线")

    def test_plugin_error_is_traceable_failure_not_empty_success(self):
        package = self.package(media=[], media_errors=["video-1 OCR: provider HTTP 200 business error"])
        failed = [row for row in package["evidence"] if row["status"] == "failed"]
        self.assertEqual(len(failed), 1)
        self.assertIn("business error", failed[0]["failureReason"])
        self.assertNotIn("provider", failed[0]["failureReason"].lower())
        self.assertIn("证据能力", failed[0]["failureReason"])
        self.assertEqual(cross_validate_reviews(package, self.reviews(package))["status"], "manual_required")

    def test_media_cache_and_job_creation_are_idempotent(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        init_schema(conn)
        save_media_cache(conn, self.item, self.media, {"errors": []})
        save_media_cache(conn, self.item, self.media, {"errors": []})
        self.assertTrue(load_media_cache(conn, self.item)["cacheHit"])
        count = conn.execute("select count(*) from douyin_content_defense_cache").fetchone()[0]
        self.assertEqual(count, 1)
        first, created = create_job(conn, org_id="local", edition="china", view="videos", range_key="24h",
                                    item=self.item, request={})
        second, recreated = create_job(conn, org_id="local", edition="china", view="videos", range_key="24h",
                                       item=self.item, request={})
        self.assertTrue(created)
        self.assertFalse(recreated)
        self.assertEqual(first["jobId"], second["jobId"])
        self.assertEqual(get_job(conn, first["jobId"])["status"], "queued")

    def _run_persistent_job(self, failing_check=False):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        db_path = Path(temp.name) / "mmn.db"
        with patch.object(server, "DB_PATH", db_path):
            server.init_db()
            with server.db() as conn:
                snapshot = save_rank_snapshot(conn, [self.item], view="videos", range_key="24h")
                job, _ = create_job(conn, org_id="local", edition="china", view="videos", range_key="24h",
                                    item=snapshot["items"][0], request={"model": "奥迪E7X"})
            server.save_product_whitepaper_evidence({
                "model": "奥迪E7X", "filename": "E7X.pdf", "status": "dual_model_verified",
                "capabilities": self.whitepaper["capabilities"],
            })

            def media_runner(assets, max_assets=1):
                return self.media, {"processedAssetCount": 1}, []

            def provider_runner(provider, messages):
                if failing_check and provider == "kimi":
                    raise RuntimeError("quality check timeout")
                packet = json.loads(messages[-1]["content"])
                ids = [row["evidenceId"] for row in packet["evidence"]]
                return json.dumps({
                    "attribute": "动力与操控", "judgementType": "strong_defense",
                    "hotClaim": "弯道表现是否可信", "contentProposition": "用实拍解释底盘能力",
                    "titleStructure": "质疑 + 证明", "requiredProof": ["关键镜头"],
                    "commentChallenges": [], "forbiddenClaims": ["销量因果"], "kpis": ["完整播放率"],
                    "evidenceIds": ids, "confidence": .88, "reason": "共同证据完整",
                }, ensure_ascii=False)

            server.execute_content_defense_job(
                job["jobId"], "local", "china", {"model": "奥迪E7X"},
                media_runner=media_runner, provider_runner=provider_runner,
            )
            with server.db() as conn:
                return get_job(conn, job["jobId"])

    def test_persistent_job_reaches_complete_and_survives_refresh(self):
        job = self._run_persistent_job()
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["progress"], 100)
        self.assertEqual(job["result"]["validation"]["status"], "published")

    def test_persistent_job_keeps_partial_quality_failure_for_human_review(self):
        job = self._run_persistent_job(failing_check=True)
        self.assertEqual(job["status"], "manual_required")
        self.assertEqual(job["result"]["validation"]["failedCheckCount"], 1)


if __name__ == "__main__":
    unittest.main()
