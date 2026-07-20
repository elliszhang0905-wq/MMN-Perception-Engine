import json
import os
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen


def _config_value(key, default=""):
    value = os.getenv(key)
    if value:
        return value
    path = Path(__file__).resolve().parents[1] / ".env"
    if not path.exists():
        return default
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        name, candidate = stripped.split("=", 1)
        if name.strip() == key:
            return candidate.strip().strip('"').strip("'")
    return default


def _identity_key(value):
    return "".join(char for char in str(value or "").casefold().strip() if char.isalnum())


def validate_creator_identity(creator, reference=None, expected_name=""):
    """Fail closed before collection/persistence when TikHub resolves the wrong account."""
    reference = reference or {}
    actual_id = str(creator.get("platform_creator_id") or "").strip()
    actual_name = str(creator.get("display_name") or "").strip()
    expected_id = str(reference.get("secUserId") or reference.get("userId") or "").strip()
    blocked_names = {
        _identity_key(item) for item in _config_value("MMN_CREATOR_BLOCKED_NAMES", "songzhen").split(",")
        if item.strip()
    }
    blocked_ids = {
        item.strip() for item in _config_value(
            "MMN_CREATOR_BLOCKED_IDS",
            "MS4wLjABAAAANXSltcLCzDGmdNFI2Q_QixVTr67NiYzjKOIP5s03CAE",
        ).split(",") if item.strip()
    }
    if _identity_key(actual_name) in blocked_names or actual_id in blocked_ids:
        raise AdapterError(f"账号 {actual_name or actual_id} 已被 MMN 禁用，拒绝采集和入库",
                           "creator_blocked", False, False)
    if expected_id and actual_id != expected_id:
        raise AdapterError(f"TikHub 身份错配：主页 ID {expected_id}，资料响应 ID {actual_id or '缺失'}",
                           "identity_mismatch", False, False)
    if not str(expected_name or "").strip():
        raise AdapterError("缺少预期达人名称，无法执行身份一致性确认",
                           "identity_confirmation_required", False, False)
    if _identity_key(actual_name) != _identity_key(expected_name):
        raise AdapterError(f"TikHub 身份错配：预期达人“{expected_name}”，实际返回“{actual_name or '未知'}”",
                           "identity_mismatch", False, False)
    identity = (creator.get("profile") or {}).setdefault("identity", {})
    identity.update({"status": "matched", "expectedName": str(expected_name).strip(),
                     "matchedPlatformCreatorId": actual_id})
    return creator


class AdapterError(RuntimeError):
    def __init__(self, message, category="platform_error", retryable=True, degraded=False):
        super().__init__(message)
        self.category = category
        self.retryable = retryable
        self.degraded = degraded


@dataclass(frozen=True)
class FieldValue:
    value: object
    platform: str
    source_endpoint: str
    fetch_time: str
    availability: str = "available"
    confidence: float = 1.0

    def as_dict(self):
        return self.__dict__.copy()


