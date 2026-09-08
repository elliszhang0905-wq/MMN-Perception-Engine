"""No listening ports, credentials, network or shared DB. Real handler methods."""
import copy
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch,Mock
import server
import brand_review_repository as repo
import brand_review_runtime as rt
from tests.test_brand_review_policy import result,claim

class ApiTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'test.db'
        isolation=patch.dict(os.environ,{'MMN_DATA_ROOT':self.temp.name,'MMN_DB_PATH':str(self.path),'MMN_SOCIAL_EVIDENCE_DB':str(Path(self.temp.name)/'social.sqlite'),'MMN_SOCIAL_EVIDENCE_RAW_DIR':str(Path(self.temp.name)/'raw'),'MMN_SOCIAL_EVIDENCE_V2_ENABLED':'false'})
        isolation.start();self.addCleanup(isolation.stop)
        self.conn=sqlite3.connect(self.path);repo.migrate(self.conn);self.conn.close()
        self.data={**result(),'keyword':'甲','snapshot':{'id':'s','filters':{'competitors':['乙'],'startDate':'2026-09-01','endDate':'2026-09-08'}}}
        self.scope=rt.scope_for_snapshot(self.data,'local','china')
        self.env={'MMN_BRAND_CONCLUSIONS_MODE':'enabled','MMN_BRAND_CONCLUSIONS_ALLOWLIST':'local:'+self.scope['projectId']}

    def handler(self,method='GET',cloud=False,auth=None,headers=None):
        h=object.__new__(server.Handler);h.command=method
        h.headers=headers or {'Host':'127.0.0.1:8899','Origin':'http://127.0.0.1:8899','X-MMN-CSRF':'1'}
        h.current_auth=Mock(return_value=auth);h.send_json=Mock();h._auth_transport='cookie'
        return h

    def test_auth_cloud_get_and_trial_post(self):
        self.assertTrue(hasattr(server.Handler,'require_brand_review_auth'),'Missing dedicated readonly auth')
        with patch.object(server,'cloud_login_required',return_value=True):
            h=self.handler();self.assertIsNone(h.require_brand_review_auth());self.assertEqual(h.send_json.call_args.args[1],401)
            h=self.handler(auth={'role':'trial','org_id':'a','user_id':'u'},method='POST')
            self.assertIsNone(h.require_brand_review_auth(write=True));self.assertEqual(h.send_json.call_args.args[1],403)

    def test_local_post_origin_guard(self):
        self.assertTrue(hasattr(server.Handler,'require_brand_review_auth'),'Missing origin guard')
        with patch.object(server,'cloud_login_required',return_value=False):
            for host in ('evil.example','localhost:8899'):
                h=self.handler('POST',headers={'Host':host,'Origin':'https://evil.example','X-MMN-CSRF':'1'})
                self.assertIsNone(h.require_brand_review_auth(write=True))

    def test_existing_analyze_entry_requires_v4_write_auth(self):
        h=self.handler('POST',headers={'Host':'127.0.0.1:8899','Origin':'https://evil.example','X-MMN-CSRF':'1'})
        h.path='/api/social-trends/jobs';h.prepare_json_request=Mock(return_value=True)
        h.read_json=Mock(return_value={'keyword':'甲','competitors':['乙'],'centerType':'brand_penetration'})
        with patch.dict(os.environ,self.env,clear=True),patch.object(server,'cloud_login_required',return_value=False),patch.object(server,'start_social_trend_job',return_value={'jobId':'bad'}) as start:
            h.do_POST();self.assertEqual(h.send_json.call_args.args[1],403);start.assert_not_called()

    def test_legacy_json_zero_new_calls(self):
        self.assertTrue(hasattr(server,'brand_review_analyze_existing'),'Missing scoped adapter')
        legacy={**self.data,'brandDecision':{'status':'old'}}
        with patch.dict(os.environ,{},clear=True),patch.object(server,'analyze_existing_brand_penetration_snapshot',return_value=copy.deepcopy(legacy)) as old,patch.object(server,'brand_review_provider_runner') as runner:
            out=server.brand_review_analyze_existing(copy.deepcopy(self.data),'local','china')
            self.assertEqual(out,legacy);old.assert_called_once();runner.assert_not_called()

    def test_legacy_pre_v4_shape_without_snapshot_identity(self):
        with patch.dict(os.environ,{},clear=True),patch.object(server,'analyze_existing_brand_penetration_snapshot',return_value={'old':True}):
            try:out=server.brand_review_analyze_existing({'keyword':'甲'},'local','china')
            except ValueError:out=None
            self.assertEqual(out,{'old':True})

    def test_actual_get_and_post_routes_scope_and_refresh(self):
        with patch.dict(os.environ,self.env,clear=True),patch.object(server,'DB_PATH',self.path),patch.object(server,'brand_review_provider_runner',return_value={'claims':[claim()]}):
            review=server.brand_review_analyze_existing(self.data,'local','china')['brandReview']
        with patch.dict(os.environ,self.env,clear=True),patch.object(server,'DB_PATH',self.path),patch.object(server,'cloud_login_required',return_value=True),patch.object(server,'latest_social_trend_snapshot',return_value=self.data),patch.object(server,'brand_review_provider_runner') as runner:
            h=self.handler(auth={'org_id':'local','user_id':'u','role':'admin'});h.path='/api/brand-reviews/latest?keyword=甲&edition=china'
            h.do_GET();self.assertEqual(h.send_json.call_args.args[0]['review'],review);runner.assert_not_called()
            cid=review['decision']['brandConclusions'][0]['insights'][0]['claimId']
            h=self.handler(method='POST',auth={'org_id':'other','user_id':'u','role':'admin'});h.path='/api/brand-reviews/decisions';h.prepare_json_request=Mock(return_value=True)
            h.read_json=Mock(return_value=dict(reviewId=review['reviewId'],expectedVersion=1,idempotencyKey='h',claimId=cid,action='reject',reason='待核'))
            h.do_POST();self.assertEqual(h.send_json.call_args.args[1],404)
            h.current_auth=Mock(return_value={'org_id':'local','user_id':'u','role':'admin'})
            h.do_POST();self.assertEqual(h.send_json.call_args.args[0]['review']['version'],2)
            h.do_POST();self.assertEqual(h.send_json.call_args.args[0]['review']['version'],2)

    def test_enabled_uses_source_and_appends_without_snapshot_save(self):
        self.assertTrue(hasattr(server,'brand_review_analyze_existing'),'Missing scoped adapter')
        with patch.dict(os.environ,self.env,clear=True),patch.object(server,'DB_PATH',self.path),patch.object(server,'analyze_existing_brand_penetration_snapshot') as old,patch.object(server,'save_social_trend_snapshot') as snapshot,patch.object(server,'brand_review_provider_runner',return_value={'claims':[claim()]}) as runner:
            out=server.brand_review_analyze_existing(copy.deepcopy(self.data),'local','china')
            self.assertEqual(out['brandReview']['version'],1);self.assertEqual(runner.call_count,3)
            self.assertEqual(out['snapshot'],self.data['snapshot']);old.assert_not_called();snapshot.assert_not_called()
            latest=server.brand_review_latest(self.data,'local','china')
            self.assertEqual(latest['review'],out['brandReview']);self.assertEqual(runner.call_count,3)

    def test_latest_rejects_changed_prompt_and_frozen_evidence_without_calls(self):
        with patch.dict(os.environ,self.env,clear=True),patch.object(server,'DB_PATH',self.path),patch.object(server,'brand_review_provider_runner',return_value={'claims':[claim()]}) as runner:
            server.brand_review_analyze_existing(self.data,'local','china')
            with patch.object(rt,'PROMPT_VERSION','new-prompt'):
                self.assertIsNone(server.brand_review_latest(self.data,'local','china')['review'])
            changed=copy.deepcopy(self.data);changed['verifiedComparisonItems'][0]['text']='来源已修正'
            self.assertIsNone(server.brand_review_latest(changed,'local','china')['review'])
            self.assertEqual(runner.call_count,3)

    def test_shadow_one_round_preserves_legacy_whole_json(self):
        legacy={**copy.deepcopy(self.data),'brandDecision':{'schemaVersion':'v3','text':'旧结论'}}
        with patch.dict(os.environ,{**self.env,'MMN_BRAND_CONCLUSIONS_MODE':'shadow'},clear=True),patch.object(server,'DB_PATH',self.path),patch.object(server,'analyze_existing_brand_penetration_snapshot') as old,patch.object(server,'brand_review_provider_runner',return_value={'claims':[claim()]}) as runner:
            out=server.brand_review_analyze_existing(legacy,'local','china')
            self.assertEqual(out,legacy);self.assertEqual(runner.call_count,3);old.assert_not_called()

    def test_collect_enabled_skips_old_brand_and_saves_source_first(self):
        events=[]
        data=copy.deepcopy(self.data);data.pop('snapshot')
        def save(conn,r,*args): events.append('source');return {'id':'new','createdAt':'2026-09-08T00:00:00Z'}
        def analyze(existing,*args):
            events.append('v4');self.assertEqual(existing['snapshot']['id'],'new')
            return {**existing,'brandReview':{'version':1}}
        with patch.dict(os.environ,self.env,clear=True),patch.object(server,'db',side_effect=lambda:sqlite3.connect(self.path)),patch.object(server,'latest_social_trend_snapshot',return_value=None),patch.object(server,'collect_social_trends',return_value={}),patch.object(server,'attach_competitor_rankings',return_value=data),patch.object(server,'apply_social_trend_history',side_effect=lambda r,p:r),patch.object(server,'validate_social_trends_with_models',side_effect=lambda r,**kw:r) as validate,patch.object(server,'save_social_trend_snapshot',side_effect=save),patch.object(server,'brand_review_analyze_existing',side_effect=analyze):
            server.run_social_trend_collection_pipeline({'keyword':'甲','competitors':['乙'],'centerType':'brand_penetration'},org_id='local')
            self.assertEqual(events,['source','v4']);self.assertEqual(validate.call_args.kwargs,{'skip_brand_conclusions':True})

    def test_collect_real_admission_shape_reaches_v4_without_custom_dates(self):
        data=copy.deepcopy(self.data);data.pop('snapshot')
        data['admission']={'dateWindow':{'start':'2026-09-01T00:00:00+08:00','end':'2026-09-08T00:00:00+08:00','endExclusive':True,'timeRange':'7d'}}
        with patch.dict(os.environ,self.env,clear=True),patch.object(server,'DB_PATH',self.path),patch.object(server,'db',side_effect=lambda:sqlite3.connect(self.path)),patch.object(server,'latest_social_trend_snapshot',return_value=None),patch.object(server,'collect_social_trends',return_value={}),patch.object(server,'attach_competitor_rankings',return_value=data),patch.object(server,'apply_social_trend_history',side_effect=lambda r,p:r),patch.object(server,'validate_social_trends_with_models',side_effect=lambda r,**kw:r),patch.object(server,'save_social_trend_snapshot',return_value={'id':'new','createdAt':'2026-09-08T00:00:00Z'}),patch.object(server,'brand_review_provider_runner',return_value={'claims':[claim()]}) as runner:
            out=server.run_social_trend_collection_pipeline({'keyword':'甲','competitors':['乙'],'centerType':'brand_penetration','timeRange':'7d'},org_id='local')
            self.assertEqual(out['brandReview']['version'],1)
            self.assertEqual(out['brandReview']['decision']['dateWindow'],{k:v for k,v in data['admission']['dateWindow'].items() if k!='timeRange'})
            self.assertEqual(runner.call_count,3)
