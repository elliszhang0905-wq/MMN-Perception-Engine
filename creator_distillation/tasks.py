import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from .repository import CreatorRepository
from .adapters import DouyinAdapter, XiaohongshuAdapter, AdapterError, validate_creator_identity
from .media_processing import process_representative_media
from .content_validation import build_creator_content_validation
from .opinion_judgment import build_opinion_judgment
from .scoring import score_assets, select_diverse_samples

try:
    from celery import Celery
except ImportError:  # local UI can run without production worker dependencies
    Celery = None

broker = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("mmn_creator_distillation", broker=broker, backend=broker) if Celery else None
if celery_app:
    celery_app.conf.update(task_track_started=True, task_acks_late=True, worker_prefetch_multiplier=1,
                           task_routes={"creator_distillation.tasks.run_distillation":"creator-distillation"})

_local_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mmn-creator-worker")
_local_futures = set()


def enqueue_distillation(task_id):
    if not celery_app: raise RuntimeError("未安装 Celery")
    run_distillation.delay(task_id)


def enqueue_local_distillation(task_id):
    """Run creator jobs asynchronously inside the local MMN process."""
    future = _local_executor.submit(_run, task_id)
    _local_futures.add(future)
    future.add_done_callback(_local_futures.discard)
    return future


def _preliminary_profile(creator, assets, evidence):
    """Build content-DNA inputs from media only; comments belong to opinion analysis."""
    topics = Counter(str(item.get("primary_tag") or "未分类") for item in assets)
    representative = [
        {"sourceId": item.get("source_id"), "title": item.get("title"),
         "performanceScore": item.get("performance_score"), "selectionReasons": item.get("selection_reasons") or []}
        for item in assets[:5]
    ]
    media_evidence = [item for item in evidence if item.get("evidence_type") != "comment"]
    return {
        "summary": f"已采集 {len(assets)} 条作品和 {len(media_evidence)} 条内容证据，等待提炼赛道、选题、叙事结构与表达方法。",
        "status": "needs_review", "generationMode": "deterministic_content_evidence_index",
        "creatorName": creator.get("display_name"),
        "contentThemes": [{"name": name, "assetCount": count} for name, count in topics.most_common(8)],
        "representativeContent": representative,
        "mediaEvidence": [{"sourceId": item.get("source_id"), "type": item.get("evidence_type"),
                           "quote": item.get("quote_text")} for item in media_evidence[:30]],
        "limitations": ["媒体处理仅覆盖代表作，不代表账号全部内容", "评论不进入博主 DNA，仅用于车型舆情辅助验证",
                        "不得将此草稿当作已确认达人 DNA"],
    }


