"""BF资产库SQLite仓储。所有读取都必须携带项目范围。"""

import json
import sqlite3
import uuid
from datetime import datetime, timezone

from .schema import validate_brief_payload


class BFRepositoryError(Exception):
    pass


class BFPermissionError(BFRepositoryError):
    pass


class BFConflictError(BFRepositoryError):
    pass


class BFNotFoundError(BFRepositoryError):
    pass


def _now():
    return datetime.now(timezone.utc).isoformat()


def _id():
    return str(uuid.uuid4())


def _row(row):
    return dict(row) if row is not None else None


class BFRepository:
    def __init__(self, connect):
        self._connect_factory = connect

    def _connect(self):
        conn = self._connect_factory()
        conn.row_factory = sqlite3.Row
        conn.execute("pragma foreign_keys=on")
        return conn

    def init_schema(self):
        with self._connect() as conn:
            conn.executescript(
                """
                create table if not exists bf_projects (
                    id text primary key,
                    org_id text not null,
                    edition text not null default 'china',
                    client_key text not null,
                    name text not null,
                    brand text,
                    model text,
                    isolation_key text not null,
                    created_by text not null,
                    created_at text not null,
                    updated_at text not null,
                    unique(org_id, client_key, name)
                );
                create table if not exists bf_documents (
                    id text primary key,
                    project_id text not null references bf_projects(id),
                    org_id text not null,
                    filename text not null,
                    extension text not null,
                    mime_type text,
                    sha256 text not null,
                    storage_path text not null,
                    size_bytes integer not null,
                    sensitivity_level text not null default 'CLIENT_CONFIDENTIAL',
                    redact_before_external integer not null default 1,
                    parse_status text not null default 'UPLOADED',
                    page_count integer,
                    uploaded_by text not null,
                    uploaded_at text not null,
                    unique(project_id, sha256)
                );
                create table if not exists bf_parse_jobs (
                    id text primary key,
                    document_id text not null references bf_documents(id),
                    stage text not null,
                    status text not null,
                    progress integer not null default 0,
                    parser_version text,
                    error_json text not null default '{}',
                    started_at text not null,
                    finished_at text
                );
                create table if not exists bf_source_segments (
                    id text primary key,
                    document_id text not null references bf_documents(id),
                    page_no integer,
                    slide_no integer,
                    paragraph_no integer,
                    sheet_name text,
                    cell_range text,
                    block_type text not null,
                    raw_text text,
                    redacted_text text,
                    table_json text not null default '{}',
                    locator_json text not null default '{}',
                    created_at text not null
                );
                create table if not exists bf_briefs (
                    id text primary key,
                    project_id text not null references bf_projects(id),
                    source_document_id text references bf_documents(id),
                    origin_type text not null,
                    bf_type text not null,
                    sample_grade text not null default 'NORMAL',
                    status text not null default 'DRAFT',
                    title text not null,
                    summary text,
                    current_version_id text,
                    current_version_no integer not null default 1,
                    outcome_json text not null default '{}',
                    created_by text not null,
                    created_at text not null,
                    updated_at text not null
                );
                create table if not exists bf_brief_versions (
                    id text primary key,
                    brief_id text not null references bf_briefs(id),
                    version_no integer not null,
                    version_kind text not null,
                    structured_json text not null,
                    rendered_markdown text not null default '',
                    base_version_id text,
                    is_final integer not null default 0,
                    created_by text not null,
                    created_at text not null,
                    unique(brief_id, version_no)
                );
                create table if not exists bf_field_provenance (
                    id text primary key,
                    version_id text not null references bf_brief_versions(id),
                    field_path text not null,
                    source_document_id text,
                    source_segment_id text,
                    origin_type text not null,
                    source_field_path text,
                    model_call_id text,
                    excerpt text,
                    confidence real,
                    is_manual integer not null default 0,
                    created_at text not null
                );
                create table if not exists bf_knowledge_chunks (
                    id text primary key,
                    project_id text not null references bf_projects(id),
                    client_key text not null,
                    brief_id text references bf_briefs(id),
                    version_id text references bf_brief_versions(id),
                    asset_type text not null,
                    scope text not null default 'PROJECT',
                    redacted_text text not null,
                    payload_json text not null default '{}',
                    sample_grade text not null default 'NORMAL',
                    allow_positive_retrieval integer not null default 1,
                    allow_cross_project integer not null default 0,
                    approved_by text,
                    created_at text not null
                );
                create table if not exists bf_template_profiles (
                    code text primary key,
                    name text not null,
                    section_intents_json text not null,
                    source text not null,
                    status text not null default 'ACTIVE',
                    usage_count integer not null default 0,
                    created_by text not null,
                    created_at text not null,
                    updated_at text not null
                );
                create table if not exists bf_generation_runs (
                    id text primary key,
                    project_id text not null references bf_projects(id),
                    created_by text not null,
                    input_json text not null,
                    strategy_judgment_json text not null default '{}',
                    retrieval_json text not null default '[]',
                    bf_type text not null,
                    stage text not null,
                    status text not null,
                    output_brief_id text,
                    error_json text not null default '{}',
                    created_at text not null,
                    updated_at text not null
                );
                create table if not exists bf_model_calls (
                    id text primary key,
                    run_id text,
                    parse_job_id text,
                    step text not null,
                    provider text not null,
                    model text,
                    redaction_mode text not null,
                    redacted_input_json text not null default '{}',
                    output_hash text,
                    latency_ms integer,
                    token_json text not null default '{}',
                    status text not null,
                    error text,
                    created_at text not null
                );
                create table if not exists bf_exports (
                    id text primary key,
                    version_id text not null references bf_brief_versions(id),
                    format text not null,
                    filename text not null,
                    storage_path text not null,
                    checksum text not null,
                    created_by text not null,
                    created_at text not null
                );
                create index if not exists idx_bf_documents_project on bf_documents(project_id, uploaded_at);
                create index if not exists idx_bf_segments_document on bf_source_segments(document_id, page_no, paragraph_no);
                create index if not exists idx_bf_briefs_project on bf_briefs(project_id, sample_grade, bf_type, updated_at);
                create index if not exists idx_bf_chunks_scope on bf_knowledge_chunks(project_id, scope, sample_grade, asset_type);
                """
            )
            columns = {row["name"] for row in conn.execute("pragma table_info(bf_briefs)").fetchall()}
            if "outcome_json" not in columns:
                conn.execute("alter table bf_briefs add column outcome_json text not null default '{}'")
            self._seed_template_profiles(conn)

    def _seed_template_profiles(self, conn):
        seeds = (
            ("STORE_VISIT", "探店BF", ["PROJECT_BACKGROUND", "TARGET_AUDIENCE", "STORE_VISIT_SCRIPT", "STATIC_EXPERIENCE", "CTA", "RISK_CONTROL", "DELIVERY"]),
            ("CLOUD_REVIEW", "云评/口播BF", ["PROJECT_BACKGROUND", "CORE_ARGUMENT", "FACT_SUPPORT", "TOPIC_MATRIX", "CREATOR_ASSIGNMENT", "VOICEOVER_LOGIC", "RISK_CONTROL", "DELIVERY"]),
            ("HIGH_END_PHOTOGRAPHY", "高质感摄影BF", ["PROJECT_BACKGROUND", "VISUAL_TONE", "PRODUCT_POINT_DISTRIBUTION", "SCENE_PLAN", "SHOT_LIST", "VEHICLE_LOGISTICS", "MATERIAL_RETURN"]),
        )
        timestamp = _now()
        for code, name, intents in seeds:
            conn.execute(
                """insert or ignore into bf_template_profiles
                (code,name,section_intents_json,source,status,usage_count,created_by,created_at,updated_at)
                values (?,?,?,?,?,?,?,?,?)""",
                (code, name, json.dumps(intents, ensure_ascii=False), "SYSTEM_SEED", "ACTIVE", 0, "system", timestamp, timestamp),
            )

    def create_project(self, *, org_id, edition, client_key, name, brand="", model="", created_by):
        project_id = _id()
        timestamp = _now()
        isolation_key = f"{org_id}:{client_key}:{project_id}"
        with self._connect() as conn:
            conn.execute(
                "insert into bf_projects values (?,?,?,?,?,?,?,?,?,?,?)",
                (project_id, org_id, edition, client_key, name, brand, model, isolation_key, created_by, timestamp, timestamp),
            )
            return _row(conn.execute("select * from bf_projects where id=?", (project_id,)).fetchone())

    def get_project(self, project_id, org_id):
        with self._connect() as conn:
            row = conn.execute("select * from bf_projects where id=?", (project_id,)).fetchone()
        if not row:
            raise BFNotFoundError("BF项目不存在")
        if row["org_id"] != org_id:
            raise BFPermissionError("BF项目不属于当前组织")
        return _row(row)

    def list_projects(self, org_id):
        with self._connect() as conn:
            rows = conn.execute("select * from bf_projects where org_id=? order by updated_at desc", (org_id,)).fetchall()
        return [_row(item) for item in rows]

    def create_document(self, *, project_id, org_id, filename, extension, mime_type, sha256, storage_path, size_bytes, uploaded_by):
        self._require_project(project_id, org_id)
        document_id = _id()
        with self._connect() as conn:
            conn.execute(
                """insert into bf_documents
                (id,project_id,org_id,filename,extension,mime_type,sha256,storage_path,size_bytes,uploaded_by,uploaded_at)
                values (?,?,?,?,?,?,?,?,?,?,?)""",
                (document_id, project_id, org_id, filename, extension, mime_type, sha256, storage_path, int(size_bytes), uploaded_by, _now()),
            )
            return _row(conn.execute("select * from bf_documents where id=?", (document_id,)).fetchone())

    def get_document(self, document_id, project_id, org_id):
        with self._connect() as conn:
            row = conn.execute("select * from bf_documents where id=?", (document_id,)).fetchone()
        if not row:
            raise BFNotFoundError("BF文件不存在")
        if row["project_id"] != project_id or row["org_id"] != org_id:
            raise BFPermissionError("BF文件不属于当前项目")
        return _row(row)

    def list_documents(self, project_id, org_id):
        self._require_project(project_id, org_id)
        with self._connect() as conn:
            rows = conn.execute("select * from bf_documents where project_id=? order by uploaded_at desc", (project_id,)).fetchall()
        return [_row(item) for item in rows]

    def save_parse_result(self, document_id, project_id, parsed):
        timestamp = _now()
        with self._connect() as conn:
            document = conn.execute("select * from bf_documents where id=?", (document_id,)).fetchone()
            if not document:
                raise BFNotFoundError("BF文件不存在")
            if document["project_id"] != project_id:
                raise BFPermissionError("BF文件不属于当前项目")
            conn.execute("delete from bf_source_segments where document_id=?", (document_id,))
            for item in parsed.get("segments") or []:
                segment_id = _id()
                item["id"] = segment_id
                conn.execute(
                    """insert into bf_source_segments
                    (id,document_id,page_no,slide_no,paragraph_no,sheet_name,cell_range,block_type,raw_text,redacted_text,table_json,locator_json,created_at)
                    values (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        segment_id,
                        document_id,
                        item.get("pageNo"),
                        item.get("slideNo"),
                        item.get("paragraphNo"),
                        item.get("sheetName"),
                        item.get("cellRange"),
                        item.get("blockType") or "TEXT",
                        item.get("text") or "",
                        item.get("text") or "",
                        json.dumps(item.get("table") or [], ensure_ascii=False),
                        json.dumps(item.get("locator") or {}, ensure_ascii=False),
                        timestamp,
                    ),
                )
            page_count = max(
                [int(item.get("pageNo") or item.get("slideNo") or 0) for item in parsed.get("segments") or []] or [0]
            ) or None
            conn.execute(
                "update bf_documents set parse_status='STRUCTURED', page_count=? where id=?",
                (page_count, document_id),
            )
            return _row(conn.execute("select * from bf_documents where id=?", (document_id,)).fetchone())

    def list_segments(self, document_id, project_id):
        with self._connect() as conn:
            document = conn.execute("select project_id from bf_documents where id=?", (document_id,)).fetchone()
            if not document:
                raise BFNotFoundError("BF文件不存在")
            if document["project_id"] != project_id:
                raise BFPermissionError("BF文件不属于当前项目")
            rows = conn.execute(
                "select * from bf_source_segments where document_id=? order by coalesce(page_no,slide_no,0), coalesce(paragraph_no,0), created_at",
                (document_id,),
            ).fetchall()
        result = []
        for item in rows:
            value = _row(item)
            value["table"] = json.loads(value.pop("table_json"))
            value["locator"] = json.loads(value.pop("locator_json"))
            result.append(value)
        return result

    def create_brief(self, *, project_id, origin_type, bf_type, title, structured_payload, created_by, source_document_id=None, sample_grade="NORMAL", status="DRAFT"):
        validate_brief_payload(structured_payload)
        if sample_grade not in {"NORMAL", "QUALITY", "NEGATIVE", "DISABLED"}:
            raise ValueError("未知样本等级")
        brief_id = _id()
        version_id = _id()
        timestamp = _now()
        payload_text = json.dumps(structured_payload, ensure_ascii=False)
        with self._connect() as conn:
            project = conn.execute("select id from bf_projects where id=?", (project_id,)).fetchone()
            if not project:
                raise BFNotFoundError("BF项目不存在")
            conn.execute(
                """insert into bf_briefs
                (id,project_id,source_document_id,origin_type,bf_type,sample_grade,status,title,summary,current_version_id,current_version_no,outcome_json,created_by,created_at,updated_at)
                values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (brief_id, project_id, source_document_id, origin_type, bf_type, sample_grade, status, title, structured_payload.get("summary", ""), version_id, 1, "{}", created_by, timestamp, timestamp),
            )
            conn.execute(
                """insert into bf_brief_versions
                (id,brief_id,version_no,version_kind,structured_json,rendered_markdown,created_by,created_at)
                values (?,?,?,?,?,?,?,?)""",
                (version_id, brief_id, 1, "EXTRACTED" if origin_type == "UPLOADED" else "GENERATED", payload_text, "", created_by, timestamp),
            )
            return _row(conn.execute("select * from bf_briefs where id=?", (brief_id,)).fetchone())

    def save_brief_version(self, *, brief_id, project_id, structured_payload, rendered_markdown, version_kind, base_version_no, created_by, is_final=False):
        validate_brief_payload(structured_payload)
        timestamp = _now()
        with self._connect() as conn:
            brief = conn.execute("select * from bf_briefs where id=?", (brief_id,)).fetchone()
            if not brief:
                raise BFNotFoundError("BF不存在")
            if brief["project_id"] != project_id:
                raise BFPermissionError("BF不属于当前项目")
            if int(brief["current_version_no"]) != int(base_version_no):
                raise BFConflictError("BF版本已更新")
            version_no = int(base_version_no) + 1
            version_id = _id()
            conn.execute(
                """insert into bf_brief_versions
                (id,brief_id,version_no,version_kind,structured_json,rendered_markdown,base_version_id,is_final,created_by,created_at)
                values (?,?,?,?,?,?,?,?,?,?)""",
                (version_id, brief_id, version_no, version_kind, json.dumps(structured_payload, ensure_ascii=False), str(rendered_markdown or ""), brief["current_version_id"], 1 if is_final else 0, created_by, timestamp),
            )
            conn.execute(
                """update bf_briefs set current_version_id=?, current_version_no=?, summary=?, status=?, updated_at=? where id=?""",
                (version_id, version_no, structured_payload.get("summary", ""), "FINAL" if is_final else brief["status"], timestamp, brief_id),
            )
            return _row(conn.execute("select * from bf_brief_versions where id=?", (version_id,)).fetchone())

    def get_brief(self, brief_id, project_id):
        with self._connect() as conn:
            brief = conn.execute("select * from bf_briefs where id=?", (brief_id,)).fetchone()
            if not brief:
                raise BFNotFoundError("BF不存在")
            if brief["project_id"] != project_id:
                raise BFPermissionError("BF不属于当前项目")
            version = conn.execute("select * from bf_brief_versions where id=?", (brief["current_version_id"],)).fetchone()
        result = _row(brief)
        result["outcome"] = json.loads(result.pop("outcome_json") or "{}")
        result["currentVersion"] = _row(version)
        result["currentVersion"]["structured"] = json.loads(result["currentVersion"].pop("structured_json"))
        return result

    def update_brief_final_metadata(self, brief_id, project_id, *, sample_grade, outcome):
        if sample_grade not in {"NORMAL", "QUALITY", "NEGATIVE", "DISABLED"}:
            raise ValueError("未知样本等级")
        with self._connect() as conn:
            brief = conn.execute("select * from bf_briefs where id=?", (brief_id,)).fetchone()
            if not brief:
                raise BFNotFoundError("BF不存在")
            if brief["project_id"] != project_id:
                raise BFPermissionError("BF不属于当前项目")
            conn.execute(
                "update bf_briefs set sample_grade=?, status='FINAL', outcome_json=?, updated_at=? where id=?",
                (sample_grade, json.dumps(outcome or {}, ensure_ascii=False), _now(), brief_id),
            )
        return self.get_brief(brief_id, project_id)

    def replace_knowledge_chunks(self, *, project_id, client_key, brief_id, version_id, chunks, approved_by):
        with self._connect() as conn:
            brief = conn.execute("select project_id,sample_grade from bf_briefs where id=?", (brief_id,)).fetchone()
            if not brief or brief["project_id"] != project_id:
                raise BFPermissionError("BF不属于当前项目")
            conn.execute("delete from bf_knowledge_chunks where brief_id=? and version_id=?", (brief_id, version_id))
            for item in chunks:
                conn.execute(
                    """insert into bf_knowledge_chunks
                    (id,project_id,client_key,brief_id,version_id,asset_type,scope,redacted_text,payload_json,sample_grade,allow_positive_retrieval,allow_cross_project,approved_by,created_at)
                    values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        _id(), project_id, client_key, brief_id, version_id,
                        item.get("assetType") or "METHOD",
                        item.get("scope") or "PROJECT",
                        item.get("text") or "",
                        json.dumps(item.get("payload") or {}, ensure_ascii=False),
                        brief["sample_grade"],
                        1 if item.get("allowPositive", True) else 0,
                        1 if item.get("allowCrossProject", False) else 0,
                        approved_by,
                        _now(),
                    ),
                )
            row = conn.execute("select count(*) as total from bf_knowledge_chunks where brief_id=? and version_id=?", (brief_id, version_id)).fetchone()
        return int(row["total"])

    def list_knowledge_chunks(self, project_id, brief_id=None, asset_type=None):
        query = "select * from bf_knowledge_chunks where project_id=?"
        params = [project_id]
        if brief_id:
            query += " and brief_id=?"
            params.append(brief_id)
        if asset_type:
            query += " and asset_type=?"
            params.append(asset_type)
        query += " order by created_at desc"
        with self._connect() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        return [_row(item) for item in rows]

    def list_briefs(self, project_id, sample_grade=None, bf_type=None):
        clauses = ["project_id=?"]
        params = [project_id]
        if sample_grade:
            clauses.append("sample_grade=?")
            params.append(sample_grade)
        if bf_type:
            clauses.append("bf_type=?")
            params.append(bf_type)
        with self._connect() as conn:
            rows = conn.execute(
                f"select * from bf_briefs where {' and '.join(clauses)} order by updated_at desc",
                tuple(params),
            ).fetchall()
        return [_row(item) for item in rows]

    def create_generation_run(self, *, project_id, created_by, input_payload, bf_type):
        run_id = _id()
        timestamp = _now()
        with self._connect() as conn:
            conn.execute(
                """insert into bf_generation_runs
                (id,project_id,created_by,input_json,bf_type,stage,status,created_at,updated_at)
                values (?,?,?,?,?,?,?,?,?)""",
                (run_id, project_id, created_by, json.dumps(input_payload, ensure_ascii=False), bf_type, "QUEUED", "RUNNING", timestamp, timestamp),
            )
            return _row(conn.execute("select * from bf_generation_runs where id=?", (run_id,)).fetchone())

    def complete_generation_run(self, run_id, *, strategy, retrieval, output_brief_id, status, error=None):
        with self._connect() as conn:
            conn.execute(
                """update bf_generation_runs set strategy_judgment_json=?, retrieval_json=?, output_brief_id=?, stage=?, status=?, error_json=?, updated_at=? where id=?""",
                (
                    json.dumps(strategy or {}, ensure_ascii=False),
                    json.dumps(retrieval or [], ensure_ascii=False),
                    output_brief_id,
                    status,
                    status,
                    json.dumps(error or {}, ensure_ascii=False),
                    _now(),
                    run_id,
                ),
            )
            return _row(conn.execute("select * from bf_generation_runs where id=?", (run_id,)).fetchone())

    def record_model_call(self, *, run_id, step, provider, model, redaction_mode, redacted_input, output_hash, status, error=""):
        call_id = _id()
        with self._connect() as conn:
            conn.execute(
                """insert into bf_model_calls
                (id,run_id,step,provider,model,redaction_mode,redacted_input_json,output_hash,status,error,created_at)
                values (?,?,?,?,?,?,?,?,?,?,?)""",
                (call_id, run_id, step, provider, model, redaction_mode, json.dumps(redacted_input or {}, ensure_ascii=False), output_hash, status, error, _now()),
            )
        return call_id

    def list_retrieval_candidates(self, project_id, purpose="POSITIVE"):
        purpose = str(purpose or "POSITIVE").upper()
        if purpose == "RISK":
            grades = ("NEGATIVE",)
            order = "updated_at desc"
        else:
            grades = ("QUALITY", "NORMAL")
            order = "case sample_grade when 'QUALITY' then 0 else 1 end, updated_at desc"
        placeholders = ",".join("?" for _ in grades)
        with self._connect() as conn:
            rows = conn.execute(
                f"select * from bf_briefs where project_id=? and sample_grade in ({placeholders}) order by {order}",
                (project_id, *grades),
            ).fetchall()
        return [_row(item) for item in rows]

    def save_template_profile(self, *, code, name, section_intents, source, created_by):
        code = str(code or "").strip().upper()
        if not code or not isinstance(section_intents, list) or not section_intents:
            raise ValueError("BF范式编码和章节意图不能为空")
        timestamp = _now()
        with self._connect() as conn:
            conn.execute(
                """insert into bf_template_profiles
                (code,name,section_intents_json,source,status,usage_count,created_by,created_at,updated_at)
                values (?,?,?,?,?,?,?,?,?)
                on conflict(code) do update set
                  name=excluded.name,
                  section_intents_json=excluded.section_intents_json,
                  source=excluded.source,
                  status='ACTIVE',
                  updated_at=excluded.updated_at""",
                (code, str(name or code), json.dumps(section_intents, ensure_ascii=False), source, "ACTIVE", 0, created_by, timestamp, timestamp),
            )
        return self.get_template_profile(code)

    def get_template_profile(self, code):
        with self._connect() as conn:
            row = conn.execute("select * from bf_template_profiles where code=? and status='ACTIVE'", (str(code or "").strip().upper(),)).fetchone()
        if not row:
            raise BFNotFoundError("BF范式不存在")
        result = _row(row)
        result["section_intents"] = json.loads(result.pop("section_intents_json"))
        return result

    def find_matching_template_profile(self, content_intents):
        requested = {str(item).strip() for item in content_intents or [] if str(item).strip()}
        if not requested:
            return None
        with self._connect() as conn:
            rows = conn.execute(
                "select * from bf_template_profiles where status='ACTIVE' and source='FINAL_BF'"
            ).fetchall()
        best = None
        best_score = (0, 0.0, "")
        for row in rows:
            result = _row(row)
            sections = json.loads(result.pop("section_intents_json"))
            reusable = {str(item).strip() for item in sections if str(item).strip()}
            overlap = len(requested & reusable)
            if not overlap:
                continue
            union = len(requested | reusable) or 1
            score = (overlap, overlap / union, result["updated_at"])
            if score > best_score:
                result["section_intents"] = sections
                best, best_score = result, score
        return best

    def _require_project(self, project_id, org_id):
        with self._connect() as conn:
            row = conn.execute("select id from bf_projects where id=? and org_id=?", (project_id, org_id)).fetchone()
        if not row:
            raise BFPermissionError("BF项目不属于当前组织")
        return True
