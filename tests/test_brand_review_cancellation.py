"""Task cancellation: injected providers, isolated jobs and SQLite only."""
import os
import sqlite3
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import server
import brand_review_runtime as runtime
import brand_review_repository as repository
from tests.test_brand_review_policy import result, claim, SCOPE, WINDOW


class BrandReviewCancellationTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(hasattr(server, 'cancel_brand_review_job'), 'Missing authenticated task cancellation')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db_path = Path(self.temp.name) / 'test.db'
        sqlite3.connect(self.db_path).close()
        self.env = patch.dict(os.environ, {'MMN_DATA_ROOT':self.temp.name,
            'MMN_DB_PATH':str(self.db_path), 'MMN_SOCIAL_EVIDENCE_V2_ENABLED':'false'}, clear=True)
        self.env.start(); self.addCleanup(self.env.stop)
        self.db = patch.object(server, 'DB_PATH', self.db_path)
        self.db.start(); self.addCleanup(self.db.stop)
        with server.SOCIAL_TREND_JOB_LOCK:
            self.prior = dict(server.SOCIAL_TREND_JOB_TASKS)
            server.SOCIAL_TREND_JOB_TASKS.clear()
        self.addCleanup(self.restore_jobs)

    def restore_jobs(self):
        with server.SOCIAL_TREND_JOB_LOCK:
            server.SOCIAL_TREND_JOB_TASKS.clear()
            server.SOCIAL_TREND_JOB_TASKS.update(self.prior)

    def test_cancelled_job_cannot_become_complete_from_late_result(self):
        started, release = threading.Event(), threading.Event()
        seen = []
        def runner(body, *, org_id, progress_callback, cancel):
            seen.append(cancel); started.set(); release.wait(2)
            progress_callback('late', 90, 'late')
            return {'late':'must not publish'}
        with patch.object(server, 'brand_review_task_mode', return_value='enabled'):
            job = server.start_social_trend_job({'keyword':'甲','centerType':'brand_penetration'}, org_id='a', runner=runner)
        self.assertTrue(started.wait(1))
        try:
            self.assertTrue(job['canCancel'])
            self.assertIsNone(server.cancel_brand_review_job(job['jobId'], 'other'))
            cancelled = server.cancel_brand_review_job(job['jobId'], 'a')
            self.assertEqual(cancelled['status'], 'cancelling')
            self.assertTrue(seen[0].is_set())
            self.assertEqual(server.active_local_job_summary()['byType']['socialTrend'], 1)
        finally:
            release.set()
        for _ in range(100):
            state = server.get_social_trend_job(job['jobId'], 'a')
            if state['status'] == 'cancelled':break
            time.sleep(.01)
        self.assertEqual(state['status'], 'cancelled')
        self.assertIsNone(state['result'])
        self.assertEqual(server.cancel_brand_review_job(job['jobId'], 'a')['status'], 'cancelled')

    def test_legacy_runner_signature_and_public_json_do_not_gain_cancellation(self):
        started, release = threading.Event(), threading.Event()
        def runner(body, *, org_id, progress_callback):
            started.set(); release.wait(1); return {'old':True}
        job = server.start_social_trend_job({'keyword':'甲'}, org_id='a', runner=runner)
        self.assertTrue(started.wait(1))
        self.assertNotIn('canCancel', job)
        self.assertIsNone(server.cancel_brand_review_job(job['jobId'], 'a'))
        release.set()
        for _ in range(100):
            if server.get_social_trend_job(job['jobId'], 'a')['status'] == 'completed':break
            time.sleep(.01)

    def test_cancel_before_frozen_review_has_no_calls_or_versions(self):
        conn = sqlite3.connect(':memory:'); self.addCleanup(conn.close)
        repository.migrate(conn)
        token = runtime.CancellationToken(); token.set()
        source = {**result(),'dateWindow':WINDOW,'snapshot':{'id':SCOPE['snapshotId']}}
        calls = Mock(return_value={'claims':[claim()]})
        with self.assertRaises(ValueError):
            runtime.analyze_snapshot(conn, source, SCOPE, calls, cancel=token)
        calls.assert_not_called()
        self.assertEqual(conn.execute('SELECT count(*) FROM brand_review_versions').fetchone()[0], 0)

    def test_published_review_cannot_be_marked_cancelled(self):
        token = runtime.CancellationToken(); token.published = True
        with server.SOCIAL_TREND_JOB_LOCK:
            server.SOCIAL_TREND_JOB_TASKS['published'] = {'jobId':'published','status':'running',
                '_org_id':'a','_cancel':token,'canCancel':True}
        with self.assertRaises(repository.ReviewConflict):
            server.cancel_brand_review_job('published','a')
        self.assertFalse(token.is_set())

    def test_actual_cancel_route_checks_admin_origin_and_scope(self):
        h = object.__new__(server.Handler); h.command='POST'; h.path='/api/brand-reviews/jobs/missing/cancel'
        h.headers={'Host':'127.0.0.1:8899','Origin':'http://127.0.0.1:8899','X-MMN-CSRF':'1'}
        h.prepare_json_request=Mock(return_value=True); h.read_json=Mock(return_value={}); h.send_json=Mock()
        h.current_auth=Mock(return_value={'role':'trial','org_id':'a','user_id':'u'}); h._auth_transport='cookie'
        with patch.object(server,'cloud_login_required',return_value=True):
            h.do_POST(); self.assertEqual(h.send_json.call_args.args[1],403)
            h.current_auth.return_value={'role':'admin','org_id':'a','user_id':'u'}
            h.do_POST(); self.assertEqual(h.send_json.call_args.args[1],404)
        with patch.object(server,'cloud_login_required',return_value=False):
            h.headers['Origin']='https://evil.example'
            h.do_POST(); self.assertEqual(h.send_json.call_args.args[1],403)

    def test_real_frozen_pipeline_cancel_prevents_review_write_and_repair(self):
        source = {**result(),'keyword':'甲','dateWindow':WINDOW,
                  'snapshot':{'id':'source','filters':{'competitors':['乙']}}}
        scope = runtime.scope_for_snapshot(source,'a','china')
        with sqlite3.connect(self.db_path) as conn:repository.migrate(conn)
        all_started = threading.Event(); calls = []; lock = threading.Lock()
        def provider(slot,packet,repair,timeout,stop):
            with lock:
                calls.append(slot)
                if len(calls)==3:all_started.set()
            stop.wait(2)
            return 'late invalid JSON must not cause repair'
        with patch.dict(os.environ,{'MMN_BRAND_CONCLUSIONS_MODE':'enabled',
                'MMN_BRAND_CONCLUSIONS_ALLOWLIST':'a:'+scope['projectId']}), \
                patch.object(server,'latest_social_trend_snapshot',return_value=source), \
                patch.object(server,'brand_review_provider_runner',side_effect=provider):
            job=server.start_social_trend_job({'keyword':'甲','competitors':['乙'],
                'centerType':'brand_penetration','analysisOnly':True},org_id='a')
            self.assertTrue(all_started.wait(1))
            server.cancel_brand_review_job(job['jobId'],'a')
            for _ in range(100):
                state=server.get_social_trend_job(job['jobId'],'a')
                if state['status']=='cancelled':break
                time.sleep(.01)
            self.assertEqual(state['status'],'cancelled')
        self.assertEqual(len(calls),3)
        with sqlite3.connect(self.db_path) as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM brand_review_versions').fetchone()[0],0)

    def test_cancel_publication_race_never_acknowledges_cancel_after_commit(self):
        token=runtime.CancellationToken()
        conn=sqlite3.connect(':memory:',check_same_thread=False); self.addCleanup(conn.close)
        repository.migrate(conn)
        source={**result(),'dateWindow':WINDOW,'snapshot':{'id':SCOPE['snapshotId']}}
        entered, release, done=threading.Event(),threading.Event(),threading.Event()
        original=repository.save_review_version; errors=[]
        def paused_save(*args,**kwargs):
            entered.set();release.wait(2);return original(*args,**kwargs)
        def run():
            try:runtime.analyze_snapshot(conn,source,SCOPE,lambda *args:{'claims':[claim()]},cancel=token)
            except Exception as exc:errors.append(exc)
        with server.SOCIAL_TREND_JOB_LOCK:
            server.SOCIAL_TREND_JOB_TASKS['race']={'jobId':'race','status':'running','_org_id':'a','_cancel':token,'canCancel':True}
        def cancel():
            try:server.cancel_brand_review_job('race','a')
            except repository.ReviewConflict:errors.append('correct-conflict')
            finally:done.set()
        with patch.object(repository,'save_review_version',side_effect=paused_save):
            worker=threading.Thread(target=run);worker.start();self.assertTrue(entered.wait(1))
            canceller=threading.Thread(target=cancel);canceller.start()
            self.assertFalse(done.wait(.03));release.set()
            worker.join(2);canceller.join(2)
        self.assertEqual(errors,['correct-conflict'])
        self.assertTrue(token.published);self.assertFalse(token.is_set())
        self.assertEqual(conn.execute('SELECT count(*) FROM brand_review_versions').fetchone()[0],1)

    def test_revoked_mode_cannot_publish_or_fall_back_to_legacy_storage(self):
        source={**result(),'keyword':'甲','dateWindow':WINDOW,
                'snapshot':{'id':'source','filters':{'competitors':['乙']}}}
        scope=runtime.scope_for_snapshot(source,'a','china')
        with sqlite3.connect(self.db_path) as conn:repository.migrate(conn)
        all_started=threading.Event(); lock=threading.Lock(); calls=[]
        def provider(*args):
            with lock:
                calls.append(1)
                if len(calls)==3:
                    os.environ['MMN_BRAND_CONCLUSIONS_MODE']='legacy'
                    all_started.set()
            all_started.wait(1)
            return {'claims':[claim()]}
        with patch.dict(os.environ,{'MMN_BRAND_CONCLUSIONS_MODE':'enabled',
                'MMN_BRAND_CONCLUSIONS_ALLOWLIST':'a:'+scope['projectId']}), \
                patch.object(server,'latest_social_trend_snapshot',return_value=source), \
                patch.object(server,'brand_review_provider_runner',side_effect=provider), \
                patch.object(server,'save_social_trend_snapshot',return_value={'id':'unexpected'}) as old_save:
            job=server.start_social_trend_job({'keyword':'甲','competitors':['乙'],
                'centerType':'brand_penetration','analysisOnly':True},org_id='a')
            for _ in range(100):
                state=server.get_social_trend_job(job['jobId'],'a')
                if state['status'] in ('completed','cancelled','failed'):break
                time.sleep(.01)
            old_save.assert_not_called()
            self.assertEqual(state['status'],'cancelled')
        with sqlite3.connect(self.db_path) as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM brand_review_versions').fetchone()[0],0)


if __name__ == '__main__':unittest.main()
