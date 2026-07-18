import json
import unittest
from unittest.mock import patch

import server


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return b'{"choices":[{"message":{"content":"ok"}}]}'


class DeepSeekV4ConfigTest(unittest.TestCase):
    def _request_body(self, profile):
        captured = {}

        def fake_urlopen(request, timeout):
            captured["body"] = json.loads(request.data.decode("utf-8"))
            captured["timeout"] = timeout
            return _Response()

        environment = {
            "DEEPSEEK_API_KEY": "test-key",
            "DEEPSEEK_MODEL": "deepseek-v4-flash",
            "DEEPSEEK_DEEP_MODEL": "deepseek-v4-pro",
        }
        with patch.dict(server.os.environ, environment, clear=False), patch.object(server, "urlopen", side_effect=fake_urlopen):
            self.assertEqual(server.call_deepseek([{"role": "user", "content": "test"}], profile=profile), "ok")
        return captured["body"]

    def test_default_models_use_supported_v4_ids(self):
        self.assertEqual(server.DEEPSEEK_DEFAULT_MODEL, "deepseek-v4-flash")
        self.assertEqual(server.DEEPSEEK_DEFAULT_DEEP_MODEL, "deepseek-v4-pro")

    def test_fast_profile_explicitly_disables_thinking(self):
        body = self._request_body("fast")
        self.assertEqual(body["model"], "deepseek-v4-flash")
        self.assertEqual(body["thinking"], {"type": "disabled"})
        self.assertIn("temperature", body)
        self.assertNotIn("reasoning_effort", body)

    def test_deep_profile_enables_high_effort_without_temperature(self):
        body = self._request_body("deep")
        self.assertEqual(body["model"], "deepseek-v4-pro")
        self.assertEqual(body["thinking"], {"type": "enabled"})
        self.assertEqual(body["reasoning_effort"], "high")
        self.assertNotIn("temperature", body)

    def test_empty_final_content_is_rejected(self):
        class EmptyResponse(_Response):
            def read(self):
                return b'{"choices":[{"message":{"content":"","reasoning_content":"thinking"}}]}'

        with patch.dict(server.os.environ, {"DEEPSEEK_API_KEY": "test-key"}, clear=False), patch.object(server, "urlopen", return_value=EmptyResponse()):
            with self.assertRaisesRegex(ValueError, "未返回最终正文"):
                server.call_deepseek([{"role": "user", "content": "test"}], profile="deep")


if __name__ == "__main__":
    unittest.main()
