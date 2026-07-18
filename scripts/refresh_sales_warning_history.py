#!/usr/bin/env python3
"""Refresh monitored-model monthly sales without touching latest warning data.

This script reads the existing warning model list and verified launch dates, then
writes only ``data/dongchedi_sales/sales_warning_history.json``.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
RANK_API_URL = "https://www.dongchedi.com/motor/pc/car/rank_data"
SOURCE_URL = "https://www.dongchedi.com/sales"
SIZE_RANK_TYPES = {
    "微型车": ("micro_car", "0"),
    "小型车": ("small_car", "1"),
    "紧凑型车": ("compact_car", "2"),
    "中型车": ("mid_car", "3"),
    "中大型车": ("mid_large_car", "4"),
    "大型车": ("large_car", "5"),
    "小型SUV": ("small_suv", "10"),
    "紧凑型SUV": ("compact_suv", "11"),
    "中型SUV": ("mid_suv", "12"),
    "中大型SUV": ("mid_large_suv", "13"),
    "大型SUV": ("large_suv", "14"),
}


def month_range(end_period: str, count: int) -> list[str]:
    year, month = (int(value) for value in end_period.split("-", 1))
    index = year * 12 + month - 1
    periods = []
    for delta in range(count - 1, -1, -1):
        value = index - delta
        periods.append(f"{value // 12:04d}-{value % 12 + 1:02d}")
    return periods


def fetch_rank(period: str, detail_type: str, timeout: int) -> list[dict]:
    params = {
        "city_name": "北京",
        "count": 100,
        "offset": 0,
        "month": period.replace("-", ""),
        "new_energy_type": "",
        "rank_data_type": 11,
        "brand_id": "",
        "price": "",
        "manufacturer": "",
        "nation": 0,
        "outter_detail_type": detail_type,
    }
    request = Request(
        f"{RANK_API_URL}?{urlencode(params)}",
        headers={
            "Accept": "application/json,text/plain,*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 Chrome/126.0.0.0 Safari/537.36",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("status") != 0:
        raise RuntimeError(str(payload.get("prompts") or payload.get("message") or "懂车帝月榜请求失败"))
    data = payload.get("data") or {}
    rows = data.get("list") or []
    if (data.get("paging") or {}).get("has_more"):
        raise RuntimeError(f"{period} 榜单超过100行，拒绝保存不完整历史")
    if not isinstance(rows, list):
        raise RuntimeError(f"{period} 榜单结构异常")
    return rows


def segment_top3_reference(rows: list[dict]) -> dict:
    ranked = sorted(
        (row for row in rows if int(row.get("rank") or 0) > 0 and int(row.get("count") or 0) >= 0),
        key=lambda row: int(row.get("rank") or 0),
    )[:3]
    if len(ranked) != 3:
        raise RuntimeError("细分市场榜单不足3款车型，不能计算前三平均销量")
    return {
        "averageSales": int(round(sum(int(row.get("count") or 0) for row in ranked) / 3)),
        "vehicles": [
            {
                "seriesId": str(row.get("series_id") or ""),
                "model": str(row.get("series_name") or "").strip(),
                "sales": int(row.get("count") or 0),
                "rank": int(row.get("rank") or 0),
            }
            for row in ranked
        ],
    }


def build_history(latest: dict, cycles: dict, *, rate_limit: float, timeout: int) -> dict:
    end_period = str(latest.get("period") or "")
    vehicles = latest.get("saic_vehicles") or []
    if not end_period or not vehicles:
        raise ValueError("最新销量预警数据缺少周期或车型")
    periods = month_range(end_period, 6)
    targets = {}
    for vehicle in vehicles:
        series_id = str(vehicle.get("series_id") or "")
        cycle = cycles.get(series_id) or {}
        launch_date = str(cycle.get("launchDate") or "")
        size_class = str(vehicle.get("size_class") or "")
        if not series_id or len(launch_date) < 7 or size_class not in SIZE_RANK_TYPES:
            raise ValueError(f"车型 {vehicle.get('series_name') or series_id} 缺少已核验上市日期或榜单分类")
        rank_type, detail_type = SIZE_RANK_TYPES[size_class]
        targets[series_id] = {
            "seriesId": series_id,
            "model": vehicle.get("series_name") or "",
            "launchDate": launch_date,
            "rankType": rank_type,
            "detailType": detail_type,
            "latestSales": int(vehicle.get("sales_volume") or 0),
            "months": [],
        }

    requests = sorted({
        (period, target["rankType"], target["detailType"])
        for target in targets.values()
        for period in periods
        if period >= target["launchDate"][:7]
    })
    last_request_at = 0.0
    for index, (period, rank_type, detail_type) in enumerate(requests, 1):
        wait = rate_limit - (time.monotonic() - last_request_at)
        if wait > 0:
            time.sleep(wait)
        rows = fetch_rank(period, detail_type, timeout)
        last_request_at = time.monotonic()
        by_id = {str(row.get("series_id") or ""): row for row in rows}
        top3_reference = segment_top3_reference(rows)
        for target in targets.values():
            if target["rankType"] != rank_type or period < target["launchDate"][:7]:
                continue
            row = by_id.get(target["seriesId"])
            if row:
                target["months"].append({
                    "period": period,
                    "sales": int(row.get("count") or 0),
                    "rank": int(row.get("rank") or 0),
                    "rankType": rank_type,
                    "segmentTop3AverageSales": top3_reference["averageSales"],
                    "segmentTop3Vehicles": top3_reference["vehicles"],
                })
        print(f"[{index}/{len(requests)}] {period} {rank_type}: {len(rows)} rows", flush=True)

    for target in targets.values():
        latest_month = next((item for item in target["months"] if item["period"] == end_period), None)
        if not latest_month or latest_month["sales"] != target["latestSales"]:
            raise RuntimeError(
                f"{target['model']} {end_period} 历史值与已核验当月销量不一致："
                f"{latest_month and latest_month['sales']} != {target['latestSales']}"
            )
        target.pop("detailType", None)
        target.pop("latestSales", None)

    return {
        "schemaVersion": "1.1",
        "source": "dongchedi_public_rank_api",
        "sourceLabel": "懂车帝月销量榜",
        "sourceUrl": SOURCE_URL,
        "updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "latestPeriod": end_period,
        "windowPeriods": periods,
        "vehicles": targets,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--latest", default="data/dongchedi_sales/sales_warning_latest.json")
    parser.add_argument("--cycles", default="data/sales_warning_cycles.json")
    parser.add_argument("--output", default="data/dongchedi_sales/sales_warning_history.json")
    parser.add_argument("--rate-limit", type=float, default=10.0)
    parser.add_argument("--timeout", type=int, default=20)
    args = parser.parse_args()
    latest_path, cycles_path, output_path = (ROOT / args.latest, ROOT / args.cycles, ROOT / args.output)
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    cycles = json.loads(cycles_path.read_text(encoding="utf-8"))
    payload = build_history(latest, cycles, rate_limit=max(0.0, args.rate_limit), timeout=args.timeout)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(output_path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output_path)
    print(f"saved: {output_path}")


if __name__ == "__main__":
    main()
