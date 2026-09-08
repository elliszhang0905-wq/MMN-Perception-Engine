"""Offline mechanism tests. All origins/approvals below are synthetic test doubles."""
import copy
import hashlib
import importlib.util
import json
import unittest

from tests.test_brand_review_policy import claim, evidence, result, SCOPE, WINDOW
from brand_review_policy import build_layered_packet, REVIEWER_IDS, RULE_VERSION

if importlib.util.find_spec('mmn_eval.brand_review'):
    from mmn_eval.brand_review import evaluate_brand_reviews, RUBRIC
else:
    evaluate_brand_reviews = None


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def make_case(index=0, category='publish'):
    scope = dict(SCOPE, snapshotId=f'synthetic-snapshot-{index}')
    source = evidence()
    source['text'] += f'样本序号{index}。'
    packet = build_layered_packet(result([source]), scope, WINDOW)
    c = claim()
    reviews = {slot: {'claims': [copy.deepcopy(c)]} for slot in REVIEWER_IDS}
    if category == 'source_only':
        reviews.pop('review_3')
    elif category == 'dispute':
        reviews['review_3']['claims'].append(claim(cid='opposition', text='存在未解决解释'))
    elif category == 'block':
        for output in reviews.values():
            output['claims'][0]['evidenceRefs'][0]['quote'] = '不存在的引用'
    return {'caseId': f'synthetic-case-{index}', 'sourceKind': 'synthetic',
            'evidenceGroupId': f'test-double-group-{index}', 'declarationId': f'test-double-declaration-{index}',
            'snapshotId': scope['snapshotId'], 'split': 'holdout' if index % 2 else 'development',
            'packet': packet, 'reviews': reviews, 'targetClaimId': 'c',
            'gold': {'expectedClass': category, 'recoverable': category in ('publish', 'source_only'),
                     'v3Blocked': True}}


def approved_test_double(cases):
    """Tests only: simulate an independently pinned human approval registry."""
    approval = {'datasetHash': digest(cases), 'ruleVersion': RULE_VERSION,
                'approvedBy': 'synthetic-product-owner', 'approvedAt': '2026-09-08T00:00:00Z',
                'thresholdsApproved': True, 'rubric': dict(RUBRIC),
                'cases': [{'caseId': c['caseId'], 'caseHash': digest(c),
                           'sourceKind': c['sourceKind'], 'evidenceGroupId': c['evidenceGroupId'],
                           'declarationId': c['declarationId'],
                           'sourceRecordId': f'test-double-only:{c["caseId"]}'} for c in cases]}
    return approval, digest(approval)


