import sqlite3
import tempfile
import unittest
import json
from pathlib import Path

from bf_factory.repository import BFRepository
from bf_factory.service import BFService


class BFServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "bf.sqlite3"

        def connect():
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn

        self.repo = BFRepository(connect)
        self.repo.init_schema()
        self.project = self.repo.create_project(
            org_id="org-1",
            edition="china",
            client_key="client-a",
            name="车展项目",
            brand="智己",
            model="智己L6",
            created_by="user-1",
        )
        self.service = BFService(self.repo, Path(self.tmp.name) / "files")

    def tearDown(self):
        self.tmp.cleanup()

    def test_upload_parse_extract_and_persist_is_one_traceable_flow(self):
        data = (
            "BF名称：智己L6探店BF\n品牌：智己\n车型：智己L6\n"
            "项目阶段：车展期\n内容方向：女性第一视角体验\n"
            "禁止表达：不得使用唯一、第一"
        ).encode("utf-8")
        result = self.service.ingest_document(
            project_id=self.project["id"],
            org_id="org-1",
            client_key="client-a",
            filename="客户brief.txt",
            data=data,
            user_id="user-1",
        )

        self.assertEqual(result["document"]["parse_status"], "STRUCTURED")
        self.assertEqual(result["brief"]["project_id"], self.project["id"])
        self.assertEqual(result["payload"]["strategy"]["brand"], "智己")
        self.assertGreater(len(self.repo.list_segments(result["document"]["id"], self.project["id"])), 2)

    def test_generation_uses_deepseek_qwen_deepseek_but_keeps_validated_structure(self):
        calls = []

        def gateway(provider, step, request):
            calls.append((provider, step))
            if step == "STRATEGY_JUDGMENT":
                return '{"bestAngle":"用女性真实体验建立底盘价值证据"}'
            if step == "DRAFT":
                return '{"sectionBodies":{"FEMALE_EXPERIENCE":"- 从通勤、停车和上下车体验展开"}}'
            return '{"verdict":"pass","findings":[]}'

        service = BFService(self.repo, Path(self.tmp.name) / "files", model_gateway=gateway)
        result = service.generate_brief(
            {
                "projectId": self.project["id"],
                "orgId": "org-1",
                "clientKey": "client-a",
                "userId": "user-1",
                "brand": "智己",
                "model": "智己L6",
                "competitors": ["小米SU7"],
                "projectStage": "车展期",
                "communicationGoals": ["种草"],
                "bfType": "CUSTOM",
                "contentDirections": ["女性体验", "竞品同场景对比", "动态素材采集"],
                "creatorTypes": ["女性生活方式"],
                "specialRequirements": "避免刻板标签，评论区讨论真实使用问题",
            }
        )

        self.assertEqual(
            calls,
            [
                ("DEEPSEEK", "STRATEGY_JUDGMENT"),
                ("QWEN", "DRAFT"),
                ("DEEPSEEK", "RISK_REVIEW"),
            ],
        )
        self.assertEqual(result["review"]["verdict"], "pass")
        self.assertIn("从通勤、停车和上下车体验展开", result["markdown"])
        self.assertIn("/strategy/brand", result["payload"]["provenance"])
        self.assertEqual(result["brief"]["bf_type"], "CUSTOM")

    def test_generation_without_model_configuration_degrades_to_editable_mmn_output(self):
        result = self.service.generate_brief(
            {
                "projectId": self.project["id"],
                "orgId": "org-1",
                "clientKey": "client-a",
                "userId": "user-1",
                "brand": "智己",
                "model": "智己L6",
                "bfType": "STORE_VISIT",
                "contentDirections": ["探店", "静态体验"],
            }
        )
        self.assertEqual(result["status"], "EDITABLE_DEGRADED")
        self.assertIn("探店脚本框架", result["markdown"])

    def test_external_model_redaction_is_default_on_and_can_be_explicitly_disabled(self):
        captured = []

        def gateway(provider, step, request):
            captured.append(json.dumps(request, ensure_ascii=False))
            if step == "RISK_REVIEW":
                return '{"verdict":"pass","findings":[]}'
            return "{}"

        service = BFService(self.repo, Path(self.tmp.name) / "files", model_gateway=gateway)
        base = {
            "projectId": self.project["id"],
            "orgId": "org-1",
            "clientKey": "client-a",
            "userId": "user-1",
            "brand": "未公开客户甲",
            "model": "未公开车型X",
            "competitors": ["竞品Y"],
            "budget": "内部价格30万元",
            "bfType": "CUSTOM",
            "contentDirections": ["女性体验"],
            "specialRequirements": "联系人13800138000，网盘https://pan.baidu.com/s/secret，提取码a1b2",
        }
        service.generate_brief(dict(base))
        default_payload = "\n".join(captured)
        for secret in ("未公开客户甲", "未公开车型X", "竞品Y", "30万元", "13800138000", "pan.baidu.com", "a1b2"):
            self.assertNotIn(secret, default_payload)

        captured.clear()
        service.generate_brief({**base, "redactBeforeExternal": False})
        self.assertIn("未公开客户甲", "\n".join(captured))


if __name__ == "__main__":
    unittest.main()
