import hashlib
import hmac
import http.client
import json
import threading
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

import server


AUTH_SECRET = "valid-auth-secret-0123456789-ABCDEFGHIJK"
SCHEDULER_SECRET = "valid-scheduler-secret-0123456789-ABCDE"


class _Response:
    status = 200
    headers = {"Content-Type": "text/html"}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return "https://example.com/final"

    def read(self, limit):
        return b"<html>public content</html>"


class _Opener:
    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = 0

    def open(self, request, timeout):
        self.calls += 1
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class P0SecurityStopgapTest(unittest.TestCase):
    def setUp(self):
        server.reset_trial_usage_limits()

    def test_known_or_short_security_secrets_are_rejected(self):
        for value in (
            "short",
            "a" * 48,
            "change-this-auth-secret",
            "CHANGE_THIS_LONG_RANDOM_SECRET",
            "CHANGE_THIS_SEPARATE_LONG_RANDOM_SECRET",
        ):
            with self.subTest(value=value):
                with self.assertRaises(RuntimeError):
                    server.validated_security_secret(value, "MMN_AUTH_SECRET")

    def test_cloud_runtime_requires_explicit_strong_secrets(self):
        with patch.dict("os.environ", {"MMN_AUTH_SECRET": "", "MMN_SCHEDULER_SECRET": ""}, clear=False):
            with self.assertRaisesRegex(RuntimeError, "MMN_AUTH_SECRET"):
                server.validate_runtime_security(host="0.0.0.0", login_required=True)
        with patch.dict(
            "os.environ",
            {"MMN_AUTH_SECRET": AUTH_SECRET, "MMN_SCHEDULER_SECRET": SCHEDULER_SECRET},
            clear=False,
        ):
            self.assertTrue(server.validate_runtime_security(host="0.0.0.0", login_required=True))

    def test_known_legacy_secret_cannot_forge_admin_token(self):
        payload = {
            "username": "attacker",
            "role": "admin",
            "org_id": "victim-org",
            "user_id": "attacker",
            "exp": int(time.time()) + 3600,
        }
        body = server.base64.urlsafe_b64encode(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
        ).decode("ascii").rstrip("=")
        signature = hmac.new(
            b"mmn-local-demo-secret", body.encode("ascii"), hashlib.sha256
        ).hexdigest()
        with patch.dict("os.environ", {"MMN_AUTH_SECRET": ""}, clear=False):
            self.assertIsNone(server.parse_auth_token(f"{body}.{signature}"))

    def test_strong_configured_secret_preserves_legitimate_tokens(self):
        with patch.dict("os.environ", {"MMN_AUTH_SECRET": AUTH_SECRET}, clear=False):
            token = server.make_auth_token("admin", "admin", "org", "user")
            self.assertEqual(server.parse_auth_token(token)["role"], "admin")

    def test_auth_disabled_runtime_is_loopback_only(self):
        self.assertTrue(server.validate_runtime_security(host="127.0.0.1", login_required=False))
        self.assertTrue(server.validate_runtime_security(host="::1", login_required=False))
        with self.assertRaisesRegex(RuntimeError, "回环地址"):
            server.validate_runtime_security(host="0.0.0.0", login_required=False)

    def test_trial_cannot_reach_shared_publication_or_arbitrary_url_routes(self):
        for path in (
            "/api/group-dashboard/cycle-review",
            "/api/ai/founder-talk",
            "/api/content-capability-kb/collect-public",
        ):
            self.assertEqual(server.cloud_post_required_roles(path), {"admin"}, path)

    def test_private_public_content_targets_are_rejected(self):
        for url in (
            "http://127.0.0.1/admin",
            "http://10.0.0.5/private",
            "http://169.254.169.254/latest/meta-data/",
            "file:///etc/passwd",
            "http://user:pass@example.com/",
            "http://example.com:not-a-port/",
        ):
            self.assertFalse(server.validated_public_content_url(url), url)

    def test_redirect_to_private_target_is_revalidated_before_second_request(self):
        redirect = HTTPError(
            "https://example.com/start",
            302,
            "Found",
            {"Location": "http://127.0.0.1/admin"},
            None,
        )
        opener = _Opener(redirect)
        with (
            patch.object(server, "build_opener", return_value=opener),
            patch.object(server, "robots_allowed", return_value=True),
            patch.object(server, "validated_public_content_url", side_effect=lambda url: "127.0.0.1" not in url),
        ):
            with self.assertRaisesRegex(ValueError, "公网地址安全校验"):
                server.fetch_public_content_page(
                    "https://example.com/start", user_agent="test", delay_seconds=0
                )
        self.assertEqual(opener.calls, 1)

    def test_legitimate_public_content_control_remains_available(self):
        opener = _Opener(_Response())
        with (
            patch.object(server, "build_opener", return_value=opener),
            patch.object(server, "robots_allowed", return_value=True),
            patch.object(server, "validated_public_content_url", return_value=True),
        ):
            result = server.fetch_public_content_page(
                "https://example.com/start", user_agent="test", delay_seconds=0
            )
        self.assertEqual(result["status"], 200)
        self.assertEqual(result["url"], "https://example.com/final")

    def test_trial_request_and_concurrency_limits_fail_with_retry(self):
        auth = {"role": "trial", "user_id": "trial-user"}
        path = "/api/ai/rag-strategy"
        with patch.dict("os.environ", {
            "MMN_TRIAL_REQUEST_LIMIT": "2",
            "MMN_TRIAL_CONCURRENCY_LIMIT": "1",
            "MMN_TRIAL_REQUEST_WINDOW_SECONDS": "60",
        }, clear=False):
            key, retry = server.acquire_trial_usage(auth, path, current_time=100)
            self.assertEqual(retry, 0)
            blocked_key, retry = server.acquire_trial_usage(auth, path, current_time=101)
            self.assertIsNone(blocked_key)
            self.assertEqual(retry, 1)
            server.release_trial_usage(key)
            key, retry = server.acquire_trial_usage(auth, path, current_time=102)
            self.assertEqual(retry, 0)
            server.release_trial_usage(key)
            blocked_key, retry = server.acquire_trial_usage(auth, path, current_time=103)
            self.assertIsNone(blocked_key)
            self.assertGreaterEqual(retry, 1)

    def test_trial_budget_covers_dynamic_retry_routes_and_cannot_be_rotated(self):
        auth = {"role": "trial", "user_id": "trial-user"}
        dynamic_paths = [
            "/api/content-capability-kb/script-jobs/job-1/retry",
            "/api/content-capability-kb/script-jobs/job-1/revise",
            "/api/social-evidence/jobs/job-1/retry",
            "/api/douyin-vehicle-radar/runs/run-1/retry",
        ]
        with patch.dict("os.environ", {
            "MMN_TRIAL_REQUEST_LIMIT": "1",
            "MMN_TRIAL_CONCURRENCY_LIMIT": "1",
            "MMN_TRIAL_REQUEST_WINDOW_SECONDS": "60",
        }, clear=False):
            key, retry = server.acquire_trial_usage(auth, dynamic_paths[0], current_time=100)
            self.assertEqual(retry, 0)
            for path in dynamic_paths[1:]:
                blocked_key, retry = server.acquire_trial_usage(auth, path, current_time=101)
                self.assertIsNone(blocked_key)
                self.assertGreaterEqual(retry, 1)
            server.release_trial_usage(key)
            blocked_key, retry = server.acquire_trial_usage(
                auth, "/api/douyin-vehicle-radar/video-insights/jobs", current_time=102
            )
            self.assertIsNone(blocked_key)
            self.assertGreaterEqual(retry, 1)

    def test_admin_and_non_trial_routes_do_not_consume_trial_budget(self):
        self.assertEqual(
            server.acquire_trial_usage({"role": "admin", "user_id": "admin"}, "/api/ai/rag-strategy"),
            (None, 0),
        )
        self.assertEqual(
            server.acquire_trial_usage({"role": "trial", "user_id": "trial"}, "/api/admin-only"),
            (None, 0),
        )


