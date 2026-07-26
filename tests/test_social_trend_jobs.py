import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Event

import server


class SocialTrendJobsTest(unittest.TestCase):
    def test_request_normalization_excludes_own_and_duplicate_competitors(self):
        normalized = server._normalize_social_trend_body({
            "keyword": "奥迪 E7X",
            "competitors": ["奥迪E7X", " 奔驰GLC EV ", "奔驰GLC  EV", "问界M7", "问界M7"],
        })
        self.assertEqual(normalized["keyword"], "奥迪 E7X")
        self.assertEqual(normalized["competitors"], ["奔驰GLC EV", "问界M7"])
        self.assertEqual(
            server._social_trend_job_request_key(normalized),
            server._social_trend_job_request_key({
                "keyword": "奥迪E7X",
                "competitors": ["奥迪 E7X", "奔驰GLC  EV", "问界M7", "问界 M7"],
            }),
        )

    def test_local_auto_update_defers_restart_while_collection_is_active(self):
        script = (Path(__file__).resolve().parents[1] / "scripts" / "ensure_local_mmn.sh").read_text(encoding="utf-8")
        self.assertIn("has_active_local_jobs", script)
        self.assertIn("activeLocalJobs", script)
        self.assertIn("activeSocialTrendJobs", script)
        self.assertIn("延后重启 MMN 本地服务", script)

    def test_health_restart_guard_counts_active_local_jobs(self):
        with server.SOCIAL_TREND_JOB_LOCK:
            server.SOCIAL_TREND_JOB_TASKS["guard-test"] = {"status": "running"}
        summary = server.active_local_job_summary()
        self.assertEqual(summary["byType"]["socialTrend"], 1)
        self.assertGreaterEqual(summary["total"], 1)

    def setUp(self):
        with server.SOCIAL_TREND_JOB_LOCK:
            self.original_jobs = dict(server.SOCIAL_TREND_JOB_TASKS)
            server.SOCIAL_TREND_JOB_TASKS.clear()

    def tearDown(self):
        with server.SOCIAL_TREND_JOB_LOCK:
            server.SOCIAL_TREND_JOB_TASKS.clear()
            server.SOCIAL_TREND_JOB_TASKS.update(self.original_jobs)

    def test_same_org_reuses_an_active_collection_job(self):
        started, release = Event(), Event()

        def runner(body, *, org_id, progress_callback):
            started.set()
            release.wait(2)
            return {"keyword": body["keyword"], "items": []}

        first = server.start_social_trend_job({"keyword": "车型A"}, org_id="org-a", runner=runner)
        self.assertTrue(started.wait(1))
        second = server.start_social_trend_job({"keyword": "车型A"}, org_id="org-a", runner=runner)
        self.assertEqual(second["jobId"], first["jobId"])
        with self.assertRaisesRegex(ValueError, "不同条件"):
            server.start_social_trend_job({"keyword": "车型B"}, org_id="org-a", runner=runner)
        release.set()
        for _ in range(20):
            job = server.get_social_trend_job(first["jobId"], "org-a")
            if job and job["status"] == "completed":
                break
            time.sleep(.02)
        self.assertEqual(job["status"], "completed")

    def test_pruning_drops_expired_completed_jobs_but_keeps_running_jobs(self):
        old = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat().replace("+00:00", "Z")
        with server.SOCIAL_TREND_JOB_LOCK:
            server.SOCIAL_TREND_JOB_TASKS.update({
                "old": {"jobId": "old", "status": "completed", "updatedAt": old},
                "active": {"jobId": "active", "status": "running", "updatedAt": old},
            })
            server._prune_social_trend_jobs()
        self.assertNotIn("old", server.SOCIAL_TREND_JOB_TASKS)
        self.assertIn("active", server.SOCIAL_TREND_JOB_TASKS)


if __name__ == "__main__":
    unittest.main()
