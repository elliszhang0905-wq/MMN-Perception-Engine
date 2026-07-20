import json
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from douyin_hot_entities import (
    finalize_manual_review,
    init_schema,
    latest_rank_snapshot,
    manual_review_queue,
    recognize_items,
    save_rank_snapshot,
)
import server


class DouyinHotEntityRecognitionTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        init_schema(self.conn)
        self.items = [{
            "itemId": "video-1",
            "sourceType": "video",
            "title": "年轻人的车当然要懂享受｜零跑全新B10",
            "author": "零跑汽车",
            "tags": ["零跑B10", "座舱体验"],
            "rank": 2,
            "playCount": 5392000,
            "sourceUrl": "https://www.douyin.com/video/video-1",
        }]

    def tearDown(self):
        self.conn.close()

    @staticmethod
    def response(model="B10"):
        return {"items": [{"id": "video-1", "mentions": [{
            "brand": "零跑汽车",
            "model": model,
            "relation": "主角",
            "evidenceType": "标题明确",
            "evidenceText": f"零跑全新{model}",
            "confidence": .96,
        }]}]}

    def test_two_models_align_and_build_brand_model_radar(self):
        result = recognize_items(
            self.conn,
            self.items,
            primary_runner=lambda _: self.response(),
            reviewer_runner=lambda _: self.response(),
            primary_configured=True,
            reviewer_configured=True,
        )
        self.assertTrue(result["dualModelReady"])
        self.assertEqual(result["items"][0]["status"], "aligned")
        self.assertEqual(result["items"][0]["mentions"][0]["model"], "B10")
        self.assertEqual(result["radar"]["brands"][0]["name"], "零跑")
        self.assertEqual(result["radar"]["models"][0]["name"], "B10")
        self.assertEqual(result["radar"]["models"][0]["totalPlay"], 5392000)

    def test_unchanged_item_reuses_cache_without_model_calls(self):
        calls = {"primary": 0, "reviewer": 0}

        def primary(_):
            calls["primary"] += 1
            return self.response()

        def reviewer(_):
            calls["reviewer"] += 1
            return self.response()

        first = recognize_items(self.conn, self.items, primary_runner=primary, reviewer_runner=reviewer,
                                primary_configured=True, reviewer_configured=True)
        second = recognize_items(self.conn, self.items, primary_runner=primary, reviewer_runner=reviewer,
                                 primary_configured=True, reviewer_configured=True)
        self.assertEqual(first["freshCount"], 1)
        self.assertEqual(second["freshCount"], 0)
        self.assertEqual(second["reusedCount"], 1)
        self.assertTrue(second["dualModelReady"])
        self.assertEqual(calls, {"primary": 1, "reviewer": 1})

    def test_model_disagreement_is_not_counted_as_confirmed_entity(self):
        result = recognize_items(
            self.conn,
            self.items,
            primary_runner=lambda _: self.response("B10"),
            reviewer_runner=lambda _: self.response("C10"),
            primary_configured=True,
            reviewer_configured=True,
        )
        self.assertEqual(result["items"][0]["status"], "conflict")
        self.assertTrue(result["items"][0]["reviewRequired"])
        self.assertEqual(result["items"][0]["mentions"], [])
        self.assertEqual(result["radar"]["models"], [])

    def test_manual_review_queue_exposes_both_model_outputs(self):
        recognize_items(
            self.conn, self.items,
            primary_runner=lambda _: self.response("B10"),
            reviewer_runner=lambda _: self.response("C10"),
            primary_configured=True, reviewer_configured=True,
        )
        queue = manual_review_queue(self.conn, ["video-1"])
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["primaryMentions"][0]["model"], "B10")
        self.assertEqual(queue[0]["reviewerMentions"][0]["model"], "C10")
        self.assertEqual(queue[0]["manualStatus"], "pending")

    def test_manual_confirmation_immediately_overrides_model_conflict(self):
        initial = recognize_items(
            self.conn, self.items,
            primary_runner=lambda _: self.response("B10"),
            reviewer_runner=lambda _: self.response("C10"),
            primary_configured=True, reviewer_configured=True,
        )
        queued = manual_review_queue(self.conn, ["video-1"])[0]
        finalize_manual_review(
            self.conn, item_id="video-1", fingerprint=queued["fingerprint"], action="confirm",
            brand="零跑", model="B10",
        )
        result = recognize_items(
            self.conn, self.items,
            primary_runner=lambda _: self.fail("manual result must be reused"),
            reviewer_runner=lambda _: self.fail("manual result must be reused"),
            primary_configured=True, reviewer_configured=True,
        )
        self.assertEqual(initial["radar"]["models"], [])
        self.assertEqual(result["items"][0]["status"], "manual_verified")
        self.assertEqual(result["items"][0]["recognitionLabel"], "人工确认")
        self.assertEqual(result["radar"]["models"][0]["name"], "B10")

    def test_manual_confirmation_cannot_be_overwritten_by_later_forced_model_result(self):
        recognize_items(
            self.conn, self.items,
            primary_runner=lambda _: self.response("B10"), reviewer_runner=lambda _: self.response("C10"),
            primary_configured=True, reviewer_configured=True,
        )
        queued = manual_review_queue(self.conn, ["video-1"])[0]
        finalize_manual_review(
            self.conn, item_id="video-1", fingerprint=queued["fingerprint"],
            action="confirm", brand="人工品牌", model="人工车型",
        )
        result = recognize_items(
            self.conn, self.items,
            primary_runner=lambda _: self.response("B10"), reviewer_runner=lambda _: self.response("C10"),
            primary_configured=True, reviewer_configured=True, force=True,
        )
        self.assertEqual(result["items"][0]["status"], "manual_verified")
        self.assertEqual(result["items"][0]["mentions"][0]["brand"], "人工品牌")
        self.assertEqual(result["radar"]["models"][0]["name"], "人工车型")

    def test_manual_confirmation_survives_later_metadata_enrichment_without_model_calls(self):
        recognize_items(
            self.conn, self.items,
            primary_runner=lambda _: self.response("B10"), reviewer_runner=lambda _: self.response("C10"),
            primary_configured=True, reviewer_configured=True,
        )
        queued = manual_review_queue(self.conn, ["video-1"])[0]
        finalize_manual_review(
            self.conn, item_id="video-1", fingerprint=queued["fingerprint"],
            action="confirm", brand="零跑", model="B10",
        )
        enriched = [{**self.items[0], "transcript": "新增字幕证据：零跑B10智能座舱"}]
        result = recognize_items(
            self.conn, enriched,
            primary_runner=lambda _: self.fail("human decision must bypass model rerun"),
            reviewer_runner=lambda _: self.fail("human decision must bypass model rerun"),
            primary_configured=True, reviewer_configured=True, force=True,
        )
        self.assertEqual(result["items"][0]["status"], "manual_verified")
        self.assertEqual(result["radar"]["models"][0]["name"], "B10")

    def test_manual_exclusion_is_final_without_creating_a_false_entity(self):
        recognize_items(
            self.conn, self.items,
            primary_runner=lambda _: self.response("B10"),
            reviewer_runner=lambda _: self.response("C10"),
            primary_configured=True, reviewer_configured=True,
        )
        queued = manual_review_queue(self.conn, ["video-1"])[0]
        finalize_manual_review(
            self.conn, item_id="video-1", fingerprint=queued["fingerprint"], action="exclude",
        )
        result = recognize_items(
            self.conn, self.items,
            primary_runner=lambda _: self.response("B10"),
            reviewer_runner=lambda _: self.response("C10"),
            primary_configured=True, reviewer_configured=True,
        )
        self.assertEqual(result["items"][0]["status"], "manual_verified")
        self.assertEqual(result["items"][0]["recognitionLabel"], "人工确认：无明确品牌车型")
        self.assertEqual(result["radar"]["models"], [])

    def test_every_recognized_item_can_be_opened_for_manual_edit(self):
        recognize_items(
            self.conn, self.items,
            primary_runner=lambda _: self.response("B10"),
            reviewer_runner=lambda _: self.response("B10"),
            primary_configured=True, reviewer_configured=True,
        )
        self.assertEqual(manual_review_queue(self.conn, ["video-1"]), [])
        queue = manual_review_queue(self.conn, ["video-1"], include_all=True)
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["status"], "aligned")
        self.assertEqual(queue[0]["mentions"][0]["model"], "B10")

    def test_missing_model_configuration_keeps_rule_result_visible_but_pending(self):
        result = recognize_items(self.conn, [{
            "itemId": "video-d99",
            "title": "零跑D99真实生活记录",
            "rank": 1,
            "playCount": 7124703,
        }])
        self.assertFalse(result["dualModelReady"])
        self.assertEqual(result["items"][0]["status"], "pending_configuration")
        self.assertEqual(result["items"][0]["mentions"][0]["model"], "D99")
        self.assertEqual(result["radar"]["brands"], [])
        self.assertEqual(result["radar"]["models"], [])

    def test_explicit_title_rules_cover_current_zero_run_and_mengshi_models(self):
        rows = [
            {"itemId": "zero-run", "title": "全新零跑C11、全新零跑C10、全新零跑C16"},
            {"itemId": "mengshi", "title": "这就是你说的环塔副驾 #猛士M817"},
        ]
        result = recognize_items(self.conn, rows)
        models = {mention["model"] for item in result["items"] for mention in item["mentions"]}
        self.assertTrue({"C10", "C11", "C16", "M817"}.issubset(models))

    def test_partial_model_disagreement_does_not_leak_aligned_subset_into_radar(self):
        primary = self.response()
        primary["items"][0]["mentions"].append({"brand": "零跑", "model": "D99", "confidence": .91})
        result = recognize_items(
            self.conn,
            self.items,
            primary_runner=lambda _: primary,
            reviewer_runner=lambda _: self.response(),
            primary_configured=True,
            reviewer_configured=True,
        )
        self.assertEqual(result["items"][0]["status"], "conflict")
        self.assertEqual(result["items"][0]["mentions"][0]["model"], "B10")
        self.assertEqual(result["radar"]["brands"], [])
        self.assertEqual(result["radar"]["models"], [])

    def test_duplicate_item_ids_are_recognized_once(self):
        duplicate = {**self.items[0], "rank": 9, "playCount": 1}
        result = recognize_items(self.conn, [self.items[0], duplicate])
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["rank"], 2)

    def test_corrupt_cached_json_is_recomputed(self):
        recognize_items(self.conn, self.items)
        self.conn.execute("update douyin_hot_entity_recognitions set result_json='not-json'")
        result = recognize_items(self.conn, self.items)
        self.assertEqual(result["freshCount"], 1)

    def test_content_change_creates_a_new_recognition(self):
        recognize_items(self.conn, self.items)
        changed = [{**self.items[0], "title": "零跑全新B10新增座舱体验"}]
        result = recognize_items(self.conn, changed)
        self.assertEqual(result["freshCount"], 1)
        count = self.conn.execute("select count(*) from douyin_hot_entity_recognitions").fetchone()[0]
        self.assertEqual(count, 2)

    def test_signed_cover_url_change_does_not_trigger_model_rerun(self):
        calls = {"primary": 0, "reviewer": 0}

        def primary(_):
            calls["primary"] += 1
            return self.response()

        def reviewer(_):
            calls["reviewer"] += 1
            return self.response()

        first_items = [{**self.items[0], "coverUrl": "https://example.com/cover.jpg?signature=old"}]
        changed_cover = [{**self.items[0], "coverUrl": "https://example.com/cover.jpg?signature=new"}]
        recognize_items(self.conn, first_items, primary_runner=primary, reviewer_runner=reviewer,
                        primary_configured=True, reviewer_configured=True)
        result = recognize_items(self.conn, changed_cover, primary_runner=primary, reviewer_runner=reviewer,
                                 primary_configured=True, reviewer_configured=True)
        self.assertEqual(result["freshCount"], 0)
        self.assertEqual(calls, {"primary": 1, "reviewer": 1})

    def test_cached_entities_use_current_rank_and_play_count(self):
        recognize_items(self.conn, self.items, primary_runner=lambda _: self.response(), reviewer_runner=lambda _: self.response(),
                        primary_configured=True, reviewer_configured=True)
        updated = [{**self.items[0], "rank": 5, "playCount": 9999999}]
        result = recognize_items(self.conn, updated, primary_runner=lambda _: self.fail("cache should be reused"),
                                 reviewer_runner=lambda _: self.fail("cache should be reused"),
                                 primary_configured=True, reviewer_configured=True)
        self.assertEqual(result["freshCount"], 0)
        self.assertEqual(result["items"][0]["rank"], 5)
        self.assertEqual(result["radar"]["models"][0]["bestRank"], 5)
        self.assertEqual(result["radar"]["models"][0]["totalPlay"], 9999999)

    def test_equivalent_brand_and_model_spellings_align(self):
        primary = self.response("Q6L e tron")
        reviewer = self.response("Q6L e-tron")
        primary["items"][0]["mentions"][0]["brand"] = "Audi"
        reviewer["items"][0]["mentions"][0]["brand"] = "奥迪"
        result = recognize_items(self.conn, self.items, primary_runner=lambda _: primary, reviewer_runner=lambda _: reviewer,
                                 primary_configured=True, reviewer_configured=True)
        self.assertEqual(result["items"][0]["status"], "aligned")
        self.assertEqual(result["items"][0]["mentions"][0]["brand"], "奥迪")
        self.assertEqual(result["items"][0]["mentions"][0]["model"], "Q6L e-tron")

    def test_invalid_items_and_non_finite_metrics_are_handled(self):
        with self.assertRaisesRegex(ValueError, "有效榜单内容"):
            recognize_items(self.conn, [None, "bad-row"])
        result = recognize_items(self.conn, [{"itemId": "infinite", "title": "无车型", "rank": "inf", "playCount": "inf"}])
        self.assertEqual(result["items"][0]["rank"], 1)
        self.assertEqual(result["items"][0]["playCount"], 0)

    def test_malformed_model_output_falls_back_without_false_confirmation(self):
        result = recognize_items(self.conn, self.items, primary_runner=lambda _: ["bad"], reviewer_runner=lambda _: {"items": "bad"},
                                 primary_configured=True, reviewer_configured=True)
        self.assertFalse(result["dualModelReady"])
        self.assertEqual(result["items"][0]["status"], "pending_configuration")
        self.assertIn("primary", result["errors"])
        self.assertIn("reviewer", result["errors"])

    def test_unknown_model_enums_are_normalized_to_safe_values(self):
        output = self.response()
        output["items"][0]["mentions"][0].update({"relation": "竞品", "evidenceType": "自由猜测"})
        result = recognize_items(self.conn, self.items, primary_runner=lambda _: output, reviewer_runner=lambda _: output,
                                 primary_configured=True, reviewer_configured=True)
        mention = result["items"][0]["mentions"][0]
        self.assertEqual(mention["relation"], "提及")
        self.assertEqual(mention["evidenceType"], "模型推断")

    def test_each_cache_row_stores_only_its_own_model_output(self):
        second = {**self.items[0], "itemId": "video-2", "title": "零跑D99"}
        output = self.response()
        output["items"].append({"id": "video-2", "mentions": [{"brand": "零跑", "model": "D99", "confidence": .9}]})
        recognize_items(self.conn, [self.items[0], second], primary_runner=lambda _: output, reviewer_runner=lambda _: output,
                        primary_configured=True, reviewer_configured=True)
        rows = self.conn.execute("select primary_json from douyin_hot_entity_recognitions order by item_key").fetchall()
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(len(json.loads(row[0])["items"]) == 1 for row in rows))

    def test_server_pipeline_uses_both_configured_models(self):
        response = json.dumps(self.response(), ensure_ascii=False)
        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "mmn.db"), \
             patch.object(server, "qwen_config", return_value={"configured": True}), \
             patch.object(server, "deepseek_config", return_value={"configured": True}), \
             patch.object(server, "call_qwen", return_value=response) as primary, \
             patch.object(server, "call_deepseek", return_value=response) as reviewer:
            result = server.run_douyin_hot_entity_recognition({"edition": "china", "items": self.items}, "org-a")
        self.assertEqual(result["outputLabel"], "MMN多模态策略输出")
        self.assertEqual(result["items"][0]["status"], "aligned")
        primary.assert_called_once()
        reviewer.assert_called_once()

    def test_server_manual_review_publishes_without_calling_models(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "mmn.db"):
            with server.db() as conn:
                recognize_items(
                    conn, self.items, org_id="org-a",
                    primary_runner=lambda _: self.response("B10"),
                    reviewer_runner=lambda _: self.response("C10"),
                    primary_configured=True, reviewer_configured=True,
                )
                queued = manual_review_queue(conn, ["video-1"], org_id="org-a")[0]
            body = {"edition": "china", "itemId": "video-1", "fingerprint": queued["fingerprint"],
                    "action": "confirm", "brand": "零跑", "model": "B10"}
            with patch.object(server, "call_qwen", side_effect=AssertionError("manual decision must not call Qwen")), \
                 patch.object(server, "call_deepseek", side_effect=AssertionError("manual decision must not call DeepSeek")):
                result = server.audit_douyin_hot_manual_review(body, org_id="org-a")
            self.assertTrue(result["published"])
            self.assertEqual(result["message"], "人工确认已生效并进入品牌车型雷达")
            with server.db() as conn:
                stored = json.loads(conn.execute(
                    "select result_json from douyin_hot_entity_recognitions where org_id='org-a' and item_key='video-1'"
                ).fetchone()[0])
            self.assertEqual(stored["status"], "manual_verified")

    def test_manual_review_payload_creates_editable_rows_before_model_pass_finishes(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "mmn.db"):
            with server.db() as conn:
                save_rank_snapshot(conn, self.items, org_id="org-a", view="videos", range_key="24h")
            payload = server.douyin_hot_manual_review_payload(
                org_id="org-a", edition="china", view="videos", range_key="24h",
            )
        self.assertEqual(payload["counts"]["total"], 1)
        self.assertEqual(payload["items"][0]["itemId"], "video-1")
        self.assertEqual(payload["items"][0]["status"], "pending_configuration")

    def test_rank_snapshots_are_isolated_by_view_and_time_range(self):
        save_rank_snapshot(self.conn, [{
            "item_id": "24-hour-video",
            "title": "24小时视频",
            "play_count": 100,
            "cover": {"url_list": ["https://example.com/24.jpg"]},
        }], view="videos", range_key="24h")
        save_rank_snapshot(self.conn, [{
            "item_id": "30-day-video",
            "title": "30天视频",
            "play_count": 900,
            "cover": {"url_list": ["https://example.com/30.jpg"]},
        }], view="videos", range_key="30d")
        day = latest_rank_snapshot(self.conn, view="videos", range_key="24h")
        month = latest_rank_snapshot(self.conn, view="videos", range_key="30d")
        topic = latest_rank_snapshot(self.conn, view="topics", range_key="30d")
        self.assertEqual(day["items"][0]["itemId"], "24-hour-video")
        self.assertEqual(month["items"][0]["itemId"], "30-day-video")
        self.assertEqual(month["items"][0]["coverUrl"], "https://example.com/30.jpg")
        self.assertEqual(month["items"][0]["sourceUrl"], "")
        self.assertFalse(topic["available"])

    def test_video_snapshot_builds_original_video_url_and_keeps_real_metrics(self):
        result = save_rank_snapshot(self.conn, [{
            "item_id": "7655593686679506202",
            "title": "真实视频",
            "author_name": "创作者",
            "play_count": 7124703,
            "like_count": 69000,
            "comment_count": 223,
            "key_words": ["汽车", "新车"],
            "subtitle": "字幕中明确提到奥迪Q6L e-tron",
        }], view="videos", range_key="7d")
        item = result["items"][0]
        self.assertEqual(item["sourceUrl"], "https://www.douyin.com/video/7655593686679506202")
        self.assertEqual(item["playCount"], 7124703)
        self.assertEqual(item["tags"], ["汽车", "新车"])
        self.assertEqual(item["transcript"], "字幕中明确提到奥迪Q6L e-tron")

    def test_video_snapshot_preserves_direct_media_without_confusing_page_url(self):
        result = save_rank_snapshot(self.conn, [{
            "item_id": "7651268281679977754", "title": "真实媒体结构",
            "video": {"play_addr": {"url_list": ["https://media.example/video.mp4?token=abc"]}},
            "subtitle_url": {"url_list": ["https://media.example/subtitle.json"]},
        }], view="videos", range_key="24h")
        item = result["items"][0]
        self.assertEqual(item["sourceUrl"], "https://www.douyin.com/video/7651268281679977754")
        self.assertEqual(item["mediaUrl"], "https://media.example/video.mp4?token=abc")
        self.assertEqual(item["subtitleUrl"], "https://media.example/subtitle.json")

    def test_collector_status_isolated_by_edition(self):
        snapshots = [{
            "item_id": f"{view}-{range_key}", "title": f"{view}-{range_key}", "play_count": 10,
        } for view in ("videos", "topics") for range_key in ("24h", "7d", "30d")]
        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "mmn.db"), \
             patch.object(server, "douyin_collector_browser_open", return_value=False):
            with server.db() as conn:
                for item, (view, range_key) in zip(snapshots, ((v, r) for v in ("videos", "topics") for r in ("24h", "7d", "30d"))):
                    save_rank_snapshot(conn, [item], org_id="org-edition", edition="china", view=view, range_key=range_key)
            china = server.douyin_collector_status("org-edition", "china")
            global_status = server.douyin_collector_status("org-edition", "global")
        self.assertTrue(china["freshToday"])
        self.assertFalse(global_status["freshToday"])

    def test_invalid_snapshot_scope_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "类型或时间范围"):
            save_rank_snapshot(self.conn, self.items, view="videos", range_key="year")

    def test_collector_pipeline_saves_six_snapshots_and_runs_six_analyses(self):
        snapshots = []
        for view in ("videos", "topics"):
            for range_key in ("24h", "7d", "30d"):
                snapshots.append({
                    "view": view, "range": range_key, "capturedAt": "2026-07-13T22:40:00+08:00",
                    "items": [{"item_id": f"{view}-{range_key}", "title": f"{view}-{range_key}", "play_count": 10}],
                })
        progress, analyses = [], []

        def collector_runner(progress_callback=None):
            progress_callback("collecting", 55, "已抓取 6/6 个真实榜单")
            return snapshots

        def recognition_runner(payload, org_id):
            analyses.append((payload["view"], payload["range"], org_id))
            return {"items": [], "radar": {"brands": [], "models": []}, "dualModelReady": True, "errors": {}}

        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "mmn.db"):
            result = server.run_douyin_collector_pipeline(
                org_id="org-a", edition="china", collector_runner=collector_runner,
                recognition_runner=recognition_runner, progress_callback=lambda *row: progress.append(row),
                insight_starter=lambda body, org_id="local": {"jobId": body["itemId"]},
            )
            with server.db() as conn:
                count = conn.execute("select count(*) from douyin_hot_rank_snapshots").fetchone()[0]
        self.assertEqual(result["snapshotCount"], 6)
        self.assertEqual(result["analysisCount"], 6)
        self.assertEqual(count, 6)
        self.assertEqual(len(analyses), 6)
        self.assertIn(("delivery", 97, "分析完成，正在刷新看板并生成交付状态"), progress)

    def test_collector_pipeline_rejects_partial_model_delivery(self):
        snapshots = [{
            "view": view, "range": range_key, "capturedAt": "2026-07-13T22:40:00+08:00",
            "items": [{"item_id": f"{view}-{range_key}", "title": "零跑C11", "play_count": 10}],
        } for view in ("videos", "topics") for range_key in ("24h", "7d", "30d")]

        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "mmn.db"):
            with self.assertRaisesRegex(RuntimeError, "双模型分析未通过"):
                server.run_douyin_collector_pipeline(
                    org_id="org-a", edition="china", collector_runner=lambda progress_callback=None: snapshots,
                    recognition_runner=lambda payload, org_id: {
                        "items": [], "dualModelReady": False, "errors": {"primary": "千问超时"},
                    },
                    insight_starter=lambda body, org_id="local": {"jobId": body["itemId"]},
                )

    def test_collector_job_reports_real_numeric_progress(self):
        def runner(org_id, edition, progress_callback):
            progress_callback("login", 8, "验证登录")
            progress_callback("collecting", 55, "抓取完成")
            progress_callback("analysis", 93, "分析完成")
            return {"snapshotCount": 6}

        job = server.start_douyin_collector_job(org_id="progress-org", runner=runner)
        deadline = time.time() + 2
        while time.time() < deadline:
            job = server.get_douyin_collector_job(job["jobId"], "progress-org")
            if job["status"] == "completed":
                break
            time.sleep(.01)
        self.assertEqual(job["status"], "completed")
        self.assertEqual(job["progress"], 100)
        self.assertEqual(job["stage"], "completed")
        self.assertEqual(job["result"]["snapshotCount"], 6)


if __name__ == "__main__":
    unittest.main()
