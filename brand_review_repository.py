"""Explicitly migrated, append-only, tenant-scoped review storage.

Only service code supplies scope and payload. Never bind HTTP JSON directly to
save_review_version. Public readers never create tables or update timestamps.
"""
import copy
import hashlib
import json
import sqlite3
import uuid
from datetime import datetime, timezone

SCOPE = ('orgId', 'edition', 'projectId', 'snapshotId')
LAYERS = ('facts', 'insights', 'actionOptions', 'disputes', 'unknowns')

class ReviewConflict(ValueError): pass
class ReviewForbidden(PermissionError): pass
class ReviewNotFound(LookupError): pass

def _json(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def _scope(scope):
    values=tuple(scope.get(k) for k in SCOPE)
    if any(not isinstance(v,str) or not v or len(v)>256 for v in values):
        raise ValueError('无效复核范围')
    return values

def migrate(conn):
    """Deployment/admin explicit migration ONLY; never called by a reader/runner."""
    conn.executescript('''
    CREATE TABLE IF NOT EXISTS brand_review_versions (
      review_id TEXT NOT NULL, org_id TEXT NOT NULL, edition TEXT NOT NULL,
      project_id TEXT NOT NULL, snapshot_id TEXT NOT NULL, version INTEGER NOT NULL,
      payload TEXT NOT NULL, idempotency_key TEXT NOT NULL, request_hash TEXT NOT NULL,
      created_at TEXT NOT NULL, supersedes INTEGER,
      PRIMARY KEY(review_id,version),
      UNIQUE(org_id,edition,project_id,snapshot_id,version),
      UNIQUE(org_id,edition,project_id,snapshot_id,idempotency_key));
    CREATE TABLE IF NOT EXISTS brand_review_decisions (
      decision_id TEXT PRIMARY KEY, review_id TEXT NOT NULL, version INTEGER NOT NULL,
      actor_id TEXT NOT NULL, server_time TEXT NOT NULL, request TEXT NOT NULL,
      before_value TEXT NOT NULL, after_value TEXT NOT NULL,
      UNIQUE(review_id,version));
    CREATE TRIGGER IF NOT EXISTS brand_review_versions_no_update
      BEFORE UPDATE ON brand_review_versions BEGIN SELECT RAISE(ABORT,'append only'); END;
    CREATE TRIGGER IF NOT EXISTS brand_review_versions_no_delete
      BEFORE DELETE ON brand_review_versions BEGIN SELECT RAISE(ABORT,'append only'); END;
    CREATE TRIGGER IF NOT EXISTS brand_review_decisions_no_update
      BEFORE UPDATE ON brand_review_decisions BEGIN SELECT RAISE(ABORT,'append only'); END;
    CREATE TRIGGER IF NOT EXISTS brand_review_decisions_no_delete
      BEFORE DELETE ON brand_review_decisions BEGIN SELECT RAISE(ABORT,'append only'); END;
    ''')

def _exists(conn):
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='brand_review_versions'").fetchone())

def _row(conn,scope,review_id=None,version=None):
    if not _exists(conn): return None
    sql='SELECT review_id,version,payload,created_at FROM brand_review_versions WHERE org_id=? AND edition=? AND project_id=? AND snapshot_id=?'
    args=list(_scope(scope))
    if review_id: sql+=' AND review_id=?';args.append(review_id)
    if version is not None: sql+=' AND version=?';args.append(version)
    return conn.execute(sql+' ORDER BY version DESC LIMIT 1',args).fetchone()

def resolve_review_scope(conn,org_id,review_id):
    """Server lookup by authenticated tenant; HTTP actor/scope are never used."""
    if not _exists(conn): raise ReviewNotFound('复核不存在')
    row=conn.execute('SELECT org_id,edition,project_id,snapshot_id FROM brand_review_versions WHERE org_id=? AND review_id=? LIMIT 1',(org_id,review_id)).fetchone()
    if not row: raise ReviewNotFound('复核不存在')
    return dict(zip(SCOPE,row))

def _pick(data,keys):
    return {k:copy.deepcopy(data[k]) for k in keys if k in data}

def public_decision(data):
    """Fixed field DTO at EVERY nested model/audit-bearing boundary."""
    out=_pick(data,('schemaVersion','ruleVersion','snapshotId','projectId','edition','reviewVersion','evidenceFingerprint','ownBrand','competitors','boundary'))
    if isinstance(data.get('dateWindow'),dict):
        out['dateWindow']=_pick(data['dateWindow'],('start','end','endExclusive'))
    for group in ('brandConclusions','pairwiseConclusions'):
        out[group]=[]
        for row in data.get(group,[]):
            safe=_pick(row,('brand','ownBrand','competitor','status','evidenceCount','independentSourceCount'))
            safe['reviewCoverage']=_pick(row.get('reviewCoverage',{}),('required','completed'))
            for layer in LAYERS:
                safe[layer]=[]
                for item in row.get(layer,[]):
                    clean=_pick(item,('claimId','kind','text','dependsOn','publicationStatus','reasonCodes','owner','affectedClaimIds','allowExecution','humanDecisionStatus','humanDecisionMessage','canonicalCandidateText'))
                    clean['evidenceRefs']=[_pick(ref,('evidenceId','sourceFingerprint','quote','span','publishedAt','brand','model','sourceUrl','platform')) for ref in item.get('evidenceRefs',[])]
                    if 'actionContract' in item:
                        from brand_review_policy import OBSERVATION_CONTRACT
                        clean['actionContract']=dict(OBSERVATION_CONTRACT)
                        clean['allowExecution']=False
                    safe[layer].append(clean)
            out[group].append(safe)
    return out

def latest_version(conn,scope):
    row=_row(conn,scope)
    return row[1] if row else 0

def get_review_projection(conn,scope,review_id=None,*,version=None,current_result=None):
    row=_row(conn,scope,review_id,version)
    if not row:return None
    payload=json.loads(row[2])
    if version is None:
        import brand_review_policy as policy
        from brand_review_runtime import PROMPT_VERSION,window_for_snapshot
        stored=payload.get('packet') or {}
        if (payload['decision'].get('ruleVersion')!=policy.RULE_VERSION
                or payload['decision'].get('schemaVersion')!=policy.SCHEMA_VERSION
                or payload['decision'].get('evidenceFingerprint')!=stored.get('fingerprint')
                or (stored.get('scope') or {}).get('promptVersion')!=PROMPT_VERSION
                or any((stored.get('scope') or {}).get(k)!=scope[k] for k in SCOPE)):
            return None
        try:
            policy._check_packet(stored)
            if current_result is not None:
                current=policy.build_layered_packet(current_result,{**scope,'promptVersion':PROMPT_VERSION,'reviewVersion':stored['scope']['reviewVersion']},window_for_snapshot(current_result))
                if current['fingerprint']!=stored['fingerprint']:return None
        except (KeyError,ValueError,TypeError):return None
    decision=copy.deepcopy(payload['decision'])
    rows=decision.get('brandConclusions',[])+decision.get('pairwiseConclusions',[])
    if payload.get('packet') and payload.get('outputs'):
        import brand_review_policy as policy
        try:
            records=policy.validate_layered_reviews(payload['outputs'],payload['packet'],actor_id='server:canonical-preview',server_time=datetime.now(timezone.utc).isoformat())
            for row_item in rows:
                for layer in ('unknowns','disputes'):
                    for item in row_item.get(layer,[]):
                        candidate=_human_candidate(payload,records,{'claimId':item['claimId'],'action':'accept'},rows)
                        if candidate:item['canonicalCandidateText']=candidate['text']
        except (KeyError,ValueError,TypeError):pass
    return dict(reviewId=row[0],version=row[1],snapshotId=scope['snapshotId'],projectId=scope['projectId'],edition=scope['edition'],createdAt=row[3],decision=public_decision(decision))

def _append(conn,scope,payload,expected_version,key,request_hash=None):
    values=_scope(scope)
    if type(expected_version) is not int or expected_version<0 or not isinstance(key,str) or not 1<=len(key)<=128:
        raise ValueError('版本或请求标识无效')
    encoded=_json(payload)
    if len(encoded.encode())>8_000_000: raise ValueError('复核产物过大')
    digest=request_hash or hashlib.sha256(encoded.encode()).hexdigest()
    prior=conn.execute('SELECT review_id,version,request_hash FROM brand_review_versions WHERE org_id=? AND edition=? AND project_id=? AND snapshot_id=? AND idempotency_key=?',(*values,key)).fetchone()
    if prior:
        if prior[2]!=digest:raise ReviewConflict('重复请求内容不一致')
        return get_review_projection(conn,scope,prior[0],version=prior[1])
    latest=_row(conn,scope)
    actual=latest[1] if latest else 0
    if actual!=expected_version: raise ReviewConflict('复核版本已更新，请刷新')
    rid=latest[0] if latest else str(uuid.uuid4())
    stamp=datetime.now(timezone.utc).isoformat()
    conn.execute('INSERT INTO brand_review_versions VALUES (?,?,?,?,?,?,?,?,?,?,?)',(rid,*values,actual+1,encoded,key,digest,stamp,actual or None))
    return get_review_projection(conn,scope,rid,version=actual+1)

def save_review_version(conn,scope,payload,expected_version,idempotency_key):
    if conn.in_transaction: raise ReviewConflict('需要独立复核事务')
    try:
        conn.execute('BEGIN IMMEDIATE')
        result=_append(conn,scope,payload,expected_version,idempotency_key)
        conn.commit();return result
    except Exception:
        conn.rollback();raise

def _human_candidate(payload,records,request,rows):
    """Bounded human choice, not a fabricated provider consensus.

    Only exact canonical source observations/manual check templates are eligible.
    Two fixed neutral suffixes are the entire soft interpretation vocabulary.
    General strategy/opposition and arbitrary provider prose stay unresolved.
    """
    import brand_review_policy as p
    if not all(payload.get('slotCompletion',{}).get(s) is True for s in p.REVIEWER_IDS):return None
    cid=request['claimId']
    matches=[r for r in records if r['semanticKey']==cid]
    if {r['providerId'] for r in matches}!=set(p.REVIEWER_IDS) or any(r['hardFailures'] for r in matches):return None
    canonical=matches[0]['canonicalText']
    if not canonical or any(r['canonicalText']!=canonical for r in matches):return None
    if any(r['canonicalText']==canonical and r['semanticKey']!=cid for r in records):return None
    if request['action']=='modify' and request.get('edit')!=canonical:return None
    allowed_texts={None,'',canonical,canonical+'（待核对）',canonical+'（仅来源表述）'}
    probes=[];is_action=False
    for slot,output in payload['outputs'].items():
        for c in output['claims']:
            matching=[r for r in matches if r['providerId']==slot and r['inputHash']==p._hash(c)]
            if not matching:continue
            is_action=c.get('kind')=='action'
            if c.get('direction') or c.get('text') not in allowed_texts:return None
            probe=copy.deepcopy(c);probe['text']=canonical
            checked=p.validate_layered_reviews({slot:{'claims':[probe]}},payload['packet'],actor_id='server:human-canonical-check',server_time=datetime.now(timezone.utc).isoformat())[0]
            if checked['status']!='supported' or checked['hardFailures']:return None
            probes.append(checked)
    if len(probes)!=len(matches):return None
    original=next((x for r in rows for layer in LAYERS for x in r.get(layer,[]) if x['claimId']==cid),None)
    if not original:return None
    blocked_sources=set(payload.get('humanBlockedEvidenceIds',[]))
    if any(ref['evidenceId'] in blocked_sources for probe in probes for ref in probe['evidenceRefs']):return None
    eligible={x['claimId'] for r in rows for layer in ('facts','insights','actionOptions') for x in r.get(layer,[]) if x.get('publicationStatus') in ('supported','source_only','candidate','human_confirmed')}
    if not set(original.get('dependsOn',[]))<=eligible:return None
    clean={k:copy.deepcopy(v) for k,v in original.items() if k not in ('candidateText','candidateTexts')}
    refs={p._hash(ref):ref for probe in probes for ref in probe['evidenceRefs']}
    clean.update(kind='hypothesis' if is_action else 'inference',text=canonical,evidenceRefs=list(refs.values()),publicationStatus='human_confirmed',reasonCodes=['human_canonical_choice'],humanDecisionStatus='modified_canonical' if request['action']=='modify' else 'accepted_canonical',humanDecisionMessage='已人工确认限定来源解释，不代表三路一致。',allowExecution=False)
    if is_action:clean['actionContract']=dict(p.OBSERVATION_CONTRACT)
    return clean

def append_review_decision(conn,scope,actor,request):
    if actor.get('role')!='admin' or not actor.get('user_id') or actor.get('org_id')!=scope.get('orgId'):
        raise ReviewForbidden('当前账号无复核写入权限')
    allowed={'reviewId','expectedVersion','idempotencyKey','claimId','action','reason','edit'}
    if not isinstance(request,dict) or set(request)-allowed:raise ValueError('裁决字段无效')
    if request.get('action') not in ('accept','modify','reject') or not isinstance(request.get('reason'),str) or not 1<=len(request['reason'].strip())<=1000:
        raise ValueError('请填写裁决原因')
    if not isinstance(request.get('claimId'),str) or len(request['claimId'])>256:raise ValueError('声明无效')
    if request.get('action')=='modify' and (not isinstance(request.get('edit'),str) or not 1<=len(request['edit'].strip())<=2000):raise ValueError('修改内容无效')
    digest=hashlib.sha256(_json(request).encode()).hexdigest()
    if conn.in_transaction:raise ReviewConflict('需要独立复核事务')
    try:
        conn.execute('BEGIN IMMEDIATE')
        current=_row(conn,scope,request.get('reviewId'))
        if not current: raise ReviewNotFound('复核不存在')
        prior=conn.execute('SELECT review_id,version,request_hash FROM brand_review_versions WHERE org_id=? AND edition=? AND project_id=? AND snapshot_id=? AND idempotency_key=?',(*_scope(scope),request.get('idempotencyKey'))).fetchone()
        if prior:
            if prior[2]!=digest:raise ReviewConflict('重复请求内容不一致')
            result=get_review_projection(conn,scope,prior[0],version=prior[1]);conn.commit();return result
        payload=json.loads(current[2]);decision=payload['decision'];cid=request['claimId']
        rows=decision.get('brandConclusions',[])+decision.get('pairwiseConclusions',[])
        found=[x for r in rows for layer in LAYERS for x in r.get(layer,[]) if x.get('claimId')==cid]
        if not found:raise ReviewNotFound('声明不存在')
        before=copy.deepcopy(found)
        # Re-fuse trusted frozen original inputs where available. Human prose is
        # audit-only: it can never create three independent supports or bypass
        # source/opposition gates. Even accept of an unresolved item stays pending.
        records=[];verified=None
        if payload.get('packet') and payload.get('outputs') is not None:
            import brand_review_policy as p
            records=p.validate_layered_reviews(payload['outputs'],payload['packet'],actor_id='server:human-recheck',server_time=datetime.now(timezone.utc).isoformat())
            payload['revalidationRecords']=records
            verified=p.fuse_layered_reviews(payload['outputs'],payload['packet'],records)
            eligible={x['claimId'] for r in verified['brandConclusions']+verified['pairwiseConclusions'] for layer in ('facts','insights','actionOptions') for x in r[layer]}
        else: eligible=set()
        candidate=_human_candidate(payload,records,request,rows) if request['action'] in ('accept','modify') else None
        acknowledged=None
        if request['action']=='accept' and verified:
            source=next((x for r in verified['brandConclusions']+verified['pairwiseConclusions'] for x in r['facts'] if x['claimId']==cid),None)
            rejected=set(payload.get('humanBlockedEvidenceIds',[]))
            if source and not ({ref['evidenceId'] for ref in source['evidenceRefs']} & rejected) and cid not in payload.get('humanBlockedClaimIds',[]):
                acknowledged={**source,'humanDecisionStatus':'acknowledged_source','humanDecisionMessage':'已核对来源表述；不代表事件获客观确认。'}
        blocked=set(payload.get('humanBlockedClaimIds',[]))
        if acknowledged:
            for r in rows:
                r['facts']=[copy.deepcopy(acknowledged) if x['claimId']==cid else x for x in r.get('facts',[])]
        elif candidate:
            blocked.discard(cid)
            for r in rows:
                if not any(x.get('claimId')==cid for layer in LAYERS for x in r.get(layer,[])):continue
                for layer in LAYERS:r[layer]=[x for x in r.get(layer,[]) if x.get('claimId')!=cid]
                r['actionOptions' if candidate['kind']=='hypothesis' else 'insights'].append(copy.deepcopy(candidate))
        else:blocked.add(cid)
        rejected_sources=set(payload.get('humanBlockedEvidenceIds',[]))
        if cid in blocked:
            for r in rows:
                for fact in r.get('facts',[]):
                    if fact.get('claimId')==cid:
                        rejected_sources.update(ref['evidenceId'] for ref in fact.get('evidenceRefs',[]))
        changed=True
        while changed:
            changed=False
            for r in rows:
                for layer in LAYERS:
                    for x in r.get(layer,[]):
                        if (set(x.get('dependsOn',[])) & blocked or {ref.get('evidenceId') for ref in x.get('evidenceRefs',[])} & rejected_sources) and x['claimId'] not in blocked:
                            blocked.add(x['claimId']);changed=True
        for r in rows:
            pending={x['claimId']:x for x in r.get('unknowns',[])}
            for layer in ('facts','insights','actionOptions','disputes'):
                keep=[]
                for x in r.get(layer,[]):
                    if x['claimId'] in blocked:
                        pending[x['claimId']]={**x,'kind':'unknown','text':'该项及相关依赖待人工核对。','publicationStatus':'blocked','reasonCodes':['human_review_required'],'allowExecution':False}
                    else:keep.append(x)
                r[layer]=keep
            r['unknowns']=list(pending.values())
            for x in r['unknowns']:
                if x['claimId']==cid:
                    x['humanDecisionStatus']='rejected' if request['action']=='reject' else 'pending'
                    x['humanDecisionMessage']='该项已否决，相关依赖已暂停。' if request['action']=='reject' else '修改或采纳请求已保存，仍需核验。'
            r['status']='partial' if r.get('insights') and pending else 'available' if r.get('insights') else 'source_only' if r.get('facts') else 'insufficient_evidence'
        payload['humanBlockedClaimIds']=sorted(blocked)
        payload['humanBlockedEvidenceIds']=sorted(rejected_sources)
        decision['reviewVersion']=str(request.get('expectedVersion',0)+1)
        payload.setdefault('humanDecisions',[]).append({**request,'actorId':actor['user_id'],'serverTime':datetime.now(timezone.utc).isoformat()})
        result=_append(conn,scope,payload,request.get('expectedVersion'),request.get('idempotencyKey'),digest)
        conn.execute('INSERT INTO brand_review_decisions VALUES (?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),result['reviewId'],result['version'],actor['user_id'],datetime.now(timezone.utc).isoformat(),_json(request),_json(before),_json(result['decision'])))
        conn.commit();return result
    except Exception:
        conn.rollback();raise
