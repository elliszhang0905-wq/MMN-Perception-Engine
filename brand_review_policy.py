"""Opt-in brand v4 policy. Pure, offline, conservative; v3 is untouched.

Trust boundary: scope/packet and validation executor metadata must come from the
authenticated server, never a request body. Record hashes detect drift, not
authenticate callers. Fusion recomputes all semantic checks, even for a record
whose hash is valid. No model verdict or confidence authorizes publication.
"""
import copy
import hashlib
import html
import json
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlsplit

SCHEMA_VERSION = 'brand-penetration-analysis-v4'
RULE_VERSION = 'brand-review-layered-v1'
SCOPE_FIELDS = ('orgId', 'edition', 'projectId', 'snapshotId', 'promptVersion', 'reviewVersion')
REVIEWER_IDS = ('review_1', 'review_2', 'review_3')
ACTION_FIELDS = ('conditions', 'costRisk', 'leadingIndicator', 'outcomeIndicator',
                 'validationThreshold', 'observationWindow', 'stopCondition', 'nonGoals')
# The only automatically eligible action is an offline manual source check.
# Free-form contracts require human review; nonempty strings are not evidence.
OBSERVATION_CONTRACT = {
    'conditions': '仅在已有来源与声明依赖均通过核验后，由项目负责人确认人工核对安排。',
    'costRisk': '需要人工核对时间；来源自述可能不实，不能据此安排投放。',
    'leadingIndicator': '已核对引文、主体和日期的样本记录数。',
    'outcomeIndicator': '可回读且核对一致的来源记录数，不作为销量或转化指标。',
    'validationThreshold': '引文、主体和日期须全部匹配；任一不匹配即停止该条记录。',
    'observationWindow': '仅限本次冻结证据包的时间窗，不扩大采集。',
    'stopCondition': '发现来源失效、冲突或范围不匹配时停止，并交项目负责人复核。',
    'nonGoals': '不投放、不调整预算、不推断销量因果、不自动执行。',
}
BOUNDARY = '公开传播样本不证明市场渗透、购买意愿、销量因果或全部消费者态度。'


def _hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def layer_status(kind, hard_failures, completed, supports, conflicts):
    if hard_failures:
        return 'blocked'
    if conflicts:
        return 'disputed'
    if kind == 'source_fact':
        return 'source_only'
    if completed != 3:
        return 'review_incomplete'
    if supports != 3:
        return 'manual_required'
    return 'supported' if kind == 'inference' else 'candidate'


def _day(value):
    return date.fromisoformat(str(value)[:10])


def _instant(value, end_of_day=False):
    value=str(value)
    if len(value)==10:
        parsed=datetime.combine(date.fromisoformat(value),datetime.min.time(),tzinfo=timezone(timedelta(hours=8)))
        return parsed+timedelta(days=1) if end_of_day else parsed
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('timezone_required')
    return parsed


