"""集团营销看板 Demo 的只读数据聚合。

所有指标都保留原始数据口径：销量榜只表达榜单趋势，社媒声量只表达
已采集公开平台样本，垂媒正反向排名只作为 VOC 行为信号。
"""

from __future__ import annotations

import json
import math
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


LAUNCH_MODELS = (
    {"model": "奥迪E7X", "brand": "上汽奥迪", "aliases": ("奥迪E7X",)},
    {"model": "奥迪E5 Sportback", "brand": "上汽奥迪", "aliases": ("奥迪E5 Sportback", "奥迪E5")},
    {"model": "智己LS8", "brand": "智己", "aliases": ("智己LS8",)},
    {"model": "MG4", "brand": "MG", "aliases": ("MG4",)},
    {"model": "荣威i6", "brand": "荣威", "aliases": ("荣威i6",)},
    {"model": "别克至境E7", "brand": "上汽通用别克", "aliases": ("别克至境E7",)},
    {"model": "ID.ERA 9X", "brand": "上汽大众", "aliases": ("ID.ERA 9X",)},
    {"model": "尚界Z7", "brand": "尚界", "aliases": ("尚界Z7",)},
)

MARKET_DIMENSIONS = (
    {"key": "energy", "label": "能源形式", "note": "纯电 / 插混 / 增程 / 燃油", "items": (
        ("ev", "纯电"), ("phev", "插电式混动"), ("erev", "增程式"), ("fuel", "燃油"),
    )},
    {"key": "car", "label": "轿车级别", "note": "按懂车帝车身级别", "items": (
        ("micro_car", "微型车"), ("small_car", "小型车"), ("compact_car", "紧凑型车"),
        ("mid_car", "中型车"), ("mid_large_car", "中大型车"), ("large_car", "大型车"),
    )},
    {"key": "suv", "label": "SUV 级别", "note": "按懂车帝车身级别", "items": (
        ("small_suv", "小型 SUV"), ("compact_suv", "紧凑型 SUV"), ("mid_suv", "中型 SUV"),
        ("mid_large_suv", "中大型 SUV"), ("large_suv", "大型 SUV"),
    )},
    {"key": "mpv", "label": "MPV 级别", "note": "按懂车帝车身级别", "items": (
        ("compact_mpv", "紧凑型 MPV"), ("mid_mpv", "中型 MPV"),
        ("mid_large_mpv", "中大型 MPV"), ("large_mpv", "大型 MPV"),
    )},
)

SAIC_BRANDS = {
    "上汽大众", "上汽奥迪", "智己", "智己汽车",
    "MG", "名爵", "荣威", "上汽通用别克", "别克", "凯迪拉克", "大通",
    "五菱汽车", "宝骏", "尚界", "沃尔沃",
}

SAIC_VOLKSWAGEN_MODELS = ("朗逸", "帕萨特", "途观", "途岳", "途昂", "凌渡", "威然", "ID.3", "ID.4 X", "ID.6 X", "ID. ERA")
SAIC_AUDI_MODELS = ("奥迪E5", "奥迪E7X")
E7X_EVALUATION_PATH = Path(__file__).with_name("data") / "e7x_product_evaluation_2026-06.json"


def _safe_json(value, fallback):
    try:
        return json.loads(value or "")
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback


def load_e7x_product_evaluation(path=E7X_EVALUATION_PATH):
    """读取由客户工作簿提取的五车聚合口径，并补齐可复核派生指标。"""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {"status": "missing", "source": {}, "models": [], "platforms": [], "attributes": []}
    models = payload.get("models") or []
    own_model = str(payload.get("ownModel") or "")
    if own_model != "奥迪E7X" or len(models) != 5:
        return {"status": "invalid", "source": payload.get("source") or {}, "models": [], "platforms": [], "attributes": []}
    for item in models:
        item["isOwn"] = item.get("model") == own_model
        item["engagementPerVoice"] = round(item.get("engagement", 0) / max(1, item.get("voice", 0)), 2)
    for metric, rank_key in (("voice", "voiceRank"), ("engagement", "engagementRank"), ("overallNsr", "overallNsrRank")):
        ordered = sorted(models, key=lambda item: item.get(metric) if item.get(metric) is not None else -1, reverse=True)
        for index, item in enumerate(ordered, 1):
            item[rank_key] = index
    valid_vertical = sorted((item for item in models if item.get("verticalNsr") is not None), key=lambda item: item["verticalNsr"], reverse=True)
    for index, item in enumerate(valid_vertical, 1):
        item["verticalNsrRank"] = index
    for item in payload.get("attributes") or []:
        item["deltaVsAverage"] = round(item.get("ownNsr", 0) - item.get("averageNsr", 0), 4)
    payload["status"] = "available"
    payload["validVerticalModels"] = len(valid_vertical)
    return payload


def _period_key(label):
    text = str(label or "").strip()
    full = re.search(r"(20\d{2})[.\-/](\d{1,2})(?:[.\-/](\d{1,2}))?", text)
    if full:
        return int(full.group(1)), int(full.group(2)), int(full.group(3) or 1)
    short = re.search(r"(\d{1,2})\.(\d{1,2})", text)
    if short:
        return 2026, int(short.group(1)), int(short.group(2))
    return 0, 0, 0


def parse_cpca_ice_market(payload):
    """解析乘联会 FuelMarket 的 ICE 批发/零售月度量与份额。"""
    if not isinstance(payload, list):
        return None
    rows_by_period = {}
    for section in payload:
        for item in (section.get("dataList") or []) if isinstance(section, dict) else []:
            ice = item.get("ICE") if isinstance(item, dict) else None
            match = re.fullmatch(r"(20\d{2})-(\d{1,2})月", str(item.get("月份") or "").strip()) if isinstance(item, dict) else None
            if not match or not isinstance(ice, list) or len(ice) < 4:
                continue
            try:
                year, month = int(match.group(1)), int(match.group(2))
                values = [float(value) for value in ice[:4]]
            except (TypeError, ValueError):
                continue
            if not 1 <= month <= 12 or not all(math.isfinite(value) for value in values):
                continue
            wholesale, retail, wholesale_share, retail_share = values
            if wholesale < 0 or retail < 0 or not 0 <= wholesale_share <= 100 or not 0 <= retail_share <= 100:
                continue
            period = f"{year:04d}-{month:02d}"
            rows_by_period[period] = {
                "period": period,
                "wholesaleSales": round(wholesale * 10000),
                "retailSales": round(retail * 10000),
                "wholesaleShare": round(wholesale_share / 100, 4),
                "retailShare": round(retail_share / 100, 4),
            }
    rows = list(rows_by_period.values())
    rows.sort(key=lambda item: item["period"])
    if len(rows) < 2:
        return None
    previous, latest = rows[-2:]
    previous_year, previous_month = map(int, previous["period"].split("-"))
    latest_year, latest_month = map(int, latest["period"].split("-"))
    if latest_year * 12 + latest_month - (previous_year * 12 + previous_month) != 1:
        return None
    retail_change = (
        (latest["retailSales"] - previous["retailSales"]) / previous["retailSales"]
        if previous["retailSales"]
        else None
    )
    wholesale_change = (
        (latest["wholesaleSales"] - previous["wholesaleSales"]) / previous["wholesaleSales"]
        if previous["wholesaleSales"]
        else None
    )
    return {
        "status": "available",
        "latestPeriod": latest["period"],
        "previousPeriod": previous["period"],
        "retailSales": latest["retailSales"],
        "previousRetailSales": previous["retailSales"],
        "retailShare": latest["retailShare"],
        "previousRetailShare": previous["retailShare"],
        "changeRate": round(retail_change, 4) if retail_change is not None else None,
        "shareChangePoints": round((latest["retailShare"] - previous["retailShare"]) * 100, 1),
        "wholesaleSales": latest["wholesaleSales"],
        "previousWholesaleSales": previous["wholesaleSales"],
        "wholesaleShare": latest["wholesaleShare"],
        "previousWholesaleShare": previous["wholesaleShare"],
        "wholesaleChangeRate": round(wholesale_change, 4) if wholesale_change is not None else None,
        "sourceLabel": "乘联会 FuelMarket",
        "sourceUrl": "https://data.cpcadata.com/FuelMarket",
    }


