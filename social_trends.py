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
import unicodedata
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
COMMERCIAL_VEHICLE_ENTITY_PATTERN = re.compile(
    r"梅赛德斯[·\-\s]*奔驰卡车|奔驰卡车|戴姆勒卡车|Daimler\s*Truck|"
    r"ABA\s*\d+\s*Plus|重卡|牵引车|半挂车|商用车|客车",
    re.IGNORECASE,
)
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
    "cover": ("封面", "封面链接", "视频封面", "cover", "cover_url", "thumbnail"),
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


def normalized_vehicle_label(value):
    """Return a stable display label without changing the user's vehicle wording."""
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).split())


def vehicle_identity_key(value):
    """Compare vehicle names independent of spacing, width and letter case."""
    return re.sub(r"\s+", "", normalized_vehicle_label(value)).casefold()


def sanitize_competitor_models(keyword, competitors, limit=3):
    """Preserve selection order while excluding the own model and duplicates."""
    own_key = vehicle_identity_key(keyword)
    seen = set()
    sanitized = []
    for value in competitors or []:
        label = normalized_vehicle_label(value)
        identity = vehicle_identity_key(label)
        if not identity or identity == own_key or identity in seen:
            continue
        seen.add(identity)
        sanitized.append(label)
        if len(sanitized) >= limit:
            break
    return sanitized


VEHICLE_BRAND_ALIASES = {
    "奥迪": "AUDI", "奔驰": "Mercedes-Benz", "宝马": "BMW", "大众": "Volkswagen",
    "特斯拉": "Tesla", "沃尔沃": "Volvo", "凯迪拉克": "Cadillac", "雷克萨斯": "Lexus",
}


def vehicle_search_aliases(keyword, supplied=None):
    """Build deterministic public-search aliases without inventing model names."""
    canonical = normalized_vehicle_label(keyword)
    aliases = []
    for value in [canonical, *(supplied or [])]:
        label = normalized_vehicle_label(value)
        if label and vehicle_identity_key(label) not in {vehicle_identity_key(x) for x in aliases}:
            aliases.append(label)
    compact = re.sub(r"\s+", "", canonical)
    for chinese_brand, english_brand in VEHICLE_BRAND_ALIASES.items():
        if not compact.startswith(chinese_brand):
            continue
        model = compact[len(chinese_brand):].strip()
        if model:
            english = f"{english_brand} {model}"
            if vehicle_identity_key(english) not in {vehicle_identity_key(x) for x in aliases}:
                aliases.append(english)
            if re.search(r"[A-Za-z0-9]", model) and len(model) >= 2 and vehicle_identity_key(model) not in {vehicle_identity_key(x) for x in aliases}:
                aliases.append(model)
        break
    return aliases


def _comparison_evidence_identity(item, fallback_model=""):
    model = item.get("normalizedModel") or item.get("brandName") or fallback_model
    evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
    content_id = (item.get("id") or item.get("platformItemId") or item.get("sourceUrl")
                  or evidence.get("contentHash") or f'{item.get("text", "")}|{item.get("publishedAt", "")}')
    return vehicle_identity_key(model), str(item.get("platform") or ""), str(content_id or "")


