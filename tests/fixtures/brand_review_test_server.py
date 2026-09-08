"""Dedicated temporary browser fixture. Synthetic sources; no remote providers.

Never import this into the application. Explicit temp data root and nonproduction
loopback port required. Only the synthetic project is seeded; old snapshots remain.
"""
import argparse
import copy
import ipaddress
import json
import os
from pathlib import Path
import socket
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
BRANDS = ['合成甲','合成乙','合成丙','合成丁','合成戊','合成己']
CONFIG = {'name':'合成分层复核验收','ownBrand':BRANDS[0],'competitors':BRANDS[1:],'range':'30'}


def validate_synthetic_packet(packet):
    if (packet.get('ownBrand') != BRANDS[0] or len(packet.get('brands', [])) != len(BRANDS)
            or set(packet['brands']) != set(BRANDS)):
        raise ValueError('隔离夹具仅支持合成验收项目')


def validate_fixture_paths(data_path, port):
    data = data_path.resolve()
    if (not 1024 <= port <= 65535 or port == 8765 or data.name != 'data'
            or data.parent.parent != Path('/tmp').resolve()
            or not data.parent.name.startswith('mmn-brand-review-')
            or data_path.is_symlink()):
        raise ValueError('Dedicated /tmp/mmn-brand-review-*/data and nonproduction port required')
    database = data/'commercial_demo.db'
    if not database.is_file():
        raise ValueError('Explicit isolated database copy must already exist')
    # Reject aliased writable paths before importing the app or initializing DBs.
    # This is a local test harness, not a defense against concurrent filesystem attackers.
    for root in (data, data.parent/'output', data.parent/'backups'):
        paths = [root, *root.rglob('*')] if root.exists() else [root]
        for path in paths:
            if path.is_symlink() or not path.resolve().is_relative_to(data.parent):
                raise ValueError('Fixture writable roots must not contain symbolic links')
            if path.is_file() and path.stat().st_nlink != 1:
                raise ValueError('Fixture files must be independent copies, not hard links')
    return data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-root',type=Path,required=True)
    parser.add_argument('--port',type=int,required=True)
    args=parser.parse_args()
    try:data=validate_fixture_paths(args.data_root,args.port)
    except ValueError as exc:parser.error(str(exc))
    if (ROOT/'.env').exists():
        parser.error('Fixture checkout must not contain .env')
    if any(value for key,value in os.environ.items() if 'API_KEY' in key or 'ACCESS_TOKEN' in key):
        parser.error('Remove inherited provider credentials before fixture startup')
    os.environ.update(MMN_DATA_ROOT=str(data),MMN_DB_PATH=str(data/'commercial_demo.db'),
        MMN_OUTPUT_ROOT=str(data.parent/'output'),MMN_BACKUP_ROOT=str(data.parent/'backups'),
        MMN_SOCIAL_EVIDENCE_DB=str(data/'social_evidence.sqlite'),
        MMN_HOST='127.0.0.1',MMN_PORT=str(args.port),MMN_CLOUD_LOGIN_REQUIRED='false',
        MMN_AUTO_OPEN_BROWSER='false',MMN_DESKTOP_BRIDGE_ENABLED='false',
        MMN_SOCIAL_EVIDENCE_V2_ENABLED='false',MMN_BRAND_CONCLUSIONS_MODE='enabled')
    original_connect=socket.socket.connect
    def local_connect(sock,address):
        if isinstance(address,tuple):
            try:local=ipaddress.ip_address(address[0]).is_loopback
            except ValueError:local=address[0]=='localhost'
            if not local:raise OSError('Fixture denies outbound network')
        return original_connect(sock,address)
    socket.socket.connect=local_connect
    import server
    import brand_review_policy as policy
    import brand_review_runtime as runtime
    import brand_review_repository as repository
    from social_trends import latest_snapshot
    project_id=runtime.project_id_for(BRANDS[0],BRANDS[1:])
    os.environ['MMN_BRAND_CONCLUSIONS_ALLOWLIST']='local:'+project_id
    seeding=True
    def fake_provider(slot,packet,repair,timeout,stop):
        validate_synthetic_packet(packet)
        if not seeding:stop.wait(min(8,timeout))
        claims=[]
        for i,brand in enumerate(BRANDS):
            if i==5 or (i==2 and slot=='review_3'):continue
            c={'claimId':'observation-'+str(i),'kind':'inference','brand':brand,
               'predicate':'sample_mentions','topic':'新品发布',
               'evidenceRefs':[{'evidenceId':'synthetic-'+str(i),'quote':'新品发布'}],'dependsOn':[]}
            if i==0 and slot=='review_3':c['text']=policy._canonical_text(c)+'（待核对）'
            if i==3:c['evidenceRefs'][0]['quote']='原文中不存在的引用'
            if i==4:c['text']='合成反例：销量一定上涨，禁止发布'
            claims.append(c)
            if i==1:
                claims.append({'claimId':'action-1','kind':'action','brand':brand,
                    'predicate':'manual_observation','topic':'新品发布',
                    'evidenceRefs':copy.deepcopy(c['evidenceRefs']),'dependsOn':[c['claimId']],
                    'actionContract':dict(policy.OBSERVATION_CONTRACT)})
        claims.append({'claimId':'pair-1','kind':'inference','ownBrand':BRANDS[0],'competitor':BRANDS[1],
            'predicate':'both_samples_mention','topic':'新品发布','dependsOn':[],
            'evidenceRefs':[{'evidenceId':'synthetic-0','quote':'新品发布'},
                            {'evidenceId':'synthetic-1','quote':'新品发布'}]})
        return {'claims':claims}
    def denied(*args,**kwargs):raise RuntimeError('Fixture disables real providers')
    server.call_qwen=server.call_deepseek=server.call_kimi=denied
    server.brand_review_provider_runner=fake_provider
    server.validate_runtime_security();server.init_db()
    filters={'competitors':BRANDS[1:],'timeRange':'30d','startDate':'','endDate':'','centerType':'brand_penetration'}
    with server.db() as conn:
        repository.migrate(conn)
        source=latest_snapshot(conn,BRANDS[0],'local','china',filters)
        if not source:
            items=[{'id':'synthetic-'+str(i),'brandName':brand,'platform':'weibo',
                'text':f'【合成验收，非真实市场信息】{brand}样本出现新品发布字样。',
                'title':brand+'合成来源','sourceUrl':'https://example.invalid/synthetic/'+str(i),
                'publishedAt':'2026-09-03T10:00:00+08:00','heat':10+i,'sentiment':'neutral',
                'metrics':{'likes':0,'comments':0,'shares':0}} for i,brand in enumerate(BRANDS)]
            source={'keyword':BRANDS[0],'items':items[:1],'comparisonItems':items,
                'verifiedComparisonItems':items,'modelComparisons':[{'model':b,'role':'own' if i==0 else 'competitor'} for i,b in enumerate(BRANDS)],
                'qa':{'legacyEvidence':{'status':'aligned'}},
                'admission':{'dateWindow':{'start':'2026-09-01T00:00:00+08:00','end':'2026-09-09T00:00:00+08:00','endExclusive':True,'timeRange':'30d'}}}
            snapshot=server.save_social_trend_snapshot(conn,source,'local','china',filters)
            source['snapshot']={**snapshot,'filters':filters}
    scope=runtime.scope_for_snapshot(source,'local','china')
    with server.db() as conn:
        if repository.latest_version(conn,scope)==0:
            runtime.analyze_snapshot(conn,source,scope,fake_provider)
    seeding=False
    print(json.dumps({'fixture':'synthetic_only','url':f'http://127.0.0.1:{args.port}',
        'dataRoot':str(data),'project':CONFIG,'snapshotId':scope['snapshotId'],
        'projectId':project_id,'realProviderCalls':0,'schedulerStarted':False},ensure_ascii=False),flush=True)
    server.Server((server.APP_HOST,server.PORT),server.Handler).serve_forever()


if __name__=='__main__':main()
