#!/usr/bin/env python3
import http.server
import csv
import io
import json
import os
import sqlite3
import socketserver
import uuid
import webbrowser
import zipfile
import re
import subprocess
import shutil
import hashlib
import time
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from threading import Timer
from urllib.parse import parse_qs, quote, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import urllib.robotparser as robotparser
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
PORT = 8765
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "commercial_demo.db"
NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
QWEN_DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_DEFAULT_MODEL = "qwen-plus"
QWEN_DEFAULT_FAST_MODEL = "qwen-plus"
QWEN_DEFAULT_DEEP_MODEL = "qwen3.7-max"
DEEPSEEK_DEFAULT_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_DEFAULT_MODEL = "deepseek-chat"
DEEPSEEK_DEFAULT_DEEP_MODEL = "deepseek-reasoner"
OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"
OPENAI_DEFAULT_MODEL = "gpt-5.5"
DONGCHEDI_SALES_BASE = "https://www.dongchedi.com"
SALES_CACHE = {"expires": "", "payload": None}
GLOBAL_SALES_CACHE = {"expires": "", "payload": None}
THAILAND_DB_PATH = ROOT.parent / "thailand-auto-market-data" / "data" / "sqlite" / "thailand_auto_market.db"
SOCIAL_PLUGIN_ID = "dbichmdlbjdeplpkhcejgkakobjbjalc"
SOCIAL_PLUGIN_EXPORT_DIRS = {
    "douyin": Path.home() / "Downloads" / "社媒助手" / "抖音",
    "xiaohongshu": Path.home() / "Downloads" / "社媒助手" / "小红书"
}
SOCIAL_PLUGIN_URLS = {
    "douyin": "https://www.douyin.com/search/%E6%B1%BD%E8%BD%A6%E8%AF%84%E6%B5%8B",
    "xiaohongshu": "https://www.xiaohongshu.com/search_result?keyword=%E6%B1%BD%E8%BD%A6%E8%AF%84%E6%B5%8B"
}
NODE_CANDIDATES = [
    os.getenv("NODE_BINARY"),
    "/Users/ellis/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node",
    shutil.which("node")
]

def db():
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.executescript("""
        create table if not exists organizations (
            id text primary key,
            name text not null,
            created_at text not null
        );
        create table if not exists users (
            id text primary key,
            org_id text not null,
            email text not null,
            name text not null,
            created_at text not null,
            unique(org_id, email)
        );
        create table if not exists learning_cases (
            id text primary key,
            org_id text not null,
            user_id text not null,
            edition text not null default 'china',
            model text not null,
            label text not null,
            conclusion text,
            recommendation text,
            evidence text,
            platform text,
            kpi text,
            stage text,
            saved_at text not null
        );
        create table if not exists workspace_contexts (
            org_id text primary key,
            hierarchy_json text not null,
            knowledge_json text not null,
            model_router_json text not null,
            updated_at text not null
        );
        create table if not exists project_snapshots (
            id text primary key,
            org_id text not null,
            user_id text not null,
            edition text not null default 'china',
            brand text,
            model text,
            project text,
            data_version text,
            payload_json text not null,
            created_at text not null
        );
        create table if not exists vertical_import_batches (
            id text primary key,
            platform text not null,
            filename text not null,
            file_hash text not null,
            periods_json text not null,
            model_count integer not null default 0,
            item_count integer not null default 0,
            imported_at text not null,
            parser_version text not null,
            unique(platform, file_hash)
        );
        create table if not exists vehicle_assets (
            id text primary key,
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
            unique(platform, model_name)
        );
        create table if not exists vertical_rank_assets (
            id text primary key,
            platform text not null,
            period text not null,
            own_model text not null,
            competitor_model text not null,
            positive_rank integer,
            negative_rank integer,
            compare_share real,
            source_file text not null,
            file_hash text not null,
            sheet text,
            parse_mode text,
            first_seen_at text not null,
            updated_at text not null,
            unique(platform, period, own_model, competitor_model)
        );
        create unique index if not exists idx_vertical_rank_assets_unique
        on vertical_rank_assets(platform, period, own_model, competitor_model);
        create unique index if not exists idx_vehicle_assets_unique
        on vehicle_assets(platform, model_name);
        create table if not exists vertical_ai_learnings (
            id text primary key,
            platform text not null,
            model_name text not null,
            period text,
            source_file text,
            summary_text text not null,
            knowledge_json text not null,
            created_at text not null,
            unique(platform, model_name, period)
        );
        create table if not exists model_judgment_assets (
            id text primary key,
            edition text not null default 'china',
            brand_name text,
            model_name text not null,
            dimension text,
            viewpoint text,
            attribution text,
            strategy_implication text,
            evidence_needed text,
            source_text text not null,
            tags_json text not null default '[]',
            confidence text,
            knowledge_json text not null,
            created_at text not null,
            updated_at text not null
        );
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
        create table if not exists founder_speech_archives (
            id text primary key,
            edition text not null default 'china',
            brand text not null,
            person text not null,
            role text,
            published_at text,
            platform text,
            source_name text,
            source_url text not null,
            event_type text,
            original_summary text,
            core_viewpoint text,
            language_style_tags_json text not null default '[]',
            distillable_talk text,
            prompt_template text,
            risk_note text,
            model_trace_json text not null default '{}',
            captured_at text not null,
            raw_payload_hash text not null,
            unique(edition, source_url, person, raw_payload_hash)
        );
        create table if not exists founder_crawl_runs (
            id text primary key,
            edition text not null default 'china',
            week_start text,
            week_end text,
            status text not null,
            source_count integer not null default 0,
            item_count integer not null default 0,
            error_json text not null default '[]',
            started_at text not null,
            finished_at text
        );
        """)
        ensure_column(conn, "learning_cases", "edition", "text not null default 'china'")
        ensure_column(conn, "project_snapshots", "edition", "text not null default 'china'")
        conn.execute("update vertical_rank_assets set compare_share=compare_share/100 where compare_share > 1")

def now():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

VERTICAL_PLATFORMS = {"汽车之家", "懂车帝"}
VERTICAL_ASSET_PARSER_VERSION = "vertical-rank-asset-v2"

def ensure_column(conn, table, column, ddl):
    cols = [row["name"] for row in conn.execute(f"pragma table_info({table})").fetchall()]
    if column not in cols:
        conn.execute(f"alter table {table} add column {column} {ddl}")

def edition_from(value):
    return "global" if value == "global" else "china"

def scoped_org_id(org_id, edition):
    return f"{org_id}::{edition_from(edition)}"

def format_int(value):
    try:
        return f"{int(value):,}"
    except Exception:
        return str(value or "—")

def stable_id(*parts):
    text = "|".join(str(x or "") for x in parts)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

def file_hash(data):
    return hashlib.sha256(data).hexdigest()

def infer_brand_from_model(model):
    text = str(model or "")
    brand_rules = [
        ("firefly", "firefly"),
        ("萤火虫", "firefly"),
        ("MG", "MG"),
        ("QQ冰淇淋", "奇瑞"),
        ("QQ3", "奇瑞"),
        ("QQ", "奇瑞"),
        ("RAV4", "丰田"),
        ("T-ROC", "大众"),
        ("探歌", "大众"),
        ("smart", "smart"),
        ("精灵", "smart"),
        ("沃尔沃", "沃尔沃"),
        ("Volvo", "沃尔沃"),
        ("EX90", "沃尔沃"),
        ("XC60", "沃尔沃"),
        ("XC90", "沃尔沃"),
        ("S90", "沃尔沃"),
        ("阿维塔", "阿维塔"),
        ("E5 Sportback", "奥迪"),
        ("E5", "奥迪"),
        ("奥迪", "奥迪"),
        ("Audi", "奥迪"),
        ("iX3", "宝马"),
        ("i3", "宝马"),
        ("i5", "宝马"),
        ("宝马", "宝马"),
        ("BMW", "宝马"),
        ("奔驰", "奔驰"),
        ("Mercedes", "奔驰"),
        ("吉利几何", "吉利"),
        ("银河", "吉利银河"),
        ("星愿", "吉利"),
        ("星瑞", "吉利"),
        ("星越", "吉利"),
        ("博越", "吉利"),
        ("缤越", "吉利"),
        ("缤瑞", "吉利"),
        ("帝豪", "吉利"),
        ("熊猫", "吉利"),
        ("翼真", "吉利"),
        ("领克", "领克"),
        ("ZEEKR", "极氪"),
        ("Zeekr", "极氪"),
        ("极氪", "极氪"),
        ("001", "极氪"),
        ("7X", "极氪"),
        ("8X", "极氪"),
        ("9X", "极氪"),
        ("智己", "智己"),
        ("小米", "小米汽车"),
        ("理想", "理想"),
        ("问界", "问界"),
        ("蔚来", "蔚来"),
        ("零跑", "零跑"),
        ("小鹏", "小鹏"),
        ("比亚迪", "比亚迪"),
        ("海鸥", "比亚迪"),
        ("海豚", "比亚迪"),
        ("海狮", "比亚迪"),
        ("秦", "比亚迪"),
        ("元", "比亚迪"),
        ("腾势", "腾势"),
        ("深蓝", "深蓝"),
        ("长安启源", "长安启源"),
        ("长安", "长安"),
        ("极狐", "极狐"),
        ("五菱", "五菱"),
        ("宏光", "五菱"),
        ("缤果", "五菱"),
        ("纳米", "东风纳米"),
        ("AION", "广汽埃安"),
        ("埃安", "广汽埃安"),
        ("凯美瑞", "丰田"),
        ("RAV4", "丰田"),
        ("汉兰达", "丰田"),
        ("赛那", "丰田"),
        ("别克", "别克"),
        ("GL8", "别克"),
        ("途昂", "大众"),
        ("途观", "大众"),
        ("速腾", "大众"),
        ("探岳", "大众"),
        ("途岳", "大众"),
        ("朗逸", "大众"),
        ("瑞虎", "奇瑞"),
        ("风云", "奇瑞"),
        ("日产", "日产"),
        ("MG", "MG"),
        ("smart", "smart"),
        ("Model", "特斯拉"),
    ]
    for key, brand in brand_rules:
        if key in text:
            return brand
    return "待确认品牌"

KNOWN_BRANDS = {
    "沃尔沃", "阿维塔", "广汽埃安", "奇瑞", "别克", "奥迪", "宝马", "奔驰", "本田",
    "智己", "小米汽车", "特斯拉", "蔚来", "极氪", "理想", "问界", "比亚迪",
    "吉利", "吉利银河", "领克", "零跑", "小鹏", "广汽传祺", "腾势", "深蓝",
    "长安", "长安启源", "五菱", "丰田", "大众", "日产", "MG", "smart", "firefly", "待确认品牌"
}

def valid_brand_name(brand, model=""):
    b = str(brand or "").strip()
    m = str(model or "").strip()
    if not b or b not in KNOWN_BRANDS:
        return False
    if b == m:
        return False
    if re.search(r"[0-9]|PLUS|PRO|MAX|GT|EV|PHEV|HEV|DM-i|DM-p|e-tron|Sportback|Hyper", b, re.I):
        return False
    return True

def corrected_brand_name(brand, model):
    b = str(brand or "").strip()
    return b if valid_brand_name(b, model) else infer_brand_from_model(model)

def social_platform(value):
    return "xiaohongshu" if value in ("xiaohongshu", "xhs", "小红书") else "douyin"

