#!/usr/bin/env python3
"""Sync MMN vehicle assets against the public brand-model standard source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("MMN_DATA_DIR", ROOT / "data")).expanduser().resolve()
DB_PATH = Path(os.getenv("MMN_DB_PATH", DATA_DIR / "commercial_demo.db")).expanduser().resolve()
DEFAULT_URL = "https://caropen.api.autohome.com.cn/v1/carprice/tree_menu"
ASSET_SOURCE = "MMN车型资产标准源"
USER_AGENT = "MMN-Vehicle-Asset-Sync/1.0 (+public-page-standard-source)"


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def stable_id(*parts: object) -> str:
    joined = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        create table if not exists model_identity_assets (
            id text primary key,
            edition text not null default 'china',
            raw_name text not null,
            normalized_name text not null,
            brand_name text,
            model_family text,
            energy_type text,
            variant_name text,
            canonical_key text not null,
            confidence text,
            source text,
            qwen_checked integer not null default 0,
            qwen_reason text,
            first_seen_at text not null,
            updated_at text not null,
            unique(edition, raw_name, canonical_key)
        );
        create table if not exists vehicle_assets (
            id text primary key,
            org_id text not null default 'local',
            edition text not null default 'china',
            platform text not null,
            brand_name text,
            model_name text not null,
            first_seen_at text not null,
            last_seen_at text not null,
            first_source text,
            last_source text,
            period_first text,
            period_last text,
            import_count integer not null default 1,
            extra_json text not null default '{}',
            unique(org_id, edition, platform, model_name)
        );
        create table if not exists mmn_vehicle_asset_sync_runs (
            id text primary key,
            source_label text not null,
            source_url text not null,
            captured_at text not null,
            raw_payload_hash text not null,
            brand_count integer not null,
            model_count integer not null,
            inserted_or_updated integer not null,
            report_path text,
            status text not null,
            error text
        );
        """
    )
    columns = {row[1] for row in conn.execute("pragma table_info(vehicle_assets)")}
    if "org_id" not in columns:
        conn.execute("alter table vehicle_assets add column org_id text not null default 'local'")
    if "edition" not in columns:
        conn.execute("alter table vehicle_assets add column edition text not null default 'china'")
    conn.execute(
        "create unique index if not exists idx_vehicle_assets_unique "
        "on vehicle_assets(org_id, edition, platform, model_name)"
    )


def normalize_asset_row(row: dict) -> dict:
    """Apply the canonical server identity rules before writing monthly assets."""
    from server import corrected_brand_name, local_standard_model_identity

    raw_model = str(row.get("model_name") or "").strip()
    source_brand = str(row.get("brand_name") or "").strip()
    composite = raw_model if source_brand and source_brand in raw_model else f"{source_brand}{raw_model}"
    standard = local_standard_model_identity(raw_model) or local_standard_model_identity(composite) or {}
    brand = corrected_brand_name(standard.get("brandName") or source_brand, composite)
    energy = str(standard.get("energyType") or row.get("energy_type") or "UNKNOWN").upper()
    if energy == "UNKNOWN" and row.get("energy_type"):
        energy = str(row["energy_type"]).upper()
    normalized = str(standard.get("normalizedName") or raw_model).strip()
    family = str(standard.get("modelFamily") or normalized).strip()
    variant = str(standard.get("variantName") or "").strip()
    canonical = str(standard.get("canonicalKey") or "|".join([brand, family, energy, variant]))
    return {
        **row,
        "brand_name": brand,
        "normalized_name": normalized,
        "model_family": family,
        "variant_name": variant,
        "energy_type": energy,
        "canonical_key": canonical,
    }


