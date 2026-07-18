import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MmnEvalApiContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = (ROOT / "server.py").read_text(encoding="utf-8")

    def test_server_imports_focused_eval_dashboard_services(self):
        self.assertIn("from mmn_eval.dashboard import (", self.server)
        self.assertIn("load_dashboard_payload as load_mmn_eval_dashboard", self.server)
        self.assertIn("run_seed_dashboard as run_mmn_eval_dashboard", self.server)
        self.assertIn("save_human_review as save_mmn_eval_human_review", self.server)

    def test_deploy_publishes_eval_seed_fixtures_into_persistent_data_volume(self):
        deploy_script = (ROOT / "scripts" / "deploy.sh").read_text(encoding="utf-8")
        self.assertIn("data/eval/mmn_eval_seed_v0.1.jsonl", deploy_script)
        self.assertIn("data/eval/mmn_eval_seed_outputs_v0.1.jsonl", deploy_script)
        self.assertIn('"mmn-app:/app/$eval_fixture"', deploy_script)

    def test_get_report_route_returns_dashboard_payload(self):
        self.assertIn('parsed.path == "/api/eval/report"', self.server)
        self.assertIn("load_mmn_eval_dashboard(org_id=auth.get(\"org_id\", \"local\"))", self.server)

    def test_post_run_route_executes_real_seed_eval(self):
        self.assertIn('parsed.path == "/api/eval/run"', self.server)
        self.assertIn("run_mmn_eval_dashboard(org_id=auth.get(\"org_id\", \"local\"))", self.server)

    def test_post_human_review_route_records_actor_and_decision(self):
        self.assertIn('parsed.path == "/api/eval/human-review"', self.server)
        self.assertIn('body.get("caseId")', self.server)
        self.assertIn('body.get("decision")', self.server)
        self.assertIn('body.get("note")', self.server)
        self.assertIn('reviewer=auth.get("email") or auth.get("username") or auth.get("user_id") or "local-human"', self.server)


if __name__ == "__main__":
    unittest.main()
