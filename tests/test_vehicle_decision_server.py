import json
import tempfile
import unittest
from pathlib import Path

import server


class VehicleDecisionServerTest(unittest.TestCase):
    def setUp(self):
        self.original_db_path = server.DB_PATH
        self.tempdir = tempfile.TemporaryDirectory()
        server.DB_PATH = Path(self.tempdir.name) / "vehicle-decision.db"
        server.init_db()

    def tearDown(self):
        server.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def test_adapter_reads_existing_alias_data_without_writing_upstream(self):
        with server.db() as conn:
            conn.execute(
                """insert into agent_runs
                (id,org_id,user_id,edition,task_type,brand,model,competitors_json,platforms_json,
                 time_window_json,status,final_output_json,qa_summary_json,created_at,updated_at)
                values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                ("run-e7x", "local", "u", "china", "strategy", "AUDI", "奥迪E7X", "[]", "[]",
                 json.dumps({"start": "2026-06-01", "end": "2026-06-30"}), "completed",
                 json.dumps({"text": "核心策略结论：当前最重要的是验证订单承接。"}, ensure_ascii=False), "{}",
                 "2026-07-21T00:00:00Z", "2026-07-21T00:00:00Z"),
            )
            before = conn.execute("select count(*) from agent_runs").fetchone()[0]
        inputs = server.vehicle_decision_surface_inputs("AUDI E7X", "local", "china")
        self.assertEqual(len(inputs["executive_summary"]), 1)
        self.assertEqual(inputs["executive_summary"][0]["evidenceIds"], ["DB:agent_runs:run-e7x"])
        with server.db() as conn:
            self.assertEqual(conn.execute("select count(*) from agent_runs").fetchone()[0], before)

    def test_real_adapter_snapshot_explicitly_covers_all_eight_surfaces(self):
        inputs = server.vehicle_decision_surface_inputs("AUDI E7X", "local", "china")
        with server.db() as conn:
            snapshot = server.create_vehicle_decision_snapshot(conn, {
                "brand": "AUDI", "model": "AUDI E7X", "project": "隔离验收",
                "vehicleStage": "上市期", "businessQuestion": "当前优先行动",
                "coreCompetitors": [], "dataCutoffAt": "2026-07-21T00:00:00Z", "surfaceInputs": inputs,
            }, org_id="local", user_id="tester", edition="china")
        self.assertEqual(len(snapshot["surfaceCoverage"]), 8)
        self.assertEqual(len({item["surface"] for item in snapshot["signals"]}), 8)

    def test_server_registers_complete_http_contract(self):
        source = Path(server.__file__).read_text(encoding="utf-8")
        for fragment in (
            '"/api/vehicle-decisions/snapshots"',
            '"/api/vehicle-decisions/reports"',
            '"/api/vehicle-decisions/actions"',
            '"/api/vehicle-decisions/learning-candidates"',
            '"/api/vehicle-decisions/knowhow-candidates"',
            'export\\.(md|pptx)',
        ):
            self.assertIn(fragment, source)


if __name__ == "__main__":
    unittest.main()
