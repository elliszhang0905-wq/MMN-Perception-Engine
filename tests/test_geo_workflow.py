"""Isolated workflow checks: synthetic evidence in temporary SQLite only."""
import base64
import tempfile
import unittest
from pathlib import Path

from geo.repository import GeoRepository
from geo.store import GeoError
Repo = GeoRepository
PNG = base64.b64encode(b'\x89PNG\r\n\x1a\nfixture').decode()


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Repo(Path(self.tmp.name) / 'geo.db')
        self.project = self.repo.create_project('a', {'name': '测试', 'target_key': 'target',
            'entities': [{'key': 'target', 'name': '测试汽车'}, {'key': 'other', 'name': '另一汽车'}]})
        self.pid = self.project['id']
        self.q = self.repo.add_question('a', self.pid, {'text': '通勤推荐哪些汽车？', 'recommendation_eligible': True})

    def sample(self, **extra):
        return self.repo.import_app('a', self.pid, {'question_version_id': self.q['version_id'],
            'question_text': self.q['text'], 'answer': '推荐测试汽车。',
            'sampled_at': '2026-10-01T10:00:00+08:00', **extra})

    def action(self, obs):
        return self.repo.save_action('a', self.pid, {'title': '增加产品说明', 'diagnosis': '样本缺少事实',
            'observation_ids': [obs['id']], 'entity_key': 'target'})

    def executed(self, obs):
        action = self.action(obs)
        action = self.repo.save_action('a', self.pid, {'status': 'approved'}, actor='reviewer', action_id=action['id'])
        return self.repo.save_action('a', self.pid, {'status': 'executed', 'execution_evidence': '已人工发布：https://example.com/a',
            'executed_at': '2026-10-02T10:00:00+08:00'}, action_id=action['id'])

    def test_import_unknown_and_immutable_review(self):
        obs = self.sample(answer='<script>throw 1</script> 推荐测试汽车。 https://example.com/fact')
        self.assertEqual(obs['channel'], 'doubao_app_manual')
        self.assertEqual(obs['sample_metadata']['new_session'], 'unknown')
        self.assertEqual(obs['sample_metadata']['personalization'], 'unknown')
        self.assertIsNone(obs['request_id'])
        self.assertIsNone(obs['search_observed'])
        self.assertEqual(obs['citations'][0]['source_type'], 'text_link')
        raw_hash = obs['raw_hash']
        review = self.repo.add_review('a', obs['id'], {'kind': 'entity', 'entity_key': 'target',
            'changes': {'recommended': False}, 'reason': '建议只代表提及', 'actor': 'forged'}, actor='human')
        self.assertEqual(review['actor'], 'human')
        fresh = self.repo.get_observation('a', obs['id'])
        effective = self.repo.apply_reviews(fresh)
        self.assertEqual(fresh['raw_hash'], raw_hash)
        self.assertTrue(effective['automatic_analysis']['entities'][0]['recommended'])
        self.assertFalse(effective['analysis']['entities'][0]['recommended'])
        self.assertTrue(effective['analysis']['entities'][0]['reviewed'])
        self.assertFalse(effective['analysis']['entities'][1].get('reviewed', False))
        self.assertIn('old', review)
        self.assertIn('new', review)

    def test_screenshot_only_and_question_mismatch_never_valid(self):
        obs = self.sample(answer='', screenshot_base64=PNG, screenshot_mime='image/png')
        self.assertFalse(obs['analysis']['valid_answer'])
        shot = self.repo.get_screenshot('a', obs['id'], obs['screenshots'][0]['id'])
        self.assertEqual(shot['base64'], PNG)
        with self.assertRaises(GeoError):
            self.repo.get_screenshot('b', obs['id'], obs['screenshots'][0]['id'])
        self.assertFalse(self.sample(question_text='另一问题')['analysis']['valid_answer'])
        self.assertFalse(self.sample(question_text='')['analysis']['valid_answer'])
        self.assertIsNone(self.sample(sampled_at=None)['sampled_at'])
        for fields in [{'screenshot_base64': '%%%','screenshot_mime': 'image/png'},
                       {'screenshot_base64': base64.b64encode(b'text').decode(), 'screenshot_mime': 'image/png'},
                       {'sampled_at': '2026-10-01'}, {'screenshot_url': 'https://example.com/x'}]:
            with self.assertRaises(GeoError): self.sample(**fields)

    def test_project_scope_and_review_rules(self):
        obs = self.sample()
        with self.assertRaises(GeoError): self.repo.add_review('b', obs['id'], {'kind': 'entity', 'changes': {}, 'reason': 'x'})
        with self.assertRaises(GeoError):
            self.repo.add_review('a', obs['id'], {'kind': 'entity', 'entity_key': 'other', 'changes': {'mentioned': True}, 'reason': 'x'})
        with self.assertRaises(GeoError):
            self.repo.add_review('a', obs['id'], {'kind': 'entity', 'entity_key': 'target', 'changes': {'mentioned': False, 'recommended': True}, 'reason': 'x'})
        other = self.repo.create_project('a', {'name': '另一项目', 'target_key': 'target', 'entities': [{'key': 'target', 'name': '测试汽车'}]})
        with self.assertRaises(GeoError):
            self.repo.import_app('a', other['id'], {'question_version_id': self.q['version_id'], 'answer': 'x'})
        with self.assertRaises(GeoError): self.repo.save_action('a', other['id'], {'title': 'x', 'observation_ids': [obs['id']]})
        with self.assertRaises(GeoError): self.repo.save_action('b', self.pid, {'title': 'x'})

    def test_action_gate_and_complete_offline_retest_freezes_versions(self):
        obs = self.sample(actual_model='explicit-offline-fixture-model', visible_search='off', new_session=True, personalization='off')
        action = self.action(obs)
        with self.assertRaises(GeoError):
            self.repo.save_action('a', self.pid, {'status': 'executed', 'execution_evidence': 'x', 'executed_at': '2026-10-02T00:00:00Z'}, action_id=action['id'])
        action = self.repo.save_action('a', self.pid, {'status': 'approved'}, actor='human', action_id=action['id'])
        self.assertEqual(action['approved_by'], 'human')
        with self.assertRaises(GeoError): self.repo.save_action('a', self.pid, {'status': 'executed'}, action_id=action['id'])
        action = self.repo.save_action('a', self.pid, {'status': 'executed', 'execution_evidence': '人工发布截图编号123',
            'executed_at': '2026-10-02T10:00:00+08:00'}, action_id=action['id'])
        self.repo.add_question('a', self.pid, {'text': '改版问题'}, question_id=self.q['id'])
        self.repo.update_entities('a', self.pid, [{'key': 'target', 'name': '新名称'}, {'key': 'other', 'name': '另一汽车'}])
        retest = self.repo.create_retest('a', action['id'], {'baseline_batch_id': obs['batch_id'], 'idempotency_key': 'retest-1'})
        self.assertFalse(retest['comparable'])
        batch = self.repo.get_batch('a', retest['batch_id'])
        self.assertEqual(batch['status'], 'draft')
        self.assertEqual(batch['manifest']['questions'][0]['id'], self.q['version_id'])
        self.assertEqual(batch['manifest']['entities'][0]['name'], '测试汽车')
        current = self.sample(batch_id=batch['id'], sampled_at='2026-10-03T10:00:00+08:00', answer='未提及目标车型', actual_model='explicit-offline-fixture-model', visible_search='off', new_session=True, personalization='off')
        retest = self.repo.get_retest('a', retest['id'])
        self.assertTrue(retest['comparable'])
        self.assertEqual(retest['comparison'][0]['mention_percentage_point_difference'], -100)
        self.assertEqual(retest['comparison'][0]['statement'], 'observed_difference_not_causal')
        with self.assertRaises(GeoError): self.sample(batch_id=batch['id'])
        self.assertEqual(self.repo.get_observation('a', current['id'])['raw_hash'], current['raw_hash'])

    def test_retest_time_and_condition_mismatch(self):
        obs = self.sample()
        action = self.executed(obs)
        condition = self.repo.add_condition('a', self.pid, {'surface': 'doubao_app_manual', 'api_mode': 'manual', 'mode': 'search_enabled'})
        retest = self.repo.create_retest('a', action['id'], {'baseline_batch_id': obs['batch_id'], 'idempotency_key': 'changed', 'condition_ids': [condition['id']]})
        self.sample(batch_id=retest['batch_id'], visible_search='on', sampled_at='2026-10-03T10:00:00+08:00')
        result = self.repo.get_retest('a', retest['id'])
        self.assertFalse(result['comparable'])
        self.assertIn('condition_mismatch', result['warnings'])
        self.assertEqual(result['comparison'], [])
        retest = self.repo.create_retest('a', action['id'], {'baseline_batch_id': obs['batch_id'], 'idempotency_key': 'early'})
        self.sample(batch_id=retest['batch_id'])
        self.assertIn('sample_not_after_execution', self.repo.get_retest('a', retest['id'])['warnings'])
        empty = self.sample(answer='')
        with self.assertRaises(GeoError): self.repo.create_retest('a', action['id'], {'baseline_batch_id': empty['batch_id'], 'idempotency_key': 'empty'})

    def test_app_pairing_channel_and_question_and_scope(self):
        obs = self.sample()
        with self.assertRaises(GeoError): self.sample(paired_observation_id=obs['id'])
        condition = self.repo.add_condition('a', self.pid, {'surface': 'ark_model_api', 'api_mode': 'chat', 'mode': 'non_search', 'model': 'm1'})
        batch = self.repo.create_batch('a', self.pid, {'question_version_ids': [self.q['version_id']], 'condition_ids': [condition['id']], 'repeats': 1, 'idempotency_key': 'api'})
        api_obs = self.repo.list_observations('a', self.pid, batch_id=batch['id'])['items'][0]
        pair = self.sample(paired_observation_id=api_obs['id'])
        comparison = self.repo.app_comparisons('a', self.pid)['items'][0]
        self.assertEqual(comparison['app_observation_id'], pair['id'])
        self.assertEqual(comparison['statement'], 'sample_difference_not_channel_equivalence')
        self.assertIn('api_sample_invalid', comparison['warnings'])
        with self.assertRaises(GeoError): self.repo.app_comparisons('b', self.pid)

    def test_retest_model_identity_unknown_and_changed_never_uplift(self):
        obs = self.sample()
        action = self.executed(obs)
        retest = self.repo.create_retest('a', action['id'], {'baseline_batch_id': obs['batch_id'], 'idempotency_key': 'unknown-model'})
        self.sample(batch_id=retest['batch_id'], sampled_at='2026-10-03T10:00:00+08:00')
        result = self.repo.get_retest('a', retest['id'])
        self.assertFalse(result['comparable'])
        self.assertIn('model_identity_unknown', result['warnings'])
        self.assertTrue(result['baseline_metrics']['groups'])
        self.assertTrue(result['current_metrics']['groups'])
        obs = self.sample(actual_model='fixture-m1')
        action = self.executed(obs)
        retest = self.repo.create_retest('a', action['id'], {'baseline_batch_id': obs['batch_id'], 'idempotency_key': 'changed-model'})
        self.sample(batch_id=retest['batch_id'], sampled_at='2026-10-03T10:00:00+08:00', actual_model='fixture-m2')
        self.assertIn('actual_model_mismatch', self.repo.get_retest('a', retest['id'])['warnings'])

    def test_fact_reviews_require_approved_scoped_baselines(self):
        obs = self.sample(answer='测试汽车指导价为10万元。')
        fact = self.repo.add_fact('a', self.pid, {'entity_key': 'target', 'year': '2026', 'trim': '标准版',
            'market': '中国', 'field': 'price', 'value': 100000, 'unit': 'CNY', 'conditions': {'market': '中国'},
            'effective_from': '2026-01-01', 'source_url': 'https://example.com/spec',
            'source_excerpt': '2026标准版指导价10万元', 'state': 'approved'}, actor='baseline-reviewer')
        payload = {'kind': 'fact', 'fact_index': 0, 'changes': {'verdict': 'supported'}, 'reason': '官方资料核对'}
        with self.assertRaises(GeoError): self.repo.add_review('a', obs['id'], payload)
        payload['changes']['baseline_id'] = fact['id']
        review = self.repo.add_review('a', obs['id'], payload, actor='human')
        self.assertEqual(review['new']['baseline_id'], fact['id'])
        self.assertEqual(self.repo.get_observation('a', obs['id'])['raw_hash'], obs['raw_hash'])
        draft = self.repo.add_fact('a', self.pid, {'entity_key': 'target', 'field': 'price', 'value': 100000})
        payload['changes']['baseline_id'] = draft['id']
        with self.assertRaises(GeoError): self.repo.add_review('a', obs['id'], payload)
        other = self.repo.create_project('b', {'name': '隔离', 'target_key': 'target', 'entities': [{'key': 'target', 'name': '测试汽车'}]})
        foreign = self.repo.add_fact('b', other['id'], {'entity_key': 'target', 'field': 'price', 'value': 100000})
        payload['changes'] = {'verdict': 'unverified', 'baseline_id': foreign['id']}
        with self.assertRaises(GeoError): self.repo.add_review('a', obs['id'], payload)

    def test_manual_frozen_condition_must_match_visible_setting(self):
        obs = self.sample(visible_search='off')
        action = self.executed(obs)
        retest = self.repo.create_retest('a', action['id'], {'baseline_batch_id': obs['batch_id'], 'idempotency_key': 'visible'})
        with self.assertRaises(GeoError): self.sample(batch_id=retest['batch_id'], visible_search='on')

    def test_unknown_search_is_distinct_and_retest_cannot_assume_off(self):
        unknown = self.sample(actual_model='explicit-offline-fixture-model')
        off = self.sample(visible_search='off')
        self.assertEqual(unknown['condition']['mode'], 'unknown')
        self.assertNotEqual(unknown['condition']['condition_hash'], off['condition']['condition_hash'])
        action = self.executed(unknown)
        retest = self.repo.create_retest('a', action['id'], {'baseline_batch_id': unknown['batch_id'], 'idempotency_key': 'unknown-search'})
        with self.assertRaises(GeoError): self.sample(batch_id=retest['batch_id'], visible_search='off')
        self.sample(batch_id=retest['batch_id'], actual_model='explicit-offline-fixture-model', sampled_at='2026-10-03T10:00:00+08:00')
        result = self.repo.get_retest('a', retest['id'])
        self.assertFalse(result['comparable'])
        self.assertIn('visible_search_unknown', result['warnings'])
        self.assertEqual(result['comparison'], [])
        self.assertTrue(result['baseline_metrics']['groups'])
        self.assertTrue(result['current_metrics']['groups'])

    def test_app_unknown_or_changed_session_personalization_are_not_comparable(self):
        cases = [
            ({}, {'new_session': False, 'personalization': 'on'}, {'new_session_unknown', 'personalization_unknown'}),
            ({'new_session': True, 'personalization': 'off'}, {'new_session': False, 'personalization': 'on'}, {'new_session_mismatch', 'personalization_mismatch'}),
            ({'new_session': True, 'personalization': 'off'}, {'new_session': True}, {'personalization_unknown'}),
        ]
        for index, (before, after, expected) in enumerate(cases):
            with self.subTest(index=index):
                baseline = self.sample(actual_model='explicit-offline-fixture-model', visible_search='off', **before)
                action = self.executed(baseline)
                retest = self.repo.create_retest('a', action['id'], {'baseline_batch_id': baseline['batch_id'], 'idempotency_key': f'app-metadata-{index}'})
                self.sample(batch_id=retest['batch_id'], actual_model='explicit-offline-fixture-model', visible_search='off',
                    sampled_at='2026-10-03T10:00:00+08:00', answer='未提及目标车型', **after)
                result = self.repo.get_retest('a', retest['id'])
                self.assertFalse(result['comparable'])
                self.assertTrue(expected.issubset(result['warnings']))
                self.assertEqual(result['comparison'], [])
                self.assertTrue(result['baseline_metrics']['groups'])
                self.assertTrue(result['current_metrics']['groups'])

    def test_import_validation_is_atomic_and_screenshot_ids_bound(self):
        before = self.repo.list_batches('a', self.pid)['total']
        for extra in ({'answer': 1}, {'personalization': 'disabled'}, {'new_session': 1}, {'repeat_index': 'no'},
            {'screenshot_base64': base64.b64encode(b'\x89PNG\r\n\x1a\n' + b'x' * (2*1024*1024)).decode(), 'screenshot_mime': 'image/png'}):
            with self.assertRaises(GeoError): self.sample(**extra)
        self.assertEqual(self.repo.list_batches('a', self.pid)['total'], before)
        obs = self.sample(screenshot_base64=PNG, screenshot_mime='image/png')
        other = self.sample()
        with self.assertRaises(GeoError): self.repo.get_screenshot('a', other['id'], obs['screenshots'][0]['id'])
        audit = self.repo.list_audit('a', self.pid)
        self.assertGreater(audit['total'], 0)
        with self.assertRaises(GeoError): self.repo.list_audit('b', self.pid)

    def test_review_rank_is_integer_and_invalid_input_is_domain_error(self):
        obs = self.sample()
        for rank in ('1', True, 0, -1):
            with self.assertRaises(GeoError):
                self.repo.add_review('a', obs['id'], {'kind': 'entity', 'entity_key': 'target',
                    'changes': {'rank': rank}, 'reason': '重新核对'})
        with self.assertRaises(GeoError):
            self.repo.add_review('a', obs['id'], {'kind': [], 'changes': {'mentioned': True}, 'reason': 'x'})
        with self.assertRaises(GeoError): self.repo.save_action('a', self.pid, {'title': 'x', 'status': []})
        with self.assertRaises(GeoError): self.sample(screenshot_base64=PNG, screenshot_mime=[])


if __name__ == '__main__': unittest.main()