def _canonical_launch(model_name):
    value = str(model_name or "").strip()
    for launch in LAUNCH_MODELS:
        if value in launch["aliases"]:
            return launch["model"]
    return ""


def _is_saic_sales_row(row):
    brand = str(row.get("normalized_brand_name") or row.get("brand_name") or "").strip()
    model = str(row.get("normalized_series_name") or row.get("series_name") or "").strip()
    if brand in SAIC_BRANDS:
        return True
    if brand == "大众":
        return model.startswith(SAIC_VOLKSWAGEN_MODELS)
    if brand in {"奥迪", "奥迪AUDI"}:
        return model.startswith(SAIC_AUDI_MODELS)
    return False


def _sales_items(payload):
    if not isinstance(payload, dict):
        return []
    return payload.get("items") or payload.get("records") or []


def _sales_model_key(row):
    return str(row.get("normalized_series_name") or row.get("series_name") or "").strip()


def _derive_fuel_periods(grouped):
    """在独立燃油榜缺失时，从全国总榜 Top10 排除新能源车型。"""
    derived_periods = set()
    energy_keys = ("new_energy", "ev", "phev", "erev")
    for period, overall_rows in grouped.get("series", {}).items():
        if period in grouped.get("fuel", {}):
            continue
        energy_models = {
            _sales_model_key(row)
            for key in energy_keys
            for row in grouped.get(key, {}).get(period, [])
            if _sales_model_key(row)
        }
        if not energy_models:
            continue
        grouped["fuel"][period] = [
            row
            for row in sorted(overall_rows, key=lambda item: item.get("rank") or 999)[:10]
            if _sales_model_key(row) not in energy_models
        ]
        derived_periods.add(period)
    return derived_periods


def merge_sales_payloads(payloads):
    """合并不同周期的销量快照，并按稳定记录标识去重。"""
    unique = {}
    for payload in payloads:
        for item in _sales_items(payload):
            identity = item.get("record_id") or (
                item.get("rank_type"),
                item.get("period_start"),
                item.get("rank"),
                item.get("series_name"),
            )
            unique[str(identity)] = item
    return {"items": list(unique.values())}


