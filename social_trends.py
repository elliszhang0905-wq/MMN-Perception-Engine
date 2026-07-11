"""Additive social-trend collection and evidence snapshot service for MMN."""
from __future__ import annotations

import hashlib
import html
import json
import math
import os
import re
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


PLATFORMS = {
    "douyin": {"label": "抖音", "method": "POST", "path": "/api/v1/douyin/search/fetch_video_search_v2", "query": "keyword", "page": "cursor"},
    "xiaohongshu": {"label": "小红书", "method": "GET", "path": "/api/v1/xiaohongshu/app_v2/search_notes", "query": "keyword", "page": "page"},
    "weibo": {"label": "微博", "method": "GET", "path": "/api/v1/weibo/web/fetch_search", "query": "keyword", "page": "page"},
}
POSITIVE = ("喜欢", "推荐", "领先", "惊喜", "好看", "舒适", "智能", "省油", "续航", "质感", "稳定", "优秀")
NEGATIVE = ("失望", "问题", "异响", "故障", "吐槽", "贵", "难用", "风险", "投诉", "不足", "差", "垃圾")
TECHNICAL_WORDS = {"span", "class", "https", "http", "href", "data-hide", "surl-text", "weibo", "containerid", "launchid", "extparam", "status"}
TIME_FILTERS = {
    "1d": {"douyin": "1", "xiaohongshu": "一天内", "weibo": "day"},
    "3d": {"douyin": "1", "xiaohongshu": "一周内", "weibo": "day"},
    "7d": {"douyin": "7", "xiaohongshu": "一周内", "weibo": "week"},
    "30d": {"douyin": "180", "xiaohongshu": "半年内", "weibo": "month"},
    "90d": {"douyin": "180", "xiaohongshu": "半年内", "weibo": ""},
}
DEFAULT_LIKE_THRESHOLDS = {"douyin": 8000, "xiaohongshu": 500, "weibo": 500}
IMPORT_ALIASES = {
    "platform": ("平台", "platform", "来源平台"), "title": ("标题", "内容标题", "作品标题", "笔记标题", "视频标题", "视频描述", "作品描述", "笔记描述", "desc", "content"),
    "author": ("作者", "博主", "达人昵称", "昵称", "author", "nickname"), "url": ("链接", "作品链接", "笔记链接", "视频链接", "url", "share_url"),
    "item_id": ("作品ID", "视频ID", "笔记ID", "内容ID", "aweme_id", "note_id", "mid", "id"), "published": ("发布时间", "发布日期", "发布于", "create_time", "publish_time"),
    "likes": ("点赞", "点赞数", "点赞量", "获赞数", "digg_count", "liked_count", "attitudes_count", "likes"), "comments": ("评论", "评论数", "评论量", "comment_count", "comments_count"),
    "shares": ("分享", "分享数", "分享量", "转发", "转发数", "转发量", "share_count", "reposts_count"), "collects": ("收藏", "收藏数", "收藏量", "collect_count", "collected_count"),
    "views": ("播放", "播放量", "观看量", "play_count", "view_count", "views"),
}
ENRICHMENT_ENDPOINTS = {
    "douyin": {
        "hot": ("GET", "/api/v1/douyin/web/fetch_hot_search_result"),
        "comments": ("GET", "/api/v1/douyin/web/fetch_video_comments"),
    },
    "xiaohongshu": {
        "comments": ("GET", "/api/v1/xiaohongshu/app_v2/get_note_comments"),
    },
    "weibo": {
        "hot": ("GET", "/api/v1/weibo/web/fetch_hot_search"),
        "comments": ("GET", "/api/v1/weibo/web/fetch_post_comments"),
    },
}


def _backend_env(name, default=""):
    value = os.getenv(name)
    if value:
        return value
    path = Path(__file__).resolve().parent / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if raw and not raw.startswith("#") and "=" in raw:
                key, candidate = raw.split("=", 1)
                if key.strip() == name:
                    return candidate.strip().strip('"').strip("'")
    return default


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_schema(conn: sqlite3.Connection):
    conn.executescript("""
    create table if not exists social_trend_snapshots (
      id text primary key, org_id text not null, edition text not null, keyword text not null,
      filters_json text not null default '{}', result_json text not null, source_mode text not null,
      created_at text not null
    );
    create index if not exists idx_social_trend_scope
      on social_trend_snapshots(org_id, edition, keyword, created_at desc);
    """)


