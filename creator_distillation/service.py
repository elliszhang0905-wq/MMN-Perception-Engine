import os

from .adapters import AdapterError, DouyinAdapter, XiaohongshuAdapter, adapter_for_url
from .media_processing import process_representative_media
from .repository import CreatorRepository
from .opinion_judgment import build_opinion_judgment


STAGES = [
    ("resolve_identity", "账号身份解析", 5), ("collect", "平台数据采集", 20),
    ("normalize", "字段标准化与评分", 45), ("persist", "资产幂等入库", 75),
    ("review", "等待人工审核", 100),
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
        platform_ready = platform in {"douyin", "xiaohongshu"}
        return {"metadata": platform_ready, "identityReview": platform_ready, "scoring": platform_ready,
                "comments": platform_ready, "evidence": platform_ready, "dnaDraft": platform_ready,
                "opinionJudgment": platform_ready,
                "dna": False, "video": platform == "douyin",
                "transcript": platform_ready, "ocr": platform_ready, "shots": platform_ready,
                "visual": platform_ready,
                "imageNote": platform == "xiaohongshu", "degradationSupported": True,
                "productionDataStatus": "metadata_ready" if platform_ready else "not_implemented"}

    def create_task(self, payload, org_id="local"):
        url = str(payload.get("creatorUrl") or "").strip()
        expected_name = str(payload.get("expectedCreatorName") or "").strip()
        if not expected_name: raise ValueError("请填写主页显示的达人名称，用于拦截 TikHub 身份错配")
        preflight = self.preflight(url)
        range_value = str(payload.get("range") or "180")
        range_days = None if range_value == "all" else int(range_value)
        if range_days not in {90, 180, None}: raise ValueError("采集范围仅支持 90、180 或 all")
        sample_count = max(20, min(100, int(payload.get("sampleCount") or 50)))
        capabilities = {**preflight["capabilities"], "expectedCreatorName": expected_name,
                        "identityConfirmationRequired": True,
                        "requestAttemptBudget": max(
                            1, min(30, int(os.getenv("MMN_CREATOR_REQUEST_ATTEMPT_BUDGET","30")))
                        )}
        active=self.repository.find_active_task(
            org_id,url,preflight["platform"],range_days,sample_count,expected_name
        )
        if active:
            return {**active,"reused":True}
        task = self.repository.create_task(org_id,url,preflight["platform"],range_days,sample_count,capabilities)
        if self.enqueue:
            try: self.enqueue(task["id"])
            except Exception as exc:
                self.repository.update_task(task["id"],org_id=org_id,status="failed",stage="queue",
                                            error_category="queue_unavailable",error_message=str(exc))
        else:
            self.repository.update_task(task["id"],org_id=org_id,status="queued",stage="awaiting_worker",progress=0,
                                        degraded_reason="Celery worker 未连接；任务已安全排队")
        return self.repository.get_task(task["id"],org_id)

    def platform_health(self):
        worker_mode = os.getenv("MMN_CREATOR_WORKER_MODE", "celery" if os.getenv("REDIS_URL") else "local")
        xiaohongshu_health = XiaohongshuAdapter().health()
        return {"douyin": DouyinAdapter().health(), "xiaohongshu": xiaohongshu_health,
                "queue": {"configured": worker_mode == "local" or bool(os.getenv("REDIS_URL")),
                          "mode": worker_mode},
                "database": {"target": "postgresql+pgvector", "localFallback": str(self.repository.path)}}

    def generate_opinion_judgment(self, creator_id, org_id="local"):
        inputs = self.repository.creator_opinion_inputs(creator_id, org_id)
        judgment = build_opinion_judgment(inputs["comments"], inputs["assetCount"])
        return self.repository.save_opinion_judgment(creator_id, judgment, org_id)

    def reprocess_asset_media(self, asset_id, org_id="local"):
        context=self.repository.asset_processing_context(asset_id,org_id)
        stored_media=(context.get("analysis") or {}).get("media") or {}
        candidate={"source_id":context["source_id"],"asset_type":context.get("asset_type"),
                   "title":context.get("title"),"media":stored_media}
        evidence=[]; errors=[]
        try:
            if any(stored_media.get(key) for key in ("videoUrl","audioUrl","imageUrls","subtitleUrls")):
                evidence,_,errors=process_representative_media([candidate],max_assets=1)
            if not evidence or errors:
                creator_url=context.get("creator_url")
                if not creator_url:
                    raise ValueError("该作品缺少原达人主页地址，请重新发起达人蒸馏后再试")
                adapter=DouyinAdapter() if context["platform"]=="douyin" else XiaohongshuAdapter()
                adapter.expected_creator_name=str(context.get("creator_display_name") or "").strip()
                _,assets,exchanges=adapter.collect_creator(
                    creator_url,max(20,min(100,int(context.get("sample_count") or 100)))
                )
                for payload,meta in exchanges:
                    self.repository.archive_raw_response(
                        context["distillation_task_id"],context["platform"],meta["endpoint"],
                        adapter.version,meta["status"],payload,
                    )
                refreshed=next((item for item in assets if str(item.get("source_id"))==str(context["source_id"])),None)
                if not refreshed:
                    raise ValueError("平台最新返回的作品中未找到该条内容，请重新发起达人蒸馏刷新作品列表")
                refreshed_evidence,_,refreshed_errors=process_representative_media([refreshed],max_assets=1)
                merged={str(item.get("comment_id") or index):item for index,item in enumerate(evidence)}
                merged.update({str(item.get("comment_id") or f"refresh-{index}"):item
                               for index,item in enumerate(refreshed_evidence)})
                evidence=list(merged.values());errors=refreshed_errors;candidate=refreshed
        except Exception as exc:
            message=f"媒体证据获取失败：{str(exc)[:420]}"
            detail=self.repository.save_asset_media_result(
                asset_id,org_id,[],{},"failed",message,media=candidate.get("media")
            )
            return {"status":"failed","message":message,**detail}

        types={str(item.get("evidence_type") or "") for item in evidence}
        capabilities={"transcript":"transcript" in types,"ocr":"ocr" in types,"shots":"shot" in types,
                      "visual":bool(types.intersection({"visual_summary","visual_structure","shot"}))}
        missing=[label for key,label in (("transcript","转写"),("ocr","OCR"),("visual","视觉"),("shots","镜头"))
                 if not capabilities[key]]
        status="available" if evidence and not missing else ("partial" if evidence else "not_returned")
        if evidence:
            message=f"已取得 {len(evidence)} 条媒体证据"+(f"；未取得：{'、'.join(missing)}" if missing else "")
        else:
            message="平台未返回可处理的媒体，或本次分析没有生成有效证据"
        if errors:
            message=f"{message}；{' | '.join(errors[:2])}"
        detail=self.repository.save_asset_media_result(
            asset_id,org_id,evidence,capabilities,status,message,media=candidate.get("media")
        )
        if evidence:
            self.repository.refresh_creator_content_profile(detail["asset"]["creator_id"], org_id)
        return {"status":status,"message":message,**detail}

    def handle_get(self, path, query, org_id="local"):
        if path == "/api/creator-distillation/preflight": return {"ok":True,"preflight":self.preflight(query.get("url",[""])[0])}
        if path == "/api/creator-distillation/tasks": return {"ok":True,"tasks":self.repository.list_tasks(org_id)}
        if path == "/api/creator-distillation/creators": return {"ok":True,"creators":self.repository.list_creators(org_id,query.get("q",[""])[0])}
        if path == "/api/creator-distillation/methodologies": return {"ok":True,"items":self.repository.methodologies(org_id)}
        if path == "/api/creator-distillation/health": return {"ok":True,"platforms":self.platform_health()}
        prefix="/api/creator-distillation/tasks/"
        if path.startswith(prefix):
            item=self.repository.get_task(path[len(prefix):],org_id);
            if not item: raise KeyError("蒸馏任务不存在")
            return {"ok":True,"task":item}
        prefix="/api/creator-distillation/creators/"
        if path.startswith(prefix): return {"ok":True,**self.repository.creator_detail(path[len(prefix):],org_id)}
        prefix="/api/creator-distillation/assets/"
        if path.startswith(prefix): return {"ok":True,**self.repository.asset_detail(path[len(prefix):],org_id)}
        return None

    def handle_post(self, path, payload, org_id="local"):
        if path == "/api/creator-distillation/tasks": return {"ok":True,"task":self.create_task(payload,org_id)}
        prefix="/api/creator-distillation/assets/"
        suffix="/media"
        if path.startswith(prefix) and path.endswith(suffix):
            asset_id=path[len(prefix):-len(suffix)].strip("/")
            return {"ok":True,**self.reprocess_asset_media(asset_id,org_id)}
        prefix="/api/creator-distillation/creators/"
        suffix="/opinion-judgment"
        if path.startswith(prefix) and path.endswith(suffix):
            creator_id=path[len(prefix):-len(suffix)].strip("/")
            return {"ok":True,"opinionJudgment":self.generate_opinion_judgment(creator_id,org_id)}
        if path.endswith("/pause"):
            return {"ok":True,"task":self.repository.pause(path.split("/")[-2],org_id)}
        if path.endswith("/retry"):
            task=self.repository.retry(path.split("/")[-2],org_id)
            if self.enqueue: self.enqueue(task["id"])
            return {"ok":True,"task":task}
        return None


def api_error(exc):
    if isinstance(exc, AdapterError):
        return {"ok":False,"error":str(exc),"category":exc.category,"retryable":exc.retryable,"degraded":exc.degraded}
    return {"ok":False,"error":str(exc),"category":"validation","retryable":False}
