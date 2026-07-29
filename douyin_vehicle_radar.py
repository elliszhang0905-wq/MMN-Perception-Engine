from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable


SUPPORTED_RANGES = {7, 14, 30}
STAGES = (
    ("preparing", 8, "正在准备车型与检索口径"),
    ("searching", 25, "正在检索本品与竞品内容"),
    ("filtering", 43, "正在按车型与时间窗口过滤"),
    ("verifying", 56, "正在核验车型命中证据"),
    ("deduplicating", 66, "正在合并重复内容"),
    ("enriching_metrics", 82, "正在核验播放热度"),
    ("ranking", 94, "正在生成正式榜单"),
)
METRIC_CACHE_MINUTES = 30
MAX_METRIC_ITEMS = 100
METRIC_BATCH_SIZE = 50
MAX_METRIC_SPLIT_RETRIES = 8


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_range(value: Any) -> int:
    try:
        days = int(value)
    except (TypeError, ValueError):
        raise ValueError("时间范围仅支持 7、14、30 天。")
    if days not in SUPPORTED_RANGES:
        raise ValueError("时间范围仅支持 7、14、30 天。")
    return days


def normalize_text(value: Any) -> str:
    return re.sub(r"[\s·•_—\-–/｜|]+", "", str(value or "")).casefold()


def clean_models(values: Iterable[Any], *, exclude: str = "") -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    excluded = normalize_text(exclude)
    for value in values or []:
        model = str(value or "").strip()
        key = normalize_text(model)
        if not model or not key or key == excluded or key in seen:
            continue
        seen.add(key)
        result.append(model)
    return result[:8]


def model_aliases(model: str) -> dict[str, list[str]]:
    canonical = str(model or "").strip()
    if not canonical:
        return {"canonical": [], "short": []}
    compact = re.sub(r"\s+", "", canonical)
    short: list[str] = []
    latin_number = re.findall(r"[A-Za-z]+\s*\d+[A-Za-z0-9-]*", compact)
    for value in latin_number:
        alias = re.sub(r"\s+", "", value)
        if normalize_text(alias) != normalize_text(canonical):
            short.append(alias)
    return {
        "canonical": [canonical],
        "short": list(dict.fromkeys(short)),
    }


def build_profiles(subject: str, competitors: Iterable[str]) -> list[dict[str, Any]]:
    subject = str(subject or "").strip()
    if not subject:
        raise ValueError("缺少本品车型。")
    models = [subject, *clean_models(competitors, exclude=subject)]
    return [
        {
            "model": model,
            "kind": "own" if index == 0 else "competitor",
            "aliases": model_aliases(model),
        }
        for index, model in enumerate(models)
    ]


