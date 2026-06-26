#!/usr/bin/env python3
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "dongchedi_sales"
BASE = "https://www.dongchedi.com"

SEGMENTS = [
    ("全国零售榜", "/sales/sale-x-x-x-x-x-x"),
    ("全部轿车", "/sales/sale-jc-x-x-x-x-x"),
    ("微型车", "/sales/sale-jc_1-x-x-x-x-x"),
    ("小型车", "/sales/sale-jc_2-x-x-x-x-x"),
    ("紧凑型车", "/sales/sale-jc_3-x-x-x-x-x"),
    ("中型车", "/sales/sale-jc_4-x-x-x-x-x"),
    ("中大型车", "/sales/sale-jc_5-x-x-x-x-x"),
    ("大型车", "/sales/sale-jc_6-x-x-x-x-x"),
    ("全部SUV", "/sales/sale-suv-x-x-x-x-x"),
    ("小型SUV", "/sales/sale-suv_1-x-x-x-x-x"),
    ("紧凑型SUV", "/sales/sale-suv_2-x-x-x-x-x"),
    ("中型SUV", "/sales/sale-suv_3-x-x-x-x-x"),
    ("中大型SUV", "/sales/sale-suv_4-x-x-x-x-x"),
    ("大型SUV", "/sales/sale-suv_5-x-x-x-x-x"),
    ("全部MPV", "/sales/sale-mpv-x-x-x-x-x"),
    ("小型MPV", "/sales/sale-mpv_1-x-x-x-x-x"),
    ("紧凑型MPV", "/sales/sale-mpv_2-x-x-x-x-x"),
    ("中型MPV", "/sales/sale-mpv_3-x-x-x-x-x"),
    ("中大型MPV", "/sales/sale-mpv_4-x-x-x-x-x"),
    ("大型MPV", "/sales/sale-mpv_5-x-x-x-x-x"),
    ("全部新能源", "/sales/sale-energy-x-x-x-x-x"),
    ("纯电动", "/sales/sale-energy_1-x-x-x-x-x"),
    ("插电式混动", "/sales/sale-energy_2-x-x-x-x-x"),
    ("增程式", "/sales/sale-energy_3-x-x-x-x-x"),
]


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def fetch_html(path):
    req = Request(
        BASE + path,
        headers={
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    return urlopen(req, timeout=18).read().decode("utf-8", "ignore")


def parse_page(path, segment):
    html = fetch_html(path)
    match = re.search(
        r'<script[^>]*>(\{.*?"page"\s*:\s*"/leaderboard/new_sales".*?\})</script>',
        html,
        re.S,
    )
    if not match:
        raise ValueError("未解析到懂车帝榜单服务端数据")
    data = json.loads(match.group(1))
    page_props = data.get("props", {}).get("pageProps", {})
    rank_data = page_props.get("rankData", {})
    rows = rank_data.get("list") or []
    title_match = re.search(r"<title>(\d{4}年\d{2}月).*?销量榜", html)
    month = title_match.group(1) if title_match else "最新月份"
    crawl_at = now_iso()
    items = []
    for row in rows:
        items.append(
            {
                "crawl_at": crawl_at,
                "source": "懂车帝销量榜",
                "month": month,
                "segment": segment,
                "segment_path": path,
                "rank": row.get("rank"),
                "series_id": row.get("series_id"),
                "series_name": row.get("series_name") or "",
                "brand_name": row.get("brand_name") or "",
                "sub_brand_name": row.get("sub_brand_name") or "",
                "sales": int(row.get("count") or 0),
                "price": row.get("price") or "",
                "last_rank": row.get("last_rank"),
                "source_url": BASE + path,
            }
        )
    return {"segment": segment, "path": path, "month": month, "items": items}


def write_outputs(records):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = OUT_DIR / f"dongchedi_sales_{stamp}.json"
    csv_path = OUT_DIR / f"dongchedi_sales_{stamp}.csv"
    latest_json = OUT_DIR / "latest.json"
    latest_csv = OUT_DIR / "latest.csv"

    payload = {
        "ok": True,
        "crawl_at": now_iso(),
        "source": "https://www.dongchedi.com/sales",
        "scope": "懂车帝销量榜各细分榜单首屏Top10",
        "segment_count": len(records),
        "row_count": sum(len(x["items"]) for x in records),
        "records": records,
    }
    json_text = json.dumps(payload, ensure_ascii=False, indent=2)
    json_path.write_text(json_text, encoding="utf-8")
    latest_json.write_text(json_text, encoding="utf-8")

    fields = [
        "crawl_at",
        "source",
        "month",
        "segment",
        "rank",
        "series_id",
        "series_name",
        "brand_name",
        "sub_brand_name",
        "sales",
        "price",
        "last_rank",
        "source_url",
    ]
    rows = [item for record in records for item in record["items"]]
    for path in (csv_path, latest_csv):
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
    return payload, json_path, csv_path


def main():
    records = []
    errors = []
    for segment, path in SEGMENTS:
        try:
            record = parse_page(path, segment)
            records.append(record)
            print(f"OK {segment}: {len(record['items'])} rows")
        except Exception as exc:
            errors.append({"segment": segment, "path": path, "error": str(exc)})
            print(f"FAIL {segment}: {exc}", file=sys.stderr)
    if not records:
        raise SystemExit("全部榜单抓取失败")
    payload, json_path, csv_path = write_outputs(records)
    if errors:
        error_path = OUT_DIR / "last_errors.json"
        error_path.write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved json: {json_path}")
    print(f"saved csv: {csv_path}")
    print(f"segments: {payload['segment_count']} rows: {payload['row_count']}")


if __name__ == "__main__":
    main()
