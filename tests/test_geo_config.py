import os
import unittest
from unittest.mock import patch

from geo.config import load_settings


class GeoConfigTests(unittest.TestCase):
    def test_isolated_database_path_is_backend_configuration_only(self):
        snapshot = {"MMN_GEO_DB_PATH": "/tmp/geo-isolated-config.sqlite"}
        with patch.dict(os.environ, {}, clear=True), patch("runtime_config.env_value", side_effect=lambda k, d="": snapshot.get(k, d)):
            settings = load_settings()
        self.assertEqual(settings.get("db_path"), snapshot["MMN_GEO_DB_PATH"])

    def test_existing_runtime_file_snapshot_is_read_without_exporting_secrets(self):
        snapshot = {"MMN_GEO_ENABLED": "true", "ARK_API_KEY": "offline-config-fixture",
                    "GEO_MODEL_ID": "fixture-endpoint", "GEO_MAX_CONCURRENCY": "2"}
        with patch.dict(os.environ, {}, clear=True), patch("runtime_config.env_value", side_effect=lambda k, d="": snapshot.get(k, d)):
            settings = load_settings()
            self.assertTrue(settings["enabled"])
            self.assertEqual(settings["model"], "fixture-endpoint")
            self.assertEqual(settings["max_concurrency"], 2)
            self.assertNotIn("ARK_API_KEY", os.environ)
            self.assertFalse(settings["real_sampling_enabled"])

    def test_explicit_process_disabled_or_empty_overrides_file_snapshot(self):
        with patch.dict(os.environ, {"MMN_GEO_ENABLED": "false", "ARK_API_KEY": ""}, clear=True), patch("runtime_config.env_value", return_value="true"):
            settings = load_settings()
            self.assertFalse(settings["enabled"])
            self.assertEqual(settings["api_key"], "")


if __name__ == "__main__":
    unittest.main()