def normalize_comparison_result(result):
    """Defensively normalize new and historical comparison payloads at read time."""
    own_model = normalized_vehicle_label(result.get("keyword"))
    own_key = vehicle_identity_key(own_model)
    canonical_models = {own_key: own_model} if own_key else {}

    comparisons = []
    seen_models = set()
    for row in result.get("modelComparisons", []) or []:
        model = normalized_vehicle_label(row.get("model"))
        identity = vehicle_identity_key(model)
        if not identity or identity in seen_models:
            continue
        seen_models.add(identity)
        canonical_models[identity] = own_model if identity == own_key else model
        normalized = dict(row)
        normalized["model"] = canonical_models[identity]
        normalized["role"] = "own" if identity == own_key else "competitor"
        comparisons.append(normalized)
    result["modelComparisons"] = comparisons
    model_collection = [{"model": row.get("model"), "status": (row.get("collectionStatus") or {}).get("status", "not_assessed")}
                        for row in comparisons]
    result["collectionStatus"] = {
        **(result.get("collectionStatus") or {}),
        "status": "complete" if model_collection and all(row["status"] == "complete" for row in model_collection) else "partial",
        "models": model_collection,
    }

    for key in ("modelHeatRanking", "positiveCompetitorsTop5"):
        normalized_rows = []
        seen = set()
        for row in result.get(key, []) or []:
            model = normalized_vehicle_label(row.get("model"))
            identity = vehicle_identity_key(model)
            if not identity or identity in seen or (key == "positiveCompetitorsTop5" and identity == own_key):
                continue
            seen.add(identity)
            normalized = dict(row)
            normalized["model"] = canonical_models.get(identity, own_model if identity == own_key else model)
            normalized_rows.append(normalized)
        result[key] = normalized_rows

    for key in ("comparisonEvidence", "comparisonItems"):
        normalized_items = []
        seen = set()
        for source_item in result.get(key, []) or []:
            item = dict(source_item)
            model = normalized_vehicle_label(item.get("normalizedModel") or item.get("brandName") or own_model)
            identity = vehicle_identity_key(model)
            canonical = canonical_models.get(identity, own_model if identity == own_key else model)
            item["normalizedModel"] = canonical
            item["brandName"] = canonical
            evidence_identity = _comparison_evidence_identity(item, canonical)
            if evidence_identity in seen:
                continue
            seen.add(evidence_identity)
            normalized_items.append(item)
        result[key] = normalized_items
    review = (result.get("qa") or {}).get("threeFlagships") or {}
    reviewed_count = int(review.get("reviewedEvidenceCount") or 0)
    verified_count = len(review.get("verifiedEvidenceIds") or [])
    if review.get("status") == "aligned" and reviewed_count > verified_count:
        review["status"] = "disagreement"
        insight = result.get("unifiedInsight") or {}
        insight["validationStatus"] = "disagreement"
        insight["publicationStatus"] = "conditional" if verified_count else "withheld"
        limitation = f"三路审阅对 {reviewed_count - verified_count} 条证据存在分歧，统一结论仅引用共同通过的证据"
        insight["limitations"] = list(dict.fromkeys([*(insight.get("limitations") or []), limitation]))
        result["unifiedInsight"] = insight
    return result


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


def _date_only(value):
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value or "").strip()))


def resolve_date_window(time_range="30d", start_date="", end_date="", now_dt=None):
    """Return an exact, inclusive user window and the TikHub search preset.

    TikHub exposes coarse presets rather than arbitrary date bounds.  For a
    custom request we fetch its widest supported window, then enforce the
    exact user-selected dates locally before a record can enter the snapshot.
    """
    now_dt = now_dt or datetime.now(timezone.utc)
    if time_range == "custom":
        start = _parse_import_date(start_date)
        end = _parse_import_date(end_date)
        if not start or not end:
            raise ValueError("自定义时间范围必须同时填写开始和结束日期")
        end_exclusive = _date_only(end_date)
        if end_exclusive:
            end += timedelta(days=1)
        if start >= end:
            raise ValueError("自定义结束日期必须晚于开始日期")
        if start < now_dt - timedelta(days=180):
            raise ValueError("自定义时间范围仅支持最近 180 天")
        if end > now_dt + timedelta(days=1, minutes=5):
            raise ValueError("自定义结束日期不能晚于今天")
        return start, end, end_exclusive, "90d"
    if time_range in {"1d", "3d", "7d", "30d", "90d"}:
        return now_dt - timedelta(days=int(time_range[:-1])), now_dt + timedelta(minutes=5), False, time_range
    raise ValueError("不支持的时间范围")


def outside_date_window(published, start, end, end_exclusive=False):
    return published < start or (published >= end if end_exclusive else published > end)


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


def _media_url(value):
    if isinstance(value, str):
        candidate = value.strip()
        if candidate.startswith("//"):
            return f"https:{candidate}"
        return candidate if candidate.startswith(("http://", "https://")) else ""
    if isinstance(value, (list, tuple)):
        return next((url for item in value if (url := _media_url(item))), "")
    if isinstance(value, dict):
        for key in ("url_list", "urlList", "urls", "url", "uri"):
            if url := _media_url(value.get(key)):
                return url
    return ""


