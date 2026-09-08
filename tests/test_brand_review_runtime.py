import copy
import importlib.util
import threading
import time
import unittest
import sqlite3
from unittest.mock import Mock
from tests.test_brand_review_policy import result, claim, SCOPE, WINDOW
import brand_review_policy as policy
rt=__import__('brand_review_runtime') if importlib.util.find_spec('brand_review_runtime') else None

class RuntimeTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(rt,'Missing bounded runtime')
        self.packet=policy.build_layered_packet(result(),SCOPE,WINDOW)

    def test_blind_common_packet_and_preserved_rows(self):
        calls=[]
        def runner(slot,packet,repair,timeout,cancel):
            calls.append((slot,copy.deepcopy(packet),copy.deepcopy(repair)))
            if repair is None: return {'claims':[claim(),{'claimId':'bad','evidenceRefs':'wrong'}]}
            return {'claims':[dict(claim(),text='unsafe replacement'),dict(claim(cid='bad'))]}
        out=rt.run_reviews(self.packet,runner)
        self.assertEqual(len(calls),6)
        self.assertTrue(all(c[1]==self.packet for c in calls))
        for c in calls:
            if c[2]: self.assertNotIn('c',[x.get('claimId') for x in c[2]['invalidClaims']])
        self.assertEqual(out['outputs']['review_1']['claims'][0],claim())

    def test_nonretryable_errors(self):
        for code in (401,403,402):
            calls=[]
            def runner(*args):
                calls.append(1); e=RuntimeError('private credential'); e.status_code=code; raise e
            out=rt.run_reviews(self.packet,runner)
            self.assertEqual(len(calls),3); self.assertNotIn('private',str(out['errors']))

    def test_deadline_cancellation_late_guard(self):
        calls=[]
        def runner(*args): calls.append(1); time.sleep(.2); return {'claims':[claim()]}
        start=time.monotonic(); out=rt.run_reviews(self.packet,runner,total_timeout=.03,call_timeout=.02)
        self.assertLess(time.monotonic()-start,.15)
        self.assertLessEqual(len(calls),3); self.assertEqual(out['outputs'],{})
        time.sleep(.22); self.assertEqual(out['outputs'],{})
        cancel=threading.Event();cancel.set()
        self.assertEqual(rt.run_reviews(self.packet,runner,cancel=cancel)['callCount'],0)

    def test_allowlist_fail_closed(self):
        scope={'orgId':'a','projectId':'p'}
        for env in ({},{'MMN_BRAND_CONCLUSIONS_MODE':'bad'},{'MMN_BRAND_CONCLUSIONS_MODE':'enabled'}):
            self.assertEqual(rt.mode_for(scope,env),'legacy')
        env={'MMN_BRAND_CONCLUSIONS_MODE':'enabled','MMN_BRAND_CONCLUSIONS_ALLOWLIST':'a:p'}
        self.assertEqual(rt.mode_for(scope,env),'enabled')
        self.assertEqual(rt.mode_for({'orgId':'b','projectId':'p'},env),'legacy')

    def test_opposing_duplicate_is_not_discarded_or_repaired_into_support(self):
        def runner(*args):return {'claims':[claim(),dict(claim(),text='销售必涨')]}
        out=rt.run_reviews(self.packet,runner)
        self.assertEqual(out['callCount'],3)
        self.assertEqual(out['decision']['brandConclusions'][0]['insights'],[])

    def test_recursive_malformed_output_does_not_crash_task(self):
        raw={'claims':[]};raw['self']=raw
        out=rt.run_reviews(self.packet,lambda *args:raw)
        self.assertLessEqual(out['callCount'],6)
        self.assertFalse(out['decision']['brandConclusions'][0]['insights'])

    def test_existing_provider_auth_error_wrappers_are_nonretryable(self):
        for message in ('千问请求未授权：密钥无效','DeepSeek 请求被拒绝：请检查账户权限','未配置 KIMI_API_KEY'):
            def runner(*args):raise ValueError(message)
            self.assertEqual(rt.run_reviews(self.packet,runner)['callCount'],3)

    def test_stored_exact_window_is_preserved_not_sample_derived(self):
        import brand_review_repository as repo
        window={'start':'2026-09-02T03:00:00+08:00','end':'2026-09-04T03:00:00+08:00','endExclusive':True}
        data={**result(),'dateWindow':window,'snapshot':{'id':'snap','filters':{'startDate':'2020-01-01','endDate':'2030-01-01'}}}
        conn=sqlite3.connect(':memory:');self.addCleanup(conn.close);repo.migrate(conn)
        seen=[]
        def runner(slot,packet,*args):seen.append(packet['dateWindow']);return {'claims':[claim()]}
        review=rt.analyze_snapshot(conn,data,SCOPE,runner)
        self.assertEqual(seen,[window]*3)
        self.assertEqual(review['decision'].get('dateWindow'),window)

    def test_missing_window_fails_before_calls(self):
        import brand_review_repository as repo
        conn=sqlite3.connect(':memory:');self.addCleanup(conn.close);repo.migrate(conn)
        runner=Mock(return_value={'claims':[claim()]})
        with self.assertRaises(ValueError):rt.analyze_snapshot(conn,{**result(),'snapshot':{'id':'snap'}},SCOPE,runner)
        runner.assert_not_called()

    def test_real_snapshot_window_allows_time_range_metadata(self):
        window={'start':'2026-09-01','end':'2026-09-08','endExclusive':True,'timeRange':'7d'}
        try:actual=rt.window_for_snapshot({'dateWindow':window})
        except ValueError:actual=None
        self.assertEqual(actual,{'start':'2026-09-01','end':'2026-09-08','endExclusive':True})

    def test_collection_admission_window_and_conflict(self):
        window={'start':'2026-09-01T08:00:00+08:00','end':'2026-09-08T08:00:00+08:00','endExclusive':True,'timeRange':'7d'}
        data={'admission':{'dateWindow':window},'snapshot':{'filters':{'startDate':'','endDate':'','timeRange':'7d'}}}
        try:actual=rt.window_for_snapshot(data)
        except ValueError:actual=None
        self.assertEqual(actual,{k:v for k,v in window.items() if k!='timeRange'})
        with self.assertRaises(ValueError):rt.window_for_snapshot({**data,'dateWindow':{'start':'2020-01-01','end':'2030-01-01'}})
