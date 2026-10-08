"""Bounded deterministic GEO extraction. No model knowledge, I/O or input execution."""
import re
from datetime import date
from decimal import Decimal, InvalidOperation, localcontext

VERSION = 'geo-rules-1'
_REFUSAL = re.compile(r'(?:抱歉|对不起).{0,30}(?:无法|不能|不便)(?:回答|提供|推荐)|(?:无法|不能)提供(?:购车|车辆|选车)建议|^(?:无法|不能)回答')
_SUGGEST = re.compile(r'(?:推荐|建议(?:选择|购买|考虑)?|(?:可以|可|值得|优先)考虑|优先选择|首选|首推|考虑购买|考虑)')
_NEGATIVE = re.compile(r'(?:不(?:再)?推荐|不建议|不要(?:选择|购买|考虑)?|不应(?:选择|购买)?|避免(?:选择|购买)?|不考虑|不值得(?:选择|购买|考虑)|不是推荐(?:车型|对象))')
_UNCERTAIN = re.compile(r'不是不|并非不|是否|你问|问题(?:中)?(?:提到|要求)|有人说|据说|“|”|「|」|而非|而不是|不意味着')


def _sentences(text):
    return [(m.start(), m.end(), m.group()) for m in re.finditer(r'[^。！？!?；;\n]+', text)]


def _candidates(text, entities):
    owners = {}
    for entity in entities:
        for name in [entity.get('name', ''), *entity.get('aliases', [])]:
            if isinstance(name, str) and name:
                owners.setdefault(name.casefold(), set()).add(entity['key'])
    hits = {e['key']: [] for e in entities}
    for entity in entities:
        for name in dict.fromkeys([entity.get('name', ''), *entity.get('aliases', [])]):
            if not isinstance(name, str) or not name:
                continue
            # ASCII tokens need both ends fenced even when appended to a Chinese brand.
            pattern = re.escape(name)
            if re.search(r'[A-Za-z0-9]$', name):
                pattern += r'(?![A-Za-z0-9])'
            if re.match(r'[A-Za-z0-9]', name):
                pattern = r'(?<![A-Za-z0-9])' + pattern
            for match in re.finditer(pattern, text, re.I):
                context = text[max(0, match.start()-16):match.end()+16]
                short = bool(re.fullmatch(r'[A-Za-z0-9]{1,4}', name))
                ambiguous = len(owners[name.casefold()]) > 1 or (
                    short and not (entity.get('brand') and entity['brand'] in context))
                hits[entity['key']].append((match.start(), match.end(), ambiguous))
    for key, matches in hits.items():
        hits[key] = sorted(set(matches), key=lambda h: (h[2], h[0], -(h[1]-h[0])))
    return hits


def _recommendation(text, hit, all_hits):
    start, end, _ = hit
    sentence = next((s for s in _sentences(text) if s[0] <= start < s[1]), (start, end, text[start:end]))
    offset, _, evidence = sentence
    local_start, local_end = start-offset, end-offset
    # A comma separates explicit recommendations from an adjacent negative object.
    left = max(evidence.rfind('，', 0, local_start), evidence.rfind(',', 0, local_start)) + 1
    right_options = [p for p in (evidence.find('，', local_end), evidence.find(',', local_end)) if p >= 0]
    right = min(right_options) if right_options else len(evidence)
    clause = evidence[left:right]
    if _UNCERTAIN.search(evidence) and _SUGGEST.search(evidence):
        return None, None, True, 'recommendation_scope_uncertain', sentence
    before = evidence[left:local_start]
    if _NEGATIVE.search(before) or _NEGATIVE.match(evidence[local_end:].lstrip()):
        return False, None, False, 'explicit_negative', sentence
    line_prefix = text[text.rfind('\n', 0, start)+1:start]
    list_number = re.search(r'(\d+)[.、)）]\s*$', line_prefix)
    ordered_context = False
    for line in reversed(text[:start].splitlines()):
        line = line.strip()
        if not line or re.match(r'^\d+[.、)）]', line):
            continue
        ordered_context = bool(re.match(r'^(?:我的)?推荐(?:排序|排名|顺序|列表)?[：:]\s*(?:\d+[.、)）]\s*)?$', line))
        break
    if list_number and ordered_context and not _NEGATIVE.search(evidence):
        return True, int(list_number.group(1)), False, 'explicit_ordered_recommendation', sentence
    if not _SUGGEST.search(clause):
        if _SUGGEST.search(evidence):
            return None, None, True, 'recommendation_scope_uncertain', sentence
        return False, None, False, 'mention_only', sentence
    trigger = _SUGGEST.search(before)
    if trigger is None:
        after = evidence[local_end:right]
        # Subject-first recommendation is only safe for a single entity in the clause.
        entity_keys = {k for k, values in all_hits.items() for a, b, _ in values
                       if offset+left <= a < offset+right}
        if not _SUGGEST.search(after) or len(entity_keys) != 1:
            return None, None, True, 'recommendation_scope_uncertain', sentence
    rank = None
    if re.search(r'首选|首推|优先选择|第一推荐', before):
        rank = 1
    elif re.search(r'其次推荐|第二推荐', before):
        rank = 2
    elif re.search(r'推荐(?:排序|排名|顺序)', text[:start]):
        line = text[text.rfind('\n', 0, start)+1:start]
        numbered = re.search(r'(\d+)[.、)）]\s*$', line)
        if numbered:
            rank = int(numbered.group(1))
    return True, rank, False, 'explicit_recommendation', sentence


