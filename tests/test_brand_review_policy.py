"""Synthetic, offline policy contracts; no model calls or business data."""
import copy
import importlib.util
import unittest

if importlib.util.find_spec('brand_review_policy'):
    import brand_review_policy as policy
else:
    policy = None

SCOPE = dict(orgId='org', edition='china', projectId='project', snapshotId='snap',
             promptVersion='p4', reviewVersion='r1')
WINDOW = dict(start='2026-09-01', end='2026-09-08')


def evidence(eid='a', brand='甲', **extra):
    return dict(id=eid, brandName=brand, platform='微博', text='该来源宣称新品发布成功。',
                sourceUrl='https://example.org/' + eid, publishedAt='2026-09-03', **extra)


def result(items=None):
    return dict(modelComparisons=[dict(model='甲', role='own'), dict(model='乙', role='competitor')],
                verifiedComparisonItems=items if items is not None else [evidence()])


def claim(cid='c', eid='a', **extra):
    return dict(claimId=cid, kind='inference', brand='甲', predicate='sample_mentions',
                topic='新品发布', evidenceRefs=[dict(evidenceId=eid, quote='新品发布')], dependsOn=[], **extra)


class PolicyTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(policy, 'Missing production brand_review_policy API')

    def packet(self, items=None):
        return policy.build_layered_packet(result(items), SCOPE, WINDOW)

    def fuse(self, claims=None, packet=None, outputs=None):
        packet = packet or self.packet()
        outputs = outputs if outputs is not None else {k: {'claims': copy.deepcopy(claims or [claim()])} for k in ['a','b','c']}
        outputs = {{'a':'review_1','b':'review_2','c':'review_3'}.get(k,k):v for k,v in outputs.items()}
        records = policy.validate_layered_reviews(outputs, packet, actor_id='server:policy', server_time='2026-09-08T00:00:00Z')
        return policy.fuse_layered_reviews(outputs, packet, records)

    def row(self, **kwargs):
        return self.fuse(**kwargs)['brandConclusions'][0]

    def test_status_matrix(self):
        for args, expected in [
            (('source_fact', [], 2, 0, []), 'source_only'),
            (('inference', ['source_conflict'], 3, 3, []), 'blocked'),
            (('inference', [], 3, 2, ['opposed']), 'disputed'),
            (('inference', [], 3, 3, []), 'supported'),
            (('inference', [], 2, 2, []), 'review_incomplete')]:
            self.assertEqual(policy.layer_status(*args), expected)

    def test_frozen_scope_and_full_source_anchors(self):
        data = result()
        packet = policy.build_layered_packet(data, SCOPE, WINDOW)
        data['verifiedComparisonItems'][0]['text'] = 'changed'
        self.assertEqual(packet['evidence'][0]['text'], '该来源宣称新品发布成功。')
        self.assertEqual(packet['scope'], SCOPE)
        self.assertEqual(packet['evidence'][0]['publishedAt'], '2026-09-03')

    def test_source_survives_incomplete_review_without_confirming_source_truth(self):
        row = self.row(outputs={'a': {'claims': [claim()]}})
        self.assertIn('来源提及', row['facts'][0]['text'])
        self.assertIn('不代表', row['facts'][0]['text'])
        self.assertEqual(row['insights'], [])

    def test_useful_canonical_observation_not_model_prose(self):
        row = self.row(claims=[claim(text='销量必然上涨', confidence=1)])
        self.assertEqual(row['insights'], [])
        row = self.row()
        self.assertEqual(row['insights'][0]['publicationStatus'], 'supported')
        self.assertIn('公开样本', row['insights'][0]['text'])

    def test_fabricated_quote_blocked(self):
        c = claim(); c['evidenceRefs'][0]['quote'] = '销量翻倍'
        self.assertEqual(self.row(claims=[c])['insights'], [])

    def test_wrong_brand_or_time_and_invalid_url_block_source(self):
        for field, value in [('brandName','丙'), ('publishedAt','2025-01-01'), ('sourceUrl','javascript:bad')]:
            e = evidence(); e[field] = value
            self.assertEqual(self.row(packet=self.packet([e]))['facts'], [])

    def test_title_only_remains_source_only(self):
        e = evidence(); e['title'] = e.pop('text')
        row = self.row(packet=self.packet([e]))
        self.assertTrue(row['facts'])
        self.assertFalse(row['insights'])

    def test_different_ids_same_proposition_supported_and_reposts_dedup(self):
        items = [evidence(x) for x in ['a','b','c']]
        outputs = {x: {'claims':[claim(eid=x)]} for x in ['a','b','c']}
        row = self.row(packet=self.packet(items), outputs=outputs)
        self.assertEqual(len(row['insights']), 1)
        self.assertEqual(len(row['insights'][0]['evidenceRefs']), 3)
        self.assertEqual(row['independentSourceCount'], 1)

    def test_opposite_trends_not_normalized(self):
        a, b = claim(), claim()
        a.update(predicate='trend', direction='increase')
        b.update(predicate='trend', direction='decrease')
        row = self.row(outputs={'a':{'claims':[a]}, 'b':{'claims':[a]}, 'c':{'claims':[b]}})
        self.assertFalse(row['insights'])
        self.assertTrue(row['disputes'])

    def test_pair_requires_both_sides_same_platform(self):
        c = claim(); c.pop('brand'); c.update(ownBrand='甲',competitor='乙',predicate='both_samples_mention')
        self.assertFalse(self.fuse(claims=[c])['pairwiseConclusions'][0]['insights'])
        c['evidenceRefs'].append(dict(evidenceId='b',quote='新品发布'))
        pair = self.fuse(claims=[c], packet=self.packet([evidence(), evidence('b','乙')]))['pairwiseConclusions'][0]
        self.assertTrue(pair['insights'])
        e = evidence('b','乙'); e['platform']='抖音'
        self.assertFalse(self.fuse(claims=[c], packet=self.packet([evidence(), e]))['pairwiseConclusions'][0]['insights'])

    def test_record_tampering_and_packet_mutation_fail_closed(self):
        p = self.packet(); outputs = {x:{'claims':[claim()]} for x in policy.REVIEWER_IDS}
        records = policy.validate_layered_reviews(outputs,p,actor_id='server',server_time='2026-09-08')
        records[0]['status'] = 'forged'
        self.assertFalse(policy.fuse_layered_reviews(outputs,p,records)['brandConclusions'][0]['insights'])
        p['evidence'][0]['text']='changed'
        with self.assertRaises(ValueError):
            policy.fuse_layered_reviews(outputs,p,records)

    def test_dependency_cycle_and_missing_dependency_block(self):
        for deps in [['c'], ['missing']]:
            c = claim(); c['dependsOn'] = deps
            self.assertFalse(self.row(claims=[c])['insights'])

    def test_model_verdict_cannot_supply_support(self):
        c = claim(); c.update(predicate='market_leadership', verdict='supported')
        self.assertFalse(self.row(claims=[c])['insights'])

    def test_action_requires_contract_and_available_dependencies(self):
        action = dict(claimId='act',kind='action',brand='甲',predicate='manual_observation',
                      topic='新品发布', evidenceRefs=[dict(evidenceId='a',quote='新品发布')], dependsOn=['c'])
        self.assertFalse(self.row(claims=[claim(),action])['actionOptions'])
        action['actionContract'] = dict(policy.OBSERVATION_CONTRACT)
        row = self.row(claims=[claim(), action])
        self.assertTrue(row['actionOptions'])
        self.assertFalse(row['actionOptions'][0]['allowExecution'])
        c = claim(); c['evidenceRefs'][0]['quote']='不存在'
        self.assertFalse(self.row(claims=[c,action])['actionOptions'])

    def test_duplicate_provider_or_claim_does_not_inflate_support(self):
        row = self.row(outputs={'a':{'claims':[claim(),claim()]},'b':{'claims':[claim()]}})
        self.assertFalse(row['insights'])

    def test_cross_scope_input_rejected(self):
        e = evidence(); e['orgId']='other'
        self.assertFalse(self.row(packet=self.packet([e]))['facts'])

    def test_direction_cannot_be_silently_dropped_from_observation(self):
        self.assertFalse(self.row(claims=[claim(direction='increase')])['insights'])

    def test_unpublished_candidate_traceability_is_escaped(self):
        row = self.row(claims=[claim(text='<script>opaque candidate</script>')])
        self.assertEqual(row['unknowns'][0].get('candidateText'), '&lt;script&gt;opaque candidate&lt;/script&gt;')

    def test_source_conflict_blocks_dependents_not_unrelated_fact(self):
        e = evidence(); e['sourceConflict']=True
        row = self.row(packet=self.packet([e,evidence('b')]))
        self.assertEqual(len(row['facts']),1)
        self.assertFalse(row['insights'])

    def test_repost_original_provenance_dedup_with_edited_text(self):
        a,b = evidence(),evidence('b')
        a['originalSourceUrl']=b['originalSourceUrl']='https://example.org/original'
        b['text']='转发：'+b['text']
        self.assertEqual(self.row(packet=self.packet([a,b]))['independentSourceCount'],1)

    def test_forged_record_rehashed_still_recomputed(self):
        p=self.packet(); c=claim(text='无依据销量增长')
        outputs={x:{'claims':[c]} for x in policy.REVIEWER_IDS}
        records=policy.validate_layered_reviews(outputs,p,actor_id='server',server_time='2026-09-08')
        for r in records:
            r['status']='supported'
            r['artifactHash']=policy._hash({k:v for k,v in r.items() if k!='artifactHash'})
        self.assertFalse(policy.fuse_layered_reviews(outputs,p,records)['brandConclusions'][0]['insights'])

    def test_negated_source_remains_literal_not_event_confirmation(self):
        e=evidence(); e['text']='没有新品发布活动。'
        row=self.row(packet=self.packet([e]))
        self.assertIn('字样',row['insights'][0]['text'])
        self.assertIn('不确认事件',row['insights'][0]['text'])

    def test_datetime_window_end_exclusive_and_timezone(self):
        window=dict(start='2026-09-03T00:00:00+08:00',end='2026-09-04T00:00:00+08:00',endExclusive=True)
        for instant,valid in [('2026-09-02T16:00:00Z',True),('2026-09-03T16:00:00Z',False)]:
            e=evidence(); e['publishedAt']=instant
            p=policy.build_layered_packet(result([e]),SCOPE,window)
            self.assertEqual(bool(self.row(packet=p)['facts']),valid)

    def test_brand_model_mapping_and_explicit_model_mismatch(self):
        e=evidence(); e['normalizedModel']='甲车型一'
        self.assertTrue(self.row(packet=self.packet([e]))['facts'])
        c=claim(model='甲车型二')
        self.assertFalse(self.row(packet=self.packet([e]),claims=[c])['insights'])

    def test_unknown_provider_cannot_complete_review(self):
        row=self.row(outputs={x:{'claims':[claim()]} for x in ['x','y','z']})
        self.assertFalse(row['insights'])

    def test_action_contract_cannot_smuggle_budget_or_sales_promises(self):
        action = dict(claimId='act',kind='action',brand='甲',predicate='manual_observation',
                      topic='新品发布', evidenceRefs=[dict(evidenceId='a',quote='新品发布')], dependsOn=['c'],
                      actionContract={k:'立即增投一千万元并保证销量翻倍' for k in policy.ACTION_FIELDS})
        row=self.row(claims=[claim(),action])
        self.assertFalse(row['actionOptions'])
        self.assertTrue(row['unknowns'])

    def test_opposing_prose_same_provider_same_proposition_is_preserved(self):
        opposed=claim(cid='opposed',text='没有任何新品发布相关样本，因此应当立即停止投放')
        row=self.row(outputs={'a':{'claims':[claim(),opposed]},'b':{'claims':[claim()]},'c':{'claims':[claim()]}})
        self.assertFalse(row['insights'])
        self.assertTrue(row['disputes'])
        self.assertIn('没有任何新品发布',str(row['unknowns']))

    def test_public_dependency_ids_resolve_to_public_claim_ids(self):
        action = dict(claimId='act',kind='action',brand='甲',predicate='manual_observation',
                      topic='新品发布', evidenceRefs=[dict(evidenceId='a',quote='新品发布')], dependsOn=['c'],
                      actionContract=dict(policy.OBSERVATION_CONTRACT))
        row=self.row(claims=[claim(),action])
        self.assertEqual(row['actionOptions'][0]['dependsOn'],[row['insights'][0]['claimId']])


if __name__ == '__main__':
    unittest.main()
