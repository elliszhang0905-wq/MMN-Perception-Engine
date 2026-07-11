import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path


def now(): return datetime.now(timezone.utc).isoformat()
def uid(prefix): return f"{prefix}_{uuid.uuid4().hex}"


class CreatorRepository:
    """Local-compatible repository. Production schema is PostgreSQL migration 001."""
    def __init__(self, path=None):
        root = Path(__file__).resolve().parents[1]
        self.path = Path(path or os.getenv("MMN_CREATOR_DB_PATH", root / "data" / "creator_distillation.db"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def connect(self):
        conn = sqlite3.connect(self.path); conn.row_factory = sqlite3.Row; return conn

    def init_schema(self):
        with self.connect() as conn:
            conn.executescript("""
            create table if not exists distillation_tasks(id text primary key, org_id text, creator_url text not null, platform text not null, range_days integer, sample_count integer, status text, stage text, progress integer, error_category text, error_message text, degraded_reason text, capabilities_json text, created_at text, updated_at text);
            create table if not exists creators(id text primary key, org_id text, platform text, platform_creator_id text, display_name text, profile_json text, created_at text, updated_at text, unique(org_id,platform,platform_creator_id));
            create table if not exists creator_profiles(id text primary key, creator_id text, version integer, status text, dna_json text, evidence_json text, corrected_by text, correction_note text, created_at text, unique(creator_id,version));
            create table if not exists assets(id text primary key, creator_id text, task_id text, platform text, asset_type text, source_id text, source_url text, title text, published_at text, metrics_json text, provenance_json text, analysis_json text, performance_score real, sample_role text, capabilities_json text, degraded_reason text, created_at text, updated_at text, unique(platform,source_id));
            create table if not exists evidence(id text primary key, asset_id text, creator_profile_id text, evidence_type text, start_ms integer, end_ms integer, quote_text text, frame_url text, comment_id text, confidence real, provenance_json text, created_at text);
            create table if not exists task_events(id text primary key, task_id text, stage text, status text, progress integer, message text, retryable integer, created_at text);
            create table if not exists raw_api_responses(id text primary key, task_id text, platform text, endpoint text, endpoint_version text, status_code integer, response_json text, fetched_at text);
            create table if not exists methodology_assets(id text primary key, methodology_type text, title text, body_json text, source_creator_ids_json text, evidence_ids_json text, created_at text, updated_at text);
            create index if not exists idx_tasks_org_status on distillation_tasks(org_id,status,updated_at);
            create index if not exists idx_assets_creator_score on assets(creator_id,performance_score desc);
            create index if not exists idx_evidence_asset_time on evidence(asset_id,start_ms);
            """)

    @staticmethod
    def _row(row):
        if not row: return None
        out = dict(row)
        for key in list(out):
            if key.endswith("_json"):
                try: out[key[:-5]] = json.loads(out.pop(key) or "{}")
                except json.JSONDecodeError: out[key[:-5]] = {}
        return out

    def create_task(self, org_id, creator_url, platform, range_days, sample_count, capabilities):
        task_id, timestamp = uid("distill"), now()
        with self.connect() as conn:
            conn.execute("insert into distillation_tasks values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         (task_id,org_id,creator_url,platform,range_days,sample_count,"queued","preflight",0,"","","",json.dumps(capabilities,ensure_ascii=False),timestamp,timestamp))
            self.event(conn, task_id, "preflight", "queued", 0, "任务已创建", True)
        return self.get_task(task_id)

    def event(self, conn, task_id, stage, status, progress, message="", retryable=False):
        conn.execute("insert into task_events values(?,?,?,?,?,?,?,?)",(uid("evt"),task_id,stage,status,progress,message,int(retryable),now()))

    def update_task(self, task_id, **fields):
        allowed={"status","stage","progress","error_category","error_message","degraded_reason","capabilities_json"}
        values={k:(json.dumps(v,ensure_ascii=False) if k.endswith("_json") else v) for k,v in fields.items() if k in allowed}
        values["updated_at"]=now()
        with self.connect() as conn:
            conn.execute("update distillation_tasks set "+",".join(f"{k}=?" for k in values)+" where id=?",(*values.values(),task_id))
            self.event(conn,task_id,values.get("stage","update"),values.get("status","running"),int(values.get("progress",0)),values.get("error_message","") or values.get("degraded_reason",""),values.get("status") in {"failed","degraded"})
        return self.get_task(task_id)

    def get_task(self, task_id):
        with self.connect() as conn:
            row=conn.execute("select * from distillation_tasks where id=?",(task_id,)).fetchone()
            events=conn.execute("select * from task_events where task_id=? order by created_at",(task_id,)).fetchall()
        out=self._row(row)
        if out: out["events"]=[self._row(x) for x in events]
        return out

    def list_tasks(self, org_id="local"):
        with self.connect() as conn: rows=conn.execute("select * from distillation_tasks where org_id=? order by created_at desc",(org_id,)).fetchall()
        return [self._row(x) for x in rows]

    def pause(self, task_id): return self.update_task(task_id,status="paused",stage="paused")
    def retry(self, task_id): return self.update_task(task_id,status="queued",stage="retry",progress=0,error_category="",error_message="")

    def list_creators(self, org_id="local", q=""):
        with self.connect() as conn:
            rows=conn.execute("select * from creators where org_id=? and (?='' or display_name like ?) order by updated_at desc",(org_id,q,f"%{q}%")).fetchall()
        return [self._row(x) for x in rows]

    def creator_detail(self, creator_id):
        with self.connect() as conn:
            creator=conn.execute("select * from creators where id=?",(creator_id,)).fetchone()
            profile=conn.execute("select * from creator_profiles where creator_id=? order by version desc limit 1",(creator_id,)).fetchone()
            assets=conn.execute("select * from assets where creator_id=? order by performance_score desc",(creator_id,)).fetchall()
        return {"creator":self._row(creator),"profile":self._row(profile),"assets":[self._row(x) for x in assets]}

    def asset_detail(self, asset_id):
        with self.connect() as conn:
            asset=conn.execute("select * from assets where id=?",(asset_id,)).fetchone()
            evidence=conn.execute("select * from evidence where asset_id=? order by start_ms",(asset_id,)).fetchall()
        return {"asset":self._row(asset),"evidence":[self._row(x) for x in evidence]}

    def methodologies(self):
        with self.connect() as conn: rows=conn.execute("select * from methodology_assets order by updated_at desc").fetchall()
        return [self._row(x) for x in rows]

    def archive_raw_response(self, task_id, platform, endpoint, endpoint_version, status_code, response):
        with self.connect() as conn:
            conn.execute("insert into raw_api_responses values(?,?,?,?,?,?,?,?)",
                         (uid("raw"),task_id,platform,endpoint,endpoint_version,status_code,json.dumps(response,ensure_ascii=False),now()))
