import http.client
import re
import threading
import unittest
from pathlib import Path

import server


ROOT = Path(__file__).resolve().parents[1]


class StaticFileBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.Server(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.host, cls.port = cls.httpd.server_address

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)

    def request(self, method, path):
        connection = http.client.HTTPConnection(self.host, self.port, timeout=3)
        try:
            connection.request(method, path)
            response = connection.getresponse()
            body = response.read(4096)
            return response.status, dict(response.getheaders()), body
        finally:
            connection.close()

    def test_public_application_assets_remain_available(self):
        for path in (
            "/",
            "/index.html",
            "/app.js?v=release",
            "/style.css",
            "/assets/favicon.svg",
            "/demo-brand-weekly-radar.html",
        ):
            with self.subTest(path=path):
                status, headers, _ = self.request("HEAD", path)
                self.assertEqual(200, status)
                self.assertEqual("nosniff", headers.get("X-Content-Type-Options"))
                self.assertEqual("SAMEORIGIN", headers.get("X-Frame-Options"))

    def test_index_references_only_explicitly_allowlisted_local_assets(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        references = re.findall(r'(?:src|href)="([^"]+)"', index)
        local_assets = {
            reference.split("?", 1)[0]
            for reference in references
            if not reference.startswith(("#", "data:", "http://", "https://"))
        }
        self.assertTrue(local_assets)
        self.assertEqual(set(), local_assets - server.PUBLIC_STATIC_FILES)

    def test_sensitive_project_files_and_directories_are_not_served(self):
        for path in (
            "/server.py",
            "/docker-compose.yml",
            "/.env",
            "/data/",
            "/data/commercial_demo.db",
            "/backups/",
            "/logs/",
            "/docs/",
            "/requirements-bf-factory.txt",
        ):
            with self.subTest(path=path):
                status, _, body = self.request("GET", path)
                self.assertEqual(404, status)
                self.assertNotIn(b"Directory listing", body)

    def test_encoded_and_traversal_variants_cannot_bypass_the_boundary(self):
        for path in (
            "/%73erver.py",
            "/data%2Fcommercial_demo.db",
            "/assets/../server.py",
            "/%2e%2e/server.py",
            "/logs%252Fscheduler.log",
        ):
            with self.subTest(path=path):
                status, _, _ = self.request("HEAD", path)
                self.assertEqual(404, status)

    def test_api_requests_still_reach_the_application_router(self):
        status, headers, _ = self.request("GET", "/api/health")
        self.assertEqual(200, status)
        self.assertIn("application/json", headers.get("Content-Type", ""))
        self.assertEqual("nosniff", headers.get("X-Content-Type-Options"))


if __name__ == "__main__":
    unittest.main()
