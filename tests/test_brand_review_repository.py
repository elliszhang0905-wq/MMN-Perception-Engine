import copy
import importlib.util
import json
import sqlite3
import unittest

repo = __import__('brand_review_repository') if importlib.util.find_spec('brand_review_repository') else None

class RepositoryTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(repo, 'Missing append-only repository')
        self.conn = sqlite3.connect(':memory:')
        self.addCleanup(self.conn.close)
        self.scope = dict(orgId='a', edition='china', projectId='p', snapshotId='s')
        self.payload = dict(decision=dict(schemaVersion='brand-penetration-analysis-v4', brandConclusions=[], pairwiseConclusions=[]))

    def save(self, expected=0, key='k'):
        return repo.save_review_version(self.conn,self.scope,self.payload,expected,key)

    def test_get_does_not_migrate(self):
        self.assertIsNone(repo.get_review_projection(self.conn,self.scope,None))
        self.assertEqual(self.conn.execute('select name from sqlite_master').fetchall(),[])

    def test_explicit_migration_and_cas(self):
        repo.migrate(self.conn)
        a=self.save(); before=self.conn.execute('select payload from brand_review_versions').fetchone()[0]
        self.assertEqual(self.save(),a)
        with self.assertRaises(repo.ReviewConflict): self.save(0,'other')
        self.payload['rawOutputs']='secret'
        with self.assertRaises(repo.ReviewConflict): self.save()
        b=self.save(1,'next'); self.assertEqual(b['version'],2)
        self.assertEqual(self.conn.execute('select payload from brand_review_versions where version=1').fetchone()[0],before)
        self.assertNotIn('secret',json.dumps(b))

    def test_scope_and_permission(self):
        repo.migrate(self.conn); a=self.save()
        for key in self.scope:
            wrong={**self.scope,key:'other'}
            self.assertIsNone(repo.get_review_projection(self.conn,wrong,a['reviewId']))
        with self.assertRaises(repo.ReviewForbidden):
            repo.append_review_decision(self.conn,self.scope,dict(user_id='u',role='trial'),{})

    def test_reject_invalidates_dependents_and_idempotency(self):
        repo.migrate(self.conn)
        row=dict(brand='甲',facts=[],insights=[dict(claimId='c',text='合格',dependsOn=[])],actionOptions=[dict(claimId='d',text='动作',dependsOn=['c'],allowExecution=False)],unknowns=[],disputes=[])
        self.payload['decision']['brandConclusions']=[row]
        a=self.save(); req=dict(reviewId=a['reviewId'],expectedVersion=1,idempotencyKey='d',claimId='c',action='reject',reason='来源待核验')
        actor=dict(user_id='u',role='admin',org_id='a')
        b=repo.append_review_decision(self.conn,self.scope,actor,req)
        self.assertEqual(b['version'],2)
        self.assertEqual(b,repo.append_review_decision(self.conn,self.scope,actor,req))
        row=b['decision']['brandConclusions'][0]
        self.assertEqual(row['insights'],[]); self.assertEqual(row['actionOptions'],[])
        self.assertEqual({r['claimId'] for r in row['unknowns']},{'c','d'})
        self.assertEqual(repo.get_review_projection(self.conn,self.scope,a['reviewId'],version=1)['version'],1)

    def test_fixed_projection(self):
        repo.migrate(self.conn)
        self.payload['decision']['brandConclusions']=[dict(brand='甲',rawOutputs='secret',unknowns=[dict(claimId='c',text='待复核',candidateText='secret',candidateTexts=['secret'],errors='secret')])]
        self.assertNotIn('secret',json.dumps(self.save()))

    def test_projection_preserves_safe_source_provenance_and_window(self):
        window={'start':'2026-09-02T00:00:00Z','end':'2026-09-03T00:00:00Z','endExclusive':True}
        ref={'evidenceId':'e','sourceUrl':'https://example.org/e','platform':'微博','sourceFingerprint':'abc','quote':'新品','publishedAt':'2026-09-02','url':'bad-url-field'}
        projected=repo.public_decision({'dateWindow':window,'brandConclusions':[{'facts':[{'claimId':'c','evidenceRefs':[ref]}]}]})
        self.assertEqual(projected.get('dateWindow'),window)
        actual=projected['brandConclusions'][0]['facts'][0]['evidenceRefs'][0]
        self.assertEqual(actual.get('sourceUrl'),ref['sourceUrl']);self.assertEqual(actual.get('platform'),'微博');self.assertNotIn('url',actual)

    def test_modify_pending_never_publishes_and_storage_append_only(self):
        repo.migrate(self.conn)
        self.payload['decision']['brandConclusions']=[dict(brand='甲',facts=[],insights=[dict(claimId='c',text='原文',dependsOn=[])],actionOptions=[],unknowns=[],disputes=[])]
        a=self.save();req=dict(reviewId=a['reviewId'],expectedVersion=1,idempotencyKey='edit',claimId='c',action='modify',reason='需确认',edit='预算翻倍，销量必涨 SECRET')
        b=repo.append_review_decision(self.conn,self.scope,dict(user_id='u',role='admin',org_id='a'),req)
        self.assertNotIn('SECRET',json.dumps(b));self.assertEqual(b['decision']['brandConclusions'][0]['insights'],[])
        with self.assertRaises(repo.ReviewConflict):repo.append_review_decision(self.conn,self.scope,dict(user_id='u',role='admin',org_id='a'),{**req,'idempotencyKey':'new'})
        for table in ('brand_review_versions','brand_review_decisions'):
            with self.assertRaises(sqlite3.IntegrityError):self.conn.execute('DELETE FROM '+table)
            self.conn.rollback()

    def test_rejected_source_fact_invalidates_claims_using_same_source(self):
        repo.migrate(self.conn)
        self.payload['decision']['brandConclusions']=[dict(brand='甲',facts=[dict(claimId='source',kind='fact',text='来源',dependsOn=[],evidenceRefs=[{'evidenceId':'e'}])],insights=[dict(claimId='c',text='观察',dependsOn=[],evidenceRefs=[{'evidenceId':'e'}])],actionOptions=[],unknowns=[],disputes=[])]
        a=self.save()
        b=repo.append_review_decision(self.conn,self.scope,dict(user_id='u',role='admin',org_id='a'),dict(reviewId=a['reviewId'],expectedVersion=1,idempotencyKey='source-reject',claimId='source',action='reject',reason='来源有误'))
        self.assertEqual(b['decision']['brandConclusions'][0]['insights'],[])

    def human_fixture(self,soft=False,incomplete=False):
        import brand_review_runtime as rt
        import brand_review_policy as p
        from tests.test_brand_review_policy import result,claim,WINDOW
        packet=p.build_layered_packet(result(),{**self.scope,'promptVersion':rt.PROMPT_VERSION,'reviewVersion':'1'},WINDOW)
        canonical=p.validate_layered_reviews({'review_1':{'claims':[claim()]}},packet,actor_id='server',server_time='2026-09-08T00:00:00Z')[0]['canonicalText']
        def runner(slot,*args):
            if incomplete and slot=='review_3':return {'claims':[claim(),{'bad':True}]}
            c=claim()
            if soft and slot=='review_3':c['text']=canonical+'（待核对）'
            return {'claims':[c]}
        self.payload=rt.run_reviews(packet,runner);repo.migrate(self.conn)
        review=self.save();row=review['decision']['brandConclusions'][0]
        cid=(row['unknowns'] or row['insights'])[0]['claimId']
        return review,cid,canonical

    def test_safe_soft_accept_and_canonical_modify_refresh(self):
        review,cid,canonical=self.human_fixture(soft=True)
        self.assertEqual(review['decision']['brandConclusions'][0]['unknowns'][0].get('canonicalCandidateText'),canonical)
        self.assertNotEqual(review['decision']['brandConclusions'][0]['unknowns'][0]['publicationStatus'],'human_confirmed')
        actor=dict(user_id='u',role='admin',org_id='a')
        req=dict(reviewId=review['reviewId'],expectedVersion=1,idempotencyKey='accept',claimId=cid,action='accept',reason='已人工核对限定来源解释')
        accepted=repo.append_review_decision(self.conn,self.scope,actor,req)
        items=accepted['decision']['brandConclusions'][0]['insights']
        self.assertTrue(items,'soft canonical choice should be visible as human-confirmed')
        self.assertEqual(items[0]['publicationStatus'],'human_confirmed')
        self.assertNotEqual(items[0]['publicationStatus'],'supported')
        self.assertEqual(items[0]['text'],canonical)
        modified=repo.append_review_decision(self.conn,self.scope,actor,{**req,'action':'modify','edit':canonical,'expectedVersion':2,'idempotencyKey':'modify'})
        self.assertEqual(modified['decision']['brandConclusions'][0]['insights'][0]['humanDecisionStatus'],'modified_canonical')
        self.assertEqual(repo.get_review_projection(self.conn,self.scope)['version'],3)

    def test_soft_reject_can_be_explicitly_resolved_not_source_reject(self):
        review,cid,canonical=self.human_fixture()
        actor=dict(user_id='u',role='admin',org_id='a')
        req=dict(reviewId=review['reviewId'],expectedVersion=1,idempotencyKey='reject',claimId=cid,action='reject',reason='先暂停')
        repo.append_review_decision(self.conn,self.scope,actor,req)
        accepted=repo.append_review_decision(self.conn,self.scope,actor,{**req,'action':'accept','reason':'限定解释已核对','expectedVersion':2,'idempotencyKey':'resolve'})
        self.assertTrue(accepted['decision']['brandConclusions'][0]['insights'])

    def test_incomplete_slot_cannot_be_human_published(self):
        review,cid,canonical=self.human_fixture(soft=True,incomplete=True)
        out=repo.append_review_decision(self.conn,self.scope,dict(user_id='u',role='admin',org_id='a'),dict(reviewId=review['reviewId'],expectedVersion=1,idempotencyKey='accept',claimId=cid,action='accept',reason='尝试'))
        self.assertEqual(out['decision']['brandConclusions'][0]['insights'],[])
        self.assertEqual(out['decision']['brandConclusions'][0]['unknowns'][0].get('humanDecisionStatus'),'pending')

    def test_human_never_overrides_rejected_source_or_hard_gate(self):
        review,cid,canonical=self.human_fixture()
        actor=dict(user_id='u',role='admin',org_id='a')
        source=review['decision']['brandConclusions'][0]['facts'][0]['claimId']
        req=dict(reviewId=review['reviewId'],expectedVersion=1,idempotencyKey='reject-source',claimId=source,action='reject',reason='来源失效')
        repo.append_review_decision(self.conn,self.scope,actor,req)
        out=repo.append_review_decision(self.conn,self.scope,actor,{**req,'expectedVersion':2,'idempotencyKey':'attempt','claimId':cid,'action':'modify','edit':canonical})
        self.assertFalse(out['decision']['brandConclusions'][0]['insights'])

    def test_accept_source_fact_acknowledges_without_hiding_or_upgrading(self):
        review,cid,canonical=self.human_fixture()
        actor=dict(user_id='u',role='admin',org_id='a')
        source=review['decision']['brandConclusions'][0]['facts'][0]['claimId']
        req=dict(reviewId=review['reviewId'],expectedVersion=1,idempotencyKey='ack-source',claimId=source,action='accept',reason='已核对来源')
        out=repo.append_review_decision(self.conn,self.scope,actor,req)
        facts=out['decision']['brandConclusions'][0]['facts']
        self.assertTrue(facts)
        self.assertEqual(facts[0]['publicationStatus'],'source_only')
        self.assertEqual(facts[0].get('humanDecisionStatus'),'acknowledged_source')
        self.assertTrue(out['decision']['brandConclusions'][0]['insights'])
        repo.append_review_decision(self.conn,self.scope,actor,{**req,'action':'reject','idempotencyKey':'reject','expectedVersion':2})
        final=repo.append_review_decision(self.conn,self.scope,actor,{**req,'idempotencyKey':'attempt-ack','expectedVersion':3})
        self.assertFalse(final['decision']['brandConclusions'][0]['facts'])

    def test_highstakes_provider_prose_stays_pending(self):
        import brand_review_runtime as rt
        import brand_review_policy as p
        from tests.test_brand_review_policy import result,claim,WINDOW
        packet=p.build_layered_packet(result(),{**self.scope,'promptVersion':rt.PROMPT_VERSION,'reviewVersion':'1'},WINDOW)
        self.payload=rt.run_reviews(packet,lambda slot,*args:{'claims':[dict(claim(),text='销量必然翻倍') if slot=='review_3' else claim()]})
        repo.migrate(self.conn);review=self.save();cid=review['decision']['brandConclusions'][0]['unknowns'][0]['claimId']
        out=repo.append_review_decision(self.conn,self.scope,dict(user_id='u',role='admin',org_id='a'),dict(reviewId=review['reviewId'],expectedVersion=1,idempotencyKey='attempt',claimId=cid,action='accept',reason='尝试'))
        self.assertFalse(out['decision']['brandConclusions'][0]['insights'])