def build_queries(
    subject: str,
    competitors: Iterable[str],
    topics: Iterable[str] = (),
    *,
    max_queries: int = 16,
) -> list[dict[str, str]]:
    profiles = build_profiles(subject, competitors)
    queries: list[dict[str, str]] = []
    for profile in profiles:
        model = profile["model"]
        queries.append({"query": model, "target": model, "kind": profile["kind"]})
        queries.append({"query": f"{model} 测评", "target": model, "kind": profile["kind"]})
    for competitor in clean_models(competitors, exclude=subject):
        queries.append({"query": f"{subject} {competitor}", "target": competitor, "kind": "comparison"})
    for topic in list(dict.fromkeys(str(item or "").strip() for item in topics if str(item or "").strip()))[:4]:
        queries.append({"query": f"{subject} {topic}", "target": subject, "kind": "attribute"})
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in queries:
        key = normalize_text(item["query"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped[: max(1, min(int(max_queries or 16), 24))]


def date_window(days: int, *, now_value: datetime | None = None) -> dict[str, str]:
    days = normalize_range(days)
    end = now_value or datetime.now(timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    start = end - timedelta(days=days)
    return {"start": start.isoformat(), "end": end.isoformat(), "days": days}


def parse_datetime(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        if re.fullmatch(r"\d{10}(?:\.\d+)?", text):
            return datetime.fromtimestamp(float(text), tz=timezone.utc)
        if re.fullmatch(r"\d{13}", text):
            return datetime.fromtimestamp(float(text) / 1000, tz=timezone.utc)
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (ValueError, OverflowError):
        return None


def optional_metric(metrics: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = metrics.get(key)
        if value is None or value == "":
            continue
        try:
            number = float(value)
        except (TypeError, ValueError):
            continue
        if number >= 0:
            return number
    return None


def metric(metrics: dict[str, Any], *keys: str) -> float:
    return optional_metric(metrics, *keys) or 0.0


def item_metrics(item: dict[str, Any]) -> dict[str, float | None]:
    native = dict(item.get("nativeMetrics") or item.get("metrics") or {})
    return {
        "views": optional_metric(native, "views", "play_count", "playCount", "view_count"),
        "likes": metric(native, "likes", "digg_count", "diggCount"),
        "comments": metric(native, "comments", "comment_count", "commentCount"),
        "shares": metric(native, "shares", "share_count", "shareCount"),
        "collects": metric(native, "collects", "collect_count", "collectCount"),
    }


def classify_candidate(
    item: dict[str, Any],
    profiles: list[dict[str, Any]],
    topics: Iterable[str],
    window: dict[str, Any],
) -> dict[str, Any]:
    published = parse_datetime(item.get("publishedAt"))
    if not published:
        return {"eligible": False, "reason": "missing_published_at"}
    start = parse_datetime(window.get("start"))
    end = parse_datetime(window.get("end"))
    if not start or not end or published < start or published > end:
        return {"eligible": False, "reason": "outside_window"}

    text = str(item.get("text") or "")
    normalized = normalize_text(text)
    exact_matches: list[dict[str, Any]] = []
    short_matches: list[dict[str, Any]] = []
    evidence: list[dict[str, str]] = []
    for profile in profiles:
        for alias in profile["aliases"]["canonical"]:
            if normalize_text(alias) and normalize_text(alias) in normalized:
                exact_matches.append(profile)
                evidence.append({"model": profile["model"], "alias": alias, "strength": "exact"})
                break
        else:
            for alias in profile["aliases"]["short"]:
                if normalize_text(alias) and normalize_text(alias) in normalized:
                    short_matches.append(profile)
                    evidence.append({"model": profile["model"], "alias": alias, "strength": "short"})
                    break

    matches = exact_matches or short_matches
    if not matches:
        return {"eligible": False, "reason": "no_vehicle_evidence"}
    matched_models = list(dict.fromkeys(match["model"] for match in [*exact_matches, *short_matches]))
    own = profiles[0]["model"]
    comparison_signal = len(matched_models) > 1 or bool(
        re.search(r"(对比|横评|PK|pk|vs|VS|怎么选|谁更|同级)", text)
    )
    role = "comparison" if comparison_signal else "subject" if exact_matches else "mention"
    topic_matches = [
        topic for topic in list(dict.fromkeys(str(value or "").strip() for value in topics))
        if topic and normalize_text(topic) in normalized
    ]
    if comparison_signal:
        bucket = "comparison"
    elif own in matched_models and topic_matches:
        bucket = "attribute"
    elif own in matched_models:
        bucket = "own"
    else:
        bucket = "competitor"

    metrics = item_metrics(item)
    views_verified = bool(item.get("viewsVerified")) and metrics["views"] is not None
    interaction = metrics["likes"] + metrics["comments"] * 2 + metrics["shares"] * 3 + metrics["collects"] * 2.5
    status = "verified" if exact_matches else "pending_review"
    item_id = str(item.get("platformItemId") or item.get("id") or "").strip()
    source_url = str(item.get("sourceUrl") or "").strip()
    stable = item_id or source_url or hashlib.sha256(
        f"{text}|{item.get('author')}|{published.isoformat()}".encode()
    ).hexdigest()[:20]
    return {
        "eligible": True,
        "itemId": stable,
        "platformItemId": item_id,
        "sourceUrl": source_url,
        "text": text,
        "author": str(item.get("author") or ""),
        "publishedAt": published.isoformat(),
        "coverUrl": str(item.get("coverUrl") or ""),
        "dynamicCoverUrl": str(item.get("dynamicCoverUrl") or ""),
        "sourceRole": str(item.get("sourceRole") or "user_or_unknown"),
        "matchedModels": matched_models,
        "matchedTopics": topic_matches,
        "matchEvidence": evidence,
        "verificationStatus": status,
        "role": role,
        "bucket": bucket,
        "metrics": metrics,
        "metricStatus": {
            "views": "verified" if views_verified else "missing",
        },
        "statisticsObservedAt": str(item.get("observedAt") or "") if views_verified else "",
        "rankingEligible": views_verified,
        "interactionScore": round(interaction, 2),
        "rawEvidence": {
            "platform": str(item.get("platform") or "douyin"),
            "observedAt": str(item.get("observedAt") or ""),
            "collectionMode": str(item.get("collectionMode") or ""),
        },
    }


def deduplicate(items: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: dict[str, dict[str, Any]] = {}
    for item in items:
        key = str(item.get("platformItemId") or item.get("sourceUrl") or item.get("itemId") or "")
        if not key:
            continue
        current = selected.get(key)
        current_score = float(current.get("interactionScore") or 0) if current else -1
        if not current or float(item.get("interactionScore") or 0) > current_score:
            selected[key] = item
    return list(selected.values())


def rank_items(items: Iterable[dict[str, Any]], *, field: str = "views") -> list[dict[str, Any]]:
    if field not in {"views", "interactionScore", "growth"}:
        raise ValueError("不支持的榜单排序方式。")
    def score(item: dict[str, Any]) -> float:
        if field == "views":
            value = (item.get("metrics") or {}).get("views")
            return float(value) if value is not None else -1
        return float(item.get(field) or 0)
    ordered = sorted(items, key=lambda item: (score(item), item.get("publishedAt") or ""), reverse=True)
    return [{**item, "rank": index + 1} for index, item in enumerate(ordered)]


def public_result(
    run: dict[str, Any],
    profiles: list[dict[str, Any]],
    items: list[dict[str, Any]],
    exclusions: dict[str, int],
) -> dict[str, Any]:
    verified = [
        item for item in items
        if item.get("verificationStatus") in {"verified", "manual_verified"}
    ]
    pending = [item for item in items if item.get("verificationStatus") == "pending_review"]
    formal = [
        item for item in verified
        if item.get("rankingEligible") and (item.get("metricStatus") or {}).get("views") == "verified"
    ]
    incomplete = [item for item in verified if item not in formal]
    buckets = {
        key: rank_items([item for item in formal if item.get("bucket") == key])
        for key in ("own", "competitor", "comparison", "attribute")
    }
    coverage = round(len(formal) / len(verified) * 100, 1) if verified else 0.0
    own_models = {
        model for item in formal if item.get("bucket") in {"own", "comparison", "attribute"}
        for model in item.get("matchedModels") or []
    }
    competitor_models = {
        model for item in formal if item.get("bucket") in {"competitor", "comparison"}
        for model in item.get("matchedModels") or []
    }
    expected_competitors = [profile["model"] for profile in profiles[1:]]
    has_relational_evidence = any(
        item.get("bucket") in {"comparison", "attribute"} for item in formal
    )
    strategy_ready = (
        profiles[0]["model"] in own_models
        and all(model in competitor_models for model in expected_competitors)
        and coverage >= 80
        and has_relational_evidence
        and bool(formal)
    )
    publication_status = "ready" if not incomplete and formal else "partial" if formal else "blocked"
    return {
        "runId": run["id"],
        "projectId": run["project_id"],
        "rangeDays": run["range_days"],
        "window": json.loads(run["window_json"]),
        "subject": profiles[0]["model"],
        "competitors": [profile["model"] for profile in profiles[1:]],
        "counts": {
            "verified": len(verified),
            "rankingEligible": len(formal),
            "viewsVerified": len(formal),
            "viewsMissing": sum((item.get("metricStatus") or {}).get("views") == "missing" for item in incomplete),
            "viewsFailed": sum((item.get("metricStatus") or {}).get("views") == "failed" for item in incomplete),
            "viewCoveragePct": coverage,
            "pendingReview": len(pending),
            "excluded": sum(exclusions.values()),
        },
        "exclusions": exclusions,
        "lists": {
            **buckets,
            "pending": sorted(pending, key=lambda item: item.get("publishedAt") or "", reverse=True),
            "incompleteMetrics": sorted(
                incomplete, key=lambda item: item.get("publishedAt") or "", reverse=True
            ),
        },
        "publicationStatus": publication_status,
        "strategyReadiness": {
            "ready": strategy_ready,
            "coveragePct": coverage,
            "hasOwnSample": profiles[0]["model"] in own_models,
            "missingCompetitors": [
                model for model in expected_competitors if model not in competitor_models
            ],
            "hasComparisonOrAttributeEvidence": has_relational_evidence,
            "message": (
                "证据达到策略输出条件"
                if strategy_ready
                else "当前仅可形成有限观察：需补齐本品、全部竞品、热度覆盖及对比或属性证据。"
            ),
        },
        "rankingRule": {
            "default": "views",
            "relevance": "gate_only",
            "interaction": "separate",
            "growth": "requires_previous_manual_snapshot",
        },
        "generatedAt": utcnow(),
    }


def sanitize_public_result(result: dict[str, Any]) -> dict[str, Any]:
    """Treat pre-contract zero views as unavailable without mutating stored history."""
    result = json.loads(json.dumps(result or {}, ensure_ascii=False))
    lists = result.get("lists") or {}
    formal_keys = ("own", "competitor", "comparison", "attribute")
    if not any(
        "metricStatus" not in item
        for key in formal_keys
        for item in (lists.get(key) or [])
    ):
        return result
    items: list[dict[str, Any]] = []
    for key in (*formal_keys, "pending", "incompleteMetrics"):
        for item in lists.get(key) or []:
            if key in formal_keys and "metricStatus" not in item:
                item.setdefault("metrics", {})["views"] = None
                item["metricStatus"] = {"views": "missing"}
                item["rankingEligible"] = False
                item["rankingExclusionReason"] = "历史记录未保存播放热度核验状态"
            items.append(item)
    profiles = build_profiles(result.get("subject") or "", result.get("competitors") or [])
    return public_result(
        {
            "id": result.get("runId") or "",
            "project_id": result.get("projectId") or "",
            "range_days": result.get("rangeDays") or 7,
            "window_json": json.dumps(result.get("window") or {}, ensure_ascii=False),
        },
        profiles,
        deduplicate(items),
        result.get("exclusions") or {},
    )


def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        create table if not exists douyin_vehicle_radar_projects (
          id text primary key,
          org_id text not null,
          edition text not null,
          fingerprint text not null,
          subject text not null,
          competitors_json text not null,
          topics_json text not null default '[]',
          created_at text not null,
          updated_at text not null,
          unique(org_id, edition, fingerprint)
        );
        create index if not exists idx_douyin_vehicle_radar_projects_scope
        on douyin_vehicle_radar_projects(org_id, edition, updated_at desc);
        create table if not exists douyin_vehicle_radar_runs (
          id text primary key,
          project_id text not null,
          org_id text not null,
          edition text not null,
          range_days integer not null,
          window_json text not null,
          request_key text not null,
          status text not null,
          stage text not null,
          progress integer not null default 0,
          message text not null default '',
          result_json text not null default '{}',
          error text not null default '',
          retryable integer not null default 0,
          created_at text not null,
          updated_at text not null,
          completed_at text,
          unique(org_id, edition, request_key)
        );
        create index if not exists idx_douyin_vehicle_radar_runs_scope
        on douyin_vehicle_radar_runs(org_id, edition, project_id, updated_at desc);
        create table if not exists douyin_vehicle_radar_observations (
          id text primary key,
          run_id text not null,
          project_id text not null,
          org_id text not null,
          edition text not null,
          platform_item_id text not null,
          observed_at text not null,
          metrics_json text not null,
          item_json text not null,
          unique(run_id, platform_item_id)
        );
        create index if not exists idx_douyin_vehicle_radar_observations_history
        on douyin_vehicle_radar_observations(org_id, edition, project_id, platform_item_id, observed_at desc);
        create table if not exists douyin_vehicle_radar_metric_snapshots (
          id text primary key,
          org_id text not null,
          edition text not null,
          platform_item_id text not null,
          status text not null,
          metrics_json text not null default '{}',
          error text not null default '',
          observed_at text not null
        );
        create index if not exists idx_douyin_vehicle_radar_metric_cache
        on douyin_vehicle_radar_metric_snapshots(
          org_id, edition, platform_item_id, observed_at desc
        );
        create table if not exists douyin_vehicle_radar_reviews (
          id text primary key,
          run_id text not null,
          org_id text not null,
          edition text not null,
          platform_item_id text not null,
          verdict text not null,
          model text,
          reason text not null,
          reviewer_id text not null,
          created_at text not null,
          unique(run_id, platform_item_id)
        );
        create table if not exists douyin_vehicle_radar_strategies (
          id text primary key,
          run_id text not null,
          org_id text not null,
          edition text not null,
          status text not null,
          evidence_hash text not null,
          result_json text not null default '{}',
          created_at text not null,
          updated_at text not null
        );
        """
    )


def project_fingerprint(subject: str, competitors: Iterable[str], topics: Iterable[str]) -> str:
    payload = {
        "subject": str(subject or "").strip(),
        "competitors": clean_models(competitors, exclude=subject),
        "topics": list(dict.fromkeys(str(item or "").strip() for item in topics if str(item or "").strip()))[:12],
    }
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


@dataclass
class RadarRepository:
    connection_factory: Callable[[], sqlite3.Connection]

    def _connect(self) -> sqlite3.Connection:
        conn = self.connection_factory()
        conn.row_factory = sqlite3.Row
        init_schema(conn)
        return conn

    def upsert_project(
        self, org_id: str, edition: str, subject: str, competitors: Iterable[str], topics: Iterable[str]
    ) -> dict[str, Any]:
        competitors = clean_models(competitors, exclude=subject)
        topics = list(dict.fromkeys(str(item or "").strip() for item in topics if str(item or "").strip()))[:12]
        fingerprint = project_fingerprint(subject, competitors, topics)
        stamp = utcnow()
        with self._connect() as conn:
            row = conn.execute(
                "select * from douyin_vehicle_radar_projects where org_id=? and edition=? and fingerprint=?",
                (org_id, edition, fingerprint),
            ).fetchone()
            if not row:
                project_id = str(uuid.uuid4())
                conn.execute(
                    """insert into douyin_vehicle_radar_projects
                       (id,org_id,edition,fingerprint,subject,competitors_json,topics_json,created_at,updated_at)
                       values (?,?,?,?,?,?,?,?,?)""",
                    (
                        project_id, org_id, edition, fingerprint, subject,
                        json.dumps(competitors, ensure_ascii=False),
                        json.dumps(topics, ensure_ascii=False), stamp, stamp,
                    ),
                )
                row = conn.execute(
                    "select * from douyin_vehicle_radar_projects where id=?", (project_id,)
                ).fetchone()
            else:
                conn.execute(
                    "update douyin_vehicle_radar_projects set updated_at=? where id=?", (stamp, row["id"])
                )
            return self._project(row)

    @staticmethod
    def _project(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "orgId": row["org_id"],
            "edition": row["edition"],
            "subject": row["subject"],
            "competitors": json.loads(row["competitors_json"]),
            "topics": json.loads(row["topics_json"]),
            "fingerprint": row["fingerprint"],
            "updatedAt": row["updated_at"],
        }

    def get_project(self, project_id: str, org_id: str, edition: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "select * from douyin_vehicle_radar_projects where id=? and org_id=? and edition=?",
                (project_id, org_id, edition),
            ).fetchone()
            return self._project(row) if row else None

    def create_run(self, project: dict[str, Any], days: int, *, force: bool = False) -> dict[str, Any]:
        days = normalize_range(days)
        window = date_window(days)
        request_seed = f"{project['id']}|{days}|{window['end'][:13]}"
        request_key = hashlib.sha256(request_seed.encode()).hexdigest()
        stamp = utcnow()
        with self._connect() as conn:
            row = None if force else conn.execute(
                "select * from douyin_vehicle_radar_runs where org_id=? and edition=? and request_key=?",
                (project["orgId"], project["edition"], request_key),
            ).fetchone()
            if row:
                return self._run(row)
            run_id = str(uuid.uuid4())
            if force:
                request_key = hashlib.sha256(f"{request_seed}|{run_id}".encode()).hexdigest()
            conn.execute(
                """insert into douyin_vehicle_radar_runs
                   (id,project_id,org_id,edition,range_days,window_json,request_key,status,stage,progress,
                    message,result_json,error,retryable,created_at,updated_at)
                   values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    run_id, project["id"], project["orgId"], project["edition"], days,
                    json.dumps(window, ensure_ascii=False), request_key, "queued", "preparing", 0,
                    "任务已创建，等待手动采集", "{}", "", 0, stamp, stamp,
                ),
            )
            row = conn.execute("select * from douyin_vehicle_radar_runs where id=?", (run_id,)).fetchone()
            return self._run(row)

    @staticmethod
    def _run(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "projectId": row["project_id"],
            "orgId": row["org_id"],
            "edition": row["edition"],
            "rangeDays": row["range_days"],
            "window": json.loads(row["window_json"]),
            "status": row["status"],
            "stage": row["stage"],
            "progress": row["progress"],
            "message": row["message"],
            "result": json.loads(row["result_json"] or "{}"),
            "error": row["error"],
            "retryable": bool(row["retryable"]),
            "createdAt": row["created_at"],
            "updatedAt": row["updated_at"],
            "completedAt": row["completed_at"],
        }

    def get_run(self, run_id: str, org_id: str, edition: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "select * from douyin_vehicle_radar_runs where id=? and org_id=? and edition=?",
                (run_id, org_id, edition),
            ).fetchone()
            return self._run(row) if row else None

    def latest_run(
        self, org_id: str, edition: str, subject: str
    ) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """select r.* from douyin_vehicle_radar_runs r
                   join douyin_vehicle_radar_projects p on p.id=r.project_id
                   where r.org_id=? and r.edition=? and p.subject=?
                   order by r.updated_at desc limit 1""",
                (org_id, edition, str(subject or "").strip()),
            ).fetchone()
            return self._run(row) if row else None

    def update_run(self, run_id: str, **changes: Any) -> None:
        mapping = {
            "status": "status", "stage": "stage", "progress": "progress", "message": "message",
            "error": "error", "retryable": "retryable", "result": "result_json",
            "completedAt": "completed_at",
        }
        fields: list[str] = []
        values: list[Any] = []
        for key, value in changes.items():
            column = mapping.get(key)
            if not column:
                continue
            if key == "result":
                value = json.dumps(value or {}, ensure_ascii=False)
            if key == "retryable":
                value = 1 if value else 0
            fields.append(f"{column}=?")
            values.append(value)
        fields.append("updated_at=?")
        values.extend([utcnow(), run_id])
        with self._connect() as conn:
            conn.execute(f"update douyin_vehicle_radar_runs set {','.join(fields)} where id=?", values)

    def previous_metrics(
        self, org_id: str, edition: str, project_id: str, platform_item_id: str, before: str
    ) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """select metrics_json from douyin_vehicle_radar_observations
                   where org_id=? and edition=? and project_id=? and platform_item_id=? and observed_at<?
                   order by observed_at desc limit 1""",
                (org_id, edition, project_id, platform_item_id, before),
            ).fetchone()
            return json.loads(row["metrics_json"]) if row else None

    def cached_metric(
        self,
        org_id: str,
        edition: str,
        platform_item_id: str,
        *,
        max_age_minutes: int = METRIC_CACHE_MINUTES,
    ) -> dict[str, Any] | None:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)).isoformat()
        with self._connect() as conn:
            row = conn.execute(
                """select status,metrics_json,error,observed_at
                   from douyin_vehicle_radar_metric_snapshots
                   where org_id=? and edition=? and platform_item_id=? and observed_at>=?
                   order by observed_at desc limit 1""",
                (org_id, edition, platform_item_id, cutoff),
            ).fetchone()
            if not row:
                return None
            return {
                "status": row["status"],
                "metrics": json.loads(row["metrics_json"] or "{}"),
                "error": row["error"],
                "observedAt": row["observed_at"],
            }

    def save_metric_snapshot(
        self,
        org_id: str,
        edition: str,
        platform_item_id: str,
        status: str,
        *,
        metrics: dict[str, Any] | None = None,
        error: str = "",
        observed_at: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """insert into douyin_vehicle_radar_metric_snapshots
                   (id,org_id,edition,platform_item_id,status,metrics_json,error,observed_at)
                   values (?,?,?,?,?,?,?,?)""",
                (
                    str(uuid.uuid4()), org_id, edition, platform_item_id, status,
                    json.dumps(metrics or {}, ensure_ascii=False), str(error or "")[:500],
                    observed_at or utcnow(),
                ),
            )

    def save_observations(self, run: dict[str, Any], items: list[dict[str, Any]]) -> None:
        observed = utcnow()
        with self._connect() as conn:
            for item in items:
                platform_item_id = str(item.get("platformItemId") or item.get("itemId") or "")
                if not platform_item_id:
                    continue
                conn.execute(
                    """insert or replace into douyin_vehicle_radar_observations
                       (id,run_id,project_id,org_id,edition,platform_item_id,observed_at,metrics_json,item_json)
                       values (?,?,?,?,?,?,?,?,?)""",
                    (
                        str(uuid.uuid4()), run["id"], run["projectId"], run["orgId"], run["edition"],
                        platform_item_id, observed,
                        json.dumps(item.get("metrics") or {}, ensure_ascii=False),
                        json.dumps(item, ensure_ascii=False),
                    ),
                )

    def recover_interrupted(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """update douyin_vehicle_radar_runs
                   set status='failed',stage='failed',retryable=1,
                       message='服务重启中断了本轮手动采集，可安全重试。',
                       error='任务在服务重启前未完成',updated_at=?
                   where status in ('queued','running')""",
                (utcnow(),),
            )

    def review_item(
        self,
        run_id: str,
        org_id: str,
        edition: str,
        platform_item_id: str,
        verdict: str,
        *,
        reviewer_id: str,
        model: str = "",
        reason: str = "",
    ) -> dict[str, Any]:
        if verdict not in {"include", "exclude"}:
            raise ValueError("人工复核仅支持纳入或排除。")
        run = self.get_run(run_id, org_id, edition)
        if not run:
            raise ValueError("未找到本轮采集任务。")
        result = dict(run.get("result") or {})
        lists = dict(result.get("lists") or {})
        pending = list(lists.get("pending") or [])
        target = next(
            (
                item for item in pending
                if str(item.get("platformItemId") or item.get("itemId") or "") == str(platform_item_id)
            ),
            None,
        )
        if not target:
            raise ValueError("该内容不在当前待复核队列。")
        pending = [
            item for item in pending
            if str(item.get("platformItemId") or item.get("itemId") or "") != str(platform_item_id)
        ]
        lists["pending"] = rank_items(pending)
        if verdict == "include":
            accepted = {
                **target,
                "verificationStatus": "manual_verified",
                "manualReview": {"verdict": verdict, "model": model, "reason": reason},
            }
            if (
                accepted.get("rankingEligible")
                and (accepted.get("metricStatus") or {}).get("views") == "verified"
            ):
                bucket = accepted.get("bucket") if accepted.get("bucket") in {
                    "own", "competitor", "comparison", "attribute"
                } else "competitor"
                lists[bucket] = rank_items([*(lists.get(bucket) or []), accepted])
            else:
                lists["incompleteMetrics"] = [
                    *(lists.get("incompleteMetrics") or []), accepted
                ]
            result.setdefault("counts", {})["verified"] = int(result.get("counts", {}).get("verified") or 0) + 1
        result.setdefault("counts", {})["pendingReview"] = len(pending)
        result["lists"] = lists
        stamp = utcnow()
        with self._connect() as conn:
            conn.execute(
                """insert or replace into douyin_vehicle_radar_reviews
                   (id,run_id,org_id,edition,platform_item_id,verdict,model,reason,reviewer_id,created_at)
                   values (?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(uuid.uuid4()), run_id, org_id, edition, str(platform_item_id), verdict,
                    str(model or ""), str(reason or ""), reviewer_id, stamp,
                ),
            )
        self.update_run(run_id, result=result, message="人工复核已保存")
        return result

    def save_strategy(
        self, run_id: str, org_id: str, edition: str, result: dict[str, Any]
    ) -> dict[str, Any]:
        evidence_hash = hashlib.sha256(
            json.dumps(result.get("comparisonItems") or [], ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()
        stamp = utcnow()
        strategy_id = str(uuid.uuid4())
        with self._connect() as conn:
            conn.execute(
                """insert into douyin_vehicle_radar_strategies
                   (id,run_id,org_id,edition,status,evidence_hash,result_json,created_at,updated_at)
                   values (?,?,?,?,?,?,?,?,?)""",
                (
                    strategy_id, run_id, org_id, edition,
                    str((result.get("unifiedInsight") or {}).get("publicationStatus") or "withheld"),
                    evidence_hash, json.dumps(result, ensure_ascii=False), stamp, stamp,
                ),
            )
        return {"id": strategy_id, "runId": run_id, "result": result, "updatedAt": stamp}

    def latest_strategy(
        self, run_id: str, org_id: str, edition: str
    ) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """select * from douyin_vehicle_radar_strategies
                   where run_id=? and org_id=? and edition=? order by updated_at desc limit 1""",
                (run_id, org_id, edition),
            ).fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "runId": row["run_id"],
                "status": row["status"],
                "result": json.loads(row["result_json"] or "{}"),
                "updatedAt": row["updated_at"],
            }


class RadarService:
    def __init__(self, repository: RadarRepository, adapter: Any):
        self.repository = repository
        self.adapter = adapter

    @staticmethod
    def _batches(values: list[str], size: int = METRIC_BATCH_SIZE) -> Iterable[list[str]]:
        for index in range(0, len(values), size):
            yield values[index:index + size]

    @staticmethod
    def _apply_metric(item: dict[str, Any], snapshot: dict[str, Any]) -> None:
        status = str(snapshot.get("status") or "failed")
        metrics = snapshot.get("metrics") or {}
        views = optional_metric(metrics, "views", "play_count", "view_count")
        if status == "verified" and views is not None:
            item.setdefault("metrics", {})["views"] = views
            item["metricStatus"] = {"views": "verified"}
            item["statisticsObservedAt"] = str(snapshot.get("observedAt") or "")
            item["rankingEligible"] = True
            item.pop("rankingExclusionReason", None)
            return
        item.setdefault("metrics", {})["views"] = None
        item["metricStatus"] = {"views": "failed" if status == "failed" else "missing"}
        item["statisticsObservedAt"] = str(snapshot.get("observedAt") or "")
        item["rankingEligible"] = False
        item["rankingExclusionReason"] = (
            "播放热度补抓失败" if status == "failed" else "未取得可核验播放热度"
        )

    def enrich_metrics(
        self,
        items: list[dict[str, Any]],
        org_id: str,
        edition: str,
        *,
        force_missing: bool = False,
    ) -> None:
        targets = [
            item for item in items
            if item.get("verificationStatus") in {"verified", "manual_verified"}
            and str(item.get("platformItemId") or "").strip()
        ][:MAX_METRIC_ITEMS]
        missing_ids: list[str] = []
        by_id = {
            str(item.get("platformItemId") or ""): item for item in targets
        }
        for item_id, item in by_id.items():
            if not force_missing and (item.get("metricStatus") or {}).get("views") == "verified":
                continue
            cached = None if force_missing else self.repository.cached_metric(
                org_id, edition, item_id
            )
            if cached:
                self._apply_metric(item, cached)
            else:
                missing_ids.append(item_id)
        if not missing_ids:
            return
        if not hasattr(self.adapter, "fetch_statistics"):
            for item_id in missing_ids:
                snapshot = {"status": "failed", "metrics": {}, "observedAt": utcnow()}
                self.repository.save_metric_snapshot(
                    org_id, edition, item_id, "failed", error="热度核验能力不可用",
                    observed_at=snapshot["observedAt"],
                )
                self._apply_metric(by_id[item_id], snapshot)
            return
        def apply_response(batch: list[str], response: dict[str, Any]) -> None:
            observed_at = utcnow()
            returned = response.get("items") or {}
            observed_at = str(response.get("observedAt") or observed_at)
            for item_id in batch:
                metrics = returned.get(item_id)
                status = "verified" if optional_metric(metrics or {}, "views") is not None else "missing"
                snapshot = {
                    "status": status,
                    "metrics": metrics or {},
                    "observedAt": observed_at,
                }
                self.repository.save_metric_snapshot(
                    org_id, edition, item_id, status, metrics=metrics,
                    observed_at=observed_at,
                )
                self._apply_metric(by_id[item_id], snapshot)

        def mark_failed(batch: list[str], exc: Exception) -> None:
            observed_at = utcnow()
            for item_id in batch:
                snapshot = {"status": "failed", "metrics": {}, "observedAt": observed_at}
                self.repository.save_metric_snapshot(
                    org_id, edition, item_id, "failed", error=str(exc),
                    observed_at=observed_at,
                )
                self._apply_metric(by_id[item_id], snapshot)

        split_budget = [MAX_METRIC_SPLIT_RETRIES]

        def fetch_batch(batch: list[str]) -> None:
            try:
                response = self.adapter.fetch_statistics(batch)
                apply_response(batch, response)
            except Exception as exc:
                if len(batch) <= 1 or split_budget[0] <= 0:
                    mark_failed(batch, exc)
                    return
                middle = max(1, len(batch) // 2)
                for child in (batch[:middle], batch[middle:]):
                    if not child:
                        continue
                    if split_budget[0] <= 0:
                        mark_failed(child, exc)
                        continue
                    split_budget[0] -= 1
                    fetch_batch(child)

        for batch in self._batches(missing_ids):
            fetch_batch(batch)

    def run(
        self,
        run_id: str,
        org_id: str,
        edition: str,
        *,
        on_stage: Callable[[str, int, str], None] | None = None,
        max_queries: int = 16,
        count: int = 20,
    ) -> dict[str, Any]:
        run = self.repository.get_run(run_id, org_id, edition)
        if not run:
            raise ValueError("未找到本轮采集任务。")
        project = self.repository.get_project(run["projectId"], org_id, edition)
        if not project:
            raise ValueError("未找到本轮车型项目。")
        profiles = build_profiles(project["subject"], project["competitors"])
        queries = build_queries(
            project["subject"], project["competitors"], project["topics"], max_queries=max_queries
        )
        def stage(name: str, progress: int, message: str) -> None:
            self.repository.update_run(
                run_id, status="running", stage=name, progress=progress, message=message, retryable=False
            )
            if on_stage:
                on_stage(name, progress, message)
        stage(*STAGES[0])
        raw: list[dict[str, Any]] = []
        stage(*STAGES[1])
        for query in queries:
            response = self.adapter.search(
                "douyin", query["query"], 1, max(5, min(int(count or 20), 50)), run["window"]
            )
            raw.extend(response.get("items") or [])
        stage(*STAGES[2])
        exclusions = {
            "missing_published_at": 0,
            "outside_window": 0,
            "no_vehicle_evidence": 0,
        }
        classified: list[dict[str, Any]] = []
        for item in raw:
            result = classify_candidate(item, profiles, project["topics"], run["window"])
            if not result.get("eligible"):
                reason = result.get("reason") or "no_vehicle_evidence"
                exclusions[reason] = exclusions.get(reason, 0) + 1
                continue
            classified.append(result)
        stage(*STAGES[3])
        stage(*STAGES[4])
        items = deduplicate(classified)
        stage(*STAGES[5])
        self.enrich_metrics(items, org_id, edition)
        observed = utcnow()
        for item in items:
            views = (item.get("metrics") or {}).get("views")
            if views is None:
                item["growth"] = None
                continue
            previous = self.repository.previous_metrics(
                org_id, edition, project["id"],
                str(item.get("platformItemId") or item.get("itemId") or ""), observed,
            )
            previous_views = optional_metric(previous or {}, "views")
            item["growth"] = max(0, float(views) - previous_views) if previous_views is not None else None
        stage(*STAGES[6])
        row = {
            "id": run["id"],
            "project_id": run["projectId"],
            "range_days": run["rangeDays"],
            "window_json": json.dumps(run["window"], ensure_ascii=False),
        }
        result = public_result(row, profiles, items, exclusions)
        self.repository.save_observations(run, items)
        status = "partial" if result.get("publicationStatus") in {"partial", "blocked"} else "completed"
        self.repository.update_run(
            run_id, status=status, stage=status, progress=100,
            message=(
                "正式榜单已生成，部分内容热度待补充"
                if status == "partial"
                else "本轮正式榜单已生成"
            ),
            result=result, completedAt=utcnow(),
            retryable=bool(result.get("lists", {}).get("incompleteMetrics")),
        )
        return result

    def retry_metrics(
        self,
        run_id: str,
        org_id: str,
        edition: str,
        *,
        on_stage: Callable[[str, int, str], None] | None = None,
    ) -> dict[str, Any]:
        run = self.repository.get_run(run_id, org_id, edition)
        if not run:
            raise ValueError("未找到本轮采集任务。")
        project = self.repository.get_project(run["projectId"], org_id, edition)
        if not project:
            raise ValueError("未找到本轮车型项目。")
        result = run.get("result") or {}
        lists = result.get("lists") or {}
        items = [
            item
            for key in ("own", "competitor", "comparison", "attribute", "pending", "incompleteMetrics")
            for item in (lists.get(key) or [])
        ]
        items = deduplicate(items)
        incomplete = [
            item for item in items
            if (item.get("metricStatus") or {}).get("views") != "verified"
            and item.get("verificationStatus") in {"verified", "manual_verified"}
        ]
        if not incomplete:
            return result
        self.repository.update_run(
            run_id, status="running", stage="enriching_metrics", progress=82,
            message="正在重试未完成的播放热度核验", retryable=False,
        )
        if on_stage:
            on_stage("enriching_metrics", 82, "正在重试未完成的播放热度核验")
        self.enrich_metrics(incomplete, org_id, edition, force_missing=True)
        rebuilt = public_result(
            {
                "id": run["id"],
                "project_id": run["projectId"],
                "range_days": run["rangeDays"],
                "window_json": json.dumps(run["window"], ensure_ascii=False),
            },
            build_profiles(project["subject"], project["competitors"]),
            items,
            result.get("exclusions") or {},
        )
        self.repository.save_observations(run, items)
        status = "partial" if rebuilt.get("publicationStatus") in {"partial", "blocked"} else "completed"
        self.repository.update_run(
            run_id, status=status, stage=status, progress=100,
            message=(
                "热度补抓仍有未完成项"
                if status == "partial"
                else "热度补抓完成，正式榜单已更新"
            ),
            result=rebuilt, completedAt=utcnow(),
            retryable=bool(rebuilt.get("lists", {}).get("incompleteMetrics")),
        )
        return rebuilt
