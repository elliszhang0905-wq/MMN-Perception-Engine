"""Evidence-locked cover reconstruction prompts with neutral three-review fusion."""

from __future__ import annotations

import hashlib
import json
from statistics import mean


SCHEMA_VERSION = "cover-prompt-v1"
PROMPT_VERSION = "cover-prompt-three-review-v1"
REVIEW_SLOTS = ("review_a", "review_b", "review_c")
TEXT_FIELDS = ("subject", "action", "scene", "composition", "lighting", "color", "material", "style", "aspectRatio")
LIST_FIELDS = ("ocrText", "layout", "negativePrompt", "limitations", "evidenceRefs")


def _text(value, limit=1600):
    return str(value or "").strip()[:limit]


def _list(value, limit=20):
    if isinstance(value, str):
        value = [value]
    result = []
    for row in value or []:
        text = _text(row, 300)
        if text and text not in result:
            result.append(text)
        if len(result) >= limit:
            break
    return result


def build_cover_evidence_packet(video_evidence, cover_observation=None):
    """Freeze cover-visible evidence; title/comments never substitute for visual evidence."""
    video_evidence = video_evidence if isinstance(video_evidence, dict) else {}
    cover_observation = cover_observation if isinstance(cover_observation, dict) else {}
    visual_rows = [
        *[row for row in video_evidence.get("keyframes") or [] if isinstance(row, dict)],
        *[row for row in video_evidence.get("visualSegments") or [] if isinstance(row, dict)],
    ]
    ocr_rows = [row for row in video_evidence.get("ocrSegments") or [] if isinstance(row, dict)]
    description = _text(cover_observation.get("visualDescription"))
    evidence_refs = _list([
        *[row.get("evidenceId") for row in visual_rows],
        *[row.get("evidenceId") for row in ocr_rows],
        *cover_observation.get("evidenceRefs", []),
    ])
    visual_facts = _list([
        description,
        *[row.get("text") for row in visual_rows],
    ])
    ocr_text = _list([
        *cover_observation.get("ocrText", []),
        *[row.get("text") for row in ocr_rows],
    ])
    status = "ready" if visual_facts and evidence_refs else "limited"
    packet = {
        "schemaVersion": SCHEMA_VERSION,
        "promptVersion": PROMPT_VERSION,
        "itemId": _text(video_evidence.get("itemId"), 160),
        "sourceUrl": _text(video_evidence.get("sourceUrl"), 2000),
        "videoEvidenceFingerprint": _text(video_evidence.get("evidenceFingerprint"), 128),
        "coverImageUrl": _text(cover_observation.get("imageUrl"), 2000),
        "visualFacts": visual_facts,
        "ocrText": ocr_text,
        "evidenceRefs": evidence_refs,
        "status": status,
        "limitations": [] if status == "ready" else ["缺少可核验的封面或视频画面证据，不能生成还原型图像提示词"],
    }
    packet["evidenceFingerprint"] = hashlib.sha256(
        json.dumps(packet, ensure_ascii=False, sort_keys=True).encode()
    ).hexdigest()
    return packet


def review_messages(packet):
    system = (
        "你是MMN图像提示词分析员。只能依据冻结证据描述可见元素，不得猜测品牌、人物、地点或画面文字。"
        "输出严格JSON，字段为subject/action/scene/composition/lighting/color/material/ocrText/layout/"
        "style/aspectRatio/negativePrompt/limitations/confidence/evidenceRefs/evidenceFingerprint。"
    )
    return [{"role": "system", "content": system}, {
        "role": "user",
        "content": json.dumps(packet, ensure_ascii=False, sort_keys=True),
    }]


def normalize_review(value, packet):
    if packet.get("status") != "ready":
        raise ValueError("封面视觉证据不足")
    if not isinstance(value, dict):
        raise ValueError("封面分析必须返回JSON对象")
    result = {field: _text(value.get(field)) for field in TEXT_FIELDS}
    result.update({field: _list(value.get(field)) for field in LIST_FIELDS})
    if not result["subject"] or not result["composition"] or not result["style"]:
        raise ValueError("封面分析缺少主体、构图或风格")
    allowed_refs = set(packet.get("evidenceRefs") or [])
    if not result["evidenceRefs"] or any(ref not in allowed_refs for ref in result["evidenceRefs"]):
        raise ValueError("封面分析引用了冻结证据之外的内容")
    try:
        result["confidence"] = max(0.0, min(float(value.get("confidence")), 1.0))
    except (TypeError, ValueError):
        raise ValueError("confidence必须为0至1") from None
    supplied_fp = _text(value.get("evidenceFingerprint"), 128)
    if supplied_fp and supplied_fp != packet["evidenceFingerprint"]:
        raise ValueError("封面分析证据指纹不一致")
    result["evidenceFingerprint"] = packet["evidenceFingerprint"]
    return result


