import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from douyin_video_insights import (
    PROMPT_VERSION,
    build_evidence_package,
    create_job,
    cross_validate,
    get_job,
    init_schema,
    list_jobs,
    normalize_output,
    resolve_video_access,
    save_manual_review,
    save_run,
    source_fingerprint,
    update_job,
)
import server
from douyin_hot_entities import save_rank_snapshot


class DouyinVideoInsightContractTest(unittest.TestCase):
    def setUp(self):
        self.item = {
            "itemId": "7650000000000000001",
            "title": "连续弯道里车身姿态发生了什么",
            "author": "测试作者",
            "tags": ["底盘", "连续弯"],
            "sourceUrl": "https://www.douyin.com/video/7650000000000000001",
            "mediaUrl": "https://media.example/video.mp4?expires=1",
            "playCount": 800000,
            "likeCount": 23000,
            "commentCount": 1900,
            "shareCount": 2100,
            "collectCount": 1700,
            "duration": 28,
        }
        self.media = [
            {"evidence_type": "transcript", "start_ms": 300, "quote_text": "先看连续三个弯的车身姿态", "source_scope": "video_body"},
            {"evidence_type": "shot", "start_ms": 2500, "quote_text": "车辆连续通过两个方向相反的弯道", "source_scope": "video_body"},
            {"evidence_type": "ocr", "start_ms": 3200, "quote_text": "连续弯挑战", "source_scope": "video_body"},
        ]

    def package(self, item=None, **kwargs):
        return build_evidence_package(item or self.item, media=self.media, comments=[{"id": "c1", "text": "这个镜头有没有加速"}], **kwargs)

    def output(self, package, mechanism="连续悬念验证", role="被验证的产品对象"):
        ids = [row["evidenceId"] for row in package["evidenceRefs"]]
        return {
            "contentSummary": "视频用连续弯实拍观察车辆姿态，而不是只罗列参数。",
            "openingHook": "开场直接提出连续弯挑战。",
            "narrativeStructure": "提出问题—连续实拍—回看姿态。",
            "emotionDrivers": ["验证欲", "驾驶代入"],
            "viralMechanisms": [mechanism, "可争论的实拍结果"],
            "primaryMechanism": mechanism,
            "brandAndModelRoles": [role],
            "primaryBrandRole": role,
            "audienceResponse": "评论质疑镜头是否加速。",
            "marketingImplications": ["保留连续镜头证明过程"],
            "reusablePatterns": ["问题先行再连续验证"],
            "copyRisks": ["不得把播放量解释成购买意向"],
            "confidence": .86,
            "evidenceCoverage": package["evidenceCoverage"],
            "evidenceRefs": {"contentSummary": ids[:2], "viralMechanisms": ids[1:3], "brandAndModelRoles": ids[1:2]},
            "limitations": [],
        }

    def test_metric_changes_do_not_change_source_fingerprint(self):
        changed = {**self.item, "playCount": 9999999, "likeCount": 999999}
        self.assertEqual(source_fingerprint(self.item), source_fingerprint(changed))
        changed["title"] = "不同的视频内容"
        self.assertNotEqual(source_fingerprint(self.item), source_fingerprint(changed))

    def test_page_url_is_not_treated_as_readable_media(self):
        item = {key: value for key, value in self.item.items() if key != "mediaUrl"}
        resolution = resolve_video_access(item)
        self.assertTrue(resolution["pageAvailable"])
        self.assertEqual(resolution["mediaAvailability"], "page_only")
        self.assertEqual(resolution["mediaUrl"], "")
        self.assertIn("不等于系统已读取视频本体", "".join(resolution["errors"]))

    def test_complete_evidence_keeps_timestamps_and_current_item_only(self):
        package = self.package()
        self.assertEqual(package["itemId"], self.item["itemId"])
        self.assertEqual(package["transcriptSegments"][0]["startMs"], 300)
        self.assertEqual(package["keyframes"][0]["startMs"], 2500)
        self.assertTrue(all(row["contentId"] == self.item["itemId"] for row in package["evidenceRefs"]))
        self.assertEqual(package["promptVersion"], PROMPT_VERSION)

    def test_strict_output_rejects_missing_fields_and_foreign_evidence(self):
        package = self.package()
        with self.assertRaises(ValueError):
            normalize_output({"contentSummary": "只有摘要"}, package)
        output = self.output(package)
        output["evidenceRefs"] = {"contentSummary": ["V:other-video"]}
        with self.assertRaises(ValueError):
            normalize_output(output, package)

    def test_schema_normalizer_preserves_common_string_and_object_values(self):
        package = self.package()
        output = self.output(package)
        output.update({"emotionDrivers": "验证欲与驾驶代入", "marketingImplications": "保留连续镜头",
                       "brandAndModelRoles": {"测试车型": "被验证对象"}, "confidence": "high"})
        normalized = normalize_output(output, package)
        self.assertEqual(normalized["emotionDrivers"], ["验证欲与驾驶代入"])
        self.assertEqual(normalized["brandAndModelRoles"], ["测试车型：被验证对象"])
        self.assertEqual(normalized["confidence"], .85)

    def test_three_way_consensus_majority_conflict_and_failure(self):
        package = self.package()
        aligned = {key: self.output(package) for key in ("qwen", "deepseek", "kimi")}
        self.assertEqual(cross_validate(package, aligned)["status"], "verified")
        aligned["kimi"] = self.output(package, mechanism="情绪冲突")
        majority = cross_validate(package, aligned)
        self.assertEqual(majority["status"], "majority_aligned")
        self.assertTrue(majority["disagreements"])
        aligned["deepseek"] = self.output(package, mechanism="知识反差")
        self.assertEqual(cross_validate(package, aligned)["status"], "manual_required")
        partial = cross_validate(package, {"qwen": self.output(package), "deepseek": self.output(package)}, {"kimi": "timeout"})
        self.assertEqual(partial["status"], "incomplete")
        self.assertEqual(sum(row["status"] == "completed" for row in partial["runs"]), 2)
        self.assertNotIn("kimi", json.dumps(partial, ensure_ascii=False).lower())

    def test_unreadable_video_is_limited_even_if_models_return(self):
        item = {key: value for key, value in self.item.items() if key != "mediaUrl"}
        package = build_evidence_package(item, media=[], comments=[])
        outputs = {key: self.output(package) for key in ("qwen", "deepseek", "kimi")}
        result = cross_validate(package, outputs)
        self.assertEqual(result["status"], "limited_analysis")
        self.assertIn("不能声称已读完整视频", result["reason"])

    def test_job_cache_dedupes_across_ranges_and_isolates_org_and_edition(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        init_schema(conn)
        first, created = create_job(conn, org_id="org-a", edition="china", view="videos", range_key="24h", item=self.item)
        second, recreated = create_job(conn, org_id="org-a", edition="china", view="videos", range_key="30d", item={**self.item, "playCount": 1})
        self.assertTrue(created)
        self.assertFalse(recreated)
        self.assertEqual(first["jobId"], second["jobId"])
        self.assertTrue(second["cacheHit"])
        other, other_created = create_job(conn, org_id="org-b", edition="china", view="videos", range_key="24h", item=self.item)
        edition, edition_created = create_job(conn, org_id="org-a", edition="global", view="videos", range_key="24h", item=self.item)
        self.assertTrue(other_created and edition_created)
        self.assertNotEqual(other["jobId"], edition["jobId"])
        self.assertEqual(len(list_jobs(conn, org_id="org-a", edition="china")), 1)

    def test_topic_cannot_create_video_insight(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        with self.assertRaises(ValueError):
            create_job(conn, org_id="local", edition="china", view="topics", range_key="24h", item=self.item)

    def test_raw_runs_are_separate_and_retry_history_is_preserved(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        job, _ = create_job(conn, org_id="local", edition="china", view="videos", range_key="24h", item=self.item)
        package = self.package()
        for provider in ("qwen", "deepseek", "kimi"):
            save_run(conn, job_id=job["jobId"], provider=provider, evidence_fingerprint=package["evidenceFingerprint"],
                     status="completed", raw=self.output(package))
        save_run(conn, job_id=job["jobId"], provider="kimi", evidence_fingerprint=package["evidenceFingerprint"],
                 status="failed", error="timeout")
        rows = conn.execute("select provider_key,attempt_no,status from douyin_video_insight_runs order by provider_key,attempt_no").fetchall()
        self.assertEqual(len(rows), 4)
        self.assertEqual([row["attempt_no"] for row in rows if row["provider_key"] == "kimi"], [1, 2])
        payload = get_job(conn, job["jobId"], "local")
        self.assertEqual(len(payload["runStatus"]), 3)
        self.assertNotIn("qwen", json.dumps(payload, ensure_ascii=False).lower())

    def test_manual_review_selects_one_public_slot_and_keeps_disagreement(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        job, _ = create_job(conn, org_id="local", edition="china", view="videos", range_key="24h", item=self.item)
        package = self.package()
        first, second = self.output(package, mechanism="产品验证"), self.output(package, mechanism="知识反差")
        result = {"validation": {"status": "manual_required", "disagreements": [{"field": "viralMechanisms", "opinions": ["产品验证", "知识反差"]}],
                                 "runs": [{"slot": 1, "label": "MMN独立分析 1", "status": "completed", "output": first},
                                          {"slot": 2, "label": "MMN独立分析 2", "status": "completed", "output": second}]}}
        update_job(conn, job["jobId"], status="manual_required", result=result, evidence=package)
        reviewed = save_manual_review(conn, job_id=job["jobId"], org_id="local", action="confirm",
                                      selected_slot=2, note="采用证据解释更完整的一路")
        self.assertEqual(reviewed["status"], "completed")
        self.assertEqual(reviewed["result"]["validation"]["status"], "human_confirmed")
        self.assertEqual(reviewed["result"]["validation"]["finalInsight"]["primaryMechanism"], "知识反差")
        self.assertTrue(reviewed["result"]["validation"]["disagreements"])
        self.assertEqual(reviewed["manualReview"]["selectedSlot"], 2)

    def test_retry_one_failed_slot_reuses_only_same_evidence_successes(self):
        package = self.package()
        calls = []
        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "mmn.db"):
            server.init_db()
            with server.db() as conn:
                job, _ = create_job(conn, org_id="local", edition="china", view="videos", range_key="24h", item=self.item)
                for provider in ("qwen", "deepseek"):
                    save_run(conn, job_id=job["jobId"], provider=provider,
                             evidence_fingerprint=package["evidenceFingerprint"], status="completed", raw=self.output(package))
                save_run(conn, job_id=job["jobId"], provider="kimi",
                         evidence_fingerprint=package["evidenceFingerprint"], status="failed", error="timeout")
            result = server.run_video_insight_reviews(
                job["jobId"], package, retry_slot="3",
                provider_runner=lambda provider, messages: calls.append(provider) or json.dumps(self.output(package), ensure_ascii=False),
            )
        self.assertEqual(calls, ["kimi"])
        self.assertEqual(result["status"], "verified")

    def test_server_runs_three_independent_calls_and_persists_completed_result(self):
        captured = []

        def media_runner(assets, max_assets=1):
            return self.media, {"processedAssetCount": 1}, []

        def provider_runner(provider, messages):
            captured.append((provider, json.loads(messages[-1]["content"]), messages[-1]["content"]))
            packet = json.loads(messages[-1]["content"])
            return json.dumps(self.output(packet), ensure_ascii=False)

        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "mmn.db"):
            server.init_db()
            with server.db() as conn:
                snapshot = save_rank_snapshot(conn, [self.item], view="videos", range_key="24h")
                job, _ = create_job(conn, org_id="local", edition="china", view="videos", range_key="24h",
                                    item=snapshot["items"][0], request={"item": snapshot["items"][0]})
            server.execute_video_insight_job(job["jobId"], "local", "china", {"item": snapshot["items"][0]},
                                             media_runner=media_runner, provider_runner=provider_runner,
                                             evidence_resolver=lambda item: (item, [], resolve_video_access(item)))
            with server.db() as conn:
                saved = get_job(conn, job["jobId"], "local")
                run_count = conn.execute("select count(*) from douyin_video_insight_runs where job_id=?", (job["jobId"],)).fetchone()[0]
        self.assertEqual(saved["status"], "completed")
        self.assertEqual(saved["result"]["validation"]["status"], "verified")
        self.assertEqual(run_count, 3)
        self.assertEqual(len(captured), 3)
        self.assertEqual(len({row[2] for row in captured}), 1)
        self.assertTrue(all("previous" not in row[2].lower() for row in captured))

    def test_server_uses_browser_frames_as_video_body_evidence(self):
        captured_media = []

        def browser_runner(source_url, item_id, root, **_kwargs):
            frame = Path(root) / "frame.jpg"
            frame.write_bytes(b"browser-frame")
            return {"imagePaths": [str(frame)], "timestampsMs": [4200], "durationMs": 28000,
                    "mediaFingerprint": "browser-proof", "mediaAvailable": True}

        def process_runner(assets, max_assets=1):
            captured_media.append(assets[0]["media"])
            return ([{"evidence_type": "shot", "start_ms": 4200,
                      "quote_text": "浏览器播放页第4.2秒出现车辆", "source_scope": "video_body"}], {}, [])

        def provider_runner(_provider, messages):
            return json.dumps(self.output(json.loads(messages[-1]["content"])), ensure_ascii=False)

        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "mmn.db"), \
                patch.object(server, "process_representative_media", side_effect=process_runner):
            server.init_db()
            with server.db() as conn:
                snapshot = save_rank_snapshot(conn, [self.item], view="videos", range_key="24h")
                job, _ = create_job(conn, org_id="local", edition="china", view="videos", range_key="24h",
                                    item=snapshot["items"][0], request={"item": snapshot["items"][0]})
            server.execute_video_insight_job(
                job["jobId"], "local", "china", {"item": snapshot["items"][0]},
                provider_runner=provider_runner, browser_runner=browser_runner,
                evidence_resolver=lambda item: (item, [], resolve_video_access(item)),
            )
            with server.db() as conn:
                saved = get_job(conn, job["jobId"], "local")
        self.assertEqual(saved["status"], "completed")
        self.assertEqual(saved["evidencePackage"]["acquisition"]["pageVerification"], "browser_playback")
        self.assertTrue(saved["evidencePackage"]["acquisition"]["mediaAvailable"])
        self.assertEqual(saved["evidencePackage"]["keyframes"][0]["startMs"], 4200)
        self.assertEqual(captured_media[0]["localImageTimestampsMs"], [4200])

    def test_server_partial_failure_is_incomplete_without_template_fill(self):
        def provider_runner(provider, messages):
            if provider == "kimi":
                raise TimeoutError("provider timeout")
            return json.dumps(self.output(json.loads(messages[-1]["content"])), ensure_ascii=False)

        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "mmn.db"):
            server.init_db()
            with server.db() as conn:
                snapshot = save_rank_snapshot(conn, [self.item], view="videos", range_key="24h")
                job, _ = create_job(conn, org_id="local", edition="china", view="videos", range_key="24h",
                                    item=snapshot["items"][0], request={"item": snapshot["items"][0]})
            server.execute_video_insight_job(job["jobId"], "local", "china", {"item": snapshot["items"][0]},
                                             media_runner=lambda assets, max_assets=1: (self.media, {}, []),
                                             provider_runner=provider_runner,
                                             evidence_resolver=lambda item: (item, [], resolve_video_access(item)))
            with server.db() as conn:
                saved = get_job(conn, job["jobId"], "local")
        self.assertEqual(saved["status"], "incomplete")
        self.assertTrue(saved["retryable"])
        self.assertEqual(sum(row["status"] == "completed" for row in saved["result"]["validation"]["runs"]), 2)

    def test_daily_pipeline_never_schedules_video_insights_without_user_click(self):
        snapshots = []
        for view in ("videos", "topics"):
            for range_key in ("24h", "7d", "30d"):
                snapshots.append({"view": view, "range": range_key, "capturedAt": "2026-07-21T00:00:00Z",
                                  "items": [{"item_id": self.item["itemId"] if view == "videos" else f"topic-{range_key}",
                                             "title": self.item["title"] if view == "videos" else f"话题{range_key}"}]})
        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "mmn.db"):
            result = server.run_douyin_collector_pipeline(
                collector_runner=lambda progress_callback=None: snapshots,
                recognition_runner=lambda payload, org_id: {"items": [], "dualModelReady": True, "errors": {}},
                insight_starter=lambda *args, **kwargs: self.fail("collector must not create video insight jobs"),
            )
        self.assertEqual(result["videoInsightJobCount"], 0)
        self.assertEqual(result["videoInsightTriggerMode"], "manual")

    def test_service_restart_keeps_evidence_and_marks_running_job_retryable(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "mmn.db"):
            server.init_db()
            with server.db() as conn:
                job, _ = create_job(conn, org_id="local", edition="china", view="videos", range_key="24h", item=self.item)
                package = self.package()
                update_job(conn, job["jobId"], status="analyzing", stage="analyzing", progress=62, evidence=package)
            server.init_db()
            with server.db() as conn:
                restored = get_job(conn, job["jobId"], "local")
        self.assertEqual(restored["status"], "incomplete")
        self.assertTrue(restored["retryable"])
        self.assertEqual(restored["evidenceFingerprint"], package["evidenceFingerprint"])


if __name__ == "__main__":
    unittest.main()
