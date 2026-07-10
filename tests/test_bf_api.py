import json
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import server


class BFAPITest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.old_data_dir = server.DATA_DIR
        cls.old_db_path = server.DB_PATH
        cls.old_cloud = server.CLOUD_LOGIN_REQUIRED
        cls.old_bf_models = getattr(server, "BF_MODELS_ENABLED", None)
        server.DATA_DIR = Path(cls.tmp.name) / "data"
        server.DB_PATH = server.DATA_DIR / "test.sqlite3"
        server.CLOUD_LOGIN_REQUIRED = False
        server.BF_MODELS_ENABLED = False
        server.init_db()
        cls.httpd = server.Server(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.httpd.server_address[1]}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=3)
        server.DATA_DIR = cls.old_data_dir
        server.DB_PATH = cls.old_db_path
        server.CLOUD_LOGIN_REQUIRED = cls.old_cloud
        if cls.old_bf_models is not None:
            server.BF_MODELS_ENABLED = cls.old_bf_models
        cls.tmp.cleanup()

    def request_json(self, method, path, payload=None, raw=None, content_type="application/json"):
        data = raw if raw is not None else (json.dumps(payload or {}, ensure_ascii=False).encode("utf-8") if method != "GET" else None)
        request = Request(self.base + path, data=data, method=method, headers={"Content-Type": content_type})
        with urlopen(request, timeout=10) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_full_http_flow_upload_generate_edit_finalize_and_export(self):
        status, project_result = self.request_json(
            "POST",
            "/api/bf/projects",
            {
                "orgId": "org-api",
                "edition": "china",
                "clientKey": "client-api",
                "name": "API车展项目",
                "brand": "智己",
                "model": "智己L6",
                "userId": "user-api",
            },
        )
        self.assertEqual(status, 201)
        project = project_result["data"]

        query = urlencode(
            {
                "projectId": project["id"],
                "orgId": "org-api",
                "clientKey": "client-api",
                "userId": "user-api",
                "filename": "客户BF.txt",
            }
        )
        status, upload = self.request_json(
            "POST",
            f"/api/bf/documents?{query}",
            raw="BF名称：智己L6车展BF\n品牌：智己\n车型：智己L6\n内容方向：女性体验\n禁止表达：不得使用唯一".encode("utf-8"),
            content_type="text/plain",
        )
        self.assertEqual(status, 201)
        self.assertEqual(upload["data"]["payload"]["strategy"]["brand"], "智己")

        status, generated = self.request_json(
            "POST",
            "/api/bf/generations",
            {
                "projectId": project["id"],
                "orgId": "org-api",
                "clientKey": "client-api",
                "userId": "user-api",
                "brand": "智己",
                "model": "智己L6",
                "bfType": "CUSTOM",
                "contentDirections": ["女性体验", "竞品同场景对比", "动态素材采集"],
            },
        )
        self.assertEqual(status, 201)
        brief_id = generated["data"]["brief"]["id"]
        payload = generated["data"]["payload"]
        markdown = generated["data"]["markdown"]
        self.assertIn("女性用户体验任务", markdown)

        status, finalized = self.request_json(
            "POST",
            f"/api/bf/briefs/{brief_id}/finalizations",
            {
                "projectId": project["id"],
                "baseVersionNo": 1,
                "payload": payload,
                "markdown": markdown,
                "sampleGrade": "QUALITY",
                "userId": "user-api",
                "outcome": {"isCustomerAdopted": True, "passedReview": True},
                "learnedProfileName": "车展女性体验竞品BF",
            },
        )
        self.assertEqual(status, 201)
        self.assertGreater(finalized["data"]["knowledgeChunkCount"], 0)

        status, chunks = self.request_json(
            "GET",
            "/api/bf/knowledge-chunks?" + urlencode({"projectId": project["id"], "orgId": "org-api", "assetType": "METHOD"}),
        )
        self.assertEqual(status, 200)
        self.assertGreater(len(chunks["data"]), 0)
        self.assertTrue(all(item["asset_type"] == "METHOD" for item in chunks["data"]))

        export_request = Request(
            self.base + f"/api/bf/briefs/{brief_id}/exports",
            data=json.dumps({"projectId": project["id"], "format": "DOCX", "includeInternal": False}).encode("utf-8"),
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        with urlopen(export_request, timeout=10) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers.get_content_type(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            self.assertTrue(response.read().startswith(b"PK"))

    def test_cross_project_document_listing_is_rejected(self):
        _, first = self.request_json(
            "POST",
            "/api/bf/projects",
            {"orgId": "org-isolation", "clientKey": "client-a", "name": "A", "userId": "u"},
        )
        query = urlencode({"projectId": first["data"]["id"], "orgId": "other-org"})
        with self.assertRaises(HTTPError) as error:
            self.request_json("GET", f"/api/bf/documents?{query}")
        self.assertEqual(error.exception.code, 403)

    def test_structured_brief_json_schema_is_available_to_editor_clients(self):
        status, result = self.request_json("GET", "/api/bf/schema")
        self.assertEqual(status, 200)
        schema = result["data"]
        self.assertEqual(schema["properties"]["schemaVersion"]["const"], "1.0.0")
        self.assertTrue({"strategy", "product", "content", "execution", "risk", "materials"}.issubset(schema["required"]))
        _, profiles = self.request_json("GET", "/api/bf/template-profiles")
        self.assertTrue(profiles["data"])
        self.assertTrue(all("created_by" not in item for item in profiles["data"]))


if __name__ == "__main__":
    unittest.main()