def _walk(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child)


def _first(row, *names, default=None):
    for name in names:
        value = row.get(name)
        if value not in (None, "", [], {}):
            return value
    return default


def _number(value):
    if isinstance(value, str):
        raw = value.strip().replace(",", "")
        multiplier = 10000 if raw.endswith("万") else 1000 if raw.lower().endswith("k") else 1
        if multiplier != 1: value = raw[:-1]
        try: return max(0, float(value or 0) * multiplier)
        except ValueError: pass
    try:
        return max(0, float(value or 0))
    except (TypeError, ValueError):
        return 0.0


def _import_value(row, name, default=""):
    normalized = {str(key or "").strip().lower(): value for key, value in row.items()}
    for alias in IMPORT_ALIASES[name]:
        value = normalized.get(alias.lower())
        if value not in (None, ""):
            return value
    return default


def _import_platform(row):
    raw = str(_import_value(row, "platform") or "").lower()
    url = str(_import_value(row, "url") or "").lower()
    combined = raw + " " + url
    if "抖音" in combined or "douyin" in combined or "iesdouyin" in combined: return "douyin"
    if "小红书" in combined or "xiaohongshu" in combined or "rednote" in combined or "xhslink" in combined: return "xiaohongshu"
    if "微博" in combined or "weibo" in combined: return "weibo"
    return ""


def _parse_import_date(value):
    raw = str(value or "").strip()
    if not raw: return None
    try:
        # Spreadsheet exports commonly encode dates as Excel serial day numbers.
        try: numeric = float(raw)
        except ValueError: numeric = None
        if numeric is not None and 20_000 <= numeric <= 80_000:
            return datetime(1899, 12, 30, tzinfo=timezone.utc) + timedelta(days=numeric)
        if numeric is not None and numeric > 100_000_000:
            stamp = numeric / 1000 if numeric > 10_000_000_000 else numeric
            return datetime.fromtimestamp(stamp, timezone.utc)
        if raw.isdigit():
            stamp = float(raw); stamp = stamp / 1000 if stamp > 10_000_000_000 else stamp
            return datetime.fromtimestamp(stamp, timezone.utc)
        try:
            return datetime.fromisoformat(raw.replace("/", "-").replace("Z", "+00:00")).replace(tzinfo=timezone.utc) if "+" not in raw and not raw.endswith("Z") else datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            try:
                return parsedate_to_datetime(raw)
            except (TypeError, ValueError):
                return None
    except (ValueError, TypeError, OSError, OverflowError):
        return None


def clean_content_text(value):
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _content_rows(payload):
    candidates = []
    for row in _walk(payload):
        text = _first(row, "desc", "title", "note_title", "text", "content", "raw_text")
        identifier = _first(row, "aweme_id", "note_id", "mid", "id", "item_id")
        if text and identifier:
            candidates.append(row)
    return candidates


def _text_rows(payload):
    rows, seen = [], set()
    for row in _walk(payload):
        text = clean_content_text(_first(row, "text", "content", "comment", "desc", "title", "note_title", "word", "hot_word", "note"))
        if len(text) < 2 or text in seen:
            continue
        seen.add(text); rows.append({"text": text, "raw": row})
    return rows


def _sentiment(text):
    positive = sum(text.count(word) for word in POSITIVE)
    negative = sum(text.count(word) for word in NEGATIVE)
    return ("positive" if positive > negative else "negative" if negative > positive else "neutral", positive, negative)


def _published_bucket(value, fallback):
    parsed = _parse_import_date(value)
    return parsed.date().isoformat() if parsed else ""