def fetch_public_tree(url: str, timeout: int = 30, retries: int = 2) -> tuple[bytes, str]:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = int(getattr(response, "status", 200))
                if status in {403, 429}:
                    raise RuntimeError(f"公开标准源返回 {status}，已停止，不进行绕过。")
                if status >= 400:
                    raise RuntimeError(f"公开标准源返回 {status}。")
                return response.read(), response.geturl()
        except (HTTPError, URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if isinstance(exc, HTTPError) and exc.code in {403, 429}:
                break
            if attempt < retries:
                time.sleep(10)
    raise RuntimeError(str(last_error or "公开标准源访问失败"))


def flatten_tree(payload: dict) -> list[dict]:
    rows: list[dict] = []
    for letter_group in payload.get("result") or []:
        first_letter = letter_group.get("firstletter") or ""
        for brand in letter_group.get("branditems") or []:
            brand_id = brand.get("id")
            brand_name = str(brand.get("name") or "").strip()
            if not brand_name:
                continue
            for fct in brand.get("fctitems") or []:
                fct_name = str(fct.get("name") or "").strip()
                for series in fct.get("seriesitems") or []:
                    model_name = str(series.get("name") or "").strip()
                    if not model_name:
                        continue
                    energy = "BEV" if int(series.get("isnewenergy") or 0) == 1 else "UNKNOWN"
                    rows.append(
                        {
                            "brand_id": brand_id,
                            "brand_name": brand_name,
                            "first_letter": first_letter,
                            "fct_id": fct.get("id"),
                            "fct_name": fct_name,
                            "model_id": series.get("id"),
                            "model_name": model_name,
                            "energy_type": energy,
                            "state": series.get("state"),
                            "spec_count": series.get("speccount"),
                        }
                    )
    return rows


def save_raw(raw: bytes, captured_at: str, payload_hash: str) -> Path:
    raw_dir = DATA_DIR / "raw" / "mmn_vehicle_asset_sync" / captured_at[:10].replace("-", "")
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"vehicle_tree_{captured_at.replace(':', '').replace('-', '').replace('+', '_')}_{payload_hash[:10]}.json"
    path.write_bytes(raw)
    return path


def upsert_assets(conn: sqlite3.Connection, rows: list[dict], captured_at: str, source_url: str, payload_hash: str) -> int:
    count = 0
    for source_row in rows:
        row = normalize_asset_row(source_row)
        brand = row["brand_name"]
        model = row["model_name"]
        normalized = row["normalized_name"]
        family = row["model_family"]
        variant = row["variant_name"]
        energy = row["energy_type"]
        canonical = row["canonical_key"]
        asset_id = stable_id("model-identity", "china", model, canonical)
        conn.execute(
            """
            insert into model_identity_assets
            (id, edition, raw_name, normalized_name, brand_name, model_family, energy_type, variant_name, canonical_key, confidence, source, qwen_checked, qwen_reason, first_seen_at, updated_at)
            values (?, 'china', ?, ?, ?, ?, ?, ?, ?, 'high', ?, 0, ?, ?, ?)
            on conflict(edition, raw_name, canonical_key) do update set
              normalized_name=excluded.normalized_name,
              brand_name=excluded.brand_name,
              model_family=excluded.model_family,
              energy_type=excluded.energy_type,
              confidence='high',
              source=excluded.source,
              qwen_reason=excluded.qwen_reason,
              updated_at=excluded.updated_at
            """,
            (
                asset_id,
                model,
                normalized,
                brand,
                family,
                energy,
                variant,
                canonical,
                ASSET_SOURCE,
                "MMN标准车型树月度撞库确认",
                captured_at,
                captured_at,
            ),
        )
        conn.execute(
            """
            insert into vehicle_assets
            (id, org_id, edition, platform, brand_name, model_name, first_seen_at, last_seen_at, first_source, last_source, period_first, period_last, import_count, extra_json)
            values (?, 'local', 'china', ?, ?, ?, ?, ?, ?, ?, '', '', 1, ?)
            on conflict(org_id, edition, platform, model_name) do update set
              brand_name=excluded.brand_name,
              last_seen_at=excluded.last_seen_at,
              last_source=excluded.last_source,
              import_count=vehicle_assets.import_count+1,
              extra_json=excluded.extra_json
            """,
            (
                stable_id("vehicle-asset", ASSET_SOURCE, model),
                ASSET_SOURCE,
                brand,
                model,
                captured_at,
                captured_at,
                ASSET_SOURCE,
                ASSET_SOURCE,
                json.dumps(
                    {
                        "asset_source": ASSET_SOURCE,
                        "source_url": source_url,
                        "raw_payload_hash": payload_hash,
                        "brand_id": row.get("brand_id"),
                        "model_id": row.get("model_id"),
                        "fct_name": row.get("fct_name"),
                        "state": row.get("state"),
                        "spec_count": row.get("spec_count"),
                    },
                    ensure_ascii=False,
                ),
            ),
        )
        count += 1
    return count


def write_report(rows: list[dict], captured_at: str, source_url: str, payload_hash: str, raw_path: Path, updated: int) -> Path:
    brands = sorted({row["brand_name"] for row in rows})
    processed_dir = DATA_DIR / "processed"
    reports_dir = DATA_DIR / "reports"
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    latest = {
        "asset_source": ASSET_SOURCE,
        "captured_at": captured_at,
        "brand_count": len(brands),
        "model_count": len(rows),
        "updated_count": updated,
        "raw_payload_hash": payload_hash,
        "raw_file": str(raw_path),
        "brands": brands,
        "sample_models": rows[:30],
    }
    (processed_dir / "mmn_vehicle_asset_catalog_latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=2))
    report = reports_dir / f"mmn_vehicle_asset_sync_{captured_at[:10]}.md"
    report.write_text(
        "\n".join(
            [
                "# MMN车型资产月度撞库报告",
                "",
                f"- 撞库时间：{captured_at}",
                f"- 资产口径：{ASSET_SOURCE}",
                f"- 品牌数量：{len(brands)}",
                f"- 车型数量：{len(rows)}",
                f"- 写入/更新：{updated}",
                f"- 原始载荷哈希：{payload_hash}",
                f"- 原始文件：{raw_path}",
                "",
                "## 处理结论",
                "",
                "本次撞库结果已写入 MMN 车型资产主库。前端车型库仅展示 MMN 品牌与车型资产，外部来源名称不在用户侧展示。",
                "",
                "## 样例车型",
                "",
                *[f"- {row['brand_name']} / {row['model_name']}" for row in rows[:40]],
                "",
            ]
        )
    )
    return report


def run_sync(url: str) -> dict:
    captured_at = now_iso()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    raw, final_url = fetch_public_tree(url)
    payload_hash = hashlib.sha256(raw).hexdigest()
    raw_path = save_raw(raw, captured_at, payload_hash)
    payload = json.loads(raw.decode("utf-8"))
    if payload.get("returncode") not in {0, "0"}:
        raise RuntimeError(f"公开标准源返回异常：{payload.get('message')}")
    rows = flatten_tree(payload)
    if not rows:
        raise RuntimeError("未解析到品牌车型树。")
    with sqlite3.connect(DB_PATH) as conn:
        ensure_schema(conn)
        updated = upsert_assets(conn, rows, captured_at, final_url, payload_hash)
        report = write_report(rows, captured_at, final_url, payload_hash, raw_path, updated)
        run_id = stable_id("mmn-vehicle-sync", captured_at, payload_hash)
        conn.execute(
            """
            insert into mmn_vehicle_asset_sync_runs
            (id, source_label, source_url, captured_at, raw_payload_hash, brand_count, model_count, inserted_or_updated, report_path, status, error)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, 'done', '')
            """,
            (run_id, ASSET_SOURCE, final_url, captured_at, payload_hash, len({x["brand_name"] for x in rows}), len(rows), updated, str(report)),
        )
    return {
        "ok": True,
        "captured_at": captured_at,
        "brand_count": len({x["brand_name"] for x in rows}),
        "model_count": len(rows),
        "updated_count": updated,
        "report": str(report),
        "raw_payload_hash": payload_hash,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync MMN vehicle asset catalog")
    parser.add_argument("--source-url", default=os.getenv("MMN_VEHICLE_ASSET_SOURCE_URL", DEFAULT_URL))
    args = parser.parse_args()
    try:
        result = run_sync(args.source_url)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        reports_dir = DATA_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        error_path = reports_dir / f"mmn_vehicle_asset_sync_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        error_path.write_text(f"# MMN车型资产月度撞库失败\n\n- 时间：{now_iso()}\n- 原因：{exc}\n")
        print(json.dumps({"ok": False, "error": str(exc), "report": str(error_path)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
