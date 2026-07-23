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


class SessionCookieSecurityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patchers = [
            patch.object(server, "cloud_login_required", return_value=True),
            patch.object(server, "session_cookie_enabled", return_value=True),
            patch.object(server, "cloud_accounts", return_value={
                "admin": {
                    "password": "correct-password",
                    "org": "安全测试组织",
                    "name": "安全测试管理员",
                    "role": "admin",
                    "permissions": ["manage_all"],
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

    def request(self, method, path, payload=None, headers=None):
        body = b"" if payload is None else json.dumps(payload).encode("utf-8")
        request_headers = dict(headers or {})
        if payload is not None:
            request_headers.setdefault("Content-Type", "application/json")
            request_headers["Content-Length"] = str(len(body))
        conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port, timeout=3)
        conn.request(method, path, body=body, headers=request_headers)
        response = conn.getresponse()
        raw = response.read()
        result = response.status, dict(response.getheaders()), json.loads(raw.decode("utf-8"))
        conn.close()
        return result

    def login(self):
        return self.request(
            "POST",
            "/api/login",
            {"username": "admin", "password": "correct-password"},
            {"X-Real-IP": "198.51.100.80"},
        )

    def test_cookie_login_is_http_only_secure_and_not_exposed_to_javascript(self):
        status, headers, payload = self.login()
        self.assertEqual(status, 200)
        cookie = headers["Set-Cookie"]
        self.assertIn("__Host-mmn_session=", cookie)
        self.assertIn("Path=/", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("Secure", cookie)
        self.assertIn("SameSite=Strict", cookie)
        self.assertNotIn("token", payload["session"])

    def test_cookie_auth_restores_public_session(self):
        _, headers, login_payload = self.login()
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        status, _, payload = self.request("GET", "/api/auth/config", headers={"Cookie": cookie})
        self.assertEqual(status, 200)
        self.assertTrue(payload["sessionCookieEnabled"])
        self.assertEqual(payload["session"]["org_id"], "security-org")
        self.assertEqual(payload["session"]["role"], "admin")
        self.assertEqual(payload["session"]["name"], login_payload["session"]["name"])

    def test_cookie_mutation_requires_same_origin_csrf_header_and_logout_clears_cookie(self):
        _, headers, _ = self.login()
        cookie = headers["Set-Cookie"].split(";", 1)[0]
        status, _, payload = self.request("POST", "/api/logout", {}, {"Cookie": cookie})
        self.assertEqual(status, 403)
        self.assertEqual(payload["error"], "请求来源校验失败，请刷新页面后重试。")

        origin = f"http://127.0.0.1:{self.httpd.server_port}"
        status, response_headers, payload = self.request(
            "POST",
            "/api/logout",
            {},
            {"Cookie": cookie, "Origin": origin, "X-MMN-CSRF": "1"},
        )
        self.assertEqual(status, 200)
        self.assertTrue(payload["ok"])
        self.assertIn("Max-Age=0", response_headers["Set-Cookie"])


class SessionCookieConfigurationTest(unittest.TestCase):
    def test_cookie_mode_fails_closed_without_https_public_base_url(self):
        with patch.dict(
            server.os.environ,
            {"MMN_SESSION_COOKIE_ENABLED": "true", "MMN_PUBLIC_BASE_URL": "http://mmn.example"},
            clear=False,
        ):
            self.assertFalse(server.session_cookie_enabled())

        with patch.dict(
            server.os.environ,
            {"MMN_SESSION_COOKIE_ENABLED": "true", "MMN_PUBLIC_BASE_URL": "https://mmn.example"},
            clear=False,
        ):
            self.assertTrue(server.session_cookie_enabled())


if __name__ == "__main__":
    unittest.main()