def normalize_item(platform, row, keyword, fetched_at):
    text = clean_content_text(_first(row, "desc", "title", "note_title", "text", "content", "raw_text", default=""))
    item_id = str(_first(row, "aweme_id", "note_id", "mid", "id", "item_id", default="")).strip()
    author = _first(row, "author", "user", "note_card", default={})
    author_name = _first(author, "nickname", "name", "nick_name", "user_name", default="") if isinstance(author, dict) else str(author)
    stats = _first(row, "statistics", "interact_info", "stats", default={})
    stats = stats if isinstance(stats, dict) else {}
    likes = _number(_first(row, "digg_count", "liked_count", "attitudes_count", "likes", default=_first(stats, "digg_count", "liked_count", "likes", default=0)))
    comments = _number(_first(row, "comment_count", "comments_count", "comments", default=_first(stats, "comment_count", "comments_count", default=0)))
    shares = _number(_first(row, "share_count", "reposts_count", "shares", default=_first(stats, "share_count", "reposts_count", default=0)))
    collects = _number(_first(row, "collect_count", "collected_count", "favorites_count", default=_first(stats, "collect_count", "collected_count", default=0)))
    views = _number(_first(row, "play_count", "view_count", "views", default=_first(stats, "play_count", "view_count", default=0)))
    published = _first(row, "create_time", "timestamp", "time", "created_at", "publish_time", default="")
    url = str(_first(row, "share_url", "url", "note_url", "detail_url", default=""))
    if not url:
        url = {"douyin": f"https://www.douyin.com/video/{item_id}", "xiaohongshu": f"https://www.xiaohongshu.com/explore/{item_id}", "weibo": f"https://weibo.com/detail/{item_id}"}[platform]
    sentiment, positive, negative = _sentiment(text)
    engagement = likes + comments * 2 + shares * 3 + collects * 2.5
    heat = math.log10(1 + engagement + views * .08) * 20
    canonical = re.sub(r"[\s·•_-]+", "", text.lower())[:80]
    content_hash = hashlib.sha256(f"{platform}|{item_id or canonical}".encode()).hexdigest()
    return {"id": content_hash[:20], "platform": platform, "platformLabel": PLATFORMS[platform]["label"],
            "platformItemId": item_id, "keyword": keyword, "normalizedModel": keyword.strip(), "text": text,
            "author": author_name, "publishedAt": str(published), "sourceUrl": url,
            "metrics": {"likes": likes, "comments": comments, "shares": shares, "collects": collects, "views": views},
            "sentiment": sentiment, "sentimentEvidence": {"positiveHits": positive, "negativeHits": negative},
            "heat": round(min(100, heat), 2), "matrixContent": bool(re.search(r"官方|旗舰店|品牌|汽车|媒体|矩阵", author_name + text)),
            "evidence": {"source": "TikHub", "fetchedAt": fetched_at, "contentHash": content_hash}}


