import unittest
from types import SimpleNamespace
from unittest.mock import patch

import server


class LegacySecurityRegressionTest(unittest.TestCase):
    def test_cloud_auth_never_reuses_model_secret_or_demo_default(self):
        with (
            patch.dict(
                server.os.environ,
                {"MMN_AUTH_SECRET": "", "DASHSCOPE_API_KEY": "model-secret"},
                clear=False,
            ),
            patch.object(server, "env_file_values", return_value={}),
            patch.object(server, "cloud_login_required", return_value=True),
        ):
            with self.assertRaises(RuntimeError):
                server.auth_secret()

    def test_only_explicitly_trusted_proxy_can_supply_real_ip(self):
        request = SimpleNamespace(
            client_address=("10.23.4.5", 1234),
            headers={"X-Real-IP": "198.51.100.77"},
        )
        with patch.dict(
            server.os.environ,
            {"MMN_TRUSTED_PROXY_CIDRS": "127.0.0.0/8"},
            clear=False,
        ):
            self.assertEqual(server.Handler.request_source_ip(request), "10.23.4.5")

    def test_scheduler_and_raw_upload_boundaries_are_registered(self):
        self.assertTrue(hasattr(server, "valid_scheduler_signature"))
        self.assertTrue(hasattr(server.Handler, "read_raw_body"))


if __name__ == "__main__":
    unittest.main()
