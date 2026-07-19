import unittest
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import server


ROOT = Path(__file__).resolve().parents[1]


def complete_delivery_payload(count=1):
    samples = [{"id": f"sample-{index}", "blogger_name": "超哥超车", "vertical_domain": "汽车垂直内容"} for index in range(count)]
    sources = [{"id": f"source-{index}", "author": "超哥超车"} for index in range(count)]
    profile = {
        "id": "profile-1", "blogger_name": "超哥超车", "vertical_domain": "汽车垂直内容",
        "validation_status": "manual_required", "source_sample_count": count,
        "professional_background": "汽车垂直内容判断能力",
        "comparison_logic": "固定预算和场景后比较",
        "evidence_preference": "公开且可复验的证据",
        "reusable_agent_instruction": "基于公开样本生成判断",
        "script_template": "问题到证据再到验证动作",
        "report_template": "结论、证据、边界、动作",
        "evaluation_framework": ["问题", "证据", "边界"],
        "terminology_system": ["预算", "场景"],
        "judgment_rules": ["结论必须可复验"],
        "content_structure_patterns": ["先问题后证据"],
        "marketing_translation_patterns": ["转成用户决策清单"],
        "strategy_assets": [{"name": "策略1"}, {"name": "策略2"}],
        "script_assets": [{"name": "脚本1"}, {"name": "脚本2"}],
    }
    return {
        "imported": count,
        "sourceMode": "social_assistant",
        "sourcePriority": "primary",
        "stats": {"samples": count},
        "result": {"profile": profile, "samples": samples, "sources": sources},
    }


class FakeCreatorRepository:
    def list_creators(self, org_id):
        return [{
            "id": "creator-1",
            "display_name": "冷静的饺子",
            "platform": "xiaohongshu",
            "profile": {
                "nickname": "冷静的饺子",
                "identity": {"status": "needs_review", "sourceUrl": "https://xhs/creator-1"},
                "followers": {"value": 23000, "availability": "available"},
            },
        }]

    def list_tasks(self, org_id):
        return [{
            "id": "task-1", "creator_url": "https://xhs/creator-1", "status": "completed",
            "stage": "review", "progress": 100,
        }]

    def creator_detail(self, creator_id):
        return {
            "profile": {
                "status": "needs_review",
                "dna": {
                    "summary": "证据索引草稿",
                    "generationMode": "deterministic_evidence_index",
                    "representativeContent": [{"title": "底盘舒适性怎么判断"}],
                },
            },
            "assets": [{"id": "asset-1"}],
        }


