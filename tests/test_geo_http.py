import json
from pathlib import Path
import secrets
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib import request, error

import server
from geo.repository import GeoRepository


class GeoHttpTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.stack = []
        def apply(patcher):
            self.stack.append(patcher); patcher.start()
        apply(patch.object(server, "DB_PATH", root / "isolated.sqlite"))
        apply(patch.object(server, "DATA_DIR", root))
        apply(patch.object(server, "cloud_login_required", return_value=True))
        apply(patch.object(server, "resolve_cloud_auth_scope", side_effect=lambda user: {"org_id": "tenant-a" if user != "B" else "tenant-b", "user_id": user}))
        apply(patch.dict("os.environ", {"MMN_GEO_ENABLED": "true", "MMN_GEO_REAL_SAMPLING_ENABLED": "false", "MMN_GEO_WORKER_MODE": "off", "MMN_GEO_DB_PATH": str(root / "geo.sqlite"), "MMN_AUTH_SECRET": secrets.token_hex(32)}))
        self.addCleanup(lambda: [p.stop() for p in reversed(self.stack)])
        server.init_db()
        self.repo = GeoRepository(root / "geo.sqlite")
        self.project = self.repo.create_project("tenant-a", {"name": "HTTP离线", "target_key": "a", "entities": [{"key": "a", "name": "测试车型A"}]})
        self.http = server.Server(("127.0.0.1", 0), server.Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True); self.thread.start()
        self.addCleanup(self.http.server_close); self.addCleanup(self.http.shutdown)
        self.url = "http://127.0.0.1:" + str(self.http.server_address[1])

    def call(self, path, user="A", role="admin", body=None, token=True, headers=None):
        request_headers = {"Content-Type": "application/json"}
        if token:
            org = "tenant-b" if user == "B" else "tenant-a"
            request_headers["Authorization"] = "Bearer " + server.make_auth_token(user, role, org, user)
        request_headers.update(headers or {})
        req = request.Request(self.url + path, data=json.dumps(body).encode() if body is not None else None, headers=request_headers)
        try:
            with request.urlopen(req, timeout=10) as response: return response.status, json.loads(response.read())
        except error.HTTPError as exc:
            content = exc.read()
            return exc.code, json.loads(content) if content.lstrip().startswith(b"{") else {"error": "non-JSON HTTP error"}

    def test_http_route_uses_existing_login_tenant_and_role(self):
        status, result = self.call("/api/geo/capabilities", token=False)
        self.assertEqual(status, 401)
        status, result = self.call("/api/geo/capabilities")
        self.assertEqual(status, 200); self.assertTrue(result["data"]["enabled"])
        suffix = "/api/geo/projects/" + self.project["id"] + "/questions"
        status, result = self.call(suffix, body={"text": "推荐哪些车型？"})
        self.assertEqual(status, 201)
        status, result = self.call(suffix, user="B")
        self.assertEqual(status, 404)
        status, result = self.call(suffix, role="trial", body={"text": "只读不能写"})
        self.assertEqual(status, 403)
        status, result = self.call(suffix, role="trial")
        self.assertEqual(status, 200)

    def test_feature_off_does_not_break_home_and_serves_geo_assets(self):
        with patch.dict("os.environ", {"MMN_GEO_ENABLED": "false"}):
            status, result = self.call("/api/geo/capabilities")
            self.assertEqual(status, 200); self.assertFalse(result["data"]["enabled"])
            status, result = self.call("/api/geo/projects")
            self.assertEqual(status, 409)
        for path, marker in [("/", b'geo-nav-entry'), ("/geo.js", b'MMNGeo'), ("/geo.css", b'geo')]:
            with request.urlopen(self.url + path, timeout=10) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(marker, response.read())

    def test_local_writes_require_loopback_host_and_matching_origin_with_csrf(self):
        body = {"name": "本地隔离项目", "target_key": "a", "entities": [{"key": "a", "name": "测试车型A"}]}
        with patch.object(server, "cloud_login_required", return_value=False):
            invalid = [
                {},
                {"Origin": "https://untrusted.invalid"},
                {"Origin": self.url},
                {"Origin": "https://untrusted.invalid", "X-MMN-CSRF": "1"},
                {"Host": "untrusted.invalid", "Origin": "http://untrusted.invalid", "X-MMN-CSRF": "1"},
            ]
            for headers in invalid:
                with self.subTest(headers=headers):
                    status, _ = self.call("/api/geo/projects", token=False, body=body, headers=headers)
                    self.assertEqual(status, 403)
            self.assertEqual(self.repo.list_projects("local", limit=20, offset=0)["total"], 0)
            status, _ = self.call("/api/geo/projects", token=False, body=body,
                                  headers={"Origin": self.url, "X-MMN-CSRF": "1"})
            self.assertEqual(status, 201)

    def test_cookie_session_writes_keep_existing_csrf_gate(self):
        cookie = server.MMN_SESSION_COOKIE_NAME + "=" + server.make_auth_token("A", "admin", "tenant-a", "A")
        suffix = "/api/geo/projects/" + self.project["id"] + "/questions"
        with patch.object(server, "session_cookie_enabled", return_value=True):
            for extra in [{}, {"Origin": self.url}, {"Origin": "https://untrusted.invalid", "X-MMN-CSRF": "1"}]:
                status, _ = self.call(suffix, token=False, body={"text": "请求来源验证"}, headers={"Cookie": cookie, **extra})
                self.assertEqual(status, 403)
            status, _ = self.call(suffix, token=False, body={"text": "请求来源验证"},
                                  headers={"Cookie": cookie, "Origin": self.url, "X-MMN-CSRF": "1"})
            self.assertEqual(status, 201)

    def test_geo_identity_resolution_does_not_claim_business_data(self):
        with patch.object(server, "ensure_legacy_vertical_claim", side_effect=AssertionError("business write")) as claim:
            status, _ = self.call("/api/geo/projects")
            self.assertEqual(status, 200)
            claim.assert_not_called()


if __name__ == "__main__": unittest.main()