class PlatformAdapter:
    platform = "unknown"
    hosts = ()
    short_hosts = ()

    def __init__(self, version=None):
        self.version = version or _config_value(f"TIKHUB_{self.platform.upper()}_VERSION", "v1")
        self.base_url = _config_value("TIKHUB_BASE_URL", "https://api.tikhub.io").rstrip("/")
        self.api_key = _config_value("TIKHUB_API_KEY", "")
        raw = _config_value(f"TIKHUB_{self.platform.upper()}_ENDPOINTS", "")
        self.endpoints = json.loads(raw) if raw else self.default_endpoints()
        self.expected_creator_name = ""

    def default_endpoints(self):
        raise NotImplementedError

    def parse_link(self, url):
        parsed = urlparse(str(url or "").strip())
        host = parsed.netloc.lower().split(":")[0]
        if parsed.scheme not in {"http", "https"} or host not in (*self.hosts, *self.short_hosts):
            raise AdapterError(f"不是受支持的{self.platform}公开链接", "invalid_link", False)
        return {"platform": self.platform, "url": parsed.geturl(), "isShortLink": host in self.short_hosts,
                "requiresResolution": host in self.short_hosts, "version": self.version}

    def _endpoint(self, name):
        path = self.endpoints.get(name)
        if not path:
            raise AdapterError(f"平台版本 {self.version} 未配置接口 {name}", "endpoint_version", True, True)
        return path.format(version=self.version)

    def request(self, name, params=None, attempts=4):
        if not self.api_key:
            raise AdapterError("未配置 TIKHUB_API_KEY", "configuration", False)
        endpoint = self._endpoint(name)
        url = endpoint if endpoint.startswith("http") else f"{self.base_url}{endpoint}"
        if params:
            from urllib.parse import urlencode
            url += ("&" if "?" in url else "?") + urlencode(params)
        for attempt in range(attempts):
            try:
                req = Request(url, headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/json",
                                            "User-Agent": "MMN-Perception-Engine/1.0"})
                with urlopen(req, timeout=float(os.getenv("TIKHUB_TIMEOUT_SECONDS", "30"))) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    self.ensure_success(payload, endpoint)
                    return payload, {"endpoint": endpoint, "url": url, "status": response.status,
                                     "fetchedAt": datetime.now(timezone.utc).isoformat()}
            except HTTPError as exc:
                category = "rate_limited" if exc.code == 429 else "auth" if exc.code in {401, 403} else "platform_error"
                retryable = exc.code in {408, 429, 500, 502, 503, 504}
                if not retryable or attempt == attempts - 1:
                    raise AdapterError(f"TikHub HTTP {exc.code}", category, retryable, category == "platform_error") from exc
            except (URLError, TimeoutError) as exc:
                if attempt == attempts - 1:
                    raise AdapterError(f"TikHub 网络错误: {exc}", "network", True, True) from exc
            time.sleep(min(8, (2 ** attempt) + random.random()))

    @staticmethod
    def ensure_success(payload, endpoint):
        """Reject provider errors hidden behind a successful HTTP response."""
        if not isinstance(payload, dict):
            raise AdapterError("TikHub 返回了非 JSON 对象", "invalid_response", False, True)
        if "code" not in payload:
            return payload
        code = str(payload.get("code")).strip()
        if code in {"0", "200"}:
            return payload
        message = str(payload.get("message_zh") or payload.get("message") or payload.get("msg") or "未知业务错误").strip()
        category = "rate_limited" if code == "429" else "auth" if code in {"401", "403"} else "provider_business_error"
        raise AdapterError(f"TikHub API {code}: {endpoint} — {message[:500]}", category,
                           code in {"408", "429", "500", "502", "503", "504"}, True)

    def field(self, value, endpoint, confidence=1.0):
        available = value is not None
        return FieldValue(value if available else None, self.platform, endpoint,
                          datetime.now(timezone.utc).isoformat(), "available" if available else "not_returned",
                          confidence if available else 0.0).as_dict()

    @staticmethod
    def first_media_url(value):
        if isinstance(value, str) and value.startswith(("https://", "http://")):
            return value
        if isinstance(value, dict):
            for key in ("url_list", "backup_urls"):
                urls = value.get(key)
                if isinstance(urls, list):
                    found = next((url for url in urls if isinstance(url, str) and url.startswith(("https://", "http://"))), None)
                    if found:
                        return found
            for key in ("master_url", "url", "play_url", "download_url"):
                found = value.get(key)
                if isinstance(found, str) and found.startswith(("https://", "http://")):
                    return found
            for child in value.values():
                found = PlatformAdapter.first_media_url(child)
                if found:
                    return found
        if isinstance(value, list):
            for child in value:
                found = PlatformAdapter.first_media_url(child)
                if found:
                    return found
        return None

    def health(self):
        return {"platform": self.platform, "configured": bool(self.api_key), "version": self.version,
                "endpoints": sorted(self.endpoints), "status": "configured" if self.api_key else "missing_key"}