def _majority(values):
    counts = {}
    for value in values:
        key = json.dumps(value, ensure_ascii=False, sort_keys=True)
        counts[key] = counts.get(key, 0) + 1
    winner = sorted(counts.items(), key=lambda row: (-row[1], row[0]))[0]
    return json.loads(winner[0]), winner[1]


def fuse_reviews(packet, outputs, errors=None):
    """Fuse independent reviews deterministically and expose neutral slots only."""
    errors = errors or {}
    if packet.get("status") != "ready":
        return {
            "status": "limited", "reason": packet["limitations"][0],
            "evidenceFingerprint": packet["evidenceFingerprint"], "finalPrompt": None,
            "runs": [], "limitations": packet["limitations"],
        }
    normalized, rejected = {}, dict(errors)
    for slot in REVIEW_SLOTS:
        try:
            if slot in outputs:
                normalized[slot] = normalize_review(outputs[slot], packet)
        except ValueError as exc:
            rejected[slot] = str(exc)
    runs = [{
        "slot": index + 1, "label": f"MMN独立分析 {index + 1}",
        "status": "completed" if slot in normalized else "failed",
    } for index, slot in enumerate(REVIEW_SLOTS)]
    if len(normalized) < 3:
        return {
            "status": "incomplete", "reason": "独立分析未全部完成",
            "evidenceFingerprint": packet["evidenceFingerprint"], "finalPrompt": None,
            "runs": runs, "limitations": ["需三路独立分析全部完成后才发布统一提示词"],
        }
    ordered = [normalized[slot] for slot in REVIEW_SLOTS]
    final, weak_fields = {}, []
    for field in (*TEXT_FIELDS, *LIST_FIELDS):
        final[field], votes = _majority([row[field] for row in ordered])
        if votes < 2:
            weak_fields.append(field)
    final["confidence"] = round(mean(row["confidence"] for row in ordered), 3)
    final["evidenceFingerprint"] = packet["evidenceFingerprint"]
    final["prompt"] = "，".join(final[field] for field in TEXT_FIELDS if final[field])
    status = "manual_required" if weak_fields else "verified"
    return {
        "status": status,
        "reason": "关键字段存在三方分歧，需人工确认" if weak_fields else "三路独立分析形成一致提示词",
        "evidenceFingerprint": packet["evidenceFingerprint"],
        "finalPrompt": final if status == "verified" else None,
        "candidatePrompt": final,
        "disagreements": weak_fields,
        "runs": runs,
        "limitations": _list([item for row in ordered for item in row["limitations"]]),
    }


def init_schema(conn):
    conn.execute("""
        create table if not exists douyin_cover_prompt_runs (
            id text primary key, job_id text not null, provider_key text not null,
            attempt_no integer not null, evidence_fingerprint text not null,
            status text not null, raw_json text, error text not null default '',
            started_at text not null, completed_at text not null,
            unique(job_id, provider_key, attempt_no)
        )
    """)
    conn.execute(
        "create index if not exists idx_cover_prompt_runs_job "
        "on douyin_cover_prompt_runs(job_id, provider_key, attempt_no desc)"
    )


def save_run(conn, *, job_id, provider, evidence_fingerprint, status, raw=None, error="", started_at="", completed_at=""):
    init_schema(conn)
    attempt = conn.execute(
        "select coalesce(max(attempt_no),0)+1 from douyin_cover_prompt_runs where job_id=? and provider_key=?",
        (job_id, provider),
    ).fetchone()[0]
    run_id = hashlib.sha256(f"{job_id}|{provider}|{attempt}".encode()).hexdigest()
    conn.execute(
        """insert into douyin_cover_prompt_runs
           (id,job_id,provider_key,attempt_no,evidence_fingerprint,status,raw_json,error,started_at,completed_at)
           values(?,?,?,?,?,?,?,?,?,?)""",
        (
            run_id, job_id, provider, attempt, evidence_fingerprint, status,
            json.dumps(raw, ensure_ascii=False) if raw is not None else None,
            _text(error, 500), _text(started_at, 80), _text(completed_at, 80),
        ),
    )
    conn.commit()
