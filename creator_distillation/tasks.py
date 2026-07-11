import os
import subprocess

from .repository import CreatorRepository
from .adapters import DouyinAdapter, XiaohongshuAdapter, AdapterError

try:
    from celery import Celery
except ImportError:  # local UI can run without production worker dependencies
    Celery = None

broker = os.getenv("REDIS_URL", "redis://redis:6379/0")
celery_app = Celery("mmn_creator_distillation", broker=broker, backend=broker) if Celery else None
if celery_app:
    celery_app.conf.update(task_track_started=True, task_acks_late=True, worker_prefetch_multiplier=1,
                           task_routes={"creator_distillation.tasks.run_distillation":"creator-distillation"})


def enqueue_distillation(task_id):
    if not celery_app: raise RuntimeError("未安装 Celery")
    run_distillation.delay(task_id)


def _tool_available(command):
    try: return subprocess.run([command,"-version"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3).returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired): return False


def _run(task_id):
    repo=CreatorRepository(); task=repo.get_task(task_id)
    if not task: raise ValueError("任务不存在")
    repo.update_task(task_id,status="running",stage="collect",progress=5)
    adapter=DouyinAdapter() if task["platform"]=="douyin" else XiaohongshuAdapter()
    try:
        profile,meta=adapter.request("profile",{"url":task["creator_url"]})
        repo.archive_raw_response(task_id,task["platform"],meta["endpoint"],adapter.version,meta["status"],profile)
        posts,meta=adapter.request("posts",{"url":task["creator_url"],"range_days":task["range_days"] or "all"})
        repo.archive_raw_response(task_id,task["platform"],meta["endpoint"],adapter.version,meta["status"],posts)
    except AdapterError as exc:
        repo.update_task(task_id,status="degraded" if exc.degraded else "failed",stage="collect",progress=8,
                         error_category=exc.category,error_message=str(exc),degraded_reason=str(exc) if exc.degraded else "")
        return repo.get_task(task_id)
    # Platform collection and media processors are deliberately strict: missing tools
    # become visible degraded states, never fabricated transcript/shot evidence.
    required={"ffmpeg":_tool_available("ffmpeg")}
    if not required["ffmpeg"]:
        repo.update_task(task_id,status="degraded",stage="media",progress=18,
                         degraded_reason="FFmpeg 不可用；仅保留平台元数据、正文、图片/OCR与评论能力")
        return repo.get_task(task_id)
    repo.update_task(task_id,status="degraded",stage="collect",progress=8,
                     degraded_reason="平台适配已就绪；需真实 TikHub 响应完成生产数据验收")
    return repo.get_task(task_id)


if celery_app:
    run_distillation=celery_app.task(autoretry_for=(TimeoutError,),retry_backoff=True,retry_jitter=True,max_retries=3)(_run)
else:
    run_distillation=_run
