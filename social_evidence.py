"""Persistent public-social evidence infrastructure for MMN.

This module deliberately separates acquisition records, canonical evidence and
task-specific marts. Platform observations remain evidence; they never become
market demand, sales causality or market-penetration claims by themselves.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo


SCHEMA_VERSION = "social-evidence-query-v2"
ALLOWED_CENTERS = {"social_trend", "brand_penetration", "nsr_validation"}
ALLOWED_PLATFORMS = {"douyin", "xiaohongshu", "weibo", "bilibili", "wechat", "kuaishou"}
TERMINAL_STATUSES = {"ready", "degraded", "manual_required", "failed"}
ACTIVE_STATUSES = {"queued", "planning", "budget_check", "running", "collecting_discovery", "normalizing", "admission", "building_evidence", "validating"}
INTERRUPTED_STATUSES = ACTIVE_STATUSES - {"queued"}
SENSITIVE_KEYS = re.compile(r"authorization|api[_-]?key|token|cookie|secret|password", re.IGNORECASE)
SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def _stable_id(*parts):
    value = "|".join(str(part or "") for part in parts)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _unique_strings(values, limit=40):
    result, seen = [], set()
    for value in values or []:
        text = str(value or "").strip()
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            result.append(text)
        if len(result) >= limit:
            break
    return result


def _safe_date(value, field):
    text = str(value or "").strip()
    try:
        datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field}必须是ISO日期") from exc
    return text


def _nsr_validation_contract(payload, subject, competitors):
    vehicle = payload.get("vehicleContext") if isinstance(payload.get("vehicleContext"), dict) else {}
    nsr_source = payload.get("nsrSource") if isinstance(payload.get("nsrSource"), dict) else {}
    targets = payload.get("validationTargets") if isinstance(payload.get("validationTargets"), list) else []
    model = str(vehicle.get("model") or "").strip()
    if not model or model.casefold() != str(subject.get("model") or "").strip().casefold():
        raise ValueError("vehicleContext必须与当前车型一致")
    required_vehicle = ("modelCode", "contextSource", "contextVersion")
    if any(not str(vehicle.get(key) or "").strip() for key in required_vehicle):
        raise ValueError("vehicleContext缺少车型编码或上下文版本")
    if not str(nsr_source.get("datasetVersion") or "").strip() or not str(nsr_source.get("fingerprint") or "").strip():
        raise ValueError("nsrSource必须包含真实数据版本和指纹")
    if not 1 <= len(targets) <= 5:
        raise ValueError("NSR验证标签必须为1至5个")
    if len(competitors) > 2:
        raise ValueError("NSR验证最多选择2个竞品")

    frozen_targets, target_ids = [], set()
    term_groups = {key: [] for key in ("directed", "counter")}
    for row in targets:
        row = row if isinstance(row, dict) else {}
        target_id = str(row.get("targetId") or "").strip()
        attribute_id = str(row.get("attributeId") or "").strip()
        label = str(row.get("label") or "").strip()
        if not target_id or not attribute_id or not label or target_id in target_ids:
            raise ValueError("NSR验证标签标识缺失或重复")
        try:
            baseline_nsr = float(row.get("baselineNsr"))
        except (TypeError, ValueError) as exc:
            raise ValueError("NSR基线值必须是数字") from exc
        terms = row.get("queryTerms") if isinstance(row.get("queryTerms"), dict) else {}
        normalized_terms = {key: _unique_strings(terms.get(key), 12) for key in (
            "canonical", "userLanguage", "scenes", "support", "challenge", "comparison"
        )}
        if not any(normalized_terms.values()):
            raise ValueError("NSR验证标签必须包含检索词")
        target_ids.add(target_id)
        frozen_targets.append({
            "targetId": target_id, "attributeId": attribute_id, "label": label,
            "baselineNsr": baseline_nsr, "queryTerms": normalized_terms,
        })
        term_groups["directed"].extend(normalized_terms["canonical"] + normalized_terms["userLanguage"]
                                       + normalized_terms["scenes"] + normalized_terms["support"]
                                       + normalized_terms["comparison"])
        term_groups["counter"].extend(normalized_terms["challenge"])

    entities = [(str(subject["model"]), "subject"), *[(name, "competitor") for name in competitors]]
    shards = []
    for entity, role in entities:
        for query_type in ("directed", "counter", "broad"):
            # Supplier search accepts a single keyword phrase, not a portable Boolean DSL.
            # Keep one directed/counter seed and let the broad shard recover the remaining labels.
            terms = _unique_strings(term_groups.get(query_type), 1)
            query = " ".join([entity, *terms]).strip()
            shards.append({
                "queryId": f"nsr_q_{len(shards) + 1}", "entity": entity, "entityRole": role,
                "queryType": query_type, "query": query,
                "targetIds": [row["targetId"] for row in frozen_targets] if query_type != "broad" else [],
            })
    return {
        "vehicleContext": {key: vehicle.get(key) for key in ("brand", "model", "modelCode", "contextSource", "contextVersion")},
        "nsrSource": {"datasetVersion": str(nsr_source["datasetVersion"]), "fingerprint": str(nsr_source["fingerprint"])},
        "validationTargets": frozen_targets,
        "queryShards": shards,
        "controlQueries": {"vehicleRequired": True, "crossVehicleBorrowing": False, "nsrMutationAllowed": False},
    }


def build_query_plan(payload, org_id, edition):
    """Validate and freeze a tenant-scoped, versioned evidence query plan."""
    payload = payload if isinstance(payload, dict) else {}
    center_type = str(payload.get("centerType") or "").strip()
    if center_type not in ALLOWED_CENTERS:
        raise ValueError("centerType不受支持")
    project_id = str(payload.get("projectId") or "").strip()
    if not project_id:
        raise ValueError("projectId不能为空")
    subject = payload.get("subject") if isinstance(payload.get("subject"), dict) else {}
    brand = str(subject.get("brand") or "").strip()
    model = str(subject.get("model") or "").strip()
    if not (brand or model):
        raise ValueError("品牌或车型至少填写一个")
    aliases = _unique_strings(subject.get("aliases"), 20)
    competitors = _unique_strings(payload.get("competitors"), 10)
    themes = _unique_strings(payload.get("themes"))
    scenes = _unique_strings(payload.get("scenes"))
    issue_terms = _unique_strings(payload.get("issueTerms"))
    event_terms = _unique_strings(payload.get("eventTerms"))
    exclusions = _unique_strings(payload.get("exclusionTerms"))
    platforms = _unique_strings(payload.get("platforms"), 10)
    if not platforms or any(platform not in ALLOWED_PLATFORMS for platform in platforms):
        raise ValueError("platforms包含未支持平台或为空")
    window = payload.get("dateWindow") if isinstance(payload.get("dateWindow"), dict) else {}
    start = _safe_date(window.get("start"), "dateWindow.start")
    end = _safe_date(window.get("end"), "dateWindow.end")
    if datetime.fromisoformat(start.replace("Z", "+00:00")) > datetime.fromisoformat(end.replace("Z", "+00:00")):
        raise ValueError("dateWindow.start不能晚于end")
    sampling_input = payload.get("sampling") if isinstance(payload.get("sampling"), dict) else {}
    page_size = max(1, min(int(sampling_input.get("pageSize") or sampling_input.get("maxItemsPerPlatform") or 20), 100))
    sampling = {
        "maxPages": max(1, min(int(sampling_input.get("maxPages") or 1), 10)),
        "pageSize": page_size,
        "maxItemsPerPlatform": page_size,
        "maxCandidatesPerPlatform": max(1, min(int(sampling_input.get("maxCandidatesPerPlatform") or page_size), 500)),
        "maxEvidencePerTargetPerPlatform": max(1, min(int(sampling_input.get("maxEvidencePerTargetPerPlatform") or page_size), 100)),
        "commentDepth": max(0, min(int(sampling_input.get("commentDepth") or 0), 5)),
        "sourceRoleQuotas": sampling_input.get("sourceRoleQuotas") if isinstance(sampling_input.get("sourceRoleQuotas"), dict) else {},
    }
    budget_input = payload.get("budget") if isinstance(payload.get("budget"), dict) else {}
    budget = {
        "maxRequests": max(1, min(int(budget_input.get("maxRequests") or 100), 1000)),
        "maxEstimatedCost": max(0.0, float(budget_input.get("maxEstimatedCost") or 100)),
    }
    primary = model or brand
    nsr_contract = _nsr_validation_contract(payload, {"brand": brand, "model": model}, competitors) if center_type == "nsr_validation" else {}
    query_terms = [primary, *aliases]
    if center_type == "nsr_validation":
        queries = [row["query"] for row in nsr_contract["queryShards"]]
    else:
        for term in [*themes, *scenes, *issue_terms, *event_terms]:
            query_terms.append(f"{primary} {term}")
        if center_type == "brand_penetration":
            query_terms.extend([brand, *competitors])
            for competitor in competitors:
                query_terms.extend(f"{competitor} {term}" for term in themes[:8])
        queries = _unique_strings(query_terms, 60)
    plan = {
        "planId": f"se_plan_{uuid.uuid4().hex}",
        "schemaVersion": SCHEMA_VERSION,
        "planVersion": str(payload.get("planVersion") or ("v2.1" if center_type == "nsr_validation" else "v2.0")).strip(),
        "projectId": project_id,
        "orgId": str(org_id or "local").strip() or "local",
        "edition": "global" if edition == "global" else "china",
        "centerType": center_type,
        "subject": {"brand": brand, "model": model, "aliases": aliases},
        "competitors": competitors,
        "themes": themes,
        "scenes": scenes,
        "issueTerms": issue_terms,
        "eventTerms": event_terms,
        "exclusionTerms": exclusions,
        "platforms": platforms,
        "dateWindow": {"start": start, "end": end},
        "sampling": sampling,
        "budget": budget,
        "queries": queries,
        "createdAt": utcnow(),
        **nsr_contract,
    }
    plan["fingerprint"] = _stable_id(json.dumps({key: value for key, value in plan.items() if key not in {"planId", "createdAt", "fingerprint"}}, ensure_ascii=False, sort_keys=True))
    return plan


class BudgetExceeded(RuntimeError):
    pass


class TikHubEvidenceAdapter:
    """Internal supplier adapter; public marts never expose supplier identity."""

    def __init__(self, client=None):
        if client is None:
            from social_trends import TikHubClient
            client = TikHubClient()
        self.client = client

    @staticmethod
    def _search_range(window):
        try:
            start = datetime.fromisoformat(str(window["start"]).replace("Z", "+00:00"))
            end = datetime.fromisoformat(str(window["end"]).replace("Z", "+00:00"))
            days = max(1, (end.date() - start.date()).days + 1)
        except (KeyError, TypeError, ValueError):
            return "90d"
        return "1d" if days <= 1 else "3d" if days <= 3 else "7d" if days <= 7 else "30d" if days <= 30 else "90d"

    @staticmethod
    def _source_role(normalized):
        if normalized.get("matrixContent"):
            return "brand_or_matrix"
        author = str(normalized.get("author") or "").casefold()
        if any(token in author for token in ("官方", "品牌", "旗舰店")):
            return "brand_or_matrix"
        if any(token in author for token in ("媒体", "汽车网", "车评", "资讯")):
            return "media"
        return "user_or_unknown"

    def search(self, platform, query, page, count, time_range, cursor=""):
        from social_trends import PLATFORMS, _content_rows, _parse_import_date, douyin_next_cursor, normalize_item
        if platform not in PLATFORMS:
            raise ValueError(f"平台{platform}尚未启用真实采集适配器")
        payload, source = self.client.search(platform, query, page, count, self._search_range(time_range), cursor)
        fetched_at = utcnow()
        items = []
        for row in _content_rows(payload):
            normalized = normalize_item(platform, row, query, fetched_at)
            published = _parse_import_date(normalized.get("publishedAt"))
            items.append({
                "id": normalized["id"],
                "platformItemId": normalized["platformItemId"],
                "platform": platform,
                "sourceUrl": normalized["sourceUrl"],
                "text": normalized["text"],
                "author": normalized.get("author") or "",
                "publishedAt": published.isoformat() if published else "",
                "nativeMetrics": dict(normalized.get("metrics") or {}),
                "sourceRole": self._source_role(normalized),
                "coverUrl": normalized.get("coverUrl") or "",
                "dynamicCoverUrl": normalized.get("dynamicCoverUrl") or "",
            })
        return {
            "items": items,
            "nextCursor": douyin_next_cursor(payload) if platform == "douyin" else "",
            "requestMeta": {
                "endpoint": str(source.get("endpoint") or ""), "status": int(source.get("status") or 0),
                "cost": float(source.get("cost") or 0),
                "paginationMode": "cursor" if platform == "douyin" else "page",
            },
            "raw": payload,
        }


class SocialEvidenceRepository:
    """Single-writer SQLite repository, isolated from MMN's business database."""

    def __init__(self, db_path=None, raw_dir=None):
        self.db_path = Path(db_path or os.getenv("MMN_SOCIAL_EVIDENCE_DB", "data/social_evidence.sqlite"))
        self.raw_dir = Path(raw_dir or os.getenv("MMN_SOCIAL_EVIDENCE_RAW_DIR", "data/social_evidence_raw"))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.init_schema()

    def connect(self):
        conn = sqlite3.connect(str(self.db_path), timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init_schema(self):
        with self._lock, self.connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS query_plans (
                    plan_id TEXT PRIMARY KEY, org_id TEXT NOT NULL, edition TEXT NOT NULL,
                    project_id TEXT NOT NULL, center_type TEXT NOT NULL, fingerprint TEXT NOT NULL,
                    plan_json TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_se_plans_scope ON query_plans(org_id, edition, project_id, center_type, created_at DESC);
                CREATE TABLE IF NOT EXISTS evidence_jobs (
                    job_id TEXT PRIMARY KEY, plan_id TEXT NOT NULL, org_id TEXT NOT NULL, edition TEXT NOT NULL,
                    project_id TEXT NOT NULL, center_type TEXT NOT NULL, status TEXT NOT NULL, stage TEXT NOT NULL,
                    progress INTEGER NOT NULL DEFAULT 0, message TEXT NOT NULL DEFAULT '', retryable INTEGER NOT NULL DEFAULT 0,
                    request_count INTEGER NOT NULL DEFAULT 0, actual_cost REAL NOT NULL DEFAULT 0,
                    result_json TEXT, error TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    FOREIGN KEY(plan_id) REFERENCES query_plans(plan_id)
                );
                CREATE INDEX IF NOT EXISTS idx_se_jobs_scope ON evidence_jobs(org_id, edition, project_id, center_type, created_at DESC);
                CREATE TABLE IF NOT EXISTS raw_requests (
                    request_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, org_id TEXT NOT NULL, platform TEXT NOT NULL,
                    endpoint TEXT NOT NULL, params_hash TEXT NOT NULL, response_path TEXT NOT NULL, response_hash TEXT NOT NULL,
                    status INTEGER, item_count INTEGER NOT NULL DEFAULT 0, cost REAL NOT NULL DEFAULT 0,
                    fetched_at TEXT NOT NULL, cache_hit INTEGER NOT NULL DEFAULT 0,
                    FOREIGN KEY(job_id) REFERENCES evidence_jobs(job_id)
                );
                CREATE TABLE IF NOT EXISTS canonical_contents (
                    canonical_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, org_id TEXT NOT NULL, edition TEXT NOT NULL,
                    platform TEXT NOT NULL, platform_item_id TEXT NOT NULL, source_url TEXT NOT NULL,
                    content_fingerprint TEXT NOT NULL, content_json TEXT NOT NULL, collected_at TEXT NOT NULL,
                    UNIQUE(org_id, edition, platform, platform_item_id, content_fingerprint)
                );
                CREATE INDEX IF NOT EXISTS idx_se_content_job ON canonical_contents(job_id, org_id);
                CREATE TABLE IF NOT EXISTS job_contents (
                    job_id TEXT NOT NULL, canonical_id TEXT NOT NULL, raw_request_id TEXT NOT NULL,
                    PRIMARY KEY(job_id, canonical_id),
                    FOREIGN KEY(job_id) REFERENCES evidence_jobs(job_id),
                    FOREIGN KEY(canonical_id) REFERENCES canonical_contents(canonical_id)
                );
                CREATE TABLE IF NOT EXISTS evidence_marts (
                    mart_id TEXT PRIMARY KEY, job_id TEXT NOT NULL, org_id TEXT NOT NULL, edition TEXT NOT NULL,
                    project_id TEXT NOT NULL, mart_type TEXT NOT NULL, schema_version TEXT NOT NULL,
                    mart_json TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_se_mart_scope ON evidence_marts(org_id, edition, project_id, mart_type, created_at DESC);
            """)

    def create_plan(self, plan):
        with self._lock, self.connect() as conn:
            conn.execute("INSERT INTO query_plans VALUES(?,?,?,?,?,?,?,?)", (
                plan["planId"], plan["orgId"], plan["edition"], plan["projectId"], plan["centerType"],
                plan["fingerprint"], json.dumps(plan, ensure_ascii=False), plan["createdAt"],
            ))
        return plan

    def get_plan(self, plan_id, org_id):
        with self.connect() as conn:
            row = conn.execute("SELECT plan_json FROM query_plans WHERE plan_id=? AND org_id=?", (plan_id, org_id)).fetchone()
        return json.loads(row[0]) if row else None

    def create_job(self, plan):
        now, job_id = utcnow(), f"se_job_{uuid.uuid4().hex}"
        with self._lock, self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            placeholders = ",".join("?" for _ in ACTIVE_STATUSES)
            existing = conn.execute(
                f"""SELECT j.* FROM evidence_jobs j JOIN query_plans p ON p.plan_id=j.plan_id
                    WHERE j.org_id=? AND p.fingerprint=? AND j.status IN ({placeholders})
                    ORDER BY j.created_at DESC LIMIT 1""",
                (plan["orgId"], plan["fingerprint"], *sorted(ACTIVE_STATUSES)),
            ).fetchone()
            if existing:
                conn.commit()
                return self._job(existing)
            conn.execute("INSERT INTO query_plans VALUES(?,?,?,?,?,?,?,?)", (
                plan["planId"], plan["orgId"], plan["edition"], plan["projectId"], plan["centerType"],
                plan["fingerprint"], json.dumps(plan, ensure_ascii=False), plan["createdAt"],
            ))
            conn.execute("""INSERT INTO evidence_jobs
                (job_id,plan_id,org_id,edition,project_id,center_type,status,stage,progress,message,retryable,created_at,updated_at)
                VALUES(?,?,?,?,?,?,'queued','queued',0,?,0,?,?)""", (
                job_id, plan["planId"], plan["orgId"], plan["edition"], plan["projectId"], plan["centerType"], "任务已进入持久化队列", now, now,
            ))
            conn.commit()
        return self.get_job(job_id, plan["orgId"])

    def claim_next_job(self):
        """Atomically claim one queued job for an external single-writer worker."""
        with self._lock, self.connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT job_id,org_id FROM evidence_jobs WHERE status='queued' ORDER BY created_at LIMIT 1"
            ).fetchone()
            if not row:
                conn.commit()
                return None
            changed = conn.execute(
                """UPDATE evidence_jobs SET status='planning',stage='planning',progress=1,
                message='Worker已领取任务',updated_at=? WHERE job_id=? AND status='queued'""",
                (utcnow(), row["job_id"]),
            ).rowcount
            conn.commit()
        return self.get_job(row["job_id"], row["org_id"]) if changed else None

    @staticmethod
    def _job(row):
        if not row:
            return None
        result = dict(row)
        result["jobId"], result["planId"] = result.pop("job_id"), result.pop("plan_id")
        for source, target in (("org_id", "orgId"), ("project_id", "projectId"), ("center_type", "centerType"), ("request_count", "requestCount"), ("actual_cost", "actualCost"), ("created_at", "createdAt"), ("updated_at", "updatedAt")):
            result[target] = result.pop(source)
        result["retryable"] = bool(result["retryable"])
        result["result"] = json.loads(result.pop("result_json")) if result.get("result_json") else None
        return result

    def get_job(self, job_id, org_id):
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM evidence_jobs WHERE job_id=? AND org_id=?", (job_id, org_id)).fetchone()
        return self._job(row)

    def latest_job(self, project_id, org_id, edition, center_type):
        with self.connect() as conn:
            row = conn.execute(
                """SELECT * FROM evidence_jobs WHERE project_id=? AND org_id=? AND edition=? AND center_type=?
                   ORDER BY created_at DESC LIMIT 1""", (project_id, org_id, edition, center_type),
            ).fetchone()
        return self._job(row)

    def update_job(self, job_id, org_id, **fields):
        mapping = {"requestCount": "request_count", "actualCost": "actual_cost", "result": "result_json"}
        allowed = {"status", "stage", "progress", "message", "retryable", "requestCount", "actualCost", "result", "error"}
        values, params = [], []
        for key, value in fields.items():
            if key not in allowed:
                continue
            column = mapping.get(key, key)
            if key == "result":
                value = json.dumps(value, ensure_ascii=False) if value is not None else None
            if key == "retryable":
                value = int(bool(value))
            values.append(f"{column}=?")
            params.append(value)
        values.append("updated_at=?")
        params.extend([utcnow(), job_id, org_id])
        with self._lock, self.connect() as conn:
            conn.execute(f"UPDATE evidence_jobs SET {','.join(values)} WHERE job_id=? AND org_id=?", params)
        return self.get_job(job_id, org_id)

    def recover_interrupted_jobs(self):
        placeholders = ",".join("?" for _ in INTERRUPTED_STATUSES)
        with self._lock, self.connect() as conn:
            cursor = conn.execute(f"""UPDATE evidence_jobs SET status='degraded',stage='recovery',retryable=1,
                message='服务重启中断任务；已保留现有证据，可从失败阶段重试',updated_at=?
                WHERE status IN ({placeholders})""", (utcnow(), *sorted(INTERRUPTED_STATUSES)))
            return cursor.rowcount

    def active_job_count(self):
        placeholders = ",".join("?" for _ in ACTIVE_STATUSES)
        with self.connect() as conn:
            return int(conn.execute(
                f"SELECT count(*) FROM evidence_jobs WHERE status IN ({placeholders})",
                tuple(sorted(ACTIVE_STATUSES)),
            ).fetchone()[0])

    def org_cost_since(self, org_id, since):
        with self.connect() as conn:
            return float(conn.execute(
                "SELECT coalesce(sum(actual_cost),0) FROM evidence_jobs WHERE org_id=? AND updated_at>=?",
                (org_id, since),
            ).fetchone()[0])

    @staticmethod
    def _sanitize(value):
        if isinstance(value, dict):
            return {key: SocialEvidenceRepository._sanitize(item) for key, item in value.items() if not SENSITIVE_KEYS.search(str(key))}
        if isinstance(value, list):
            return [SocialEvidenceRepository._sanitize(item) for item in value]
        return value

    @staticmethod
    def request_cache_key(plan, platform, query, page, cursor=""):
        return _stable_id(json.dumps({
            "edition": plan["edition"], "platform": platform, "query": query, "page": page,
            "cursor": cursor, "dateWindow": plan["dateWindow"],
            "count": plan["sampling"]["maxItemsPerPlatform"],
        }, ensure_ascii=False, sort_keys=True))

    def find_cached_response(self, org_id, platform, params_hash, ttl_hours=24):
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=max(0, ttl_hours))).isoformat()
        with self.connect() as conn:
            row = conn.execute("""SELECT response_path FROM raw_requests
                WHERE org_id=? AND platform=? AND params_hash=? AND fetched_at>=?
                ORDER BY fetched_at DESC LIMIT 1""", (org_id, platform, params_hash, cutoff)).fetchone()
        if not row:
            return None
        try:
            payload = json.loads(Path(row["response_path"]).read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            return None
        if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
            return None
        meta = dict(payload.get("requestMeta") or {})
        meta.update({"cacheHit": True, "cost": 0})
        return {**payload, "requestMeta": meta}

    def save_raw_request(self, job, platform, query, page, response, params_hash=None):
        request_id, fetched_at = f"se_req_{uuid.uuid4().hex}", utcnow()
        safe = self._sanitize({
            "raw": response.get("raw") or {}, "items": response.get("items") or [],
            "nextCursor": response.get("nextCursor") or "", "requestMeta": response.get("requestMeta") or {},
        })
        text = json.dumps(safe, ensure_ascii=False, sort_keys=True)
        scope = self.raw_dir / _stable_id(job["orgId"])[:12] / job["edition"] / job["jobId"]
        scope.mkdir(parents=True, exist_ok=True)
        path = scope / f"{request_id}.json"
        path.write_text(text, encoding="utf-8")
        meta = response.get("requestMeta") or {}
        with self._lock, self.connect() as conn:
            conn.execute("INSERT INTO raw_requests VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                request_id, job["jobId"], job["orgId"], platform, str(meta.get("endpoint") or ""),
                params_hash or _stable_id(platform, query, page), str(path), hashlib.sha256(text.encode("utf-8")).hexdigest(),
                int(meta.get("status") or 0), len(response.get("items") or []), float(meta.get("cost") or 0), fetched_at, int(bool(meta.get("cacheHit"))),
            ))
        return request_id

    def upsert_content(self, job, item, raw_request_id):
        platform = str(item.get("platform") or "").strip()
        platform_item_id = str(item.get("platformItemId") or item.get("id") or "").strip()
        text = str(item.get("text") or "").strip()
        fingerprint = _stable_id(platform, text)
        canonical_id = _stable_id(job["orgId"], job["edition"], platform, platform_item_id, fingerprint)
        content = {**item, "canonicalContentId": canonical_id, "contentFingerprint": fingerprint,
                   "rawRecordIds": [raw_request_id], "collectedAt": utcnow(), "verificationStatus": "platform_observation"}
        with self._lock, self.connect() as conn:
            conn.execute("""INSERT OR IGNORE INTO canonical_contents
                (canonical_id,job_id,org_id,edition,platform,platform_item_id,source_url,content_fingerprint,content_json,collected_at)
                VALUES(?,?,?,?,?,?,?,?,?,?)""", (
                canonical_id, job["jobId"], job["orgId"], job["edition"], platform, platform_item_id,
                item.get("sourceUrl") or "", fingerprint, json.dumps(content, ensure_ascii=False), utcnow(),
            ))
            conn.execute("INSERT OR IGNORE INTO job_contents VALUES(?,?,?)", (job["jobId"], canonical_id, raw_request_id))
        return content

    def list_contents(self, job_id, org_id):
        with self.connect() as conn:
            rows = conn.execute("""SELECT c.content_json FROM canonical_contents c
                JOIN job_contents j ON j.canonical_id=c.canonical_id
                WHERE j.job_id=? AND c.org_id=? ORDER BY c.collected_at""", (job_id, org_id)).fetchall()
        return [json.loads(row[0]) for row in rows]

    def save_mart(self, job, mart):
        mart_id, created_at = f"se_mart_{uuid.uuid4().hex}", utcnow()
        mart = {**mart, "martId": mart_id, "jobId": job["jobId"], "createdAt": created_at}
        with self._lock, self.connect() as conn:
            conn.execute("INSERT INTO evidence_marts VALUES(?,?,?,?,?,?,?,?,?)", (
                mart_id, job["jobId"], job["orgId"], job["edition"], job["projectId"], mart["martType"],
                mart["schemaVersion"], json.dumps(mart, ensure_ascii=False), created_at,
            ))
        return mart

    def latest_mart(self, project_id, org_id, edition, mart_type):
        with self.connect() as conn:
            row = conn.execute("""SELECT mart_json FROM evidence_marts
                WHERE project_id=? AND org_id=? AND edition=? AND mart_type=? ORDER BY created_at DESC LIMIT 1""",
                (project_id, org_id, edition, mart_type)).fetchone()
        return json.loads(row[0]) if row else None

    def get_mart(self, mart_id, org_id):
        with self.connect() as conn:
            row = conn.execute(
                "SELECT mart_json FROM evidence_marts WHERE mart_id=? AND org_id=?", (mart_id, org_id),
            ).fetchone()
        return json.loads(row[0]) if row else None


def _valid_public_url(value):
    parsed = urlparse(str(value or ""))
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _within_date_window(value, window):
    try:
        observed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
        start_text, end_text = str(window["start"]), str(window["end"])
        start = datetime.fromisoformat(start_text.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_text.replace("Z", "+00:00"))
        if observed.tzinfo is None:
            observed = observed.replace(tzinfo=SHANGHAI_TZ)
        if start.tzinfo is None:
            start = start.replace(tzinfo=SHANGHAI_TZ)
        if end.tzinfo is None:
            end = end.replace(tzinfo=SHANGHAI_TZ)
        end_exclusive = end + timedelta(days=1) if "T" not in end_text else end
        return start <= observed < end_exclusive
    except (KeyError, TypeError, ValueError):
        return False


def _platform_observations(items):
    observations = []
    for platform in sorted({item["platform"] for item in items}):
        rows = [item for item in items if item["platform"] == platform]
        observations.append({"platform": platform, "contentCount": len(rows), "nativeMetricCoverage": sorted({key for row in rows for key in (row.get("nativeMetrics") or {})})})
    return observations


def apply_evidence_sampling(items, plan):
    """Build a deterministic, platform-balanced task evidence set."""
    per_platform = int(plan["sampling"].get(
        "maxCandidatesPerPlatform" if plan.get("centerType") == "nsr_validation" else "maxItemsPerPlatform",
        plan["sampling"]["maxItemsPerPlatform"],
    ))
    quotas = {str(role): max(0, int(limit)) for role, limit in (plan["sampling"].get("sourceRoleQuotas") or {}).items()}
    sampled, role_counts = [], {}
    for platform in plan["platforms"]:
        platform_rows = [item for item in items if item.get("platform") == platform]
        accepted = []
        for item in platform_rows:
            role = str(item.get("sourceRole") or "unknown")
            if role in quotas and role_counts.get(role, 0) >= quotas[role]:
                continue
            accepted.append(item)
            role_counts[role] = role_counts.get(role, 0) + 1
            if len(accepted) >= per_platform:
                break
        sampled.extend(accepted)
    return sampled


def build_social_trend_mart(plan, items, previous=None):
    quotes = [{"text": item["text"][:180], "evidenceId": item["canonicalContentId"], "platform": item["platform"],
               "sourceUrl": item.get("sourceUrl") or "", "nativeMetrics": item.get("nativeMetrics") or {}} for item in items[:12]]
    return {
        "martType": "social_trend", "schemaVersion": "social-trend-mart-v2",
        "projectId": plan["projectId"], "subject": plan["subject"],
        "queryScope": {"planVersion": plan["planVersion"], "dateWindow": plan["dateWindow"], "platforms": plan["platforms"]},
        "coverage": {"contentCount": len(items), "platforms": _platform_observations(items), "missingPlatforms": [p for p in plan["platforms"] if p not in {i["platform"] for i in items}]},
        "changeSignals": [{"statementType": "fact", "label": "本周期公开讨论变化", "contentCount": len(items),
                           "previousContentCount": previous.get("coverage", {}).get("contentCount") if previous else None,
                           "delta": len(items) - int(previous.get("coverage", {}).get("contentCount") or 0) if previous else None,
                           "comparisonStatus": "comparable" if previous else "first_baseline",
                           "evidenceIds": [item["canonicalContentId"] for item in items[:20]]}],
        "userLanguage": quotes,
        "competitorOccupancy": [{"competitor": competitor, "mentionCount": sum(competitor.casefold() in item["text"].casefold() for item in items)} for competitor in plan["competitors"]],
        "limitations": ["公开平台传播证据不能单独证明市场需求、购买意愿或成交因果", "平台原生互动指标保留各自口径，不直接跨平台相加"],
        "status": "verified" if items else "limited",
    }


def build_brand_penetration_mart(plan, items, previous=None):
    brand = plan["subject"].get("brand") or plan["subject"].get("model")
    terms = [*plan["themes"], *plan["scenes"], *plan["issueTerms"]]
    source_mix = {}
    for item in items:
        role = item.get("sourceRole") or "unknown"
        source_mix[role] = source_mix.get(role, 0) + 1
    associations = [{"term": term, "mentionCount": sum(term.casefold() in item["text"].casefold() for item in items), "evidenceIds": [item["canonicalContentId"] for item in items if term.casefold() in item["text"].casefold()][:10]} for term in terms]
    previous_associations = {row.get("term"): int(row.get("mentionCount") or 0) for row in (previous or {}).get("brandAssociations", [])}
    for association in associations:
        association["previousMentionCount"] = previous_associations.get(association["term"]) if previous else None
        association["delta"] = association["mentionCount"] - previous_associations.get(association["term"], 0) if previous else None
    return {
        "martType": "brand_penetration", "schemaVersion": "brand-penetration-mart-v2",
        "projectId": plan["projectId"], "brand": brand,
        "queryScope": {"planVersion": plan["planVersion"], "dateWindow": plan["dateWindow"], "platforms": plan["platforms"]},
        "coverage": {"contentCount": len(items), "platforms": _platform_observations(items), "missingPlatforms": [p for p in plan["platforms"] if p not in {i["platform"] for i in items}]},
        "brandAssociations": associations,
        "sourceRoleMix": [{"role": role, "contentCount": count} for role, count in sorted(source_mix.items())],
        "representativeEvidence": [{
            "text": item["text"][:180], "evidenceId": item["canonicalContentId"],
            "platform": item["platform"], "sourceUrl": item.get("sourceUrl") or "",
            "sourceRole": item.get("sourceRole") or "unknown", "nativeMetrics": item.get("nativeMetrics") or {},
        } for item in items[:18]],
        "competitorObservations": [{"competitor": competitor, "mentionCount": sum(competitor.casefold() in item["text"].casefold() for item in items)} for competitor in plan["competitors"]],
        "boundary": {"scope": "limited public social evidence; not market penetration or sales causality", "statementType": "fact"},
        "status": "verified" if items else "limited",
    }


def build_nsr_validation_mart(plan, items, previous=None):
    """Build an independent public-discussion validation set; never mutate the NSR baseline."""
    model_terms = _unique_strings([plan["subject"].get("model"), *plan["subject"].get("aliases", [])], 20)
    model_terms = [term.casefold() for term in model_terms]
    per_target_platform = int(plan["sampling"]["maxEvidencePerTargetPerPlatform"])
    validations = []
    for target in plan["validationTargets"]:
        terms = target["queryTerms"]
        # A positive/negative word establishes stance, not attribute identity.  Requiring
        # an attribute-specific term prevents generic posts such as "吐槽这台车" from
        # being copied into every selected NSR label.
        attribute_terms = _unique_strings([target["label"], *terms["canonical"], *terms["userLanguage"],
                                           *terms["scenes"], *terms["comparison"]], 60)
        support_terms = [term.casefold() for term in terms["support"]]
        challenge_terms = [term.casefold() for term in terms["challenge"]]
        evidence, stance_counts = [], {"supporting": 0, "challenging": 0, "mixed": 0, "neutral": 0}
        for platform in plan["platforms"]:
            accepted = 0
            for item in items:
                text = str(item.get("text") or "")
                folded = text.casefold()
                if item.get("platform") != platform or not any(term in folded for term in model_terms):
                    continue
                matched_terms = [term for term in attribute_terms if term.casefold() in folded]
                if not matched_terms:
                    continue
                supports = any(term in folded for term in support_terms)
                challenges = any(term in folded for term in challenge_terms)
                stance = "mixed" if supports and challenges else "supporting" if supports else "challenging" if challenges else "neutral"
                stance_counts[stance] += 1
                evidence.append({
                    "evidenceId": item["canonicalContentId"], "platform": platform,
                    "sourceUrl": item.get("sourceUrl") or "", "publishedAt": item.get("publishedAt") or "",
                    "text": text[:240], "matchedTerms": matched_terms, "stance": stance,
                    "nativeMetrics": item.get("nativeMetrics") or {},
                })
                accepted += 1
                if accepted >= per_target_platform:
                    break
        validations.append({
            "targetId": target["targetId"], "attributeId": target["attributeId"],
            "label": target["label"], "baselineNsr": target["baselineNsr"],
            "verdict": "pending_adjudication" if evidence else "insufficient_evidence",
            "evidenceCount": len(evidence), "stanceCounts": stance_counts, "evidence": evidence,
        })
    return {
        "martType": "nsr_validation", "schemaVersion": "nsr-validation-mart-v1",
        "projectId": plan["projectId"], "vehicleContext": plan["vehicleContext"],
        "nsrSource": plan["nsrSource"], "queryPlanFingerprint": plan["fingerprint"],
        "queryScope": {"planVersion": plan["planVersion"], "dateWindow": plan["dateWindow"], "platforms": plan["platforms"]},
        "coverage": {"contentCount": len(items), "platforms": _platform_observations(items),
                     "missingPlatforms": [p for p in plan["platforms"] if p not in {i["platform"] for i in items}]},
        "targetValidations": validations,
        "controlObservations": [{
            "competitor": competitor,
            "mentionCount": sum(competitor.casefold() in str(item.get("text") or "").casefold() for item in items),
        } for competitor in plan["competitors"]],
        "adjudication": {"required": True, "status": "pending"},
        "boundary": {
            "scope": "public social discussion validation only; not NSR recalculation, market demand, or sales causality",
            "nsrMutationAllowed": False,
        },
        "status": "pending_adjudication" if any(row["evidenceCount"] for row in validations) else "limited",
    }


class SocialEvidenceService:
    def __init__(self, repository):
        self.repository = repository

    def create_job(self, plan):
        return self.repository.create_job(plan)

    def run_job(self, job_id, org_id, adapter, brand_analysis_runner=None):
        job = self.repository.get_job(job_id, org_id)
        if not job:
            raise KeyError("任务不存在或无权访问")
        plan = self.repository.get_plan(job["planId"], org_id)
        planned_requests = len(plan["platforms"]) * len(plan["queries"]) * plan["sampling"]["maxPages"]
        estimated_unit_cost = max(0.0, float(os.getenv("MMN_SOCIAL_EVIDENCE_ESTIMATED_UNIT_COST", "1")))
        estimated_cost = planned_requests * estimated_unit_cost
        daily_limit = max(0.0, float(os.getenv("MMN_SOCIAL_EVIDENCE_ORG_DAILY_COST_LIMIT", "500")))
        day_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        org_cost = self.repository.org_cost_since(org_id, day_start)
        if (planned_requests > plan["budget"]["maxRequests"] or estimated_cost > plan["budget"]["maxEstimatedCost"]
                or org_cost + estimated_cost > daily_limit):
            self.repository.update_job(job_id, org_id, status="manual_required", stage="budget_check", progress=0, retryable=True,
                                       message=f"预计{planned_requests}次请求、成本单位{estimated_cost:g}，超过任务或企业日预算")
            raise BudgetExceeded("查询计划超过任务预算")
        self.repository.update_job(job_id, org_id, status="running", stage="collecting_discovery", progress=5, message="正在采集公开平台证据")
        request_count, actual_cost = 0, 0.0
        exclusions = [term.casefold() for term in plan["exclusionTerms"]]
        collection_coverage = {platform: {
            "platform": platform, "pagesVisited": 0, "rawCandidateCount": 0,
            "effectiveCount": 0, "earliestPublishedAt": "", "latestPublishedAt": "",
            "stopReason": "not_started",
        } for platform in plan["platforms"]}
        platform_failures = []
        try:
            for platform in plan["platforms"]:
                stats, platform_candidates, hit_page_limit = collection_coverage[platform], 0, False
                try:
                    for query in plan["queries"]:
                        cursor = ""
                        for page in range(1, plan["sampling"]["maxPages"] + 1):
                            cache_key = self.repository.request_cache_key(plan, platform, query, page, cursor)
                            response = self.repository.find_cached_response(job["orgId"], platform, cache_key)
                            if response is None:
                                response = adapter.search(platform, query, page, plan["sampling"]["pageSize"], plan["dateWindow"], cursor)
                                request_count += 1
                                actual_cost += float((response.get("requestMeta") or {}).get("cost") or 0)
                                if actual_cost > plan["budget"]["maxEstimatedCost"] or org_cost + actual_cost > daily_limit:
                                    self.repository.update_job(job_id, org_id, status="manual_required", stage="budget_check", progress=0,
                                                               retryable=True, requestCount=request_count, actualCost=actual_cost,
                                                               message="实际采集成本已达到任务或企业日预算，任务已停止")
                                    raise BudgetExceeded("实际采集成本超过预算")
                            raw_id = self.repository.save_raw_request(job, platform, query, page, response, cache_key)
                            candidates = response.get("items") or []
                            stats["pagesVisited"] += 1
                            stats["rawCandidateCount"] += len(candidates)
                            for candidate in candidates:
                                if platform_candidates >= plan["sampling"]["maxCandidatesPerPlatform"]:
                                    break
                                platform_candidates += 1
                                text = str(candidate.get("text") or "").strip()
                                source_url = str(candidate.get("sourceUrl") or "").strip()
                                if (not text or not _valid_public_url(source_url)
                                        or not _within_date_window(candidate.get("publishedAt"), plan["dateWindow"])
                                        or any(term in text.casefold() for term in exclusions)):
                                    continue
                                published_at = str(candidate.get("publishedAt") or "")
                                if published_at:
                                    stats["earliestPublishedAt"] = min(filter(None, [stats["earliestPublishedAt"], published_at]))
                                    stats["latestPublishedAt"] = max(stats["latestPublishedAt"], published_at)
                                item = {**candidate, "platform": platform, "sourceUrl": source_url,
                                        "platformItemId": str(candidate.get("platformItemId") or candidate.get("id") or _stable_id(text))}
                                self.repository.upsert_content(job, item, raw_id)
                            if platform_candidates >= plan["sampling"]["maxCandidatesPerPlatform"]:
                                stats["stopReason"] = "candidate_limit"
                                break
                            cursor = str(response.get("nextCursor") or "")
                            pagination_mode = str((response.get("requestMeta") or {}).get("paginationMode") or "cursor")
                            if pagination_mode == "cursor" and not cursor:
                                stats["stopReason"] = "source_exhausted"
                                break
                            if pagination_mode == "none" or (pagination_mode == "page" and not candidates):
                                stats["stopReason"] = "source_exhausted"
                                break
                            if page == plan["sampling"]["maxPages"] and candidates:
                                hit_page_limit = True
                        if platform_candidates >= plan["sampling"]["maxCandidatesPerPlatform"]:
                            break
                    if stats["stopReason"] == "not_started":
                        stats["stopReason"] = "partial_page_limit" if hit_page_limit else "source_exhausted"
                except BudgetExceeded:
                    raise
                except Exception:
                    stats["stopReason"] = "platform_unavailable"
                    platform_failures.append(platform)
            self.repository.update_job(job_id, org_id, status="running", stage="building_evidence", progress=80,
                                       requestCount=request_count, actualCost=actual_cost, message="正在构建任务专属证据集")
            items = self.repository.list_contents(job_id, org_id)
            items = apply_evidence_sampling(items, plan)
            previous = self.repository.latest_mart(plan["projectId"], org_id, plan["edition"], plan["centerType"])
            if plan["centerType"] == "social_trend":
                mart = build_social_trend_mart(plan, items, previous)
            elif plan["centerType"] == "brand_penetration":
                mart = build_brand_penetration_mart(plan, items, previous)
                if brand_analysis_runner:
                    self.repository.update_job(
                        job_id, org_id, status="running", stage="validating", progress=88,
                        message="正在生成品牌与逐竞品交叉验证结论",
                    )
                    mart["brandDecision"] = brand_analysis_runner(plan, items)
                    mart["schemaVersion"] = "brand-penetration-mart-v3"
            else:
                mart = build_nsr_validation_mart(plan, items, previous)
            for platform, stats in collection_coverage.items():
                stats["effectiveCount"] = sum(item.get("platform") == platform for item in items)
            mart["collectionCoverage"] = list(collection_coverage.values())
            if platform_failures:
                mart["coverageStatus"] = "partial_platform_failure"
            elif any(row["stopReason"] == "partial_page_limit" for row in collection_coverage.values()):
                mart["coverageStatus"] = "partial_page_limit"
            else:
                mart["coverageStatus"] = "bounded_complete"
            mart = self.repository.save_mart(job, mart)
            decision_status = ((mart.get("brandDecision") or {}).get("validation") or {}).get("status")
            final_status = ("degraded" if platform_failures or not items else
                            "manual_required" if decision_status and decision_status != "aligned" else "ready")
            message = ("部分平台暂不可用，已保留其余证据" if platform_failures else
                       "证据集已就绪，品牌结论等待人工复核" if final_status == "manual_required" else
                       "证据集与品牌结论已就绪" if items and decision_status == "aligned" else
                       "证据集已就绪" if items else "未取得符合准入规则的公开证据")
            return self.repository.update_job(job_id, org_id, status=final_status, stage="ready" if items else "admission",
                                              progress=100, retryable=bool(platform_failures) or not bool(items), requestCount=request_count,
                                              actualCost=actual_cost, result={"martId": mart["martId"]}, message=message) | {"mart": mart}
        except BudgetExceeded:
            raise
        except Exception as exc:
            self.repository.update_job(job_id, org_id, status="degraded", stage="recovery", retryable=True,
                                       requestCount=request_count, actualCost=actual_cost,
                                       message="外部证据采集未完成，已保留成功部分", error=str(exc)[:500])
            raise
