import io
import sqlite3
import tempfile
import unittest
import zipfile
from pathlib import Path

from docx import Document

from bf_factory.exporters import export_brief_docx
from bf_factory.generation import compose_section_plan, generate_internal_strategy, render_adaptive_brief
from bf_factory.repository import BFRepository
from bf_factory.schema import new_brief_payload
from bf_factory.service import BFService


class BFExportTest(unittest.TestCase):
    def setUp(self):
        self.payload = new_brief_payload("project-1", "client-a", "source.docx")
        self.payload["classification"].update(
            {
                "bfType": "CUSTOM",
                "bfTypeLabel": "女性体验+竞品对比商业化内容BF",
                "confidence": 0.8,
                "reasons": ["混合内容意图"],
                "contentIntents": ["FEMALE_EXPERIENCE", "COMPETITOR_COMPARISON"],
            }
        )
        self.payload["strategy"].update(
            {
                "bfName": "智己L6车展体验BF",
                "bfType": "CUSTOM",
                "brand": "智己",
                "model": "智己L6",
                "competitors": ["小米SU7"],
                "projectStage": "车展期",
                "communicationGoals": ["种草"],
                "targetAudience": ["年轻女性用户"],
            }
        )
        self.payload["product"]["coreSellingPoints"] = ["灵蜥数字底盘"]
        self.payload["risk"]["prohibitedExpressions"] = ["不得使用第一、唯一、绝对安全"]
        self.payload["provenance"]["/product/coreSellingPoints"] = [
            {
                "originType": "EXTRACTED",
                "sourceDocumentId": "doc-1",
                "sourceSegmentId": "seg-3",
                "sourceLocator": "第3页",
                "sourceFieldPath": "",
                "excerpt": "灵蜥数字底盘",
                "confidence": 0.9,
                "isManual": False,
            }
        ]
        strategy = generate_internal_strategy(self.payload, [])
        self.rendered = render_adaptive_brief(self.payload, strategy, compose_section_plan(self.payload))

    def test_docx_export_has_business_brief_structure_sources_and_scrubbed_metadata(self):
        data = export_brief_docx(
            payload=self.payload,
            sections=self.rendered["sections"],
            include_internal=False,
        )
        self.assertTrue(data.startswith(b"PK"))
        document = Document(io.BytesIO(data))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        self.assertIn("智己L6车展体验BF", text)
        self.assertIn("女性用户体验任务", text)
        self.assertIn("来源与策略推断说明", text)
        self.assertIn("第3页", text)
        self.assertNotIn("仅供MMN内部策略判断", text)
        self.assertFalse(document.core_properties.author)
        self.assertFalse(document.core_properties.last_modified_by)
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            self.assertNotIn("docProps/custom.xml", archive.namelist())

    def test_final_version_returns_to_asset_library_and_learns_custom_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "bf.sqlite3"

            def connect():
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                return conn

            repo = BFRepository(connect)
            repo.init_schema()
            project = repo.create_project(
                org_id="org-1",
                edition="china",
                client_key="client-a",
                name="项目",
                brand="智己",
                model="智己L6",
                created_by="user-1",
            )
            self.payload["document"]["projectId"] = project["id"]
            brief = repo.create_brief(
                project_id=project["id"],
                origin_type="GENERATED",
                bf_type="CUSTOM",
                title=self.payload["strategy"]["bfName"],
                structured_payload=self.payload,
                created_by="user-1",
            )
            service = BFService(repo, Path(tmp) / "files")
            result = service.finalize_brief(
                brief_id=brief["id"],
                project_id=project["id"],
                base_version_no=1,
                payload=self.payload,
                markdown=self.rendered["markdown"],
                sample_grade="QUALITY",
                user_id="user-1",
                outcome={"isCustomerAdopted": True, "isCommercialUsed": True, "needsReshoot": False, "passedReview": True},
                learned_profile_name="智己L6 client-a 车展女性体验竞品BF",
            )
            self.assertTrue(result["version"]["is_final"])
            self.assertEqual(result["brief"]["sample_grade"], "QUALITY")
            self.assertGreater(result["knowledgeChunkCount"], 0)
            learned = repo.get_template_profile(result["learnedProfile"]["code"])
            self.assertIn("FEMALE_EXPERIENCE", learned["section_intents"])
            self.assertNotIn("智己", learned["name"])
            self.assertNotIn("client-a", learned["name"])

            second_project = repo.create_project(
                org_id="org-2",
                edition="china",
                client_key="client-b",
                name="另一客户项目",
                brand="另一品牌",
                model="车型B",
                created_by="user-2",
            )
            reused = service.generate_brief(
                {
                    "projectId": second_project["id"],
                    "orgId": "org-2",
                    "clientKey": "client-b",
                    "userId": "user-2",
                    "brand": "另一品牌",
                    "model": "车型B",
                    "bfType": "CUSTOM",
                    "contentDirections": ["女性体验", "竞品同场景对比"],
                }
            )
            self.assertEqual(reused["learnedProfile"]["code"], learned["code"])
            self.assertTrue(any(item["origin"] == "LEARNED_PROFILE" for item in reused["sectionPlan"]))


if __name__ == "__main__":
    unittest.main()
