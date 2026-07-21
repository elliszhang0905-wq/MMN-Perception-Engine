import tempfile
import unittest
from pathlib import Path

import server
from tests.test_strategy_report_package import completed_output, request_body


class StrategyReportPackageApiTest(unittest.TestCase):
    def setUp(self):
        self.original_db_path = server.DB_PATH
        self.tempdir = tempfile.TemporaryDirectory()
        server.DB_PATH = Path(self.tempdir.name) / "strategy-report-package.db"
        server.init_db()

    def tearDown(self):
        server.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def test_server_adapter_reuses_existing_read_only_surfaces_and_neutralizes_channels(self):
        providers = []

        def runner(provider, messages):
            providers.append(provider)
            return completed_output()

        with server.db() as conn:
            result = server.run_strategy_report_package_request(
                conn, request_body(), org_id="org-a", user_id="ellis", provider_runner=runner,
            )
            upstream_count = conn.execute("select count(*) from vehicle_decision_snapshots").fetchone()[0]
        self.assertEqual(result["package"]["status"], "completed")
        self.assertEqual(result["package"]["completedChannelCount"], 3)
        self.assertEqual(len(providers), 3)
        self.assertEqual(upstream_count, 0)

    def test_http_contract_registers_create_and_zip_download_routes(self):
        source = Path(server.__file__).read_text(encoding="utf-8")
        self.assertIn('parsed.path == "/api/strategy-report-packages"', source)
        self.assertIn(r'/api/strategy-report-packages/([^/]+)/download', source)
        self.assertIn('"Content-Type", "application/zip"', source)


if __name__ == "__main__":
    unittest.main()
