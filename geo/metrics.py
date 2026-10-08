"""Evidence bounded GEO metrics. Ratios are 0..1, never percentages or scores."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from urllib.parse import urlsplit
import hashlib
import json
import math

VERSION = 'geo-metrics-1'
_SUCCESS = {'succeeded', 'completed', 'success', 'imported'}
_FAILED = {'failed', 'error', 'api_failed', 'timeout', 'rate_limited', 'unauthorized',
           'permission_denied', 'parse_failed', 'tool_only', 'partial', 'incomplete', 'stream_incomplete'}
_PENDING = {'queued', 'pending', 'draft', 'running', 'planned', 'created', 'processing', 'retrying'}
_CANCELLED = {'cancelled', 'canceled'}
_BLOCKED = {'blocked'}
_NONANSWER = {'refused', 'empty', 'unanalysable', 'unanalyzable'}
_KNOWN_STATUS = _SUCCESS | _FAILED | _PENDING | _CANCELLED | _BLOCKED | _NONANSWER
_CHECKED = {'supported', 'contradicted', 'outdated'}


def _ratio(numerator, denominator):
    return numerator / denominator if denominator else None


def _target(record, key):
    return next((e for e in record['analysis'].get('entities', []) if e.get('entity_key') == key), {})


def _is_valid(record):
    analysis = record.get('analysis')
    return (record.get('status') in _SUCCESS and isinstance(record.get('answer'), str)
            and bool(record['answer'].strip()) and isinstance(analysis, dict)
            and analysis.get('valid_answer') is True and not analysis.get('refusal'))


def _is_judgment_candidate(record):
    if record.get('status') not in _SUCCESS or not isinstance(record.get('answer'), str) or not record['answer'].strip():
        return False
    analysis = record.get('analysis')
    return not isinstance(analysis, dict) or (analysis.get('valid_answer') is True and not analysis.get('refusal'))


def _judgment_coverage(records, target):
    coverage, causes = {}, {}
    for field in ('mention', 'recommendation'):
        decision_field = 'mentioned' if field == 'mention' else 'recommended'
        candidate_n = judged_n = missing_n = review_n = 0
        for record in records:
            if not _is_judgment_candidate(record):
                continue
            if field == 'recommendation' and not (record.get('question') or {}).get('recommendation_eligible'):
                continue
            candidate_n += 1
            if not isinstance(record.get('analysis'), dict):
                missing_n += 1
                continue
            entity = _target(record, target)
            if isinstance(entity.get(decision_field), bool):
                judged_n += 1
            elif entity.get('needs_review'):
                review_n += 1
        coverage[field] = dict(judged_n=judged_n, candidate_n=candidate_n,
                               unresolved_n=candidate_n-judged_n, rate=_ratio(judged_n, candidate_n))
        causes[field] = dict(analysis_missing_n=missing_n,
                            indeterminate_n=candidate_n-judged_n-missing_n, needs_review_n=review_n)
    return coverage, causes


def _domain(citation):
    url = citation.get('normalized_url') or citation.get('url') or ''
    try:
        parsed = urlsplit(url)
        return parsed.hostname.lower() if parsed.scheme in {'http', 'https'} and parsed.hostname else None
    except (ValueError, AttributeError):
        return None


def _counts(records, target, fixed):
    valid = [r for r in records if _is_valid(r)]
    numerators = Counter()
    denominators = Counter()
    facts = Counter()
    citation_counts = {'structured': Counter(), 'text_link': Counter()}
    missing_citation = ranking_missing = review_n = capability_n = 0
    share_unresolved = fact_review = 0
    question_counts = defaultdict(lambda: {'total_n': 0, 'valid_n': 0, 'failed_n': 0,
        'mention': Counter(), 'recommendation': Counter()})
    for record in records:
        qid = str(record.get('question_version_id', 'unknown'))
        qrow = question_counts[qid]
        qrow['total_n'] += 1
        if not _is_valid(record):
            if record.get('status') in _FAILED:
                qrow['failed_n'] += 1
            continue
        qrow['valid_n'] += 1
        entity = _target(record, target)
        qrow['mention'][{True: 'yes_n', False: 'no_n'}.get(entity.get('mentioned'), 'unknown_n')] += 1
        qrow['recommendation'][{True: 'yes_n', False: 'no_n'}.get(entity.get('recommended'), 'unknown_n')] += 1
        if entity.get('needs_review') or entity.get('mentioned') is None or entity.get('recommended') is None:
            review_n += 1
        if isinstance(entity.get('mentioned'), bool):
            denominators['mention_rate'] += 1
            numerators['mention_rate'] += entity['mentioned'] is True
        question = record.get('question') or {}
        entities = {e.get('entity_key'): e for e in record['analysis'].get('entities', [])}
        if question.get('recommendation_eligible'):
            if isinstance(entity.get('recommended'), bool):
                denominators['recommendation_rate'] += 1
                numerators['recommendation_rate'] += entity['recommended'] is True
            # Share is computed only on answers with all fixed competitors resolved.
            if all(isinstance(entities.get(k, {}).get('recommended'), bool) for k in fixed):
                denominators['recommendation_share'] += sum(entities[k]['recommended'] is True for k in fixed)
                numerators['recommendation_share'] += entities.get(target, {}).get('recommended') is True and target in fixed
            else:
                share_unresolved += 1
        if question.get('ranking_eligible') and isinstance(entity.get('recommended'), bool):
            explicit = any(e.get('recommended') is True and isinstance(e.get('rank'), int) and
                           not isinstance(e.get('rank'), bool) and e['rank'] >= 1 for k, e in entities.items() if k in fixed)
            ranking_missing += not explicit
            denominators['first_recommendation_rate'] += 1
            numerators['first_recommendation_rate'] += (entity.get('recommended') is True and
                type(entity.get('rank')) is int and entity['rank'] == 1)
        if question.get('fact_eligible'):
            for fact in record['analysis'].get('fact_checks', []):
                verdict = fact.get('verdict', 'unverified')
                fact_review += bool(fact.get('needs_review') or verdict in {'unverified', 'conflicting_sources'})
                facts[verdict] += 1
                if verdict in _CHECKED:
                    denominators['fact_error_rate'] += 1
                    numerators['fact_error_rate'] += verdict in {'contradicted', 'outdated'}
        seen = {'structured': set(), 'text_link': set()}
        for citation in record.get('citations') or []:
            source = citation.get('source_type')
            domain = _domain(citation)
            if source in seen and domain:
                seen[source].add(domain)
        for source in seen:
            citation_counts[source].update(seen[source])
        missing_citation += not any(seen.values())
        capabilities = (record.get('condition') or {}).get('capabilities') or {}
        capable = (capabilities.get('structured_citations') is True or capabilities.get('citations') is True
                   or record.get('citation_capability') is True)
        capability_n += capable
    metrics = {name: _ratio(numerators[name], denominators[name]) for name in
               ('mention_rate', 'recommendation_rate', 'first_recommendation_rate', 'recommendation_share', 'fact_error_rate')}
    citation_rates = {source: {domain: _ratio(n, len(valid)) for domain, n in counts.items()}
                      for source, counts in citation_counts.items()}
    total_facts = sum(n for verdict, n in facts.items() if verdict != 'subjective')
    cost, unknown, uncertain = 0., 0, 0
    for record in records:
        for attempt in record.get('attempts') or []:
            value = attempt.get('cost')
            known = isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0
            if known:
                cost += value
            unknown += bool(attempt.get('cost_unknown') or not known)
            uncertain += bool(attempt.get('billing_uncertain'))
    counts = dict(total_n=len(records), valid_n=len(valid),
        failed_n=sum(r.get('status') in _FAILED for r in records),
        pending_n=sum(r.get('status') in _PENDING for r in records),
        cancelled_n=sum(r.get('status') in _CANCELLED for r in records),
        blocked_n=sum(r.get('status') in _BLOCKED for r in records),
        draft_n=sum(r.get('status') == 'draft' for r in records),
        uncertain_n=sum(r.get('status') not in _KNOWN_STATUS for r in records),
        offline_fixture_n=sum(r.get('evidence_origin') == 'offline_fixture' for r in records),
        refused_n=sum(r.get('status') == 'refused' or (r.get('status') in _SUCCESS and
            bool((r.get('analysis') or {}).get('refusal'))) for r in records),
        empty_n=sum(r.get('status') == 'empty' or (r.get('status') in _SUCCESS and
            not str(r.get('answer') or '').strip()) for r in records),
        analysis_missing_n=sum(r.get('status') in _SUCCESS and bool(str(r.get('answer') or '').strip()) and not isinstance(r.get('analysis'), dict) for r in records),
        reviewed_n=sum(r.get('reviewed') is True for r in records), needs_review_n=review_n,
        invalid_answer_n=sum(r.get('status') in {'unanalysable', 'unanalyzable'} or (r.get('status') in _SUCCESS and isinstance(r.get('analysis'), dict) and
            not r['analysis'].get('refusal') and bool(str(r.get('answer') or '').strip()) and
            r['analysis'].get('valid_answer') is not True) for r in records),
        fact_needs_review_n=fact_review, share_unresolved_n=share_unresolved,
        no_explicit_ranking_n=ranking_missing, no_verifiable_citation_n=missing_citation)
    repeat = []
    for qid, qrow in sorted(question_counts.items()):
        repeat.append({'question_version_id': qid, **{k: qrow[k] for k in ('total_n', 'valid_n', 'failed_n')},
            **{kind: {key: qrow[kind][key] for key in ('yes_n', 'no_n', 'unknown_n')} for kind in ('mention', 'recommendation')}})
    dated = []
    for record in records:
        raw = record.get('sampled_at')
        if not isinstance(raw, str) or not raw:
            continue
        try:
            parsed = datetime.fromisoformat(raw.replace('Z', '+00:00'))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            dated.append((parsed, raw))
        except ValueError:
            continue
    counts.update(observation_ids=[r.get('id') for r in records if r.get('id') is not None],
                  sampled_at_min=min(dated)[1] if dated else None,
                  sampled_at_max=max(dated)[1] if dated else None)
    coverage, causes = _judgment_coverage(records, target)
    return {**counts, 'judgment_coverage': coverage, 'judgment_unresolved_causes': causes, 'metrics': metrics, 'numerators': {k: numerators[k] for k in metrics},
            'denominators': {k: denominators[k] for k in metrics}, 'fact_counts': dict(facts),
            'fact_coverage': _ratio(denominators['fact_error_rate'], total_facts),
            'citation_rates': citation_rates, 'citation_counts': {s: dict(c) for s, c in citation_counts.items()},
            'citation_denominator_n': len(valid), 'citation_capability_n': capability_n,
            'citation_capability_coverage': _ratio(capability_n, len(valid)),
            'cost': {'known_total': cost, 'unknown_attempt_n': unknown, 'billing_uncertain_attempt_n': uncertain},
            'repeat_consistency': repeat}


def _aggregate(records, target, fixed, include_frozen=True):
    pooled = _counts(records, target, fixed)
    questions = defaultdict(list)
    for record in records:
        questions[str(record.get('question_version_id', 'unknown'))].append(record)
    if include_frozen:
        for record in records:
            for qid in record.get('fixed_question_ids') or []:
                questions.setdefault(str(qid), [])
    per_question = {qid: _counts(rows, target, fixed) for qid, rows in sorted(questions.items())}
    eligible_ids = {'mention': sorted(questions), 'recommendation': [qid for qid, rows in sorted(questions.items())
        if any((r.get('question') or {}).get('recommendation_eligible') is True for r in rows)]}
    eligibility_unknown = [qid for qid, rows in sorted(questions.items()) if not rows or
        not any(isinstance((r.get('question') or {}).get('recommendation_eligible'), bool) for r in rows)]
    for qid, q in per_question.items():
        q['eligible_question_n'] = {field: int(qid in ids) for field, ids in eligible_ids.items()}
        q['equal_weight_judged_question_n'] = {field: int(qid in eligible_ids[field] and
            q['judgment_coverage'][field]['judged_n'] > 0) for field in eligible_ids}
        q['zero_judgment_question_ids'] = {field: [qid] if qid in eligible_ids[field] and
            q['judgment_coverage'][field]['judged_n'] == 0 else [] for field in eligible_ids}
    equal = {}
    equal_n = {}
    for metric in pooled['metrics']:
        values = [q['metrics'][metric] for q in per_question.values() if q['metrics'][metric] is not None]
        equal[metric] = sum(values) / len(values) if values else None
        equal_n[metric] = len(values)
    # Citation domains also use question equal weight; each valid question contributes zero for absent domain.
    equal_citations = {}
    for source in pooled['citation_rates']:
        domains = pooled['citation_rates'][source]
        eligible = [q for q in per_question.values() if q['valid_n']]
        equal_citations[source] = {d: sum(q['citation_rates'][source].get(d, 0) for q in eligible) / len(eligible)
                                  for d in domains} if eligible else {}
    return {**pooled, 'metrics': equal, 'answer_level_rates': pooled['metrics'],
            'answer_level_citation_rates': pooled['citation_rates'], 'citation_rates': equal_citations,
            'equal_weight_question_n': equal_n, 'question_n': len(questions), 'per_question': per_question,
            'eligible_question_n': {field: len(ids) for field, ids in eligible_ids.items()},
            'equal_weight_judged_question_n': {field: sum(per_question[qid]['judgment_coverage'][field]['judged_n'] > 0
                for qid in ids) for field, ids in eligible_ids.items()},
            'zero_judgment_question_ids': {field: [qid for qid in ids if
                per_question[qid]['judgment_coverage'][field]['judged_n'] == 0] for field, ids in eligible_ids.items()},
            'eligibility_unknown_question_ids': {'mention': [], 'recommendation': eligibility_unknown},
            'missing_question_ids': [qid for qid, q in per_question.items() if not q['valid_n']]}


def _group_key(record, question_set_hash):
    condition = record.get('condition') or {}
    return tuple(str(value or 'unknown') for value in (
        record.get('channel'), condition.get('surface'), condition.get('mode'),
        condition.get('model'), condition.get('condition_hash'), question_set_hash,
        record.get('entity_set_hash'), record.get('fact_baseline_hash')))


def compute_metrics(records: list[dict], target_key: str, fixed_entities: list[str]) -> dict:
    """Root partitions frozen targets/entities and supplies list hashes and missing placeholders."""
    fixed = list(dict.fromkeys(fixed_entities))
    if target_key not in fixed:
        raise ValueError('target_key must belong to fixed_entities')
    grouped = defaultdict(list)
    inferred_sets = defaultdict(set)
    for record in records:
        base = _group_key(record, 'unknown')[:5]
        inferred_sets[base].add(str(record.get('question_version_id', 'unknown')))
    for record in records:
        base = _group_key(record, 'unknown')[:5]
        fallback = hashlib.sha256(json.dumps(sorted(inferred_sets[base])).encode()).hexdigest()
        key = _group_key(record, record.get('question_set_hash') or fallback)
        grouped[key].append(record)
    groups = []
    dimensions = ('channel', 'surface', 'mode', 'model', 'condition_hash',
                  'question_set_hash', 'entity_set_hash', 'fact_baseline_hash')
    for key, rows in sorted(grouped.items()):
        group = dict(zip(dimensions, key))
        configured = sorted({str((r.get('condition') or {}).get('configured_model') or 'unknown') for r in rows})
        group['configured_model'] = configured[0] if len(configured) == 1 else None
        group['configured_models'] = configured
        group.update(_aggregate(rows, target_key, fixed))
        group['sets'] = {name: _aggregate([r for r in rows if (r.get('question') or {}).get('unbranded') is value], target_key, fixed, include_frozen=False)
                         for name, value in (('unbranded', True), ('branded', False))}
        groups.append(group)
    return dict(version=VERSION, aggregation='question_equal_weight', target_key=target_key,
                fixed_entities=fixed, groups=groups)