def build_segment_cards(sales_payload):
    items = _sales_items(sales_payload)
    labels = {key: label for dimension in MARKET_DIMENSIONS for key, label in dimension["items"]}
    grouped = defaultdict(lambda: defaultdict(list))
    for item in items:
        key = str(item.get("rank_type") or "")
        period = str(item.get("period_start") or "")
        if (key in labels or key in {"series", "new_energy"}) and period:
            grouped[key][period].append(item)

    derived_fuel_periods = _derive_fuel_periods(grouped)

    cards = []
    for key, label in labels.items():
        periods = sorted(grouped[key])
        latest_period = periods[-1] if periods else ""
        previous_period = periods[-2] if len(periods) > 1 else ""
        latest_rows = sorted(grouped[key].get(latest_period, []), key=lambda row: row.get("rank") or 999)[:10]
        previous_rows = sorted(grouped[key].get(previous_period, []), key=lambda row: row.get("rank") or 999)[:10]
        latest_total = sum(int(row.get("sales_volume") or row.get("sales") or 0) for row in latest_rows)
        previous_total = sum(int(row.get("sales_volume") or row.get("sales") or 0) for row in previous_rows)
        data_basis = "overall_top10_minus_new_energy" if key == "fuel" and latest_period in derived_fuel_periods else "independent_rank"
        previous_data_basis = "overall_top10_minus_new_energy" if key == "fuel" and previous_period in derived_fuel_periods else "independent_rank"
        comparison_basis_changed = bool(previous_period and data_basis != previous_data_basis)
        change_rate = (
            ((latest_total - previous_total) / previous_total)
            if previous_total and not comparison_basis_changed
            else None
        )
        saic_rows = [
            {
                "rank": row.get("rank"),
                "model": row.get("normalized_series_name") or row.get("series_name") or "—",
                "brand": row.get("normalized_brand_name") or row.get("brand_name") or "—",
                "sales": int(row.get("sales_volume") or row.get("sales") or 0),
            }
            for row in latest_rows
            if _is_saic_sales_row(row)
        ]
        cards.append({
            "key": key,
            "label": label,
            "latestPeriod": latest_period[:7],
            "previousPeriod": previous_period[:7],
            "top10Sales": latest_total,
            "previousTop10Sales": previous_total,
            "changeRate": round(change_rate, 4) if change_rate is not None else None,
            "leader": ({
                "model": latest_rows[0].get("normalized_series_name") or latest_rows[0].get("series_name") or "—",
                "brand": latest_rows[0].get("normalized_brand_name") or latest_rows[0].get("brand_name") or "—",
                "sales": int(latest_rows[0].get("sales_volume") or latest_rows[0].get("sales") or 0),
            } if latest_rows else None),
            "saicTop10": saic_rows,
            "status": "available" if latest_rows or latest_period in derived_fuel_periods else "missing",
            "dataBasis": data_basis,
            "previousDataBasis": previous_data_basis,
            "comparisonBasisChanged": comparison_basis_changed,
            "scopeNote": (
                "懂车帝全国总榜 Top10 排除同期新能源榜车型后的燃油车型，非燃油独立榜、非全市场份额"
                if data_basis == "overall_top10_minus_new_energy"
                else "懂车帝细分榜 Top10，非全市场份额"
            ),
        })
    return cards


def build_market_dimensions(sales_payload):
    cards = {item["key"]: item for item in build_segment_cards(sales_payload)}
    return [
        {
            "key": dimension["key"],
            "label": dimension["label"],
            "note": dimension["note"],
            "items": [cards[key] for key, _ in dimension["items"]],
        }
        for dimension in MARKET_DIMENSIONS
    ]


def apply_cpca_fuel_market(market_dimensions, fuel_market):
    if not fuel_market or fuel_market.get("status") != "available" or not market_dimensions:
        return market_dimensions
    fuel = next((item for item in market_dimensions[0].get("items", []) if item.get("key") == "fuel"), None)
    if not fuel:
        return market_dimensions
    original_basis = fuel.get("dataBasis")
    saic_rank_period = fuel.get("latestPeriod")
    saic_rank_basis = (
        "missing"
        if fuel.get("status") != "available" or not saic_rank_period
        else "dongchedi_fuel_top10"
        if original_basis == "independent_rank"
        else "dongchedi_national_overall_top10"
    )
    fuel.update({
        "latestPeriod": fuel_market["latestPeriod"],
        "previousPeriod": fuel_market["previousPeriod"],
        "marketSales": fuel_market["retailSales"],
        "previousMarketSales": fuel_market["previousRetailSales"],
        "marketShare": fuel_market["retailShare"],
        "previousMarketShare": fuel_market["previousRetailShare"],
        "shareChangePoints": fuel_market["shareChangePoints"],
        "changeRate": fuel_market["changeRate"],
        "wholesaleSales": fuel_market["wholesaleSales"],
        "wholesaleChangeRate": fuel_market["wholesaleChangeRate"],
        "status": "available",
        "dataBasis": "cpca_ice_retail_market",
        "previousDataBasis": "cpca_ice_retail_market",
        "comparisonBasisChanged": False,
        "sourceLabel": "乘联会 ICE 零售",
        "sourceUrl": fuel_market["sourceUrl"],
        "sourceFetchedAt": fuel_market.get("sourceFetchedAt"),
        "sourceStale": fuel_market.get("sourceStale") is True,
        "saicRankBasis": saic_rank_basis,
        "saicRankPeriod": saic_rank_period,
        "scopeNote": (
            "乘联会 ICE 零售整体市场销量与份额；懂车帝车型榜暂未接入，当前不判断上汽车型是否进入榜单"
            if saic_rank_basis == "missing"
            else "乘联会 ICE 零售整体市场销量与份额；上汽车型名次来自懂车帝燃油榜，两套来源的月份分别标注"
            if saic_rank_basis == "dongchedi_fuel_top10"
            else "乘联会 ICE 零售整体市场销量与份额；上汽车型名次来自懂车帝全国总榜，不代表燃油榜名次，两套来源的月份分别标注"
        ),
    })
    return market_dimensions


