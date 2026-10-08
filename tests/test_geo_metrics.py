import unittest
try:
    from geo.metrics import compute_metrics
except ImportError:
    compute_metrics = None


def record(i, mention=False, recommend=False, **changes):
    row = dict(id=str(i), question_version_id='q1', question=dict(unbranded=True,
        recommendation_eligible=True, ranking_eligible=True, fact_eligible=True),
        condition=dict(id='c1', condition_hash='h1', surface='responses', mode='plain', model='fixture'),
        channel='api', status='succeeded', answer='完整回答', sampled_at='2026-10-08',
        analysis=dict(valid_answer=True, refusal=False, entities=[dict(entity_key='l6', mentioned=mention,
        recommended=recommend, rank=None, needs_review=False)], fact_checks=[]),
        citations=[], attempts=[], reviews=[], reviewed=False)
    row.update(changes)
    return row


class GeoMetricsTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(compute_metrics), 'compute_metrics feature is missing')

    def group(self, rows):
        return compute_metrics(rows, 'l6', ['l6', 'su7'])['groups'][0]

    def test_at09_twelve_observations(self):
        rows = [record(i, i < 4, i < 3) for i in range(10)]
        rows += [record(10, status='failed'), record(11, status='failed')]
        group = self.group(rows)
        self.assertEqual(group['valid_n'], 10)
        self.assertEqual(group['total_n'], 12)
        self.assertEqual(group['failed_n'], 2)
        self.assertEqual(group['answer_level_rates']['mention_rate'], .4)
        self.assertEqual(group['answer_level_rates']['recommendation_rate'], .3)
        self.assertEqual(group['metrics']['mention_rate'], .4)

    def test_equal_question_weight_and_eligibility(self):
        rows = [record(i, True, True) for i in range(3)]
        rows.append(record(4, question_version_id='q2'))
        group = self.group(rows)
        self.assertEqual(group['metrics']['mention_rate'], .5)
        self.assertEqual(group['answer_level_rates']['mention_rate'], .75)
        self.assertEqual(group['repeat_consistency'][0]['mention']['yes_n'], 3)
        rows[-1]['question']['recommendation_eligible'] = False
        self.assertEqual(self.group(rows)['denominators']['recommendation_rate'], 3)

    def test_invalid_missing_review_and_refusal(self):
        rows = [record(1, analysis=None), record(2, answer=''), record(3, status='tool_only'),
            record(4, status='partial'), record(5, status='parse_failed'),
            record(6, analysis=dict(valid_answer=False, refusal=True, entities=[], fact_checks=[])),
            record(7, reviewed=True)]
        group = self.group(rows)
        self.assertEqual(group['valid_n'], 1)
        self.assertEqual(group['analysis_missing_n'], 1)
        self.assertEqual(group['refused_n'], 1)
        self.assertEqual(group['empty_n'], 1)
        self.assertEqual(group['failed_n'], 3)
        self.assertEqual(group['reviewed_n'], 1)

    def test_no_samples_and_separate_conditions(self):
        self.assertEqual(compute_metrics([], 'l6', ['l6'])['groups'], [])
        group = self.group([record(1, status='failed')])
        self.assertIsNone(group['metrics']['mention_rate'])
        rows = [record(1), record(2, channel='app'), record(3, condition=dict(
            condition_hash='h2', surface='responses', mode='plain', model='fixture'))]
        self.assertEqual(len(compute_metrics(rows, 'l6', ['l6'])['groups']), 3)

    def test_fixed_share_explicit_rank_and_unknown(self):
        row = record(1, True, True)
        row['analysis']['entities'] += [dict(entity_key='su7', mentioned=True, recommended=True, rank=1),
            dict(entity_key='outside', mentioned=True, recommended=True, rank=1)]
        group = self.group([row])
        self.assertEqual(group['metrics']['recommendation_share'], .5)
        self.assertEqual(group['metrics']['first_recommendation_rate'], 0)
        self.assertEqual(group['no_explicit_ranking_n'], 0)
        row['analysis']['entities'][1]['rank'] = None
        self.assertEqual(self.group([row])['no_explicit_ranking_n'], 1)
        row['analysis']['entities'][0]['recommended'] = None
        row['analysis']['entities'][0]['needs_review'] = True
        group = self.group([row])
        self.assertEqual(group['needs_review_n'], 1)
        self.assertIsNone(group['metrics']['recommendation_rate'])

    def test_frozen_question_sets_and_capability_contract(self):
        rows = [record(1, question_set_hash='set-a'), record(2, question_set_hash='set-b')]
        self.assertEqual(len(compute_metrics(rows, 'l6', ['l6'])['groups']), 2)
        row = record(3)
        row['condition']['capabilities'] = {'structured_citations': True}
        group = self.group([row])
        self.assertEqual(group['citation_capability_coverage'], 1)
        self.assertEqual(group['no_verifiable_citation_n'], 1)

    def test_review_coverage_and_answer_invalid_visible(self):
        row = record(1)
        row['analysis']['valid_answer'] = False
        group = self.group([row])
        self.assertIn('invalid_answer_n', group)
        self.assertEqual(group['invalid_answer_n'], 1)
        self.assertIsNone(group['metrics']['mention_rate'])
        row = record(2)
        row['analysis']['fact_checks'] = [dict(verdict='unverified', needs_review=True)]
        self.assertEqual(self.group([row])['fact_needs_review_n'], 1)

    def test_missing_recommendation_not_false_share(self):
        row = record(1, True, True)
        group = self.group([row])
        self.assertIsNone(group['metrics']['recommendation_share'])
        self.assertIn('share_unresolved_n', group)
        self.assertEqual(group['share_unresolved_n'], 1)

    def test_completion_states_and_request_failures_are_separate(self):
        statuses = ['refused', 'empty', 'unanalysable', 'failed', 'queued', 'draft',
                    'blocked', 'cancelled', 'pending', 'billing_uncertain']
        rows = [record(i, status=status) for i, status in enumerate(statuses)]
        group = self.group(rows)
        self.assertEqual(group['failed_n'], 1)
        self.assertEqual(group['refused_n'], 1)
        self.assertEqual(group['empty_n'], 1)
        self.assertEqual(group['invalid_answer_n'], 1)
        self.assertIn('pending_n', group)
        self.assertEqual(group['pending_n'], 3)
        self.assertEqual(group['cancelled_n'], 1)
        self.assertEqual(group['blocked_n'], 1)
        self.assertEqual(group['draft_n'], 1)
        self.assertEqual(group['uncertain_n'], 1)
        self.assertEqual(group['valid_n'], 0)

    def test_drilldown_dates_offline_and_frozen_missing_questions(self):
        row = record('a', evidence_origin='offline_fixture', sampled_at='2026-10-08T01:00:00Z',
                     fixed_question_ids=['q1', 'q2'])
        later = record('b', sampled_at='2026-10-08T02:00:00Z', fixed_question_ids=['q1', 'q2'])
        group = self.group([row, later])
        self.assertIn('offline_fixture_n', group)
        self.assertEqual(group['offline_fixture_n'], 1)
        self.assertEqual(group['observation_ids'], ['a', 'b'])
        self.assertEqual(group['sampled_at_min'], row['sampled_at'])
        self.assertEqual(group['sampled_at_max'], later['sampled_at'])
        self.assertEqual(group['question_n'], 2)
        self.assertIn('q2', group['missing_question_ids'])
        self.assertEqual(group['per_question']['q2']['total_n'], 0)

    def test_frozen_entity_fact_vectors_do_not_pool(self):
        rows = [record(1, question_set_hash='q-scope', entity_set_hash='entities-a', fact_baseline_hash='facts-a'),
                record(2, question_set_hash='q-scope', entity_set_hash='entities-b', fact_baseline_hash='facts-a'),
                record(3, question_set_hash='q-scope', entity_set_hash='entities-a', fact_baseline_hash='facts-b')]
        for row in rows:
            row['condition']['model'] = 'actual-model'
            row['condition']['configured_model'] = 'deployment-name'
        groups = compute_metrics(rows, 'l6', ['l6'])['groups']
        self.assertEqual(len(groups), 3)
        self.assertEqual({(g['entity_set_hash'], g['fact_baseline_hash']) for g in groups},
                         {('entities-a', 'facts-a'), ('entities-b', 'facts-a'), ('entities-a', 'facts-b')})
        for group in groups:
            self.assertEqual(group['condition_hash'], 'h1')
            self.assertEqual(group['question_set_hash'], 'q-scope')
            self.assertEqual(group['model'], 'actual-model')
            self.assertEqual(group['configured_model'], 'deployment-name')
            self.assertEqual(group['valid_n'], 1)

    def test_boolean_is_not_a_rank(self):
        row = record(1, True, True)
        row['analysis']['entities'][0]['rank'] = True
        group = self.group([row])
        self.assertEqual(group['metrics']['first_recommendation_rate'], 0)
        self.assertEqual(group['no_explicit_ranking_n'], 1)

    def test_field_judgment_coverage_missing_and_unequal_repeats(self):
        unknown = record('unknown', question_version_id='q-unknown')
        unknown['analysis']['entities'][0].update(mentioned=None, recommended=None, needs_review=True)
        missing = record('missing', question_version_id='q-missing', analysis=None)
        proven = record('proven', True, True, question_version_id='q-proven')
        proven['analysis']['entities'][0].update(recommended=None, needs_review=True)
        rows = [unknown, missing, proven,
                record('yes1', True, True, question_version_id='q-repeat'),
                record('yes2', True, True, question_version_id='q-repeat'),
                record('no', False, False, question_version_id='q-repeat')]
        for row in rows:
            row['fixed_question_ids'] = ['q-unknown', 'q-missing', 'q-proven', 'q-repeat', 'q-absent']
        group = self.group(rows)
        self.assertIn('judgment_coverage', group)
        mention = group['judgment_coverage']['mention']
        self.assertEqual(mention, dict(judged_n=4, candidate_n=6, unresolved_n=2, rate=4 / 6))
        recommendation = group['judgment_coverage']['recommendation']
        self.assertEqual(recommendation, dict(judged_n=3, candidate_n=6, unresolved_n=3, rate=.5))
        self.assertAlmostEqual(group['metrics']['mention_rate'], (1 + 2 / 3) / 2)
        self.assertAlmostEqual(group['metrics']['recommendation_rate'], 2 / 3)
        self.assertEqual(group['eligible_question_n']['mention'], 5)
        self.assertEqual(group['equal_weight_judged_question_n']['mention'], 2)
        self.assertEqual(set(group['zero_judgment_question_ids']['mention']), {'q-unknown', 'q-missing', 'q-absent'})
        self.assertEqual(group['per_question']['q-proven']['judgment_coverage']['mention']['rate'], 1)
        self.assertEqual(group['per_question']['q-proven']['judgment_coverage']['recommendation']['rate'], 0)
        self.assertIsNone(group['per_question']['q-absent']['judgment_coverage']['mention']['rate'])
        self.assertEqual(group['judgment_unresolved_causes']['mention']['analysis_missing_n'], 1)
        self.assertEqual(group['judgment_unresolved_causes']['mention']['indeterminate_n'], 1)
        self.assertEqual(group['needs_review_n'], 2)

    def test_coverage_excludes_failed_refused_empty_unanalysable(self):
        rows = [record(1, status='failed'), record(2, status='refused'), record(3, status='empty'),
                record(4, status='unanalysable'), record(5, analysis=None)]
        group = self.group(rows)
        self.assertIn('judgment_coverage', group)
        self.assertEqual(group['judgment_coverage']['mention']['candidate_n'], 1)
        self.assertEqual(group['judgment_coverage']['mention']['judged_n'], 0)
        self.assertEqual(group['judgment_coverage']['mention']['rate'], 0)

    def test_facts_citations_costs_and_sets(self):
        row = record(1)
        row['analysis']['fact_checks'] = [dict(verdict=v) for v in
            ['supported', 'contradicted', 'outdated', 'unverified', 'subjective']]
        row['citations'] = [dict(source_type='structured', url='https://official.test/a'),
            dict(source_type='text_link', normalized_url='https://official.test/b')]
        row['citation_capability'] = True
        row['attempts'] = [dict(cost=2, cost_unknown=False), dict(cost=None, cost_unknown=True, billing_uncertain=True)]
        group = self.group([row])
        self.assertAlmostEqual(group['metrics']['fact_error_rate'], 2 / 3)
        self.assertEqual(group['fact_counts']['unverified'], 1)
        self.assertEqual(group['citation_rates']['structured']['official.test'], 1)
        self.assertEqual(group['citation_rates']['text_link']['official.test'], 1)
        self.assertEqual(group['cost']['known_total'], 2)
        self.assertEqual(group['cost']['unknown_attempt_n'], 1)
        self.assertEqual(group['sets']['unbranded']['valid_n'], 1)
        self.assertIsNone(group['sets']['branded']['metrics']['mention_rate'])


if __name__ == '__main__':
    unittest.main()