def _date(value):
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


_NUMERIC_FIELDS = {'electric_range', 'combined_range', 'range', 'length', 'width',
                   'height', 'wheelbase', 'price', 'charging_voltage'}


def _scope_value(field, value):
    # HTML form years are strings; normalize year only, never units/cycles/enums.
    if field == 'year' and not isinstance(value, bool):
        if isinstance(value, int) or (isinstance(value, str) and re.fullmatch(r'20\d{2}', value.strip())):
            return int(value)
    return value


def _numeric_value(value):
    # Boolean equipment availability is not a numeric 0/1 assertion.
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        return None
    raw = str(value).strip()
    if not re.fullmatch(r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)', raw):
        return None
    try:
        number = Decimal(raw)
        return number if number.is_finite() else None
    except InvalidOperation:
        return None


def _scaled_value(number_text, multiplier=1):
    """Scale source digits exactly; use JSON numbers only when their decimal survives."""
    with localcontext() as precision:
        precision.prec = max(28, len(number_text) + 8)
        value = Decimal(number_text) * Decimal(multiplier)
    if value == value.to_integral_value():
        return int(value)
    approximate = float(value)
    if _numeric_value(approximate) == value:
        return approximate
    return format(value, 'f')


def _fact_value(field, value):
    return _numeric_value(value) if field in _NUMERIC_FIELDS else value


