"""集团营销看板 Demo 的只读数据聚合。

所有指标都保留原始数据口径：销量榜只表达榜单趋势，社媒声量只表达
已采集公开平台样本，垂媒正反向排名只作为 VOC 行为信号。
"""

from __future__ import annotations

import json
import math
import os
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from mmn_data import module_path
from statistics import median


LAUNCH_MODELS = (
    {"model": "奥迪E7X", "brand": "上汽奥迪", "aliases": ("奥迪E7X", "AUDI E7X")},
    {"model": "奥迪E5 Sportback", "brand": "上汽奥迪", "aliases": ("奥迪E5 Sportback", "奥迪E5", "AUDI E5 Sportback", "AUDI E5")},
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
    "五菱汽车", "上汽通用五菱", "宝骏", "尚界", "沃尔沃", "飞凡", "飞凡汽车",
}

SAIC_VOLKSWAGEN_MODELS = ("朗逸", "帕萨特", "途观", "途岳", "途昂", "凌渡", "威然", "ID.3", "ID.4 X", "ID.6 X", "ID. ERA")
SAIC_AUDI_MODELS = ("奥迪E5", "奥迪E7X")
E7X_EVALUATION_PATH = module_path(
    "product_evaluation",
    "e7x_product_evaluation_2026-06.json",
    legacy=("e7x_product_evaluation_2026-06.json",),
)
SALES_WARNING_DEMO_PATH = module_path(
    "sales_warning", "sales_warning_demo_2026-06.json", legacy=("sales_warning_demo_2026-06.json",)
)
SALES_WARNING_LATEST_PATH = module_path(
    "sales_warning", "sales_warning_latest.json", legacy=("dongchedi_sales/sales_warning_latest.json",)
)
SALES_WARNING_OBSERVED_PATH = module_path(
    "sales_warning", "sales_warning_observed_2026-06.json", legacy=("dongchedi_sales/sales_warning_observed_2026-06.json",)
)
SALES_WARNING_MONITOR_SOURCE = "周对比次数正反向排名"

# 销量预警量价图的电池租用口径。这里保留懂车帝经销商报价原值，
# 仅在图表价格视图中扣除当前车型对应的 BaaS 电池价值。
BAAS_DISCOUNT_WAN = {
    "nio": 10.8,
    "onvo_l60": 5.7,
    "onvo": 8.6,
    "firefly": 4.0,
}


def _safe_json(value, fallback):
    try:
        return json.loads(value or "")
    except (TypeError, ValueError, json.JSONDecodeError):
        return fallback


def _baas_discount_view(model, manufacturer):
    """Return the current BaaS deduction rule for NIO's three brands."""
    model_text = str(model or "").strip()
    maker_text = str(manufacturer or "").strip()
    identity = f"{maker_text} {model_text}".lower()
    if "萤火虫" in identity or "firefly" in identity:
        return {"brand": "萤火虫", "discountWan": BAAS_DISCOUNT_WAN["firefly"]}
    if "乐道" in identity or "onvo" in identity:
        key = "onvo_l60" if re.search(r"(?:^|\D)l60(?:\D|$)", model_text.lower()) else "onvo"
        return {"brand": "乐道", "discountWan": BAAS_DISCOUNT_WAN[key]}
    if "蔚来" in identity or re.search(r"(?:^|\W)nio(?:\W|$)", identity):
        return {"brand": "蔚来", "discountWan": BAAS_DISCOUNT_WAN["nio"]}
    return {"brand": "", "discountWan": 0.0}


def _baas_price_view(model, manufacturer, price_display, price_source=""):
    """Build a traceable dealer-price view, applying BaaS only to three brands."""
    dealer_price_display = str(price_display or "价格待复核")
    prices = [
        float(value)
        for value in re.findall(r"\d+(?:\.\d+)?", dealer_price_display.replace(",", ""))
    ]
    dealer_start_price = prices[0] if prices else None
    rule = _baas_discount_view(model, manufacturer)
    discount = float(rule["discountWan"])
    baas_applied = dealer_start_price is not None and discount > 0
    adjusted_prices = [round(max(0.0, price - discount), 2) for price in prices[:2]] if baas_applied else prices[:2]
    if baas_applied:
        adjusted_display = (
            f"{adjusted_prices[0]:.2f}-{adjusted_prices[1]:.2f}万（BaaS后）"
            if len(adjusted_prices) > 1
            else f"{adjusted_prices[0]:.2f}万（BaaS后）"
        )
        adjusted_source = "dongchedi_dealer_price_baas_adjusted"
        price_basis = (
            f"懂车帝经销商报价扣除{rule['brand']}BaaS电池价值{discount:.2f}万元"
        )
    else:
        adjusted_display = dealer_price_display
        adjusted_source = str(price_source or "")
        price_basis = "懂车帝经销商报价"
    return {
        "priceDisplay": adjusted_display,
        "startPriceWan": adjusted_prices[0] if adjusted_prices else None,
        "priceSource": adjusted_source,
        "priceBasis": price_basis,
        "dealerPriceDisplay": dealer_price_display,
        "dealerStartPriceWan": dealer_start_price,
        "dealerPriceSource": str(price_source or ""),
        "baasApplied": baas_applied,
        "baasBrand": rule["brand"],
        "baasDiscountWan": discount if baas_applied else 0.0,
    }