def latest_social_export(platform):
    folder = SOCIAL_PLUGIN_EXPORT_DIRS[social_platform(platform)]
    files = sorted(folder.glob("*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True) if folder.exists() else []
    return files[0] if files else None

def social_plugin_manifest():
    base = Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "Default" / "Extensions" / SOCIAL_PLUGIN_ID
    versions = sorted([p for p in base.glob("*") if (p / "manifest.json").exists()], reverse=True) if base.exists() else []
    if not versions:
        return None
    path = versions[0] / "manifest.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    return {"path": str(path), "id": SOCIAL_PLUGIN_ID, "version": data.get("version"), "externallyConnectable": bool(data.get("externally_connectable"))}

def social_plugin_status():
    manifest = social_plugin_manifest()
    platforms = {}
    for key, folder in SOCIAL_PLUGIN_EXPORT_DIRS.items():
        files = sorted(folder.glob("*.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True) if folder.exists() else []
        latest = files[0] if files else None
        platforms[key] = {
            "folder": str(folder),
            "count": len(files),
            "latestFile": latest.name if latest else "",
            "latestPath": str(latest) if latest else "",
            "latestMtime": datetime.fromtimestamp(latest.stat().st_mtime).isoformat(timespec="seconds") if latest else ""
        }
    return {
        "installed": bool(manifest),
        "manifest": manifest,
        "mode": "export-folder-bridge",
        "note": "当前插件未开放 externally_connectable，MMN 先通过打开采集页 + 同步插件导出 Excel 完成对接。",
        "platforms": platforms
    }

def thailand_market_payload():
    cached = GLOBAL_SALES_CACHE.get("payload")
    expires = GLOBAL_SALES_CACHE.get("expires") or ""
    if cached and expires > now():
        return cached
    if not THAILAND_DB_PATH.exists():
        return {
            "ok": True,
            "status": "pending",
            "source": "泰国汽车市场月度采集",
            "updatedAt": now(),
            "note": "泰国市场数据库尚未生成，请先运行 thailand-auto-market-data 月度更新。",
            "items": [
                {"text": "Thailand Market｜等待泰国月度市场数据入库"},
                {"text": "Global RAG｜海外市场资料库等待首批数据导入"}
            ],
            "errors": []
        }
    items = []
    errors = []
    try:
        conn = sqlite3.connect(THAILAND_DB_PATH)
        conn.row_factory = sqlite3.Row
        latest = conn.execute(
            "select * from monthly_market_table order by period desc limit 1"
        ).fetchone()
        if latest:
            period = latest["period"]
            total_sales = latest["total_sales"]
            bev_sales = latest["bev_sales"]
            production = latest["production_volume"]
            registration = latest["new_registration_volume"]
            bev_registration = latest["bev_registration_volume"]
            coverage = latest["source_coverage"] or "泰国月度市场数据"
            market_bits = []
            if total_sales is not None:
                market_bits.append(f"总销量 {format_int(total_sales)}")
            if bev_sales is not None:
                market_bits.append(f"BEV销量 {format_int(bev_sales)}")
            if production is not None:
                market_bits.append(f"产量 {format_int(production)}")
            if market_bits:
                items.append({
                    "label": "Thailand Market",
                    "month": period,
                    "text": f"Thailand Market｜{period}｜{'｜'.join(market_bits)}｜来源 {coverage}"
                })
            if registration is not None:
                reg_bits = [f"新注册 {format_int(registration)}"]
                if bev_registration is not None:
                    reg_bits.append(f"BEV注册 {format_int(bev_registration)}")
                items.append({
                    "label": "Thailand Registration",
                    "month": period,
                    "text": f"Thailand Registration｜{period}｜{'｜'.join(reg_bits)}｜注册量不等于销量"
                })
            brand_rows = conn.execute(
                "select period, brand_name, sales_volume, rank from brand_sales_records where period=? order by rank, sales_volume desc limit 5",
                (period,)
            ).fetchall()
            if brand_rows:
                brands = "、".join([f"{r['brand_name']} {format_int(r['sales_volume'])}" for r in brand_rows[:3]])
                items.append({
                    "label": "Thailand Brand Top",
                    "month": period,
                    "text": f"Thailand Brand Top｜{period}｜前三：{brands}"
                })
        conn.close()
    except Exception as exc:
        errors.append(str(exc))
    if not items:
        items = [
            {"text": "Thailand Market｜已接入泰国数据底座，等待公开月报或授权文件导入"},
            {"text": "Global RAG｜海外汽车市场数据将进入 MMN RAG 知识库"}
        ]
    payload = {
        "ok": True,
        "status": "local" if not errors else "limited",
        "source": "泰国汽车市场月度采集",
        "updatedAt": now(),
        "note": "出海版当前优先展示泰国月度市场宽表；注册量与销量分开展示。",
        "items": items,
        "errors": errors[:4]
    }
    GLOBAL_SALES_CACHE["payload"] = payload
    GLOBAL_SALES_CACHE["expires"] = (datetime.utcnow() + timedelta(minutes=30)).isoformat(timespec="seconds") + "Z"
    return payload

def parse_dongchedi_sales_page(path, label):
    url = DONGCHEDI_SALES_BASE + path
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
    )
    html = urlopen(req, timeout=12).read().decode("utf-8", "ignore")
    match = re.search(r'<script[^>]*>(\{.*?"page"\s*:\s*"/leaderboard/new_sales".*?\})</script>', html, re.S)
    if not match:
        raise ValueError(f"未在懂车帝页面解析到 {label} 销量数据")
    data = json.loads(match.group(1))
    page_props = data.get("props", {}).get("pageProps", {})
    rank_data = page_props.get("rankData", {})
    rows = rank_data.get("list") or []
    if not rows:
        raise ValueError(f"懂车帝 {label} 榜单为空")
    title_match = re.search(r"<title>(\d{4}年\d{2}月).*?销量榜", html)
    month = title_match.group(1) if title_match else "最新月份"
    top = rows[:3]
    top_text = "、".join([f"{x.get('series_name','—')} {format_int(x.get('count'))}" for x in top])
    top10_total = sum([int(x.get("count") or 0) for x in rows[:10]])
    return {
        "label": label,
        "month": month,
        "sourceUrl": url,
        "top10Total": top10_total,
        "top3": [
            {
                "rank": x.get("rank"),
                "name": x.get("series_name", ""),
                "brand": x.get("sub_brand_name") or x.get("brand_name") or "",
                "sales": int(x.get("count") or 0)
            }
            for x in top
        ],
        "text": f"{month} {label}Top10合计 {format_int(top10_total)}｜前三：{top_text}"
    }

def dongchedi_sales_payload():
    cached = SALES_CACHE.get("payload")
    expires = SALES_CACHE.get("expires") or ""
    if cached and expires > now():
        return cached
    latest_candidates = [
        ROOT.parent / "mmn-dcd-sales-crawler" / "data" / "processed" / "latest.json",
        DATA_DIR / "dongchedi_sales" / "latest.json"
    ]
    latest_path = next((path for path in latest_candidates if path.exists()), None)
    if latest_path:
        try:
            latest = json.loads(latest_path.read_text(encoding="utf-8"))
            items = []
            if latest.get("items"):
                grouped = {}
                for row in latest.get("items", []):
                    key = row.get("rank_type") or "series"
                    grouped.setdefault(key, []).append(row)
                for key, rows in list(grouped.items())[:8]:
                    rows = sorted(rows, key=lambda x: x.get("rank") or 999)
                    top = rows[:3]
                    total_rows = rows[:10]
                    total = sum(int(x.get("sales_volume") or 0) for x in total_rows)
                    total_label = f"Top{len(total_rows)}合计"
                    top_text = "、".join([f"{x.get('series_name','—')} {format_int(x.get('sales_volume'))}" for x in top])
                    label_map = {
                        "series": "全国零售榜", "car": "全部轿车", "micro_car": "微型车", "small_car": "小型车",
                        "compact_car": "紧凑型车", "mid_car": "中型车", "mid_large_car": "中大型车", "large_car": "大型车",
                        "suv": "全部SUV", "small_suv": "小型SUV", "compact_suv": "紧凑型SUV", "mid_suv": "中型SUV",
                        "mid_large_suv": "中大型SUV", "large_suv": "大型SUV", "mpv": "全部MPV",
                        "small_mpv": "小型MPV", "compact_mpv": "紧凑型MPV", "mid_mpv": "中型MPV",
                        "mid_large_mpv": "中大型MPV", "large_mpv": "大型MPV", "new_energy": "全部新能源",
                        "ev": "纯电动", "phev": "插电式混动", "erev": "增程式"
                    }
                    label = label_map.get(key, key)
                    month = (top[0].get("period_start") or "最新周期")[:7]
                    items.append({
                        "label": label,
                        "month": month,
                        "sourceUrl": top[0].get("source_url", DONGCHEDI_SALES_BASE + "/sales"),
                        "top10Total": total,
                        "top3": [{"rank": x.get("rank"), "name": x.get("series_name", ""), "brand": x.get("brand_name") or "", "sales": int(x.get("sales_volume") or 0)} for x in top],
                        "text": f"{month} {label}{total_label} {format_int(total)}｜前三：{top_text}"
                    })
            for record in latest.get("records", [])[:8]:
                rows = record.get("items", [])
                if not rows:
                    continue
                top = rows[:3]
                total = int(record.get("top_n_total") or sum(int(x.get("sales") or 0) for x in rows[:10]))
                top_text = "、".join([f"{x.get('series_name','—')} {format_int(x.get('sales'))}" for x in top])
                items.append({
                    "label": record.get("segment", ""),
                    "month": record.get("month", ""),
                    "sourceUrl": top[0].get("source_url", DONGCHEDI_SALES_BASE + "/sales"),
                    "top10Total": total,
                    "top3": [{"rank": x.get("rank"), "name": x.get("series_name", ""), "brand": x.get("sub_brand_name") or x.get("brand_name") or "", "sales": int(x.get("sales") or 0)} for x in top],
                    "text": f"{record.get('month','最新月份')} {record.get('segment','销量榜')}Top10合计 {format_int(total)}｜前三：{top_text}"
                })
            if items:
                payload = {
                    "ok": True,
                    "status": "local",
                    "source": "懂车帝销量榜定时采集",
                    "updatedAt": latest.get("crawl_at") or now(),
                    "note": "当前优先展示本地定时采集结果；完整全量榜单需接入分页或授权接口。",
                    "items": items,
                    "errors": []
                }
                SALES_CACHE["payload"] = payload
                SALES_CACHE["expires"] = (datetime.utcnow() + timedelta(minutes=30)).isoformat(timespec="seconds") + "Z"
                return payload
        except Exception:
            pass
    segments = [
        ("全国零售榜", "/sales/sale-x-x-x-x-x-x"),
        ("轿车市场", "/sales/sale-jc-x-x-x-x-x"),
        ("SUV市场", "/sales/sale-suv-x-x-x-x-x"),
        ("MPV市场", "/sales/sale-mpv-x-x-x-x-x"),
        ("新能源市场", "/sales/sale-energy-x-x-x-x-x")
    ]
    items, errors = [], []
    for label, path in segments:
        try:
            items.append(parse_dongchedi_sales_page(path, label))
        except Exception as exc:
            errors.append(f"{label}: {exc}")
    status = "live" if items else "limited"
    if not items:
        items = [
            {"label": "懂车帝销量榜", "month": "最新月份", "sourceUrl": DONGCHEDI_SALES_BASE + "/sales", "top10Total": 0, "top3": [], "text": "懂车帝销量榜接入受限：等待实时页面或正式数据接口"},
            {"label": "细分市场", "month": "最新月份", "sourceUrl": DONGCHEDI_SALES_BASE + "/sales", "top10Total": 0, "top3": [], "text": "细分车型市场总量需要分页/授权接口，当前先保留结构化入口"}
        ]
    payload = {
        "ok": True,
        "status": status,
        "source": "懂车帝销量榜",
        "updatedAt": now(),
        "note": "当前使用懂车帝页面首屏服务端数据；页面只稳定暴露Top10，完整市场总销量需接入分页或授权接口。",
        "items": items,
        "errors": errors[:4]
    }
    SALES_CACHE["payload"] = payload
    SALES_CACHE["expires"] = (datetime.utcnow() + timedelta(minutes=30)).isoformat(timespec="seconds") + "Z"
    return payload

def default_workspace(org_name="演示客户"):
    return {
        "hierarchy": {
            "group": org_name,
            "brands": [
                {
                    "name": "智己汽车",
                    "role": "集团可见 / 品牌可见",
                    "models": [
                        {"name": "智己LS8", "projects": ["上市期认知战役", "口碑修复追踪"]},
                        {"name": "智己L6", "projects": ["竞品对抗周报"]}
                    ]
                },
                {
                    "name": "上汽奥迪",
                    "role": "集团可见 / 品牌隔离",
                    "models": [
                        {"name": "奥迪E5 Sportback", "projects": ["上市传播复盘"]},
                        {"name": "奥迪E7X", "projects": ["垂媒声量追踪"]}
                    ]
                }
            ],
            "activeScope": "集团空间 / 智己汽车 / 智己LS8 / 上市期认知战役"
        },
        "knowledge": [
            {"tier": "MMN母知识库", "scope": "全客户共享方法论", "items": 128, "storage": "平台只读"},
            {"tier": "客户私有知识库", "scope": f"{org_name} 专属策略资产", "items": 12, "storage": "企业隔离"},
            {"tier": "项目学习库", "scope": "车型项目人工结论和复盘", "items": 0, "storage": "项目隔离"}
        ],
        "modelRouter": [
            {"provider": "OpenAI / ChatGPT", "role": "复杂策略推理与报告生成", "status": "可插拔"},
            {"provider": "豆包 / 千问 / DeepSeek / Kimi", "role": "国内网络可用的通用模型路由", "status": "预留"},
            {"provider": "客户私有模型", "role": "私有化或专属云部署", "status": "预留"},
            {"provider": "无模型规则引擎", "role": "基础评分、排名、分类、权限判断", "status": "已在本地运行"}
        ]
    }

def ensure_workspace(conn, org_id, org_name):
    row = conn.execute("select * from workspace_contexts where org_id=?", (org_id,)).fetchone()
    if row:
        return row
    seed = default_workspace(org_name)
    conn.execute(
        "insert into workspace_contexts values (?,?,?,?,?)",
        (
            org_id,
            json.dumps(seed["hierarchy"], ensure_ascii=False),
            json.dumps(seed["knowledge"], ensure_ascii=False),
            json.dumps(seed["modelRouter"], ensure_ascii=False),
            now()
        )
    )
    return conn.execute("select * from workspace_contexts where org_id=?", (org_id,)).fetchone()

FOUNDER_PEOPLE = [
    {"brand": "理想", "person": "李想", "role": "创始人/CEO"},
    {"brand": "小鹏", "person": "何小鹏", "role": "董事长/CEO"},
    {"brand": "小米汽车", "person": "雷军", "role": "创始人/董事长"},
    {"brand": "蔚来", "person": "李斌", "role": "创始人/CEO"},
    {"brand": "零跑", "person": "朱江明", "role": "创始人/董事长"},
    {"brand": "极氪", "person": "安聪慧", "role": "CEO"},
    {"brand": "华为鸿蒙智行", "person": "余承东", "role": "高管"},
    {"brand": "比亚迪", "person": "王传福", "role": "董事长"},
]

FOUNDER_PUBLIC_SOURCES = [
    {"name": "新浪汽车公开资讯", "platform": "媒体报道", "url": "https://auto.sina.com.cn/", "enabled": True},
    {"name": "腾讯汽车公开资讯", "platform": "媒体报道", "url": "https://auto.qq.com/", "enabled": True},
    {"name": "网易汽车公开资讯", "platform": "媒体报道", "url": "https://auto.163.com/", "enabled": True},
]

def shanghai_now():
    return datetime.now(ZoneInfo("Asia/Shanghai"))

def current_natural_week(now_dt=None):
    dt = now_dt or shanghai_now()
    start = (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=6, hours=23, minutes=59, seconds=59)
    return start, end

def robots_allowed(url, user_agent="MMNFounderCrawler/1.0"):
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = robotparser.RobotFileParser()
    try:
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(user_agent, url)
    except Exception:
        return False

def safe_public_fetch(url, rate_limit_seconds=10):
    if not robots_allowed(url):
        raise ValueError("robots.txt 不允许抓取或无法确认权限")
    time.sleep(max(0, rate_limit_seconds))
    req = Request(url, headers={"User-Agent": "MMNFounderCrawler/1.0 (+local compliant research)"})
    try:
        with urlopen(req, timeout=20) as resp:
            status = getattr(resp, "status", 200)
            ctype = resp.headers.get("Content-Type", "")
            data = resp.read(1024 * 512)
    except HTTPError as exc:
        if exc.code in (401, 403, 429):
            raise ValueError(f"公开源拒绝访问：HTTP {exc.code}，已停止，不尝试绕过")
        raise
    text = data.decode("utf-8", errors="ignore")
    lowered = text.lower()
    if any(x in lowered for x in ["captcha", "验证码", "登录后", "付费", "subscribe", "人机验证"]):
        raise ValueError("疑似验证码、登录或付费限制，已停止，不尝试绕过")
    return {"url": url, "status": status, "content_type": ctype, "text": text, "hash": file_hash(data)}

def extract_founder_candidates(payload, week_start, week_end, source):
    text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", " ", payload.get("text") or "", flags=re.I)
    plain = re.sub(r"<[^>]+>", " ", text)
    plain = re.sub(r"\s+", " ", plain)
    items = []
    for person in FOUNDER_PEOPLE:
        idx = plain.find(person["person"])
        if idx < 0 and person["brand"] not in plain:
            continue
        start = max(0, idx - 160 if idx >= 0 else 0)
        excerpt = plain[start:start + 520].strip()
        if not excerpt:
            continue
        topic = "品牌叙事"
        if re.search(r"智驾|自动驾驶|辅助驾驶|技术|芯片|算法|纯电|增程", excerpt):
            topic = "技术表达"
        if re.search(r"价格|权益|订单|交付|销量", excerpt):
            topic = "市场经营"
        if re.search(r"争议|回应|质疑|舆论|事故|危机", excerpt):
            topic = "舆论回应"
        items.append({
            "brand": person["brand"],
            "person": person["person"],
            "role": person["role"],
            "published_at": week_end.date().isoformat(),
            "platform": source.get("platform") or "公开网页",
            "source_name": source.get("name") or urlparse(payload["url"]).netloc,
            "source_url": payload["url"],
            "event_type": topic,
            "original_summary": excerpt[:220],
            "core_viewpoint": "待Qwen清洗摘要",
            "language_style_tags": ["公开表达", topic],
            "distillable_talk": "待DeepSeek蒸馏",
            "prompt_template": f"请参考{person['brand']}{person['person']}的公开表达风格，围绕用户问题、事实证据和行动承诺生成高管IP话术。",
            "risk_note": "待DeepSeek质检",
            "model_trace": {"extractor": "local-compliant-html", "qwen": "reserved", "deepseek": "reserved"},
            "raw_payload_hash": payload["hash"]
        })
    return items

def founder_seed_items():
    captured = now()
    return [
        {"brand":"理想","person":"李想","role":"创始人/CEO","published_at":"2026-06-24","platform":"微博","source_name":"公开表达样例","source_url":"local://founder-seed/li-xiang","event_type":"产品定义","original_summary":"用家庭用户真实场景解释产品取舍，把配置、空间、能耗和智能化放回日常用车任务里讲。","core_viewpoint":"产品表达应从家庭任务出发，而不是堆参数。","language_style_tags":["家庭场景","产品定义","用户价值"],"distillable_talk":"这件事我们先不讲参数，先讲一家人每天怎么用车。","prompt_template":"以李想式家庭场景表达，先讲用户任务，再讲产品取舍，最后讲承诺。","risk_note":"避免把产品定义说成绝对正确，需要承认不同用户场景差异。","model_trace":{"source":"seed"},"raw_payload_hash":stable_id("founder-seed","li-xiang"),"captured_at":captured},
        {"brand":"小鹏","person":"何小鹏","role":"董事长/CEO","published_at":"2026-06-20","platform":"发布会","source_name":"公开表达样例","source_url":"local://founder-seed/he-xiaopeng","event_type":"技术叙事","original_summary":"强调技术路线、长期投入和体验边界，把智能驾驶从参数竞争转成可验证的用户体验。","core_viewpoint":"智能化要讲清长期投入、体验边界和可验证成果。","language_style_tags":["智驾","技术路线","长期主义"],"distillable_talk":"技术不是口号，用户每天敢不敢用、好不好用，才是标准。","prompt_template":"以何小鹏式技术路线表达，明确技术投入、用户体验和边界条件。","risk_note":"避免过度承诺自动驾驶能力。","model_trace":{"source":"seed"},"raw_payload_hash":stable_id("founder-seed","he-xiaopeng"),"captured_at":captured},
        {"brand":"小米汽车","person":"雷军","role":"创始人/董事长","published_at":"2026-06-18","platform":"短视频","source_name":"公开表达样例","source_url":"local://founder-seed/lei-jun","event_type":"用户沟通","original_summary":"用通俗语言降低技术理解门槛，通过个人信誉、工程细节和用户反馈建立品牌亲近感。","core_viewpoint":"复杂技术要转译为用户听得懂的真实体验。","language_style_tags":["用户沟通","工程细节","亲和表达"],"distillable_talk":"我们把复杂的工程问题讲简单，让大家知道每一处改进到底解决什么麻烦。","prompt_template":"以雷军式通俗表达，少术语，多细节，多用户视角。","risk_note":"避免过度个人化承诺，应保留团队和数据依据。","model_trace":{"source":"seed"},"raw_payload_hash":stable_id("founder-seed","lei-jun"),"captured_at":captured}
    ]

def founder_talk_prompt(profile, scene, brief, archives):
    return [
        {"role": "system", "content": (
            "你是MMN汽车营销引擎的高管IP话术生成模块。Qwen负责主控执行、知识调用、结构化输出和常规话术生成。"
            "请基于已归档的公开表达样本生成可直接使用的中文话术。不要声称这是高管本人原话，只能说是风格参考。"
            "输出结构：核心话术、表达拆解、可发布版本、注意事项。"
            + MMN_OUTPUT_STYLE
        )},
        {"role": "user", "content": json.dumps({"profile": profile, "scene": scene, "brief": brief, "archives": archives[:8]}, ensure_ascii=False)}
    ]

def founder_quality_prompt(profile, scene, brief, draft):
    return [
        {"role": "system", "content": (
            "你是MMN汽车营销引擎的DeepSeek策略推理与质检模型。负责观点归因、语言风格蒸馏、舆论风险判断和高管IP Prompt校验。"
            "请检查话术是否符合人物公开表达风格、是否存在过度承诺、事实不明、舆论风险或逻辑断裂。"
            "输出结构：质检结论、风险点、优化建议、最终可用Prompt。"
        )},
        {"role": "user", "content": json.dumps({"profile": profile, "scene": scene, "brief": brief, "draft": draft}, ensure_ascii=False)}
    ]

def save_founder_items(items, edition="china"):
    saved = []
    with db() as conn:
        for item in items:
            item_id = stable_id("founder", edition, item.get("source_url"), item.get("person"), item.get("raw_payload_hash"))
            captured = item.get("captured_at") or now()
            conn.execute("""
                insert into founder_speech_archives
                (id, edition, brand, person, role, published_at, platform, source_name, source_url, event_type, original_summary, core_viewpoint, language_style_tags_json, distillable_talk, prompt_template, risk_note, model_trace_json, captured_at, raw_payload_hash)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(edition, source_url, person, raw_payload_hash) do update set
                  brand=excluded.brand, role=excluded.role, published_at=excluded.published_at, platform=excluded.platform,
                  source_name=excluded.source_name, event_type=excluded.event_type, original_summary=excluded.original_summary,
                  core_viewpoint=excluded.core_viewpoint, language_style_tags_json=excluded.language_style_tags_json,
                  distillable_talk=excluded.distillable_talk, prompt_template=excluded.prompt_template,
                  risk_note=excluded.risk_note, model_trace_json=excluded.model_trace_json, captured_at=excluded.captured_at
            """, (
                item_id, edition, item.get("brand") or "待识别品牌", item.get("person") or "待识别人物", item.get("role") or "",
                item.get("published_at") or "", item.get("platform") or "", item.get("source_name") or "", item.get("source_url") or "",
                item.get("event_type") or "", item.get("original_summary") or "", item.get("core_viewpoint") or "",
                json.dumps(item.get("language_style_tags") or [], ensure_ascii=False), item.get("distillable_talk") or "",
                item.get("prompt_template") or "", item.get("risk_note") or "",
                json.dumps(item.get("model_trace") or {}, ensure_ascii=False), captured, item.get("raw_payload_hash") or stable_id(item)
            ))
            saved.append({"id": item_id, **item, "captured_at": captured})
    return saved

def founder_archive_rows(edition="china", limit=200):
    with db() as conn:
        rows = conn.execute("select * from founder_speech_archives where edition=? order by published_at desc, captured_at desc limit ?", (edition, limit)).fetchall()
    out = []
    for r in rows:
        d = rowdict(r)
        d["language_style_tags"] = json.loads(d.pop("language_style_tags_json") or "[]")
        d["model_trace"] = json.loads(d.pop("model_trace_json") or "{}")
        out.append(d)
    return out

def run_founder_weekly_crawl(edition="china", manual=False):
    week_start, week_end = current_natural_week()
    run_id = stable_id("founder-run", edition, week_start.isoformat(), now(), "manual" if manual else "auto")
    started = now()
    errors, items = [], []
    with db() as conn:
        conn.execute("insert into founder_crawl_runs (id, edition, week_start, week_end, status, started_at) values (?, ?, ?, ?, ?, ?)", (run_id, edition, week_start.date().isoformat(), week_end.date().isoformat(), "running", started))
    for source in FOUNDER_PUBLIC_SOURCES:
        if not source.get("enabled"):
            continue
        try:
            payload = safe_public_fetch(source["url"], rate_limit_seconds=10)
            items.extend(extract_founder_candidates(payload, week_start, week_end, source))
        except Exception as exc:
            errors.append({"source": source.get("name"), "url": source.get("url"), "error": str(exc)})
    if not items:
        items = founder_seed_items()
        errors.append({"source": "fallback", "error": "本次公开源未抓取到可结构化内容，已保留样例数据结构；请补充可访问公开源清单。"})
    saved = save_founder_items(items, edition=edition)
    with db() as conn:
        conn.execute("update founder_crawl_runs set status=?, source_count=?, item_count=?, error_json=?, finished_at=? where id=?", ("done", len(FOUNDER_PUBLIC_SOURCES), len(saved), json.dumps(errors, ensure_ascii=False), now(), run_id))
    return {"ok": True, "runId": run_id, "weekStart": week_start.date().isoformat(), "weekEnd": week_end.date().isoformat(), "items": saved, "errors": errors}

def seconds_until_next_founder_run():
    dt = shanghai_now()
    target = dt.replace(hour=23, minute=0, second=0, microsecond=0)
    days = (6 - dt.weekday()) % 7
    target = target + timedelta(days=days)
    if target <= dt:
        target += timedelta(days=7)
    return max(60, (target - dt).total_seconds())

FOUNDER_TIMER = None
def schedule_founder_weekly_crawl():
    global FOUNDER_TIMER
    delay = seconds_until_next_founder_run()
    def job():
        try:
            run_founder_weekly_crawl(edition="china", manual=False)
        finally:
            schedule_founder_weekly_crawl()
    FOUNDER_TIMER = Timer(delay, job)
    FOUNDER_TIMER.daemon = True
    FOUNDER_TIMER.start()

def rowdict(row):
    return dict(row) if row else None

def env_file_values():
    path = ROOT / ".env"
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, value = s.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values

def env_value(key, default=""):
    return os.getenv(key) or env_file_values().get(key) or default

def qwen_model_for(profile="default"):
    profile = (profile or "default").lower()
    if profile == "deep":
        return env_value("QWEN_DEEP_MODEL", env_value("QWEN_MODEL", QWEN_DEFAULT_DEEP_MODEL))
    if profile == "fast":
        return env_value("QWEN_FAST_MODEL", env_value("QWEN_MODEL", QWEN_DEFAULT_FAST_MODEL))
    return env_value("QWEN_MODEL", QWEN_DEFAULT_MODEL)

def qwen_config(profile="default"):
    api_key = env_value("DASHSCOPE_API_KEY")
    profile = (profile or "default").lower()
    return {
        "configured": bool(api_key),
        "base_url": env_value("QWEN_BASE_URL", QWEN_DEFAULT_BASE_URL).rstrip("/"),
        "model": qwen_model_for(profile),
        "profile": profile,
        "fast_model": qwen_model_for("fast"),
        "deep_model": qwen_model_for("deep")
    }

def deepseek_model_for(profile="default"):
    profile = (profile or "default").lower()
    if profile == "deep":
        return env_value("DEEPSEEK_DEEP_MODEL", env_value("DEEPSEEK_MODEL", DEEPSEEK_DEFAULT_DEEP_MODEL))
    return env_value("DEEPSEEK_MODEL", DEEPSEEK_DEFAULT_MODEL)

def deepseek_config(profile="default"):
    api_key = env_value("DEEPSEEK_API_KEY")
    profile = (profile or "default").lower()
    return {
        "configured": bool(api_key),
        "base_url": env_value("DEEPSEEK_BASE_URL", DEEPSEEK_DEFAULT_BASE_URL).rstrip("/"),
        "model": deepseek_model_for(profile),
        "profile": profile,
        "fast_model": deepseek_model_for("fast"),
        "deep_model": deepseek_model_for("deep")
    }

def openai_config():
    api_key = env_value("OPENAI_API_KEY")
    return {
        "configured": bool(api_key),
        "base_url": env_value("OPENAI_BASE_URL", OPENAI_DEFAULT_BASE_URL).rstrip("/"),
        "model": env_value("OPENAI_MODEL", OPENAI_DEFAULT_MODEL)
    }

def call_qwen(messages, temperature=.35, profile="fast", timeout=None):
    cfg = qwen_config(profile)
    api_key = env_value("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("未配置 DASHSCOPE_API_KEY。请在启动命令或终端环境中配置千问 API Key。")
    payload = json.dumps({
        "model": cfg["model"],
        "messages": messages,
        "temperature": temperature
    }, ensure_ascii=False).encode("utf-8")
    req = Request(
        cfg["base_url"] + "/chat/completions",
        data=payload,
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        request_timeout = timeout or (120 if (profile or "").lower() == "deep" else 45)
        with urlopen(req, timeout=request_timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        if exc.code == 401:
            raise ValueError("千问请求未授权：DASHSCOPE_API_KEY 无效、过期或不属于当前 DashScope 服务。")
        if exc.code == 403:
            raise ValueError("千问请求被拒绝：请检查模型权限或阿里云百炼服务开通状态。")
        raise ValueError(f"千问请求失败：HTTP {exc.code} {detail[:300]}")
    return data["choices"][0]["message"]["content"]

def call_deepseek(messages, temperature=.25, profile="fast", timeout=None, max_tokens=None):
    cfg = deepseek_config(profile)
    api_key = env_value("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("未配置 DEEPSEEK_API_KEY。请在 .env 中配置 DeepSeek API Key。")
    body = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": temperature
    }
    if max_tokens:
        body["max_tokens"] = max_tokens
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = Request(
        cfg["base_url"] + "/chat/completions",
        data=payload,
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        request_timeout = timeout or (90 if (profile or "").lower() == "deep" else 45)
        with urlopen(req, timeout=request_timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        if exc.code == 401:
            raise ValueError("DeepSeek 请求未授权：DEEPSEEK_API_KEY 无效或已过期。")
        if exc.code == 403:
            raise ValueError("DeepSeek 请求被拒绝：请检查账户权限或模型可用状态。")
        raise ValueError(f"DeepSeek 请求失败：HTTP {exc.code} {detail[:300]}")
    choices = data.get("choices") or []
    if not choices:
        raise ValueError("DeepSeek 模型无响应。")
    return choices[0]["message"]["content"]

def node_binary():
    for candidate in NODE_CANDIDATES:
        if candidate and Path(candidate).exists():
            return candidate
    raise ValueError("未找到 Node.js，无法调用 OpenAI 官方 SDK。请安装 Node.js 或配置 NODE_BINARY。")

def openai_prompt_from_messages(messages):
    parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        parts.append(f"{role}:\n{content}")
    return "\n\n".join(parts).strip()

def call_openai(messages, temperature=.35):
    if not openai_config()["configured"]:
        raise ValueError("未配置 OPENAI_API_KEY。请在项目 .env 中配置 OpenAI API Key。")
    runner = ROOT / "scripts" / "ask_openai.mjs"
    if not runner.exists():
        raise ValueError("OpenAI 调用脚本缺失：scripts/ask_openai.mjs")
    env = os.environ.copy()
    for key, value in env_file_values().items():
        env.setdefault(key, value)
    payload = json.dumps({"input": openai_prompt_from_messages(messages)}, ensure_ascii=False)
    proc = subprocess.run(
        [node_binary(), str(runner)],
        input=payload,
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        env=env,
        timeout=90
    )
    if proc.returncode != 0:
        try:
            data = json.loads(proc.stdout or proc.stderr or "{}")
            raise ValueError(data.get("error") or "OpenAI 请求失败。")
        except json.JSONDecodeError:
            raise ValueError((proc.stderr or proc.stdout or "OpenAI 请求失败。").strip())
    data = json.loads(proc.stdout)
    text = (data.get("text") or "").strip()
    if not text:
        raise ValueError("OpenAI 模型无响应。")
    return text

def rule_strategy(context):
    summary = context.get("summary", {})
    breakdown = context.get("breakdown", {})
    labels = breakdown.get("labels") or []
    platforms = breakdown.get("platforms") or []
    top_label = labels[0].get("key") if labels else context.get("drillKey", "核心标签")
    top_platform = platforms[0].get("key") if platforms else "核心平台"
    negative = summary.get("negativeScore", 0)
    positive = summary.get("positiveScore", 0)
    mode = "优先修复" if negative > positive else "资产放大"
    return "\n".join([
        f"核心判断：当前围绕“{top_label}”应采取“{mode}”策略。",
        f"关键触发点：样本量 {summary.get('samples', 0)}，正向分 {positive}，负向风险 {negative}。",
        f"平台动作：优先在 {top_platform} 制作证据型内容，并将高频问题转成FAQ、短视频脚本和销售话术。",
        "证据链：第三方实测、真实车主反馈、官方解释三类素材同步沉淀。",
        "KPI：情绪负向占比下降、目标标签正向声量提升、收藏/询价/试驾线索改善。",
        "数据缺口：如缺少原始评论、字幕、作者类型、互动量和商业化标记，应先补齐。"
    ])

MMN_OUTPUT_STYLE = (
    "请使用MMN专属专业语气：像汽车营销咨询顾问给品牌市场负责人做策略交付。"
    "表达要通俗、明确、有判断，不要AI腔、不要堆概念、不要使用过多emoji或口号。"
    "每个结论必须回答：发生了什么、为什么会这样、下一步先做什么、用什么证据验证。"
    "优先使用短句和清晰小标题；归因分析要把数据现象翻译成用户心智和传播动作。"
    "避免空泛词：赋能、闭环、生态、抓手、矩阵、势能、心智占领，除非后面给出具体动作。"
)

def llm_strategy_prompt(context, engine_name):
    system = (
        f"你是MMN汽车营销引擎中的{engine_name}策略专家。"
        "请基于输入的数据拆解、词云、know-how、learning与RAG引用，生成可执行、可复盘的中文汽车营销建议。"
        "必须包含：核心判断、关键触发点、内容策略、平台动作、证据链、KPI、数据缺口。"
        "不要编造不存在的数据；如果依据不足，请明确说明。"
        + MMN_OUTPUT_STYLE
    )
    user = "请基于以下本地声量拆解生成策略：\n" + json.dumps(context, ensure_ascii=False, indent=2)
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]

def creator_tag_prompt(creator, campaign):
    system = (
        "你是MMN汽车营销引擎的达人策略分析助手。请基于达人账号信息、抓取到的样本内容、当前车型项目，输出可编辑的达人标签。"
        "只返回JSON，不要返回Markdown。字段必须包含："
        "type: review/lifestyle/owner 三选一；"
        "categories: 3-6个中文内容赛道标签；"
        "strengths: 3-5个中文优势标签；"
        "fitStages: 2-4个中文推荐场景；"
        "risk: 一句话风险提示；"
        "costLevel: 高/中高/中/中低/低/待评估；"
        "summary: 一句话说明为什么适合或不适合当前Campaign；"
        "estimatedCity: 如果账号名称、样本或公开常识足以判断则给城市，否则返回空字符串；"
        "estimatedInfluenceRole: KOC/KOL/待核验 三选一；"
        "estimatedInfluenceTier: KOC/踝部/膝部/腰部/肩部/头部/待核验 七选一；"
        "estimatedInfluenceLabel: 例如 MMN估算 · KOL · 腰部、MMN估算 · KOC、待核验；"
        "estimatedFansText: 如果你基于模型知识知道该抖音达人公开粉丝量级，则返回如3300万、180万、8万，否则返回空字符串；"
        "estimatedFansValue: 与estimatedFansText对应的数字估算，例如33000000；不确定则返回0；"
        "publicProfile: 一句话补充该抖音账号的公开定位、常见内容方向或行业认知；"
        "confidence: high/medium/low 三选一。"
        "这是抖音达人库，请优先基于你对抖音公开达人信息的已知知识补充账号画像；"
        "如果没有把握，请返回空字符串或待核验，不要硬编报价和合作历史。"
    )
    user = json.dumps({"creator": creator, "campaign": campaign}, ensure_ascii=False, indent=2)
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]

def model_identity_prompt(models):
    return [
        {"role": "system", "content": (
            "你是MMN汽车车型资产库的品牌归属与车型标准化助手。只返回JSON，不要Markdown。"
            "返回根对象必须是：{\"items\":[...]}。"
            "你要把每个原始车型名归纳为：rawName, normalizedName, brandName, modelFamily, energyType, variantName, canonicalKey, confidence, reason。"
            "品牌名必须是汽车品牌，不是车型。很多中国汽车品牌使用“品牌名+数字/字母”命名车型，例如：阿维塔06的brandName必须是阿维塔，modelFamily/normalizedName必须是阿维塔06；沃尔沃EX90的brandName必须是沃尔沃，modelFamily/normalizedName必须是沃尔沃EX90；蔚来ET5T的brandName必须是蔚来，modelFamily/normalizedName必须是蔚来ET5T；ZEEKR 001的brandName必须是极氪，modelFamily/normalizedName必须是ZEEKR 001。"
            "不要把阿维塔06、阿维塔07、艾瑞泽8、奥迪E5、宝马i3、沃尔沃EX90、蔚来ET5T、ZEEKR 001、ZEEKR 7X这类完整车型名写进brandName。"
            "energyType只能是：BEV、EREV、PHEV、HEV、ICE、UNKNOWN。"
            "注意：纯电、增程、插混/PHEV、燃油版本不能盲目排重；例如同一车型家族下不同能源版本要保留不同canonicalKey。"
            "canonicalKey格式建议：品牌|车型家族|能源类型|关键版本；无法确认能源时用UNKNOWN，但不要编造。"
            "如品牌或能源无法准确判断，confidence返回low，并在reason说明需要人工确认。"
        )},
        {"role": "user", "content": json.dumps({"models": models[:80]}, ensure_ascii=False)}
    ]

def rule_model_identity(raw_name):
    name = str(raw_name or "").strip()
    brand = infer_brand_from_model(name)
    energy = "UNKNOWN"
    if re.search(r"纯电|EV|BEV|e-tron|ID\\.|i3|i5|iX|E5|E7X|E8|E9", name, re.I):
        energy = "BEV"
    if re.search(r"增程|EREV|REV", name, re.I):
        energy = "EREV"
    if re.search(r"插混|PHEV|DM-i|DM-p|DHT|Hi4|混动", name, re.I):
        energy = "PHEV"
    if re.search(r"HEV|双擎", name, re.I):
        energy = "HEV"
    family = re.sub(r"\s*(纯电|增程|插混|PHEV|BEV|EV|HEV|DM-i|DM-p|DHT|e-tron|Sportback|新能源)\s*", " ", name, flags=re.I).strip() or name
    return {
        "rawName": name,
        "normalizedName": name,
        "brandName": brand,
        "modelFamily": family,
        "energyType": energy,
        "variantName": name.replace(family, "").strip() if family != name else "",
        "canonicalKey": "|".join([brand or "UNKNOWN", family or name, energy, ""]),
        "confidence": "medium" if brand and energy != "UNKNOWN" else "low",
        "reason": "本地规则预判，等待Qwen复核"
    }

def display_model_name_under_brand(brand, model):
    b = str(brand or "").strip()
    m = str(model or "").strip()
    aliases = {
        "沃尔沃": ["沃尔沃", "Volvo"],
        "阿维塔": ["阿维塔"],
        "奥迪": ["奥迪", "Audi"],
        "宝马": ["宝马", "BMW"],
        "奔驰": ["奔驰", "Mercedes-Benz", "Mercedes"],
        "蔚来": ["蔚来", "NIO"],
        "智己": ["智己"],
        "极氪": ["极氪"],
        "小米汽车": ["小米"],
        "特斯拉": ["特斯拉", "Tesla"],
        "奇瑞": ["奇瑞"],
        "比亚迪": ["比亚迪"],
        "广汽埃安": ["广汽埃安", "埃安", "AION"],
        "广汽传祺": ["广汽传祺", "传祺"],
        "吉利银河": ["吉利银河", "银河"],
    }
    out = m
    for alias in aliases.get(b, [b]):
        if alias:
            out = re.sub(rf"^{re.escape(alias)}\s*", "", out, flags=re.I)
    return out.strip() or m

def normalize_model_identity_records(records, edition="china", source="model_identity"):
    saved = []
    stamp = now()
    with db() as conn:
        for rec in records:
            raw = str(rec.get("rawName") or rec.get("raw_name") or rec.get("normalizedName") or "").strip()
            if not raw:
                continue
            normalized = str(rec.get("normalizedName") or raw).strip()
            brand = corrected_brand_name(rec.get("brandName"), raw)
            if not brand:
                brand = corrected_brand_name("", normalized)
            family = str(rec.get("modelFamily") or normalized).strip()
            energy = str(rec.get("energyType") or "UNKNOWN").strip().upper()
            if energy not in {"BEV", "EREV", "PHEV", "HEV", "ICE", "UNKNOWN"}:
                energy = "UNKNOWN"
            variant = str(rec.get("variantName") or "").strip()
            canonical = str(rec.get("canonicalKey") or "|".join([brand or "UNKNOWN", family, energy, variant])).strip()
            item_id = stable_id("model-identity", edition, raw, canonical)
            payload = {
                "id": item_id,
                "edition": edition,
                "raw_name": raw,
                "normalized_name": normalized,
                "brand_name": brand,
                "model_family": family,
                "energy_type": energy,
                "variant_name": variant,
                "display_model_name": display_model_name_under_brand(brand, normalized),
                "canonical_key": canonical,
                "confidence": rec.get("confidence") or "low",
                "source": source,
                "qwen_checked": 1 if source == "qwen" else 0,
                "qwen_reason": rec.get("reason") or ""
            }
            conn.execute("""
                insert into model_identity_assets
                (id, edition, raw_name, normalized_name, brand_name, model_family, energy_type, variant_name, canonical_key, confidence, source, qwen_checked, qwen_reason, first_seen_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(edition, raw_name, canonical_key) do update set
                  normalized_name=excluded.normalized_name,
                  brand_name=excluded.brand_name,
                  model_family=excluded.model_family,
                  energy_type=excluded.energy_type,
                  variant_name=excluded.variant_name,
                  confidence=excluded.confidence,
                  source=excluded.source,
                  qwen_checked=max(model_identity_assets.qwen_checked, excluded.qwen_checked),
                  qwen_reason=excluded.qwen_reason,
                  updated_at=excluded.updated_at
            """, (
                item_id, edition, raw, normalized, brand, family, energy, variant, canonical,
                payload["confidence"], source, payload["qwen_checked"], payload["qwen_reason"], stamp, stamp
            ))
            saved.append(payload)
    return saved

def identity_needs_deepseek_review(items):
    if not items:
        return True
    for item in items:
        brand = item.get("brand_name") or item.get("brandName") or ""
        confidence = str(item.get("confidence") or "").lower()
        raw = item.get("raw_name") or item.get("rawName") or item.get("normalized_name") or ""
        if brand == "待确认品牌" or confidence in {"", "low"} or not valid_brand_name(brand, raw):
            return True
    return False

def model_judgment_prompt(text, project):
    return [
        {"role": "system", "content": (
            "你是MMN营销引擎的车型判断资产分析模块。用户会输入一句或一段对某台车的市场/营销/销售判断。"
            "你必须识别品牌、车型、判断维度、核心观点、归因、策略动作、还缺什么证据，并输出JSON。"
            "只返回JSON，不要Markdown。字段：brand_name, model_name, dimension, viewpoint, attribution, strategy_implication, evidence_needed, tags, confidence。"
            "dimension从市场/营销/销售/竞品/内容/渠道/产品/价格/用户心智/综合判断中选择最合适的一项。"
            "不要编造数据；如果车型或品牌不确定，用当前项目兜底并把confidence设为low。"
            + MMN_OUTPUT_STYLE
        )},
        {"role": "user", "content": json.dumps({"input": text, "currentProject": project or {}}, ensure_ascii=False)}
    ]

def local_model_judgment(text, project):
    model = (project or {}).get("model") or ""
    brand = (project or {}).get("brand") or infer_brand_from_model(model)
    mentioned = re.findall(r"[\u4e00-\u9fffA-Za-z0-9][\u4e00-\u9fffA-Za-z0-9 .\\-/]{1,24}", text or "")
    for m in mentioned:
        if any(k in m for k in ("智己", "奥迪", "理想", "小米", "蔚来", "宝马", "奔驰", "比亚迪", "问界", "传祺")):
            model = m.strip(" ，。")
            brand = infer_brand_from_model(model)
            break
    return {
        "brand_name": brand,
        "model_name": model or (project or {}).get("model") or "待识别车型",
        "dimension": "用户心智" if re.search(r"认知|理解|心智|身份|定位", text or "") else "综合判断",
        "viewpoint": str(text or "").strip()[:220],
        "attribution": "当前输入更像一条人工专业判断，需要继续用声量、垂媒、内容和销售线索验证。",
        "strategy_implication": "先把该判断拆成可验证证据，再决定内容、渠道和销售话术优先级。",
        "evidence_needed": "需要补充平台声量、竞品对比、用户评论原文、销售反馈或转化线索。",
        "tags": ["车型判断", "人工观点", "MMN学习"],
        "confidence": "low"
    }

def save_model_judgment_asset(item, source_text, edition="china"):
    stamp = now()
    tags = item.get("tags") if isinstance(item.get("tags"), list) else []
    item_id = stable_id("model-judgment", edition, item.get("brand_name"), item.get("model_name"), item.get("dimension"), source_text)
    knowledge = {
        "id": stable_id("model-judgment-knowledge", item_id),
        "type": "车型判断资产",
        "title": f"{item.get('model_name') or '车型'}｜{item.get('dimension') or '综合判断'}",
        "body": " ".join([str(item.get(k) or "") for k in ("viewpoint", "attribution", "strategy_implication", "evidence_needed")])[:1400],
        "keywords": [item.get("brand_name"), item.get("model_name"), item.get("dimension"), *tags],
        "tags": [item.get("brand_name"), item.get("model_name"), item.get("dimension"), *tags],
        "targets": ["决策驾驶舱", "RAG知识库管理", "MMN策略"],
        "source": "model_judgment_workbench",
        "createdAt": stamp,
        "metadata": {
            "doc_id": item_id,
            "domain": "车型判断资产",
            "module": item.get("dimension") or "综合判断",
            "entity": item.get("model_name") or "",
            "brand": item.get("brand_name") or "",
            "confidence": item.get("confidence") or "low"
        }
    }
    with db() as conn:
        conn.execute("""
            insert into model_judgment_assets
            (id, edition, brand_name, model_name, dimension, viewpoint, attribution, strategy_implication, evidence_needed, source_text, tags_json, confidence, knowledge_json, created_at, updated_at)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(id) do update set
              brand_name=excluded.brand_name,
              model_name=excluded.model_name,
              dimension=excluded.dimension,
              viewpoint=excluded.viewpoint,
              attribution=excluded.attribution,
              strategy_implication=excluded.strategy_implication,
              evidence_needed=excluded.evidence_needed,
              tags_json=excluded.tags_json,
              confidence=excluded.confidence,
              knowledge_json=excluded.knowledge_json,
              updated_at=excluded.updated_at
        """, (
            item_id, edition, item.get("brand_name") or "", item.get("model_name") or "", item.get("dimension") or "",
            item.get("viewpoint") or "", item.get("attribution") or "", item.get("strategy_implication") or "",
            item.get("evidence_needed") or "", source_text, json.dumps(tags, ensure_ascii=False),
            item.get("confidence") or "low", json.dumps(knowledge, ensure_ascii=False), stamp, stamp
        ))
    saved = {
        "id": item_id,
        "knowledge_id": knowledge["id"],
        "edition": edition,
        **item,
        "created_at": stamp,
        "updated_at": stamp
    }
    return saved, knowledge

def parse_json_object(text):
    s = str(text or "").strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.I | re.S).strip()
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"\{.*\}", s, re.S)
        if m:
            return json.loads(m.group(0))
        raise

def fuse_strategy(context, qwen_text=None, deepseek_text=None, openai_text=None, rule_text=None):
    available = []
    if qwen_text:
        available.append(("千问", qwen_text))
    if deepseek_text:
        available.append(("DeepSeek", deepseek_text))
    if openai_text:
        available.append(("ChatGPT", openai_text))
    if rule_text:
        available.append(("规则引擎", rule_text))
    if not available:
        return "MMN融合策略暂不可用：没有可用模型或规则结果。"
    common = "\n".join([f"- {name}：{text[:500]}" for name, text in available])
    return "\n".join([
        "核心判断：综合多模型与规则引擎结果，优先采用可被当前数据和RAG依据支持的策略，不采纳无证据扩展。",
        "共同建议：围绕高声量标签建立“数据拆解 → 证据链 → 平台内容 → KPI复盘”的闭环。",
        "分歧处理：若模型表述不一致，以本地规则引擎的样本量、情绪风险和平台分布为底线，以RAG引用作为策略依据。",
        "平台打法：优先选择当前拆解中的高声量平台，输出短视频/种草/垂媒解释/销售话术四类资产。",
        "内容资产需求：补齐原始评论、标题、字幕、话题、作者类型、互动量和商业化/自然声量标记。",
        "下一步行动：把融合策略保存为Learning，并在下一轮导入后比较情绪占比、标签声量和转化指标变化。",
        "",
        "多模型依据摘要：",
        common
    ])

def col_to_num(col):
    n = 0
    for ch in col:
        n = n * 26 + ord(ch.upper()) - 64
    return n

def parse_cell_ref(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (int(m.group(2)), col_to_num(m.group(1))) if m else (0, 0)

def cell_value(cell, shared):
    t = cell.attrib.get("t")
    v = cell.find("a:v", NS)
    if v is None:
        inline = cell.find("a:is/a:t", NS)
        return inline.text if inline is not None else None
    raw = v.text
    if raw is None:
        return None
    if t == "s":
        return shared[int(raw)] if raw.isdigit() and int(raw) < len(shared) else raw
    try:
        num = float(raw)
        return int(num) if num.is_integer() else num
    except ValueError:
        return raw

def read_xlsx_cells(data):
    z = zipfile.ZipFile(io.BytesIO(data))
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in root.findall("a:si", NS):
            parts = [t.text or "" for t in si.findall(".//a:t", NS)]
            shared.append("".join(parts))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rel_map = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
    sheets = {}
    for s in wb.findall("a:sheets/a:sheet", NS):
        name = s.attrib["name"]
        rid = s.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        target = rel_map.get(rid, "")
        if target.startswith("/"):
            path = target.lstrip("/")
        elif target.startswith("xl/"):
            path = target
        else:
            path = "xl/" + target
        if path not in z.namelist():
            continue
        ws = ET.fromstring(z.read(path))
        cells = {}
        for c in ws.findall(".//a:sheetData/a:row/a:c", NS):
            ref = c.attrib.get("r", "")
            r, col = parse_cell_ref(ref)
            cells[(r, col)] = cell_value(c, shared)
        sheets[name] = cells
    return sheets

def gv(cells, r, c):
    return cells.get((r, c))

def emotion_pos(nsr):
    if nsr >= .55: return "兴奋"
    if nsr >= .25: return "认可"
    if nsr >= .08: return "期待"
    return "信任"

def emotion_neg(nsr, label):
    if nsr <= -.55: return "愤怒" if label in ("质量", "安全") else "后悔"
    if nsr <= -.25: return "失望"
    if label in ("价格", "用车成本"): return "焦虑"
    return "怀疑"

def build_dataset_from_workbook(data, filename):
    sheets = read_xlsx_cells(data)
    cells = sheets.get("数据整理") or next(iter(sheets.values()))
    models = [gv(cells, r, 1) for r in range(10, 16) if isinstance(gv(cells, r, 1), str)]
    if not models:
        raise ValueError("未识别到车型列表。请确认 Excel 中包含“数据整理”页和车型行。")
    own_model = next((m for m in models if "智己" in m), models[0])
    vol_cols = {"垂媒车主口碑":3, "抖音":4, "B站":5, "微信视频号":6, "微博":7, "今日头条":8, "其他":9}
    model_row = {m: 10 + i for i, m in enumerate(models)}
    blocks = {
        "垂媒车主口碑": {"attr_col":30, "start":10, "end":21, "model_start_col":31},
        "抖音": {"attr_col":20, "start":25, "end":36, "model_start_col":21},
        "B站": {"attr_col":30, "start":25, "end":36, "model_start_col":31},
        "微信视频号": {"attr_col":20, "start":40, "end":51, "model_start_col":21},
        "微博": {"attr_col":30, "start":40, "end":51, "model_start_col":31},
    }
    impact = {"安全":5,"质量":5,"辅助/自动驾驶":4.6,"动力与操控":4.4,"价格":4.2,"智能座舱":4.2,"空间":4.0,"舒适性":3.9,"用车成本":3.8,"外观":3.4,"内饰":3.3,"用户服务":3.6,"总体口碑":4.0}
    identity = {"价格":"价格敏感用户","用车成本":"价格敏感用户","空间":"家庭用户","舒适性":"家庭用户","安全":"家庭用户","智能座舱":"科技用户","辅助/自动驾驶":"科技用户","动力与操控":"性能用户","外观":"增量人群","内饰":"增量人群","质量":"目标核心人群","用户服务":"目标核心人群","总体口碑":"目标核心人群"}
    category = {"价格":"价格权益","用车成本":"价格权益","动力与操控":"动力操控","辅助/自动驾驶":"智能化","智能座舱":"智能化","空间":"空间舒适","舒适性":"空间舒适","安全":"安全质量","质量":"安全质量","外观":"造型设计","内饰":"造型设计","用户服务":"服务体验","总体口碑":"整体口碑"}
    def intent_for(platform, label, nsr):
        return "高意向" if platform in ("抖音","微博","垂媒车主口碑") or label in ("价格","质量","安全","辅助/自动驾驶") and nsr < .1 else "中意向"
    def growth_for(platform, label):
        base = {"抖音":1.35,"微博":1.20,"微信视频号":1.15,"B站":1.10,"垂媒车主口碑":1.05,"今日头条":1.05,"其他":1.0}.get(platform, 1.0)
        if label in ("智能座舱","辅助/自动驾驶"): base += .12
        if label in ("质量","安全"): base += .08
        return round(base, 2)
    def comp_for(label):
        if label in ("价格","动力与操控","辅助/自动驾驶","智能座舱"): return 5
        if label in ("外观","空间","舒适性","质量","安全"): return 4
        return 3
    rows = []
    for platform, b in blocks.items():
        for mi, model in enumerate(models):
            vol = gv(cells, model_row[model], vol_cols[platform]) or 0
            attrs = []
            for r in range(b["start"], b["end"] + 1):
                label = gv(cells, r, b["attr_col"])
                nsr = gv(cells, r, b["model_start_col"] + mi)
                if label and isinstance(nsr, (int, float)):
                    attrs.append((label, float(nsr)))
            if not attrs or not vol:
                continue
            per_attr = float(vol) / len(attrs)
            for label, nsr in attrs:
                pos, neg = round(max(0, (1 + nsr) / 2 * per_attr)), round(max(0, (1 - nsr) / 2 * per_attr))
                common = [model, "本品" if model == own_model else "竞品", platform, category.get(label, label), label]
                meta = [identity.get(label, "目标核心人群"), intent_for(platform, label, nsr), impact.get(label, 3.5), growth_for(platform, label), comp_for(label)]
                if pos:
                    rows.append(common + [emotion_pos(nsr), meta[0], meta[1], pos, meta[2], meta[3], meta[4]])
                if neg:
                    rows.append(common + [emotion_neg(nsr, label), meta[0], meta[1], neg, meta[2], meta[3], meta[4]])
    platforms = {"抖音":1.25,"小红书":1.15,"微博":1.1,"懂车帝":1.2,"汽车之家":1.15,"微信":1.05,"B站":1.1,"线下活动":1.3,"垂媒车主口碑":1.25,"微信视频号":1.08,"今日头条":1.05,"其他":0.95}
    return {
        "datasetVersion": "xlsx_" + re.sub(r"[^0-9A-Za-z一-龥]+", "_", filename)[:40],
        "sourceNote": f"已从《{filename}》导入，识别车型：{'、'.join(models)}。",
        "config": {"project": f"{own_model}认知诊断｜Excel导入", "brand": own_model, "model": own_model, "competitor": " / ".join([m for m in models if m != own_model]), "targetIdentity": "目标核心人群", "budget": 800, "priorityThreshold": 60, "riskThreshold": 500},
        "platforms": platforms,
        "rows": rows,
        "models": models
    }

def sheet_rows(cells):
    if not cells:
        return []
    max_r = max(r for r, _ in cells)
    max_c = max(c for _, c in cells)
    return [[gv(cells, r, c) for c in range(1, max_c + 1)] for r in range(1, max_r + 1)]

def find_header(rows):
    title_keys = ("标题", "视频标题", "视频描述", "内容标题", "笔记标题", "作品标题", "title")
    for idx, row in enumerate(rows[:30]):
        texts = [str(x or "").strip().lower() for x in row]
        if any(any(k.lower() in t for k in title_keys) for t in texts):
            return idx
    return 0

def col_index(headers, keys):
    for i, h in enumerate(headers):
        s = str(h or "").strip().lower()
        if any(k.lower() in s for k in keys):
            return i
    return None

def col_index_exact(headers, keys):
    normalized = [str(h or "").strip().lower() for h in headers]
    for key in keys:
        k = key.lower()
        for i, h in enumerate(normalized):
            if h == k:
                return i
    return col_index(headers, keys)

def num(v):
    if isinstance(v, (int, float)):
        return v
    s = str(v or "").replace(",", "").strip()
    m = re.search(r"[-+]?\d+(\.\d+)?", s)
    return float(m.group(0)) if m else 0

def share_num(v):
    n = num(v)
    if not n:
        return 0
    if isinstance(v, str) and "%" in v:
        return n / 100
    return n / 100 if n > 1 else n

def classify_video_title(title):
    t = str(title or "")
    rules = [
        ("价格权益", "价格|售价|权益|优惠|补贴|定金|盲订|锁单|性价比|贵不贵|值不值|购车|金融"),
        ("上市发布", "上市|发布|首发|发布会|预售|开启交付|交付|亮相|新车|官宣"),
        ("竞品对比", "对比|横评|大战|吊打|不输|胜过|打得过|PK|pk|vs|VS|Model|小米|理想|蔚来|极氪|特斯拉"),
        ("智驾科技", "智驾|智能驾驶|自动驾驶|NOA|城市NOA|辅助驾驶|激光雷达|端到端|泊车|座舱|车机|语音|OTA|芯片"),
        ("续航补能", "续航|电耗|能耗|充电|补能|快充|电池|亏电|长途|高速续航|CLTC"),
        ("动力操控", "动力|加速|零百|操控|底盘|悬架|转向|刹车|麋鹿|赛道|驾驶感"),
        ("空间舒适", "空间|后排|二排|座椅|舒适|家用|家庭|亲子|后备箱|露营|NVH|静谧"),
        ("外观内饰", "外观|颜值|设计|内饰|配色|车漆|轮毂|灯|氛围灯|豪华|质感"),
        ("安全质量", "安全|碰撞|质量|异响|故障|召回|品控|耐久|自燃|刹不住|投诉"),
        ("用户口碑", "车主|真实体验|提车|用车|试驾|测评|长测|口碑|后悔|满意|吐槽"),
        ("流量热点", "爆了|热搜|刷屏|出圈|争议|翻车|雷军|余承东|老板|大事件|热点"),
    ]
    for name, pattern in rules:
        if re.search(pattern, t, re.I):
            return name
    return "其他内容"

def infer_platform(text):
    s = str(text or "").lower()
    if "douyin.com" in s or "抖音" in s:
        return "抖音"
    if "xiaohongshu.com" in s or "小红书" in s or "xhslink" in s:
        return "小红书"
    return ""

def infer_model(text):
    s = str(text or "")
    low = s.lower().replace(" ", "")
    aliases = {
        "智己LS8": "智己LS8",
        "智己L6": "智己L6",
        "小米SU7": "小米SU7",
        "小米YU7": "小米YU7",
        "理想L8": "理想L8",
        "理想新L8": "理想L8",
        "全新理想L8": "理想L8",
        "理想L9": "理想L9",
        "理想L7": "理想L7",
        "Model 3": "Model 3",
        "Model Y": "Model Y",
        "蔚来ET5T": "蔚来ET5T",
        "蔚来ET5": "蔚来ET5",
        "极氪007": "极氪007",
    }
    for p, canonical in aliases.items():
        if p.lower().replace(" ", "") in low:
            return canonical
    brand = r"(智己|理想|蔚来|极氪|小米|特斯拉|问界|小鹏|腾势|领克|比亚迪)"
    m = re.search(brand + r"(?:全新|新款|新)?\s*([A-Za-z]{0,4}\d[A-Za-z0-9]{0,4})", s, re.I)
    return (m.group(1) + m.group(2)).replace(" ", "") if m else ""

def build_video_dataset_from_workbook(data, filename):
    sheets = read_xlsx_cells(data)
    items = []
    for sheet, cells in sheets.items():
        rows = sheet_rows(cells)
        if not rows:
            continue
        hidx = find_header(rows)
        headers = [str(x or "").strip() for x in rows[hidx]]
        title_i = col_index(headers, ("标题", "视频标题", "视频描述", "内容标题", "笔记标题", "作品标题", "title"))
        if title_i is None:
            continue
        platform_i = col_index(headers, ("平台", "来源", "渠道", "app"))
        model_i = col_index(headers, ("车型", "车系", "车款", "model"))
        author_i = col_index_exact(headers, ("达人昵称", "作者", "账号昵称", "昵称", "博主", "达人"))
        date_i = col_index(headers, ("发布时间", "日期", "时间", "发布"))
        like_i = col_index(headers, ("点赞", "赞"))
        comment_i = col_index(headers, ("评论",))
        collect_i = col_index(headers, ("收藏", "收集"))
        share_i = col_index(headers, ("分享", "转发"))
        url_i = col_index(headers, ("链接", "url", "地址"))
        search_i = col_index(headers, ("大家都在搜", "搜索词", "热搜词"))
        topic_i = col_index(headers, ("视频话题", "话题", "标签", "hashtag"))
        play_i = col_index(headers, ("播放", "观看", "浏览", "曝光"))
        for row in rows[hidx + 1:]:
            title = row[title_i] if title_i < len(row) else ""
            if not str(title or "").strip():
                continue
            url = str(row[url_i] if url_i is not None and url_i < len(row) and row[url_i] else "").strip()
            search_text = str(row[search_i] if search_i is not None and search_i < len(row) and row[search_i] else "").strip()
            topic_text = str(row[topic_i] if topic_i is not None and topic_i < len(row) and row[topic_i] else "").strip()
            platform = row[platform_i] if platform_i is not None and platform_i < len(row) else ""
            if not platform:
                platform = infer_platform(" ".join([filename, sheet, url, str(title), topic_text])) or "未知平台"
            model = str(row[model_i] if model_i is not None and model_i < len(row) and row[model_i] else "").strip()
            if not model:
                model = infer_model(" ".join([str(title), search_text, topic_text]))
            item = {
                "platform": str(platform or "未知平台").strip(),
                "model": model,
                "title": str(title).strip(),
                "category": classify_video_title(title),
                "author": str(row[author_i] if author_i is not None and author_i < len(row) and row[author_i] else "").strip(),
                "date": str(row[date_i] if date_i is not None and date_i < len(row) and row[date_i] else "").strip(),
                "likes": num(row[like_i] if like_i is not None and like_i < len(row) else 0),
                "comments": num(row[comment_i] if comment_i is not None and comment_i < len(row) else 0),
                "collects": num(row[collect_i] if collect_i is not None and collect_i < len(row) else 0),
                "shares": num(row[share_i] if share_i is not None and share_i < len(row) else 0),
                "plays": num(row[play_i] if play_i is not None and play_i < len(row) else 0),
                "url": url,
                "sheet": sheet,
                "source": filename
            }
            item["engagement"] = item["likes"] + item["comments"] * 2 + item["collects"] * 1.5 + item["shares"] * 2 + item["plays"] * 0.01
            items.append(item)
    if not items:
        raise ValueError("未识别到视频标题列。请确认 Excel 中包含“标题/视频标题/内容标题”等字段。")
    return {"source": filename, "count": len(items), "items": items}

def creator_type_from_text(text):
    s = str(text or "")
    if re.search(r"车主|提车|用车|日常|真实|分享|Vlog|vlog", s):
        return "owner"
    if re.search(r"生活|露营|亲子|旅行|穿搭|女性|家庭|城市|美学|设计", s):
        return "lifestyle"
    return "review"

def creator_categories_from_text(text):
    s = str(text or "")
    rules = [
        ("智能驾驶", r"智驾|自动驾驶|辅助驾驶|NOA|城区|高速|泊车"),
        ("安全质量", r"安全|质量|事故|碰撞|耐久|故障"),
        ("价格权益", r"价格|优惠|权益|补贴|金融|保值"),
        ("空间舒适", r"空间|舒适|座椅|家庭|亲子|露营"),
        ("用车成本", r"能耗|续航|补能|充电|油耗|电耗|保养"),
        ("外观设计", r"外观|设计|改色|颜值|内饰|座舱"),
        ("性能操控", r"动力|操控|底盘|刹车|加速|麋鹿"),
    ]
    cats = [name for name, pattern in rules if re.search(pattern, s, re.I)]
    return cats[:4] or ["汽车评测"]

def creator_strengths_from_text(text, creator_type):
    base = {
        "review": ["评测内容供给", "车型对比表达", "适合疑虑澄清"],
        "lifestyle": ["场景化种草", "生活方式表达", "适合破圈触达"],
        "owner": ["真实用车视角", "信任感较强", "适合口碑修复"],
    }
    strengths = list(base.get(creator_type, base["review"]))
    if re.search(r"二手|维修|整备|老车", str(text or "")):
        strengths[0] = "用车经验内容"
    return strengths

def creator_influence_tier(platform_key, fans):
    fans = int(num(fans) or 0)
    if platform_key != "douyin" or fans <= 0:
        return {"influenceRole": "待补充", "influenceTier": "待补充", "influenceLabel": "粉丝待补充"}
    if fans < 100000:
        return {"influenceRole": "KOC", "influenceTier": "KOC", "influenceLabel": "KOC"}
    if fans < 200000:
        return {"influenceRole": "KOL", "influenceTier": "踝部", "influenceLabel": "KOL · 踝部"}
    if fans < 500000:
        return {"influenceRole": "KOL", "influenceTier": "膝部", "influenceLabel": "KOL · 膝部"}
    if fans < 1000000:
        return {"influenceRole": "KOL", "influenceTier": "腰部", "influenceLabel": "KOL · 腰部"}
    if fans < 2000000:
        return {"influenceRole": "KOL", "influenceTier": "肩部", "influenceLabel": "KOL · 肩部"}
    return {"influenceRole": "KOL", "influenceTier": "头部", "influenceLabel": "KOL · 头部"}

def build_creator_dataset_from_workbook(data, filename, platform_key="douyin"):
    sheets = read_xlsx_cells(data)
    creators = {}
    for sheet, cells in sheets.items():
        rows = sheet_rows(cells)
        if not rows:
            continue
        hidx = find_header(rows)
        headers = [str(x or "").strip() for x in rows[hidx]]
        author_i = col_index_exact(headers, ("达人昵称", "作者", "账号昵称", "昵称", "博主", "达人", "用户名", "用户昵称"))
        uid_i = col_index(headers, ("达人UID", "UID", "用户ID", "账号ID", "达人ID"))
        link_i = col_index(headers, ("达人链接", "主页链接", "账号链接", "用户链接"))
        title_i = col_index(headers, ("标题", "视频标题", "视频描述", "内容标题", "笔记标题", "作品标题", "title"))
        fans_i = col_index(headers, ("粉丝", "粉丝量", "粉丝数"))
        like_i = col_index(headers, ("点赞", "点赞量", "赞"))
        comment_i = col_index(headers, ("评论", "评论量"))
        collect_i = col_index(headers, ("收藏", "收藏量", "收集"))
        share_i = col_index(headers, ("分享", "分享量", "转发"))
        play_i = col_index(headers, ("播放", "观看", "浏览", "曝光", "推荐量"))
        tag_i = col_index(headers, ("视频标签", "标签", "话题", "hashtag"))
        if author_i is None:
            continue
        for row in rows[hidx + 1:]:
            name = str(row[author_i] if author_i < len(row) and row[author_i] else "").strip()
            if not name:
                continue
            uid = str(row[uid_i] if uid_i is not None and uid_i < len(row) and row[uid_i] else "").strip()
            key = uid or name
            safe_key = re.sub(r"[^A-Za-z0-9_\u4e00-\u9fff]+", "_", key)[:48]
            text = " ".join([
                str(row[title_i] if title_i is not None and title_i < len(row) and row[title_i] else ""),
                str(row[tag_i] if tag_i is not None and tag_i < len(row) and row[tag_i] else ""),
                filename,
            ])
            ctype = creator_type_from_text(text)
            item = creators.setdefault(key, {
                "id": f"plugin_{platform_key}_{safe_key}",
                "name": name,
                "uid": uid,
                "type": ctype,
                "city": "待补充",
                "fans": 0,
                "avgViews": 0,
                "engagementRate": 0,
                "costLevel": "待评估",
                "categories": [],
                "strengths": [],
                "fitStages": ["达人初筛", "Campaign候选"],
                "risk": "插件导入达人，需人工复核账号质量与合作可用性",
                "source": filename,
                "profileUrl": "",
                "sampleTitles": [],
                "sampleCount": 0,
                "engagement": 0,
            })
            if link_i is not None and link_i < len(row) and row[link_i]:
                item["profileUrl"] = str(row[link_i]).strip()
            item["fans"] = max(item["fans"], num(row[fans_i] if fans_i is not None and fans_i < len(row) else 0))
            plays = num(row[play_i] if play_i is not None and play_i < len(row) else 0)
            engagement = (
                num(row[like_i] if like_i is not None and like_i < len(row) else 0)
                + num(row[comment_i] if comment_i is not None and comment_i < len(row) else 0) * 2
                + num(row[collect_i] if collect_i is not None and collect_i < len(row) else 0) * 1.5
                + num(row[share_i] if share_i is not None and share_i < len(row) else 0) * 2
            )
            item["sampleCount"] += 1
            item["avgViews"] += plays
            item["engagement"] += engagement
            if title_i is not None and title_i < len(row) and row[title_i] and len(item["sampleTitles"]) < 8:
                item["sampleTitles"].append(str(row[title_i]).strip())
            item["categories"] = list(dict.fromkeys(item["categories"] + creator_categories_from_text(text)))[:5]
            item["type"] = item["type"] if item["type"] != "review" else ctype
    for item in creators.values():
        n = max(1, item.pop("sampleCount", 1))
        item["avgViews"] = round(item["avgViews"] / n)
        engagement = item.pop("engagement", 0)
        item["engagementRate"] = round(min(18, engagement / max(1, item["avgViews"] * n) * 100), 1) if item["avgViews"] else 0
        item["strengths"] = creator_strengths_from_text(" ".join(item.get("categories", [])), item.get("type"))
        item.update(creator_influence_tier(platform_key, item.get("fans")))
    return {"source": filename, "count": len(creators), "creators": list(creators.values())}

def build_social_plugin_dataset(data, filename, platform_key):
    video_result = None
    video_error = None
    try:
        video_result = build_video_dataset_from_workbook(data, filename)
    except Exception as exc:
        video_error = str(exc)
    creator_result = build_creator_dataset_from_workbook(data, filename, platform_key)
    creators = creator_result.get("creators", [])
    items = video_result.get("items", []) if video_result else []
    if not items and not creators:
        raise ValueError(video_error or "未识别到可导入的内容或达人字段。")
    kind = "creator" if creators and not items else "content_with_creators" if creators else "content"
    return {
        "source": filename,
        "kind": kind,
        "count": len(items),
        "creatorCount": len(creators),
        "items": items,
        "creators": creators,
        "parseNote": "已同时抽取达人画像" if creators else "未发现达人账号字段"
    }

def clean_model_name(v):
    s = re.sub(r"\s+", " ", str(v or "")).strip()
    s = s.replace("MG 4", "MG4").replace("AUDI E7X", "奥迪E7X").replace("大众ID ERA 9X", "ID.ERA 9X")
    return s

def date_label(v):
    if isinstance(v, (int, float)):
        return str(v)
    return re.sub(r"\s+", "", str(v or "")).strip()

def period_order(label):
    s = date_label(label)
    m = re.search(r"(20\d{2})[./-](\d{1,2})[./-](\d{1,2})", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(20\d{2})[./年-]\s*(\d{1,2})(?:月)?(?:\s*至\s*20\d{2}[./年-]\s*\d{1,2}(?:月)?)?$", s)
    if m:
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}"
    m = re.search(r"(\d{1,2})[./-]\d{1,2}[~-](\d{1,2})[./-](\d{1,2})", s)
    if m:
        return f"2026-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m = re.search(r"(\d{1,2})[./-](\d{1,2})", s)
    if m:
        return f"2026-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    return s

def source_platform(filename, sheet_names):
    text = filename + " " + " ".join(sheet_names)
    if any(k in text for k in ("汽车之家", "autohome", "AutoHome")):
        return "汽车之家"
    if any(k in text for k in ("懂车帝", "dongchedi", "DCD", "dcdapp")):
        return "懂车帝"
    if any(k in text for k in ("易车", "yiche", "BitAuto")):
        return "易车"
    return "自动识别"

def infer_vertical_platform(filename, sheet, headers=None, row=None, fallback="自动识别"):
    text = " ".join([filename or "", sheet or "", " ".join(map(str, headers or [])), " ".join(map(str, row or []))])
    if any(k in text for k in ("汽车之家", "autohome", "AutoHome")):
        return "汽车之家"
    if any(k in text for k in ("懂车帝", "dongchedi", "DCD", "dcdapp")):
        return "懂车帝"
    if any(k in text for k in ("易车", "yiche", "BitAuto")):
        return "易车"
    return fallback or "自动识别"

def period_from_text(*parts):
    text = " ".join(str(x or "") for x in parts)
    m = re.search(r"(20\d{2})[./年-]\s*(\d{1,2})[./月-]\s*(\d{1,2})?", text)
    if m:
        if m.group(3):
            return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
        return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}"
    m = re.search(r"(\d{1,2})[./月-]\s*(\d{1,2})[日]?", text)
    if m:
        return f"2026-{int(m.group(1)):02d}-{int(m.group(2)):02d}"
    m = re.search(r"(第?\d{1,2}周|W\d{1,2}|week\s*\d{1,2}|周度|月度|季度)", text, re.I)
    return m.group(1) if m else ""

def cell_at(row, idx):
    return row[idx] if idx is not None and idx < len(row) else ""

def vertical_item_key(item):
    return "|".join(str(item.get(k) or "") for k in ("platform", "period", "ownModel", "competitor", "positiveRank", "negativeRank", "sheet"))

def add_vertical_item(items, *, filename, platform, sheet, period, own, comp, pos=None, neg=None, share=None, note=""):
    own = clean_model_name(own)
    comp = clean_model_name(comp)
    if not own or not comp or own == comp:
        return
    pos_v, neg_v, share_v = num(pos), num(neg), share_num(share)
    if not pos_v and not neg_v:
        return
    items.append({
        "source": filename,
        "platform": platform or "自动识别",
        "period": period or date_label(sheet),
        "periodOrder": period_order(period or sheet),
        "ownModel": own,
        "competitor": comp,
        "positiveRank": int(pos_v) if pos_v else None,
        "negativeRank": int(neg_v) if neg_v else None,
        "share": share_v or None,
        "sheet": sheet,
        "parseMode": note or "auto"
    })

def build_competition_rank_export_items(sheets, filename, fallback_platform):
    items = []
    for sheet, cells in sheets.items():
        rows = sheet_rows(cells)
        if not rows:
            continue
        meta = {}
        for row in rows[:8]:
            key = str(cell_at(row, 0) or "").strip()
            val = str(cell_at(row, 1) or "").strip()
            if key and val:
                meta[key] = val
        header_idx = None
        for i, row in enumerate(rows[:20]):
            headers = [str(x or "").strip() for x in row]
            if "车系名称" in headers and any("正向排名top20车系名称" == h for h in headers):
                header_idx = i
                break
        if header_idx is None:
            continue
        headers = [str(x or "").strip() for x in rows[header_idx]]
        time_i = col_index_exact(headers, ("时间",)) or 0
        own_i = col_index_exact(headers, ("车系名称",))
        comp_i = col_index_exact(headers, ("正向排名top20车系名称",))
        pos_i = col_index_exact(headers, ("正向排名",))
        neg_i = col_index_exact(headers, ("反向排名",))
        pos_share_i = col_index_exact(headers, ("正向占比",))
        compare_share_i = col_index_exact(headers, ("车系对比次数占比",))
        period_hint = period_from_text(meta.get("时间"), sheet, filename)
        platform = infer_vertical_platform(filename, sheet, headers, fallback=fallback_platform)
        if platform == "自动识别" and "正反向竞争排名" in sheet:
            platform = "懂车帝"
        if own_i is None or comp_i is None or pos_i is None or neg_i is None:
            continue
        for row in rows[header_idx + 1:]:
            row_own = clean_model_name(cell_at(row, own_i))
            if not row_own:
                continue
            period = cell_at(row, time_i) or period_hint
            add_vertical_item(
                items,
                filename=filename,
                platform=platform,
                sheet=sheet,
                period=date_label(period),
                own=row_own,
                comp=cell_at(row, comp_i),
                pos=cell_at(row, pos_i),
                neg=cell_at(row, neg_i),
                share=cell_at(row, compare_share_i) or cell_at(row, pos_share_i),
                note="auto-competition-rank"
            )
    return items

def find_vertical_header(rows):
    best_i, best_score = 0, -1
    keys = ("本品", "竞品", "车系", "车型", "正向", "反向", "排名", "周期", "时间", "平台", "来源")
    for i, row in enumerate(rows[:20]):
        score = sum(1 for cell in row if any(k in str(cell or "") for k in keys))
        if score > best_score:
            best_i, best_score = i, score
    return best_i if best_score >= 2 else find_header(rows)

def build_generic_vertical_items(sheets, filename, fallback_platform):
    items = []
    own_keys = ("本品车型", "本品车系", "本品", "主车型", "分析车型", "车型A", "车系A", "own")
    comp_keys = ("竞品车型", "竞品车系", "竞品", "对比车型", "车型B", "车系B", "competitor")
    model_keys = ("车型", "车系", "model")
    platform_keys = ("平台", "数据平台", "来源平台", "渠道", "来源")
    period_keys = ("周期", "时间周期", "数据周期", "时间", "日期", "月份", "周")
    pos_keys = ("正向排名", "正向排行", "正向rank", "正向", "正向PK排名", "正向对比排名")
    neg_keys = ("反向排名", "反向排行", "反向rank", "反向", "反向PK排名", "反向对比排名")
    share_keys = ("占比", "对比占比", "share", "份额")

    for sheet, cells in sheets.items():
        rows = sheet_rows(cells)
        if not rows:
            continue
        hidx = find_vertical_header(rows)
        headers = [str(x or "").strip() for x in rows[hidx]]
        if any(h == "正向排名top20车系名称" for h in headers):
            continue
        platform_i = col_index(headers, platform_keys)
        period_i = col_index(headers, period_keys)
        own_i = col_index(headers, own_keys)
        comp_i = col_index(headers, comp_keys)
        model_i = col_index(headers, model_keys)
        pos_i = col_index(headers, pos_keys)
        neg_i = col_index(headers, neg_keys)
        share_i = col_index(headers, share_keys)
        sheet_platform = infer_vertical_platform(filename, sheet, headers, fallback=fallback_platform)
        sheet_period = period_from_text(filename, sheet)
        rank_cols = []
        for i, h in enumerate(headers):
            hs = str(h or "")
            is_pos = any(k in hs for k in ("正向", "正排", "正向排名"))
            is_neg = any(k in hs for k in ("反向", "反排", "反向排名"))
            if is_pos or is_neg:
                period = period_from_text(hs) or sheet_period
                rank_cols.append((i, "pos" if is_pos else "neg", period))
        dated_rank_cols = sum(1 for _, _, p in rank_cols if p and p != sheet_period)

        # 长表：本品、竞品、正向排名、反向排名、周期、平台分别在列里。
        if (own_i is not None or model_i is not None) and comp_i is not None and (pos_i is not None or neg_i is not None) and not (period_i is None and dated_rank_cols >= 2):
            current_own = ""
            for row in rows[hidx + 1:]:
                own = cell_at(row, own_i) or (cell_at(row, model_i) if comp_i is not None else "")
                if own:
                    current_own = own
                comp = cell_at(row, comp_i)
                period = cell_at(row, period_i) or sheet_period or period_from_text(filename, sheet, *row[:8])
                platform = cell_at(row, platform_i) or infer_vertical_platform(filename, sheet, headers, row, sheet_platform)
                add_vertical_item(
                    items,
                    filename=filename,
                    platform=platform,
                    sheet=sheet,
                    period=date_label(period),
                    own=current_own,
                    comp=comp,
                    pos=cell_at(row, pos_i),
                    neg=cell_at(row, neg_i),
                    share=cell_at(row, share_i),
                    note="auto-long"
                )

        # 竞品长表：只有一个车型列时，尝试用上方/文件名中的“本品”作为分析车型。
        if own_i is None and comp_i is None and model_i is not None and (pos_i is not None or neg_i is not None):
            hinted_own = ""
            for pre in rows[:hidx + 1]:
                text = " ".join(str(x or "") for x in pre)
                m = re.search(r"(?:本品|分析车型|主车型)[:：\s]*([\u4e00-\u9fffA-Za-z0-9 ._-]{2,24})", text)
                if m:
                    hinted_own = clean_model_name(m.group(1))
                    break
            if hinted_own:
                for row in rows[hidx + 1:]:
                    comp = cell_at(row, model_i)
                    period = cell_at(row, period_i) or sheet_period
                    platform = cell_at(row, platform_i) or infer_vertical_platform(filename, sheet, headers, row, sheet_platform)
                    add_vertical_item(
                        items,
                        filename=filename,
                        platform=platform,
                        sheet=sheet,
                        period=date_label(period),
                        own=hinted_own,
                        comp=comp,
                        pos=cell_at(row, pos_i),
                        neg=cell_at(row, neg_i),
                        share=cell_at(row, share_i),
                        note="auto-competitor-list"
                    )

        # 宽表：本品/竞品在行里，多个日期/周期横向展开，列名里包含正向/反向。
        if (own_i is not None or model_i is not None) and comp_i is not None:
            if rank_cols and dated_rank_cols >= 2:
                for row in rows[hidx + 1:]:
                    own = cell_at(row, own_i) or cell_at(row, model_i)
                    comp = cell_at(row, comp_i)
                    grouped = {}
                    for i, kind, period in rank_cols:
                        grouped.setdefault(period or sheet_period or date_label(sheet), {})[kind] = cell_at(row, i)
                    for period, ranks in grouped.items():
                        platform = cell_at(row, platform_i) or infer_vertical_platform(filename, sheet, headers, row, sheet_platform)
                        add_vertical_item(
                            items,
                            filename=filename,
                            platform=platform,
                            sheet=sheet,
                            period=date_label(period),
                            own=own,
                            comp=comp,
                            pos=ranks.get("pos"),
                            neg=ranks.get("neg"),
                            share=cell_at(row, share_i),
                            note="auto-wide"
                        )
    return items

def build_vertical_media_dataset_from_workbook(data, filename):
    sheets = read_xlsx_cells(data)
    platform = source_platform(filename, list(sheets.keys()))
    items = []

    # 汽车之家格式：每个 sheet 是一个周周期；列为 本品、正向排名、竞品、占比、反向排名。
    for sheet, cells in sheets.items():
        rows = sheet_rows(cells)
        if not rows:
            continue
        header = [str(x or "").strip() for x in rows[0]]
        if "本品车系名称" in header and "竞品车系名称" in header:
            sheet_platform = "汽车之家" if platform == "自动识别" else platform
            own = ""
            for row in rows[1:]:
                if len(row) < 5:
                    continue
                if row[0]:
                    own = clean_model_name(row[0])
                comp = clean_model_name(row[2])
                if not own or not comp:
                    continue
                pos, share, neg = num(row[1]), share_num(row[3]), num(row[4])
                if not pos and not neg:
                    continue
                items.append({
                    "source": filename,
                    "platform": sheet_platform,
                    "period": date_label(sheet),
                    "periodOrder": period_order(sheet),
                    "ownModel": own,
                    "competitor": comp,
                    "positiveRank": int(pos) if pos else None,
                    "negativeRank": int(neg) if neg else None,
                    "share": share,
                    "sheet": sheet
                })

    # 懂车帝格式：一个宽表；每个本品车型纵向分块，每个日期横向分组。
    for sheet, cells in sheets.items():
        rows = sheet_rows(cells)
        if not rows:
            continue
        header_rows = []
        for i, row in enumerate(rows):
            first = str(row[0] or "")
            if "正反向PK" in first:
                header_rows.append(i)
        if not header_rows:
            continue
        sheet_platform = "懂车帝" if platform == "自动识别" else platform
        header_rows.append(len(rows))
        for idx in range(len(header_rows) - 1):
            h = header_rows[idx]
            end = header_rows[idx + 1]
            own = clean_model_name(str(rows[h][0]).replace("正反向PK", ""))
            if not own:
                continue
            row0, row1 = rows[h], rows[h + 1] if h + 1 < len(rows) else []
            max_len = max(len(row0), len(row1))
            for c in range(max_len):
                if c >= len(row0) or str(row0[c] or "").strip() != "车系":
                    continue
                period = date_label(row0[c + 1] if c + 1 < len(row0) else "")
                if not period:
                    continue
                for r in range(h + 2, end):
                    row = rows[r]
                    comp = clean_model_name(row[c] if c < len(row) else "")
                    if not comp:
                        continue
                    pos = num(row[c + 1] if c + 1 < len(row) else 0)
                    neg = num(row[c + 2] if c + 2 < len(row) else 0)
                    if not pos and not neg:
                        continue
                    items.append({
                        "source": filename,
                        "platform": sheet_platform,
                        "period": period,
                        "periodOrder": period_order(period),
                        "ownModel": own,
                        "competitor": comp,
                        "positiveRank": int(pos) if pos else None,
                        "negativeRank": int(neg) if neg else None,
                        "share": None,
                        "sheet": sheet
                    })

    items.extend(build_competition_rank_export_items(sheets, filename, platform))
    items.extend(build_generic_vertical_items(sheets, filename, platform))
    deduped = {}
    for item in items:
        deduped[vertical_item_key(item)] = item
    items = list(deduped.values())

    if not items:
        raise ValueError("未识别到垂媒正反向排名数据。请确认表格中包含本品车型、竞品车型、正向/反向排名、时间周期或平台字段。")
    models = sorted({x["ownModel"] for x in items})
    periods = [p for p, _ in sorted({(x["period"], x.get("periodOrder", x["period"])) for x in items}, key=lambda v: v[1])]
    item_platforms = sorted({x.get("platform") for x in items if x.get("platform") and x.get("platform") != "自动识别"})
    detected_platform = item_platforms[0] if platform == "自动识别" and len(item_platforms) == 1 else platform
    return {"source": filename, "platform": detected_platform, "count": len(items), "models": models, "periods": periods, "items": items}

def validate_vertical_platform(dataset):
    platforms = {dataset.get("platform"), *[x.get("platform") for x in dataset.get("items", [])]}
    platforms = {x for x in platforms if x and x != "自动识别"}
    if not platforms:
        raise ValueError("正反向排名只支持汽车之家和懂车帝。当前文件未能识别平台，请在文件名、Sheet名或表头中标明汽车之家/懂车帝。")
    unsupported = sorted(x for x in platforms if x not in VERTICAL_PLATFORMS)
    if unsupported:
        raise ValueError(f"正反向排名只支持汽车之家和懂车帝，当前识别到：{'、'.join(unsupported)}。")
    if len(platforms) == 1:
        platform = next(iter(platforms))
        dataset["platform"] = platform
        for item in dataset.get("items", []):
            if item.get("platform") in ("", "自动识别", None):
                item["platform"] = platform
    return dataset

def summarize_vertical_assets(platform):
    with db() as conn:
        row = conn.execute("""
            select
              count(*) as model_count,
              count(distinct nullif(brand_name,'')) as brand_count
            from vehicle_assets
            where platform=?
        """, (platform,)).fetchone()
        rank_row = conn.execute("""
            select
              count(*) as relation_count,
              count(distinct period) as period_count
            from vertical_rank_assets
            where platform=?
        """, (platform,)).fetchone()
        brands = conn.execute("""
            select coalesce(nullif(brand_name,''),'待识别品牌') as brand_name,
                   count(*) as model_count
            from vehicle_assets
            where platform=?
            group by coalesce(nullif(brand_name,''),'待识别品牌')
            order by model_count desc, brand_name asc
            limit 12
        """, (platform,)).fetchall()
    return {
        "platform": platform,
        "brandCount": int(row["brand_count"] or 0),
        "modelCount": int(row["model_count"] or 0),
        "relationCount": int(rank_row["relation_count"] or 0),
        "periodCount": int(rank_row["period_count"] or 0),
        "topBrands": [dict(x) for x in brands]
    }

def remember_vertical_dataset(data, filename, dataset):
    validate_vertical_platform(dataset)
    init_db()
    imported_at = now()
    h = file_hash(data)
    platform = dataset["platform"]
    periods = sorted(set(dataset.get("periods") or [x.get("period") for x in dataset.get("items", []) if x.get("period")]))
    models = set(dataset.get("models") or [])
    for item in dataset.get("items", []):
        if item.get("ownModel"):
            models.add(item["ownModel"])
        if item.get("competitor"):
            models.add(item["competitor"])

    with db() as conn:
        conn.execute("""
            insert into vertical_import_batches
            (id, platform, filename, file_hash, periods_json, model_count, item_count, imported_at, parser_version)
            values (?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(platform, file_hash) do update set
              filename=excluded.filename,
              periods_json=excluded.periods_json,
              model_count=excluded.model_count,
              item_count=excluded.item_count,
              imported_at=excluded.imported_at,
              parser_version=excluded.parser_version
        """, (
            stable_id("vertical-batch", platform, h),
            platform,
            filename,
            h,
            json.dumps(periods, ensure_ascii=False),
            len(models),
            len(dataset.get("items", [])),
            imported_at,
            VERTICAL_ASSET_PARSER_VERSION
        ))
        for model in sorted(x for x in models if x):
            brand = infer_brand_from_model(model)
            period_first = periods[0] if periods else ""
            period_last = periods[-1] if periods else ""
            conn.execute("""
                insert into vehicle_assets
                (id, platform, brand_name, model_name, first_seen_at, last_seen_at, first_source, last_source,
                 period_first, period_last, import_count, extra_json)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                on conflict(platform, model_name) do update set
                  brand_name=excluded.brand_name,
                  last_seen_at=excluded.last_seen_at,
                  last_source=excluded.last_source,
                  period_first=case
                    when vehicle_assets.period_first='' or excluded.period_first < vehicle_assets.period_first then excluded.period_first
                    else vehicle_assets.period_first end,
                  period_last=case
                    when excluded.period_last > vehicle_assets.period_last then excluded.period_last
                    else vehicle_assets.period_last end,
                  import_count=vehicle_assets.import_count+1
            """, (
                stable_id("vehicle-asset", platform, model),
                platform,
                brand,
                model,
                imported_at,
                imported_at,
                filename,
                filename,
                period_first,
                period_last,
                json.dumps({"assetSource": "vertical_rank_import"}, ensure_ascii=False)
            ))
        for item in dataset.get("items", []):
            item_platform = item.get("platform") or platform
            if item_platform not in VERTICAL_PLATFORMS:
                continue
            conn.execute("""
                insert into vertical_rank_assets
                (id, platform, period, own_model, competitor_model, positive_rank, negative_rank, compare_share,
                 source_file, file_hash, sheet, parse_mode, first_seen_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(platform, period, own_model, competitor_model) do update set
                  positive_rank=excluded.positive_rank,
                  negative_rank=excluded.negative_rank,
                  compare_share=excluded.compare_share,
                  source_file=excluded.source_file,
                  file_hash=excluded.file_hash,
                  sheet=excluded.sheet,
                  parse_mode=excluded.parse_mode,
                  updated_at=excluded.updated_at
            """, (
                stable_id("vertical-rank", item_platform, item.get("period"), item.get("ownModel"), item.get("competitor")),
                item_platform,
                item.get("period") or "",
                item.get("ownModel") or "",
                item.get("competitor") or "",
                item.get("positiveRank"),
                item.get("negativeRank"),
                item.get("share"),
                filename,
                h,
                item.get("sheet") or "",
                item.get("parseMode") or "",
                imported_at,
                imported_at
            ))
    dataset["assetSummary"] = summarize_vertical_assets(platform)
    dataset["remembered"] = {
        "platform": platform,
        "fileHash": h,
        "modelCount": len(models),
        "itemCount": len(dataset.get("items", [])),
        "periods": periods,
        "savedAt": imported_at
    }
    dataset["knowledgeItems"] = build_vertical_knowledge_items(dataset, filename, limit=120)
    return dataset

def build_vertical_knowledge_items(dataset, filename="", limit=120):
    items = dataset.get("items", [])
    by_model = {}
    for item in items:
        by_model.setdefault(item.get("ownModel") or "", []).append(item)
    knowledge = []
    for own, rows in sorted(by_model.items())[:limit]:
        if not own:
            continue
        rows = sorted(rows, key=lambda x: (str(x.get("periodOrder") or x.get("period") or ""), x.get("positiveRank") or 999))
        latest_period = rows[-1].get("period") if rows else ""
        latest_rows = [x for x in rows if x.get("period") == latest_period] or rows[-20:]
        top_pos = sorted(latest_rows, key=lambda x: x.get("positiveRank") or 999)[:5]
        top_neg = sorted(latest_rows, key=lambda x: x.get("negativeRank") or 999)[:5]
        competitors = list(dict.fromkeys([x.get("competitor") for x in top_pos + top_neg if x.get("competitor")]))
        platform = dataset.get("platform") or rows[0].get("platform") or ""
        title = f"{own}｜{platform}正反向竞争格局｜{latest_period}"
        pos_copy = "、".join([f"{x.get('competitor')}第{x.get('positiveRank')}" for x in top_pos]) or "暂无"
        neg_copy = "、".join([f"{x.get('competitor')}第{x.get('negativeRank')}" for x in top_neg]) or "暂无"
        body = (
            f"{own}在{platform}{latest_period}正反向排名中，正向Top竞品为"
            f"{pos_copy}；"
            f"反向高相关竞品为{neg_copy}。"
            "这类数据用于判断用户在垂媒环境中主动对比谁、又被哪些车型反向牵引，辅助内容选题、竞品拦截和口碑修复。"
        )
        knowledge.append({
            "id": stable_id("vertical-rag", platform, own, latest_period, filename),
            "type": "垂媒竞争格局",
            "title": title,
            "body": body,
            "keywords": [own, platform, latest_period, "正反向排名", "竞品监测", *competitors],
            "tags": [platform, "正反向排名", "车型数据资产", "垂媒竞争格局"],
            "targets": ["垂媒竞争格局", "RAG知识库管理", "MMN策略", "决策驾驶舱"],
            "source": filename or "vertical_rank_assets",
            "createdAt": now(),
            "metadata": {
                "doc_id": stable_id("vertical-rag-doc", platform, own, latest_period, filename),
                "domain": "车型数据资产",
                "module": "正反向排名训练材料",
                "topic": title,
                "entity": own,
                "period": latest_period,
                "platform": platform,
                "source_file": filename
            }
        })
    return knowledge

def vertical_learning_prompt(context):
    model = context.get("model") or "当前车型"
    platform = context.get("platform") or "垂媒"
    period = context.get("period") or "当前周期"
    rows = context.get("rows") or []
    compact = [
        {
            "competitor": x.get("competitor"),
            "positiveRank": x.get("positiveRank"),
            "negativeRank": x.get("negativeRank"),
            "share": x.get("share"),
            "status": x.get("status")
        }
        for x in rows[:30]
    ]
    return [
        {"role": "system", "content": "你是MMN汽车营销智能体的垂媒竞争格局学习模块。只基于用户提供的正反向排名数据分析，不要编造销量、声量或事实。输出中文，偏营销策略。" + MMN_OUTPUT_STYLE},
        {"role": "user", "content": json.dumps({
            "任务": "学习并归纳车型正反向竞争格局，形成可进入RAG知识库的策略学习卡",
            "车型": model,
            "平台": platform,
            "周期": period,
            "正反向排名数据": compact,
            "输出要求": [
                "1. 先给一句清楚结论，不超过35字",
                "2. 拆清楚归因：用户为什么会把这些车放在一起比",
                "3. 识别核心正向对比竞品和核心反向牵引竞品",
                "4. 判断该车型在用户心智里处于主动被搜索、被替代比较、还是反向被牵引",
                "5. 给出3条垂媒内容/口碑/竞品拦截打法，每条必须有动作和验证指标",
                "6. 给出适合写入RAG知识库的标题、标签和一句话结论"
            ]
        }, ensure_ascii=False)}
    ]

def rag_strategy_prompt(question, project, references):
    compact_refs = []
    for i, item in enumerate((references or [])[:8], start=1):
        compact_refs.append({
            "序号": i,
            "标题": item.get("title", ""),
            "类型": item.get("type", ""),
            "内容": item.get("body", "")[:700],
            "来源": item.get("source", ""),
            "关键词": item.get("keywords", [])[:10],
            "引用原因": item.get("reason", "")
        })
    return [
        {"role": "system", "content": "你是MMN营销引擎的汽车营销智能体。你必须先利用RAG召回资料，再结合通用汽车营销策略能力输出。不要编造未给出的数据；如果依据不足，要说明依据不足并给出可执行的下一步补数建议。" + MMN_OUTPUT_STYLE},
        {"role": "user", "content": json.dumps({
            "用户问题": question,
            "当前项目": project or {},
            "RAG召回资料": compact_refs,
            "输出格式": [
                "结论先说：一句话说明最该解决的问题",
                "归因分析：用3点说明为什么会这样，每点都要联系用户心智或平台传播机制",
                "策略结论：明确主打法，不超过3条",
                "马上怎么做：按优先级列3-5条动作，每条写清内容形态、平台、人群、验证指标",
                "需要补充的数据：只列真正影响判断的数据缺口"
            ]
        }, ensure_ascii=False)}
    ]

def local_rag_strategy_answer(question, project, references):
    refs = references or []
    titles = "、".join([x.get("title", "") for x in refs[:4] if x.get("title")]) or "当前知识库"
    model = (project or {}).get("model") or "当前车型"
    return "\n".join([
        f"结论先说：{model}现在不要先扩大投放，先把用户最在意的疑虑讲清楚。",
        f"归因分析：本次本地RAG召回了 {len(refs)} 条依据，主要来自：{titles}。说明当前问题不是没有话题，而是缺少能让用户相信的解释材料。",
        "策略结论：先做证据型内容，再做平台扩散，最后承接试驾或咨询。不要把预算直接砸到泛流量上。",
        "马上怎么做：1. 把最高风险认知拆成三条可验证证据；2. 用垂媒或真实车主补第三方视角；3. 在小红书/抖音用真实场景解释价格、空间、智驾或安全疑虑；4. 把有效说法写回项目学习库。",
        "还缺什么数据：正式给客户前，需要补平台声量、达人质量、竞品正反向变化和转化线索。"
    ])

def save_vertical_ai_learning(context, summary_text):
    platform = context.get("platform") or ""
    model = context.get("model") or ""
    period = context.get("period") or ""
    source_file = context.get("source") or ""
    knowledge = {
        "id": stable_id("vertical-ai-learning", platform, model, period),
        "type": "MMN智能体学习",
        "title": f"{model}｜正反向竞争格局AI学习｜{period}",
        "body": summary_text[:1600],
        "keywords": [model, platform, period, "正反向排名", "千问学习", "竞品策略"],
        "tags": [platform, "MMN学习", "垂媒竞争格局", "车型数据资产"],
        "targets": ["MMN策略", "RAG知识库管理", "垂媒竞争格局", "决策驾驶舱"],
        "source": source_file or "qwen_vertical_learning",
        "createdAt": now(),
        "metadata": {
            "doc_id": stable_id("vertical-ai-learning-doc", platform, model, period),
            "domain": "车型数据资产",
            "module": "千问正反向排名学习",
            "topic": f"{model}正反向竞争格局",
            "entity": model,
            "period": period,
            "platform": platform,
            "model_provider": "qwen"
        }
    }
    with db() as conn:
        conn.execute("""
            insert into vertical_ai_learnings
            (id, platform, model_name, period, source_file, summary_text, knowledge_json, created_at)
            values (?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(platform, model_name, period) do update set
              source_file=excluded.source_file,
              summary_text=excluded.summary_text,
              knowledge_json=excluded.knowledge_json,
              created_at=excluded.created_at
        """, (
            knowledge["id"], platform, model, period, source_file,
            summary_text, json.dumps(knowledge, ensure_ascii=False), now()
        ))
    return knowledge

def split_tags(value):
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    return [x.strip() for x in re.split(r"[/,，、|｜;；\n]+", str(value or "")) if x.strip()]

def rag_targets(domain, module, knowledge_type):
    text = " ".join([domain or "", module or "", knowledge_type or ""])
    targets = []
    if any(k in text for k in ("内容", "达人", "KOC", "KOL", "KOS", "脚本")):
        targets.append("内容资产中心")
    if any(k in text for k in ("垂媒", "竞品", "对比", "排名")):
        targets.append("垂媒竞争格局")
    if any(k in text for k in ("数据", "RAG", "指标", "NSR", "Gap")):
        targets.append("决策驾驶舱")
    if any(k in text for k in ("车型", "品牌", "集团", "定位")):
        targets.append("认知赛道诊断")
    targets += ["RAG知识库管理", "MMN策略"]
    return list(dict.fromkeys(targets))

def normalize_rag_record(record, source_name):
    doc_id = str(record.get("doc_id") or record.get("id") or "").strip()
    content = str(record.get("content") or record.get("body") or record.get("text") or "").strip()
    if not content:
        return None
    domain = str(record.get("domain") or record.get("knowledge_type") or "MMN RAG训练材料").strip()
    module = str(record.get("module") or "").strip()
    topic = str(record.get("topic") or record.get("title") or "").strip()
    entity = str(record.get("entity") or "").strip()
    knowledge_type = str(record.get("knowledge_type") or domain or "knowledge").strip()
    tags = split_tags(record.get("tags"))
    queries = record.get("retrieval_queries")
    if isinstance(queries, str):
        queries = split_tags(queries)
    elif not isinstance(queries, list):
        queries = []
    keywords = list(dict.fromkeys([*tags, *queries, entity, topic, module, domain]))
    item_id = doc_id or "rag_" + uuid.uuid4().hex[:12]
    return {
        "id": item_id,
        "type": domain,
        "title": "｜".join([x for x in [module, topic or entity or item_id] if x]) or item_id,
        "body": content[:1200],
        "keywords": [x for x in keywords if x][:16],
        "tags": [x for x in [*tags, entity, knowledge_type, record.get("confidence"), record.get("status")] if x],
        "targets": rag_targets(domain, module, knowledge_type),
        "source": source_name,
        "createdAt": now(),
        "metadata": {
            "doc_id": item_id,
            "domain": domain,
            "module": module,
            "topic": topic,
            "entity": entity,
            "knowledge_type": knowledge_type,
            "confidence": record.get("confidence", ""),
            "source_context": record.get("source_context", ""),
            "status": record.get("status", ""),
            "retrieval_queries": queries
        }
    }

def parse_markdown_rag(text, source_name):
    chunks = []
    current = []
    title = source_name
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            if current:
                chunks.append((title, "\n".join(current).strip()))
                current = []
            title = re.sub(r"^#+\s*", "", s)[:80] or source_name
        elif s:
            current.append(s)
    if current:
        chunks.append((title, "\n".join(current).strip()))
    items = []
    for i, (chunk_title, body) in enumerate(chunks):
        if len(body) < 30:
            continue
        items.append(normalize_rag_record({
            "doc_id": f"{re.sub(r'[^0-9A-Za-z一-龥]+', '_', source_name)[:32]}_{i+1:03d}",
            "domain": "MMN RAG训练材料",
            "module": "Markdown知识库",
            "topic": chunk_title,
            "content": body[:1200],
            "tags": chunk_title
        }, source_name))
    return [x for x in items if x]

def parse_rag_file(data, filename):
    name = filename or "rag_material"
    lower = name.lower()
    items = []
    if lower.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            for entry in z.namelist():
                if entry.endswith("/") or entry.startswith("__MACOSX/"):
                    continue
                if not re.search(r"\.(jsonl|csv|md|txt|json)$", entry, re.I):
                    continue
                items.extend(parse_rag_file(z.read(entry), Path(entry).name)["items"])
    elif lower.endswith(".jsonl"):
        text = data.decode("utf-8-sig")
        for line in text.splitlines():
            if line.strip():
                items.append(normalize_rag_record(json.loads(line), name))
    elif lower.endswith(".csv"):
        text = data.decode("utf-8-sig")
        for row in csv.DictReader(io.StringIO(text)):
            items.append(normalize_rag_record(row, name))
    elif lower.endswith(".json"):
        obj = json.loads(data.decode("utf-8-sig"))
        records = obj if isinstance(obj, list) else obj.get("records") or obj.get("items") or []
        if records:
            for row in records:
                items.append(normalize_rag_record(row, name))
        else:
            items.extend(parse_markdown_rag(json.dumps(obj, ensure_ascii=False, indent=2), name))
    else:
        items.extend(parse_markdown_rag(data.decode("utf-8-sig", errors="ignore"), name))
    deduped = {}
    for item in items:
        if item and item.get("id") not in deduped:
            deduped[item["id"]] = item
    return {"source": name, "count": len(deduped), "items": list(deduped.values())}

def bundled_rag_package():
    path = DATA_DIR / "rag_training" / "v1" / "mmn_auto_marketing_rag_corpus_v1.jsonl"
    if not path.exists():
        raise ValueError("未找到内置MMN RAG训练包。")
    return parse_rag_file(path.read_bytes(), path.name)

def ppt_text(text, limit=280):
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    return text[:limit] + ("…" if len(text) > limit else "")

def make_pptx(payload):
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    navy = RGBColor(16, 35, 59)
    blue = RGBColor(20, 120, 157)
    grey = RGBColor(94, 111, 124)

    def add_title(slide, title, subtitle=None):
        box = slide.shapes.add_textbox(Inches(.55), Inches(.35), Inches(12.2), Inches(.8))
        p = box.text_frame.paragraphs[0]
        p.text = title
        p.font.size = Pt(30)
        p.font.bold = True
        p.font.color.rgb = navy
        if subtitle:
            sub = slide.shapes.add_textbox(Inches(.58), Inches(1.02), Inches(11.7), Inches(.35))
            sp = sub.text_frame.paragraphs[0]
            sp.text = subtitle
            sp.font.size = Pt(12)
            sp.font.color.rgb = grey

    def add_body(slide, lines, x=.7, y=1.35, w=12, h=5.6, size=16):
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = box.text_frame
        tf.word_wrap = True
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.text = line
            p.font.size = Pt(size)
            p.font.color.rgb = navy if i == 0 else RGBColor(40, 55, 70)
            if i == 0:
                p.font.bold = True
            p.space_after = Pt(8)

    title = payload.get("title") or "中国汽车营销引擎策略报告"
    model = payload.get("model") or ""
    competitor = payload.get("competitor") or ""
    metrics = payload.get("metrics") or {}
    diagnostics = payload.get("diagnostics") or []
    manual = payload.get("manual") or []
    knowhow = payload.get("knowhow") or []
    calendar = payload.get("calendar") or []
    account = payload.get("account") or "本机试用"

    s = prs.slides.add_slide(prs.slide_layouts[6])
    bg = s.background.fill
    bg.solid()
    bg.fore_color.rgb = navy
    t = s.shapes.add_textbox(Inches(.8), Inches(1.6), Inches(11.8), Inches(1.5))
    p = t.text_frame.paragraphs[0]
    p.text = title
    p.font.size = Pt(38)
    p.font.bold = True
    p.font.color.rgb = RGBColor(255, 255, 255)
    st = s.shapes.add_textbox(Inches(.85), Inches(3.1), Inches(11.5), Inches(.8))
    sp = st.text_frame.paragraphs[0]
    sp.text = f"分析对象：{model}｜核心竞品：{competitor}｜{account}"
    sp.font.size = Pt(16)
    sp.font.color.rgb = RGBColor(210, 226, 236)

    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "核心数据结果", "系统计算结果，仅作为结论判断的输入")
    kpis = [
        ("口碑健康 NSR", metrics.get("nsr", "—")),
        ("目标人群穿透 IPS", metrics.get("ips", "—")),
        ("购买意向指数", metrics.get("intent", "—")),
        ("购买阻力风险", metrics.get("risk", "—")),
    ]
    for i, (k, v) in enumerate(kpis):
        x = .75 + i * 3.15
        shape = s.shapes.add_shape(1, Inches(x), Inches(1.75), Inches(2.75), Inches(1.6))
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor(240, 247, 250)
        shape.line.color.rgb = RGBColor(215, 228, 235)
        tb = s.shapes.add_textbox(Inches(x+.18), Inches(1.92), Inches(2.4), Inches(1.2))
        tf = tb.text_frame
        tf.paragraphs[0].text = k
        tf.paragraphs[0].font.size = Pt(12)
        tf.paragraphs[0].font.color.rgb = grey
        pp = tf.add_paragraph()
        pp.text = str(v)
        pp.font.size = Pt(26)
        pp.font.bold = True
        pp.font.color.rgb = blue

    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "认知诊断排序", f"{model} 当前最需要关注的认知标签")
    add_body(s, [f"{i+1}. {d.get('label')}｜{d.get('diagnosis')}｜负向 {d.get('negative')}｜Gap {d.get('gap')}｜优先级 {d.get('priority')}" for i,d in enumerate(diagnostics[:8])], size=15)

    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "人工结论与建议", "以人工填写内容为准，系统负责沉淀和复用")
    if manual:
        lines = []
        for i, m in enumerate(manual[:5]):
            lines += [f"{i+1}. {m.get('label')}：{ppt_text(m.get('conclusion'), 120)}", f"建议：{ppt_text(m.get('recommendation'), 150)}"]
    else:
        lines = ["尚未填写人工结论。请在“人工结论学习”页面补充。"]
    add_body(s, lines, size=14)

    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "参考 Know-how", "来自系统框架与企业知识库的组合参考")
    add_body(s, [f"{i+1}. {k.get('label')}：{ppt_text(k.get('message'), 130)}｜证据：{ppt_text(k.get('evidence'), 100)}" for i,k in enumerate(knowhow[:6])], size=14)

    s = prs.slides.add_slide(prs.slide_layouts[6])
    add_title(s, "30天行动节奏参考", "用于把数据结果转成项目推进节奏")
    add_body(s, [f"{c.get('week')}｜{c.get('theme')}：{ppt_text(c.get('task'), 180)}" for c in calendar], size=15)

    out = BytesIO()
    prs.save(out)
    return out.getvalue()

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def send_json(self, payload, status=200):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self.send_json({"ok": True, "mode": "commercial-demo", "db": str(DB_PATH)})
            return
        if parsed.path == "/api/ai/status":
            qcfg = qwen_config()
            dcfg = deepseek_config()
            ocfg = openai_config()
            self.send_json({
                "ok": True,
                "qwen": {"configured": qcfg["configured"], "model": qcfg["model"], "baseUrl": qcfg["base_url"]},
                "qwenFast": {"configured": qcfg["configured"], "model": qwen_model_for("fast"), "baseUrl": qcfg["base_url"]},
                "qwenDeep": {"configured": qcfg["configured"], "model": qwen_model_for("deep"), "baseUrl": qcfg["base_url"]},
                "deepseek": {"configured": dcfg["configured"], "model": dcfg["model"], "baseUrl": dcfg["base_url"]},
                "deepseekDeep": {"configured": dcfg["configured"], "model": deepseek_model_for("deep"), "baseUrl": dcfg["base_url"]},
                "openai": {"configured": ocfg["configured"], "model": ocfg["model"], "baseUrl": ocfg["base_url"]},
                "rules": {"configured": True, "model": "MMN规则引擎"}
            })
            return
        if parsed.path == "/api/sales-marquee":
            try:
                self.send_json(dongchedi_sales_payload())
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc), "items": []}, 500)
            return
        if parsed.path == "/api/global-sales-marquee":
            try:
                self.send_json(thailand_market_payload())
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc), "items": []}, 500)
            return
        if parsed.path == "/api/social-plugin/status":
            self.send_json({"ok": True, "plugin": social_plugin_status()})
            return
        if parsed.path == "/api/founder-archives":
            q = parse_qs(parsed.query)
            edition = edition_from(q.get("edition", ["china"])[0])
            self.send_json({
                "ok": True,
                "items": founder_archive_rows(edition=edition),
                "scheduler": {
                    "timezone": "Asia/Shanghai",
                    "rrule": "每周日 23:00",
                    "nextRunInSeconds": int(seconds_until_next_founder_run())
                },
                "sources": [{"name": x["name"], "platform": x["platform"], "url": x["url"], "enabled": x["enabled"]} for x in FOUNDER_PUBLIC_SOURCES],
                "modelRoles": {
                    "qwen": "主控执行：抓取内容清洗、摘要和结构化入库",
                    "deepseek": "策略质检：观点归因、语言风格蒸馏、舆论风险判断和高管IP Prompt生成"
                }
            })
            return
        if parsed.path == "/api/vertical-assets":
            q = parse_qs(parsed.query)
            platform = q.get("platform", ["懂车帝"])[0]
            if platform not in VERTICAL_PLATFORMS:
                self.send_json({"ok": False, "error": "正反向车型资产只支持汽车之家和懂车帝"}, 400)
                return
            self.send_json({"ok": True, "assetSummary": summarize_vertical_assets(platform)})
            return
        if parsed.path == "/api/learnings":
            q = parse_qs(parsed.query)
            org_id = q.get("org_id", [""])[0]
            edition = edition_from(q.get("edition", ["china"])[0])
            if not org_id:
                self.send_json({"ok": False, "error": "缺少 org_id"}, 400)
                return
            with db() as conn:
                rows = conn.execute(
                    "select * from learning_cases where org_id=? and edition=? order by saved_at desc",
                    (org_id, edition)
                ).fetchall()
            self.send_json({"ok": True, "items": [rowdict(r) for r in rows]})
            return
        if parsed.path == "/api/workspace":
            q = parse_qs(parsed.query)
            org_id = q.get("org_id", [""])[0]
            edition = edition_from(q.get("edition", ["china"])[0])
            if not org_id:
                self.send_json({"ok": False, "error": "缺少 org_id"}, 400)
                return
            with db() as conn:
                org = conn.execute("select * from organizations where id=?", (org_id,)).fetchone()
                scoped_id = scoped_org_id(org_id, edition)
                row = ensure_workspace(conn, scoped_id, org["name"] if org else "演示客户")
                snapshots = conn.execute(
                    """select id, brand, model, project, data_version, created_at
                    from project_snapshots where org_id=? and edition=? order by created_at desc limit 8""",
                    (org_id, edition)
                ).fetchall()
            self.send_json({
                "ok": True,
                "workspace": {
                    "hierarchy": json.loads(row["hierarchy_json"]),
                    "knowledge": json.loads(row["knowledge_json"]),
                    "modelRouter": json.loads(row["model_router_json"]),
                    "updatedAt": row["updated_at"],
                    "snapshots": [rowdict(r) for r in snapshots]
                }
            })
            return
        super().do_GET()

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/learnings":
            self.send_error(404)
            return
        q = parse_qs(parsed.query)
        org_id = q.get("org_id", [""])[0]
        edition = edition_from(q.get("edition", ["china"])[0])
        if not org_id:
            self.send_json({"ok": False, "error": "缺少 org_id"}, 400)
            return
        with db() as conn:
            conn.execute("delete from learning_cases where org_id=? and edition=?", (org_id, edition))
        self.send_json({"ok": True})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/login":
            try:
                body = self.read_json()
                org_name = (body.get("org") or "默认客户").strip()
                email = (body.get("email") or "demo@example.com").strip().lower()
                name = (body.get("name") or email.split("@")[0]).strip()
                created = now()
                with db() as conn:
                    org = conn.execute("select * from organizations where name=?", (org_name,)).fetchone()
                    if not org:
                        org_id = str(uuid.uuid4())
                        conn.execute("insert into organizations values (?,?,?)", (org_id, org_name, created))
                    else:
                        org_id = org["id"]
                    user = conn.execute("select * from users where org_id=? and email=?", (org_id, email)).fetchone()
                    if not user:
                        user_id = str(uuid.uuid4())
                        conn.execute("insert into users values (?,?,?,?,?)", (user_id, org_id, email, name, created))
                    else:
                        user_id = user["id"]
                    ensure_workspace(conn, scoped_org_id(org_id, "china"), org_name)
                    ensure_workspace(conn, scoped_org_id(org_id, "global"), org_name)
                self.send_json({"ok": True, "session": {"org_id": org_id, "org": org_name, "user_id": user_id, "email": email, "name": name}})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/workspace":
            try:
                body = self.read_json()
                org_id = body["org_id"]
                edition = edition_from(body.get("edition", "china"))
                scoped_id = scoped_org_id(org_id, edition)
                updated = now()
                with db() as conn:
                    conn.execute(
                        """insert into workspace_contexts
                        (org_id, hierarchy_json, knowledge_json, model_router_json, updated_at)
                        values (?,?,?,?,?)
                        on conflict(org_id) do update set
                        hierarchy_json=excluded.hierarchy_json,
                        knowledge_json=excluded.knowledge_json,
                        model_router_json=excluded.model_router_json,
                        updated_at=excluded.updated_at""",
                        (
                            scoped_id,
                            json.dumps(body.get("hierarchy", {}), ensure_ascii=False),
                            json.dumps(body.get("knowledge", []), ensure_ascii=False),
                            json.dumps(body.get("modelRouter", []), ensure_ascii=False),
                            updated
                        )
                    )
                self.send_json({"ok": True, "updatedAt": updated})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/project-state":
            try:
                body = self.read_json()
                payload = body.get("payload") or {}
                edition = edition_from(body.get("edition") or payload.get("edition") or "china")
                config = payload.get("state", {}).get("config", {})
                item_id = str(uuid.uuid4())
                created = now()
                with db() as conn:
                    conn.execute(
                        """insert into project_snapshots
                        (id, org_id, user_id, edition, brand, model, project, data_version, payload_json, created_at)
                        values (?,?,?,?,?,?,?,?,?,?)""",
                        (
                            item_id,
                            body["org_id"],
                            body["user_id"],
                            edition,
                            config.get("brand", ""),
                            config.get("model", ""),
                            config.get("project", ""),
                            payload.get("state", {}).get("datasetVersion", ""),
                            json.dumps(payload, ensure_ascii=False),
                            created
                        )
                    )
                self.send_json({"ok": True, "id": item_id, "createdAt": created})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/learnings":
            try:
                body = self.read_json()
                item_id = str(uuid.uuid4())
                saved_at = now()
                edition = edition_from(body.get("edition", "china"))
                with db() as conn:
                    conn.execute(
                        """insert into learning_cases
                        (id, org_id, user_id, edition, model, label, conclusion, recommendation, evidence, platform, kpi, stage, saved_at)
                        values (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                        (
                            item_id, body["org_id"], body["user_id"], edition, body.get("model",""), body.get("label",""),
                            body.get("conclusion",""), body.get("recommendation",""), body.get("evidence",""),
                            body.get("platform",""), body.get("kpi",""), body.get("stage",""), saved_at
                        )
                    )
                    row = conn.execute("select * from learning_cases where id=?", (item_id,)).fetchone()
                self.send_json({"ok": True, "item": rowdict(row)})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/export-pptx":
            try:
                body = self.read_json()
                pptx = make_pptx(body)
                filename = re.sub(r"[^0-9A-Za-z一-龥_-]+", "_", body.get("title") or "策略报告") + ".pptx"
                self.send_response(200)
                self.send_header("Content-Type", "application/vnd.openxmlformats-officedocument.presentationml.presentation")
                self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{quote(filename)}")
                self.send_header("Content-Length", str(len(pptx)))
                self.end_headers()
                self.wfile.write(pptx)
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/social-plugin/open":
            try:
                body = self.read_json()
                platform = social_platform(body.get("platform"))
                url = body.get("url") or SOCIAL_PLUGIN_URLS[platform]
                subprocess.Popen(["open", "-a", "Google Chrome", url])
                self.send_json({"ok": True, "platform": platform, "url": url, "message": "已打开 Chrome 采集页面"})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/social-plugin/import-latest":
            try:
                body = self.read_json()
                platform = social_platform(body.get("platform"))
                path = latest_social_export(platform)
                if not path:
                    raise ValueError("未找到插件导出的 Excel。请先在 Chrome 插件里完成采集并导出。")
                result = build_social_plugin_dataset(path.read_bytes(), path.name, platform)
                result["platformKey"] = platform
                result["exportPath"] = str(path)
                result["exportedAt"] = datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
                self.send_json({"ok": True, "dataset": result})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/import-video-xlsx":
            length = int(self.headers.get("Content-Length", "0"))
            filename = parse_qs(parsed.query).get("filename", ["视频采集数据.xlsx"])[0]
            try:
                data = self.rfile.read(length)
                result = build_video_dataset_from_workbook(data, filename)
                self.send_json({"ok": True, "dataset": result})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/import-vertical-xlsx":
            length = int(self.headers.get("Content-Length", "0"))
            filename = parse_qs(parsed.query).get("filename", ["垂媒正反向排名.xlsx"])[0]
            try:
                data = self.rfile.read(length)
                result = build_vertical_media_dataset_from_workbook(data, filename)
                result = remember_vertical_dataset(data, filename, result)
                self.send_json({"ok": True, "dataset": result})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/import-rag-file":
            length = int(self.headers.get("Content-Length", "0"))
            filename = parse_qs(parsed.query).get("filename", ["rag_material"])[0]
            try:
                data = self.rfile.read(length)
                result = parse_rag_file(data, filename)
                self.send_json({"ok": True, "dataset": result})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/import-rag-seed":
            try:
                result = bundled_rag_package()
                self.send_json({"ok": True, "dataset": result})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/founder-archives/seed":
            try:
                body = self.read_json()
                edition = edition_from(body.get("edition", "china"))
                saved = save_founder_items(founder_seed_items(), edition=edition)
                self.send_json({"ok": True, "items": saved, "count": len(saved)})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/founder-archives/run-weekly":
            try:
                body = self.read_json()
                edition = edition_from(body.get("edition", "china"))
                result = run_founder_weekly_crawl(edition=edition, manual=True)
                self.send_json(result)
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/ai/founder-talk":
            try:
                body = self.read_json()
                edition = edition_from(body.get("edition", "china"))
                person = str(body.get("person") or "").strip()
                scene = str(body.get("scene") or "发布会").strip()
                brief = str(body.get("brief") or "").strip()
                if not person:
                    raise ValueError("请选择创始人/高管。")
                archives = [x for x in founder_archive_rows(edition=edition) if x.get("person") == person][:12]
                if not archives:
                    archives = save_founder_items(founder_seed_items(), edition=edition)
                    archives = [x for x in archives if x.get("person") == person][:12]
                profile = {
                    "brand": archives[0].get("brand") if archives else "",
                    "person": person,
                    "role": archives[0].get("role") if archives else "",
                    "styleTags": sorted({t for x in archives for t in (x.get("language_style_tags") or [])})
                }
                errors = {}
                draft = ""
                review = ""
                try:
                    draft = call_qwen(founder_talk_prompt(profile, scene, brief, archives), temperature=.28, profile="fast", timeout=60)
                except Exception as exc:
                    errors["qwen"] = str(exc)
                    draft = "\n".join([
                        f"核心话术：围绕{brief or scene}，用{profile.get('brand','品牌')}{person}公开表达中常见的用户视角、事实证据和行动承诺来组织内容。",
                        "表达拆解：先讲用户问题，再讲产品/技术逻辑，最后给出后续动作。",
                        "可发布版本：这件事我们先回到用户真实场景里看。用户关心的不是概念，而是每天用起来是否更安心、更高效、更有确定性。",
                        "注意事项：当前为本地规则兜底生成，正式发布前需要人工复核事实依据。"
                    ])
                try:
                    review = call_deepseek(founder_quality_prompt(profile, scene, brief, draft), temperature=.2, profile="fast", timeout=120, max_tokens=700)
                except Exception as exc:
                    errors["deepseek"] = str(exc)
                    review = "质检结论：DeepSeek暂未完成复核，请人工检查事实依据、过度承诺和舆论风险。"
                self.send_json({"ok": True, "draft": draft, "review": review, "errors": errors, "qwen": qwen_config(), "deepseek": deepseek_config()})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/ai/qwen-strategy":
            try:
                body = self.read_json()
                context = body.get("context", {})
                text = call_qwen(llm_strategy_prompt(context, "千问"))
                self.send_json({"ok": True, "text": text, "qwen": qwen_config()})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/ai/creator-tags":
            try:
                body = self.read_json()
                creator = body.get("creator", {})
                campaign = body.get("campaign", {})
                text = call_qwen(creator_tag_prompt(creator, campaign), temperature=.25)
                tags = parse_json_object(text)
                self.send_json({"ok": True, "tags": tags, "raw": text, "qwen": qwen_config()})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/ai/vertical-rank-learning":
            try:
                body = self.read_json()
                context = body.get("context", {})
                text = call_qwen(vertical_learning_prompt(context), temperature=.25)
                knowledge = save_vertical_ai_learning(context, text)
                self.send_json({"ok": True, "text": text, "knowledgeItem": knowledge, "qwen": qwen_config()})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/ai/rag-strategy":
            try:
                body = self.read_json()
                question = str(body.get("question") or "").strip()
                project = body.get("project") or {}
                references = body.get("references") or []
                mode = "deep" if body.get("mode") == "deep" else "fast"
                if not question:
                    raise ValueError("请输入策略问题。")
                errors = {}
                used_model = "local-rag"
                try:
                    text = call_qwen(rag_strategy_prompt(question, project, references), temperature=.28, profile=mode)
                    used_model = "qwen"
                except Exception as exc:
                    errors["qwen"] = str(exc)
                    try:
                        text = call_deepseek(rag_strategy_prompt(question, project, references), temperature=.25, profile=mode, timeout=60)
                        used_model = "deepseek"
                    except Exception as ds_exc:
                        errors["deepseek"] = str(ds_exc)
                        text = local_rag_strategy_answer(question, project, references)
                self.send_json({
                    "ok": True,
                    "text": text,
                    "model": used_model,
                    "mode": mode,
                    "modelLabel": "MMN深度策略" if mode == "deep" else "MMN快速策略",
                    "references": references[:8],
                    "errors": errors,
                    "qwen": qwen_config(mode),
                    "deepseek": deepseek_config(mode)
                })
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/ai/model-identities":
            try:
                body = self.read_json()
                edition = edition_from(body.get("edition", "china"))
                raw_models = [str(x).strip() for x in (body.get("models") or []) if str(x).strip()]
                raw_models = list(dict.fromkeys(raw_models))[:80]
                if not raw_models:
                    raise ValueError("缺少车型列表。")
                fallback = [rule_model_identity(x) for x in raw_models]
                errors = {}
                used_model = "local-rule"
                try:
                    text = call_qwen(model_identity_prompt(raw_models), temperature=.1, profile="fast", timeout=45)
                    parsed_items = parse_json_object(text)
                    if isinstance(parsed_items, dict):
                        parsed_items = parsed_items.get("items") or parsed_items.get("models") or []
                    if not isinstance(parsed_items, list) or not parsed_items:
                        raise ValueError("Qwen未返回车型数组")
                    saved = normalize_model_identity_records(parsed_items, edition=edition, source="qwen")
                    used_model = "qwen"
                except Exception as exc:
                    errors["qwen"] = str(exc)
                    saved = []
                if identity_needs_deepseek_review(saved) and deepseek_config()["configured"]:
                    try:
                        text = call_deepseek(model_identity_prompt(raw_models), temperature=.1, profile="fast", timeout=45)
                        parsed_items = parse_json_object(text)
                        if isinstance(parsed_items, dict):
                            parsed_items = parsed_items.get("items") or parsed_items.get("models") or []
                        if not isinstance(parsed_items, list) or not parsed_items:
                            raise ValueError("DeepSeek未返回车型数组")
                        saved = normalize_model_identity_records(parsed_items, edition=edition, source="qwen+deepseek" if used_model == "qwen" else "deepseek")
                        used_model = "qwen+deepseek" if used_model == "qwen" else "deepseek"
                    except Exception as exc:
                        errors["deepseek"] = str(exc)
                if not saved:
                    saved = normalize_model_identity_records(fallback, edition=edition, source="local-rule")
                    used_model = "local-rule"
                self.send_json({"ok": True, "items": saved, "model": used_model, "errors": errors, "deepseek": deepseek_config()})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/ai/model-judgment":
            try:
                body = self.read_json()
                text = str(body.get("text") or "").strip()
                project = body.get("project") or {}
                edition = edition_from(body.get("edition", "china"))
                if not text:
                    raise ValueError("请输入车型判断。")
                errors = {}
                try:
                    raw = call_qwen(model_judgment_prompt(text, project), temperature=.2, profile="fast", timeout=45)
                    item = parse_json_object(raw)
                    used_model = "qwen"
                except Exception as exc:
                    errors["qwen"] = str(exc)
                    item = local_model_judgment(text, project)
                    used_model = "local-rule"
                if not item.get("model_name"):
                    item["model_name"] = project.get("model") or "待识别车型"
                if not item.get("brand_name"):
                    item["brand_name"] = project.get("brand") or infer_brand_from_model(item.get("model_name"))
                normalize_model_identity_records([{
                    "rawName": item.get("model_name"),
                    "normalizedName": item.get("model_name"),
                    "brandName": item.get("brand_name"),
                    "modelFamily": item.get("model_name"),
                    "energyType": "UNKNOWN",
                    "variantName": "",
                    "canonicalKey": "|".join([item.get("brand_name") or "UNKNOWN", item.get("model_name") or "UNKNOWN", "UNKNOWN", ""]),
                    "confidence": item.get("confidence") or "low",
                    "reason": "来自车型判断工作台"
                }], edition=edition, source=used_model)
                saved, knowledge = save_model_judgment_asset(item, text, edition=edition)
                self.send_json({"ok": True, "item": saved, "knowledgeItem": knowledge, "model": used_model, "errors": errors})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/ai/openai-strategy":
            try:
                body = self.read_json()
                context = body.get("context", {})
                text = call_openai(llm_strategy_prompt(context, "ChatGPT/OpenAI"))
                self.send_json({"ok": True, "text": text, "openai": openai_config()})
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path == "/api/ai/fusion-strategy":
            try:
                body = self.read_json()
                context = body.get("context", {})
                qwen_text = deepseek_text = openai_text = None
                errors = {}
                rules = rule_strategy(context)
                if qwen_config()["configured"]:
                    try:
                        qwen_text = call_qwen(llm_strategy_prompt(context, "千问"))
                    except Exception as exc:
                        errors["qwen"] = str(exc)
                if deepseek_config()["configured"]:
                    try:
                        deepseek_text = call_deepseek(llm_strategy_prompt(context, "DeepSeek策略质检"), temperature=.2)
                    except Exception as exc:
                        errors["deepseek"] = str(exc)
                if openai_config()["configured"]:
                    try:
                        openai_text = call_openai(llm_strategy_prompt(context, "ChatGPT/OpenAI"))
                    except Exception as exc:
                        errors["openai"] = str(exc)
                fused = fuse_strategy(context, qwen_text=qwen_text, deepseek_text=deepseek_text, openai_text=openai_text, rule_text=rules)
                self.send_json({
                    "ok": True,
                    "text": fused,
                    "parts": {"qwen": qwen_text, "deepseek": deepseek_text, "openai": openai_text, "rules": rules},
                    "errors": errors,
                    "qwen": qwen_config(),
                    "deepseek": deepseek_config(),
                    "openai": openai_config()
                })
            except Exception as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        if parsed.path != "/api/import-xlsx":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        filename = parse_qs(parsed.query).get("filename", ["导入数据.xlsx"])[0]
        try:
            data = self.rfile.read(length)
            result = build_dataset_from_workbook(data, filename)
            self.send_json({"ok": True, "dataset": result})
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, 400)

    def log_message(self, format, *args):
        pass

class Server(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    init_db()
    schedule_founder_weekly_crawl()
    with Server(("127.0.0.1", PORT), Handler) as server:
        print(f"中国汽车营销引擎已启动：http://127.0.0.1:{PORT}")
        print("关闭此窗口即可停止系统。")
        Timer(0.7, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
