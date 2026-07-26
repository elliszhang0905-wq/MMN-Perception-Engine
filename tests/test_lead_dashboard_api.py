import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER = (ROOT / "server.py").read_text(encoding="utf-8")


class LeadDashboardApiContractTest(unittest.TestCase):
    def test_read_and_import_routes_are_registered(self):
        self.assertIn('parsed.path == "/api/lead-dashboard-data"', SERVER)
        self.assertIn('parsed.path == "/api/lead-dashboard/import"', SERVER)
        self.assertIn("get_lead_dashboard_dataset", SERVER)
        self.assertIn("save_lead_dashboard_datasets", SERVER)
        self.assertIn("extract_lead_dashboard_rows", SERVER)

    def test_import_is_raw_body_admin_only_and_size_limited(self):
        raw_paths = re.search(r"RAW_BODY_POST_PATHS = frozenset\(\{([\s\S]*?)\}\)", SERVER)
        self.assertIsNotNone(raw_paths)
        self.assertIn("/api/lead-dashboard/import", raw_paths.group(1))
        trial_paths = re.search(r"TRIAL_POST_ALLOWED_PATHS = frozenset\(\{([\s\S]*?)\}\)", SERVER)
        self.assertIsNotNone(trial_paths)
        self.assertNotIn("/api/lead-dashboard/import", trial_paths.group(1))
        self.assertIn("LEAD_DASHBOARD_MAX_UPLOAD_BYTES", SERVER)
        self.assertIn("线索数据文件超出上传限制", SERVER)
        self.assertIn("lead_dashboard_rows_from_file", SERVER)


if __name__ == "__main__":
    unittest.main()
