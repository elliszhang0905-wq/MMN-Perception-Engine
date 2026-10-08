"""Small SQLite primitives; only internal code may select table names."""
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid
from zoneinfo import ZoneInfo


class GeoError(ValueError):
    def __init__(self, message, code="invalid_request", status=400):
        super().__init__(message)
        self.code, self.status = code, status


def stamp():
    return datetime.now(timezone.utc).isoformat()


def day_key():
    return datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()


def uid(kind):
    return f"geo_{kind}_{uuid.uuid4().hex}"


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(dumps(value).encode()).hexdigest()


def text_value(value, label, limit=2000, required=False):
    if value is None:
        value = ""
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise GeoError(f"{label}为空或超出长度限制")
    return value.strip()


def integer(value, label, low, high):
    if isinstance(value, bool):
        raise GeoError(f"{label}必须为整数")
    try:
        number = int(value)
        if str(number) != str(value) and not isinstance(value, int):
            raise ValueError()
    except (ValueError, TypeError, OverflowError):
        raise GeoError(f"{label}必须为整数") from None
    if not low <= number <= high:
        raise GeoError(f"{label}须在{low}至{high}之间")
    return number


def money_micro(value):
    try:
        number = Decimal(str(value))
        if not number.is_finite() or number < 0 or number > Decimal("100000000"):
            raise InvalidOperation()
        return int((number * 1000000).to_integral_value())
    except (InvalidOperation, ValueError, TypeError):
        raise GeoError("金额必须为有限的非负数") from None


def decoded(row):
    if row is None:
        raise GeoError("记录不存在或不属于当前空间", "not_found", 404)
    result = dict(row)
    payload = json.loads(result.pop("payload_json", "{}"))
    result = {**payload, **result}
    for key in list(result):
        if key.endswith("_json"):
            value = result.pop(key)
            output_key = "raw_response" if key == "raw_json" else key[:-5]
            result[output_key] = json.loads(value) if value is not None else None
    return result


class Store:
    def __init__(self, db_path):
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.executescript((Path(__file__).parent / "migrations/001_geo.sql").read_text())

    @contextmanager
    def connect(self, immediate=False):
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=15000")
        try:
            if immediate:
                conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _get(self, conn, table, org_id, ident, project_id=None):
        sql, args = f"SELECT * FROM {table} WHERE org_id=? AND id=?", [org_id, ident]
        if project_id is not None:
            sql += " AND project_id=?"
            args.append(project_id)
        return decoded(conn.execute(sql, args).fetchone())

    def _insert(self, conn, table, values):
        names = list(values)
        conn.execute(f"INSERT INTO {table} ({','.join(names)}) VALUES ({','.join('?' for _ in names)})",
                     [values[x] for x in names])

    def _audit(self, conn, org, project, event, ident, actor="local", detail=None):
        self._insert(conn, "geo_audit", {"id": uid("audit"), "org_id": org, "project_id": project,
                     "event": event, "record_id": ident, "actor": actor,
                     "detail_json": dumps(detail or {}), "created_at": stamp()})

    def _page(self, conn, table, org, project, limit=20, offset=0, extra="", args=()):
        limit = integer(limit, "每页条数", 1, 100)
        offset = integer(offset, "分页位置", 0, 1000000)
        where = "org_id=? AND project_id=?" + extra
        params = [org, project, *args]
        total = conn.execute(f"SELECT count(*) FROM {table} WHERE {where}", params).fetchone()[0]
        rows = conn.execute(f"SELECT * FROM {table} WHERE {where} ORDER BY created_at DESC,id LIMIT ? OFFSET ?",
                            [*params, limit, offset]).fetchall()
        return {"items": [decoded(x) for x in rows], "total": total, "limit": limit, "offset": offset}
