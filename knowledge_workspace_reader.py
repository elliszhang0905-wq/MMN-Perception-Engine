"""Side-effect-free reader for the organization knowledge workspace."""

import json
import ipaddress
import sqlite3
from contextlib import closing
from pathlib import Path
from urllib.parse import parse_qsl, quote, urlparse


ALLOWED_EDITIONS = {"china", "global"}
ALLOWED_TYPES = {"原始材料", "知识结论", "方法论", "案例", "未分类"}
KNOWLEDGE_TYPE_MAP = {"case": "案例", "framework": "方法论", "analysis_method": "方法论"}
PROJECT_KEYS = {"project", "projectId", "project_id"}
SENSITIVE_URL_KEYS = {
    "token", "access_token", "api_key", "apikey", "key", "signature", "sig",
    "auth", "authorization", "password", "secret", "client_secret", "credential",
    "jwt", "session", "session_token",
}
MAX_ASSET_JSON_BYTES = 1024 * 1024
MAX_TEXT_BYTES = 256 * 1024
MAX_SCAN_ROWS = 10000
MAX_SCAN_BYTES = 64 * 1024 * 1024


class KnowledgeWorkspaceError(Exception):
    pass


class KnowledgeWorkspaceInputError(KnowledgeWorkspaceError):
    pass


class KnowledgeWorkspaceUnavailable(KnowledgeWorkspaceError):
    pass


class KnowledgeWorkspaceDataError(KnowledgeWorkspaceError):
    pass


def readonly_connection(db_path):
    path = Path(db_path).expanduser().resolve()
    uri = "file:" + quote(str(path), safe="/") + "?mode=ro"
    try:
        conn = sqlite3.connect(uri, uri=True)
        conn.row_factory = sqlite3.Row
        conn.execute("pragma query_only=on")
        return conn
    except sqlite3.Error as exc:
        raise KnowledgeWorkspaceUnavailable("知识库暂不可用") from exc


def _string(value, field, *, nullable=True, max_bytes=MAX_TEXT_BYTES):
    if value is None and nullable:
        return None
    if not isinstance(value, str):
        raise KnowledgeWorkspaceDataError(f"{field}字段类型无效")
    if len(value.encode("utf-8")) > max_bytes:
        raise KnowledgeWorkspaceDataError(f"{field}字段过大")
    return value


def _project_scoped(asset, metadata):
    return any(key in asset and asset[key] not in (None, "") for key in PROJECT_KEYS) or any(
        key in metadata and metadata[key] not in (None, "") for key in PROJECT_KEYS
    )