class DouyinAdapter(PlatformAdapter):
    platform = "douyin"
    hosts = ("www.douyin.com", "douyin.com")
    short_hosts = ("v.douyin.com",)

    def default_endpoints(self):
        return {"profile": "/api/{version}/douyin/web/handler_user_profile",
                "posts": "/api/{version}/douyin/app/v3/fetch_user_post_videos",
                "video": "/api/{version}/douyin/app/v3/fetch_one_video_v2",
                "comments": "/api/{version}/douyin/app/v3/fetch_video_comments"}

    @staticmethod
    def _walk_dicts(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from DouyinAdapter._walk_dicts(child)
        elif isinstance(value, list):
            for child in value:
                yield from DouyinAdapter._walk_dicts(child)

    @staticmethod
    def _find_list(value, names):
        if isinstance(value, dict):
            for name in names:
                candidate = value.get(name)
                if isinstance(candidate, list):
                    return candidate
            for child in value.values():
                found = DouyinAdapter._find_list(child, names)
                if found is not None:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = DouyinAdapter._find_list(child, names)
                if found is not None:
                    return found
        return None

    def resolve_public_url(self, url):
        parsed = self.parse_link(url)
        if not parsed["requiresResolution"]:
            return parsed["url"]
        try:
            req = Request(parsed["url"], headers={"User-Agent": "MMN-Perception-Engine/1.0"})
            with urlopen(req, timeout=float(os.getenv("TIKHUB_TIMEOUT_SECONDS", "30"))) as response:
                resolved = response.geturl()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise AdapterError(f"抖音短链接解析失败: {exc}", "link_resolution", True, True) from exc
        resolved_parsed = urlparse(resolved)
        resolved_host = resolved_parsed.netloc.lower().split(":")[0]
        if resolved_host in {"iesdouyin.com", "www.iesdouyin.com"}:
            query = parse_qs(resolved_parsed.query)
            path_match = re.search(r"/share/user/([^/?#]+)", resolved_parsed.path)
            sec_user_id = (path_match.group(1) if path_match else "") or (query.get("sec_uid") or [""])[0]
            if not sec_user_id:
                raise AdapterError("抖音短链接解析后缺少 sec_user_id", "identity_resolution", False, True)
            resolved = f"https://www.douyin.com/user/{sec_user_id}"
        self.parse_link(resolved)
        return resolved

    def creator_reference(self, url):
        resolved_url = self.resolve_public_url(url)
        parsed = urlparse(resolved_url)
        match = re.search(r"/user/([^/?#]+)", parsed.path)
        query = parse_qs(parsed.query)
        sec_user_id = (match.group(1) if match else "") or (query.get("sec_uid") or query.get("sec_user_id") or [""])[0]
        if not sec_user_id:
            raise AdapterError("抖音主页链接中缺少 sec_user_id", "identity_resolution", False, True)
        return {"sourceUrl": str(url), "resolvedUrl": resolved_url, "secUserId": sec_user_id}

    @staticmethod
    def _metric(value):
        if value is None or value == "":
            return None
        try:
            return max(0, int(float(value)))
        except (TypeError, ValueError):
            return None

    def normalize_profile(self, payload, endpoint, reference):
        profile = None
        for candidate in self._walk_dicts(payload.get("data")):
            sec_uid = candidate.get("sec_uid") or candidate.get("sec_user_id")
            nickname = candidate.get("nickname") or candidate.get("display_name")
            if sec_uid and nickname:
                profile = candidate
                break
        if not profile:
            raise AdapterError("TikHub 抖音资料响应缺少账号身份字段", "invalid_response", False, True)
        sec_uid = profile.get("sec_uid") or profile.get("sec_user_id")
        fetched_at = datetime.now(timezone.utc).isoformat()
        followers = self._metric(profile.get("follower_count") or profile.get("fans_count"))
        return {
            "platform": self.platform,
            "platform_creator_id": str(sec_uid),
            "display_name": str(profile.get("nickname") or profile.get("display_name") or sec_uid),
            "followers": followers,
            "profile": {
                "nickname": profile.get("nickname") or profile.get("display_name"),
                "uniqueId": profile.get("unique_id") or profile.get("short_id"),
                "uid": profile.get("uid") or profile.get("user_id"),
                "secUserId": sec_uid,
                "signature": profile.get("signature") or profile.get("bio"),
                "followers": self.field(followers, endpoint),
                "following": self.field(self._metric(profile.get("following_count")), endpoint),
                "postCount": self.field(self._metric(profile.get("aweme_count") or profile.get("post_count")), endpoint),
                "verification": self.field(profile.get("enterprise_verify_reason") or profile.get("custom_verify") or
                                           profile.get("verification_reason"), endpoint, .9),
                "identity": {"status": "needs_review", **reference},
                "provenance": {"platform": self.platform, "sourceEndpoint": endpoint, "fetchTime": fetched_at,
                               "availability": "available", "confidence": .9},
            },
        }

    def normalize_posts(self, payload, endpoint):
        rows = self._find_list(payload.get("data"), ("aweme_list", "items", "videos", "post_list")) or []
        assets = []
        fetched_at = datetime.now(timezone.utc).isoformat()
        for row in rows:
            if not isinstance(row, dict):
                continue
            source_id = row.get("aweme_id") or row.get("item_id")
            if not source_id:
                continue
            stats = row.get("statistics") if isinstance(row.get("statistics"), dict) else {}
            likes = self._metric(stats.get("digg_count") if "digg_count" in stats else row.get("digg_count"))
            comments = self._metric(stats.get("comment_count") if "comment_count" in stats else row.get("comment_count"))
            shares = self._metric(stats.get("share_count") if "share_count" in stats else row.get("share_count"))
            collects = self._metric(stats.get("collect_count") if "collect_count" in stats else row.get("collect_count"))
            views = self._metric(stats.get("play_count") if "play_count" in stats else row.get("play_count"))
            if views == 0 and any((likes or 0, comments or 0, shares or 0, collects or 0)):
                views = None
            timestamp = row.get("create_time") or row.get("published_at")
            try:
                published_at = datetime.fromtimestamp(float(timestamp), timezone.utc).isoformat() if timestamp else None
            except (TypeError, ValueError, OSError):
                published_at = None
            share_info = row.get("share_info") if isinstance(row.get("share_info"), dict) else {}
            video = row.get("video") if isinstance(row.get("video"), dict) else {}
            image_urls = []
            for image in row.get("images") or []:
                found = self.first_media_url(image)
                if found and found not in image_urls:
                    image_urls.append(found)
            cover_url = self.first_media_url(video.get("cover"))
            if cover_url and cover_url not in image_urls:
                image_urls.append(cover_url)
            is_image_note = row.get("aweme_type") == 68
            play_url = self.first_media_url(video.get("play_addr"))
            audio_url = self.first_media_url(video.get("audio")) or (play_url if is_image_note else None)
            tags = [str(item.get("hashtag_name")) for item in (row.get("text_extra") or [])
                    if isinstance(item, dict) and item.get("hashtag_name")]
            assets.append({
                "source_id": str(source_id),
                "source_url": share_info.get("share_url") or row.get("share_url"),
                "title": str(row.get("desc") or row.get("title") or "").strip(),
                "published_at": published_at,
                "asset_type": "image_note" if is_image_note else "video",
                "views": views, "likes": likes, "comments": comments, "collects": collects, "shares": shares,
                "primary_tag": tags[0] if tags else "未分类", "tags": tags,
                "interference_tags": [],
                "media": {"videoUrl": None if is_image_note else play_url, "audioUrl": audio_url,
                          "imageUrls": image_urls[:12],
                          "durationMs": self._metric(row.get("duration") or video.get("duration"))},
                "provenance": {"platform": self.platform, "sourceEndpoint": endpoint, "fetchTime": fetched_at,
                               "availability": "available", "confidence": .95,
                               "missingMetrics": [name for name, value in (("views", views), ("likes", likes),
                                                                          ("comments", comments), ("collects", collects),
                                                                          ("shares", shares)) if value is None]},
            })
        return assets

    def normalize_comments(self, payload, endpoint, source_id):
        rows = self._find_list(payload.get("data"), ("comments", "comment_list", "items")) or []
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            comment_id = row.get("cid") or row.get("comment_id") or row.get("id")
            quote = str(row.get("text") or row.get("content") or row.get("comment_text") or "").strip()
            if not comment_id or not quote:
                continue
            user = row.get("user") if isinstance(row.get("user"), dict) else {}
            evidence.append({
                "source_id": str(source_id), "comment_id": str(comment_id), "evidence_type": "comment",
                "quote_text": quote, "confidence": .95,
                "metadata": {"likes": self._metric(row.get("digg_count") or row.get("like_count")),
                             "createdAt": row.get("create_time"), "userName": user.get("nickname"),
                             "userId": user.get("uid") or user.get("sec_uid")},
                "provenance": {"platform": self.platform, "sourceEndpoint": endpoint, "fetchTime": fetched_at,
                               "availability": "available", "confidence": .95},
            })
        return evidence

    def collect_comments(self, assets, max_assets=3, comments_per_asset=20):
        evidence, exchanges = [], []
        for asset in list(assets)[:max(0, max_assets)]:
            payload, meta = self.request("comments", {"aweme_id": asset["source_id"], "cursor": 0,
                                                       "count": max(1, min(50, comments_per_asset))})
            exchanges.append((payload, meta))
            page = self.normalize_comments(payload, meta["endpoint"], asset["source_id"])
            evidence.extend(page[:max(1, min(50, comments_per_asset))])
        return evidence, exchanges

    def collect_creator(self, url, max_posts=50):
        reference = self.creator_reference(url)
        profile_payload, profile_meta = self.request("profile", {"sec_user_id": reference["secUserId"]})
        creator = self.normalize_profile(profile_payload, profile_meta["endpoint"], reference)
        validate_creator_identity(creator, reference, self.expected_creator_name)
        collected, cursor, exchanges = [], 0, [(profile_payload, profile_meta)]
        while len(collected) < max_posts:
            count = min(20, max_posts - len(collected))
            posts_payload, posts_meta = self.request("posts", {"sec_user_id": creator["platform_creator_id"],
                                                                "max_cursor": cursor, "count": count, "sort_type": 0})
            exchanges.append((posts_payload, posts_meta))
            page = self.normalize_posts(posts_payload, posts_meta["endpoint"])
            known = {item["source_id"] for item in collected}
            collected.extend(item for item in page if item["source_id"] not in known)
            data = posts_payload.get("data") if isinstance(posts_payload, dict) else {}
            next_cursor = None
            for candidate in self._walk_dicts(data):
                if "max_cursor" in candidate:
                    next_cursor = candidate.get("max_cursor")
                    break
            if not page or next_cursor in {None, cursor, str(cursor)}:
                break
            cursor = next_cursor
        return creator, collected[:max_posts], exchanges


class XiaohongshuAdapter(PlatformAdapter):
    platform = "xiaohongshu"
    hosts = ("www.xiaohongshu.com", "xiaohongshu.com")
    short_hosts = ("xhslink.com", "www.xhslink.com")

    def default_endpoints(self):
        return {"profile": "/api/{version}/xiaohongshu/app_v2/get_user_info",
                "posts": "/api/{version}/xiaohongshu/app_v2/get_user_posted_notes",
                "comments": "/api/{version}/xiaohongshu/app_v2/get_note_comments"}

    @staticmethod
    def _data(payload):
        envelope = payload.get("data") if isinstance(payload, dict) else None
        return envelope.get("data") if isinstance(envelope, dict) else None

    @classmethod
    def ensure_success(cls, payload, endpoint):
        super().ensure_success(payload, endpoint)
        envelope = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(envelope, dict):
            code = str(envelope.get("code", "0"))
            success = envelope.get("success")
            if success is False or code not in {"0", "200"}:
                message = str(envelope.get("msg") or envelope.get("message") or "小红书接口业务错误")
                raise AdapterError(f"TikHub 小红书 API {code}: {endpoint} — {message[:500]}",
                                   "provider_business_error", False, True)
        return payload

    def resolve_public_url(self, url):
        parsed = self.parse_link(url)
        if not parsed["requiresResolution"]:
            return parsed["url"]
        try:
            req = Request(parsed["url"], headers={"User-Agent": "MMN-Perception-Engine/1.0"})
            with urlopen(req, timeout=float(os.getenv("TIKHUB_TIMEOUT_SECONDS", "30"))) as response:
                resolved = response.geturl()
        except (HTTPError, URLError, TimeoutError) as exc:
            raise AdapterError(f"小红书短链接解析失败: {exc}", "link_resolution", True, True) from exc
        self.parse_link(resolved)
        return resolved

    def creator_reference(self, url):
        resolved_url = self.resolve_public_url(url)
        parsed = urlparse(resolved_url)
        match = re.search(r"/user/profile/([^/?#]+)", parsed.path)
        user_id = match.group(1) if match else ""
        if not user_id:
            raise AdapterError("小红书主页链接中缺少 user_id", "identity_resolution", False, True)
        query = parse_qs(parsed.query)
        return {"sourceUrl": str(url), "resolvedUrl": resolved_url, "userId": user_id,
                "xsecToken": (query.get("xsec_token") or [""])[0]}

    @staticmethod
    def _metric(value):
        if value is None or value == "":
            return None
        try:
            return max(0, int(float(value)))
        except (TypeError, ValueError):
            return None

    def normalize_profile(self, payload, endpoint, reference):
        profile = self._data(payload)
        if not isinstance(profile, dict) or not profile.get("userid") or not profile.get("nickname"):
            raise AdapterError("TikHub 小红书资料响应缺少账号身份字段", "invalid_response", False, True)
        fetched_at = datetime.now(timezone.utc).isoformat()
        followers = self._metric(profile.get("fans"))
        posted = profile.get("note_num_stat") if isinstance(profile.get("note_num_stat"), dict) else {}
        return {
            "platform": self.platform, "platform_creator_id": str(profile["userid"]),
            "display_name": str(profile["nickname"]), "followers": followers,
            "profile": {
                "nickname": profile.get("nickname"), "redId": profile.get("red_id"),
                "signature": profile.get("desc"), "location": profile.get("location"),
                "followers": self.field(followers, endpoint),
                "following": self.field(self._metric(profile.get("follows")), endpoint),
                "postCount": self.field(self._metric(posted.get("posted")), endpoint),
                "likesAndCollects": self.field(self._metric(sum((posted.get("liked") or 0,
                                                                  posted.get("collected") or 0))), endpoint),
                "verification": self.field(profile.get("red_official_verify_content") or None, endpoint, .9),
                "identity": {"status": "needs_review", **reference},
                "provenance": {"platform": self.platform, "sourceEndpoint": endpoint,
                               "fetchTime": fetched_at, "availability": "available", "confidence": .95},
            },
        }

    def normalize_posts(self, payload, endpoint):
        data = self._data(payload)
        rows = data.get("notes") if isinstance(data, dict) else []
        fetched_at = datetime.now(timezone.utc).isoformat()
        assets = []
        for row in rows or []:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            likes = self._metric(row.get("likes"))
            comments = self._metric(row.get("comments_count"))
            collects = self._metric(row.get("collected_count"))
            shares = self._metric(row.get("share_count"))
            views = self._metric(row.get("view_count"))
            if views == 0 and any((likes or 0, comments or 0, collects or 0, shares or 0)):
                views = None
            timestamp = row.get("create_time")
            try:
                published_at = datetime.fromtimestamp(float(timestamp), timezone.utc).isoformat() if timestamp else None
            except (TypeError, ValueError, OSError):
                published_at = None
            note_type = str(row.get("type") or "").lower()
            title = str(row.get("display_title") or row.get("title") or row.get("desc") or "").strip()
            images = [str(item.get("url")) for item in (row.get("images_list") or [])
                      if isinstance(item, dict) and str(item.get("url") or "").startswith(("https://", "http://"))]
            video_info = row.get("video_info_v2") if isinstance(row.get("video_info_v2"), dict) else {}
            media = video_info.get("media") if isinstance(video_info.get("media"), dict) else {}
            streams = media.get("stream") if isinstance(media.get("stream"), dict) else {}
            video_url = self.first_media_url(streams.get("h264")) or self.first_media_url(streams.get("h265"))
            audio_url = self.first_media_url(media.get("audio_stream"))
            video_meta = media.get("video") if isinstance(media.get("video"), dict) else {}
            subtitles = video_meta.get("subtitles") if isinstance(video_meta.get("subtitles"), dict) else {}
            subtitle_urls = []
            for language in ("source", "zh-CN", "en-US"):
                found = self.first_media_url(subtitles.get(language))
                if found and found not in subtitle_urls:
                    subtitle_urls.append(found)
            first_frame = self.first_media_url(video_info.get("image"))
            if first_frame and first_frame not in images:
                images.insert(0, first_frame)
            duration = self._metric(video_meta.get("duration") or video_info.get("capa", {}).get("duration"))
            assets.append({
                "source_id": str(row["id"]),
                "source_url": f"https://www.xiaohongshu.com/explore/{row['id']}",
                "title": title, "description": str(row.get("desc") or "").strip(),
                "published_at": published_at, "asset_type": "video" if note_type == "video" else "image_note",
                "views": views, "likes": likes, "comments": comments, "collects": collects, "shares": shares,
                "primary_tag": "未分类", "tags": [], "interference_tags": [],
                "media": {"videoUrl": video_url, "audioUrl": audio_url, "imageUrls": images[:12],
                          "subtitleUrls": subtitle_urls, "durationMs": duration * 1000 if duration else None},
                "provenance": {"platform": self.platform, "sourceEndpoint": endpoint, "fetchTime": fetched_at,
                               "availability": "available", "confidence": .95,
                               "missingMetrics": [name for name, value in (("views", views), ("likes", likes),
                                                                           ("comments", comments), ("collects", collects),
                                                                           ("shares", shares)) if value is None]},
            })
        return assets

    def normalize_comments(self, payload, endpoint, source_id):
        data = self._data(payload)
        rows = data.get("comments") if isinstance(data, dict) else []
        fetched_at = datetime.now(timezone.utc).isoformat()
        evidence = []
        for row in rows or []:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            quote = str(row.get("content") or "").strip()
            if not quote:
                continue
            user = row.get("user") if isinstance(row.get("user"), dict) else {}
            evidence.append({
                "source_id": str(source_id), "comment_id": str(row["id"]), "evidence_type": "comment",
                "quote_text": quote, "confidence": .95,
                "metadata": {"likes": self._metric(row.get("like_count")), "createdAt": row.get("time"),
                             "userName": user.get("nickname"), "userId": user.get("userid")},
                "provenance": {"platform": self.platform, "sourceEndpoint": endpoint,
                               "fetchTime": fetched_at, "availability": "available", "confidence": .95},
            })
        return evidence

    def collect_comments(self, assets, max_assets=3, comments_per_asset=20):
        evidence, exchanges = [], []
        for asset in list(assets)[:max(0, max_assets)]:
            payload, meta = self.request("comments", {"note_id": asset["source_id"], "cursor": "", "index": 0,
                                                       "pageArea": "UNFOLDED", "sort_strategy": "like_count"})
            exchanges.append((payload, meta))
            page = self.normalize_comments(payload, meta["endpoint"], asset["source_id"])
            evidence.extend(page[:max(1, min(50, comments_per_asset))])
        return evidence, exchanges

    def collect_creator(self, url, max_posts=50):
        reference = self.creator_reference(url)
        profile_payload, profile_meta = self.request("profile", {"user_id": reference["userId"]})
        creator = self.normalize_profile(profile_payload, profile_meta["endpoint"], reference)
        validate_creator_identity(creator, reference, self.expected_creator_name)
        collected, cursor, exchanges = [], "", [(profile_payload, profile_meta)]
        while len(collected) < max_posts:
            posts_payload, posts_meta = self.request("posts", {"user_id": creator["platform_creator_id"],
                                                                "cursor": cursor})
            exchanges.append((posts_payload, posts_meta))
            page = self.normalize_posts(posts_payload, posts_meta["endpoint"])
            known = {item["source_id"] for item in collected}
            collected.extend(item for item in page if item["source_id"] not in known)
            data = self._data(posts_payload)
            has_more = bool(data.get("has_more")) if isinstance(data, dict) else False
            next_cursor = page[-1]["source_id"] if page else ""
            if not page or not has_more or next_cursor == cursor:
                break
            cursor = next_cursor
        return creator, collected[:max_posts], exchanges


def adapter_for_url(url):
    host = urlparse(str(url or "").strip()).netloc.lower().split(":")[0]
    for adapter in (DouyinAdapter(), XiaohongshuAdapter()):
        if host in (*adapter.hosts, *adapter.short_hosts):
            return adapter
    raise AdapterError("仅支持抖音和小红书公开主页链接", "invalid_link", False)