def build_layered_packet(result, scope, date_window):
    """Copy and fingerprint trusted frozen source data, retaining rejected rows.

    Input uses the existing modelComparisons/verifiedComparisonItems shape.
    Unlike v3 no anchor text is truncated. Invalid sources remain audit-only.
    Scope is mandatory and independent of any untrusted result identity.
    """
    if any(not isinstance(scope.get(k), str) or not scope[k].strip() for k in SCOPE_FIELDS):
        raise ValueError('authenticated_scope_required')
    if _instant(date_window['start']) > _instant(date_window['end']):
        raise ValueError('invalid_date_window')
    comparisons = result.get('modelComparisons') or []
    own = next((r['model'] for r in comparisons if r.get('role') == 'own'), result.get('keyword'))
    competitors = sorted({r['model'] for r in comparisons if r.get('role') == 'competitor' and r.get('model') != own})
    if not own:
        raise ValueError('own_brand_required')
    packet = dict(scope={k: scope[k] for k in SCOPE_FIELDS}, ownBrand=own,
                  competitors=competitors, brands=[own, *competitors],
                  dateWindow=copy.deepcopy(date_window), evidence=[], boundary=BOUNDARY,
                  ruleVersion=RULE_VERSION)
    for source in result.get('verifiedComparisonItems') or []:
        row = dict(id=source.get('id') or source.get('canonicalContentId'),
                   brand=source.get('brandName') or source.get('normalizedModel') or source.get('keyword'),
                   platform=source.get('platformLabel') or source.get('platform'),
                   text=source.get('text') or '', title=source.get('title') or '',
                   sourceUrl=source.get('sourceUrl') or '', publishedAt=source.get('publishedAt'),
                   model=source.get('normalizedModel'), sourceScope={k:source[k] for k in SCOPE_FIELDS if k in source},
                   provenance=source.get('originalSourceUrl') or source.get('canonicalContentId'),
                   sourceConflict=bool(source.get('sourceConflict')), invalidSource=bool(source.get('invalidSource')))
        row['sourceFingerprint'] = _hash(row)
        # Exact repost text shares an independence group even if URLs differ.
        row['independenceKey'] = _hash([row['brand'], row['provenance'] or row['text'] or row['title']])
        packet['evidence'].append(row)
    packet['evidence'].sort(key=lambda r: (str(r['id']),r['sourceFingerprint']))
    packet['fingerprint'] = _hash(packet)
    return packet


def _check_packet(packet):
    if packet.get('ruleVersion') != RULE_VERSION or packet.get('fingerprint') != _hash({k:v for k,v in packet.items() if k != 'fingerprint'}):
        raise ValueError('packet_integrity_failed')


def _source_failures(row, packet):
    failures = []
    parsed = urlsplit(row['sourceUrl'])
    if not row['id'] or not row['platform'] or not (row['text'] or row['title']) or parsed.scheme not in ('http','https') or not parsed.hostname or parsed.username:
        failures.append('invalid_source')
    if row['brand'] not in packet['brands']:
        failures.append('brand_mismatch')
    if any(v != packet['scope'][k] for k,v in row['sourceScope'].items()):
        failures.append('scope_mismatch')
    try:
        window=packet['dateWindow']
        start=_instant(window['start'])
        end=_instant(window['end'],end_of_day=not window.get('endExclusive'))
        instant=_instant(row['publishedAt'])
        exclusive=window.get('endExclusive') or len(str(window['end']))==10
        if instant<start or (instant>=end if exclusive else instant>end):
            failures.append('date_mismatch')
    except (ValueError,TypeError):
        failures.append('date_mismatch')
    if row['sourceConflict']:
        failures.append('source_conflict')
    if row['invalidSource']:
        failures.append('invalid_source')
    if len({r['sourceFingerprint'] for r in packet['evidence'] if r['id'] == row['id']}) > 1:
        failures.append('duplicate_id_conflict')
    return failures


def _identity(c):
    return {'ownBrand':c.get('ownBrand'), 'competitor':c.get('competitor')} if c.get('competitor') else {'brand':c.get('brand')}


def _canonical_text(c):
    topic = c.get('topic')
    if not isinstance(topic,str) or not topic.strip() or len(topic) > 80:
        return None
    if c.get('kind') == 'inference' and c.get('predicate') == 'sample_mentions' and c.get('brand'):
        return f'本期{c["brand"]}公开样本中出现“{topic}”字样；仅说明样本表述，不确认事件或趋势。'
    if c.get('kind') == 'inference' and c.get('predicate') == 'both_samples_mention' and c.get('competitor'):
        return f'本期{c.get("ownBrand")}与{c["competitor"]}同平台公开样本均出现“{topic}”字样；不表示优劣或消费者替代。'
    if c.get('kind') == 'action' and c.get('predicate') == 'manual_observation':
        return f'可选：人工核对“{topic}”相关样本；须先确认适用条件、指标和停止条件，不自动执行。'
    return None


