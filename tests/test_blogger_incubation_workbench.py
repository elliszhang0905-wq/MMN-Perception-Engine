import unittest
from pathlib import Path
from unittest.mock import patch

import server


ROOT = Path(__file__).resolve().parents[1]


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