class TikHubClient:
    def __init__(self):
        self.key = _backend_env("TIKHUB_API_KEY")
        self.base = _backend_env("TIKHUB_BASE_URL", "https://api.tikhub.io").rstrip("/")
        self.timeout = float(_backend_env("TIKHUB_TIMEOUT_SECONDS", "30"))

    def configured(self):
        return bool(self.key)

    def request_json(self, method, path, params=None):
        params = params or {}
        headers = {"Authorization": f"Bearer {self.key}", "Accept": "application/json", "User-Agent": "MMN-Perception-Engine/1.0"}
        if method == "POST":
            headers["Content-Type"] = "application/json"
            request = Request(f"{self.base}{path}", data=json.dumps(params).encode("utf-8"), headers=headers, method="POST")
        else:
            suffix = f"?{urlencode(params)}" if params else ""
            request = Request(f"{self.base}{path}{suffix}", headers=headers)
        for attempt in range(3):
            try:
                with urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8")), {"endpoint": path, "status": response.status}
            except HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                    raise RuntimeError(f"TikHub HTTP {exc.code}: {path}") from exc
            except (URLError, TimeoutError) as exc:
                if attempt == 2: raise RuntimeError("TikHub 网络错误") from exc
            time.sleep(2 ** attempt)

    def search(self, platform, keyword, page=1, count=20, time_range="30d"):
        cfg = dict(PLATFORMS[platform])
        override = os.getenv(f"TIKHUB_SOCIAL_{platform.upper()}_ENDPOINT")
        if override:
            cfg["path"] = override
        params = {cfg["query"]: keyword, cfg["page"]: (page - 1) * count if platform == "douyin" else page}
        window = TIME_FILTERS.get(time_range, TIME_FILTERS["30d"])[platform]
        if platform == "douyin": params.update({"sort_type": "0", "publish_time": window, "filter_duration": "0", "content_type": "0", "search_id": "", "backtrace": ""})
        if platform == "xiaohongshu": params.update({"sort_type": "general", "note_type": "不限", "time_filter": window, "ai_mode": 0})
        if platform == "weibo": params.update({"search_type": "1", **({"time_scope": window} if window else {})})
        return self.request_json(cfg["method"], cfg["path"], params)

    def hot_list(self, platform):
        method, path = ENRICHMENT_ENDPOINTS[platform]["hot"]
        return self.request_json(method, path)

    def comments(self, item):
        platform = item["platform"]; method, path = ENRICHMENT_ENDPOINTS[platform]["comments"]
        item_id = item["platformItemId"]
        params = ({"aweme_id": item_id, "cursor": 0, "count": 20} if platform == "douyin" else
                  {"note_id": item_id, "share_text": item.get("sourceUrl", ""), "cursor": "", "index": "", "pageArea": "", "sort_strategy": 0} if platform == "xiaohongshu" else
                  {"post_id": item_id, "mid": item_id, "max_id": 0, "max_id_type": 0})
        return self.request_json(method, path, params)


