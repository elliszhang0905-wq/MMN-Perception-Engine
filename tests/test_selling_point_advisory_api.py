import json
import sqlite3
import unittest
from pathlib import Path

import server
import selling_point_advisory as advisory
from tests.test_selling_point_advisory import completed_review, context


class SellingPointAdvisoryApiTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        advisory.init_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_server_runtime_maps_three_internal_providers_to_neutral_public_reviews(self):
        calls = []

        def provider_runner(provider, messages):
            calls.append((provider, messages[-1]["content"]))
            return completed_review()

        result = server.run_selling_point_advisory_request(
            self.conn,
            context(complete=True),
            org_id="org-a",
            user_id="ellis",
            provider_runner=provider_runner,
        )
        self.assertEqual(len(calls), 3)
        self.assertEqual(len({payload for _, payload in calls}), 1)
        self.assertEqual([item["label"] for item in result["reviews"]], ["独立建议一", "独立建议二", "独立建议三"])
        public = json.dumps(result, ensure_ascii=False).lower()
        for provider, _ in calls:
            self.assertNotIn(provider, public)

    def test_routes_take_org_and_user_from_session_not_request_body(self):
        source = Path(server.__file__).read_text(encoding="utf-8")
        run_route = source.split('if parsed.path == "/api/selling-point-advisory/run":', 1)[1].split("return", 1)[0]
        manual_route = source.split('if parsed.path == "/api/selling-point-advisory/manual-review":', 1)[1].split("return", 1)[0]
        for route in (run_route, manual_route):
            self.assertIn("self.current_auth()", route)
            self.assertIn('auth.get("org_id", "local")', route)
            self.assertNotIn("body.get(\"org", route)


if __name__ == "__main__":
    unittest.main()