def _hashtags(row, text):
    values = []
    for name in ("cha_list", "challenge_list", "tag_list", "hashtags", "topics"):
        raw = row.get(name)
        if not isinstance(raw, list):
            continue
        for value in raw:
            if isinstance(value, dict):
                value = _first(value, "cha_name", "name", "title", "tag_name", default="")
            label = clean_content_text(value).strip("# ")
            if label:
                values.append(label)
    values.extend(match.strip() for match in re.findall(r"#([^#\s]{1,40})#?", str(text or "")))
    return list(dict.fromkeys(value for value in values if value))


def normalize_item(platform, row, keyword, fetched_at, search_alias=""):
    title = clean_content_text(_first(row, "title", "note_title", "video_title", default=""))
    description = clean_content_text(_first(row, "desc", "description", "text", "content", "raw_text", default=""))
    text = clean_content_text(" ".join(value for value in (title, description) if value))
    if not text:
        text = title or description
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
    video = _first(row, "video", "video_info", default={})
    video = video if isinstance(video, dict) else {}
    cover_url = (_media_url(_first(row, "cover_url", "coverUrl", "thumbnail", "cover", "origin_cover", default=""))
                 or _media_url(_first(video, "cover", "origin_cover", "thumbnail", default="")))
    dynamic_cover_url = (_media_url(_first(row, "dynamic_cover", "dynamicCover", default=""))
                         or _media_url(_first(video, "dynamic_cover", "dynamicCover", default="")))
    share_info = _first(row, "share_info", "shareInfo", default={})
    share_info = share_info if isinstance(share_info, dict) else {}
    url = str(_first(row, "share_url", "url", "note_url", "detail_url", default=_first(share_info, "share_url", "url", default="")))
    if not url:
        url = {"douyin": f"https://www.douyin.com/video/{item_id}", "xiaohongshu": f"https://www.xiaohongshu.com/explore/{item_id}", "weibo": f"https://weibo.com/detail/{item_id}"}[platform]
    sentiment, positive, negative = _sentiment(text)
    engagement = likes + comments * 2 + shares * 3 + collects * 2.5
    heat = math.log10(1 + engagement + views * .08) * 20
    canonical = re.sub(r"[\s·•_-]+", "", text.lower())[:80]
    content_hash = hashlib.sha256(f"{platform}|{item_id or canonical}".encode()).hexdigest()
    aliases = [search_alias] if search_alias else []
    searchable_fields = {"title": title, "description": description, "hashtags": " ".join(_hashtags(row, text))}
    matched_fields = [name for name, value in searchable_fields.items()
                      if search_alias and vehicle_identity_key(search_alias) in vehicle_identity_key(value)]
    return {"id": content_hash[:20], "platform": platform, "platformLabel": PLATFORMS[platform]["label"],
            "platformItemId": item_id, "keyword": keyword, "normalizedModel": keyword.strip(), "text": text,
            "title": title, "description": description, "hashtags": _hashtags(row, text),
            "matchedAliases": aliases, "matchedFields": matched_fields,
            "author": author_name, "publishedAt": str(published), "sourceUrl": url,
            "coverUrl": cover_url, "dynamicCoverUrl": dynamic_cover_url,
            "metrics": {"likes": likes, "comments": comments, "shares": shares, "collects": collects, "views": views},
            "sentiment": sentiment, "sentimentEvidence": {"positiveHits": positive, "negativeHits": negative},
            "heat": round(min(100, heat), 2), "matrixContent": bool(re.search(r"官方|旗舰店|品牌|汽车|媒体|矩阵", author_name + text)),
            "evidence": {"source": "TikHub", "fetchedAt": fetched_at, "contentHash": content_hash}}


def passenger_vehicle_scope_exclusion_reason(value):
    """Return a stable rejection code when content belongs to a commercial-vehicle entity."""
    text = value.get("text", "") if isinstance(value, dict) else value
    return "commercial_vehicle_entity" if COMMERCIAL_VEHICLE_ENTITY_PATTERN.search(str(text or "")) else ""


def douyin_pagination_state(payload):
    state = {"hasMore": False, "cursor": "", "searchId": "", "backtrace": ""}
    for node in _walk((payload or {}).get("data") or {}):
        if "cursor" not in node or "has_more" not in node:
            continue
        state = {
            "hasMore": str(node.get("has_more")).lower() in {"1", "true"},
            "cursor": str(node.get("cursor") or "").strip(),
            "searchId": str(node.get("search_id") or node.get("searchId") or "").strip(),
            "backtrace": str(node.get("backtrace") or "").strip(),
        }
        return state
    return state


