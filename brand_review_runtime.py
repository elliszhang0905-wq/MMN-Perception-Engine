"""Brand-only opt-in runtime. Fixed blind slots; bounded daemon calls and DTOs."""
import copy
import hashlib
import json
import os
import queue
import threading
import time
from contextlib import nullcontext
from datetime import datetime, timezone
import brand_review_policy as policy

PROMPT_VERSION='brand-review-prompt-v1'

class CancellationToken(threading.Event):
    """Serializes cancellation acceptance with final review publication."""
    def __init__(self):
        super().__init__()
        self.publication_lock = threading.Lock()
        self.published = False

def mode_for(scope,env=None):
    env=os.environ if env is None else env
    mode=env.get('MMN_BRAND_CONCLUSIONS_MODE','legacy')
    entries={x.strip() for x in env.get('MMN_BRAND_CONCLUSIONS_ALLOWLIST','').split(',') if x.strip()}
    key=scope.get('orgId','')+':'+scope.get('projectId','')
    return mode if mode in ('enabled','shadow') and key in entries else 'legacy'

def scope_for_snapshot(result,org_id,edition):
    snapshot=result.get('snapshot') or {}
    if not snapshot.get('id'):raise ValueError('缺少服务端证据快照')
    filters=snapshot.get('filters') or {}
    project=project_id_for(result.get('keyword'),filters.get('competitors',[]))
    return dict(orgId=org_id,edition=edition,projectId=project,snapshotId=snapshot['id'])

def project_id_for(keyword,competitors):
    identity={'keyword':keyword,'competitors':competitors,'centerType':'brand_penetration'}
    return hashlib.sha256(json.dumps(identity,sort_keys=True,ensure_ascii=False).encode()).hexdigest()[:24]

def _bounded(value,depth=0):
    if depth>12:raise ValueError('structure')
    if isinstance(value,str):
        if len(value)>20000:raise ValueError('string')
    elif isinstance(value,list):
        if len(value)>200:raise ValueError('list')
        for x in value:_bounded(x,depth+1)
    elif isinstance(value,dict):
        if len(value)>60:raise ValueError('object')
        for k,v in value.items():
            if not isinstance(k,str) or len(k)>100:raise ValueError('key')
            _bounded(v,depth+1)
    elif value is not None and type(value) not in (int,float,bool):raise ValueError('type')

def admit(raw):
    """Structure admission only; substantive disputes are not retry triggers."""
    if isinstance(raw,str):
        if len(raw.encode())>1_000_000:raise ValueError('bytes')
        raw=json.loads(raw)
    encoded=json.dumps(raw,allow_nan=False)
    if len(encoded.encode())>1_000_000:raise ValueError('bytes')
    if not isinstance(raw,dict) or not isinstance(raw.get('claims'),list) or len(raw['claims'])>200:raise ValueError('claims')
    good=[];bad=[]
    for c in raw['claims']:
        try:
            _bounded(c)
            if not isinstance(c,dict) or not isinstance(c.get('claimId'),str) or not 1<=len(c['claimId'])<=256:raise ValueError('claim_id')
            if c.get('kind') not in ('inference','action') or not isinstance(c.get('predicate'),str) or not isinstance(c.get('topic'),str):raise ValueError('claim_type')
            for key in ('brand','ownBrand','competitor','model','text','direction'):
                if key in c and not isinstance(c[key],str):raise ValueError('string')
            refs=c.get('evidenceRefs');deps=c.get('dependsOn')
            if not isinstance(refs,list) or len(refs)>50 or not isinstance(deps,list) or any(not isinstance(x,str) or len(x)>256 for x in deps):raise ValueError('refs')
            if any(not isinstance(r,dict) or not isinstance(r.get('evidenceId'),str) or not isinstance(r.get('quote'),str) for r in refs):raise ValueError('anchor')
            if 'dateWindow' in c and (not isinstance(c['dateWindow'],dict) or any(not isinstance(x,str) for x in c['dateWindow'].values())):raise ValueError('window')
            good.append(copy.deepcopy(c))
        except (ValueError,TypeError):bad.append(copy.deepcopy(c))
    return good,bad

