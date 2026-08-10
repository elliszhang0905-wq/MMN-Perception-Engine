"""Validated weekly market snapshot storage for the management dashboard.

The refresher is deliberately fail-closed: an incomplete/newer payload never
replaces the last published snapshot. The production discovery source is the
fixed CPCA weekly market-scan index; tests and admin tools may still pass a
validated payload directly.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen


SNAPSHOT_FILE = "weekly_market_snapshot.json"
STATUS_FILE = "weekly_market_refresh_status.json"
REQUIRED_FACTS = {"retail", "wholesale", "nev_retail", "nev_penetration"}
OFFICIAL_INDEX_URL = "https://www.cpcaauto.com/news.php?types=csjd&anid=128"


class LatestArticleParseError(ValueError):
    """The newest official article exists but cannot be safely published."""

    def __init__(self, title, url):
        super().__init__(f"官网最新一期已发布但数据处理未完成：{title}")
        self.title = title
        self.url = url


class _TextAndLinksParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.links = []
        self._href = ""
        self._link_parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href", "")
            self._link_parts = []

    def handle_data(self, data):
        self.parts.append(data)
        if self._href:
            self._link_parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href:
            self.links.append(("".join(self._link_parts).strip(), self._href))
            self._href = ""
            self._link_parts = []

    @property
    def text(self):
        return re.sub(r"\s+", " ", html.unescape(" ".join(self.parts))).strip()


def _fetch_text(url):
    request = Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        },
    )
    with urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def _signed_percent(direction, value):
    return float(value) / 100 * (1 if direction == "增长" else -1)


def _week_title_parts(title):
    match = re.search(
        r"车市扫描\s*[（(](\d{4})年(\d{1,2})月(\d{1,2})日\s*[-—至]\s*(?:(\d{1,2})月)?(\d{1,2})日[）)]",
        title,
    )
    if not match:
        compact = re.search(r"(20\d{2})(\d{2})(\d{2})\s*[-—至]\s*(\d{2})(\d{2})", title)
        if compact:
            year, start_month, start_day, end_month, end_day = map(int, compact.groups())
            return year, start_month, start_day, end_month, end_day
        return None
    year, start_month, start_day, end_month, end_day = match.groups()
    return tuple(map(int, (year, start_month, start_day, end_month or start_month, end_day)))


def _is_weekly_market_scan_title(title, require_weekly_analysis=True):
    normalized = re.sub(r"\s+", "", str(title or ""))
    has_expected_category = not require_weekly_analysis or "周度分析" in normalized
    return has_expected_category and "车市扫描" in normalized and _week_title_parts(normalized) is not None


def _format_week_period(parts):
    year, start_month, start_day, end_month, end_day = parts
    if start_month == end_month:
        return f"{year}年{start_month}月{start_day}—{end_day}日"
    return f"{year}年{start_month}月{start_day}日—{end_month}月{end_day}日"


def _metric_match(text, pattern, label):
    match = re.search(pattern, text)
    if not match:
        raise ValueError(f"官方车市扫描未识别到{label}")
    return match


def parse_official_market_article(article_html, url, title=""):
    parser = _TextAndLinksParser()
    parser.feed(article_html)
    text = parser.text
    title_match = re.search(r"车市扫描\s*[（(][^）)]+[）)]", title or text)
    article_title = title_match.group(0) if title_match else title
    week_parts = _week_title_parts(article_title)
    if not week_parts:
        raise ValueError("官方车市扫描缺少可识别的自然周标题")
    year, _, _, _, _ = week_parts
    yoy_comparison = r"同比去年(?:\d{1,2}月)?同期"
    retail = _metric_match(text, rf"(\d{{1,2}})月1[-—至](\d{{1,2}})日，全国乘用车市场零售([\d.]+)万辆，{yoy_comparison}(下降|增长)([\d.]+)%", "乘用车零售")
    month, end_day, retail_value, retail_direction, retail_yoy = retail.groups()
    wholesale = _metric_match(text, rf"全国乘用车厂商批发([\d.]+)万辆，{yoy_comparison}(下降|增长)([\d.]+)%", "乘用车厂商批发")
    nev = _metric_match(
        text,
        rf"全国乘用车(?:市场新能源|新能源市场)零售([\d.]+)万辆，{yoy_comparison}(下降|增长)([\d.]+)%",
        "新能源零售",
    )
    penetration = _metric_match(text, r"新能源(?:市场)?零售渗透率([\d.]+)%", "新能源零售渗透率")
    published = re.search(r"时间[:：]\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})", text)
    natural_week = _format_week_period(week_parts)
    metric_period = f"{year}年{int(month)}月1—{int(end_day)}日"
    return {
        "facts": [
            {"id": "retail", "label": "乘用车零售", "value": float(retail_value), "unit": "万辆", "yoy": _signed_percent(retail_direction, retail_yoy)},
            {"id": "wholesale", "label": "乘用车厂商批发", "value": float(wholesale.group(1)), "unit": "万辆", "yoy": _signed_percent(wholesale.group(2), wholesale.group(3))},
            {"id": "nev_retail", "label": "新能源零售", "value": float(nev.group(1)), "unit": "万辆", "yoy": _signed_percent(nev.group(2), nev.group(3))},
            {"id": "nev_penetration", "label": "新能源零售渗透率", "value": float(penetration.group(1)), "unit": "%"},
        ],
        "source": {
            "label": f"中国汽车流通协会乘用车市场信息联席分会《{article_title}》",
            "url": url,
            "period": f"截至{year}年{int(month)}月{int(end_day)}日 · {int(month)}月月内累计",
            "metricPeriod": metric_period,
            "metricBasis": "month_to_date",
            "naturalWeekPeriod": natural_week,
            "naturalWeekEndDate": date(week_parts[0], week_parts[3], week_parts[4]).isoformat(),
        },
        "publishedAt": published.group(1) if published else _now(),
    }


def fetch_latest_official_market_payload(fetch_text=None, index_url=OFFICIAL_INDEX_URL):
    fetch = fetch_text or _fetch_text
    index_html = fetch(index_url)
    parser = _TextAndLinksParser()
    parser.feed(index_html)
    candidates = []
    for title, href in parser.links:
        if not _is_weekly_market_scan_title(title, require_weekly_analysis=True):
            continue
        parts = _week_title_parts(title)
        if parts:
            candidates.append((date(parts[0], parts[3], parts[4]), title, urljoin(index_url, href)))
    if not candidates:
        raise ValueError("乘联分会发布页未找到车市扫描周报")
    _, title, article_url = max(candidates, key=lambda item: item[0])
    try:
        return parse_official_market_article(fetch(article_url), article_url, title)
    except ValueError as exc:
        raise LatestArticleParseError(title, article_url) from exc


def _expected_completed_week_end(today=None):
    current = today or datetime.now().astimezone().date()
    return current - timedelta(days=(current.weekday() + 1) % 7)


def _covers_expected_completed_week(natural_week_end, expected_end):
    if natural_week_end >= expected_end:
        return True
    closes_month = (natural_week_end + timedelta(days=1)).day == 1
    return closes_month and expected_end - natural_week_end <= timedelta(days=6)


def _normalize_source(source):
    normalized = dict(source)
    raw_period = str(normalized.get("metricPeriod") or normalized.get("period") or "")
    match = re.search(r"(\d{4})年(\d{1,2})月1\s*[-—至]\s*(\d{1,2})日", raw_period)
    if match:
        year, month, end_day = map(int, match.groups())
        normalized.setdefault("metricPeriod", f"{year}年{month}月1—{end_day}日")
        normalized.setdefault("metricBasis", "month_to_date")
        normalized["period"] = f"截至{year}年{month}月{end_day}日 · {month}月月内累计"
    if not normalized.get("naturalWeekPeriod"):
        parts = _week_title_parts(str(normalized.get("label") or ""))
        if parts:
            normalized["naturalWeekPeriod"] = _format_week_period(parts)
            normalized["naturalWeekEndDate"] = date(parts[0], parts[3], parts[4]).isoformat()
    return normalized


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _atomic_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def _validate(payload):
    if not isinstance(payload, dict):
        raise ValueError("周度市场数据必须是JSON对象")
    source = _normalize_source(payload.get("source") or {})
    facts = payload.get("facts") or []
    by_id = {str(item.get("id") or ""): item for item in facts if isinstance(item, dict)}
    missing = REQUIRED_FACTS - set(by_id)
    if missing:
        raise ValueError("周度市场数据字段不完整：" + ", ".join(sorted(missing)))
    if not all(str(source.get(key) or "").strip() for key in ("label", "url", "period")):
        raise ValueError("周度市场数据缺少来源、链接或统计周期")
    for key in REQUIRED_FACTS:
        value = float(by_id[key].get("value"))
        if value < 0:
            raise ValueError(f"{key}不能为负数")
    penetration = float(by_id["nev_penetration"]["value"])
    if not 0 <= penetration <= 100:
        raise ValueError("新能源渗透率必须在0到100之间")
    for key in ("retail", "wholesale", "nev_retail"):
        yoy = float(by_id[key].get("yoy"))
        if not -1 < yoy < 5:
            raise ValueError(f"{key}同比超出合理范围")
        by_id[key]["priorValue"] = round(float(by_id[key]["value"]) / (1 + yoy), 1)
    normalized_facts = [by_id[key] for key in ("retail", "wholesale", "nev_retail", "nev_penetration")]
    normalized = {"facts": normalized_facts, "source": source}
    normalized["batchId"] = hashlib.sha256(
        json.dumps(normalized, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    normalized["publishedAt"] = str(payload.get("publishedAt") or _now())
    return normalized


def load_weekly_market_snapshot(data_dir, baseline):
    data_dir = Path(data_dir)
    path = data_dir / SNAPSHOT_FILE
    status_path = data_dir / STATUS_FILE
    try:
        snapshot = _validate(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else _validate(baseline)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        snapshot = _validate(baseline)
    try:
        status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        status = {}
    stored_label = str(status.get("statusLabel") or "")
    if stored_label in {"本周数据已更新", "当前为已发布周度数据"}:
        stored_label = "最近一期已发布 · 指标为月内累计"
    elif stored_label in {"本周数据待发布 · 沿用上期"}:
        stored_label = "最近自然周数据待发布 · 当前显示上期月内累计"
    refresh = {
        "cadence": "weekly",
        "schedule": "每周二00:00自动抓取；未发布时工作日上午补抓",
        "scope": ["topKpis", "executiveBrief", "groupImplications", "raceEnvironment"],
        "status": status.get("status") or "baseline",
        "statusLabel": stored_label or "最近一期已发布 · 指标为月内累计",
        "lastAttemptAt": status.get("lastAttemptAt") or "",
        "lastSuccessAt": status.get("lastSuccessAt") or snapshot.get("publishedAt", ""),
        "error": status.get("error") or "",
        "batchId": snapshot["batchId"],
        "sourcePeriod": snapshot["source"]["period"],
        "metricPeriod": snapshot["source"].get("metricPeriod", ""),
        "metricBasis": snapshot["source"].get("metricBasis", ""),
        "naturalWeekPeriod": snapshot["source"].get("naturalWeekPeriod", ""),
    }
    return snapshot, refresh


def refresh_weekly_market_snapshot(data_dir, payload=None, feed_url=None, fetcher=None, official_fetcher=None, today=None):
    data_dir = Path(data_dir)
    attempted_at = _now()
    try:
        if payload is None:
            payload = fetch_latest_official_market_payload(fetch_text=official_fetcher)
        snapshot = _validate(payload)
        natural_week_end = snapshot["source"].get("naturalWeekEndDate")
        expected_end = _expected_completed_week_end(today)
        if natural_week_end and not _covers_expected_completed_week(date.fromisoformat(natural_week_end), expected_end):
            raise RuntimeError(
                f"最近自然周数据待发布：官网最新为{snapshot['source'].get('naturalWeekPeriod')}，"
                f"待发布周截至{expected_end.isoformat()}"
            )
        _atomic_json(data_dir / SNAPSHOT_FILE, snapshot)
        status = {
            "status": "published",
            "statusLabel": "最近自然周已发布 · 指标为月内累计",
            "lastAttemptAt": attempted_at,
            "lastSuccessAt": attempted_at,
            "batchId": snapshot["batchId"],
            "sourcePeriod": snapshot["source"]["period"],
            "naturalWeekPeriod": snapshot["source"].get("naturalWeekPeriod", ""),
            "error": "",
        }
    except Exception as exc:
        error = str(exc)
        awaiting = error.startswith("最近自然周数据待发布")
        latest_parse_failed = isinstance(exc, LatestArticleParseError)
        source_unavailable = not awaiting and not latest_parse_failed and isinstance(exc, (OSError, TimeoutError))
        status = {
            "status": (
                "awaiting_publication"
                if awaiting else (
                    "latest_parse_failed"
                    if latest_parse_failed else ("source_unavailable" if source_unavailable else "carried_forward")
                )
            ),
            "statusLabel": (
                "最近自然周数据待发布 · 当前显示上期月内累计"
                if awaiting else (
                    "最新一期已发布，数据处理未完成 · 当前显示上期月内累计"
                    if latest_parse_failed else (
                        "官方数据源暂时不可用 · 当前显示上期月内累计"
                        if source_unavailable else "数据校验未通过 · 当前显示上期月内累计"
                    )
                )
            ),
            "lastAttemptAt": attempted_at,
            "lastSuccessAt": "",
            "error": error,
        }
        if latest_parse_failed:
            status["latestArticle"] = {"title": exc.title, "url": exc.url}
    _atomic_json(data_dir / STATUS_FILE, status)
    return status
