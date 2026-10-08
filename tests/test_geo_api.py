from pathlib import Path
import hashlib
import sqlite3
import tempfile
import unittest

from geo.repository import GeoRepository, GeoError
try:
    from geo.api import execute
except ImportError:
    execute = None


class GeoApiTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(execute, "GEO authenticated API dispatch not implemented")
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "isolated.sqlite"
        self.settings = {"enabled": True, "real_sampling_enabled": False, "worker_mode": "off", "api_mode": "responses",
                         "db_path": str(self.path),
                         "max_questions": 50, "max_repeats": 5, "max_concurrency": 1, "max_output_tokens": 2048,
                         "day_budget": 0, "batch_budget": 0, "configuration_errors": []}
        self.auth = {"org_id": "tenant-a", "role": "admin", "user_id": "reviewer-a"}
        self.repo = GeoRepository(self.path)
        self.project = self.repo.create_project("tenant-a", {"name": "API fixture", "target_key": "a", "entities": [{"key": "a", "name": "测试车型A"}]})
        self.q = self.repo.add_question("tenant-a", self.project["id"], {"text": "推荐哪些车型？", "unbranded": True, "recommendation_eligible": True})

    def request(self, method, suffix, body=None, auth=None, query=None):
        return execute(method, "/api/geo" + suffix, query or {}, body or {}, auth or self.auth, Path(self.temp.name) / "business.sqlite", self.settings)

    def test_metric_evidence_scope_excludes_other_actual_models_and_stale_tokens(self):
        for model in ["offline-version-1", "offline-version-2"]:
            self.request("POST", f"/projects/{self.project['id']}/app-imports", {
                "question_version_id": self.q["version_id"], "question_text": self.q["text"],
                "answer": "可以考虑测试车型A。", "sampled_at": "2026-10-08T01:00:00+00:00",
                "actual_model": model, "visible_search": "off",
            })
        metrics, _ = self.request("GET", f"/projects/{self.project['id']}/metrics")
        self.assertEqual(len(metrics["groups"]), 2)
        group = metrics["groups"][0]
        result, _ = self.request("GET", f"/projects/{self.project['id']}/observations", query={"metric_scope": [group["evidence_scope_hash"]]})
        self.assertEqual({x["id"] for x in result["items"]}, set(group["observation_ids"]))
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["entities"][0]["name"], "测试车型A")
        with self.assertRaises(GeoError):
            self.request("GET", f"/projects/{self.project['id']}/observations", query={"metric_scope": ["stale-scope"]})

    def test_metric_evidence_retains_original_filtered_batch_scope(self):
        samples = []
        for _ in range(2):
            sample, _ = self.request("POST", f"/projects/{self.project['id']}/app-imports", {
                "question_version_id": self.q["version_id"], "question_text": self.q["text"],
                "answer": "可以考虑测试车型A。", "actual_model": "offline-version-1",
                "sampled_at": "2026-10-08T01:00:00+00:00", "visible_search": "off",
            })
            samples.append(sample)
        batch_id = samples[0]["batch_id"]
        metrics, _ = self.request("GET", f"/projects/{self.project['id']}/metrics", query={"batch_id": [batch_id]})
        group = metrics["groups"][0]
        result, _ = self.request("GET", f"/projects/{self.project['id']}/observations", query={"metric_scope": [group["evidence_scope_hash"]], "batch_id": [batch_id]})
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["items"][0]["id"], samples[0]["id"])

    def test_non_cny_prices_cannot_reinterpret_cny_project_limits(self):
        self.settings.update({"real_sampling_enabled": True, "worker_mode": "external", "api_key": "offline-only", "model": "fixture-endpoint",
            "pricing": {"version": "offline-v1", "currency": "USD", "model": "fixture-endpoint", "priced_at": "2026-10-08", "source_url": "https://example.com/price", "input_per_million": 1, "output_per_million": 1, "input_token_ceiling": 10000}})
        self.repo.update_budget("tenant-a", self.project["id"], {"batch_budget": 50, "day_budget": 50})
        condition, _ = self.request("POST", f"/projects/{self.project['id']}/conditions", {"surface": "ark_model_api", "mode": "non_search"})
        preview, _ = self.request("POST", f"/projects/{self.project['id']}/batches/preview", {"question_version_ids": [self.q["version_id"]], "condition_ids": [condition["id"]], "repeats": 1, "idempotency_key": "currency-check"})
        self.assertIn("预算币种", " ".join(preview["blocked_reasons"]))

    def test_cross_tenant_ids_stats_and_export_denied(self):
        other = {"org_id": "tenant-b", "role": "admin", "user_id": "b"}
        for suffix in [f"/projects/{self.project['id']}/questions", f"/projects/{self.project['id']}/metrics", f"/projects/{self.project['id']}/export"]:
            with self.assertRaises(GeoError): self.request("GET", suffix, auth=other)
        with self.assertRaises(GeoError): self.request("POST", "/projects", {"org_id": "tenant-b"})

    def test_viewer_can_read_but_cannot_mutate_or_get_raw(self):
        viewer = {**self.auth, "role": "trial"}
        result = self.request("GET", "/projects", auth=viewer)
        self.assertEqual(result[0]["items"][0]["id"], self.project["id"])
        with self.assertRaises(GeoError):
            self.request("POST", f"/projects/{self.project['id']}/questions", {"text": "新问题？"}, viewer)

    def test_offline_condition_and_batch_are_real_blocked_plan(self):
        condition, _ = self.request("POST", f"/projects/{self.project['id']}/conditions", {"surface": "ark_model_api", "api_mode": "responses", "mode": "non_search", "max_output_tokens": 128, "timeout_seconds": 3})
        body = {"question_version_ids": [self.q["version_id"]], "condition_ids": [condition["id"]], "repeats": 3, "idempotency_key": "offline"}
        preview, _ = self.request("POST", f"/projects/{self.project['id']}/batches/preview", body)
        self.assertEqual(preview["planned_calls"], 3)
        self.assertIsNone(preview["estimated_cost"])
        batch, _ = self.request("POST", f"/projects/{self.project['id']}/batches", body)
        self.assertEqual(batch["status"], "blocked")
        self.assertIsNone(self.repo.claim_next("never-call"))

    def test_csv_formula_safe_and_failed_import_transactional(self):
        self.repo.add_question("tenant-a", self.project["id"], {"text": "=HYPERLINK(\"https://example.com\")"})
        exported, _ = self.request("GET", f"/projects/{self.project['id']}/export", query={"kind": ["questions"]})
        self.assertIn("'=HYPERLINK", exported["csv"])
        before = self.repo.list_questions("tenant-a", self.project["id"])["total"]
        with self.assertRaises(GeoError):
            self.request("POST", f"/projects/{self.project['id']}/questions/import", {"csv": "text,category\n有效问题,category\n错误问题,bad_category\n"})
        self.assertEqual(self.repo.list_questions("tenant-a", self.project["id"])["total"], before)

    def test_disabled_module_does_not_migrate_database(self):
        fresh = Path(self.temp.name) / "not-created.sqlite"
        result, _ = execute("GET", "/api/geo/capabilities", {}, {}, self.auth, fresh, {"enabled": False})
        self.assertFalse(result["enabled"])
        self.assertFalse(fresh.exists())
        with self.assertRaises(GeoError):
            execute("GET", "/api/geo/projects", {}, {}, self.auth, fresh, {"enabled": False})
        self.assertFalse(fresh.exists())

    def test_blank_unapproved_budget_allows_offline_project_only(self):
        project, _ = self.request("POST", "/projects", {"name": "尚无批准预算", "target_key": "a", "entities": [{"key": "a", "name": "车型A"}], "budget": {"batch_budget": None, "day_budget": None, "max_questions": 50, "max_repeats": 3, "max_concurrency": 1, "max_output_tokens": 2048}})
        self.assertEqual(project["budget"]["batch_budget"], 0)
        self.assertEqual(project["budget"]["day_budget"], 0)

    def test_api_workflow_full_text_review_action_and_retest(self):
        obs, _ = self.request("POST", f"/projects/{self.project['id']}/app-imports", {
            "question_version_id": self.q["version_id"], "question_text": self.q["text"],
            "answer": "可以考虑测试车型A。", "sampled_at": "2026-10-08T01:00:00+00:00",
            "new_session": True, "personalization": "off", "visible_search": "off", "actual_model": "offline-recorded-model",
        })
        review, _ = self.request("POST", f"/observations/{obs['id']}/reviews", {"kind": "entity", "entity_key": "a", "changes": {"recommended": False, "needs_review": False}, "reason": "离线人工标注核验"})
        detail, _ = self.request("GET", f"/observations/{obs['id']}")
        self.assertFalse(detail["analysis"]["entities"][0]["recommended"])
        self.assertEqual(detail["raw_hash"], obs["raw_hash"])
        viewer, _ = self.request("GET", f"/observations/{obs['id']}", auth={**self.auth, "role": "trial"})
        self.assertNotIn("raw_response", viewer)
        action, _ = self.request("POST", f"/projects/{self.project['id']}/actions", {"title": "补充事实材料", "diagnosis": "离线测试假设", "observation_ids": [obs["id"]], "status": "draft"})
        self.request("POST", f"/actions/{action['id']}", {"status": "approved"})
        self.request("POST", f"/actions/{action['id']}", {"status": "executed", "execution_evidence": "仅离线动作记录，不代表已发布", "executed_at": "2026-10-08T02:00:00+00:00"})
        retest, _ = self.request("POST", f"/actions/{action['id']}/retest", {"baseline_batch_id": obs["batch_id"], "idempotency_key": "retest-1"})
        self.assertEqual(self.repo.get_batch("tenant-a", retest["batch_id"])["status"], "draft")
        self.assertTrue(retest["manual"])

    def test_cockpit_requires_diagnostic_review_and_invalidates_stale_review(self):
        obs, _ = self.request("POST", f"/projects/{self.project['id']}/app-imports", {
            "question_version_id": self.q["version_id"], "question_text": self.q["text"],
            "answer": "可以考虑其他候选车型，先查阅官方资料。", "sampled_at": "2026-10-08T01:00:00+00:00",
        })
        self.request("POST", f"/observations/{obs['id']}/reviews", {"kind": "entity", "entity_key": "a", "changes": {"needs_review": False}, "reason": "仅复核提及，不等于审批诊断"})
        summary, _ = self.request("GET", f"/projects/{self.project['id']}/cockpit-summary")
        self.assertEqual(summary["reviewed_diagnostic_n"], 0)
        diagnostics, _ = self.request("GET", f"/projects/{self.project['id']}/diagnostics")
        item = diagnostics["items"][0]
        self.request("POST", f"/projects/{self.project['id']}/diagnostics/reviews", {"diagnostic_id": item["id"], "source_hash": item["source_hash"], "decision": "accepted", "reason": "人工审核诊断与建议"})
        summary, _ = self.request("GET", f"/projects/{self.project['id']}/cockpit-summary")
        self.assertEqual(summary["reviewed_diagnostic_n"], 1)
        self.assertEqual(summary["reviewed_diagnostics"][0]["reviewer"], "reviewer-a")
        self.request("POST", f"/observations/{obs['id']}/reviews", {"kind": "entity", "entity_key": "a", "changes": {"needs_review": True}, "reason": "原证据需要再次核实"})
        summary, _ = self.request("GET", f"/projects/{self.project['id']}/cockpit-summary")
        self.assertEqual(summary["reviewed_diagnostic_n"], 0)

    def test_retest_alternate_search_condition_rechecks_live_and_cost_gates(self):
        self.settings.update({"real_sampling_enabled": True, "worker_mode": "external", "api_key": "offline-only", "model": "fixture-endpoint", "batch_budget": 50, "day_budget": 50,
            "pricing": {"version": "offline-price-v1", "currency": "CNY", "model": "fixture-endpoint", "priced_at": "2026-10-08", "source_url": "https://example.com/offline-price", "input_per_million": 1, "output_per_million": 1, "input_token_ceiling": 10000}})
        self.repo.update_budget("tenant-a", self.project["id"], {"batch_budget": 50, "day_budget": 50})
        base, _ = self.request("POST", f"/projects/{self.project['id']}/conditions", {"surface": "ark_model_api", "mode": "non_search"})
        searched, _ = self.request("POST", f"/projects/{self.project['id']}/conditions", {"surface": "ark_model_api", "mode": "search_enabled"})
        batch, _ = self.request("POST", f"/projects/{self.project['id']}/batches", {"question_version_ids": [self.q["version_id"]], "condition_ids": [base["id"]], "repeats": 1, "idempotency_key": "baseline-no-network"})
        claim = self.repo.claim_next("offline-fixture")
        self.repo.finish_attempt("tenant-a", claim["observation"]["id"], "offline-fixture", {"status": "completed", "answer": "可以考虑测试车型A。", "cost": 0.01, "billing_uncertain": False, "actual_model": "fixture-endpoint", "finished_at": "2026-10-08T01:00:00+00:00", "raw_response": {"evidence_origin": "offline_fixture"}}, analysis={"valid_answer": True, "entities": [{"entity_key": "a", "mentioned": True, "recommended": True}]})
        action, _ = self.request("POST", f"/projects/{self.project['id']}/actions", {"title": "离线改进任务", "observation_ids": [claim["observation"]["id"]], "status": "draft"})
        self.request("POST", f"/actions/{action['id']}", {"status": "approved"})
        self.request("POST", f"/actions/{action['id']}", {"status": "executed", "execution_evidence": "离线执行声明", "executed_at": "2026-10-08T02:00:00+00:00"})
        retest, _ = self.request("POST", f"/actions/{action['id']}/retest", {"baseline_batch_id": batch["id"], "condition_ids": [searched["id"]], "idempotency_key": "alternate-search"})
        new_batch = self.repo.get_batch("tenant-a", retest["batch_id"])
        self.assertEqual(new_batch["status"], "blocked")
        self.assertIn("联网工具次数", " ".join(new_batch["manifest"]["blocked_reasons"]))
        self.assertIsNone(self.repo.claim_next("must-not-dispatch"))

    def test_diagnostic_acceptance_publishes_exact_modified_snapshot(self):
        obs, _ = self.request("POST", f"/projects/{self.project['id']}/app-imports", {"question_version_id": self.q["version_id"], "question_text": self.q["text"], "answer": "可以考虑其他候选。", "sampled_at": "2026-10-08T01:00:00+00:00"})
        path = f"/projects/{self.project['id']}/diagnostics"
        first = self.request("GET", path)[0]["items"][0]
        self.request("POST", path + "/reviews", {"diagnostic_id": first["id"], "source_hash": first["source_hash"], "decision": "modified", "changes": {"label": "人工修改确认的诊断"}, "reason": "人工修改"})
        current = self.request("GET", path)[0]["items"][0]
        self.request("POST", path + "/reviews", {"diagnostic_id": current["id"], "source_hash": current["source_hash"], "decision": "accepted", "reason": "接受当前修改稿"})
        summary = self.request("GET", f"/projects/{self.project['id']}/cockpit-summary")[0]
        self.assertEqual(summary["reviewed_diagnostics"][0]["label"], "人工修改确认的诊断")
        latest = self.request("GET", path)[0]["items"][0]
        self.request("POST", path + "/reviews", {"diagnostic_id": latest["id"], "source_hash": latest["source_hash"], "decision": "modified", "changes": {"action_suggestion": "人工保留的补证假设"}, "reason": "仅调整建议"})
        self.assertEqual(self.request("GET", path)[0]["items"][0]["label"], "人工修改确认的诊断")
        with self.assertRaises(GeoError):
            self.request("POST", path + "/reviews", {"diagnostic_id": first["id"], "source_hash": first["source_hash"], "decision": "accepted", "reason": "旧页面不能批准新稿"})


class GeoIsolatedDatabaseTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.business = Path(self.temp.name) / "business.sqlite"
        self.geo = Path(self.temp.name) / "geo.sqlite"
        with sqlite3.connect(self.business) as conn:
            conn.execute("CREATE TABLE vehicle_assets(id TEXT,org_id TEXT,edition TEXT,brand_name TEXT,model_name TEXT)")
            conn.executemany("INSERT INTO vehicle_assets VALUES(?,?,?,?,?)", [
                ("a", "tenant-a", "china", "品牌A", "测试车型A"),
                ("b", "tenant-b", "china", "品牌B", "测试车型B"),
                ("c", "tenant-a", "global", "品牌C", "测试车型C"),
            ])
        self.before = hashlib.sha256(self.business.read_bytes()).hexdigest()
        self.settings = {"enabled": True, "real_sampling_enabled": False, "worker_mode": "off", "db_path": str(self.geo)}
        self.auth = {"org_id": "tenant-a", "role": "admin", "user_id": "reviewer"}

    def assert_business_preserved(self):
        self.assertEqual(hashlib.sha256(self.business.read_bytes()).hexdigest(), self.before)
        with sqlite3.connect(self.business.resolve().as_uri() + "?mode=ro", uri=True) as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM sqlite_master WHERE name LIKE 'geo_%'").fetchone()[0], 0)

    def test_project_write_uses_only_configured_geo_database(self):
        project, status = execute("POST", "/api/geo/projects", {}, {
            "name": "隔离验收", "target_key": "a", "entities": [{"key": "a", "name": "测试车型A"}],
        }, self.auth, self.business, self.settings)
        self.assertEqual(status, 201)
        self.assertTrue(self.geo.is_file())
        self.assertEqual(GeoRepository(self.geo).get_project("tenant-a", project["id"])["name"], "隔离验收")
        self.assert_business_preserved()

    def test_catalog_reads_business_database_with_tenant_and_edition_scope(self):
        catalog, status = execute("GET", "/api/geo/catalog", {"edition": ["china"]}, {}, self.auth, self.business, self.settings)
        self.assertEqual(status, 200)
        self.assertEqual(catalog["total"], 1)
        self.assertEqual(catalog["items"][0]["name"], "测试车型A")
        self.assertFalse(self.geo.exists())
        self.assert_business_preserved()

    def test_disabled_module_does_not_create_configured_database(self):
        settings = {**self.settings, "enabled": False}
        data, status = execute("GET", "/api/geo/capabilities", {}, {}, self.auth, self.business, settings)
        self.assertEqual(status, 200)
        self.assertFalse(data["enabled"])
        with self.assertRaises(GeoError):
            execute("GET", "/api/geo/projects", {}, {}, self.auth, self.business, settings)
        self.assertFalse(self.geo.exists())
        self.assert_business_preserved()

    def test_missing_geo_path_refuses_access_before_business_migration(self):
        with self.assertRaises(GeoError):
            execute("GET", "/api/geo/projects", {}, {}, self.auth, self.business, {**self.settings, "db_path": ""})
        self.assertFalse(self.geo.exists())
        self.assert_business_preserved()

    def test_business_database_cannot_be_configured_as_geo_storage(self):
        with self.assertRaises(GeoError):
            execute("GET", "/api/geo/projects", {}, {}, self.auth, self.business, {**self.settings, "db_path": str(self.business)})
        self.assert_business_preserved()

    def test_hardlink_to_business_database_is_also_rejected(self):
        self.geo.hardlink_to(self.business)
        with self.assertRaises(GeoError):
            execute("GET", "/api/geo/projects", {}, {}, self.auth, self.business, self.settings)
        self.assert_business_preserved()


if __name__ == "__main__": unittest.main()
