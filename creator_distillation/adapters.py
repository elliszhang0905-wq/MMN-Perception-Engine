import json
import os
import random
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


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
        self.version = version or os.getenv(f"TIKHUB_{self.platform.upper()}_VERSION", "v1")
        self.base_url = os.getenv("TIKHUB_BASE_URL", "https://api.tikhub.io").rstrip("/")
        self.api_key = os.getenv("TIKHUB_API_KEY", "")
        raw = os.getenv(f"TIKHUB_{self.platform.upper()}_ENDPOINTS", "")
        self.endpoints = json.loads(raw) if raw else self.default_endpoints()

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
                    return json.loads(response.read().decode("utf-8")), {"endpoint": endpoint, "url": url, "status": response.status}
            except HTTPError as exc:
                category = "rate_limited" if exc.code == 429 else "auth" if exc.code in {401, 403} else "platform_error"
                retryable = exc.code in {408, 429, 500, 502, 503, 504}
                if not retryable or attempt == attempts - 1:
                    raise AdapterError(f"TikHub HTTP {exc.code}", category, retryable, category == "platform_error") from exc
            except (URLError, TimeoutError) as exc:
                if attempt == attempts - 1:
                    raise AdapterError(f"TikHub 网络错误: {exc}", "network", True, True) from exc
            time.sleep(min(8, (2 ** attempt) + random.random()))

    def field(self, value, endpoint, confidence=1.0):
        available = value is not None
        return FieldValue(value if available else None, self.platform, endpoint,
                          datetime.now(timezone.utc).isoformat(), "available" if available else "not_returned",
                          confidence if available else 0.0).as_dict()

    def health(self):
        return {"platform": self.platform, "configured": bool(self.api_key), "version": self.version,
                "endpoints": sorted(self.endpoints), "status": "configured" if self.api_key else "missing_key"}


class DouyinAdapter(PlatformAdapter):
    platform = "douyin"
    hosts = ("www.douyin.com", "douyin.com")
    short_hosts = ("v.douyin.com",)

    def default_endpoints(self):
        return {"profile": "/api/{version}/douyin/web/fetch_user_profile",
                "posts": "/api/{version}/douyin/web/fetch_user_post_videos",
                "comments": "/api/{version}/douyin/web/fetch_video_comments"}


class XiaohongshuAdapter(PlatformAdapter):
    platform = "xiaohongshu"
    hosts = ("www.xiaohongshu.com", "xiaohongshu.com")
    short_hosts = ("xhslink.com", "www.xhslink.com")

    def default_endpoints(self):
        return {"profile": "/api/{version}/xiaohongshu/web/get_user_info",
                "posts": "/api/{version}/xiaohongshu/web/get_user_notes",
                "comments": "/api/{version}/xiaohongshu/web/get_note_comments"}


def adapter_for_url(url):
    host = urlparse(str(url or "").strip()).netloc.lower().split(":")[0]
    for adapter in (DouyinAdapter(), XiaohongshuAdapter()):
        if host in (*adapter.hosts, *adapter.short_hosts):
            return adapter
    raise AdapterError("仅支持抖音和小红书公开主页链接", "invalid_link", False)
