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
            create table if not exists opinion_judgments(id text primary key, creator_id text, version integer, status text, scope text, judgment_json text, model_validation_json text, evidence_ids_json text, created_at text, unique(creator_id,version));
            create table if not exists task_events(id text primary key, task_id text, stage text, status text, progress integer, message text, retryable integer, created_at text);
            create table if not exists raw_api_responses(id text primary key, task_id text, platform text, endpoint text, endpoint_version text, status_code integer, response_json text, fetched_at text);
            create table if not exists methodology_assets(id text primary key, methodology_type text, title text, body_json text, source_creator_ids_json text, evidence_ids_json text, created_at text, updated_at text);
            create index if not exists idx_tasks_org_status on distillation_tasks(org_id,status,updated_at);
            create index if not exists idx_assets_creator_score on assets(creator_id,performance_score desc);
            create index if not exists idx_evidence_asset_time on evidence(asset_id,start_ms);
            create index if not exists idx_opinion_creator_version on opinion_judgments(creator_id,version desc);
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
            opinion=conn.execute("select * from opinion_judgments where creator_id=? order by version desc limit 1",(creator_id,)).fetchone()
            assets=conn.execute("select * from assets where creator_id=? order by performance_score desc",(creator_id,)).fetchall()
        opinion_row=self._row(opinion)
        judgment=(opinion_row or {}).get("judgment")
        if judgment:
            judgment={**judgment,"version":opinion_row.get("version"),"recordId":opinion_row.get("id")}
        return {"creator":self._row(creator),"profile":self._row(profile),
                "opinionJudgment":judgment,"assets":[self._row(x) for x in assets]}

    def creator_opinion_inputs(self, creator_id):
        """Return comment-only evidence for opinion analysis; media evidence never enters this path."""
        with self.connect() as conn:
            assets=conn.execute("select id,source_id,title from assets where creator_id=?",(creator_id,)).fetchall()
            comments=conn.execute(
                """select e.*,a.source_id from evidence e join assets a on a.id=e.asset_id
                   where a.creator_id=? and e.evidence_type='comment' order by e.created_at""",(creator_id,)
            ).fetchall()
        return {"assetCount":len(assets),"assets":[dict(x) for x in assets],
                "comments":[self._row(x) for x in comments]}

    def creator_content_inputs(self, creator_id):
        """Return persisted evidence IDs and provenance for the content release gate."""
        with self.connect() as conn:
            creator=conn.execute("select * from creators where id=?",(creator_id,)).fetchone()
            assets=conn.execute(
                "select id,source_id,title,asset_type from assets where creator_id=? order by performance_score desc",
                (creator_id,),
            ).fetchall()
            evidence=conn.execute(
                """select e.*,a.source_id from evidence e join assets a on a.id=e.asset_id
                   where a.creator_id=? and e.evidence_type!='comment' order by e.created_at,e.id""",
                (creator_id,),
            ).fetchall()
        if not creator:
            raise KeyError("达人档案不存在")
        return {"creator":self._row(creator),"assets":[self._row(x) for x in assets],
                "evidence":[self._row(x) for x in evidence]}

    def save_opinion_judgment(self, creator_id, judgment):
        """Append a versioned judgment; raw evidence remains immutable and separately queryable."""
        with self.connect() as conn:
            creator=conn.execute("select id from creators where id=?",(creator_id,)).fetchone()
            if not creator:
                raise KeyError("达人档案不存在")
            latest=conn.execute("select max(version) as version from opinion_judgments where creator_id=?",
                                (creator_id,)).fetchone()
            version=int((latest or {"version":0})["version"] or 0)+1
            record_id=uid("opinion")
            validation=judgment.get("modelValidation") or {}
            evidence_ids=validation.get("commonEvidenceIds") or []
            conn.execute("insert into opinion_judgments values(?,?,?,?,?,?,?,?,?)",
                         (record_id,creator_id,version,judgment.get("status"),judgment.get("scope"),
                          json.dumps(judgment,ensure_ascii=False),json.dumps(validation,ensure_ascii=False),
                          json.dumps(evidence_ids,ensure_ascii=False),now()))
        return {**judgment,"version":version,"recordId":record_id}

    def asset_detail(self, asset_id, org_id=None):
        with self.connect() as conn:
            if org_id is None:
                asset=conn.execute("select * from assets where id=?",(asset_id,)).fetchone()
            else:
                asset=conn.execute(
                    """select a.* from assets a join creators c on c.id=a.creator_id
                       where a.id=? and c.org_id=?""",(asset_id,org_id)
                ).fetchone()
            if not asset:
                raise KeyError("作品资产不存在")
            evidence=conn.execute("select * from evidence where asset_id=? order by start_ms",(asset_id,)).fetchall()
        return {"asset":self._row(asset),"evidence":[self._row(x) for x in evidence]}

    def asset_processing_context(self, asset_id, org_id="local"):
        """Return the minimum scoped context needed to refresh one asset's media evidence."""
        with self.connect() as conn:
            row=conn.execute(
                """select a.*,c.display_name as creator_display_name,
                          t.creator_url,t.sample_count,t.id as distillation_task_id
                   from assets a
                   join creators c on c.id=a.creator_id
                   left join distillation_tasks t on t.id=a.task_id
                   where a.id=? and c.org_id=?""",(asset_id,org_id)
            ).fetchone()
        if not row:
            raise KeyError("作品资产不存在")
        return self._row(row)

    def save_asset_media_result(self, asset_id, org_id, evidence, capabilities, status, message="", media=None):
        """Atomically replace derived media evidence after a successful per-asset analysis."""
        timestamp=now()
        media_types=("transcript","ocr","shot","visual_summary","visual_structure")
        with self.connect() as conn:
            row=conn.execute(
                """select a.analysis_json,a.capabilities_json,a.creator_id
                   from assets a join creators c on c.id=a.creator_id
                   where a.id=? and c.org_id=?""",(asset_id,org_id)
            ).fetchone()
            if not row:
                raise KeyError("作品资产不存在")
            try: analysis=json.loads(row["analysis_json"] or "{}")
            except json.JSONDecodeError: analysis={}
            try: current_capabilities=json.loads(row["capabilities_json"] or "{}")
            except json.JSONDecodeError: current_capabilities={}
            analysis["mediaProcessing"]={"status":status,"message":str(message or "")[:500],
                                         "evidenceCount":len(evidence or []),"updatedAt":timestamp}
            if media:
                analysis["media"]=media
            if evidence:
                placeholders=",".join("?" for _ in media_types)
                conn.execute(f"delete from evidence where asset_id=? and evidence_type in ({placeholders})",
                             (asset_id,*media_types))
                profile=conn.execute(
                    "select id from creator_profiles where creator_id=? order by version desc limit 1",
                    (row["creator_id"],)
                ).fetchone()
                for item in evidence:
                    provenance={**(item.get("provenance") or {}),"metadata":item.get("metadata") or {}}
                    conn.execute(
                        "insert into evidence values(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (uid("evidence"),asset_id,profile["id"] if profile else None,
                         item.get("evidence_type") or "visual_summary",item.get("start_ms"),item.get("end_ms"),
                         item.get("quote_text"),item.get("frame_url"),item.get("comment_id") or uid("media"),
                         item.get("confidence"),json.dumps(provenance,ensure_ascii=False),timestamp),
                    )
                current_capabilities.update(capabilities or {})
            conn.execute(
                "update assets set analysis_json=?,capabilities_json=?,updated_at=? where id=?",
                (json.dumps(analysis,ensure_ascii=False),json.dumps(current_capabilities,ensure_ascii=False),
                 timestamp,asset_id),
            )
        return self.asset_detail(asset_id,org_id)

    def refresh_creator_content_profile(self, creator_id):
        """Refresh the deterministic content-evidence index after one asset is reprocessed."""
        timestamp=now()
        with self.connect() as conn:
            creator=conn.execute("select profile_json from creators where id=?",(creator_id,)).fetchone()
            profile=conn.execute(
                "select id,dna_json from creator_profiles where creator_id=? order by version desc limit 1",
                (creator_id,),
            ).fetchone()
            if not creator or not profile:
                return None
            asset_count=conn.execute("select count(*) as total from assets where creator_id=?",(creator_id,)).fetchone()["total"]
            evidence=conn.execute(
                """select e.evidence_type,e.quote_text,a.source_id
                   from evidence e join assets a on a.id=e.asset_id
                   where a.creator_id=? and e.evidence_type!='comment'
                   order by e.created_at,e.id""",(creator_id,)
            ).fetchall()
            try: dna=json.loads(profile["dna_json"] or "{}")
            except json.JSONDecodeError: dna={}
            try: platform_profile=json.loads(creator["profile_json"] or "{}")
            except json.JSONDecodeError: platform_profile={}
            summary=f"已沉淀 {asset_count} 条作品和 {len(evidence)} 条内容证据，等待提炼赛道、选题、叙事结构与表达方法。"
            dna["summary"]=summary
            dna["mediaEvidence"]=[{"sourceId":row["source_id"],"type":row["evidence_type"],
                                   "quote":row["quote_text"]} for row in evidence[:30]]
            platform_profile["summary"]=summary
            platform_profile["draft"]=dna
            conn.execute("update creator_profiles set dna_json=? where id=?",
                         (json.dumps(dna,ensure_ascii=False),profile["id"]))
            conn.execute("update creators set profile_json=?,updated_at=? where id=?",
                         (json.dumps(platform_profile,ensure_ascii=False),timestamp,creator_id))
        return summary

    def methodologies(self):
        with self.connect() as conn: rows=conn.execute("select * from methodology_assets order by updated_at desc").fetchall()
        return [self._row(x) for x in rows]

    def archive_raw_response(self, task_id, platform, endpoint, endpoint_version, status_code, response):
        with self.connect() as conn:
            raw_id = uid("raw")
            conn.execute("insert into raw_api_responses values(?,?,?,?,?,?,?,?)",
                         (raw_id,task_id,platform,endpoint,endpoint_version,status_code,json.dumps(response,ensure_ascii=False),now()))
        return raw_id

    def save_collection(self, task, creator, assets, evidence=None):
        """Persist a normalized collection without duplicating creators or platform assets."""
        timestamp = now()
        platform = str(creator["platform"])
        platform_creator_id = str(creator["platform_creator_id"])
        profile = creator.get("profile") or {}
        with self.connect() as conn:
            existing = conn.execute(
                "select id from creators where org_id=? and platform=? and platform_creator_id=?",
                (task["org_id"], platform, platform_creator_id),
            ).fetchone()
            creator_id = existing["id"] if existing else uid("creator")
            profile_json = json.dumps(profile, ensure_ascii=False)
            if existing:
                conn.execute(
                    "update creators set display_name=?,profile_json=?,updated_at=? where id=?",
                    (creator["display_name"], profile_json, timestamp, creator_id),
                )
            else:
                conn.execute(
                    "insert into creators values(?,?,?,?,?,?,?,?)",
                    (creator_id, task["org_id"], platform, platform_creator_id, creator["display_name"],
                     profile_json, timestamp, timestamp),
                )

            evidence_json = json.dumps({"identity": profile.get("identity"), "provenance": profile.get("provenance")},
                                       ensure_ascii=False)
            latest = conn.execute(
                "select version,evidence_json from creator_profiles where creator_id=? order by version desc limit 1",
                (creator_id,),
            ).fetchone()
            if not latest or latest["evidence_json"] != evidence_json:
                version = int(latest["version"] if latest else 0) + 1
                conn.execute(
                    "insert into creator_profiles values(?,?,?,?,?,?,?,?,?)",
                    (uid("profile"), creator_id, version, "needs_review",
                     json.dumps({"summary": None, "status": "awaiting_distillation"}, ensure_ascii=False),
                     evidence_json, "", "", timestamp),
                )

            profile_row = conn.execute(
                "select id from creator_profiles where creator_id=? order by version desc limit 1", (creator_id,)
            ).fetchone()
            creator_profile_id = profile_row["id"] if profile_row else None
            inserted = updated = 0
            asset_ids = []
            asset_by_source = {}
            for item in assets:
                existing_asset = conn.execute(
                    "select id from assets where platform=? and source_id=?", (platform, item["source_id"])
                ).fetchone()
                asset_id = existing_asset["id"] if existing_asset else uid("asset")
                asset_ids.append(asset_id)
                asset_by_source[str(item["source_id"])] = asset_id
                metrics = {name: item.get(name) for name in ("views", "likes", "comments", "collects", "shares")}
                analysis = {name: item.get(name) for name in
                            ("primary_tag", "tags", "interference_tags", "relative_percentile", "selection_reasons",
                             "scoring_mode", "media")}
                missing = (item.get("provenance") or {}).get("missingMetrics") or []
                degraded_reason = "缺少指标: " + "、".join(missing) if missing else ""
                values = (creator_id, task["id"], platform, item.get("asset_type") or "video", item["source_id"],
                          item.get("source_url"), item.get("title"), item.get("published_at"),
                          json.dumps(metrics, ensure_ascii=False), json.dumps(item.get("provenance") or {}, ensure_ascii=False),
                          json.dumps(analysis, ensure_ascii=False), item.get("performance_score"), item.get("sample_role"),
                          json.dumps(item.get("capabilities") or
                                     {"metadata": True, "comments": False, "transcript": False,
                                      "ocr": False, "visual": False}, ensure_ascii=False),
                          degraded_reason, timestamp, timestamp)
                if existing_asset:
                    conn.execute(
                        """update assets set creator_id=?,task_id=?,platform=?,asset_type=?,source_id=?,source_url=?,title=?,
                           published_at=?,metrics_json=?,provenance_json=?,analysis_json=?,performance_score=?,sample_role=?,
                           capabilities_json=?,degraded_reason=?,updated_at=? where id=?""",
                        (*values[:-2], values[-1], asset_id),
                    )
                    updated += 1
                else:
                    conn.execute("insert into assets values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (asset_id, *values))
                    inserted += 1
            evidence_inserted = evidence_updated = 0
            for item in evidence or []:
                asset_id = asset_by_source.get(str(item.get("source_id") or ""))
                evidence_key = str(item.get("comment_id") or "")
                if not asset_id or not evidence_key:
                    continue
                existing_evidence = conn.execute(
                    "select id from evidence where asset_id=? and comment_id=?", (asset_id, evidence_key)
                ).fetchone()
                provenance = {**(item.get("provenance") or {}), "metadata": item.get("metadata") or {}}
                if existing_evidence:
                    conn.execute(
                        """update evidence set evidence_type=?,start_ms=?,end_ms=?,quote_text=?,frame_url=?,
                           confidence=?,provenance_json=? where id=?""",
                        (item.get("evidence_type") or "comment", item.get("start_ms"), item.get("end_ms"),
                         item.get("quote_text"), item.get("frame_url"), item.get("confidence"),
                         json.dumps(provenance, ensure_ascii=False), existing_evidence["id"]),
                    )
                    evidence_updated += 1
                else:
                    conn.execute(
                        "insert into evidence values(?,?,?,?,?,?,?,?,?,?,?,?)",
                        (uid("evidence"), asset_id, creator_profile_id, item.get("evidence_type") or "comment",
                         item.get("start_ms"), item.get("end_ms"), item.get("quote_text"), item.get("frame_url"),
                         evidence_key, item.get("confidence"),
                         json.dumps(provenance, ensure_ascii=False), timestamp),
                    )
                    evidence_inserted += 1
            self.event(conn, task["id"], "review", "completed", 100,
                       f"已入库 {len(asset_ids)} 条作品、{evidence_inserted + evidence_updated} 条结构化证据，等待人工审核", False)
        return {"creatorId": creator_id, "assetIds": asset_ids, "inserted": inserted, "updated": updated,
                "evidenceInserted": evidence_inserted, "evidenceUpdated": evidence_updated}

    def save_profile_draft(self, creator_id, draft):
        """Save an evidence-indexed draft while keeping the profile in human review."""
        timestamp = now()
        with self.connect() as conn:
            latest = conn.execute(
                "select id from creator_profiles where creator_id=? order by version desc limit 1", (creator_id,)
            ).fetchone()
            if not latest:
                raise KeyError("达人档案不存在")
            conn.execute(
                "update creator_profiles set status='needs_review',dna_json=? where id=?",
                (json.dumps(draft, ensure_ascii=False), latest["id"]),
            )
            creator = conn.execute("select profile_json from creators where id=?", (creator_id,)).fetchone()
            try:
                platform_profile = json.loads(creator["profile_json"] or "{}") if creator else {}
            except json.JSONDecodeError:
                platform_profile = {}
            platform_profile["summary"] = draft.get("summary")
            platform_profile["draft"] = draft
            conn.execute("update creators set profile_json=?,updated_at=? where id=?",
                         (json.dumps(platform_profile, ensure_ascii=False), timestamp, creator_id))
        return self.creator_detail(creator_id)["profile"]
