"""Exercise the scheduler's Bash flow and signed HTTP client without real services.

Only the log root and infinite loop bound are changed in the temporary copy.
Time/sleep and urllib transport are fixtures; the scheduling and response code
under test are the production script, not a second implementation.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import re
import shlex
from concurrent.futures import ThreadPoolExecutor


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/run_scheduler.sh"


class WeeklyRefreshSchedulerTests(unittest.TestCase):
    def test_log_timestamps_use_a_host_supported_date_format(self):
        commands = re.findall(r"\$\((date [^)]*)\)", SCRIPT.read_text())
        self.assertTrue(commands)
        for command in set(commands):
            result = subprocess.run(shlex.split(command), capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertRegex(result.stdout, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.logs = self.root / "logs"
        self.calls = self.root / "calls.jsonl"
        self.script = self.root / "scheduler.sh"
        self.script.write_text(SCRIPT.read_text().replace("/app/logs", str(self.logs)).replace(
            "while true; do", "for scheduler_test_iteration in 1; do"))
        self.shell_env = self.root / "shell-env.sh"
        self.shell_env.write_text('''
date() {
  case "$*" in
    '+%u %H:%M') echo "$TEST_DAY $TEST_TIME";;
    '+%u') echo "$TEST_DAY";;
    '+%H:%M') echo "$TEST_TIME";;
    '+%Y-%m') echo '2026-09';;
    '+%d %H:%M') echo "22 $TEST_TIME";;
    '+%d') echo '22';;
    '+%G-W%V') echo '2026-W39';;
    '+%Y-%m-%d') echo "2026-09-2$TEST_DAY";;
    *) echo '2026-09-22T00:01:00+08:00';;
  esac
}
sleep() { :; }
python3() { "$TEST_PYTHON" "$@"; }
''')
        (self.root / "sitecustomize.py").write_text('''
import json, os, urllib.request, urllib.error
class Response:
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return os.environ["TEST_RESPONSE"].encode()
def urlopen(request, timeout):
    with open(os.environ["TEST_CALLS"], "a") as stream:
        stream.write(json.dumps({"url": request.full_url, "headers": dict(request.header_items())}) + "\\n")
    if os.environ.get("TEST_TRANSPORT_ERROR") == "1":
        raise urllib.error.URLError("fixture unavailable")
    return Response()
urllib.request.urlopen = urlopen
''')

    def run_tick(self, day="2", clock="00:01", status="published", transport_error=False,
                 refresh_time="00:00", retry_time="09:00", local_weekly=False):
        env = dict(os.environ, BASH_ENV=str(self.shell_env), PYTHONPATH=str(self.root),
                   TEST_DAY=day, TEST_TIME=clock, TEST_PYTHON=sys.executable,
                   TEST_CALLS=str(self.calls), MMN_SCHEDULER_SECRET="" if local_weekly else "isolated-test-secret",
                   MMN_GROUP_WEEKLY_REFRESH_TIME=refresh_time, MMN_GROUP_WEEKLY_RETRY_TIME=retry_time,
                   MMN_SCHEDULER_LOCAL_WEEKLY_ONLY="true" if local_weekly else "false",
                   MMN_SCHEDULER_LOG_DIR=str(self.logs),
                   TEST_RESPONSE=json.dumps({"ok": True, "result": {"status": status}}),
                   TEST_TRANSPORT_ERROR="1" if transport_error else "0")
        result = subprocess.run(["bash", str(self.script)], env=env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return [json.loads(line) for line in self.calls.read_text().splitlines()] if self.calls.exists() else []

    def test_missed_midnight_minute_runs_once_and_keeps_signature(self):
        calls = self.run_tick()
        self.assertEqual(len(calls), 1)
        headers = {key.lower(): value for key, value in calls[0]["headers"].items()}
        self.assertIn("x-mmn-scheduler-signature", headers)
        self.assertNotIn("x-mmn-scheduler", headers)
        self.assertEqual(len(self.run_tick(clock="00:02")), 1)
        self.assertTrue((self.logs / "group_dashboard_weekly_2026-W39.done").exists())

    def test_late_morning_coalesces_overdue_windows(self):
        self.assertEqual(len(self.run_tick(clock="09:01")), 1)
        self.assertEqual(len(self.run_tick(clock="10:00")), 1)

    def test_wednesday_restart_runs_catchup_after_scheduled_minute(self):
        self.assertEqual(len(self.run_tick(day="3", clock="11:20")), 1)

    def test_no_early_or_weekend_trigger(self):
        self.assertEqual(self.run_tick(day="3", clock="08:59"), [])
        self.assertEqual(self.run_tick(day="6", clock="10:00"), [])

    def test_business_failure_is_not_done_and_not_retried_each_tick(self):
        self.assertEqual(len(self.run_tick(clock="09:00", status="awaiting_publication")), 1)
        self.assertEqual(list(self.logs.glob("*.done")), [])
        self.assertEqual(len(self.run_tick(clock="09:01", status="awaiting_publication")), 1)
        self.assertEqual(len(self.run_tick(day="3", clock="09:01")), 2)

    def test_transport_failure_waits_until_next_window(self):
        self.assertEqual(len(self.run_tick(clock="00:00", transport_error=True)), 1)
        self.assertEqual(len(self.run_tick(clock="00:00", transport_error=True)), 1)
        self.assertEqual(list(self.logs.glob("*.done")), [])
        self.assertEqual(len(self.run_tick(clock="09:01")), 2)

    def test_custom_evening_primary_is_not_swallowed_by_morning_retry(self):
        self.assertEqual(len(self.run_tick(clock="09:00", status="awaiting_publication", refresh_time="18:00")), 1)
        self.assertEqual(len(self.run_tick(clock="18:01", refresh_time="18:00")), 2)
        self.assertTrue((self.logs / "group_dashboard_weekly_2026-W39.done").exists())
        self.assertEqual(len(self.run_tick(clock="18:02", refresh_time="18:00")), 2)

    def test_equal_windows_and_late_restart_only_run_latest_due_once(self):
        self.assertEqual(len(self.run_tick(clock="09:01", refresh_time="09:00")), 1)
        self.assertEqual(len(self.run_tick(clock="09:02", refresh_time="09:00")), 1)

    def test_six_concurrent_ticks_claim_only_one_request(self):
        with ThreadPoolExecutor(max_workers=6) as executor:
            list(executor.map(lambda _: self.run_tick(clock="09:01"), range(6)))
        self.assertEqual(len(self.run_tick(clock="09:02")), 1)

    def test_failed_week_is_bounded_to_five_attempts(self):
        for day, clock in (("2", "00:01"), ("2", "09:01"), ("3", "09:01"),
                           ("4", "09:01"), ("5", "09:01"), ("6", "09:01"), ("7", "09:01")):
            for _ in range(2):
                calls = self.run_tick(day=day, clock=clock, status="source_unavailable")
        self.assertEqual(len(calls), 5)
        self.assertEqual(list(self.logs.glob("*.done")), [])

    def test_local_weekly_mode_uses_loopback_origin_without_cloud_secret(self):
        calls = self.run_tick(local_weekly=True)
        self.assertEqual(calls[0]["url"], "http://127.0.0.1:8765/api/group-dashboard/refresh-weekly")
        headers = {key.lower(): value for key, value in calls[0]["headers"].items()}
        self.assertEqual(headers.get("origin"), "http://127.0.0.1:8765")
        self.assertNotIn("x-mmn-scheduler-signature", headers)

    def test_local_weekly_mode_never_runs_other_scheduled_jobs(self):
        self.assertEqual(self.run_tick(day="7", clock="23:00", local_weekly=True), [])

    def test_local_tick_exits_even_with_production_infinite_loop(self):
        self.script.write_text(SCRIPT.read_text().replace("/app/logs", str(self.logs)))
        self.assertEqual(self.run_tick(day="3", clock="08:59", local_weekly=True), [])


if __name__ == "__main__":
    unittest.main()