def _analyze_claim(c, packet):
    """Literal observation only. Text with negation is quoted, never event truth."""
    hard, refs = [], []
    identity = _identity(c)
    brands = set(identity.values())
    if (None in brands or not brands <= set(packet['brands']) or
            (c.get('competitor') and (c.get('ownBrand') != packet['ownBrand'] or c['competitor'] not in packet['competitors']))):
        hard.append('brand_mismatch')
    if any(k in c and c[k] != packet['scope'][k] for k in SCOPE_FIELDS):
        hard.append('scope_mismatch')
    if 'dateWindow' in c and c['dateWindow'] != packet['dateWindow']:
        hard.append('date_mismatch')
    sources = {r['id']:r for r in packet['evidence']}
    supplied = c.get('evidenceRefs')
    if not isinstance(supplied,list) or not supplied:
        hard.append('missing_evidence')
        supplied = []
    for ref in supplied:
        if not isinstance(ref,dict):
            hard.append('invalid_anchor'); continue
        row = sources.get(ref.get('evidenceId'))
        quote = ref.get('quote')
        if not row:
            hard.append('missing_evidence'); continue
        hard.extend(_source_failures(row,packet))
        if row['brand'] not in brands:
            hard.append('brand_mismatch')
        if c.get('model') and c['model'] != row['model']:
            hard.append('model_mismatch')
        anchor = row['text'] or row['title']
        if not isinstance(quote,str) or not quote or quote not in anchor:
            hard.append('unsupported_quote'); continue
        if ref.get('sourceFingerprint',row['sourceFingerprint']) != row['sourceFingerprint']:
            hard.append('anchor_fingerprint_mismatch')
        refs.append(dict(evidenceId=row['id'], sourceFingerprint=row['sourceFingerprint'], quote=quote,
                         span=[anchor.index(quote),anchor.index(quote)+len(quote)],
                         publishedAt=row['publishedAt'],brand=row['brand'],platform=row['platform'],sourceUrl=row['sourceUrl']))
    if c.get('competitor'):
        if {r['brand'] for r in refs} != brands:
            hard.append('pair_missing_side')
        if len({r['platform'] for r in refs}) != 1:
            hard.append('pair_scope_mismatch')
    text = _canonical_text(c)
    supported = bool(text) and not c.get('direction') and (not c.get('text') or c['text'] == text)
    # A valid ID alone is never a semantic support. Only exact literal topic
    # occurrence in body-backed quotes authorizes these limited templates.
    supported = supported and all(c['topic'] in r['quote'] and sources[r['evidenceId']]['text'] for r in refs)
    if c.get('kind') == 'action':
        contract = c.get('actionContract') or {}
        supported = supported and bool(c.get('dependsOn')) and contract == OBSERVATION_CONTRACT
    semantic = {k:c.get(k) for k in ('kind','predicate','topic','direction','model','dependsOn','actionContract')}
    semantic.update(identity)
    return dict(identity=identity, semanticKey=_hash(semantic), canonicalText=text,
                evidenceRefs=refs, hardFailures=sorted(set(hard)),
                status='blocked' if hard else 'supported' if supported else 'manual_required')


def _candidates(outputs, packet):
    """Provider IDs come from fixed server runtime, never model-supplied fields."""
    if not isinstance(outputs,dict) or len(outputs)>3:
        raise ValueError('three_provider_mapping_required')
    for provider,payload in sorted(outputs.items()):
        if provider not in REVIEWER_IDS:
            continue
        if not isinstance(payload,dict) or not isinstance(payload.get('claims'),list):
            continue
        if len(payload['claims']) > 200:
            raise ValueError('claim_limit_exceeded')
        for c in payload['claims']:
            if isinstance(c,dict) and isinstance(c.get('claimId'),str) and c['claimId']:
                yield provider,c