def douyin_next_cursor(payload):
    state = douyin_pagination_state(payload)
    return state["cursor"] if state["hasMore"] else ""


def ensure_tikhub_success(payload, path):
    """Do not turn a provider-level error hidden behind HTTP 200 into zero rows."""
    if not isinstance(payload, dict) or "code" not in payload:
        return payload
    code = str(payload.get("code")).strip()
    if code in {"0", "200"}:
        return payload
    message = str(payload.get("message") or payload.get("msg") or "未知业务错误").strip()
    raise RuntimeError(f"TikHub API {code}: {path} — {message[:500]}")


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
                    payload = ensure_tikhub_success(json.loads(response.read().decode("utf-8")), path)
                    return payload, {"endpoint": path, "status": response.status}
            except HTTPError as exc:
                if exc.code not in {429, 500, 502, 503, 504} or attempt == 2:
                    detail = exc.read().decode("utf-8", errors="replace").strip()
                    raise RuntimeError(f"TikHub HTTP {exc.code}: {path}{f' — {detail[:500]}' if detail else ''}") from exc
            except (URLError, TimeoutError) as exc:
                if attempt == 2: raise RuntimeError("TikHub 网络错误") from exc
            time.sleep(2 ** attempt)

    def search(self, platform, keyword, page=1, count=20, time_range="30d", cursor="", search_context=None):
        cfg = dict(PLATFORMS[platform])
        override = os.getenv(f"TIKHUB_SOCIAL_{platform.upper()}_ENDPOINT")
        if override:
            cfg["path"] = override
        page_value = cursor if platform == "douyin" and cursor else (page - 1) * count if platform == "douyin" else page
        params = {cfg["query"]: keyword, cfg["page"]: page_value}
        window = TIME_FILTERS.get(time_range, TIME_FILTERS["30d"])[platform]
        if platform == "douyin":
            context = search_context or {}
            params.update({"sort_type": "0", "publish_time": window, "filter_duration": "0", "content_type": "0",
                           "search_id": context.get("searchId", ""), "backtrace": context.get("backtrace", "")})
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


def _aggregate(items, keyword, sources, warnings, comment_rows=None, hot_lists=None, selected_platforms=None,
               hot_items=None, collection_status=None):
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
    hot_items = sorted({item["id"]: item for item in (items if hot_items is None else hot_items)}.values(), key=lambda row: row["heat"], reverse=True)
    analyzed_count = len(items)
    coverage = {
        "relevance": {"analyzed": analyzed_count, "total": analyzed_count, "rate": 100 if analyzed_count else 0},
        "sentiment": {"analyzed": analyzed_count, "total": analyzed_count, "rate": 100 if analyzed_count else 0,
                      "method": "规则初判并进入三路独立复核"},
        "risk": {"analyzed": analyzed_count, "total": analyzed_count, "rate": 100 if analyzed_count else 0},
    }
    return {"keyword": keyword, "generatedAt": utcnow(), "items": items, "hotItems": hot_items, "contentRanking": hot_items[:50],
            "hotWords": hot_words, "ownModelRanking": [{"model": keyword, "heat": round(sum(x["heat"] for x in items), 2), "contentCount": len(items)}],
            "positiveCompetitorsTop5": [], "platforms": platform_rows, "platformShare": platform_rows,
            "creatorRanking": creator_ranking, "matrixSummary": {"contentCount": sum(x["matrixContent"] for x in items), "creatorCount": sum(x["matrixContent"] for x in creator_ranking), "heat": round(sum(x["heat"] for x in items if x["matrixContent"]), 2)},
            "timeline": timeline_rows, "timelineUndated": undated, "riskTopics": sorted(risk_topics, key=lambda x: -x["heat"])[:10], "riskItems": risks[:20],
            "commentInsights": comment_summary, "hotLists": hot_lists or [], "contentClusters": clusters,
            "sources": sources, "warnings": warnings, "collectionStatus": collection_status or {"status": "not_assessed"},
            "analysisCoverage": coverage,
            "statusHint": "未形成高热度" if not items or max((x["heat"] for x in items), default=0) < 60 else "已形成可识别热度",
            "methodology": {"heat": "log10(1+点赞+2×评论+3×分享+2.5×收藏+0.08×播放)×20，封顶100；跨平台总热度为内容热度求和",
                            "dedup": "平台内容ID优先，缺失时使用平台+规范化文本哈希", "sentiment": "正负向词证据计数；冲突或无命中标记中性并进入模型复核", "matrix": "作者名与正文中的官方/品牌/媒体/矩阵标记"},
            "qa": {"evidenceTraceable": all(row["sourceUrl"] and row["evidence"]["contentHash"] for row in items),
                   "threeFlagships": {"required": True, "status": "pending"}, "strategyOutput": "待三路独立审阅形成统一结论"}}


