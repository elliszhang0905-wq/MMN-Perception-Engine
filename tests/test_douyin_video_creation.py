import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import server
from douyin_video_creation import (
    create_plan,
    get_plan,
    init_schema,
    list_plans,
    normalize_result,
)
from douyin_video_insights import (
    build_evidence_package,
    create_job as create_insight_job,
    update_job as update_insight_job,
)


ITEM = {
    "itemId": "7650000000000000099",
    "title": "连续弯挑战为什么让人想看完",
    "author": "测试作者",
    "tags": ["底盘", "连续弯"],
    "sourceUrl": "https://www.douyin.com/video/7650000000000000099",
    "mediaUrl": "https://media.example/video.mp4",
    "playCount": 810000,
    "likeCount": 24000,
    "commentCount": 1900,
    "shareCount": 2100,
    "collectCount": 1700,
    "duration": 31,
}

MEDIA = [
    {
        "evidence_type": "transcript",
        "start_ms": 200,
        "quote_text": "先别看参数，连续三个弯以后再下结论",
        "source_scope": "video_body",
    },
    {
        "evidence_type": "shot",
        "start_ms": 3200,
        "quote_text": "车辆连续通过两个方向相反的弯道",
        "source_scope": "video_body",
    },
]


def insight_result(package):
    refs = [row["evidenceId"] for row in package["evidenceRefs"]]
    return {
        "validation": {
            "status": "verified",
            "reason": "三路独立分析在关键机制上形成一致判断。",
            "finalInsight": {
                "contentSummary": "视频先提出连续弯挑战，再用连续画面验证车身姿态。",
                "openingHook": "先否定只看参数，再承诺用连续弯给出结论。",
                "narrativeStructure": "提出争议—连续挑战—回看证据—邀请讨论。",
                "emotionDrivers": ["验证欲", "驾驶代入"],
                "viralMechanisms": ["悬念验证", "可争论的连续画面"],
                "primaryMechanism": "悬念验证",
                "brandAndModelRoles": ["车型是被验证对象"],
                "primaryBrandRole": "被验证对象",
                "audienceResponse": "评论集中讨论镜头是否加速。",
                "marketingImplications": ["保留连续画面证明过程"],
                "reusablePatterns": ["问题先行，再用连续动作给证据"],
                "copyRisks": ["不能把播放热度写成产品能力证明"],
                "confidence": 0.86,
                "evidenceCoverage": "full",
                "evidenceRefs": {
                    "contentSummary": refs[:2],
                    "viralMechanisms": refs[:2],
                },
                "limitations": [],
            },
            "runs": [],
            "disagreements": [],
        }
    }


def direction(index, evidence_id):
    return {
        "id": f"direction-{index}",
        "title": f"方向{index}：家庭连续弯体验",
        "coreIdea": "用家庭乘员体感代替参数堆砌。",
        "openingHook": "先提出一个用户在连续弯中能感知的问题。",
        "structureSteps": [
            {"timing": "0-3秒", "purpose": "提出冲突", "content": "参数好不等于家人坐得稳。"},
            {"timing": "4-20秒", "purpose": "连续验证", "content": "保持连续镜头展示乘员与车辆状态。"},
            {"timing": "21-35秒", "purpose": "给出边界", "content": "提示到店按同一路线自行验证。"},
        ],
        "productIntegration": "把目标车型作为待验证对象，不预设能力成立。",
        "emotionTrigger": "家庭责任感与验证欲。",
        "visualSuggestions": ["乘员上车", "连续弯不切镜", "结束后复盘"],
        "endingInteraction": "你更在意驾驶感还是家人的乘坐感？",
        "transferNotes": ["迁移悬念验证结构", "保留连续证据镜头"],
        "copyRisks": ["不复制原视频文案", "不把创意简报写成车型事实"],
        "evidenceRefs": [evidence_id],
    }


def fake_creation_runner(stage, messages):
    payload = json.loads(messages[-1]["content"])
    evidence_id = payload["evidenceRefs"][0]["evidenceId"]
    if stage == "draft":
        return {"directions": [direction(index, evidence_id) for index in range(1, 4)]}
    if stage == "review":
        return {
            "verdict": "pass",
            "issues": [],
            "factualRisks": [],
            "copyRisks": [],
            "revisionInstructions": [],
        }
    return {
        "directions": [direction(index, evidence_id) for index in range(1, 4)],
        "qualityNote": "已完成证据、原创性与可拍摄性复核。",
        "limitations": ["创作方向不构成传播结果承诺。"],
    }


class DouyinVideoCreationContractTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_patch = patch.object(server, "DB_PATH", Path(self.temp.name) / "video-creation.db")
        self.db_patch.start()
        server.init_db()
        self.package = build_evidence_package(
            ITEM,
            media=MEDIA,
            comments=[{"id": "c1", "text": "这个连续镜头有没有加速"}],
        )
        with server.db() as conn:
            self.insight_job, _ = create_insight_job(
                conn,
                org_id="org-a",
                edition="china",
                view="videos",
                range_key="24h",
                item=ITEM,
            )
            update_insight_job(
                conn,
                self.insight_job["jobId"],
                status="completed",
                evidence=self.package,
                result=insight_result(self.package),
            )

    def tearDown(self):
        self.db_patch.stop()
        self.temp.cleanup()

    def brief(self, **overrides):
        return {
            "insightJobId": self.insight_job["jobId"],
            "brand": "上汽奥迪",
            "model": "奥迪E7X",
            "audience": "关注家庭乘坐体验的增换购用户",
            "marketingTask": "建立连续弯场景中的产品验证方法",
            "productBenefit": "家庭成员能感知的乘坐稳定性，需要拍摄补证",
            "style": "真实、克制、可拍摄",
            **overrides,
        }

    def test_normalizer_requires_three_directions_and_current_evidence(self):
        evidence_id = self.package["evidenceRefs"][0]["evidenceId"]
        with self.assertRaises(ValueError):
            normalize_result({"directions": [direction(1, evidence_id)]}, self.package)
        invalid = [direction(index, "V:other-video") for index in range(1, 4)]
        with self.assertRaises(ValueError):
            normalize_result({"directions": invalid}, self.package)
        result = normalize_result(
            {
                "directions": [direction(index, evidence_id) for index in range(1, 4)],
                "qualityNote": "完成",
                "limitations": ["不承诺传播结果"],
            },
            self.package,
        )
        self.assertEqual(len(result["directions"]), 3)
        self.assertTrue(all(len(row["structureSteps"]) >= 3 for row in result["directions"]))

    def test_plan_cache_is_scoped_and_brief_changes_create_new_asset(self):
        with server.db() as conn:
            init_schema(conn)
            first, created = create_plan(
                conn,
                org_id="org-a",
                edition="china",
                insight_job=self.insight_job,
                request=self.brief(),
            )
            cached, recreated = create_plan(
                conn,
                org_id="org-a",
                edition="china",
                insight_job=self.insight_job,
                request=self.brief(),
            )
            changed, changed_created = create_plan(
                conn,
                org_id="org-a",
                edition="china",
                insight_job=self.insight_job,
                request=self.brief(audience="年轻性能用户"),
            )
            other_org, other_created = create_plan(
                conn,
                org_id="org-b",
                edition="china",
                insight_job=self.insight_job,
                request=self.brief(),
            )
            rows = list_plans(conn, org_id="org-a", edition="china")
        self.assertTrue(created)
        self.assertFalse(recreated)
        self.assertEqual(first["id"], cached["id"])
        self.assertTrue(cached["cacheHit"])
        self.assertTrue(changed_created and other_created)
        self.assertNotEqual(changed["id"], other_org["id"])
        self.assertEqual(len(rows), 2)

    def test_schema_upgrade_preserves_older_creation_assets(self):
        legacy = sqlite3.connect(":memory:")
        legacy.row_factory = sqlite3.Row
        legacy.execute(
            """
            create table douyin_video_creation_plans (
              id text primary key,
              org_id text not null,
              edition text not null,
              insight_job_id text not null,
              item_id text not null,
              brief_fingerprint text not null,
              prompt_version text not null,
              schema_version text not null,
              request_json text not null default '{}',
              status text not null,
              stage text not null,
              progress integer not null default 0,
              message text not null default '',
              error text not null default '',
              retryable integer not null default 0,
              result_json text not null default '{}',
              review_json text not null default '{}',
              selected_direction_id text not null default '',
              script_job_id text not null default '',
              created_at text not null,
              updated_at text not null,
              completed_at text
            )
            """
        )
        init_schema(legacy)
        columns = {
            row["name"]
            for row in legacy.execute(
                "pragma table_info(douyin_video_creation_plans)"
            ).fetchall()
        }
        legacy.close()
        self.assertIn("source_json", columns)
        self.assertIn("favorite", columns)

    def test_server_blocks_unverified_or_limited_insight(self):
        with server.db() as conn:
            update_insight_job(
                conn,
                self.insight_job["jobId"],
                status="limited_analysis",
                evidence=self.package,
                result={
                    "validation": {
                        **insight_result(self.package)["validation"],
                        "status": "limited_analysis",
                    }
                },
            )
        with self.assertRaisesRegex(ValueError, "证据"):
            server.create_video_creation_plan(
                self.brief(),
                org_id="org-a",
                start_worker=False,
            )

    def test_server_persists_three_direction_result_and_cache(self):
        plan = server.create_video_creation_plan(
            self.brief(),
            org_id="org-a",
            start_worker=False,
        )
        completed = server.run_video_creation_plan(plan["id"], runner=fake_creation_runner)
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["progress"], 100)
        self.assertEqual(len(completed["result"]["directions"]), 3)
        cached = server.create_video_creation_plan(
            self.brief(),
            org_id="org-a",
            start_worker=False,
        )
        self.assertEqual(cached["id"], plan["id"])
        self.assertTrue(cached["cacheHit"])
        with server.db() as conn:
            persisted = get_plan(conn, plan["id"], "org-a")
        self.assertEqual(persisted["result"]["qualityNote"], "已完成证据、原创性与可拍摄性复核。")
        favorite = server.set_video_creation_favorite(
            plan["id"], True, org_id="org-a"
        )
        self.assertTrue(favorite["favorite"])
        with server.db() as conn:
            self.assertTrue(get_plan(conn, plan["id"], "org-a")["favorite"])

    def test_external_video_link_creates_manual_insight_without_ranking_row(self):
        item = server.resolve_external_douyin_video_item(
            "https://www.douyin.com/video/7650000000000000098?previous_page=web_code_link"
        )
        self.assertEqual(item["itemId"], "7650000000000000098")
        self.assertEqual(
            item["sourceUrl"],
            "https://www.douyin.com/video/7650000000000000098",
        )
        with self.assertRaises(ValueError):
            server.resolve_external_douyin_video_item(
                "https://www.douyin.com/user/SEC-USER"
            )
        with self.assertRaises(Exception):
            server.resolve_external_douyin_video_item(
                "https://example.com/video/7650000000000000098"
            )
        job = server.start_external_video_insight_job(
            {
                "edition": "china",
                "sourceUrl": item["sourceUrl"],
            },
            org_id="org-a",
            start_worker=False,
        )
        self.assertEqual(job["range"], "external")
        self.assertEqual(job["itemId"], item["itemId"])

    def test_selected_direction_hands_source_context_to_script_job(self):
        plan = server.create_video_creation_plan(
            self.brief(),
            org_id="org-a",
            start_worker=False,
        )
        completed = server.run_video_creation_plan(plan["id"], runner=fake_creation_runner)
        with patch.object(
            server,
            "create_creator_script_job",
            return_value={"id": "creator_script_linked", "status": "queued"},
        ) as create_script:
            linked = server.create_script_from_video_creation_plan(
                completed["id"],
                {
                    "directionId": "direction-1",
                    "creatorAssetId": "creator-dna-1",
                    "platform": "douyin",
                },
                org_id="org-a",
                start_worker=False,
            )
        forwarded = create_script.call_args.args[0]
        self.assertEqual(forwarded["brand"], "上汽奥迪")
        self.assertEqual(forwarded["model"], "奥迪E7X")
        self.assertEqual(forwarded["creatorAssetId"], "creator-dna-1")
        self.assertIn("连续验证", forwarded["sourceContext"])
        self.assertEqual(linked["scriptJobId"], "creator_script_linked")

    def test_frontend_exposes_ranking_trigger_library_and_script_handoff(self):
        root = Path(__file__).resolve().parents[1]
        app = (root / "douyin-hot-demo.js").read_text(encoding="utf-8")
        css = (root / "douyin-hot-demo.css").read_text(encoding="utf-8")
        for phrase in (
            "按此结构生成创作方向",
            "爆款内容拆解库",
            "目标人群",
            "营销任务",
            "核心产品利益点",
            "继续生成完整脚本",
            "只迁移结构和机制",
            "分析排行榜外的视频",
            "结构对比",
            "仅看收藏",
        ):
            self.assertIn(phrase, app)
        for token in (
            "data-creation-plan-open",
            "data-creation-library",
            "data-creation-script",
            "/api/douyin-hot/creation-plans",
        ):
            self.assertIn(token, app)
        self.assertIn(".douyin-creation-dialog", css)
        self.assertIn(".douyin-creation-library", css)
        self.assertRegex(css, r"@media\s*\(max-width:\s*640px\)")


if __name__ == "__main__":
    unittest.main()