def _check_fact(claim, facts, observed_at, context):
    if claim['field'] == 'subjective':
        return 'subjective', None, 'subjective_experience'
    if not claim['entity_key']:
        return 'unverified', None, 'entity_scope_uncertain'
    candidates = [f for f in facts if f.get('entity_key') == claim['entity_key'] and f.get('field') == claim['field']]
    eligible = []
    incomplete = False
    for fact in candidates:
        required = ('id', 'logical_id', 'version', 'year', 'trim', 'market', 'field', 'unit',
                    'source_url', 'source_excerpt', 'reviewer', 'effective_from')
        if (fact.get('state') != 'approved' or any(fact.get(k) in (None, '') for k in required)
                or not isinstance(fact.get('conditions'), dict) or not fact['conditions']
                or not _date(fact.get('effective_from'))
                or not re.match(r'https?://', str(fact.get('source_url', '')))
                or 'value' not in fact):
            incomplete = True
            continue
        eligible.append(fact)
    if not eligible:
        return 'unverified', None, 'baseline_incomplete' if incomplete else 'no_approved_baseline'
    applicable, uncertain = [], []
    for fact in eligible:
        checks = {'year': claim['year'], 'trim': claim['trim'], 'market': context.get('market'),
                  'unit': claim['unit'], 'cycle': claim['cycle']}
        mismatched = any(checks[k] is not None and _scope_value(k, fact.get(k)) != _scope_value(k, checks[k]) for k in checks)
        if mismatched:
            continue
        missing = any(checks[k] is None and fact.get(k) not in (None, '') for k in checks)
        for key, expected in fact['conditions'].items():
            actual = context.get(key)
            if actual is None:
                missing = True
            elif _scope_value(key, actual) != _scope_value(key, expected):
                mismatched = True
        if not mismatched:
            (uncertain if missing else applicable).append(fact)
    if not applicable:
        return ('unverified', uncertain[0]['id'], 'conditions_missing') if uncertain else (
            'not_applicable', eligible[0]['id'], 'conditions_mismatch')
    when = _date(observed_at)
    if when is None:
        return 'unverified', applicable[0]['id'], 'observation_date_missing'
    active = [f for f in applicable if _date(f['effective_from']) <= when and
              (not f.get('effective_to') or (_date(f['effective_to']) and when <= _date(f['effective_to'])))]
    if not active:
        expired = [f for f in applicable if _date(f.get('effective_to')) and _date(f['effective_to']) < when]
        return ('outdated', expired[0]['id'], 'baseline_expired') if expired else (
            'not_applicable', applicable[0]['id'], 'baseline_not_yet_effective')
    if claim['field'] in _NUMERIC_FIELDS and any(_fact_value(claim['field'], f.get('value')) is None for f in active):
        return 'unverified', [f['id'] for f in active], 'baseline_numeric_value_invalid'
    active_values = [_fact_value(claim['field'], f.get('value')) for f in active]
    if any(type(value) is not type(active_values[0]) or value != active_values[0] for value in active_values[1:]):
        return 'conflicting_sources', [f['id'] for f in active], 'approved_baselines_disagree'
    fact = active[0]
    actual = _fact_value(claim['field'], claim['value'])
    expected = _fact_value(claim['field'], fact['value'])
    if type(actual) is not type(expected):
        return 'unverified', fact['id'], 'baseline_value_type_mismatch'
    equal = actual == expected
    return ('supported' if equal else 'contradicted'), fact['id'], 'approved_baseline_comparison'