def _safe_source_url(value):
    value = _string(value, "sourceUrl")
    if not value:
        return None
    try:
        parsed = urlparse(value)
        query_keys = {key.casefold().replace("-", "_") for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
        fragment_keys = {key.casefold().replace("-", "_") for key, _ in parse_qsl(parsed.fragment, keep_blank_values=True)}
        credential_key = any(
            key in SENSITIVE_URL_KEYS
            or key.endswith(("_token", "_api_key", "_signature", "_secret", "_credential"))
            for key in query_keys | fragment_keys
        )
        try:
            address = ipaddress.ip_address(parsed.hostname)
            public_host = not (address.is_private or address.is_loopback or address.is_link_local
                               or address.is_reserved or address.is_unspecified)
        except (TypeError, ValueError):
            public_host = bool(parsed.hostname) and parsed.hostname.casefold() != "localhost"
        valid = (parsed.scheme in {"http", "https"} and bool(parsed.hostname)
                 and not parsed.username and not parsed.password
                 and not credential_key and public_host)
    except ValueError:
        return None
    if not valid:
        return None
    return value


def _safe_source_label(value):
    value = _string(value, "sourceLabel", max_bytes=2048)
    if not value:
        return None
    normalized = value.strip().replace("\\", "/")
    if normalized.startswith(("/", "file://")) or (len(normalized) >= 3 and normalized[1:3] == ":/"):
        return None
    return value


def _first(asset, metadata, *keys):
    for source in (asset, metadata):
        for key in keys:
            if key in source:
                return source[key]
    return None


def _display_type(asset, metadata):
    explicit = _first(asset, metadata, "type")
    if explicit is not None:
        explicit = _string(explicit, "type")
        if explicit in ALLOWED_TYPES:
            return explicit
    knowledge_type = metadata.get("knowledge_type")
    if knowledge_type is None:
        return "未分类"
    knowledge_type = _string(knowledge_type, "metadata.knowledge_type")
    return KNOWLEDGE_TYPE_MAP.get(knowledge_type, "未分类")


def _project_row(row):
    if row["source_snapshot_id"] not in (None, ""):
        return None
    raw = row["asset_json"]
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_ASSET_JSON_BYTES:
        raise KnowledgeWorkspaceDataError("知识记录数据过大或类型无效")
    try:
        asset = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise KnowledgeWorkspaceDataError("知识记录JSON无效") from exc
    if not isinstance(asset, dict):
        raise KnowledgeWorkspaceDataError("知识记录必须是对象")
    metadata = asset.get("metadata")
    if metadata is None:
        metadata = {}
    if not isinstance(metadata, dict):
        raise KnowledgeWorkspaceDataError("metadata字段类型无效")
    if _project_scoped(asset, metadata):
        return None
    item_id = _string(row["id"], "id", nullable=False)
    return {
        "id": item_id,
        "title": _string(_first(asset, metadata, "title"), "title", max_bytes=8192) or "",
        "body": _string(_first(asset, metadata, "body"), "body") or "",
        "type": _display_type(asset, metadata),
        "brand": _string(_first(asset, metadata, "brand"), "brand", max_bytes=512),
        "module": _string(_first(asset, metadata, "module"), "module", max_bytes=512),
        "createdAt": _string(row["created_at"], "createdAt"),
        "updatedAt": _string(row["updated_at"], "updatedAt"),
        "sourceLabel": _safe_source_label(_first(asset, metadata, "sourceLabel", "source_label")),
        "sourceUrl": _safe_source_url(_first(asset, metadata, "sourceUrl", "source_url")),
        "reviewStatus": "unavailable",
        "validity": "unknown",
    }


def _integer(value, name, minimum, maximum=None):
    if isinstance(value, bool):
        raise KnowledgeWorkspaceInputError(f"{name}参数无效")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise KnowledgeWorkspaceInputError(f"{name}参数无效") from exc
    if result < minimum or (maximum is not None and result > maximum):
        raise KnowledgeWorkspaceInputError(f"{name}参数超出范围")
    return result


def read_knowledge_workspace(db_path, *, org_id, edition, q="", item_type="", brand="", module="", offset=0, limit=50):
    if not isinstance(org_id, str) or not org_id.strip():
        raise KnowledgeWorkspaceInputError("组织范围无效")
    if edition not in ALLOWED_EDITIONS:
        raise KnowledgeWorkspaceInputError("edition参数无效")
    if not isinstance(q, str) or len(q.encode("utf-8")) > 1000:
        raise KnowledgeWorkspaceInputError("q参数无效")
    if item_type and item_type not in ALLOWED_TYPES:
        raise KnowledgeWorkspaceInputError("type参数无效")
    for value, name in ((brand, "brand"), (module, "module")):
        if not isinstance(value, str) or len(value.encode("utf-8")) > 512:
            raise KnowledgeWorkspaceInputError(f"{name}参数无效")
    offset = _integer(offset, "offset", 0)
    limit = _integer(limit, "limit", 1, 100)
    try:
        with closing(readonly_connection(db_path)) as conn:
            conn.execute("begin")
            stats = conn.execute(
                "select count(*),coalesce(sum(length(cast(asset_json as blob))),0),"
                "coalesce(max(length(cast(asset_json as blob))),0) from strategy_knowledge_assets "
                "where org_id=? and edition=? and coalesce(source_snapshot_id,'')=''",
                (org_id.strip(), edition),
            ).fetchone()
            if stats[0] > MAX_SCAN_ROWS or stats[1] > MAX_SCAN_BYTES or stats[2] > MAX_ASSET_JSON_BYTES:
                raise KnowledgeWorkspaceDataError("知识库读取范围超出安全上限")
            rows = conn.execute(
                "select id,asset_json,source_snapshot_id,created_at,updated_at "
                "from strategy_knowledge_assets where org_id=? and edition=? "
                "and coalesce(source_snapshot_id,'')='' "
                "order by updated_at desc,id asc",
                (org_id.strip(), edition),
            )
            scoped_items = []
            for row in rows:
                item = _project_row(row)
                if item is not None:
                    scoped_items.append(item)
    except KnowledgeWorkspaceError:
        raise
    except sqlite3.Error as exc:
        raise KnowledgeWorkspaceUnavailable("知识库暂不可用") from exc
    needle = q.casefold().strip()
    facets = {
        "brands": sorted({item["brand"] for item in scoped_items if item["brand"]}),
        "modules": sorted({item["module"] for item in scoped_items if item["module"]}),
    }
    items = []
    for item in scoped_items:
        if needle and needle not in (item["title"] + "\n" + item["body"]).casefold():
            continue
        if item_type and item["type"] != item_type:
            continue
        if brand and item["brand"] != brand:
            continue
        if module and item["module"] != module:
            continue
        items.append(item)
    total = len(items)
    page = items[offset:offset + limit]
    return {
        "ok": True, "edition": edition, "scope": "organization", "items": page,
        "total": total, "offset": offset, "limit": limit, "hasMore": offset + len(page) < total,
        "facets": facets,
    }


def resolve_auth_scope_readonly(db_path, *, username, account_org):
    """Resolve an old signed token without opening the database for writes."""
    email = f"{str(username or '').lower()}@mmn.local"
    try:
        with closing(readonly_connection(db_path)) as conn:
            conn.execute("begin")
            candidates = conn.execute(
                "select u.id as user_id,u.org_id,u.created_at from users u "
                "join organizations o on o.id=u.org_id where u.email=? and o.name=?",
                (email, account_org),
            ).fetchall()
            scored = []
            tables = {row[0] for row in conn.execute("select name from sqlite_master where type='table'")}
            activity = ("learning_cases", "project_snapshots", "strategy_knowledge_assets",
                        "product_fact_documents", "cockpit_execution_cycles", "agent_runs", "social_trend_snapshots")
            for candidate in candidates:
                score = sum(
                    int(conn.execute(f"select count(*) from {table} where org_id=?", (candidate["org_id"],)).fetchone()[0])
                    for table in activity if table in tables
                )
                scored.append((score, candidate["created_at"] or "", candidate))
    except (KnowledgeWorkspaceError, sqlite3.Error):
        return {}
    if not scored:
        return {}
    selected = max(scored, key=lambda item: (item[0], item[1]))[2]
    return {"org_id": selected["org_id"], "user_id": selected["user_id"], "org": account_org, "email": email}