def _rows_with_demo_fallback(conn, sql, org_id, edition, params=()):
    rows = conn.execute(sql, (org_id, edition, *params)).fetchall()
    if rows or org_id == "local":
        return rows, False
    return conn.execute(sql, ("local", edition, *params)).fetchall(), True


def _latest_social_by_model(conn, org_id, edition):
    sql = """
        select keyword, result_json, created_at
        from social_trend_snapshots
        where org_id=? and edition=?
        order by created_at desc
    """
    rows, fallback = _rows_with_demo_fallback(conn, sql, org_id, edition)
    latest = {}
    for row in rows:
        canonical = _canonical_launch(row["keyword"])
        if not canonical or canonical in latest:
            continue
        result = _safe_json(row["result_json"], {})
        items = result.get("items") or []
        platforms = result.get("platforms") or []
        latest[canonical] = {
            "contentCount": len(items),
            "heat": round(sum(float(item.get("heat") or 0) for item in items), 1),
            "platformCount": sum(1 for item in platforms if int(item.get("contentCount") or 0) > 0),
            "commentCount": int((result.get("commentInsights") or {}).get("total") or 0),
            "confidence": result.get("confidenceLabel") or "未标注",
            "updatedAt": row["created_at"],
            "sourceMode": "TikHub 公开社媒样本",
        }
    return latest, fallback


def _vertical_signals(conn, org_id, edition):
    aliases = tuple(alias for launch in LAUNCH_MODELS for alias in launch["aliases"])
    placeholders = ",".join("?" for _ in aliases)
    sql = f"""
        select platform, period, own_model, competitor_model, positive_rank, negative_rank, updated_at
        from vertical_rank_assets
        where org_id=? and edition=? and own_model in ({placeholders})
    """
    rows, fallback = _rows_with_demo_fallback(conn, sql, org_id, edition, aliases)
    by_model_platform_period = defaultdict(list)
    for row in rows:
        canonical = _canonical_launch(row["own_model"])
        if not canonical:
            continue
        key = (canonical, row["platform"], row["period"])
        by_model_platform_period[key].append(row)

    output = {}
    for launch in LAUNCH_MODELS:
        model = launch["model"]
        platform_periods = defaultdict(list)
        for candidate_model, platform, period in by_model_platform_period:
            if candidate_model == model:
                platform_periods[platform].append(period)
        latest_rows = []
        latest_labels = []
        for platform, periods in platform_periods.items():
            latest_period = max(periods, key=_period_key)
            latest_labels.append(f"{platform} {latest_period}")
            latest_rows.extend(by_model_platform_period[(model, platform, latest_period)])
        positives = [row for row in latest_rows if row["positive_rank"] is not None]
        negatives = [row for row in latest_rows if row["negative_rank"] is not None]
        positive_leader = min(positives, key=lambda row: row["positive_rank"]) if positives else None
        risk_leader = min(negatives, key=lambda row: row["negative_rank"]) if negatives else None
        output[model] = {
            "positiveTop10": sum(int(row["positive_rank"]) <= 10 for row in positives),
            "negativeTop10": sum(int(row["negative_rank"]) <= 10 for row in negatives),
            "positiveLeader": positive_leader["competitor_model"] if positive_leader else "待补数据",
            "riskLeader": risk_leader["competitor_model"] if risk_leader else "待补数据",
            "platformCount": len(platform_periods),
            "periodCount": max([len(set(periods)) for periods in platform_periods.values()] or [0]),
            "latestPeriods": latest_labels,
            "relationCount": len(latest_rows),
            "status": "available" if latest_rows else "missing",
            "scopeNote": "垂媒正反向对比排名，作为 VOC 行为信号，不等同评论情绪",
        }
    return output, fallback


