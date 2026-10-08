import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

try:
    from geo.repository import GeoRepository, GeoError
except ImportError:
    GeoRepository = GeoError = None


class GeoRepositoryTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(GeoRepository, "GEO tenant/version/job repository is not implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = GeoRepository(Path(self.temp.name) / "test.sqlite")
        self.project = self.repo.create_project("tenant-a", {
            "name": "离线测试项目", "target_key": "a",
            "entities": [{"key": "a", "name": "测试车型A", "brand": "测试品牌"},
                         {"key": "b", "name": "测试车型B", "brand": "另一品牌"}],
            "budget": {"batch_budget": 50, "day_budget": 50},
        }, actor="reviewer-a")
        self.pid = self.project["id"]
        self.q = self.repo.add_question("tenant-a", self.pid, {
            "text": "通勤可以考虑哪些车型？", "category": "category",
            "unbranded": True, "recommendation_eligible": True,
        })
        self.condition = self.repo.add_condition("tenant-a", self.pid, {
            "surface": "ark_model_api", "api_mode": "responses", "mode": "non_search",
            "model": "test-endpoint", "max_output_tokens": 32, "timeout_seconds": 2,
            "system_prompt_version": "neutral-v1", "capabilities": {},
        })
        self.policy = {"queue_allowed": True, "blocked_reasons": [],
                       "attempt_reserve_micro": 1000000, "max_attempts": 3,
                       "currency": "CNY", "pricing": {"version": "fixture-v1"}}

    def batch(self, key="key-1", **changes):
        payload = {"question_version_ids": [self.q["version_id"]],
                   "condition_ids": [self.condition["id"]], "repeats": 1,
                   "idempotency_key": key, **changes}
        return self.repo.create_batch("tenant-a", self.pid, payload, self.policy)

    def test_versions_and_entity_scope_are_frozen(self):
        batch = self.batch()
        edited = self.repo.add_question("tenant-a", self.pid, {"text": "改成另一问题？"},
                                        question_id=self.q["id"])
        self.repo.update_entities("tenant-a", self.pid, [{"key": "a", "name": "新别名"},
                                                        {"key": "b", "name": "测试车型B"}])
        frozen = self.repo.get_batch("tenant-a", batch["id"])["manifest"]
        self.assertEqual(frozen["questions"][0]["text"], "通勤可以考虑哪些车型？")
        self.assertEqual(frozen["entities"][0]["name"], "测试车型A")
        self.assertEqual(edited["version"], 2)
        self.assertNotEqual(edited["version_id"], self.q["version_id"])

    def test_idempotency_reuses_batch_and_rejects_changed_request(self):
        first = self.batch()
        self.assertEqual(first["id"], self.batch()["id"])
        with self.assertRaises(GeoError):
            self.batch(repeats=2)
        self.assertEqual(self.repo.list_batches("tenant-a", self.pid)["total"], 1)

    def test_foreign_tenant_and_same_tenant_other_project_are_denied(self):
        batch = self.batch()
        for getter, ident in [(self.repo.get_project, self.pid),
                             (self.repo.get_batch, batch["id"]),
                             (self.repo.get_observation, self.repo.list_observations("tenant-a", self.pid)["items"][0]["id"])]:
            with self.assertRaises(GeoError):
                getter("tenant-b", ident)
        other = self.repo.create_project("tenant-a", {"name": "another", "target_key": "x",
                                                     "entities": [{"key": "x", "name": "车型X"}]})
        with self.assertRaises(GeoError):
            self.repo.create_batch("tenant-a", other["id"], {
                "question_version_ids": [self.q["version_id"]],
                "condition_ids": [self.condition["id"]], "repeats": 1,
                "idempotency_key": "foreign-project",
            }, self.policy)

    def test_concurrent_claim_creates_one_network_attempt(self):
        self.batch()
        claims = []
        barrier = threading.Barrier(2)
        def run(owner):
            barrier.wait()
            claims.append(self.repo.claim_next(owner))
        threads = [threading.Thread(target=run, args=(x,)) for x in ["worker-a", "worker-b"]]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        self.assertEqual(len([c for c in claims if c]), 1)
        obs = self.repo.list_observations("tenant-a", self.pid)["items"][0]
        self.assertEqual(len(self.repo.get_observation("tenant-a", obs["id"])["attempts"]), 1)

    def test_stale_inflight_attempt_becomes_uncertain_without_reissue(self):
        batch = self.batch()
        claim = self.repo.claim_next("dead-worker", now_epoch=100, lease_seconds=10)
        self.assertIsNotNone(claim)
        self.assertIsNone(self.repo.claim_next("new-worker", now_epoch=111))
        observation = self.repo.get_observation("tenant-a", claim["observation"]["id"])
        self.assertEqual(observation["status"], "uncertain")
        self.assertTrue(observation["attempts"][0]["billing_uncertain"])
        self.assertEqual(len(observation["attempts"]), 1)
        self.assertEqual(self.repo.get_batch("tenant-a", batch["id"])["status"], "completed_with_errors")

    def test_cancel_preserves_inflight_success_and_stops_new_calls(self):
        batch = self.batch(repeats=2)
        claim = self.repo.claim_next("worker")
        self.repo.control_batch("tenant-a", batch["id"], "cancel", actor="reviewer-a")
        self.repo.finish_attempt("tenant-a", claim["observation"]["id"], "worker", {
            "status": "completed", "answer": "可以考虑测试车型A。", "request_id": "fixture",
            "raw_response": {"origin": "offline_fixture"}, "cost": 0.25,
            "billing_uncertain": False,
        }, analysis={"version": "fixture", "valid_answer": True, "entities": []})
        self.assertIsNone(self.repo.claim_next("worker-2"))
        preserved = self.repo.get_observation("tenant-a", claim["observation"]["id"])
        self.assertEqual(preserved["answer"], "可以考虑测试车型A。")
        self.assertEqual(self.repo.get_batch("tenant-a", batch["id"])["status"], "cancelled")

    def test_retry_costs_belong_to_attempts_not_experiment_repeats(self):
        self.batch()
        first = self.repo.claim_next("worker")
        self.repo.finish_attempt("tenant-a", first["observation"]["id"], "worker", {
            "status": "failed", "error_class": "rate_limit", "cost": 0.1,
            "billing_uncertain": False, "retry_after": 0,
        }, retry_delay=0)
        second = self.repo.claim_next("worker")
        self.assertEqual(first["observation"]["id"], second["observation"]["id"])
        self.repo.finish_attempt("tenant-a", second["observation"]["id"], "worker", {
            "status": "completed", "answer": "回答", "cost": 0.2,
            "raw_response": {"origin": "offline_fixture"}, "billing_uncertain": False,
        }, analysis={"valid_answer": True, "entities": []})
        rows = self.repo.list_observations("tenant-a", self.pid)
        self.assertEqual(rows["total"], 1)
        details = self.repo.get_observation("tenant-a", rows["items"][0]["id"])
        self.assertEqual(len(details["attempts"]), 2)
        self.assertAlmostEqual(sum(a["cost"] for a in details["attempts"]), 0.3)

    def test_atomic_day_budget_reservation_cannot_be_bypassed_by_two_batches(self):
        self.repo.update_budget("tenant-a", self.pid, {"batch_budget": 5, "day_budget": 5})
        self.batch(key="first")
        with self.assertRaises(GeoError):
            self.batch(key="second")
        self.assertEqual(self.repo.list_batches("tenant-a", self.pid)["total"], 1)

    def test_missing_price_creates_blocked_plan_with_unknown_cost(self):
        result = self.repo.create_batch("tenant-a", self.pid, {
            "question_version_ids": [self.q["version_id"]], "condition_ids": [self.condition["id"]],
            "repeats": 1, "idempotency_key": "blocked",
        }, {"queue_allowed": False, "blocked_reasons": ["单价未配置"], "currency": "CNY"})
        self.assertEqual(result["status"], "blocked")
        self.assertIsNone(result["estimated_cost"])
        self.assertIsNone(self.repo.claim_next("worker"))

    def test_explicit_failed_retry_keeps_same_observation_and_new_attempt(self):
        batch = self.batch()
        claim = self.repo.claim_next("worker")
        self.repo.finish_attempt("tenant-a", claim["observation"]["id"], "worker", {
            "status": "failed", "error_class": "authentication", "cost": 0.1, "billing_uncertain": False,
        })
        self.repo.control_batch("tenant-a", batch["id"], "retry", actor="reviewer-a", reason="凭证已修正", policy=self.policy)
        retry = self.repo.claim_next("worker-2")
        self.assertEqual(retry["observation"]["id"], claim["observation"]["id"])
        self.assertNotEqual(retry["attempt_id"], claim["attempt_id"])

    def test_uncertain_resample_is_linked_and_does_not_erase_unknown_cost(self):
        batch = self.batch()
        claim = self.repo.claim_next("worker")
        self.repo.finish_attempt("tenant-a", claim["observation"]["id"], "worker", {
            "status": "uncertain", "error_class": "timeout", "cost": None, "billing_uncertain": True,
            "raw_response": {"partial": "保留原调用"},
        })
        resample = self.repo.control_batch("tenant-a", batch["id"], "resolve_uncertain", observation_id=claim["observation"]["id"], actor="reviewer-a", reason="人工决定另起关联采样", policy=self.policy)
        self.assertNotEqual(resample["id"], batch["id"])
        self.assertEqual(resample["manifest"]["linked_observation_id"], claim["observation"]["id"])
        old = self.repo.get_observation("tenant-a", claim["observation"]["id"])
        self.assertEqual(old["status"], "uncertain")
        self.assertIsNone(old["attempts"][0]["cost"])

    def test_rollover_keeps_old_day_inflight_reservation_until_settled(self):
        self.repo.update_budget("tenant-a", self.pid, {"max_concurrency": 2})
        with patch("geo.jobs.day_key", return_value="2026-10-08"):
            batch = self.batch(repeats=2)
            old = self.repo.claim_next("old-day")
        with patch("geo.jobs.day_key", return_value="2026-10-09"):
            new = self.repo.claim_next("new-day")
        self.assertIsNotNone(new)
        self.repo.finish_attempt("tenant-a", old["observation"]["id"], "old-day", {
            "status": "completed", "answer": "保存跨日原回答", "cost": 0.25,
            "raw_response": {"request_id": "before-midnight"}, "request_id": "before-midnight", "billing_uncertain": False,
        }, analysis={"valid_answer": True, "entities": []})
        result = self.repo.get_observation("tenant-a", old["observation"]["id"])
        self.assertEqual(result["answer"], "保存跨日原回答")
        self.assertEqual(result["request_id"], "before-midnight")

    def test_over_budget_settlement_stops_other_batches_in_project(self):
        self.repo.update_budget("tenant-a", self.pid, {"batch_budget": 20, "day_budget": 6})
        self.batch("first"); self.batch("second")
        claim = self.repo.claim_next("worker")
        self.repo.finish_attempt("tenant-a", claim["observation"]["id"], "worker", {
            "status": "completed", "answer": "已发生费用", "cost": 10, "billing_uncertain": False,
            "raw_response": {"source": "offline_fixture"},
        }, analysis={"valid_answer": True, "entities": []})
        self.assertIsNone(self.repo.claim_next("another-worker"))

    def test_uncertain_resample_obeys_current_lowered_project_budget(self):
        batch = self.batch()
        claim = self.repo.claim_next("worker")
        self.repo.finish_attempt("tenant-a", claim["observation"]["id"], "worker", {
            "status": "uncertain", "cost": None, "billing_uncertain": True,
        })
        self.repo.update_budget("tenant-a", self.pid, {"batch_budget": 1, "day_budget": 1})
        with self.assertRaises(GeoError):
            self.repo.control_batch("tenant-a", batch["id"], "resolve_uncertain", observation_id=claim["observation"]["id"], reason="另起采样", policy=self.policy)

    def test_question_boolean_and_related_entities_validation(self):
        for payload in [{"text": "问题", "unbranded": "false"},
                        {"text": "问题", "target_entities": ["foreign"]},
                        {"text": ""}]:
            with self.assertRaises(GeoError):
                self.repo.add_question("tenant-a", self.pid, payload)

    def test_unknown_search_mode_is_only_valid_for_manual_app(self):
        manual = self.repo.add_condition("tenant-a", self.pid, {
            "surface": "doubao_app_manual", "api_mode": "manual", "mode": "unknown",
        })
        self.assertEqual(manual["mode"], "unknown")
        for api_mode, surface in [("responses", "ark_model_api"), ("assistant", "ark_assistant_api")]:
            with self.assertRaises(GeoError):
                self.repo.add_condition("tenant-a", self.pid, {
                    "surface": surface, "api_mode": api_mode, "mode": "unknown",
                })

    def test_example_questions_are_exactly_50_without_fake_answers(self):
        self.assertEqual(self.repo.seed_examples("tenant-a", self.pid)["created"], 50)
        examples = self.repo.list_questions("tenant-a", self.pid, limit=100)["items"]
        counts = {}
        for item in examples:
            if item["source"] == "editable_example_not_user_research":
                counts[item["category"]] = counts.get(item["category"], 0) + 1
        self.assertEqual(counts, {"category": 15, "scenario": 10, "comparison": 10, "recognition": 10, "concern": 5})
        self.assertEqual(self.repo.list_observations("tenant-a", self.pid)["total"], 0)


if __name__ == "__main__":
    unittest.main()