def attach_competitor_rankings(result, competitor_results):
    own_model = normalized_vehicle_label(result.get("keyword"))
    sanitized_models = sanitize_competitor_models(
        own_model, [row.get("keyword") for row in competitor_results], limit=3,
    )
    allowed = {vehicle_identity_key(model) for model in sanitized_models}
    distinct_competitors = []
    seen_competitors = set()
    for competitor in competitor_results:
        identity = vehicle_identity_key(competitor.get("keyword"))
        if identity not in allowed or identity in seen_competitors:
            continue
        seen_competitors.add(identity)
        distinct_competitors.append(competitor)
    competitor_results = distinct_competitors
    rankings = []
    for competitor in competitor_results[:3]:
        positive_items = [item for item in competitor.get("items", []) if item.get("sentiment") == "positive"]
        rankings.append({"model": competitor.get("keyword", ""),
                         "positiveHeat": round(sum(float(item.get("heat") or 0) for item in positive_items), 2),
                         "positiveContentCount": len(positive_items),
                         "contentCount": len(competitor.get("items", []))})
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
            "collectionStatus": dataset.get("collectionStatus", {"status": "not_assessed"}),
            "analysisCoverage": dataset.get("analysisCoverage", {}),
            "collection": {
                "admission": dataset.get("admission", {}),
                "warnings": dataset.get("warnings", []),
                "sources": [source for source in dataset.get("sources", []) if not source.get("capability")],
            },
        })
    result["modelComparisons"] = comparisons
    comparison_evidence = []
    seen_evidence = set()
    for dataset in [result] + competitor_results:
        model = normalized_vehicle_label(dataset.get("keyword"))
        for source_item in dataset.get("contentRanking", [])[:10]:
            item = dict(source_item)
            item["normalizedModel"] = model
            item["brandName"] = model
            identity = _comparison_evidence_identity(item, model)
            if identity in seen_evidence:
                continue
            seen_evidence.add(identity)
            comparison_evidence.append(item)
    result["comparisonEvidence"] = sorted(comparison_evidence, key=lambda x: -float(x.get("heat") or 0))[:50]
    comparison_items = []
    seen_items = set()
    for dataset in [result] + competitor_results:
        model = str(dataset.get("keyword") or "").strip()
        for source_item in dataset.get("items", []):
            item = dict(source_item)
            item["normalizedModel"] = model
            item["brandName"] = model
            identity = _comparison_evidence_identity(item, model)
            if identity in seen_items:
                continue
            seen_items.add(identity)
            comparison_items.append(item)
    result["comparisonItems"] = sorted(comparison_items, key=lambda x: -float(x.get("heat") or 0))
    return normalize_comparison_result(result)


