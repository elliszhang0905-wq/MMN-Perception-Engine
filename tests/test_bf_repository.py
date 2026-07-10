import sqlite3
import tempfile
import unittest
from pathlib import Path

from bf_factory.repository import (
    BFConflictError,
    BFPermissionError,
    BFRepository,
)
from bf_factory.schema import new_brief_payload, validate_brief_payload


class BFRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "bf-test.sqlite3"

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
            name="A项目",
            brand="智己",
            model="智己L6",
            created_by="user-1",
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_project_scope_blocks_cross_project_document_access(self):
        document = self.repo.create_document(
            project_id=self.project["id"],
            org_id="org-1",
            filename="客户BF.docx",
            extension=".docx",
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            sha256="a" * 64,
            storage_path="/private/document.docx",
            size_bytes=128,
            uploaded_by="user-1",
        )
        other = self.repo.create_project(
            org_id="org-1",
            edition="china",
            client_key="client-b",
            name="B项目",
            brand="别克",
            model="GL8",
            created_by="user-1",
        )

        self.assertEqual(
            self.repo.get_document(document["id"], self.project["id"], "org-1")["filename"],
            "客户BF.docx",
        )
        with self.assertRaises(BFPermissionError):
            self.repo.get_document(document["id"], other["id"], "org-1")

    def test_version_write_rejects_stale_base_version(self):
        payload = new_brief_payload(
            project_id=self.project["id"],
            client_key="client-a",
            file_name="generated.json",
        )
        payload["strategy"].update({"bfName": "智己L6探店BF", "brand": "智己", "model": "智己L6"})
        validate_brief_payload(payload)
        brief = self.repo.create_brief(
            project_id=self.project["id"],
            origin_type="GENERATED",
            bf_type="STORE_VISIT",
            title="智己L6探店BF",
            structured_payload=payload,
            created_by="user-1",
        )

        version = self.repo.save_brief_version(
            brief_id=brief["id"],
            project_id=self.project["id"],
            structured_payload=payload,
            rendered_markdown="# V2",
            version_kind="MANUAL",
            base_version_no=1,
            created_by="user-1",
        )
        self.assertEqual(version["version_no"], 2)

        with self.assertRaises(BFConflictError):
            self.repo.save_brief_version(
                brief_id=brief["id"],
                project_id=self.project["id"],
                structured_payload=payload,
                rendered_markdown="# stale",
                version_kind="MANUAL",
                base_version_no=1,
                created_by="user-1",
            )

    def test_retrieval_policy_separates_positive_risk_and_disabled_samples(self):
        ids = {}
        for grade in ("QUALITY", "NORMAL", "NEGATIVE", "DISABLED"):
            payload = new_brief_payload(
                project_id=self.project["id"],
                client_key="client-a",
                file_name=f"{grade}.txt",
            )
            payload["strategy"].update({"bfName": grade, "brand": "智己", "model": "智己L6"})
            brief = self.repo.create_brief(
                project_id=self.project["id"],
                origin_type="UPLOADED",
                bf_type="STORE_VISIT",
                title=grade,
                structured_payload=payload,
                created_by="user-1",
                sample_grade=grade,
            )
            ids[grade] = brief["id"]

        positive = self.repo.list_retrieval_candidates(self.project["id"], purpose="POSITIVE")
        risk = self.repo.list_retrieval_candidates(self.project["id"], purpose="RISK")

        self.assertEqual([row["id"] for row in positive], [ids["QUALITY"], ids["NORMAL"]])
        self.assertEqual([row["id"] for row in risk], [ids["NEGATIVE"]])
        self.assertNotIn(ids["DISABLED"], {row["id"] for row in positive + risk})

    def test_schema_requires_all_six_structured_layers(self):
        payload = new_brief_payload(
            project_id=self.project["id"],
            client_key="client-a",
            file_name="sample.pdf",
        )
        validate_brief_payload(payload)
        del payload["risk"]
        with self.assertRaises(ValueError):
            validate_brief_payload(payload)

    def test_template_profiles_are_open_and_can_learn_new_brief_shapes(self):
        profile = self.repo.save_template_profile(
            code="AUTO_SHOW_LIFESTYLE_COMPARE",
            name="车展生活方式竞品体验BF",
            section_intents=[
                "PROJECT_BACKGROUND",
                "FEMALE_EXPERIENCE",
                "COMPETITOR_COMPARISON",
                "DYNAMIC_MATERIAL_CAPTURE",
                "RISK_CONTROL",
            ],
            source="HUMAN_CONFIRMED",
            created_by="user-1",
        )

        loaded = self.repo.get_template_profile(profile["code"])
        self.assertEqual(loaded["name"], "车展生活方式竞品体验BF")
        self.assertEqual(loaded["section_intents"][1], "FEMALE_EXPERIENCE")
        self.assertNotEqual(loaded["code"], "STORE_VISIT")


if __name__ == "__main__":
    unittest.main()
