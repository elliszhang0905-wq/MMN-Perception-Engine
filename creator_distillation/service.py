import os

from .adapters import AdapterError, DouyinAdapter, XiaohongshuAdapter, adapter_for_url
from .repository import CreatorRepository


STAGES = [
    ("collect", "平台数据采集", 8), ("media", "素材获取与标准化", 18),
    ("transcribe", "SenseVoice 转写", 34), ("ocr", "PaddleOCR 识别", 47),
    ("shots", "镜头切分与视觉分析", 61), ("comments", "评论分析", 73),
    ("evidence", "结构化证据", 86), ("dna", "内容 DNA 与资产入库", 100),
]


class CreatorDistillationService:
    def __init__(self, repository=None, enqueue=None):
        self.repository = repository or CreatorRepository()
        self.enqueue = enqueue

    def preflight(self, url):
        adapter = adapter_for_url(url)
        parsed = adapter.parse_link(url)
        parsed["health"] = adapter.health()
        parsed["capabilities"] = self._capabilities(adapter.platform)
        return parsed

    @staticmethod
    def _capabilities(platform):
        common = {"metadata": True, "comments": True, "evidence": True, "dna": True}
        return {**common, "video": True, "transcript": True, "ocr": True, "shots": True,
                "imageNote": platform == "xiaohongshu", "degradationSupported": True}

    def create_task(self, payload, org_id="local"):
        url = str(payload.get("creatorUrl") or "").strip()
        preflight = self.preflight(url)
        range_value = str(payload.get("range") or "180")
        range_days = None if range_value == "all" else int(range_value)
        if range_days not in {90, 180, None}: raise ValueError("采集范围仅支持 90、180 或 all")
        sample_count = max(20, min(100, int(payload.get("sampleCount") or 50)))
        task = self.repository.create_task(org_id,url,preflight["platform"],range_days,sample_count,preflight["capabilities"])
        if self.enqueue:
            try: self.enqueue(task["id"])
            except Exception as exc:
                self.repository.update_task(task["id"],status="failed",stage="queue",error_category="queue_unavailable",error_message=str(exc))
        else:
            self.repository.update_task(task["id"],status="queued",stage="awaiting_worker",progress=0,
                                        degraded_reason="Celery worker 未连接；任务已安全排队")
        return self.repository.get_task(task["id"])

    def platform_health(self):
        return {"douyin": DouyinAdapter().health(), "xiaohongshu": XiaohongshuAdapter().health(),
                "queue": {"configured": bool(os.getenv("REDIS_URL")), "mode": "celery"},
                "database": {"target": "postgresql+pgvector", "localFallback": str(self.repository.path)}}

    def handle_get(self, path, query, org_id="local"):
        if path == "/api/creator-distillation/preflight": return {"ok":True,"preflight":self.preflight(query.get("url",[""])[0])}
        if path == "/api/creator-distillation/tasks": return {"ok":True,"tasks":self.repository.list_tasks(org_id)}
        if path == "/api/creator-distillation/creators": return {"ok":True,"creators":self.repository.list_creators(org_id,query.get("q",[""])[0])}
        if path == "/api/creator-distillation/methodologies": return {"ok":True,"items":self.repository.methodologies()}
        if path == "/api/creator-distillation/health": return {"ok":True,"platforms":self.platform_health()}
        prefix="/api/creator-distillation/tasks/"
        if path.startswith(prefix):
            item=self.repository.get_task(path[len(prefix):]);
            if not item: raise KeyError("蒸馏任务不存在")
            return {"ok":True,"task":item}
        prefix="/api/creator-distillation/creators/"
        if path.startswith(prefix): return {"ok":True,**self.repository.creator_detail(path[len(prefix):])}
        prefix="/api/creator-distillation/assets/"
        if path.startswith(prefix): return {"ok":True,**self.repository.asset_detail(path[len(prefix):])}
        return None

    def handle_post(self, path, payload, org_id="local"):
        if path == "/api/creator-distillation/tasks": return {"ok":True,"task":self.create_task(payload,org_id)}
        if path.endswith("/pause"):
            return {"ok":True,"task":self.repository.pause(path.split("/")[-2])}
        if path.endswith("/retry"):
            task=self.repository.retry(path.split("/")[-2])
            if self.enqueue: self.enqueue(task["id"])
            return {"ok":True,"task":task}
        return None


def api_error(exc):
    if isinstance(exc, AdapterError):
        return {"ok":False,"error":str(exc),"category":exc.category,"retryable":exc.retryable,"degraded":exc.degraded}
    return {"ok":False,"error":str(exc),"category":"validation","retryable":False}
