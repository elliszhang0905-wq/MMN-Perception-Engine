import json
import tempfile
import unittest
from pathlib import Path

import server


class ServerTenantScopeTest(unittest.TestCase):
    def setUp(self):
        self.original_db_path = server.DB_PATH
        self.tempdir = tempfile.TemporaryDirectory()
        server.DB_PATH = Path(self.tempdir.name) / "tenant-scope.db"
        server.init_db()
        with server.db() as conn:
            for org_id, document_id in (("org-a", "doc-a"), ("org-b", "doc-b")):
                payload = {
                    "documentId": document_id,
                    "filename": f"{document_id}.pdf",
                    "brand": "测试品牌",
                    "model": f"车型-{org_id}",
                    "facts": [],
                    "manualReviewItems": [],
                }
                conn.execute(
                    """insert into product_fact_documents
                       (id, org_id, user_id, edition, brand, model, version, filename,
                        sha256, storage_path, payload_json, created_at)
                       values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        document_id,
                        org_id,
                        "tester",
                        "china",
                        "测试品牌",
                        payload["model"],
                        "v1",
                        payload["filename"],
                        f"sha-{org_id}",
                        "",
                        json.dumps(payload, ensure_ascii=False),
                        "2026-07-12T00:00:00Z",
                    ),
                )
        self._save_run("run-a", "org-a")
        self._save_run("run-b", "org-b")

    def tearDown(self):
        server.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def _save_run(self, run_id, org_id):
        server.save_agent_run_record(
            {
                "id": run_id,
                "org_id": org_id,
                "user_id": "tester",
                "edition": "china",
                "task_type": "opportunity_map",
                "brand": "测试品牌",
                "model": f"车型-{org_id}",
                "competitors": [],
                "platforms": [],
                "status": "completed",
                "final_output": {"opportunities": [], "executionRecommendations": []},
                "qa_summary": {},
                "created_at": "2026-07-12T00:00:00Z",
                "updated_at": "2026-07-12T00:00:00Z",
            },
            [],
            [],
            [],
        )

    def test_document_and_run_reads_reject_other_org(self):
        self.assertIsNotNone(server._opportunity_document_payload("doc-a", "org-a"))
        self.assertIsNone(server._opportunity_document_payload("doc-b", "org-a"))
        self.assertIsNotNone(server.agent_run_payload("run-a", "org-a"))
        self.assertIsNone(server.agent_run_payload("run-b", "org-a"))

        with self.assertRaisesRegex(ValueError, "未找到本品产品资料"):
            server.opportunity_manual_review_payload("doc-b", org_id="org-a")
        with self.assertRaisesRegex(ValueError, "未找到本品产品资料"):
            server.run_opportunity_map_pipeline({"documentId": "doc-b"}, org_id="org-a")
        with self.assertRaisesRegex(ValueError, "同一客户空间"):
            server.save_opportunity_run_review("run-b", "舒适性", org_id="org-a")

    def test_execution_cycle_list_is_scoped_by_org(self):
        with server.db() as conn:
            conn.executemany(
                """insert into cockpit_execution_cycles
                   (id, org_id, user_id, edition, model, opportunity_run_id,
                    opportunity_label, status, plan_json, monitoring_json, created_at, updated_at)
                   values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    ("cycle-a", "org-a", "u", "china", "同名车型", "run-a", "舒适性", "planned", "{}", "{}", "2026-07-12", "2026-07-12"),
                    ("cycle-b", "org-b", "u", "china", "同名车型", "run-b", "安全", "planned", "{}", "{}", "2026-07-12", "2026-07-12"),
                ],
            )

        payload = server.cockpit_execution_cycles_payload("china", "同名车型", org_id="org-a")

        self.assertEqual([item["id"] for item in payload["cycles"]], ["cycle-a"])

    def test_same_asset_id_in_two_orgs_does_not_overwrite_first_org(self):
        with server.db() as conn:
            for org_id, title in (("org-a", "A客户策略"), ("org-b", "B客户策略")):
                payload = {"strategyKb": [{"id": "shared-visible-id", "title": title}]}
                conn.execute(
                    """insert into project_snapshots
                       (id, org_id, user_id, edition, brand, model, project,
                        data_version, payload_json, created_at)
                       values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        f"snapshot-{org_id}",
                        org_id,
                        "tester",
                        "china",
                        "",
                        "",
                        "",
                        "",
                        json.dumps(payload, ensure_ascii=False),
                        "2026-07-12T00:00:00Z",
                    ),
                )
            server.backfill_strategy_knowledge_assets(conn)

        assets_a = server.durable_asset_library("china", "org-a")["strategyAssets"]
        assets_b = server.durable_asset_library("china", "org-b")["strategyAssets"]
        self.assertEqual([item["title"] for item in assets_a], ["A客户策略"])
        self.assertEqual([item["title"] for item in assets_b], ["B客户策略"])

    def test_router_decision_id_is_scoped_by_embedded_owner(self):
        decision_id = server.save_router_decision({
            "id": "router-org-b",
            "edition": "china",
            "task_type": "strategy_reasoning",
            "route_key": "test",
            "question": "测试",
            "project": {"model": "车型B", "_org_id": "org-b"},
            "references": [],
            "primary_output": "B客户结论",
            "conflict_status": "aligned",
        })

        self.assertIsNotNone(server.router_decision_payload(decision_id, "org-b"))
        self.assertIsNone(server.router_decision_payload(decision_id, "org-a"))


if __name__ == "__main__":
    unittest.main()