def validate_layered_reviews(provider_outputs, packet, *, actor_id, server_time):
    """Generate reproducible server validation artifacts; no I/O or clock read."""
    _check_packet(packet)
    if not actor_id or not server_time:
        raise ValueError('server_executor_required')
    _day(server_time)
    records=[]
    for provider,c in _candidates(provider_outputs,packet):
        rec=dict(claimId=c['claimId'], providerId=provider, inputHash=_hash(c),
                 evidenceFingerprint=packet['fingerprint'], ruleVersion=RULE_VERSION,
                 reviewVersion=packet['scope']['reviewVersion'], actorId=actor_id,
                 serverTime=server_time, **_analyze_claim(c,packet))
        rec['artifactHash']=_hash(rec)
        records.append(rec)
    return records


def _record_valid(record, c, provider, packet):
    if not isinstance(record,dict):
        return False
    try:
        expected=validate_layered_reviews({provider:{'claims':[c]}},packet,
                                         actor_id=record['actorId'],server_time=record['serverTime'])[0]
        return expected == record
    except (KeyError,ValueError,TypeError):
        return False


def _source_facts(packet, brands):
    facts=[]
    seen=set()
    for row in packet['evidence']:
        if row['brand'] not in brands or _source_failures(row,packet) or row['sourceFingerprint'] in seen:
            continue
        seen.add(row['sourceFingerprint'])
        quote=row['text'] or row['title']
        facts.append(dict(claimId='source:'+row['sourceFingerprint'],kind='fact',
                          text=f'{row["publishedAt"]}，{row["brand"]}的{row["platform"]}来源提及：“{quote}”。此为来源表述，不代表内容已获客观确认。',
                          evidenceRefs=[dict(evidenceId=row['id'],sourceFingerprint=row['sourceFingerprint'],quote=quote,
                                             span=[0,len(quote)],sourceUrl=row['sourceUrl'],publishedAt=row['publishedAt'],brand=row['brand'],platform=row['platform'])],
                          dependsOn=[],publicationStatus='source_only',reasonCodes=[]))
    return facts