def collect(keyword, platforms=None, pages=1, count=20, time_range="30d", include_enrichment=True, thresholds=None,
            progress_callback=None, start_date="", end_date="", aliases=None):
    keyword = str(keyword or "").strip()
    if not keyword: raise ValueError("请输入车型名")
    platforms = [p for p in (platforms or PLATFORMS) if p in PLATFORMS]
    client, raw_items, sources, warnings = TikHubClient(), [], [], []
    if not client.configured(): raise RuntimeError("服务端未配置 TIKHUB_API_KEY")
    collected_at = datetime.now(timezone.utc)
    start, end, end_exclusive, search_time_range = resolve_date_window(time_range, start_date, end_date, collected_at)
    query_aliases = vehicle_search_aliases(keyword, aliases)
    requested_pages = int(pages or 0)
    safety_limit = max(1, int(_backend_env("MMN_SOCIAL_MAX_PAGES", "100")))
    page_limit = min(requested_pages, safety_limit) if requested_pages > 0 else safety_limit
    page_size = min(50, max(1, int(count)))
    diagnostics = []
    for platform in platforms:
        for alias in query_aliases:
            cursor, context, end_reason, alias_rows = "", {}, "", 0
            for page in range(1, page_limit + 1):
                try:
                    payload, source = client.search(platform, alias, page, page_size, search_time_range, cursor, context)
                    fetched = utcnow(); rows = _content_rows(payload); alias_rows += len(rows)
                    raw_items.extend(normalize_item(platform, row, keyword, fetched, alias) for row in rows)
                    sources.append({"platform": platform, "alias": alias, "page": page, **source,
                                    "fetchedAt": fetched, "itemCount": len(rows)})
                except Exception as exc:
                    warnings.append({"platform": platform, "alias": alias, "message": str(exc)})
                    end_reason = "request_failed"
                    break
                if platform == "douyin":
                    state = douyin_pagination_state(payload)
                    if not state["hasMore"]:
                        end_reason = "exhausted"
                        break
                    cursor = state["cursor"]
                    context = {"searchId": state["searchId"], "backtrace": state["backtrace"]}
                    if not cursor:
                        end_reason = "pagination_context_missing"
                        break
                elif not rows or len(rows) < page_size:
                    end_reason = "exhausted"
                    break
            if not end_reason:
                end_reason = "requested_page_limit" if requested_pages > 0 else "safety_limit"
            diagnostics.append({"platform": platform, "alias": alias, "pagesFetched": page,
                                "candidateCount": alias_rows, "status": "complete" if end_reason == "exhausted" else "partial",
                                "endReason": end_reason})
        if progress_callback:
            progress_callback("collect", 33, f"已完成{PLATFORMS[platform]['label']}全部查询词采集")
    like_thresholds = ({**DEFAULT_LIKE_THRESHOLDS, **{key: int(float(value)) for key, value in thresholds.items() if key in PLATFORMS}}
                       if thresholds is not None else None)
    unique_items = {}
    duplicate_count = 0
    for item in raw_items:
        current = unique_items.get(item["id"])
        if not current:
            unique_items[item["id"]] = item
            continue
        duplicate_count += 1
        current["matchedAliases"] = list(dict.fromkeys([*current.get("matchedAliases", []), *item.get("matchedAliases", [])]))
        current["matchedFields"] = list(dict.fromkeys([*current.get("matchedFields", []), *item.get("matchedFields", [])]))
    admitted, rejected = [], []
    alias_keys = [vehicle_identity_key(alias) for alias in query_aliases]
    for item in unique_items.values():
        published = _parse_import_date(item.get("publishedAt")); reason = ""
        if passenger_vehicle_scope_exclusion_reason(item): reason = "commercial_vehicle_entity"
        elif not any(alias_key and alias_key in vehicle_identity_key(item.get("text", "")) for alias_key in alias_keys): reason = "model_not_relevant"
        elif not published: reason = "publish_time_unverified"
        elif outside_date_window(published, start, end, end_exclusive): reason = "outside_time_range"
        rejection = {"id": item["id"], "platform": item["platform"], "title": item["text"], "likes": item["metrics"]["likes"], "reason": reason}
        if reason:
            rejected.append(rejection)
        else:
            item["evidence"]["verificationStatus"] = "tikhub_search_observation"
            admitted.append(item)
    hot_items = [item for item in admitted if like_thresholds is None or item["metrics"]["likes"] >= like_thresholds[item["platform"]]]
    admission = {"inputCount": len(unique_items), "admittedCount": len(admitted), "rejectedCount": len(rejected), "duplicateCount": duplicate_count,
                 "dateWindow": {"timeRange": time_range, "start": start.isoformat(), "end": end.isoformat(), "endExclusive": end_exclusive},
                 "rejectedReasons": {reason: sum(x["reason"] == reason for x in rejected) for reason in sorted({x["reason"] for x in rejected})},
                 "rejectedByPlatform": {platform: {reason: sum(x["platform"] == platform and x["reason"] == reason for x in rejected)
                                                       for reason in sorted({x["reason"] for x in rejected if x["platform"] == platform})}
                                        for platform in platforms},
                 "rejectedSamples": rejected[:30]}
    hot_admission = {"thresholds": like_thresholds, "qualifiedCount": len(hot_items),
                     "belowThresholdCount": len(admitted) - len(hot_items),
                     "purpose": "仅用于热门内容排行，不影响内容量、情感和风险分析"}
    collection_complete = bool(diagnostics) and all(row["status"] == "complete" for row in diagnostics)
    collection_status = {"status": "complete" if collection_complete else "partial",
                         "scope": "所选平台公开搜索接口在所选时间窗和查询词下可返回的结果",
                         "queries": diagnostics, "reason": "" if collection_complete else "存在未采尽或失败的查询"}
    if progress_callback:
        progress_callback("admission", 67, f"已完成相关性与时间窗校验，相关内容{len(admitted)}条")
    comment_rows, hot_lists = [], []
    if include_enrichment:
        for platform in platforms:
            if "hot" in ENRICHMENT_ENDPOINTS[platform]:
                try:
                    payload, source = client.hot_list(platform); rows = _text_rows(payload)[:20]
                    hot_lists.append({"platform": platform, "platformLabel": PLATFORMS[platform]["label"], "items": [x["text"] for x in rows], **source})
                except Exception as exc: warnings.append({"platform": platform, "capability": "hot_list", "message": str(exc)})
            top = sorted((x for x in hot_items if x["platform"] == platform), key=lambda x: -x["heat"])[:1]
            for item in top:
                try:
                    payload, source = client.comments(item)
                    for row in _text_rows(payload)[:20]:
                        sentiment, positive, negative = _sentiment(row["text"])
                        comment_rows.append({"platform": platform, "platformLabel": PLATFORMS[platform]["label"], "contentId": item["id"], "text": row["text"], "sentiment": sentiment, "positiveHits": positive, "negativeHits": negative, "sourceUrl": item["sourceUrl"]})
                    sources.append({"platform": platform, "capability": "comments", **source, "fetchedAt": utcnow()})
                except Exception as exc: warnings.append({"platform": platform, "capability": "comments", "message": str(exc)})
    result = _aggregate(admitted, keyword, sources, warnings, comment_rows, hot_lists, platforms,
                        hot_items=hot_items, collection_status=collection_status)
    if admission:
        result["admission"] = admission; result["hotAdmission"] = hot_admission
        result["rankingMethod"] = "热门池按点赞量降序，其次评论量、收藏量、分享量、发布时间"
        result["contentRanking"] = sorted(result["hotItems"], key=lambda x: (-x["metrics"]["likes"], -x["metrics"]["comments"], -x["metrics"]["collects"], -x["metrics"]["shares"], -_number(x["publishedAt"])))[:50]
    if progress_callback:
        progress_callback("aggregate", 100, "已完成去重、三类内容池与指标聚合")
    return result


