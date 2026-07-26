#!/usr/bin/env python3
"""Compare two SQLite databases by logical table content, not file bytes."""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def normalized(value):
    if isinstance(value, bytes):
        return {"__bytes__": value.hex()}
    return value


def table_snapshot(conn, table):
    columns = conn.execute(f'pragma table_info("{table}")').fetchall()
    column_names = [row[1] for row in columns]
    rows = [
        [normalized(value) for value in row]
        for row in conn.execute(f'select * from "{table}"').fetchall()
    ]
    rows.sort(key=lambda row: json.dumps(row, ensure_ascii=False, sort_keys=True, default=str))
    payload = json.dumps(
        {"columns": column_names, "rows": rows},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return {
        "columns": column_names,
        "rowCount": len(rows),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def database_snapshot(path):
    uri = f"{Path(path).resolve().as_uri()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        tables = [
            row[0]
            for row in conn.execute(
                """select name from sqlite_master
                   where type='table' and name not like 'sqlite_%'
                   order by name"""
            )
        ]
        return {table: table_snapshot(conn, table) for table in tables}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    args = parser.parse_args()
    before = database_snapshot(args.before)
    after = database_snapshot(args.after)
    names = sorted(set(before) | set(after))
    changed = [
        {
            "table": name,
            "before": before.get(name),
            "after": after.get(name),
        }
        for name in names
        if before.get(name) != after.get(name)
    ]
    result = {
        "ok": not changed,
        "beforeTableCount": len(before),
        "afterTableCount": len(after),
        "changedTableCount": len(changed),
        "changedTables": changed,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