def _extract_facts(text, entities, hits, facts, observed_at, question):
    rows = []
    definitions = [
        ('range', r'(?:(CLTC|WLTC)\s*)?(纯电|综合)?续航(?:里程)?(?:为|达到|约|是|并非|不是)?\s*([+-]?\d+(?:\.\d+)?)\s*(公里|km)', None),
        ('powertrain', r'(?:不)?(?:采用|搭载|动力形式(?:为|是)?)(纯电|增程|插混|燃油)(?:动力)?', None),
        ('dimension', r'(车长|车宽|车高|轴距)(?:为|是|约)?\s*([+-]?\d+(?:\.\d+)?)\s*(毫米|厘米|米|mm|cm|m)', None),
        ('price', r'(?:售价|指导价|价格)(?:为|是|约)?\s*([+-]?\d+(?:\.\d+)?)\s*(万元|元)', None),
        ('equipment', r'(激光雷达|空气悬架|座椅加热|座椅通风|全景天窗)(?:为|是|需要)?(全系标配|标配|选装)', None),
        ('charging_voltage', r'(?:不)?(?:支持|采用)\s*(\d+)\s*V(?:高压|快充|平台)', None),
        ('charging_method', r'(?:不)?(?:支持)(换电|快充|慢充)', None),
        ('subjective', r'(?:驾乘舒适|操控出色|外观漂亮|体验很好)', None),
    ]
    context = dict(question) if isinstance(question, dict) else {}
    for offset, _, sentence in _sentences(text):
        keys = {k for k, values in hits.items() for a, b, ambiguous in values if offset <= a < offset+len(sentence) and not ambiguous}
        entity = next((e for e in entities if len(keys) == 1 and e['key'] in keys), {})
        year_match = re.search(r'(20\d{2})\s*款', sentence)
        year = int(year_match.group(1)) if year_match else entity.get('year')
        trim_match = re.search(r'(标准版|旗舰版|豪华版|Pro版|Max版|Ultra版)', sentence)
        trim = trim_match.group(1) if trim_match else entity.get('trim')
        local_context = {**context, 'year': year, 'trim': trim}
        # An entity registry supplies market only if explicitly recorded, never inferred by model knowledge.
        if entity.get('market'):
            local_context.setdefault('market', entity['market'])
        if '中国' in sentence:
            local_context['market'] = '中国'
        for kind, pattern, _ in definitions:
            for match in re.finditer(pattern, sentence, re.I):
                field, value, unit, cycle = kind, match.group(0), '', None
                claim_trim = trim
                claim_context = dict(local_context)
                if kind == 'range':
                    cycle = (match.group(1) or '').upper() or None
                    field = {'纯电': 'electric_range', '综合': 'combined_range'}.get(match.group(2), 'range')
                    value, unit = _scaled_value(match.group(3)), 'km'
                elif kind == 'powertrain':
                    value, unit = match.group(1), 'type'
                elif kind == 'dimension':
                    field = {'车长': 'length', '车宽': 'width', '车高': 'height', '轴距': 'wheelbase'}[match.group(1)]
                    scale = {'毫米': 1, 'mm': 1, '厘米': 10, 'cm': 10, '米': 1000, 'm': 1000}[match.group(3).lower()]
                    value, unit = _scaled_value(match.group(2), scale), 'mm'
                elif kind == 'price':
                    value = _scaled_value(match.group(1), 10000 if match.group(2) == '万元' else 1)
                    unit = 'CNY'
                elif kind == 'equipment':
                    field, value, unit = 'equipment:' + match.group(1), match.group(2), 'availability'
                    if value == '全系标配':
                        claim_trim = '全系'
                        claim_context['trim'] = claim_trim
                elif kind == 'charging_voltage':
                    value, unit = _scaled_value(match.group(1)), 'V'
                elif kind == 'charging_method':
                    value, unit = match.group(1), 'type'
                polarity = 'negative' if re.search(r'并非|不是|不支持|不采用|不搭载', match.group(0)) else 'positive'
                claim = dict(claim=match.group(0), polarity=polarity, field=field, value=value, unit=unit, cycle=cycle,
                             year=year, trim=claim_trim, entity_key=entity.get('key'), evidence=match.group(0),
                             start=offset+match.start(), end=offset+match.end())
                verdict, baseline_id, reason = _check_fact(claim, facts, observed_at, claim_context)
                if field in _NUMERIC_FIELDS and _numeric_value(value) is not None and _numeric_value(value) < 0:
                    verdict, baseline_id, reason = 'unverified', None, 'negative_numeric_value_requires_review'
                if polarity == 'negative':
                    verdict, baseline_id, reason = 'unverified', None, 'negated_claim_requires_review'
                rows.append({**claim, 'verdict': verdict, 'baseline_id': baseline_id, 'reason': reason})
    return rows


def analyze_answer(answer: str, entities: list[dict], facts=(), observed_at=None, question=None) -> dict:
    """Offsets are Python Unicode character indices, end exclusive; null means unknown."""
    text = answer if isinstance(answer, str) else ''
    refusal = bool(_REFUSAL.search(text))
    valid = bool(text.strip()) and not refusal
    hits = _candidates(text, entities) if valid else {e['key']: [] for e in entities}
    rows = []
    for entity in entities:
        matches = hits[entity['key']]
        row = dict(entity_key=entity['key'], mentioned=False if valid else None,
                   recommended=False if valid else None, rank=None, evidence='', start=None,
                   end=None, needs_review=False, reason='not_mentioned' if valid else 'non_answer')
        if matches:
            hit = matches[0]
            if hit[2]:
                row.update(mentioned=None, recommended=None, needs_review=True, reason='ambiguous_alias',
                           start=hit[0], end=hit[1], evidence=text[hit[0]:hit[1]])
            else:
                decisions = [_recommendation(text, h, hits) for h in matches if not h[2]]
                positive = next((d for d in decisions if d[0] is True), None)
                uncertain = next((d for d in decisions if d[2]), None)
                negative = any(d[3] == 'explicit_negative' for d in decisions)
                decision = uncertain or positive or decisions[0]
                recommended, rank, review, reason, sentence = decision
                if positive and negative:
                    recommended, rank, review, reason = None, None, True, 'contradictory_recommendations'
                row.update(mentioned=True, recommended=recommended, rank=rank, needs_review=review,
                           reason=reason, start=sentence[0], end=sentence[1], evidence=sentence[2])
        rows.append(row)
    return dict(version=VERSION, valid_answer=valid, refusal=refusal, entities=rows,
                fact_checks=_extract_facts(text, entities, hits, facts, observed_at, question) if valid else [])
