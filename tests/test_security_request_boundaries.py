import contextlib
import http.client
import json
import threading
import unittest
from unittest.mock import patch

import server


@contextlib.contextmanager
def fake_db():
    yield object()


class SecurityRequestBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patchers = [
            patch.object(server, "cloud_login_required", return_value=True),
            patch.object(server, "cloud_accounts", return_value={
                "admin": {
                    "password": "correct-password",
                    "org": "安全测试组织",
                    "name": "安全测试管理员",
                    "role": "admin",
                    "permissions": ["all"],
                },
            }),
            patch.object(
                server,
                "resolve_cloud_auth_scope",
                return_value={"org_id": "security-org", "user_id": "security-user"},
            ),
            patch.object(server, "db", fake_db),
            patch.object(server, "ensure_workspace", return_value=None),
            patch.object(server, "seed_policy_mvp", return_value=None),
            patch.object(server, "ensure_legacy_vertical_claim", return_value=None),
            patch.object(server, "MMN_MAX_JSON_BODY_BYTES", 64, create=True),
            patch.object(server, "MMN_LOGIN_MAX_FAILURES", 3, create=True),
            patch.object(server, "MMN_LOGIN_FAILURE_WINDOW_SECONDS", 60, create=True),
            patch.object(server, "MMN_LOGIN_BLOCK_SECONDS", 60, create=True),
        ]
        for patcher in cls.patchers:
            patcher.start()
        cls.httpd = server.http.server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)
        for patcher in reversed(cls.patchers):
            patcher.stop()

    def setUp(self):
        server.reset_login_rate_limits()

    def post(self, payload, *, content_type="application/json", real_ip="198.51.100.10"):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port, timeout=3)
        headers = {"Content-Length": str(len(body)), "X-Real-IP": real_ip}
        if content_type is not None:
            headers["Content-Type"] = content_type
        conn.request("POST", "/api/login", body=body, headers=headers)
        response = conn.getresponse()
        raw = response.read()
        result = response.status, dict(response.getheaders()), json.loads(raw.decode("utf-8"))
        conn.close()
        return result

    def test_rejects_oversized_json_before_login_logic(self):
        status, _, payload = self.post({"padding": "x" * 80})
        self.assertEqual(status, 413)
        self.assertEqual(payload, {"ok": False, "error": "JSON请求体不能超过64字节。"})

    def test_rejects_non_json_media_type(self):
        status, _, payload = self.post(
            b'{"username":"admin","password":"correct-password"}',
            content_type="text/plain",
        )
        self.assertEqual(status, 415)
        self.assertEqual(payload, {"ok": False, "error": "该接口只接受JSON请求。"})

    def test_rejects_malformed_json_with_stable_public_error(self):
        status, _, payload = self.post(b'{"username":')
        self.assertEqual(status, 400)
        self.assertEqual(payload, {"ok": False, "error": "JSON格式无效。"})

    def test_rejects_non_object_json(self):
        status, _, payload = self.post(b'["admin","correct-password"]')
        self.assertEqual(status, 400)
        self.assertEqual(payload, {"ok": False, "error": "JSON请求体必须是对象。"})

    def test_wrong_account_and_wrong_password_have_same_response(self):
        first = self.post({"username": "missing", "password": "wrong"}, real_ip="198.51.100.20")
        second = self.post({"username": "admin", "password": "wrong"}, real_ip="198.51.100.21")
        self.assertEqual(first[0], 400)
        self.assertEqual(second[0], 400)
        self.assertEqual(first[2], second[2])
        self.assertEqual(first[2]["error"], "账号或密码不正确。")

    def test_source_dimension_blocks_repeated_failures_and_recovers_after_success(self):
        for username in ("missing-1", "missing-2"):
            status, _, _ = self.post(
                {"username": username, "password": "wrong"},
                real_ip="198.51.100.30",
            )
            self.assertEqual(status, 400)
        status, headers, payload = self.post(
            {"username": "missing-3", "password": "wrong"},
            real_ip="198.51.100.30",
        )
        self.assertEqual(status, 429)
        self.assertGreaterEqual(int(headers["Retry-After"]), 1)
        self.assertEqual(payload["error"], "登录尝试过于频繁，请稍后再试。")

        server.reset_login_rate_limits()
        status, _, payload = self.post(
            {"username": "admin", "password": "correct-password"},
            real_ip="198.51.100.30",
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertTrue(payload["session"]["token"])

    def test_account_dimension_blocks_failures_from_multiple_sources(self):
        for index in range(2):
            status, _, _ = self.post(
                {"username": "admin", "password": "wrong"},
                real_ip=f"198.51.100.{40 + index}",
            )
            self.assertEqual(status, 400)
        status, headers, payload = self.post(
            {"username": "admin", "password": "wrong"},
            real_ip="198.51.100.42",
        )
        self.assertEqual(status, 429)
        self.assertGreaterEqual(int(headers["Retry-After"]), 1)
        self.assertEqual(payload["error"], "登录尝试过于频繁，请稍后再试。")


if __name__ == "__main__":
    unittest.main()