def _aggregate(items, keyword, sources, warnings, comment_rows=None, hot_lists=None, selected_platforms=None):
    unique = {item["id"]: item for item in items}
    items = sorted(unique.values(), key=lambda row: row["heat"], reverse=True)
    platform_rows = []
    platform_keys = [key for key in (selected_platforms or PLATFORMS) if key in PLATFORMS]
    for key in platform_keys:
        cfg = PLATFORMS[key]
        rows = [row for row in items if row["platform"] == key]
        platform_rows.append({"platform": key, "label": cfg["label"], "contentCount": len(rows),
                              "heat": round(sum(row["heat"] for row in rows), 2),
                              "positive": sum(row["sentiment"] == "positive" for row in rows),
                              "negative": sum(row["sentiment"] == "negative" for row in rows)})
    words = re.findall(r"[\u4e00-\u9fff]{2,8}|[A-Za-z][A-Za-z0-9-]{2,}", " ".join(row["text"] for row in items))
    stop = {keyword, "汽车", "车型", "这个", "我们", "真的", "一个", "视频"}
    counts = {}
    for word in words:
        if word.lower() not in TECHNICAL_WORDS and word not in stop and keyword not in word: counts[word] = counts.get(word, 0) + 1
    hot_words = [{"word": word, "count": count} for word, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0]))[:20]]
    confidence = min(1, len(items) / 30)
    total_heat = sum(row["heat"] for row in items) or 1
    for row in platform_rows:
        row["share"] = round(row["heat"] / total_heat * 100, 1)
    creators = {}
    for row in items:
        name = row.get("author") or "未知作者"; key = (row["platform"], name)
        current = creators.setdefault(key, {"author": name, "platform": row["platform"], "platformLabel": row["platformLabel"], "contentCount": 0, "heat": 0, "matrixContent": False})
        current["contentCount"] += 1; current["heat"] += row["heat"]; current["matrixContent"] = current["matrixContent"] or row["matrixContent"]
    creator_ranking = sorted(creators.values(), key=lambda x: (-x["heat"], x["author"]))[:20]
    for row in creator_ranking: row["heat"] = round(row["heat"], 2)
    timeline, undated = {}, {"contentCount": 0, "heat": 0, "platforms": {}}
    for row in items:
        day = _published_bucket(row.get("publishedAt"), row["evidence"].get("fetchedAt"))
        if not day:
            undated["contentCount"] += 1; undated["heat"] += row["heat"]
            bucket = undated["platforms"].setdefault(row["platform"], {"platform": row["platform"], "label": row["platformLabel"], "contentCount": 0, "heat": 0})
            bucket["contentCount"] += 1; bucket["heat"] += row["heat"]
            continue
        point = timeline.setdefault(day, {"date": day, "contentCount": 0, "heat": 0, "positive": 0, "negative": 0})
        point["contentCount"] += 1; point["heat"] += row["heat"]; point[row["sentiment"]] = point.get(row["sentiment"], 0) + 1
        platforms_by_day = point.setdefault("platforms", {})
        platform_point = platforms_by_day.setdefault(row["platform"], {"platform": row["platform"], "label": row["platformLabel"], "contentCount": 0, "heat": 0})
        platform_point["contentCount"] += 1; platform_point["heat"] += row["heat"]
    timeline_rows = sorted(timeline.values(), key=lambda x: x["date"])
    for point in timeline_rows:
        point["heat"] = round(point["heat"], 2)
        point["platforms"] = [{**value, "heat": round(value["heat"], 2)} for value in point.get("platforms", {}).values()]
    undated["heat"] = round(undated["heat"], 2); undated["platforms"] = [{**value, "heat": round(value["heat"], 2)} for value in undated["platforms"].values()]
    risks = [row for row in items if row["sentiment"] == "negative"]
    risk_topics = []
    for word in hot_words:
        matching = [row for row in risks if word["word"] in row["text"]]
        if matching: risk_topics.append({"topic": word["word"], "contentCount": len(matching), "heat": round(sum(x["heat"] for x in matching), 2), "evidenceIds": [x["id"] for x in matching[:5]]})
    comments = comment_rows or []
    comment_summary = {"total": len(comments), "positive": sum(x["sentiment"] == "positive" for x in comments), "negative": sum(x["sentiment"] == "negative" for x in comments), "neutral": sum(x["sentiment"] == "neutral" for x in comments), "samples": comments[:20]}
    clusters = []
    for word in hot_words[:8]:
        matching = [row for row in items if word["word"] in row["text"]]
        clusters.append({"topic": word["word"], "contentCount": len(matching), "heat": round(sum(x["heat"] for x in matching), 2), "sentiment": {"positive": sum(x["sentiment"] == "positive" for x in matching), "negative": sum(x["sentiment"] == "negative" for x in matching)}})
    return {"keyword": keyword, "generatedAt": utcnow(), "items": items, "contentRanking": items[:50],
            "hotWords": hot_words, "ownModelRanking": [{"model": keyword, "heat": round(sum(x["heat"] for x in items), 2), "contentCount": len(items)}],
            "positiveCompetitorsTop5": [], "platforms": platform_rows, "platformShare": platform_rows,
            "creatorRanking": creator_ranking, "matrixSummary": {"contentCount": sum(x["matrixContent"] for x in items), "creatorCount": sum(x["matrixContent"] for x in creator_ranking), "heat": round(sum(x["heat"] for x in items if x["matrixContent"]), 2)},
            "timeline": timeline_rows, "timelineUndated": undated, "riskTopics": sorted(risk_topics, key=lambda x: -x["heat"])[:10], "riskItems": risks[:20],
            "commentInsights": comment_summary, "hotLists": hot_lists or [], "contentClusters": clusters,
            "sources": sources, "warnings": warnings,
            "confidence": round(confidence, 2), "confidenceLabel": "高" if confidence >= .7 else "中" if confidence >= .4 else "低",
            "statusHint": "未形成高热度" if not items or max((x["heat"] for x in items), default=0) < 60 else "已形成可识别热度",
            "methodology": {"heat": "log10(1+点赞+2×评论+3×分享+2.5×收藏+0.08×播放)×20，封顶100；跨平台总热度为内容热度求和",
                            "dedup": "平台内容ID优先，缺失时使用平台+规范化文本哈希", "sentiment": "正负向词证据计数；冲突或无命中标记中性并进入模型复核", "matrix": "作者名与正文中的官方/品牌/媒体/矩阵标记"},
            "qa": {"evidenceTraceable": all(row["sourceUrl"] and row["evidence"]["contentHash"] for row in items),
                   "dualModel": {"required": True, "status": "pending"}, "strategyOutput": "待双模型交叉验证后输出策略结论"}}