class BrandReviewEvalTest(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(evaluate_brand_reviews, 'Missing brand review evaluator')

    def evaluate(self, cases, approved=False, **kwargs):
        approval, pin = approved_test_double(cases) if approved else (None, None)
        return evaluate_brand_reviews(cases, approval=approval, trusted_approval_sha256=pin, **kwargs)

    def full_test_double(self):
        cases = [make_case(i, ('publish', 'source_only', 'dispute', 'block')[i % 4]) for i in range(60)]
        # Deliberately simulated provenance for positive contract tests only.
        for c in cases[:30]:
            c['sourceKind'] = 'historical_redacted'
        return cases

    def test_no_gold_returns_not_ready_not_success_rate(self):
        report = self.evaluate([make_case()])
        self.assertEqual(report['status'], 'not_ready')
        self.assertIsNone(report['metrics']['recoveryRate'])
        self.assertIn('human_approval_missing', report['blockers'])

    def test_zero_denominator_never_passes(self):
        cases = self.full_test_double()
        for c in cases:
            c['gold']['recoverable'] = False
        report = self.evaluate(cases, True)
        self.assertEqual(report['status'], 'not_ready')
        self.assertEqual(report['metrics']['recoveryDenominator'], 0)
        self.assertIsNone(report['metrics']['recoveryRate'])

    def test_synthetic_cannot_masquerade_as_historical(self):
        cases = [make_case(i) for i in range(60)]
        approval, pin = approved_test_double(cases)
        cases[0]['sourceKind'] = 'historical_redacted'
        report = evaluate_brand_reviews(cases, approval=approval, trusted_approval_sha256=pin)
        self.assertEqual(report['status'], 'not_ready')
        self.assertIn('approval_dataset_mismatch', report['blockers'])

    def test_unpinned_or_tampered_approval_is_not_authority(self):
        cases = self.full_test_double()
        approval, pin = approved_test_double(cases)
        for expected_pin in (None, '0' * 64):
            report = evaluate_brand_reviews(cases, approval=approval, trusted_approval_sha256=expected_pin)
            self.assertEqual(report['status'], 'not_ready')
        approval['approvedBy'] = 'spoofed'
        report = evaluate_brand_reviews(cases, approval=approval, trusted_approval_sha256=pin)
        self.assertEqual(report['status'], 'not_ready')

    def test_snapshot_cannot_leak_between_development_and_holdout(self):
        cases = self.full_test_double()
        cases[1]['snapshotId'] = cases[0]['snapshotId']
        cases[1]['packet'] = cases[0]['packet']
        report = self.evaluate(cases, True)
        self.assertEqual(report['status'], 'not_ready')
        self.assertIn('snapshot_split_leakage', report['blockers'])

    def test_minor_but_critical_unsafe_case_stops_quality_gate(self):
        cases = self.full_test_double()
        cases[0]['gold']['expectedClass'] = 'block'
        cases[0]['gold']['recoverable'] = False
        report = self.evaluate(cases, True)
        self.assertEqual(report['status'], 'failed')
        self.assertEqual(report['metrics']['unsafePublications'], 1)
        self.assertLess(report['metrics']['hardBlockRate'], 1)

    def test_actual_policy_is_recomputed_not_supplied_verdict(self):
        c = make_case(category='block')
        c['candidateResult'] = {'status': 'available', 'publicationStatus': 'supported'}
        report = self.evaluate([c], True)
        self.assertEqual(report['cases'][0]['actualClass'], 'block')

    def test_development_success_does_not_hide_holdout_recovery_failure(self):
        cases = self.full_test_double()
        for c in [c for c in cases if c['gold']['expectedClass'] == 'source_only'][:4]:
            for output in c['reviews'].values():
                output['claims'][0]['evidenceRefs'][0]['quote'] = '不存在的引用'
        report = self.evaluate(cases, True)
        self.assertGreater(report['metrics']['recoveryRate'], .8)
        self.assertEqual(report['status'], 'failed')

    def test_false_blocks_are_visible_within_approved_recovery_tolerance(self):
        cases = self.full_test_double()
        for output in cases[0]['reviews'].values():
            output['claims'][0]['evidenceRefs'][0]['quote'] = '不存在的引用'
        report = self.evaluate(cases, True)
        self.assertEqual(report['metrics'].get('falseBlockCount'), 1)
        self.assertIs(report['cases'][0].get('falseBlock'), True)
        self.assertEqual(report['metrics'].get('hitCount'), 59)
        # Existing approved rubric tolerates some recovery loss, not unsafe
        # publishing. Reporting a miss does not invent a zero-false-block gate.
        self.assertEqual(report['status'], 'passed')

    def test_owner_group_prevents_rewritten_snapshot_leakage(self):
        cases = self.full_test_double()
        cases[1]['evidenceGroupId'] = cases[0]['evidenceGroupId']
        report = self.evaluate(cases, True)
        self.assertEqual(report['status'], 'not_ready')
        self.assertIn('evidence_group_split_leakage', report['blockers'])

    def test_duplicate_declaration_cannot_pad_minimum_counts(self):
        cases = self.full_test_double()
        cases[2]['evidenceGroupId'] = cases[0]['evidenceGroupId']
        cases[2]['declarationId'] = cases[0]['declarationId']
        report = self.evaluate(cases, True)
        self.assertEqual(report['status'], 'not_ready')
        self.assertIn('duplicate_approved_declaration', report['blockers'])

    def test_full_contract_test_double_reports_denominators_and_hash(self):
        cases = self.full_test_double()
        report = self.evaluate(cases, True)
        self.assertEqual(report['status'], 'passed')
        self.assertEqual(report['datasetHash'], digest(cases))
        self.assertEqual(report['metrics']['recoveryDenominator'], 30)
        self.assertEqual(report['metrics']['recoveryRate'], 1)
        self.assertEqual(report['metrics']['hardBlockDenominator'], 15)
        self.assertEqual(report['metrics']['citationCompleteness'], 1)
        self.assertEqual(report['sourceCounts']['historical_redacted'], 30)

    def test_duplicates_missing_class_or_missing_holdout_do_not_pass(self):
        for transform in ('duplicates', 'no_holdout', 'single_class'):
            cases = self.full_test_double()
            if transform == 'duplicates':
                cases[1] = copy.deepcopy(cases[0])
            elif transform == 'no_holdout':
                for c in cases:
                    c['split'] = 'development'
            else:
                cases = [make_case(i) for i in range(60)]
            report = self.evaluate(cases, True)
            self.assertEqual(report['status'], 'not_ready', transform)


if __name__ == '__main__':
    unittest.main()
