import threading
import time
import unittest

from server import get_opportunity_map_job, start_opportunity_map_job


class OpportunityMapJobTest(unittest.TestCase):
    def wait_for(self, job_id, status, timeout=1.5):
        deadline = time.time() + timeout
        while time.time() < deadline:
            job = get_opportunity_map_job(job_id)
            if job and job.get("status") == status:
                return job
            time.sleep(0.01)
        self.fail(f"job {job_id} did not reach {status}: {get_opportunity_map_job(job_id)}")

    def test_job_returns_immediately_and_reports_pipeline_progress(self):
        reached_model = threading.Event()
        release_model = threading.Event()

        def runner(body, *, org_id, user_id, run_id, progress_callback):
            progress_callback("official_sources", 25, "正在核验 4 个竞品官网")
            progress_callback("primary_model", 52, "MMN旗舰模型 A 正在独立分析")
            reached_model.set()
            release_model.wait(1)
            progress_callback("cross_validation", 90, "正在交叉验证双模型结论")
            return {"ok": True, "runId": run_id, "status": "manual_required"}

        started_at = time.monotonic()
        accepted = start_opportunity_map_job(
            {"documentId": "doc-1"},
            org_id="local",
            user_id="tester",
            runner=runner,
        )
        self.assertLess(time.monotonic() - started_at, 0.25)
        self.assertIn(accepted["status"], {"queued", "running"})
        self.assertTrue(reached_model.wait(1))

        running = get_opportunity_map_job(accepted["jobId"])
        self.assertEqual(running["status"], "running")
        self.assertEqual(running["stage"], "primary_model")
        self.assertEqual(running["progress"], 52)
        self.assertIn("旗舰模型 A", running["message"])

        release_model.set()
        completed = self.wait_for(accepted["jobId"], "completed")
        self.assertEqual(completed["progress"], 100)
        self.assertEqual(completed["result"]["runId"], accepted["jobId"])

    def test_job_failure_is_queryable(self):
        def runner(*args, **kwargs):
            raise RuntimeError("模型网关暂时不可用")

        accepted = start_opportunity_map_job(
            {"documentId": "doc-2"},
            runner=runner,
        )
        failed = self.wait_for(accepted["jobId"], "failed")
        self.assertEqual(failed["stage"], "failed")
        self.assertIn("模型网关暂时不可用", failed["error"])


if __name__ == "__main__":
    unittest.main()