def attach_competitor_rankings(result, competitor_results):
    rankings = []
    for competitor in competitor_results[:3]:
        positive_items = [item for item in competitor.get("items", []) if item.get("sentiment") == "positive"]
        rankings.append({"model": competitor.get("keyword", ""),
                         "positiveHeat": round(sum(float(item.get("heat") or 0) for item in positive_items), 2),
                         "positiveContentCount": len(positive_items),
                         "contentCount": len(competitor.get("items", [])),
                         "confidence": competitor.get("confidence", 0)})
    result["positiveCompetitorsTop5"] = sorted((x for x in rankings if x["model"]), key=lambda x: (-x["positiveHeat"], x["model"]))[:5]
    own = result.get("ownModelRanking", [])
    result["modelHeatRanking"] = sorted(own + [{"model": x.get("keyword"), "heat": round(sum(i["heat"] for i in x.get("items", [])), 2), "contentCount": len(x.get("items", []))} for x in competitor_results], key=lambda x: -x["heat"])
    comparisons = []
    for dataset, role in [(result, "own")] + [(row, "competitor") for row in competitor_results]:
        items = dataset.get("items", [])
        positives = sum(x.get("sentiment") == "positive" for x in items)
        negatives = sum(x.get("sentiment") == "negative" for x in items)
        comparisons.append({
            "model": dataset.get("keyword", ""), "role": role,
            "heat": round(sum(float(x.get("heat") or 0) for x in items), 2),
            "contentCount": len(items),
            "positiveRate": round(positives / len(items) * 100, 1) if items else 0,
            "riskCount": negatives,
            "platforms": dataset.get("platforms", []),
            "hotWords": dataset.get("hotWords", [])[:8],
            "topContent": dataset.get("contentRanking", [])[:5],
            "confidence": dataset.get("confidence", 0),
        })
    result["modelComparisons"] = comparisons
    result["comparisonEvidence"] = sorted([item for dataset in [result] + competitor_results for item in dataset.get("contentRanking", [])[:10]], key=lambda x: -float(x.get("heat") or 0))[:50]
    return result