def load_e7x_product_evaluation(path=None):
    """读取由客户工作簿提取的五车聚合口径，并补齐可复核派生指标。"""
    if path is None:
        path = module_path(
            "product_evaluation",
            "e7x_product_evaluation_2026-06.json",
            legacy=("e7x_product_evaluation_2026-06.json",),
        )
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


def _warning_level(performance_rate):
    if performance_rate >= 0.8:
        return "green", "正常"
    if performance_rate >= 0.25:
        return "yellow", "黄色预警"
    return "red", "红色预警"


def build_sales_warning_demo(path=SALES_WARNING_DEMO_PATH):
    """构建可复核的细分市场销量失速预警 Demo。"""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {"status": "missing", "source": {}, "segment": {}, "summary": {}, "saicModels": [], "ranking": []}

    models = []
    for item in payload.get("models") or []:
        adjustment = float(item.get("effectivePriceAdjustment") or 0)
        normalized = {
            **item,
            "sales": int(item.get("sales") or 0),
            "effectivePriceMin": round(float(item.get("priceMin") or 0) + adjustment, 2),
            "effectivePriceMax": round(float(item.get("priceMax") or item.get("priceMin") or 0) + adjustment, 2),
            "priceRule": "车电分离口径 -10万" if adjustment else "榜单展示价格",
        }
        models.append(normalized)
    models.sort(key=lambda item: item["sales"], reverse=True)
    for rank, item in enumerate(models, 1):
        item["rank"] = rank
        item["isSaic"] = _is_saic_sales_row({
            "brand_name": item.get("brand"),
            "series_name": item.get("model"),
        })

    saic_models = []
    for item in (model for model in models if model["isSaic"]):
        peers = [peer for peer in models if peer["model"] != item["model"]]
        benchmark_peers = sorted(peers, key=lambda peer: peer["sales"], reverse=True)
        benchmark = int(round(median([peer["sales"] for peer in benchmark_peers]))) if benchmark_peers else 0
        performance_rate = round(item["sales"] / benchmark, 4) if benchmark else 0
        level, level_label = _warning_level(performance_rate)
        yellow_line = int(round(benchmark * 0.5))
        red_line = int(round(benchmark * 0.25))
        saic_models.append({
            **item,
            "benchmark": benchmark,
            "performanceRate": performance_rate,
            "yellowLine": yellow_line,
            "redLine": red_line,
            "gapToWarningLine": max(0, yellow_line - item["sales"]),
            "level": level,
            "levelLabel": level_label,
            "peerBasis": "懂车帝同细分市场全量（仅排除本品）",
            "peerCount": len(peers),
            "benchmarkPeers": [
                {"model": peer["model"], "sales": peer["sales"], "effectivePriceMin": peer["effectivePriceMin"]}
                for peer in benchmark_peers[:3]
            ],
            "benchmarkAuditPeers": [
                {"model": peer["model"], "sales": peer["sales"], "effectivePriceMin": peer["effectivePriceMin"]}
                for peer in benchmark_peers
            ],
            "workflow": {
                "status": "待认领" if level in {"red", "orange"} else "持续观察" if level == "yellow" else "正常监测",
                "owner": "品牌与产品联合专项" if level in {"red", "orange"} else "品牌经营团队",
                "nextReview": "2026年7月销量发布后",
                "closeCriteria": "连续2个月高于黄色预警线；连续2个月达到市场基准80%则恢复正常",
            },
        })

    severity = {"red": 0, "orange": 1, "yellow": 2, "green": 3}
    saic_models.sort(key=lambda item: (severity[item["level"]], item["performanceRate"]))
    market_total = sum(item["sales"] for item in models)
    return {
        "status": "available",
        "mode": "single_segment_demo",
        "source": payload.get("source") or {},
        "segment": payload.get("segment") or {},
        "priceRules": payload.get("priceRules") or {},
        "summary": {
            "marketSales": market_total,
            "modelCount": len(models),
            "saicModelCount": len(saic_models),
            "redCount": sum(item["level"] == "red" for item in saic_models),
            "warningCount": sum(item["level"] != "green" for item in saic_models),
            "method": "懂车帝同车型种类×同尺寸×同动力形式的全部其他车型销量中位数；仅排除本品",
            "levelRules": {
                "green": "表现率≥80%",
                "yellow": "25%≤表现率＜80%",
                "red": "表现率＜25%",
                "warningDefinition": "黄色、红色均计入预警；仅绿色为正常",
            },
        },
        "saicModels": saic_models,
        "ranking": models,
    }


