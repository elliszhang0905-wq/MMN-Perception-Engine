import json
import tempfile
import unittest
from pathlib import Path

import server


class OpportunityDocumentRestoreTest(unittest.TestCase):
    def setUp(self):
        self.original_db_path = server.DB_PATH
        self.tempdir = tempfile.TemporaryDirectory()
        server.DB_PATH = Path(self.tempdir.name) / "restore.db"
        server.init_db()

    def tearDown(self):
        server.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def test_latest_document_returns_compact_metadata_for_reload(self):
        payload = {
            "documentId": "doc-new",
            "filename": "AUDI E7X 产品白皮书.pdf",
            "brand": "奥迪",
            "model": "奥迪E7X",
            "version": "V260410",
            "facts": [{"id": "f1"}, {"id": "f2"}, {"id": "f3"}],
            "manualReviewItems": [{"label": "版本"}, {"label": "标签"}],
        }
        with server.db() as conn:
            conn.execute(
                """insert into product_fact_documents
                (id, org_id, user_id, edition, brand, model, version, filename, sha256, storage_path, payload_json, created_at)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                ("doc-new", "local", "tester", "china", "奥迪", "奥迪E7X", "V260410", payload["filename"], "sha", "", json.dumps(payload, ensure_ascii=False), "2026-07-11T02:38:31Z"),
            )

        restored = server.latest_opportunity_product_document("china", "奥迪E7X")

        self.assertEqual(restored, {
            "documentId": "doc-new",
            "filename": "AUDI E7X 产品白皮书.pdf",
            "brand": "奥迪",
            "model": "奥迪E7X",
            "version": "V260410",
            "factCount": 3,
            "manualReviewCount": 2,
        })


if __name__ == "__main__":
    unittest.main()