def collect(keyword, platforms=None, pages=1, count=20, time_range="30d", include_enrichment=True, thresholds=None):
    keyword = str(keyword or "").strip()
    if not keyword: raise ValueError("请输入车型名")
    platforms = [p for p in (platforms or PLATFORMS) if p in PLATFORMS]
    client, items, sources, warnings = TikHubClient(), [], [], []
    if not client.configured(): raise RuntimeError("服务端未配置 TIKHUB_API_KEY")
    for platform in platforms:
        for page in range(1, max(1, min(int(pages), 3)) + 1):
            try:
                payload, source = client.search(platform, keyword, page, min(50, max(1, int(count))), time_range)
                fetched = utcnow(); rows = _content_rows(payload)
                items.extend(normalize_item(platform, row, keyword, fetched) for row in rows)
                sources.append({"platform": platform, **source, "fetchedAt": fetched, "itemCount": len(rows)})
            except Exception as exc:
                warnings.append({"platform": platform, "message": str(exc)})
                break
    like_thresholds = ({**DEFAULT_LIKE_THRESHOLDS, **{key: int(float(value)) for key, value in thresholds.items() if key in PLATFORMS}}
                       if thresholds is not None else None)
    collected_at = datetime.now(timezone.utc)
    cutoff = collected_at - timedelta(days=int(time_range[:-1])) if time_range in {"1d", "3d", "7d", "30d", "90d"} else None
    admitted, rejected = [], []
    keyword_key = re.sub(r"[\s·•_-]+", "", keyword.lower())
    for item in items:
        published = _parse_import_date(item.get("publishedAt")); reason = ""
        if keyword_key not in re.sub(r"[\s·•_-]+", "", item.get("text", "").lower()): reason = "model_not_relevant"
        elif not published: reason = "publish_time_unverified"
        elif cutoff and (published < cutoff or published > collected_at + timedelta(minutes=5)): reason = "outside_time_range"
        elif like_thresholds is not None and item["metrics"]["likes"] < like_thresholds[item["platform"]]: reason = "below_like_threshold"
        if reason: rejected.append({"id": item["id"], "platform": item["platform"], "title": item["text"], "likes": item["metrics"]["likes"], "reason": reason})
        else:
            item["evidence"]["verificationStatus"] = "tikhub_search_observation"
            admitted.append(item)
    items = admitted
    admission = {"inputCount": len(admitted) + len(rejected), "admittedCount": len(admitted), "rejectedCount": len(rejected), "duplicateCount": 0, "thresholds": like_thresholds,
                 "rejectedReasons": {reason: sum(x["reason"] == reason for x in rejected) for reason in sorted({x["reason"] for x in rejected})}, "rejectedSamples": rejected[:30]}
    comment_rows, hot_lists = [], []
    if include_enrichment:
        for platform in platforms:
            if "hot" in ENRICHMENT_ENDPOINTS[platform]:
                try:
                    payload, source = client.hot_list(platform); rows = _text_rows(payload)[:20]
                    hot_lists.append({"platform": platform, "platformLabel": PLATFORMS[platform]["label"], "items": [x["text"] for x in rows], **source})
                except Exception as exc: warnings.append({"platform": platform, "capability": "hot_list", "message": str(exc)})
            top = sorted((x for x in items if x["platform"] == platform), key=lambda x: -x["heat"])[:1]
            for item in top:
                try:
                    payload, source = client.comments(item)
                    for row in _text_rows(payload)[:20]:
                        sentiment, positive, negative = _sentiment(row["text"])
                        comment_rows.append({"platform": platform, "platformLabel": PLATFORMS[platform]["label"], "contentId": item["id"], "text": row["text"], "sentiment": sentiment, "positiveHits": positive, "negativeHits": negative, "sourceUrl": item["sourceUrl"]})
                    sources.append({"platform": platform, "capability": "comments", **source, "fetchedAt": utcnow()})
                except Exception as exc: warnings.append({"platform": platform, "capability": "comments", "message": str(exc)})
    result = _aggregate(items, keyword, sources, warnings, comment_rows, hot_lists, platforms)
    if admission:
        result["admission"] = admission; result["rankingMethod"] = "点赞量降序，其次评论量、收藏量、分享量、发布时间"
        result["contentRanking"] = sorted(result["items"], key=lambda x: (-x["metrics"]["likes"], -x["metrics"]["comments"], -x["metrics"]["collects"], -x["metrics"]["shares"], -_number(x["publishedAt"])))[:50]
    return result


