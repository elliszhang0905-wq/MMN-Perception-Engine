import contextlib
import hashlib
import hmac
import http.client
import json
import threading
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import server


@contextlib.contextmanager
def fake_db():
    yield object()


class SecurityRequestBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ensure_workspace = patch.object(server, "ensure_workspace", return_value=None)
        cls.seed_policy_mvp = patch.object(server, "seed_policy_mvp", return_value=None)
        cls.ensure_legacy_vertical_claim = patch.object(server, "ensure_legacy_vertical_claim", return_value=None)
        cls.patchers = [
            patch.object(server, "cloud_login_required", return_value=True),
            patch.dict(server.os.environ, {
                "MMN_AUTH_SECRET": "test-auth-secret",
                "MMN_SCHEDULER_SECRET": "test-scheduler-secret",
                "MMN_TRUSTED_PROXY_CIDRS": "127.0.0.0/8",
            }, clear=False),
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
            cls.ensure_workspace,
            cls.seed_policy_mvp,
            cls.ensure_legacy_vertical_claim,
            patch.object(server, "MMN_MAX_JSON_BODY_BYTES", 64, create=True),
            patch.object(server, "MMN_LOGIN_MAX_FAILURES", 3, create=True),
            patch.object(server, "MMN_LOGIN_FAILURE_WINDOW_SECONDS", 60, create=True),
            patch.object(server, "MMN_LOGIN_BLOCK_SECONDS", 60, create=True),
        ]
        for patcher in cls.patchers:
            patcher.start()
        cls.ensure_workspace_mock = server.ensure_workspace
        cls.seed_policy_mvp_mock = server.seed_policy_mvp
        cls.ensure_legacy_vertical_claim_mock = server.ensure_legacy_vertical_claim
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
        self.ensure_workspace_mock.reset_mock()
        self.seed_policy_mvp_mock.reset_mock()
        self.ensure_legacy_vertical_claim_mock.reset_mock()

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
        self.ensure_workspace_mock.assert_not_called()
        self.seed_policy_mvp_mock.assert_not_called()
        self.ensure_legacy_vertical_claim_mock.assert_not_called()

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

    def test_cloud_auth_secret_fails_closed_without_dedicated_secret(self):
        with (
            patch.dict(server.os.environ, {"MMN_AUTH_SECRET": "", "DASHSCOPE_API_KEY": "model-secret"}, clear=False),
            patch.object(server, "env_file_values", return_value={}),
            patch.object(server, "cloud_login_required", return_value=True),
        ):
            with self.assertRaises(RuntimeError):
                server.auth_secret()

    def test_untrusted_private_peer_cannot_spoof_real_ip(self):
        request = SimpleNamespace(
            client_address=("10.23.4.5", 1234),
            headers={"X-Real-IP": "198.51.100.77"},
        )
        with patch.dict(server.os.environ, {"MMN_TRUSTED_PROXY_CIDRS": "127.0.0.0/8"}, clear=False):
            self.assertEqual(server.Handler.request_source_ip(request), "10.23.4.5")

    def test_legacy_scheduler_headers_do_not_bypass_admin_auth(self):
        body = b"{}"
        conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port, timeout=3)
        conn.request(
            "POST",
            "/api/group-dashboard/refresh-weekly",
            body=body,
            headers={
                "Content-Type": "application/json",
                "Content-Length": str(len(body)),
                "Host": "mmn-app",
                "X-MMN-Scheduler": "1",
            },
        )
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        conn.close()
        self.assertEqual(response.status, 401)
        self.assertEqual(payload["error"], "请先登录 MMN 云端演示系统。")

    def test_valid_scheduler_signature_is_accepted(self):
        timestamp = str(int(time.time()))
        signed = f"POST\n/api/group-dashboard/refresh-weekly\n{timestamp}".encode("utf-8")
        signature = hmac.new(b"test-scheduler-secret", signed, hashlib.sha256).hexdigest()
        body = b"{}"
        with patch.object(server, "run_weekly_group_dashboard_refresh", return_value={"status": "verified"}) as refresh:
            conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port, timeout=3)
            conn.request(
                "POST",
                "/api/group-dashboard/refresh-weekly",
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                    "X-MMN-Scheduler-Timestamp": timestamp,
                    "X-MMN-Scheduler-Signature": signature,
                },
            )
            response = conn.getresponse()
            payload = json.loads(response.read().decode("utf-8"))
            conn.close()
        self.assertEqual(response.status, 200)
        self.assertTrue(payload["ok"])
        refresh.assert_called_once_with(None)

    def test_valid_scheduler_signature_covers_non_dashboard_jobs(self):
        path = "/api/founder-archives/run-weekly"
        timestamp = str(int(time.time()))
        signature = server.scheduler_signature(
            "POST",
            path,
            timestamp,
            secret="test-scheduler-secret",
        )
        body = json.dumps({"edition": "china"}).encode("utf-8")
        with patch.object(server, "run_founder_weekly_crawl", return_value={"ok": True}) as crawl:
            conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port, timeout=3)
            conn.request(
                "POST",
                path,
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                    "X-MMN-Scheduler-Timestamp": timestamp,
                    "X-MMN-Scheduler-Signature": signature,
                },
            )
            response = conn.getresponse()
            payload = json.loads(response.read().decode("utf-8"))
            conn.close()
        self.assertEqual(response.status, 200)
        self.assertTrue(payload["ok"])
        crawl.assert_called_once_with(edition="china", manual=True)

    def test_expired_scheduler_signature_is_rejected(self):
        timestamp = str(int(time.time()) - server.MMN_SCHEDULER_MAX_CLOCK_SKEW_SECONDS - 1)
        signature = server.scheduler_signature(
            "POST",
            "/api/group-dashboard/refresh-weekly",
            timestamp,
            secret="test-scheduler-secret",
        )
        self.assertFalse(server.valid_scheduler_signature(
            {
                "X-MMN-Scheduler-Timestamp": timestamp,
                "X-MMN-Scheduler-Signature": signature,
            },
            "POST",
            "/api/group-dashboard/refresh-weekly",
        ))

    def test_raw_upload_rejects_oversized_body_before_auth_or_read(self):
        conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port, timeout=3)
        conn.request(
            "POST",
            "/api/import-video-xlsx",
            body=b"",
            headers={"Content-Length": str(server.MAX_UPLOAD_BYTES + 1)},
        )
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        conn.close()
        self.assertEqual(response.status, 413)
        self.assertEqual(payload["error"], f"上传文件不能超过{server.MAX_UPLOAD_BYTES // 1024 // 1024}MB。")

    def test_cloud_server_error_does_not_expose_internal_details(self):
        with patch.object(server, "cloud_login_required", return_value=True):
            self.assertEqual(
                server.public_server_error(RuntimeError("sqlite path=/secret/data.db")),
                "服务暂时不可用，请稍后重试。",
            )


if __name__ == "__main__":
    unittest.main()
