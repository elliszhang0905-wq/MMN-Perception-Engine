from pathlib import Path
import tempfile
import threading
import unittest
from unittest import mock

from geo.repository import GeoRepository, GeoError
try:
    from geo.worker import GeoWorker
    from geo.service import GeoService
except ImportError:
    GeoWorker = GeoService = None


class FixtureProvider:
    def __init__(self, results):
        self.results, self.calls = list(results), 0
    def sample(self, question, condition, cancel_event=None):
        self.calls += 1
        return {"raw_response": {"evidence_origin": "offline_fixture"},
                "finished_at": "2026-10-08T03:00:00+00:00", **self.results.pop(0)}


class GeoWorkerTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(GeoWorker, "GEO recoverable worker is not implemented")
        self.assertIsNotNone(GeoService, "GEO service quota/configuration gate is not implemented")
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.repo = GeoRepository(Path(self.temp.name) / "fixture.sqlite")
        self.project = self.repo.create_project("a", {"name": "离线测试", "target_key": "a", "entities": [{"key": "a", "name": "测试车型A", "market": "中国"}], "budget": {"batch_budget": 50, "day_budget": 50}})
        self.q = self.repo.add_question("a", self.project["id"], {"text": "有哪些车型值得考虑？", "recommendation_eligible": True})
        self.c = self.repo.add_condition("a", self.project["id"], {"surface": "ark_model_api", "api_mode": "responses", "mode": "non_search", "model": "fixture", "max_output_tokens": 32, "timeout_seconds": 2})
        self.policy = {"queue_allowed": True, "blocked_reasons": [], "attempt_reserve_micro": 1000000, "max_attempts": 3, "currency": "CNY", "pricing": {"version": "fixture-v1", "currency": "CNY", "input_per_million": 1000, "output_per_million": 1000}}
        self.settings = {"enabled": True, "real_sampling_enabled": True, "worker_mode": "external", "api_key": "fixture-only-no-network", "model": "fixture", "api_mode": "responses", "max_concurrency": 1}

    def batch(self, **kw):
        return self.repo.create_batch("a", self.project["id"], {"question_version_ids": [self.q["version_id"]], "condition_ids": [self.c["id"]], "repeats": 1, "idempotency_key": "first", **kw}, self.policy)

    def test_worker_costs_success_and_preserves_provenance(self):
        batch = self.batch()
        provider = FixtureProvider([{"status": "completed", "answer": "可以考虑测试车型A。", "usage": {"input_tokens": 10, "output_tokens": 20}, "request_id": "fixture-1", "billing_uncertain": False}])
        worker = GeoWorker(self.repo, self.settings, provider)
        self.assertTrue(worker.tick())
        self.assertFalse(worker.tick())
        observation = self.repo.list_observations("a", self.project["id"])["items"][0]
        self.assertTrue(observation["analysis"]["entities"][0]["recommended"])
        self.assertAlmostEqual(observation["attempts"][0]["cost"], 0.03)
        self.assertEqual(observation["evidence_origin"], "offline_fixture")
        self.assertEqual(self.repo.get_batch("a", batch["id"])["status"], "completed")

    def test_timeout_is_unknown_and_never_retried(self):
        self.batch()
        provider = FixtureProvider([{"status": "uncertain", "error_class": "timeout", "billing_uncertain": True, "usage": None}])
        worker = GeoWorker(self.repo, self.settings, provider)
        self.assertTrue(worker.tick()); self.assertFalse(worker.tick())
        observation = self.repo.list_observations("a", self.project["id"])["items"][0]
        self.assertEqual(observation["status"], "uncertain")
        self.assertEqual(provider.calls, 1)
        self.assertIsNone(observation["attempts"][0]["cost"])

    def test_analysis_failure_keeps_completed_raw_answer(self):
        self.batch()
        provider = FixtureProvider([{"status": "completed", "answer": "真实返回的原始回答", "usage": {"input_tokens": 10, "output_tokens": 20}, "billing_uncertain": False}])
        worker = GeoWorker(self.repo, self.settings, provider)
        with mock.patch("geo.worker.analyze_answer", side_effect=ValueError("offline analysis failure")):
            worker.tick()
        obs = self.repo.list_observations("a", self.project["id"])["items"][0]
        self.assertEqual(obs["answer"], "真实返回的原始回答")
        self.assertEqual(obs["status"], "completed")
        self.assertIsNone(obs["analysis"])
        self.assertIsNotNone(obs["raw_hash"])

    def test_authentication_failure_stops_batch_before_next_call(self):
        batch = self.batch(repeats=2)
        provider = FixtureProvider([{"status": "failed", "error_class": "authentication", "usage": None, "billing_uncertain": False}])
        worker = GeoWorker(self.repo, self.settings, provider)
        worker.tick()
        self.assertFalse(worker.tick())
        self.assertEqual(provider.calls, 1)
        self.assertEqual(self.repo.get_batch("a", batch["id"])["status"], "blocked")

    def test_stop_and_disabled_sampling_never_create_attempt(self):
        self.batch()
        provider = FixtureProvider([])
        worker = GeoWorker(self.repo, {**self.settings, "real_sampling_enabled": False}, provider)
        self.assertFalse(worker.tick())
        worker = GeoWorker(self.repo, self.settings, provider)
        worker.stop.set()
        self.assertFalse(worker.tick())
        self.assertEqual(provider.calls, 0)

    def test_service_preview_uses_missing_configuration_and_unknown_price(self):
        service = GeoService(self.repo, {"enabled": True, "real_sampling_enabled": False, "worker_mode": "off"})
        result = service.preview("a", self.project["id"], {"question_version_ids": [self.q["version_id"]], "condition_ids": [self.c["id"]], "repeats": 3})
        self.assertEqual(result["planned_calls"], 3)
        self.assertIsNone(result["estimated_cost"])
        self.assertTrue(result["blocked_reasons"])

    def test_cancellation_after_claim_before_sample_sends_no_request(self):
        batch = self.batch()
        provider = FixtureProvider([{"status": "completed", "answer": "不应发出", "usage": {"input_tokens": 1, "output_tokens": 1}, "billing_uncertain": False}])
        worker = GeoWorker(self.repo, self.settings, provider)
        original = self.repo.claim_next
        def claim_then_cancel(*args, **kwargs):
            claim = original(*args, **kwargs)
            self.repo.control_batch("a", batch["id"], "cancel")
            return claim
        with mock.patch.object(self.repo, "claim_next", side_effect=claim_then_cancel):
            worker.tick()
        self.assertEqual(provider.calls, 0)


if __name__ == "__main__": unittest.main()