def build_group_dashboard_payload(conn, sales_payload, org_id="local", edition="china", fuel_market=None):
    market_dimensions = build_market_dimensions(sales_payload)
    apply_cpca_fuel_market(market_dimensions, fuel_market)
    product_evaluation = load_e7x_product_evaluation()
    social, social_fallback = _latest_social_by_model(conn, org_id, edition)
    voc, vertical_fallback = _vertical_signals(conn, org_id, edition)
    launches = []
    for launch in LAUNCH_MODELS:
        model = launch["model"]
        voice = social.get(model) or {
            "contentCount": None,
            "heat": None,
            "platformCount": 0,
            "commentCount": 0,
            "confidence": "待采集",
            "updatedAt": "",
            "sourceMode": "尚未形成该车型的持续社媒快照",
        }
        launches.append({"model": model, "brand": launch["brand"], "voice": voice, "voc": voc[model]})

    sales_items = _sales_items(sales_payload)
    rank_types = {str(item.get("rank_type") or "") for item in sales_items if item.get("rank_type")}
    sales_periods = {str(item.get("period_start") or "") for item in sales_items if item.get("period_start")}
    return {
        "ok": True,
        "meta": {
            "title": "上汽集团营销经营驾驶舱 Demo",
            "generatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "edition": edition,
            "dataMode": "真实数据 Beta",
            "demoFallback": social_fallback or vertical_fallback,
            "scope": "当前本地已导入与已采集数据，不代表集团全量数据",
        },
        "kpis": {
            "launchModels": len(LAUNCH_MODELS),
            "segmentCategories": len(rank_types),
            "salesPeriods": len(sales_periods),
            "socialPlatforms": max([item["voice"]["platformCount"] for item in launches] or [0]),
            "voiceReadyModels": sum(item["voice"]["contentCount"] is not None for item in launches),
            "vocReadyModels": sum(item["voc"]["status"] == "available" for item in launches),
        },
        "marketDimensions": market_dimensions,
        "segments": market_dimensions[0]["items"],
        "launches": launches,
        "productEvaluation": product_evaluation,
        "methodology": [
            "市场结构：纯电、插混、增程及车身级别采用懂车帝 Top10；燃油采用乘联会 ICE 零售整体市场月度数据。",
            "燃油卡的销量、环比与份额来自乘联会 FuelMarket；上汽车型名次仅来自懂车帝全国总榜，不表述为燃油榜名次。",
            "营销声量：已存 TikHub 公开社媒样本的内容量与互动热度，未采集车型明确留空。",
            "VOC：懂车帝与汽车之家正反向对比排名，仅作为用户比较行为信号。",
            "E7X产品评价：来自 AUDI E7X等5车产品评价_0710_v2.xlsx，数据期为2026年6月；声量、互动量和NSR均沿用工作簿定义。",
            "属性星图：横轴为E7X属性NSR，纵轴为E7X相对五车平均NSR的差值；工作簿未提供属性样本量，因此点大小不编码样本量。",
        ],
    }