def import_records(records, keyword, platforms=None, thresholds=None, time_range="30d", start_date="", end_date="", filename=""):
    keyword = str(keyword or "").strip()
    if not keyword: raise ValueError("请输入车型名后再导入数据")
    platforms = [p for p in (platforms or PLATFORMS) if p in PLATFORMS]
    thresholds = {**DEFAULT_LIKE_THRESHOLDS, **{key: int(float(value)) for key, value in (thresholds or {}).items() if key in PLATFORMS}}
    now_dt = datetime.now(timezone.utc)
    start = _parse_import_date(start_date)
    end = _parse_import_date(end_date)
    if not start and time_range in {"1d", "3d", "7d", "30d", "90d"}:
        start = now_dt - timedelta(days=int(time_range[:-1]))
    if not end: end = now_dt + timedelta(days=1)
    admitted, rejected, duplicates, seen = [], [], 0, set()
    keyword_key = re.sub(r"[\s·•_-]+", "", keyword.lower())
    for index, row in enumerate(records or []):
        platform = _import_platform(row)
        text = clean_content_text(_import_value(row, "title"))
        published = _parse_import_date(_import_value(row, "published"))
        likes = _number(_import_value(row, "likes")); item_id = str(_import_value(row, "item_id") or "").strip()
        url = str(_import_value(row, "url") or "").strip()
        reason = ""
        if not platform or platform not in platforms: reason = "platform_not_selected"
        elif keyword_key not in re.sub(r"[\s·•_-]+", "", text.lower()): reason = "model_not_relevant"
        elif not published: reason = "publish_time_unverified"
        elif published < start or published > end: reason = "outside_time_range"
        elif likes < thresholds[platform]: reason = "below_like_threshold"
        identity = f"{platform}|{item_id or url or text[:100]}"
        if identity in seen: duplicates += 1; continue
        seen.add(identity)
        if reason:
            rejected.append({"row": index + 1, "platform": platform, "title": text, "likes": likes, "reason": reason})
            continue
        raw = {"id": item_id or hashlib.sha1(identity.encode()).hexdigest()[:18], "title": text,
               "author": {"nickname": _import_value(row, "author")}, "create_time": published.timestamp(), "share_url": url,
               "statistics": {"digg_count": likes, "comment_count": _number(_import_value(row, "comments")), "share_count": _number(_import_value(row, "shares")),
                              "collect_count": _number(_import_value(row, "collects")), "play_count": _number(_import_value(row, "views"))}}
        item = normalize_item(platform, raw, keyword, utcnow())
        item["evidence"].update({"source": "社媒助手导入", "filename": filename, "verificationStatus": "page_export_verified"})
        admitted.append(item)
    admitted.sort(key=lambda x: (-x["metrics"]["likes"], -x["metrics"]["comments"], -x["metrics"]["collects"], -x["metrics"]["shares"], -_number(x["publishedAt"])))
    result = _aggregate(admitted, keyword, [{"source": "social_assistant_import", "filename": filename, "itemCount": len(records or [])}], [], selected_platforms=platforms)
    result["contentRanking"] = admitted[:50]; result["items"] = admitted
    result["admission"] = {"inputCount": len(records or []), "admittedCount": len(admitted), "rejectedCount": len(rejected), "duplicateCount": duplicates,
                           "thresholds": thresholds, "rejectedReasons": {reason: sum(x["reason"] == reason for x in rejected) for reason in sorted({x["reason"] for x in rejected})},
                           "rejectedSamples": rejected[:30]}
    result["rankingMethod"] = "点赞量降序，其次评论量、收藏量、分享量、发布时间"
    result["sourceMode"] = "social_assistant_import"
    return attach_competitor_rankings(result, [])


def apply_history(result, previous):
    current_items = result.get("items", []); previous_items = (previous or {}).get("items", [])
    def metrics(rows):
        positives = sum(x.get("sentiment") == "positive" for x in rows)
        return {"contentCount": len(rows), "heat": round(sum(float(x.get("heat") or 0) for x in rows), 2), "positiveRate": round(positives / len(rows) * 100, 1) if rows else 0}
    current, prior = metrics(current_items), metrics(previous_items)
    result["historyComparison"] = {"available": bool(previous), "current": current, "previous": prior,
        "delta": {"contentCount": current["contentCount"] - prior["contentCount"], "heat": round(current["heat"] - prior["heat"], 2), "positiveRate": round(current["positiveRate"] - prior["positiveRate"], 1)},
        "previousSnapshot": (previous or {}).get("snapshot")}
    return result


def save_snapshot(conn, result, org_id="local", edition="china", filters=None):
    stamp = utcnow(); payload = json.dumps(result, ensure_ascii=False)
    snapshot_id = hashlib.sha256(f"{org_id}|{edition}|{result['keyword']}|{stamp}".encode()).hexdigest()[:24]
    conn.execute("insert into social_trend_snapshots values (?, ?, ?, ?, ?, ?, ?, ?)",
                 (snapshot_id, org_id, edition, result["keyword"], json.dumps(filters or {}, ensure_ascii=False), payload, "tikhub", stamp))
    return {"id": snapshot_id, "createdAt": stamp}


def latest_snapshot(conn, keyword, org_id="local", edition="china"):
    row = conn.execute("select * from social_trend_snapshots where org_id=? and edition=? and keyword=? order by created_at desc limit 1", (org_id, edition, keyword)).fetchone()
    if not row: return None
    result = json.loads(row["result_json"]); result["snapshot"] = {"id": row["id"], "createdAt": row["created_at"]}
    return result