class P0HandlerBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.patchers = [
            patch.object(server, "cloud_login_required", return_value=True),
            patch.dict(
                "os.environ",
                {"MMN_AUTH_SECRET": AUTH_SECRET, "MMN_SCHEDULER_SECRET": SCHEDULER_SECRET},
                clear=False,
            ),
            patch.object(server, "ensure_legacy_vertical_claim", return_value=None),
            patch.object(server, "run_weekly_group_dashboard_refresh", return_value={"status": "ok"}),
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

    def post(self, path, payload=None, headers=None):
        body = json.dumps(payload or {}).encode("utf-8")
        request_headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(body)),
            **(headers or {}),
        }
        conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port, timeout=3)
        conn.request("POST", path, body=body, headers=request_headers)
        response = conn.getresponse()
        result = response.status, json.loads(response.read().decode("utf-8"))
        conn.close()
        return result

    def test_trial_request_is_rejected_before_shared_write_handler(self):
        token = server.make_auth_token("trial", "trial", "trial-org", "trial-user")
        with patch.object(server, "collect_public_content_capability") as collector:
            status, payload = self.post(
                "/api/content-capability-kb/collect-public",
                {"url": "http://127.0.0.1/private"},
                {"Authorization": f"Bearer {token}"},
            )
        self.assertEqual(status, 403)
        self.assertFalse(payload["ok"])
        collector.assert_not_called()

    def test_legacy_scheduler_headers_no_longer_bypass_auth(self):
        status, payload = self.post(
            "/api/group-dashboard/refresh-weekly",
            headers={"Host": "mmn-app", "X-MMN-Scheduler": "1"},
        )
        self.assertEqual(status, 401)
        self.assertFalse(payload["ok"])

    def test_valid_scheduler_signature_keeps_refresh_working(self):
        timestamp = str(int(time.time()))
        signature = server.scheduler_signature(
            "POST", "/api/group-dashboard/refresh-weekly", timestamp, secret=SCHEDULER_SECRET
        )
        status, payload = self.post(
            "/api/group-dashboard/refresh-weekly",
            headers={
                "X-MMN-Scheduler-Timestamp": timestamp,
                "X-MMN-Scheduler-Signature": signature,
            },
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["result"], {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