def run_reviews(packet,provider_runner,*,cancel=None,total_timeout=300,call_timeout=120):
    cancel=cancel or threading.Event()
    deadline=time.monotonic()+min(300,max(0,total_timeout));call_timeout=min(120,max(0,call_timeout))
    outputs={};errors={};calls=0;raw_outputs={};completion={s:False for s in policy.REVIEWER_IDS}
    # Each wave is blind. Workers only write their private queue. Main thread
    # alone accepts results before deadline; late workers cannot mutate output.
    def invoke(slot,repair):
        nonlocal calls
        timeout=min(call_timeout,deadline-time.monotonic())
        if cancel.is_set() or timeout<=0:return None
        q=queue.Queue(maxsize=1);stop=threading.Event();calls+=1
        def work():
            try:q.put((True,provider_runner(slot,copy.deepcopy(packet),copy.deepcopy(repair),timeout,stop)))
            except Exception as exc:q.put((False,exc))
        threading.Thread(target=work,daemon=True,name='brand-review-'+slot).start()
        return q,stop,time.monotonic()+timeout
    active={s:invoke(s,None) for s in policy.REVIEWER_IDS}
    repairs={}
    for wave in range(2):
        while active:
            for slot,handle in list(active.items()):
                if handle is None:active.pop(slot);continue
                q,stop,until=handle
                if cancel.is_set() or time.monotonic()>=min(deadline,until):
                    stop.set();errors[slot]='复核超时或已取消';active.pop(slot);continue
                try:ok,value=q.get_nowait()
                except queue.Empty:continue
                active.pop(slot)
                if not ok:
                    code=getattr(value,'status_code',None) or getattr(getattr(value,'response',None),'status_code',None)
                    message=str(value).lower()
                    fatal=code in (401,402,403) or any(x in message for x in ('quota','insufficient_quota','额度','nonretryable','401','403','未授权','被拒绝','未配置','api_key'))
                    errors[slot]='复核权限或额度不足' if fatal else '复核通道未完成'
                    if not fatal and wave==0:repairs[slot]={'invalidClaims':[],'errors':['channel_incomplete']}
                    continue
                raw_outputs.setdefault(slot,[]).append(copy.deepcopy(value))
                try:good,bad=admit(value)
                except (ValueError,TypeError,OverflowError):good=[];bad=[];errors[slot]='复核结构未完成'
                else:
                    errors.pop(slot,None)
                    if not good and not bad: errors[slot]='复核未返回声明'
                existing=outputs.setdefault(slot,{'claims':[]})['claims'];seen={x['claimId'] for x in existing}
                allowed={c.get('claimId') for c in repairs.get(slot,{}).get('invalidClaims',[]) if isinstance(c,dict)}
                existing.extend(c for c in good if c['claimId'] not in seen and (wave==0 or not allowed or c['claimId'] in allowed))
                original_bad=repairs.get(slot,{}).get('invalidClaims',[])
                completion[slot]=bool(good) and not bad and slot not in errors and (wave==0 or (
                    all(isinstance(c,dict) and isinstance(c.get('claimId'),str) for c in original_bad)
                    and allowed<={c['claimId'] for c in good}))
                if wave==0 and (bad or slot in errors):repairs[slot]={'invalidClaims':bad,'errors':['invalid_structure']}
            if active:time.sleep(.002)
        if wave==0:
            active={s:invoke(s,repair) for s,repair in repairs.items() if time.monotonic()<deadline and not cancel.is_set()}
    records=policy.validate_layered_reviews(outputs,packet,actor_id='server:brand-review',server_time=datetime.now(timezone.utc).isoformat())
    decision=policy.fuse_layered_reviews(outputs,packet,records)
    return dict(outputs=outputs,rawOutputs=raw_outputs,errors=errors,callCount=calls,slotCompletion=completion,validationRecords=records,decision=decision,packet=copy.deepcopy(packet))

def window_for_snapshot(result):
    filters=(result.get('snapshot') or {}).get('filters') or {}
    def exact(value):
        if (not isinstance(value,dict)
                or not all(isinstance(value.get(k),str) and value[k] for k in ('start','end'))
                or ('endExclusive' in value and type(value['endExclusive']) is not bool)):
            raise ValueError('冻结证据缺少有效时间窗')
        # Existing producer includes descriptive timeRange metadata. Only exact
        # source admission bounds enter policy/fingerprints; never sample dates.
        return {k:copy.deepcopy(value[k]) for k in ('start','end','endExclusive') if k in value}
    admission=result.get('admission') or {}
    if 'dateWindow' in result:
        window=exact(result['dateWindow'])
        if 'dateWindow' in admission and exact(admission['dateWindow'])!=window:
            raise ValueError('冻结证据时间窗冲突')
        return window
    if 'dateWindow' in admission:return exact(admission['dateWindow'])
    return exact({'start':filters.get('startDate'),'end':filters.get('endDate')})

def analyze_snapshot(conn,result,scope,provider_runner,*,cancel=None):
    from brand_review_repository import latest_version,save_review_version
    if cancel and cancel.is_set():raise ValueError('复核已取消')
    version=latest_version(conn,scope)
    window=window_for_snapshot(result)
    packet=policy.build_layered_packet(result,{**scope,'promptVersion':PROMPT_VERSION,'reviewVersion':str(version+1)},window)
    payload=run_reviews(packet,provider_runner,cancel=cancel)
    import uuid
    with getattr(cancel,'publication_lock',nullcontext()):
        authorized = getattr(cancel,'authorized_check',None)
        if callable(authorized) and not authorized():cancel.set()
        if cancel and cancel.is_set():raise ValueError('复核已取消')
        review=save_review_version(conn,scope,payload,version,str(uuid.uuid4()))
        if isinstance(cancel,CancellationToken):cancel.published=True
        return review