def build_sales_warning_full(payload):
    """Adapt the crawler's complete deterministic dataset to the dashboard contract."""
    if not isinstance(payload, dict) or payload.get("complete") is not True:
        raise ValueError("全量细分市场数据未通过完整性门禁")
    if payload.get("source") not in {
        "dongchedi_authenticated_browser",
        "dongchedi_public_rank_api",
    }:
        raise ValueError("全量细分市场数据来源不受支持")
    price_contract = payload.get("price_contract") or {}
    if not (
        price_contract.get("provider") == "懂车帝"
        and price_contract.get("field") == "dealer_price"
        and price_contract.get("required_flag") == "has_dealer_price=true"
        and price_contract.get("fallback") == "none"
    ):
        raise ValueError("车型起售价未锁定为懂车帝经销商报价")
    period = str(payload.get("period") or "").strip()
    thresholds = payload.get("thresholds") or {}
    red_ratio = float(thresholds.get("red_ratio") or 0)
    green_ratio = float(thresholds.get("green_ratio") or 0)
    yellow_ratio = float(thresholds.get("yellow_ratio") or ((red_ratio + green_ratio) / 2))
    if not period or not (0 < red_ratio < yellow_ratio < green_ratio):
        raise ValueError("全量细分市场月份或阈值无效")

    level_labels = {
        "red": "红色预警",
        "orange": "橙色预警",
        "yellow": "黄色观察",
        "green": "绿色正常",
        "gray": "灰色待复核",
    }
    saic_models = []
    for item in payload.get("saic_vehicles") or []:
        level = str(item.get("warning_level") or "gray")
        if level not in level_labels:
            raise ValueError(f"未知销量预警等级：{level}")
        sales = int(item.get("sales_volume") or 0)
        market_sales = int(item.get("segment_total_sales") or 0)
        benchmark = float(item.get("benchmark_sales") or item.get("segment_median_sales") or 0)
        red_line = int(item.get("red_line_sales") or round(benchmark * red_ratio))
        yellow_line = int(round(benchmark * yellow_ratio))
        green_line = int(item.get("green_line_sales") or round(benchmark * green_ratio))
        body_type = str(item.get("body_type") or "待复核")
        size_class = str(item.get("size_class") or "待复核")
        energy_type = str(item.get("energy_type") or "待复核")
        segment_energy_type = str(item.get("energy_group") or energy_type)
        vehicle_start_price = item.get("vehicle_start_price_wan")
        vehicle_start_price_source = str(item.get("vehicle_start_price_source") or "")
        if vehicle_start_price is not None and vehicle_start_price_source != "dongchedi_dealer_price":
            raise ValueError(f"车型起售价来源无效：{item.get('series_name')}")
        competitor_pool = list(item.get("competitor_pool") or [])
        benchmark_pool = list(item.get("benchmark_pool") or competitor_pool[:3])[:3]
        benchmark_ids = {int(peer.get("series_id") or 0) for peer in benchmark_pool}
        market_median = int(item.get("segment_median_sales") or 0)
        median_pool = sorted(
            (peer for peer in competitor_pool if int(peer.get("series_id") or 0) not in benchmark_ids),
            key=lambda peer: (
                abs(int(peer.get("sales_volume") or 0) - market_median),
                -int(peer.get("sales_volume") or 0),
                str(peer.get("series_name") or ""),
            ),
        )[:3]

        def comparison_peer(peer, role, apply_baas=False):
            model = str(peer.get("series_name") or "待复核车型")
            manufacturer = str(peer.get("manufacturer") or "待复核厂商")
            price_view = _baas_price_view(
                model,
                manufacturer,
                peer.get("price"),
                peer.get("price_source"),
            )
            if not apply_baas and price_view["baasApplied"]:
                price_view = {
                    **price_view,
                    "priceDisplay": price_view["dealerPriceDisplay"],
                    "startPriceWan": price_view["dealerStartPriceWan"],
                    "priceSource": price_view["dealerPriceSource"],
                }
            return {
                "seriesId": int(peer.get("series_id") or 0),
                "model": model,
                "manufacturer": manufacturer,
                "sales": int(peer.get("sales_volume") or 0),
                **price_view,
                "role": role,
                "roleLabel": {
                    "top3": "细分市场销量前三",
                    "median": "接近细分市场中位数",
                    "market": "同细分市场车型",
                }.get(role, "同细分市场车型"),
            }

        top_peers = [comparison_peer(peer, "top3") for peer in benchmark_pool]
        median_peers = [comparison_peer(peer, "median") for peer in median_pool]
        benchmark_audit_peers = [comparison_peer(peer, "market", apply_baas=True) for peer in competitor_pool]
        adjusted_benchmark_peers = [comparison_peer(peer, "market", apply_baas=True) for peer in benchmark_pool]
        adjusted_benchmark_prices = [
            peer["startPriceWan"]
            for peer in adjusted_benchmark_peers
            if peer["startPriceWan"] is not None
        ]
        adjusted_benchmark_average = (
            round(sum(adjusted_benchmark_prices) / len(adjusted_benchmark_prices), 2)
            if adjusted_benchmark_prices
            else None
        )
        own_price_view = _baas_price_view(
            item.get("series_name"),
            item.get("manufacturer"),
            item.get("price"),
            vehicle_start_price_source,
        )
        chart_vehicle_start_price = own_price_view["startPriceWan"]
        saic_models.append({
            "seriesId": int(item.get("series_id") or 0),
            "model": str(item.get("series_name") or "待复核车型"),
            "brand": str(item.get("manufacturer") or "上汽集团"),
            "bodyType": body_type,
            "sizeClass": size_class,
            "energyType": energy_type,
            "segmentEnergyType": segment_energy_type,
            "segmentKey": str(item.get("segment_key") or ""),
            "segmentLabel": " · ".join((size_class, segment_energy_type)),
            "sales": sales,
            "rank": int(item.get("segment_rank") or 0),
            "priceDisplay": own_price_view["priceDisplay"],
            "dealerPriceDisplay": own_price_view["dealerPriceDisplay"],
            "dealerStartPriceWan": own_price_view["dealerStartPriceWan"],
            "baasApplied": own_price_view["baasApplied"],
            "baasBrand": own_price_view["baasBrand"],
            "baasDiscountWan": own_price_view["baasDiscountWan"],
            "marketSales": market_sales,
            "marketShare": round(sales / market_sales, 4) if market_sales else None,
            "marketModelCount": int(item.get("segment_model_count") or 0),
            "salesMedian": market_median,
            "benchmark": benchmark,
            "peerBasis": str(item.get("competitor_pool_rule") or "排除本品后，取同细分市场销量前3名竞品的销量中位数；不足3款不计算"),
            "peerCount": int(item.get("benchmark_pool_count") or item.get("competitor_pool_count") or 0),
            "marketPeerCount": int(item.get("competitor_pool_count") or 0),
            "benchmarkMethod": str(item.get("benchmark_method") or "top_competitor_median"),
            "benchmarkPeers": top_peers,
            "medianPeers": median_peers,
            "comparisonPeers": top_peers + median_peers,
            "benchmarkAuditPeers": benchmark_audit_peers,
            "vehicleStartPriceWan": chart_vehicle_start_price,
            "vehicleStartPriceSource": own_price_view["priceSource"],
            "vehiclePriceBasis": own_price_view["priceBasis"],
            "benchmarkAverageStartPriceWan": adjusted_benchmark_average,
            "benchmarkMinimumStartPriceWan": min(adjusted_benchmark_prices) if adjusted_benchmark_prices else None,
            "benchmarkMaximumStartPriceWan": max(adjusted_benchmark_prices) if adjusted_benchmark_prices else None,
            "benchmarkPriceSampleCount": len(adjusted_benchmark_prices),
            "startPricePremiumRate": (
                round(chart_vehicle_start_price / adjusted_benchmark_average - 1, 4)
                if chart_vehicle_start_price is not None and adjusted_benchmark_average
                else None
            ),
            "performanceRate": float(item.get("performance_ratio") or 0),
            "redLine": red_line,
            "yellowLine": yellow_line,
            "greenLine": green_line,
            "gapToRedLine": max(0, red_line - sales),
            "level": level,
            "levelLabel": level_labels[level],
            "qualityStatus": str(item.get("quality_status") or "unknown"),
            "workflow": {
                "status": "待认领" if level == "red" else "持续观察" if level in {"orange", "yellow"} else "正常监测" if level == "green" else "数据待复核",
                "owner": "品牌与产品联合专项" if level == "red" else "品牌经营团队",
                "nextReview": "下月16日自动复盘",
                "closeCriteria": "连续2个月达到或高于头部竞争基准80%",
            },
        })

    severity = {"red": 0, "orange": 1, "yellow": 2, "gray": 3, "green": 4}
    saic_models.sort(key=lambda item: (severity[item["level"]], item["performanceRate"], item["model"]))
    first = saic_models[0] if saic_models else {}
    return {
        "status": "available",
        "mode": "full_segment_market",
        "source": {
            "provider": "懂车帝",
            "period": period,
            "capturedAt": payload.get("captured_at") or "",
            "complete": True,
        },
        "segment": {
            "id": "dynamic-by-selected-vehicle",
            "label": "按所选车型动态切换",
        },
        "summary": {
            "marketCount": int(payload.get("market_count") or 0),
            "saicModelCount": len(saic_models),
            "calculableModelCount": len(saic_models),
            "redCount": sum(item["level"] == "red" for item in saic_models),
            "orangeCount": sum(item["level"] == "orange" for item in saic_models),
            "yellowCount": sum(item["level"] == "yellow" for item in saic_models),
            "greenCount": sum(item["level"] == "green" for item in saic_models),
            "grayCount": sum(item["level"] == "gray" for item in saic_models),
            "warningCount": sum(item["level"] in {"red", "orange", "yellow"} for item in saic_models),
            "method": "新能源车型按尺寸×新能源分群，新能源包含纯电动、增程式和插电式混动；预警基准为排除本品后的同市场销量前3名竞品中位数，少于3款不计算",
            "levelRules": {
                "red": f"头部基准达成率＜{red_ratio:.0%}",
                "yellow": f"{red_ratio:.0%}≤头部基准达成率＜{green_ratio:.0%}",
                "green": f"头部基准达成率≥{green_ratio:.0%}",
                "gray": "数据冲突、能源形式待复核或头部竞品少于3款",
            },
        },
        "thresholds": {
            "redRatio": red_ratio,
            "yellowRatio": yellow_ratio,
            "greenRatio": green_ratio,
        },
        "qualityIssues": payload.get("quality_issues") or [],
        "saicModels": saic_models,
        "ranking": [],
    }