def import_records(records, keyword, platforms=None, thresholds=None, time_range="30d", start_date="", end_date="", filename=""):
    keyword = str(keyword or "").strip()
    if not keyword: raise ValueError("请输入车型名后再导入数据")
    platforms = [p for p in (platforms or PLATFORMS) if p in PLATFORMS]
    thresholds = {**DEFAULT_LIKE_THRESHOLDS, **{key: int(float(value)) for key, value in (thresholds or {}).items() if key in PLATFORMS}}
    start, end, end_exclusive, _ = resolve_date_window(time_range, start_date, end_date)
    admitted, rejected, duplicates, seen = [], [], 0, set()
    keyword_key = re.sub(r"[\s·•_-]+", "", keyword.lower())
    for index, row in enumerate(records or []):
        platform = _import_platform(row)
        text = clean_content_text(_import_value(row, "title"))
        published = _parse_import_date(_import_value(row, "published"))
        likes = _number(_import_value(row, "likes")); item_id = str(_import_value(row, "item_id") or "").strip()
        url = str(_import_value(row, "url") or "").strip()
        cover_url = str(_import_value(row, "cover") or "").strip()
        reason = ""
        if not platform or platform not in platforms: reason = "platform_not_selected"
        elif passenger_vehicle_scope_exclusion_reason(text): reason = "commercial_vehicle_entity"
        elif keyword_key not in re.sub(r"[\s·•_-]+", "", text.lower()): reason = "model_not_relevant"
        elif not published: reason = "publish_time_unverified"
        elif outside_date_window(published, start, end, end_exclusive): reason = "outside_time_range"
        identity = f"{platform}|{item_id or url or text[:100]}"
        if identity in seen: duplicates += 1; continue
        seen.add(identity)
        if reason:
            rejected.append({"row": index + 1, "platform": platform, "title": text, "likes": likes, "reason": reason})
            continue
        raw = {"id": item_id or hashlib.sha1(identity.encode()).hexdigest()[:18], "title": text,
               "author": {"nickname": _import_value(row, "author")}, "create_time": published.timestamp(), "share_url": url, "cover_url": cover_url,
               "statistics": {"digg_count": likes, "comment_count": _number(_import_value(row, "comments")), "share_count": _number(_import_value(row, "shares")),
                              "collect_count": _number(_import_value(row, "collects")), "play_count": _number(_import_value(row, "views"))}}
        item = normalize_item(platform, raw, keyword, utcnow())
        item["evidence"].update({"source": "社媒助手导入", "filename": filename, "verificationStatus": "page_export_verified"})
        admitted.append(item)
    admitted.sort(key=lambda x: (-x["metrics"]["likes"], -x["metrics"]["comments"], -x["metrics"]["collects"], -x["metrics"]["shares"], -_number(x["publishedAt"])))
    hot_items = [item for item in admitted if item["metrics"]["likes"] >= thresholds[item["platform"]]]
    result = _aggregate(admitted, keyword, [{"source": "social_assistant_import", "filename": filename, "itemCount": len(records or [])}], [],
                        selected_platforms=platforms, hot_items=hot_items,
                        collection_status={"status": "complete", "scope": "用户导入文件中的全部记录"})
    result["contentRanking"] = hot_items[:50]; result["items"] = admitted; result["hotItems"] = hot_items
    result["admission"] = {"inputCount": len(records or []), "admittedCount": len(admitted), "rejectedCount": len(rejected), "duplicateCount": duplicates,
                           "rejectedReasons": {reason: sum(x["reason"] == reason for x in rejected) for reason in sorted({x["reason"] for x in rejected})},
                           "dateWindow": {"timeRange": time_range, "start": start.isoformat(), "end": end.isoformat(), "endExclusive": end_exclusive},
                           "rejectedByPlatform": {platform: {reason: sum(x["platform"] == platform and x["reason"] == reason for x in rejected)
                                                               for reason in sorted({x["reason"] for x in rejected if x["platform"] == platform})}
                                                for platform in platforms},
                           "rejectedSamples": rejected[:30]}
    result["hotAdmission"] = {"thresholds": thresholds, "qualifiedCount": len(hot_items),
                              "belowThresholdCount": len(admitted) - len(hot_items),
                              "purpose": "仅用于热门内容排行，不影响内容量、情感和风险分析"}
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
    blocked = [item for item in result.get("items", []) if passenger_vehicle_scope_exclusion_reason(item)]
    if blocked:
        raise ValueError(f"乘用车范围校验未通过：发现{len(blocked)}条商用车实体内容，已阻止快照入库")
    stamp = utcnow(); payload = json.dumps(result, ensure_ascii=False)
    snapshot_id = hashlib.sha256(f"{org_id}|{edition}|{result['keyword']}|{stamp}".encode()).hexdigest()[:24]
    conn.execute("insert into social_trend_snapshots values (?, ?, ?, ?, ?, ?, ?, ?)",
                 (snapshot_id, org_id, edition, result["keyword"], json.dumps(filters or {}, ensure_ascii=False), payload, "tikhub", stamp))
    return {"id": snapshot_id, "createdAt": stamp}


def latest_snapshot(conn, keyword, org_id="local", edition="china", project_filters=None):
    rows = conn.execute(
        "select * from social_trend_snapshots where org_id=? and edition=? and keyword=? order by created_at desc",
        (org_id, edition, keyword),
    ).fetchall()
    expected = project_filters or {}
    expected_competitors = sanitize_competitor_models(keyword, expected.get("competitors", []))
    expected_time_range = str(expected.get("timeRange") or "").strip()
    for row in rows:
        filters = json.loads(row["filters_json"] or "{}")
        stored_competitors = sanitize_competitor_models(keyword, filters.get("competitors", []))
        if expected_competitors and stored_competitors != expected_competitors:
            continue
        if expected_time_range and str(filters.get("timeRange") or "") != expected_time_range:
            continue
        result = json.loads(row["result_json"])
        filters["competitors"] = stored_competitors
        result["snapshot"] = {"id": row["id"], "createdAt": row["created_at"], "filters": filters}
        return normalize_comparison_result(result)
    return None