def _run(task_id):
    repo=CreatorRepository(); task=repo.get_task(task_id)
    if not task: raise ValueError("任务不存在")
    repo.update_task(task_id,status="running",stage="resolve_identity",progress=5)
    adapter=DouyinAdapter() if task["platform"]=="douyin" else XiaohongshuAdapter()
    try:
        expected_name=str((task.get("capabilities") or {}).get("expectedCreatorName") or "").strip()
        if not expected_name:
            raise AdapterError("任务缺少预期达人名称，已阻止调用 TikHub 和写入达人库",
                               "identity_confirmation_required",False,False)
        adapter.expected_creator_name=expected_name
        creator,assets,exchanges=adapter.collect_creator(task["creator_url"],task["sample_count"])
        validate_creator_identity(creator, expected_name=expected_name)
        for payload,meta in exchanges:
            repo.archive_raw_response(task_id,task["platform"],meta["endpoint"],adapter.version,meta["status"],payload)
        repo.update_task(task_id,status="running",stage="normalize",progress=45)
        if not assets:
            raise AdapterError("TikHub 未返回可用作品", "empty_collection", False, True)
        scored=score_assets(assets,followers=creator.get("followers"))
        selected=select_diverse_samples(scored,task["sample_count"])
        comment_evidence=[]; comment_error=""
        repo.update_task(task_id,status="running",stage="comments",progress=55)
        try:
            comment_evidence,comment_exchanges=adapter.collect_comments(
                selected,
                max_assets=max(0,min(10,int(os.getenv("MMN_CREATOR_COMMENT_ASSET_LIMIT","3")))),
                comments_per_asset=max(1,min(50,int(os.getenv("MMN_CREATOR_COMMENTS_PER_ASSET","20")))),
            )
            for payload,meta in comment_exchanges:
                repo.archive_raw_response(task_id,task["platform"],meta["endpoint"],adapter.version,meta["status"],payload)
        except AdapterError as exc:
            comment_error=str(exc)
        repo.update_task(task_id,status="running",stage="media",progress=65)
        try:
            media_evidence,media_stats,media_errors=process_representative_media(
                selected, max_assets=max(0,min(5,int(os.getenv("MMN_CREATOR_MEDIA_ASSET_LIMIT","3"))))
            )
        except Exception as exc:
            media_evidence=[]
            media_stats={"processedAssetCount":0,"transcriptAssetCount":0,"visualAssetCount":0,
                         "crossVisualAssetCount":0,"ocrAssetCount":0,"shotAssetCount":0}
            media_errors=[f"媒体处理器异常: {type(exc).__name__}"]
        commented_sources={str(item.get("source_id")) for item in comment_evidence}
        for item in selected:
            item.setdefault("capabilities", {"metadata":True,"transcript":False,"ocr":False,
                                              "visual":False,"shots":False})
            item["capabilities"]["comments"]=str(item.get("source_id")) in commented_sources
        all_evidence=comment_evidence+media_evidence
        repo.update_task(task_id,status="running",stage="persist",progress=85)
        result=repo.save_collection(task,creator,selected,all_evidence)
        draft=_preliminary_profile(creator,selected,all_evidence)
        content_validation_status="manual_required"
        try:
            repo.update_task(task_id,status="running",stage="content_validation",progress=89)
            content_inputs=repo.creator_content_inputs(result["creatorId"])
            content_validation=build_creator_content_validation(
                content_inputs["creator"],content_inputs["assets"],content_inputs["evidence"])
            content_validation_status=content_validation["status"]
            draft["contentValidation"]=content_validation
            draft["validatedClaims"]=content_validation.get("validatedClaims") or []
            draft["validationMode"]="qwen_deepseek_common_evidence_gate"
            if content_validation_status != "aligned":
                draft["limitations"].append("Qwen 与 DeepSeek 未形成共同证据结论，禁止发布达人 DNA")
        except Exception as exc:
            draft["contentValidation"]={"status":"manual_required","validatedClaims":[],
                                        "reasons":[f"内容交叉质检失败: {type(exc).__name__}"]}
            draft["limitations"].append("内容交叉质检未完成，禁止发布达人 DNA")
        repo.save_profile_draft(result["creatorId"],draft)
        opinion_status="not_available"
        try:
            repo.update_task(task_id,status="running",stage="opinion",progress=92)
            opinion_inputs=repo.creator_opinion_inputs(result["creatorId"])
            opinion=build_opinion_judgment(opinion_inputs["comments"],opinion_inputs["assetCount"])
            repo.save_opinion_judgment(result["creatorId"],opinion)
            opinion_status=opinion["status"]
        except Exception as exc:
            opinion_status="manual_required"
            comment_error=(comment_error+" | " if comment_error else "")+f"舆情判断降级: {type(exc).__name__}"
        missing=sum(1 for item in selected if (item.get("provenance") or {}).get("missingMetrics"))
        notes=[]
        if missing: notes.append(f"{missing} 条作品存在缺失指标；已保留 null 并采用相对互动排序")
        if comment_error: notes.append(f"评论证据降级：{comment_error}")
        if media_errors: notes.append(f"媒体处理部分降级：{' | '.join(media_errors[:3])}")
        note="；".join(notes)
        repo.update_task(task_id,status="completed",stage="review",progress=100,
                         degraded_reason=note,
                         capabilities_json={"metadata":True,"scoring":True,"identityReview":True,
                                            "comments":bool(comment_evidence),
                                            "transcript":media_stats["transcriptAssetCount"]>0,
                                            "ocr":media_stats["ocrAssetCount"]>0,
                                            "visual":media_stats["visualAssetCount"]>0,
                                            "shots":media_stats["shotAssetCount"]>0,
                                            "dnaDraft":True,"dna":False,
                                            "creatorId":result["creatorId"],"assetCount":len(result["assetIds"]),
                                            "commentEvidenceCount":len(comment_evidence),
                                            "mediaEvidenceCount":len(media_evidence),
                                            "opinionJudgmentStatus":opinion_status,
                                            "contentValidationStatus":content_validation_status,
                                            **media_stats})
        return repo.get_task(task_id)
    except AdapterError as exc:
        repo.update_task(task_id,status="degraded" if exc.degraded else "failed",stage="collect",progress=8,
                         error_category=exc.category,error_message=str(exc),degraded_reason=str(exc) if exc.degraded else "")
        return repo.get_task(task_id)


if celery_app:
    run_distillation=celery_app.task(autoretry_for=(TimeoutError,),retry_backoff=True,retry_jitter=True,max_retries=3)(_run)
else:
    run_distillation=_run