def fuse_layered_reviews(provider_outputs, packet, validation_records):
    """Fuse same atomic propositions, never whole-card enum votes or prose."""
    _check_packet(packet)
    groups={}
    for provider,c in _candidates(provider_outputs,packet):
        analysis=_analyze_claim(c,packet)
        key=analysis['semanticKey']
        group=groups.setdefault(key,dict(analysis=analysis, entries=[], claimIds=set()))
        matched=[r for r in validation_records if isinstance(r,dict) and r.get('providerId')==provider and r.get('claimId')==c['claimId'] and r.get('inputHash')==_hash(c)]
        trusted=len(matched)==1 and _record_valid(matched[0],c,provider,packet)
        group['entries'].append((provider,c,analysis,trusted))
        group['claimIds'].add(c['claimId'])
    # Stable atomic IDs independent of provider-local naming and source IDs.
    alias={}
    for key,g in groups.items():
        for cid in g['claimIds']:
            alias.setdefault(cid,set()).add(key)
    statuses={}
    pending=set(groups)
    while pending:
        progressed=False
        for key in sorted(pending):
            g=groups[key]; a=g['analysis']; entries=g['entries']
            dependencies=entries[0][1].get('dependsOn') or []
            hard=set(x for _,_,v,_ in entries for x in v['hardFailures'])
            depkeys=set()
            for cid in dependencies:
                if len(alias.get(cid,set())) != 1:
                    hard.add('dependency_missing_or_ambiguous')
                else:
                    depkeys.update(alias[cid])
            g['resolvedDependencies']=sorted(depkeys)
            if not hard and depkeys & pending:
                continue
            if any(statuses.get(d) not in ('supported','source_only') for d in depkeys):
                hard.add('dependency_blocked')
            providers={p for p,_,_,trusted in entries if trusted}
            supports={p for p,_,v,t in entries if t and v['status']=='supported'}
            conflicts=[]
            unresolved={p for p,_,v,t in entries if not t or v['status']!='supported'}
            if supports and unresolved:
                conflicts.append('unresolved_same_proposition')
            supports-=unresolved
            c=entries[0][1]
            for other in groups.values():
                oc=other['entries'][0][1]
                if a['identity']==other['analysis']['identity'] and c.get('topic')==oc.get('topic') and c.get('predicate')==oc.get('predicate') and {c.get('direction'),oc.get('direction')}=={'increase','decrease'}:
                    conflicts.append('interpretation_conflict')
            status=layer_status(c.get('kind'),sorted(hard),len(providers),len(supports),conflicts)
            g.update(status=status,reasons=sorted(hard) or conflicts or ([] if status in ('supported','candidate') else [status]))
            statuses[key]=status; pending.remove(key); progressed=True
        if not progressed:
            for key in pending:
                groups[key].update(status='blocked',reasons=['dependency_cycle'])
                statuses[key]='blocked'
            break
    identities=[{'brand':b} for b in packet['brands']]+[{'ownBrand':packet['ownBrand'],'competitor':b} for b in packet['competitors']]
    rows=[]
    for identity in identities:
        facts=_source_facts(packet,set(identity.values()))
        row=dict(**identity,facts=facts,insights=[],actionOptions=[],disputes=[],unknowns=[])
        counts=[]
        for key,g in groups.items():
            if g['analysis']['identity']!=identity:
                continue
            entries=g['entries']; c=entries[0][1]
            refs={_hash(ref):ref for _,_,a,_ in entries for ref in a['evidenceRefs']}
            published=g['status'] in ('supported','candidate')
            item=dict(claimId=key,kind='hypothesis' if c.get('kind')=='action' else 'inference',
                      text=g['analysis']['canonicalText'] if published else '该项声明尚待核对来源、解释或适用条件。',
                      evidenceRefs=list(refs.values()),dependsOn=g.get('resolvedDependencies',[]),
                      publicationStatus=g['status'],reasonCodes=g['reasons'])
            counts.append(len({p for p,_,_,t in entries if t}))
            if published and c.get('kind')=='action':
                item.update(actionContract=dict(OBSERVATION_CONTRACT),allowExecution=False)
                row['actionOptions'].append(item)
            elif published:
                row['insights'].append(item)
            else:
                item.update(kind='unknown',owner='项目复核负责人',affectedClaimIds=sorted(g['claimIds']))
                # Inert display-only candidate, never substituted into fact text.
                item['candidateText']=html.escape(str(c.get('text') or g['analysis']['canonicalText'] or '未规范化声明')[:1200])
                item['candidateTexts']=sorted({html.escape(str(entry.get('text') or a['canonicalText'] or '未规范化声明')[:1200]) for _,entry,a,_ in entries})
                row['unknowns'].append(item)
                if g['status']=='disputed':
                    row['disputes'].append(copy.deepcopy(item))
        row['reviewCoverage']=dict(required=3,completed=min(counts) if counts else 0)
        row['evidenceCount']=len({r['evidenceId'] for f in facts for r in f['evidenceRefs']})
        valid_ids={r['evidenceId'] for f in facts for r in f['evidenceRefs']}
        row['independentSourceCount']=len({r['independenceKey'] for r in packet['evidence'] if r['id'] in valid_ids})
        row['status']='partial' if row['insights'] and row['unknowns'] else 'available' if row['insights'] else 'source_only' if facts else 'insufficient_evidence'
        rows.append(row)
    return dict(schemaVersion=SCHEMA_VERSION,ruleVersion=RULE_VERSION,**packet['scope'],
                evidenceFingerprint=packet['fingerprint'],dateWindow=copy.deepcopy(packet['dateWindow']),
                ownBrand=packet['ownBrand'],competitors=packet['competitors'],boundary=BOUNDARY,
                brandConclusions=[r for r in rows if 'brand' in r],pairwiseConclusions=[r for r in rows if 'competitor' in r])