def _verified_observed_markets(path=SALES_WARNING_DEMO_PATH):
    """Split the verified Dongchedi snapshot into exact size-level markets."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {}
    source = payload.get("source") or {}
    segment = payload.get("segment") or {}
    if source.get("name") != "懂车帝销量榜" or not source.get("period"):
        return {}
    if segment.get("bodyType") != "轿车" or segment.get("energyType") != "纯电动":
        return {}
    grouped = defaultdict(list)
    for row in payload.get("models") or []:
        size_class = str(row.get("sizeClass") or "").strip()
        sales = int(row.get("sales") or 0)
        if size_class and sales >= 0:
            grouped[size_class].append({
                "series_name": str(row.get("model") or "").strip(),
                "manufacturer": str(row.get("brand") or "").strip(),
                "sales_volume": sales,
                "price": f"{float(row.get('priceMin') or 0):.2f}—{float(row.get('priceMax') or row.get('priceMin') or 0):.2f}万元",
            })
    return {
        f"轿车|{size_class}|纯电动": {
            "period": str(source["period"]),
            "source": source,
            "rows": rows,
        }
        for size_class, rows in grouped.items()
    }


def build_sales_warning_observed(path=SALES_WARNING_OBSERVED_PATH, market_path=SALES_WARNING_DEMO_PATH):
    """Expose verified focal observations and retain every already-verified market metric."""
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError):
        return {"status": "missing", "source": {}, "segment": {}, "summary": {}, "saicModels": [], "ranking": []}
    if payload.get("source") != "dongchedi_user_verified_observations" or not payload.get("period"):
        raise ValueError("重点车型销量观察文件来源或月份无效")

    verified_markets = _verified_observed_markets(market_path)
    items = []
    for source_item in payload.get("vehicles") or []:
        model = str(source_item.get("series_name") or "").strip()
        body_type = str(source_item.get("body_type") or "待核验").strip()
        size_class = str(source_item.get("size_class") or "待核验").strip()
        energy_type = str(source_item.get("energy_type") or "待核验").strip()
        sales = int(source_item.get("sales_volume") or 0)
        if not model or sales <= 0:
            continue
        item = {
            "seriesId": int(source_item.get("series_id") or 0),
            "model": model,
            "brand": str(source_item.get("manufacturer") or "上汽集团"),
            "bodyType": body_type,
            "sizeClass": size_class,
            "energyType": energy_type,
            "segmentKey": "|".join((body_type, size_class, energy_type)),
            "segmentLabel": " · ".join((body_type, size_class, energy_type)),
            "sales": sales,
            "rank": int(source_item.get("segment_rank") or 0),
            "priceDisplay": str(source_item.get("price") or "价格待核验"),
            "marketSales": None,
            "marketShare": None,
            "marketModelCount": None,
            "benchmark": None,
            "peerBasis": "懂车帝同车型种类×同尺寸×同动力形式，仅排除本品；完整竞品池待接入",
            "peerCount": None,
            "benchmarkPeers": [],
            "benchmarkAuditPeers": [],
            "performanceRate": None,
            "redLine": None,
            "greenLine": None,
            "gapToRedLine": None,
            "level": "gray",
            "levelLabel": "竞品池待补齐",
            "qualityStatus": "focal_sales_verified_competitor_pool_pending",
            "evidence": source_item.get("evidence") or {},
            "workflow": {
                "status": "竞品池待补齐",
                "owner": "销量数据运营",
                "nextReview": "完整同月榜单接入后自动计算",
                "closeCriteria": "同车型种类×同尺寸×同动力形式完整榜单通过门禁",
            },
        }
        verified_market = verified_markets.get(item["segmentKey"])
        market_rows = list((verified_market or {}).get("rows") or [])
        market_own = next(
            (row for row in market_rows if _model_identity_key(row.get("series_name")) == _model_identity_key(model)),
            None,
        )
        if verified_market and verified_market.get("period") == str(payload.get("period")) and market_own:
            ordered = sorted(market_rows, key=lambda row: (-int(row["sales_volume"]), row["series_name"]))
            peers = [row for row in ordered if _model_identity_key(row["series_name"]) != _model_identity_key(model)]
            benchmark = float(median([row["sales_volume"] for row in peers])) if peers else 0
            performance_rate = round(sales / benchmark, 4) if benchmark else 0
            level, level_label = _warning_level(performance_rate)
            item.update({
                "rank": next(index for index, row in enumerate(ordered, 1) if row is market_own),
                "marketSales": sum(int(row["sales_volume"]) for row in market_rows),
                "marketShare": round(sales / sum(int(row["sales_volume"]) for row in market_rows), 4),
                "marketModelCount": len(market_rows),
                "benchmark": benchmark,
                "peerBasis": "懂车帝同车型种类×同尺寸×同动力形式完整榜单，仅排除本品",
                "peerCount": len(peers),
                "benchmarkPeers": [
                    {"model": row["series_name"], "sales": row["sales_volume"], "priceDisplay": row["price"]}
                    for row in peers[:3]
                ],
                "benchmarkAuditPeers": [
                    {"model": row["series_name"], "sales": row["sales_volume"], "priceDisplay": row["price"]}
                    for row in peers
                ],
                "performanceRate": performance_rate,
                "redLine": round(benchmark * 0.25),
                "yellowLine": round(benchmark * 0.5),
                "greenLine": round(benchmark * 0.8),
                "gapToRedLine": max(0, round(benchmark * 0.25) - sales),
                "level": level,
                "levelLabel": level_label,
                "qualityStatus": "verified_complete_market",
                "workflow": {
                    "status": "待认领" if level in {"red", "orange"} else "持续观察" if level == "yellow" else "正常监测",
                    "owner": "品牌与产品联合专项" if level in {"red", "orange"} else "品牌经营团队",
                    "nextReview": "下月销量发布后复盘",
                    "closeCriteria": "连续2个月达到细分市场竞品中位数80%",
                },
            })
        items.append(item)
    calculable_count = sum(item.get("performanceRate") is not None for item in items)
    return {
        "status": "available",
        "mode": "observed_focal_models",
        "source": {
            "provider": "懂车帝",
            "period": str(payload.get("period")),
            "capturedAt": str(payload.get("captured_at") or ""),
            "complete": False,
            "scope": "重点车型销量与分类已核验；完整竞品池待接入",
        },
        "segment": {"id": "dynamic-by-selected-vehicle", "label": "按所选车型动态切换"},
        "summary": {
            "marketCount": 0,
            "saicModelCount": len(items),
            "calculableModelCount": calculable_count,
            "redCount": sum(item["level"] == "red" for item in items),
            "orangeCount": sum(item["level"] == "orange" for item in items),
            "yellowCount": sum(item["level"] == "yellow" for item in items),
            "greenCount": sum(item["level"] == "green" for item in items),
            "grayCount": sum(item["level"] == "gray" for item in items),
            "warningCount": sum(item["level"] in {"red", "orange", "yellow"} for item in items),
            "method": "已存在完整同月市场数据的车型直接展示真实总量、中位数和预警；其余车型仅对缺失指标保留待补状态",
            "levelRules": {"gray": "本品销量已识别，竞品池尚未通过完整性门禁"},
        },
        "thresholds": {"redRatio": 0.25, "yellowRatio": 0.5, "greenRatio": 0.8},
        "qualityIssues": [],
        "saicModels": items,
        "ranking": [],
    }


def _latest_sales_warning_observed_path(directory=None):
    """Resolve the newest period-specific monitored-model table without a code change."""
    directory = Path(directory or SALES_WARNING_OBSERVED_PATH.parent)
    candidates = sorted(directory.glob("sales_warning_observed_????-??.json"))
    return candidates[-1] if candidates else SALES_WARNING_OBSERVED_PATH


def load_sales_warning(path=None, demo_path=SALES_WARNING_DEMO_PATH, observed_path=None):
    """Prefer the verified full segment file, then focal observations; never present demo data as formal."""
    path = Path(path or os.getenv("MMN_SALES_WARNING_PATH") or SALES_WARNING_LATEST_PATH)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return build_sales_warning_full(payload)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return build_sales_warning_observed(observed_path or _latest_sales_warning_observed_path())


def sales_warning_methodology(warning):
    """Describe the active warning contract instead of retaining stale Demo copy."""
    warning = warning or {}
    summary = warning.get("summary") or {}
    thresholds = warning.get("thresholds") or {}
    method = str(summary.get("method") or "当前数据只展示已核验事实，缺失指标保持待补状态").rstrip("；。")
    ratios = [thresholds.get(key) for key in ("redRatio", "yellowRatio", "greenRatio")]
    if all(isinstance(value, (int, float)) and value > 0 for value in ratios):
        ratio_text = "/".join(f"{value:.0%}" for value in ratios)
        return f"销量预警：{method}；红/黄/绿参考线为头部竞争基准的 {ratio_text}。"
    return f"销量预警：{method}。"


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
    value = _model_identity_key(model_name)
    for launch in LAUNCH_MODELS:
        if value in {_model_identity_key(alias) for alias in launch["aliases"]}:
            return launch["model"]
    return ""


def _model_identity_key(model_name):
    """车型匹配只识别中英文字符，忽略所有空白与英文大小写。"""
    return re.sub(r"\s+", "", str(model_name or "")).casefold()


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


def _latest_model_cycles(conn, org_id, edition):
    """Read retained T-cycle stages from MMN model-router projects, newest first."""
    table = conn.execute(
        "select 1 from sqlite_master where type='table' and name='model_router_decisions'"
    ).fetchone()
    if not table:
        return {}
    rows = conn.execute("""
        select project_json, updated_at, created_at
        from model_router_decisions
        where edition=?
        order by updated_at desc, created_at desc
    """, (edition,)).fetchall()
    projects = []
    for row in rows:
        project = _safe_json(row["project_json"], {})
        if not isinstance(project, dict):
            continue
        project_org = str(project.get("_org_id") or "local")
        if project_org not in {org_id, "local"}:
            continue
        projects.append((project_org != org_id, project, row))
    projects.sort(key=lambda entry: entry[0])
    latest = {}
    for _, project, row in projects:
        model = str(project.get("model") or "").strip()
        stage = str(project.get("stage") or project.get("launchStage") or "").strip()
        match = re.search(
            r"T\s*(?:[+-]\s*\d+|0)(?:\s*[～~—–]\s*T?\s*(?:[+-]\s*)?\d+)?",
            stage,
            flags=re.IGNORECASE,
        )
        canonical = _canonical_launch(model) or _model_identity_key(model)
        if not canonical or not match or canonical in latest:
            continue
        cycle = re.sub(r"\s+", "", match.group(0)).upper()
        latest[canonical] = {
            "cycle": cycle,
            "stage": stage,
            "source": "MMN数据库",
            "updatedAt": row["updated_at"] or row["created_at"],
        }
    return latest


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
    """读取最新一份懂车帝正反向表；本品列同时定义销量预警监测集合。"""
    sql = """
        select platform, period, own_model, competitor_model, positive_rank, negative_rank,
               compare_share, source_file, updated_at
        from vertical_rank_assets
        where org_id=? and edition=? and platform='懂车帝' and source_file like ?
        order by updated_at desc, period desc, own_model, competitor_model
    """
    rows, fallback = _rows_with_demo_fallback(conn, sql, org_id, edition, (f"%{SALES_WARNING_MONITOR_SOURCE}%",))
    latest_source = str(rows[0]["source_file"] or "") if rows else ""
    if latest_source:
        rows = [row for row in rows if str(row["source_file"] or "") == latest_source]

    raw_models = []
    seen_models = set()
    for row in rows:
        key = _model_identity_key(row["own_model"])
        if not key or key in seen_models:
            continue
        seen_models.add(key)
        raw_models.append(str(row["own_model"] or "").strip())
    monitored_models = []
    monitored_keys = {_model_identity_key(model) for model in raw_models}
    for launch in LAUNCH_MODELS:
        if any(_model_identity_key(alias) in monitored_keys for alias in launch["aliases"]):
            monitored_models.append(launch["model"])
    monitored_models.extend(
        model for model in raw_models
        if not _canonical_launch(model) and _model_identity_key(model) not in {_model_identity_key(item) for item in monitored_models}
    )

    by_model_platform_period = defaultdict(list)
    for row in rows:
        canonical = _canonical_launch(row["own_model"]) or str(row["own_model"] or "").strip()
        key = (canonical, row["platform"], row["period"])
        by_model_platform_period[key].append(row)

    output = {}
    output_models = [launch["model"] for launch in LAUNCH_MODELS]
    output_models.extend(model for model in monitored_models if model not in output_models)
    for model in output_models:
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
        period_count = max([len(set(periods)) for periods in platform_periods.values()] or [0])
        rank_pairs = sum(row["positive_rank"] is not None and row["negative_rank"] is not None for row in latest_rows)
        confidence = "高" if period_count >= 6 and rank_pairs else "中" if period_count >= 3 else "低"
        leader_share = float(positive_leader["compare_share"]) if positive_leader and positive_leader["compare_share"] is not None else None
        output[model] = {
            "positiveTop10": sum(int(row["positive_rank"]) <= 10 for row in positives),
            "negativeTop10": sum(int(row["negative_rank"]) <= 10 for row in negatives),
            "positiveLeader": positive_leader["competitor_model"] if positive_leader else "待补数据",
            "riskLeader": risk_leader["competitor_model"] if risk_leader else "待补数据",
            "platformCount": len(platform_periods),
            "periodCount": period_count,
            "latestPeriods": latest_labels,
            "relationCount": len(latest_rows),
            "status": "available" if latest_rows else "missing",
            "activeCompetitor": positive_leader["competitor_model"] if positive_leader else "待补数据",
            "reverseCompetitor": risk_leader["competitor_model"] if risk_leader else "待补数据",
            "activeRank": int(positive_leader["positive_rank"]) if positive_leader else None,
            "reverseRank": int(risk_leader["negative_rank"]) if risk_leader else None,
            "compareShare": leader_share,
            "confidence": confidence,
            "inference": (
                f"{positive_leader['competitor_model']}是本品当前主动对比首位；"
                f"{risk_leader['competitor_model']}是当前反向对比首位。"
                if positive_leader and risk_leader
                else "正反向关系数据不足，暂不形成竞争关系推论。"
            ),
            "scopeNote": "垂媒正反向对比排名，作为 VOC 行为信号，不等同评论情绪",
        }
    monitoring = {
        "status": "available" if monitored_models else "missing",
        "platform": "懂车帝",
        "source": latest_source,
        "models": monitored_models,
        "modelCount": len(monitored_models),
        "updatedAt": str(rows[0]["updated_at"] or "") if rows else "",
        "scopeNote": "监测对象仅取最新正反向表的本品车型；空格差异不影响车型匹配。",
    }
    return output, fallback, monitoring


def _apply_vertical_monitoring(sales_warning, monitoring, signals):
    """以表内本品收敛预警对象；销量事实与预警等级保持原计算结果。"""
    warning = dict(sales_warning or {})
    summary = dict(warning.get("summary") or {})
    monitored_models = list(monitoring.get("models") or [])
    monitored_keys = {_model_identity_key(model) for model in monitored_models}
    items = []
    for source_item in warning.get("saicModels") or []:
        canonical = _canonical_launch(source_item.get("model")) or str(source_item.get("model") or "").strip()
        if _model_identity_key(canonical) not in monitored_keys:
            continue
        item = dict(source_item)
        item["comparisonSignal"] = signals.get(canonical) or {
            "status": "missing",
            "confidence": "低",
            "inference": "正反向关系数据不足，暂不形成竞争关系推论。",
            "scopeNote": "正反向关系只解释预警，不改写销量、市场口径或预警等级。",
        }
        items.append(item)
    calculable_items = [item for item in items if item.get("performanceRate") is not None]
    summary.update({
        "saicModelCount": len(items),
        "trackedModelCount": len(monitored_models),
        "salesReadyModelCount": len(items),
        "calculableModelCount": len(calculable_items),
        "pendingModelCount": max(0, len(monitored_models) - len(items)),
        "redCount": sum(item.get("level") == "red" for item in items),
        "orangeCount": sum(item.get("level") == "orange" for item in items),
        "yellowCount": sum(item.get("level") == "yellow" for item in items),
        "greenCount": sum(item.get("level") == "green" for item in items),
        "grayCount": sum(item.get("level") == "gray" for item in items),
        "warningCount": sum(item.get("level") in {"red", "orange", "yellow"} for item in items),
    })
    warning["summary"] = summary
    warning["saicModels"] = items
    warning["monitoring"] = monitoring
    return warning


def build_group_dashboard_payload(conn, sales_payload, org_id="local", edition="china", fuel_market=None):
    market_dimensions = build_market_dimensions(sales_payload)
    apply_cpca_fuel_market(market_dimensions, fuel_market)
    product_evaluation = load_e7x_product_evaluation()
    sales_warning = load_sales_warning()
    social, social_fallback = _latest_social_by_model(conn, org_id, edition)
    voc, vertical_fallback, monitoring = _vertical_signals(conn, org_id, edition)
    sales_warning = _apply_vertical_monitoring(sales_warning, monitoring, voc)
    model_cycles = _latest_model_cycles(conn, org_id, edition)
    for item in sales_warning.get("saicModels") or []:
        canonical = _canonical_launch(item.get("model")) or _model_identity_key(item.get("model"))
        retained = model_cycles.get(canonical)
        if retained:
            item.update({
                "cycle": retained["cycle"],
                "cycleStage": retained["stage"],
                "cycleSource": retained["source"],
                "cycleUpdatedAt": retained["updatedAt"],
            })
    sales_warning["cycleLookup"] = {
        "rule": "MMN数据库留存优先；无留存数据才允许人工填写",
        "databaseMatchedCount": sum(bool(item.get("cycle")) for item in sales_warning.get("saicModels") or []),
    }
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
        "salesWarnings": sales_warning,
        "launches": launches,
        "productEvaluation": product_evaluation,
        "methodology": [
            "市场结构：纯电、插混、增程及车身级别采用懂车帝 Top10；燃油采用乘联会 ICE 零售整体市场月度数据。",
            "燃油卡的销量、环比与份额来自乘联会 FuelMarket；上汽车型名次仅来自懂车帝全国总榜，不表述为燃油榜名次。",
            "营销声量：已存 TikHub 公开社媒样本的内容量与互动热度，未采集车型明确留空。",
            "VOC：懂车帝与汽车之家正反向对比排名，仅作为用户比较行为信号。",
            "E7X产品评价：来自 AUDI E7X等5车产品评价_0710_v2.xlsx，数据期为2026年6月；声量、互动量和NSR均沿用工作簿定义。",
            "属性星图：横轴为E7X属性NSR，纵轴为E7X相对五车平均NSR的差值；工作簿未提供属性样本量，因此点大小不编码样本量。",
            sales_warning_methodology(sales_warning),
        ],
    }