class BloggerIncubationWorkbenchTest(unittest.TestCase):
    def test_general_auto_samples_do_not_inherit_chassis_profile(self):
        sources = [server.normalize_blogger_source({
            "达人昵称": "超哥超车",
            "视频描述": title,
            "视频链接": f"https://www.douyin.com/video/{index}",
        }, "【社媒助手】达人「超哥超车」的视频数据.xlsx", "digest") for index, title in enumerate([
            "油车价格大降价，买车三买三不买",
            "粉丝连麦：50万预算买什么车更理性",
            "新能源汽车真的有看见的那么好吗",
        ])]
        samples = [server.distill_blogger_sample(source) for source in sources]
        profile = server.blogger_skill_profile_from_samples(samples, blogger_name="超哥超车")

        self.assertEqual(server.dominant_blogger_domain(samples), "汽车垂直内容")
        self.assertEqual(profile["vertical_domain"], "汽车垂直内容")
        self.assertNotIn("底盘工程方向", profile["professional_background"])
        self.assertIn("预算与使用场景", profile["evaluation_framework"])

    def test_filename_creator_must_match_export_rows(self):
        rows = [{"视频描述": "购车建议", "达人昵称": "另一位达人"}]
        with patch.object(server, "generic_rows_from_file", return_value=rows):
            with self.assertRaisesRegex(ValueError, "身份不一致"):
                server.import_blogger_skill_file(
                    b"xlsx", "【社媒助手】达人「超哥超车」的视频数据.xlsx"
                )

    def test_file_without_named_creator_rejects_mixed_accounts(self):
        rows = [
            {"视频描述": "购车建议一", "达人昵称": "达人甲"},
            {"视频描述": "购车建议二", "达人昵称": "达人乙"},
        ]
        with patch.object(server, "generic_rows_from_file", return_value=rows):
            with self.assertRaisesRegex(ValueError, "多个达人"):
                server.import_blogger_skill_file(b"xlsx", "达人视频数据.xlsx")

    def test_async_import_job_persists_four_stage_progress_and_result(self):
        with tempfile.TemporaryDirectory() as temp_dir, \
                patch.object(server, "DB_PATH", Path(temp_dir) / "jobs.db"), \
                patch.object(server, "BLOGGER_SKILL_JOB_ROOT", Path(temp_dir) / "job-files"):
            server.init_db()

            def runner(data, filename, edition, limit, progress_callback):
                for stage, progress in (("import", 20), ("distillation", 45), ("analysis", 80), ("delivery", 98)):
                    progress_callback(stage, progress, f"{stage} ready")
                return complete_delivery_payload(12)

            job = server.start_blogger_skill_import_job(
                b"workbook", "【社媒助手】达人「超哥超车」的视频数据.xlsx", runner=runner
            )
            deadline = time.time() + 3
            while time.time() < deadline:
                job = server.get_blogger_skill_import_job(job["id"])
                if job["status"] == "completed":
                    break
                time.sleep(.02)

            self.assertEqual(job["status"], "completed")
            self.assertEqual(job["progress"], 100)
            self.assertEqual(job["importedCount"], 12)
            self.assertEqual(job["result"]["creatorName"], "超哥超车")
            self.assertEqual(job["result"]["verticalDomain"], "汽车垂直内容")
            self.assertTrue({"import", "distillation", "analysis", "delivery"}.issubset(
                {event["stage"] for event in job["stages"]}
            ))

    def test_failed_import_job_can_retry_the_same_preserved_file(self):
        with tempfile.TemporaryDirectory() as temp_dir, \
                patch.object(server, "DB_PATH", Path(temp_dir) / "jobs.db"), \
                patch.object(server, "BLOGGER_SKILL_JOB_ROOT", Path(temp_dir) / "job-files"):
            server.init_db()

            def failing_runner(data, filename, edition, limit, progress_callback):
                progress_callback("analysis", 48, "analysis started")
                raise ValueError("能力画像证据不足")

            job = server.start_blogger_skill_import_job(
                b"workbook", "【社媒助手】达人「超哥超车」的视频数据.xlsx", runner=failing_runner
            )
            deadline = time.time() + 3
            while time.time() < deadline:
                job = server.get_blogger_skill_import_job(job["id"])
                if job["status"] == "failed":
                    break
                time.sleep(.02)
            self.assertEqual(job["status"], "failed")
            self.assertIn("证据不足", job["error"])

            def successful_runner(data, filename, edition, limit, progress_callback):
                for stage, progress in (("import", 20), ("distillation", 45), ("analysis", 80), ("delivery", 98)):
                    progress_callback(stage, progress, f"{stage} ready")
                return complete_delivery_payload(1)

            retried = server.retry_blogger_skill_import_job(job["id"], runner=successful_runner)
            self.assertEqual(retried["id"], job["id"])
            deadline = time.time() + 3
            while time.time() < deadline:
                retried = server.get_blogger_skill_import_job(job["id"])
                if retried["status"] == "completed":
                    break
                time.sleep(.02)
            self.assertEqual(retried["status"], "completed")
            self.assertEqual(retried["progress"], 100)
            self.assertEqual(retried["error"], "")

    def test_delivery_gate_rejects_incomplete_or_cross_creator_cards(self):
        payload = complete_delivery_payload(2)
        payload["result"]["profile"]["script_assets"] = []
        with self.assertRaisesRegex(ValueError, "资产不完整"):
            server.validate_blogger_import_delivery(payload, expected_creator="超哥超车")

        payload = complete_delivery_payload(2)
        payload["result"]["samples"][1]["blogger_name"] = "另一位达人"
        with self.assertRaisesRegex(ValueError, "混入其他达人"):
            server.validate_blogger_import_delivery(payload, expected_creator="超哥超车")

    def test_incomplete_card_is_rejected_before_any_database_write(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.object(server, "DB_PATH", Path(temp_dir) / "gate.db"):
            server.init_db()
            source = server.normalize_blogger_source({
                "达人昵称": "超哥超车", "视频描述": "20万预算如何选家用车",
                "视频链接": "https://www.douyin.com/video/1",
            }, "【社媒助手】达人「超哥超车」的视频数据.xlsx", "digest")

            def incomplete_distill(profile, samples, progress_callback=None):
                candidate = server.attach_blogger_assets(profile, samples)
                candidate["source_sample_count"] = len(samples)
                candidate["script_assets"] = []
                return candidate

            with patch.object(server, "blogger_skill_model_distill", side_effect=incomplete_distill):
                with self.assertRaisesRegex(ValueError, "资产不完整"):
                    server.save_blogger_skill_items([source])

            with server.db() as conn:
                self.assertEqual(conn.execute("select count(*) from blogger_skill_sources").fetchone()[0], 0)
                self.assertEqual(conn.execute("select count(*) from blogger_skill_samples").fetchone()[0], 0)
                self.assertEqual(conn.execute("select count(*) from blogger_skill_profiles").fetchone()[0], 0)

    def test_job_stage_cannot_go_backwards_or_complete_early(self):
        with tempfile.TemporaryDirectory() as temp_dir, \
                patch.object(server, "DB_PATH", Path(temp_dir) / "jobs.db"), \
                patch.object(server, "BLOGGER_SKILL_JOB_ROOT", Path(temp_dir) / "job-files"):
            server.init_db()
            with patch.object(server.Thread, "start", return_value=None):
                job = server.start_blogger_skill_import_job(
                    b"workbook", "【社媒助手】达人「超哥超车」的视频数据.xlsx"
                )
            server.update_blogger_skill_import_job(job["id"], status="running", stage="analysis", progress=60)
            with self.assertRaisesRegex(ValueError, "不能回退"):
                server.update_blogger_skill_import_job(job["id"], status="running", stage="distillation", progress=70)
            with self.assertRaisesRegex(ValueError, "全部交付门禁"):
                server.update_blogger_skill_import_job(job["id"], status="completed", stage="delivery", progress=90)
            server.init_db()
            interrupted = server.get_blogger_skill_import_job(job["id"])
            self.assertEqual(interrupted["status"], "failed")
            self.assertIsNotNone(interrupted["completedAt"])

    def test_local_directory_scan_uses_the_same_async_job_pipeline(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.object(server, "BLOGGER_SKILL_IMPORT_ROOT", Path(temp_dir)):
            older = Path(temp_dir) / "【社媒助手】达人「达人甲」的视频数据.csv"
            newer = Path(temp_dir) / "【社媒助手】达人「达人乙」的视频数据.xlsx"
            older.write_bytes(b"old")
            time.sleep(.01)
            newer.write_bytes(b"new")
            with patch.object(server, "start_blogger_skill_import_job", return_value={"id": "job-1"}) as start:
                result = server.scan_blogger_skill_imports(org_id="org-1")

            self.assertEqual(result["job"]["id"], "job-1")
            self.assertEqual(result["queuedFiles"], 1)
            self.assertEqual(result["remainingFiles"], 1)
            self.assertEqual(start.call_args.args[1], newer.name)
            self.assertEqual(start.call_args.kwargs["org_id"], "org-1")

    def test_social_assistant_fields_are_attributed_to_creator(self):
        row = {
            "视频ID": "7348040890440551707",
            "视频链接": "https://www.douyin.com/video/7348040890440551707",
            "视频描述": "帮粉丝大哥整备一台老车",
            "达人UID": "104332721863",
            "达人昵称": "猴哥说车",
            "发布时间": 45370.84258101852,
        }

        source = server.normalize_blogger_source(
            row, "【社媒助手】达人「猴哥说车」的视频数据.xlsx", "digest"
        )

        self.assertEqual(source["author"], "猴哥说车")
        self.assertEqual(source["title"], row["视频描述"])
        self.assertEqual(source["content_id"], row["视频ID"])
        self.assertEqual(source["source_url"], row["视频链接"])
        self.assertEqual(source["publish_time"], "2024-03-19 20:13:19")
        self.assertEqual(source["source_origin"], "social_assistant")
        self.assertEqual(source["raw_payload"]["_mmn_source_origin"], "social_assistant")

    def test_social_assistant_import_keeps_full_export(self):
        rows = [{"视频ID": str(i)} for i in range(100)]
        normalized = {
            "title": "样本", "content": "正文", "source_url": "https://example.com/video"
        }
        with patch.object(server, "generic_rows_from_file", return_value=rows), \
                patch.object(server, "normalize_blogger_source", return_value=normalized) as normalize, \
                patch.object(server, "normalize_content_capability_source", return_value={
                    "raw_text": "样本正文", "account_name": "猴哥说车", "platform": "抖音"
                }) as normalize_capability, \
                patch.object(server, "save_blogger_skill_items", return_value={}), \
                patch.object(server, "save_content_capability_items", return_value={
                    "sources": 100, "chunks": 100, "profiles": []
                }) as save_capability, \
                patch.object(server, "blogger_skill_payload", return_value={"ok": True}):
            result = server.import_blogger_skill_file(
                b"xlsx", "【社媒助手】达人「猴哥说车」的视频数据.xlsx", limit=30
            )

        self.assertEqual(normalize.call_count, 100)
        self.assertEqual(normalize_capability.call_count, 100)
        save_capability.assert_called_once()
        self.assertEqual(len(save_capability.call_args.args[0]), 100)
        self.assertFalse(save_capability.call_args.kwargs["sync_profiles"])
        self.assertEqual(result["contentCapabilitySync"]["chunks"], 100)
        self.assertEqual(result["sourceMode"], "social_assistant")
        self.assertEqual(result["sourcePriority"], "primary")

    def test_imported_blogger_is_published_to_creator_script_asset_selector(self):
        rows = [{
            "视频ID": str(index),
            "视频描述": f"家庭用户买车要验证的第{index}个动作",
            "达人昵称": "超哥超车",
            "平台": "抖音",
            "视频链接": f"https://www.douyin.com/video/{index}",
        } for index in range(6)]
        with tempfile.TemporaryDirectory() as temp_dir, \
                patch.object(server, "DB_PATH", Path(temp_dir) / "creator-sync.db"), \
                patch.object(server, "generic_rows_from_file", return_value=rows), \
                patch.object(server, "save_blogger_skill_items", return_value={}), \
                patch.object(server, "blogger_skill_payload", return_value={"ok": True}):
            server.init_db()
            result = server.import_blogger_skill_file(
                b"xlsx", "【社媒助手】达人「超哥超车」的视频数据.xlsx"
            )
            payload = server.content_capability_payload(edition="china")

        creator = next(item for item in payload["creatorAssets"] if item["account_name"] == "超哥超车")
        self.assertEqual(result["contentCapabilitySync"]["sources"], 6)
        self.assertEqual(creator["platform"], "抖音")
        self.assertEqual(creator["sample_count"], 6)
        self.assertIn("短视频脚本", creator["fit_tasks"])

    def test_dual_model_gate_requires_shared_evidence(self):
        profile = server.blogger_skill_profile_from_samples([], blogger_name="测试达人")
        samples = [{
            "id": f"chunk-{i}", "source_id": f"source-{i}", "original_topic": f"选题{i}",
            "professional_dimensions": ["产品体验"], "phenomenon_description": "现象",
            "engineering_reasoning": "原因", "subjective_judgment": "判断",
        } for i in range(5)]
        qwen = '{"content_topics":["产品体验"],"evaluation_framework":["场景","证据","判断"]}'
        deepseek = '{"verdict":"approved","common_evidence_ids":["source-0","source-1","source-2"],"issues":[],"summary":"通过"}'
        with patch.object(server, "call_qwen", return_value=qwen), patch.object(server, "call_deepseek", return_value=deepseek):
            result = server.blogger_skill_model_distill(profile, samples)
        self.assertEqual(result["validation_status"], "dual_model_approved")
        self.assertEqual(result["model_trace"]["critic"], "deepseek")
        self.assertEqual(len(result["model_trace"]["common_evidence_ids"]), 3)

    def test_dual_model_gate_does_not_publish_when_critic_fails(self):
        profile = server.blogger_skill_profile_from_samples([], blogger_name="测试达人")
        samples = [{"id": f"chunk-{i}", "source_id": f"source-{i}"} for i in range(5)]
        with patch.object(server, "call_qwen", return_value='{"content_topics":["汽车内容"]}'), patch.object(server, "call_deepseek", side_effect=ValueError("timeout")):
            result = server.blogger_skill_model_distill(profile, samples)
        self.assertEqual(result["validation_status"], "manual_required")
        self.assertFalse(result["model_trace"]["critic_completed"])

    def test_content_capability_account_builds_standard_profile(self):
        chunks = [{
            "id": f"chunk-{i}", "source_id": f"source-{i}", "account_name": "猴哥说车", "platform": "抖音",
            "title": f"选题{i}", "chunk_text": "综合场景里的汽车产品判断",
            "professional_knowledge": ["汽车产品认知"], "flat_tags": ["汽车垂直内容", "专业表达"],
            "knowledge_structure": "观点拆解型",
            "content_breakdown": {"main_viewpoint": "先说判断", "argument_structure": "现象 -> 证据 -> 边界"},
            "tags": {"专业领域标签": ["汽车垂直内容"], "表达风格标签": ["专业表达"], "场景标签": ["综合场景"]},
        } for i in range(6)]
        profile, samples = server.content_capability_profile_from_chunks("猴哥说车", chunks)
        self.assertEqual(profile["blogger_name"], "猴哥说车")
        self.assertEqual(profile["platform"], "抖音")
        self.assertIn("判断框架", profile["professional_background"])
        self.assertEqual(len(samples), 6)

    def test_backend_joins_creator_profile_without_migrating_legacy_skill(self):
        profiles = [{
            "blogger_name": "冷静的饺子",
            "professional_background": "底盘工程公开内容能力样本",
            "evaluation_framework": ["现象", "归因", "证据", "用户翻译"],
            "strategy_assets": [{"name": "车型传播策略辅助"}],
            "script_assets": [{"name": "短视频脚本骨架"}],
        }]
        samples = [{"blogger_name": "冷静的饺子", "id": "sample-1"}]

        rows = server.creator_incubation_workbenches(
            profiles, samples, org_id="org-1", repository=FakeCreatorRepository()
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["displayName"], "冷静的饺子")
        self.assertEqual(rows[0]["assetCount"], 1)
        self.assertEqual(rows[0]["sampleCount"], 1)
        self.assertEqual(rows[0]["lifecycleStatus"], "evidence_ready")
        self.assertEqual(rows[0]["latestTask"]["id"], "task-1")
        self.assertIn("不复制原文", rows[0]["incubation"]["boundary"])

    def test_new_creator_task_is_visible_before_creator_profile_exists(self):
        class PendingTaskRepository:
            def list_creators(self, org_id): return []
            def list_tasks(self, org_id):
                return [{
                    "id": "task-new", "creator_url": "https://v.douyin.com/new/", "platform": "douyin",
                    "status": "failed", "stage": "collect", "progress": 8,
                    "error_category": "invalid_link", "error_message": "短链接解析失败",
                    "capabilities": {"expectedCreatorName": "超哥超车"},
                }]

        rows = server.creator_incubation_workbenches([], [], repository=PendingTaskRepository())

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["displayName"], "超哥超车")
        self.assertIsNone(rows[0]["creatorId"])
        self.assertEqual(rows[0]["lifecycleStatus"], "failed")
        self.assertEqual(rows[0]["latestTask"]["progress"], 8)
        self.assertEqual(rows[0]["latestTask"]["error_message"], "短链接解析失败")

    def test_existing_blogger_page_contains_account_intake_and_workbench(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="blogger-creator-form"', html)
        self.assertIn('id="blogger-incubation-workbench"', html)
        self.assertIn("博主档案 × 能力蒸馏 × 账号孵化", html)
        self.assertEqual(html.count('data-page="bloggerskill"'), 1)
        self.assertNotIn('data-page="creatorassets">达人蒸馏与档案', html)
        self.assertIn("博主蒸馏孵化", html)
        self.assertIn("createBloggerCreatorTask", app)
        self.assertIn("pollBloggerCreatorTask", app)
        self.assertIn('role="progressbar"', app)
        self.assertIn("data-blogger-task-retry", app)
        self.assertIn("error_message||task.degraded_reason", app)
        self.assertIn('api("/api/creator-distillation/tasks"', app)
        self.assertIn("未经人工确认的 DNA 不作为最终孵化结论", app)
        self.assertIn("导入公开数据（主来源）", html)
        self.assertIn("补充采集（可选）", html)
        self.assertIn("不覆盖主证据", html)
        self.assertIn("账号补充采集任务", app)
        self.assertIn("公开主证据 · 能力卡生成任务", app)
        self.assertIn("BLOGGER_IMPORT_PHASES", app)
        self.assertIn("/api/blogger-skill/import-jobs/", app)
        self.assertIn("data-blogger-import-retry", app)
        self.assertIn('role="progressbar"', app)
        self.assertNotIn("社媒助手主采集", html)
        self.assertNotIn("TikHub 补充采集", html)
        self.assertNotIn("Qwen + DeepSeek 共同证据质检通过", app)

    def test_blogger_workbench_visual_scope_survives_content_view_mount(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        style = (ROOT / "style.css").read_text(encoding="utf-8")

        self.assertIn('id="content-blogger-distill-view"', html)
        self.assertIn('class="blogger-value-chain"', html)
        self.assertIn("#content-blogger-distill-view .founder-hero", style)
        self.assertIn("#content-blogger-distill-view .data-kpis", style)
        self.assertNotIn("#bloggerskill .data-kpis", style)

    def test_shared_content_route_keeps_blogger_navigation_identity(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")

        self.assertIn("const requestedId=id", app)
        self.assertIn("b.dataset.page===requestedId", app)
        self.assertIn("pageNames[requestedId]||pageNames[id]", app)


if __name__ == "__main__":
    unittest.main()
