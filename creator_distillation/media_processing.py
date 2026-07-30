import ipaddress
import base64
import json
import os
import re
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class MediaProcessingError(RuntimeError):
    pass


_TRUSTED_MEDIA_HOST_SUFFIXES = (
    "douyinstatic.com", "douyinpic.com", "douyinvod.com", "bytecdntp.com",
    "rednotecdn.com", "xhscdn.com", "tikhub.io",
    "dashscope-result-bj.oss-cn-beijing.aliyuncs.com",
)
_LOCAL_PROXY_SYNTHETIC_NETWORK = ipaddress.ip_network("198.18.0.0/15")


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


def _safe_public_url(url):
    parsed = urlparse(str(url or ""))
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise MediaProcessingError("媒体 URL 非公开 HTTP(S) 地址")
    try:
        addresses = {item[4][0] for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443)}
    except OSError as exc:
        raise MediaProcessingError(f"媒体域名无法解析: {parsed.hostname}") from exc
    trusted_platform_cdn = any(parsed.hostname == suffix or parsed.hostname.endswith("." + suffix)
                               for suffix in _TRUSTED_MEDIA_HOST_SUFFIXES)
    for address in addresses:
        ip = ipaddress.ip_address(address)
        # Some local proxy/VPN resolvers map approved public CDN hosts into RFC 2544's
        # benchmark range. The provider still receives the original hostname, so only
        # allow that synthetic range for known platform CDN suffixes.
        if trusted_platform_cdn and ip in _LOCAL_PROXY_SYNTHETIC_NETWORK:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise MediaProcessingError("拒绝访问非公网媒体地址")
    return parsed.geturl()


def _fetch_text(url, max_bytes=4 * 1024 * 1024):
    safe_url = _safe_public_url(url)
    request = Request(safe_url, headers={"User-Agent": "MMN-Perception-Engine/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read(max_bytes + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise MediaProcessingError(f"字幕读取失败: {type(exc).__name__}") from exc
    if len(raw) > max_bytes:
        raise MediaProcessingError("字幕文件超过 4MB 安全上限")
    return raw.decode("utf-8", errors="replace")


def _timestamp_ms(value):
    match = re.match(r"(?:(\d+):)?(\d{2}):(\d{2})[,.](\d{3})", str(value).strip())
    if not match:
        return None
    hours, minutes, seconds, millis = match.groups()
    return ((int(hours or 0) * 60 + int(minutes)) * 60 + int(seconds)) * 1000 + int(millis)


def parse_srt(text, source_id):
    blocks = re.split(r"\r?\n\s*\r?\n", str(text or "").strip())
    evidence = []
    for index, block in enumerate(blocks):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing_index = next((i for i, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        start, end = (part.strip() for part in lines[timing_index].split("-->", 1))
        quote = " ".join(lines[timing_index + 1:]).strip()
        if not quote:
            continue
        evidence.append({
            "source_id": source_id, "comment_id": f"media:transcript:{index}",
            "evidence_type": "transcript", "start_ms": _timestamp_ms(start), "end_ms": _timestamp_ms(end),
            "quote_text": quote, "confidence": .98,
            "provenance": {"processor": "platform_subtitle", "availability": "available",
                           "fetchTime": datetime.now(timezone.utc).isoformat()},
        })
    return evidence


def _model_content(payload):
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise MediaProcessingError("多模态模型返回缺少内容") from exc
    if isinstance(content, list):
        content = "\n".join(str(item.get("text") or "") for item in content if isinstance(item, dict))
    return str(content or "").strip()


def _chat_completion(model, messages, timeout=180, extra=None, api_key_env="DASHSCOPE_API_KEY",
                     base_url_env="QWEN_BASE_URL"):
    api_key = _config_value(api_key_env) or _config_value("DASHSCOPE_API_KEY")
    if not api_key:
        raise MediaProcessingError(f"未配置 {api_key_env}")
    base_url = _config_value(base_url_env,
                             "https://dashscope.aliyuncs.com/compatible-mode/v1").rstrip("/")
    body = {"model": model, "messages": messages, "temperature": 0.1, **(extra or {})}
    request = Request(
        base_url + "/chat/completions", data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}, method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        try:
            provider_message = json.loads(detail).get("error", {}).get("message")
        except (json.JSONDecodeError, AttributeError):
            provider_message = None
        concise = str(provider_message or f"HTTP {exc.code}").split(":", 1)[-1].strip()[:180]
        raise MediaProcessingError(f"多模态模型 HTTP {exc.code}: {concise}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise MediaProcessingError(f"多模态模型调用失败: {type(exc).__name__}") from exc


def _json_object(text, *, list_field=""):
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", str(text or "").strip(), flags=re.I | re.S)
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError:
        value = None
        decoder = json.JSONDecoder()
        for match in re.finditer(r"\{", cleaned):
            try:
                candidate, _end = decoder.raw_decode(cleaned[match.start():])
            except json.JSONDecodeError:
                continue
            if isinstance(candidate, dict):
                value = candidate
                break
        if value is None:
            raise MediaProcessingError("多模态模型未返回 JSON 对象")
    if isinstance(value, list) and list_field:
        return {list_field: value}
    if not isinstance(value, dict):
        raise MediaProcessingError("多模态模型结果不是 JSON 对象")
    return value


def _request_json(request, timeout, label):
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise MediaProcessingError(f"{label} HTTP {exc.code}: {detail[:180]}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise MediaProcessingError(f"{label}失败: {type(exc).__name__}") from exc


def _filetrans_text(value):
    """Extract only provider transcript text fields from a completed result document."""
    texts = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"text", "transcript", "transcription"} and isinstance(item, str) and item.strip():
                texts.append(item.strip())
            elif isinstance(item, (dict, list)):
                texts.extend(_filetrans_text(item))
    elif isinstance(value, list):
        for item in value:
            texts.extend(_filetrans_text(item))
    return "\n".join(dict.fromkeys(texts))


def transcribe_long_media(audio_url, duration_ms=None):
    api_key = (_config_value("MMN_CREATOR_ASR_FILETRANS_API_KEY")
               or _config_value("DASHSCOPE_API_KEY"))
    if not api_key:
        raise MediaProcessingError("未配置 MMN_CREATOR_ASR_FILETRANS_API_KEY")
    base_url = _config_value(
        "MMN_CREATOR_ASR_FILETRANS_BASE_URL", "https://dashscope.aliyuncs.com/api/v1").rstrip("/")
    model = _config_value("MMN_CREATOR_ASR_FILETRANS_MODEL", "qwen3-asr-flash-filetrans")
    headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json",
               "X-DashScope-Async": "enable"}
    body = {"model": model, "input": {"file_url": _safe_public_url(audio_url)},
            "parameters": {"language": "zh", "enable_itn": True, "enable_words": True}}
    request = Request(base_url + "/services/audio/asr/transcription",
                      data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
                      headers=headers, method="POST")
    submitted = _request_json(request, 60, "长音频转写任务提交")
    task_id = str((submitted.get("output") or {}).get("task_id") or "")
    if not task_id:
        raise MediaProcessingError("长音频转写未返回 task_id")
    completed = None
    for _ in range(150):
        status_request = Request(base_url + "/tasks/" + task_id, headers=headers, method="GET")
        status_payload = _request_json(status_request, 30, "长音频转写状态查询")
        status = str((status_payload.get("output") or {}).get("task_status") or "").upper()
        if status == "SUCCEEDED":
            completed = status_payload
            break
        if status in {"FAILED", "CANCELED", "UNKNOWN"}:
            raise MediaProcessingError(f"长音频转写任务终止: {status}")
        time.sleep(2)
    if not completed:
        raise MediaProcessingError("长音频转写等待超过 5 分钟")
    result = (completed.get("output") or {}).get("result") or {}
    result_url = result.get("transcription_url")
    if result_url:
        result_request = Request(_safe_public_url(result_url), headers={"User-Agent": "MMN-Perception-Engine/1.0"})
        result = _request_json(result_request, 60, "长音频转写结果下载")
    text = _filetrans_text(result)
    if not text:
        raise MediaProcessingError("长音频转写结果没有可用文本")
    return text, model


def transcribe_media(asset):
    media = asset.get("media") or {}
    for subtitle_url in media.get("subtitleUrls") or []:
        try:
            evidence = parse_srt(_fetch_text(subtitle_url), str(asset["source_id"]))
            if evidence:
                return evidence, "platform_subtitle"
        except MediaProcessingError:
            continue
    audio_url = media.get("audioUrl") or media.get("videoUrl")
    duration_ms = media.get("durationMs")
    if duration_ms in {None, ""}:
        duration_ms = asset.get("durationMs") or asset.get("duration_ms")
    if not audio_url:
        return [], "unavailable"
    if duration_ms and int(duration_ms) > 5 * 60 * 1000:
        text, model = transcribe_long_media(audio_url, duration_ms)
        return [{
            "source_id": str(asset["source_id"]), "comment_id": "media:transcript:filetrans",
            "evidence_type": "transcript", "start_ms": 0, "end_ms": duration_ms,
            "quote_text": text, "confidence": .9,
            "provenance": {"processor": "qwen3_asr_filetrans", "model": model,
                           "availability": "available",
                           "fetchTime": datetime.now(timezone.utc).isoformat()},
        }], "qwen3_asr_filetrans"
    safe_url = _safe_public_url(audio_url)
    payload = _chat_completion(
        _config_value("MMN_CREATOR_ASR_MODEL", "qwen3-asr-flash"),
        [{"role": "user", "content": [{"type": "input_audio", "input_audio": safe_url}]}],
        timeout=180, extra={"asr_options": {"language": "zh"}},
        api_key_env="MMN_CREATOR_ASR_API_KEY",
    )
    text = _model_content(payload)
    if not text:
        return [], "asr_empty"
    return [{
        "source_id": str(asset["source_id"]), "comment_id": "media:transcript:asr",
        "evidence_type": "transcript", "start_ms": 0, "end_ms": duration_ms,
        "quote_text": text, "confidence": .9,
        "provenance": {"processor": "qwen3_asr", "model": payload.get("model"),
                       "availability": "available", "fetchTime": datetime.now(timezone.utc).isoformat()},
    }], "qwen3_asr"


def _visual_content(asset):
    media = asset.get("media") or {}
    content = []
    local_paths = list(media.get("localImagePaths") or [])[:6]
    timestamps = list(media.get("localImageTimestampsMs") or [])[:6]
    for image_path in local_paths:
        path = Path(str(image_path or "")).expanduser().resolve()
        if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
            raise MediaProcessingError("浏览器关键帧不可用")
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        content.append({"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + encoded}})
    video_url = media.get("videoUrl")
    if content:
        pass
    elif video_url:
        content.append({"type": "video_url", "video_url": {"url": _safe_public_url(video_url), "fps": .2}})
    else:
        for image_url in (media.get("imageUrls") or [])[:6]:
            content.append({"type": "image_url", "image_url": {"url": _safe_public_url(image_url)}})
    if not content:
        return []
    content.append({"type": "text", "text": (
        "你是MMN汽车内容证据分析器。只依据媒体画面输出JSON，不推测看不到的信息。"
        "字段：visual_summary字符串；ocr_text字符串数组；shots数组，每项含time_ms(未知为null)、description；"
        "content_structure字符串数组；product_entities字符串数组；limitations字符串数组。"
        f"输入图片依次对应时间点：{', '.join(str(value) + 'ms' for value in timestamps)}。"
        "shots.time_ms必须使用这些时间点之一；不要模仿创作者，不要生成营销文案。"
    )})
    return content


def _visual_evidence(asset, analysis, provider, model):
    source_id = str(asset["source_id"])
    timestamp = datetime.now(timezone.utc).isoformat()
    provenance = {"processor": "multimodal_visual", "provider": provider,
                  "model": model,
                  "availability": "available", "fetchTime": timestamp}
    evidence = []
    summary = str(analysis.get("visual_summary") or "").strip()
    if summary:
        evidence.append({"source_id": source_id, "comment_id": f"media:{provider}:visual:summary",
                         "evidence_type": "visual_summary", "quote_text": summary,
                         "confidence": .85, "provenance": provenance})
    for index, text in enumerate(analysis.get("ocr_text") or []):
        quote = str(text or "").strip()
        if quote:
            evidence.append({"source_id": source_id, "comment_id": f"media:{provider}:ocr:{index}",
                             "evidence_type": "ocr", "quote_text": quote,
                             "confidence": .82, "provenance": provenance})
    for index, shot in enumerate(analysis.get("shots") or []):
        if not isinstance(shot, dict) or not str(shot.get("description") or "").strip():
            continue
        time_ms = shot.get("time_ms") if isinstance(shot.get("time_ms"), int) else None
        evidence.append({"source_id": source_id, "comment_id": f"media:{provider}:shot:{index}",
                         "evidence_type": "shot", "start_ms": time_ms, "end_ms": time_ms,
                         "quote_text": str(shot["description"]).strip(), "confidence": .8,
                         "provenance": provenance})
    structure = [str(item).strip() for item in analysis.get("content_structure") or [] if str(item).strip()]
    entities = [str(item).strip() for item in analysis.get("product_entities") or [] if str(item).strip()]
    if structure or entities:
        evidence.append({"source_id": source_id, "comment_id": f"media:{provider}:visual:structure",
                         "evidence_type": "visual_structure",
                         "quote_text": json.dumps({"structure": structure, "productEntities": entities},
                                                  ensure_ascii=False),
                         "confidence": .8, "provenance": provenance})
    return evidence


def _run_visual_provider(asset, provider, model, api_key_env, base_url_env="QWEN_BASE_URL"):
    content = _visual_content(asset)
    if not content:
        return [], "unavailable"
    payload = _chat_completion(model, [{"role": "user", "content": content}], timeout=300,
                               api_key_env=api_key_env, base_url_env=base_url_env)
    analysis = _json_object(_model_content(payload))
    return _visual_evidence(asset, analysis, provider, payload.get("model") or model), provider


def analyze_visual_media(asset):
    """Run two independent visual observers; Qwen Flash is a Qwen fallback only."""
    evidence, modes, errors = [], [], []
    qwen_model = _config_value("MMN_CREATOR_VISION_MODEL", "qwen3.7-plus")
    try:
        rows, mode = _run_visual_provider(
            asset, "qwen", qwen_model, "MMN_CREATOR_VISION_API_KEY")
        evidence.extend(rows); modes.append(mode)
    except MediaProcessingError as exc:
        fallback = _config_value("MMN_CREATOR_VISION_FAST_MODEL", "qwen3.6-flash")
        try:
            rows, mode = _run_visual_provider(
                asset, "qwen", fallback, "MMN_CREATOR_VISION_FAST_API_KEY")
            evidence.extend(rows); modes.append(mode + "_fast_fallback")
        except MediaProcessingError as fallback_exc:
            errors.append(f"Qwen视觉失败: {exc}; fallback: {fallback_exc}")
    kimi_model = _config_value("MMN_CREATOR_VISION_REVIEW_MODEL", "kimi/kimi-k2.6")
    try:
        rows, mode = _run_visual_provider(
            asset, "kimi", kimi_model, "MMN_CREATOR_VISION_REVIEW_API_KEY", "KIMI_BASE_URL")
        evidence.extend(rows); modes.append(mode)
    except MediaProcessingError as exc:
        errors.append(f"Kimi视觉复核失败: {exc}")
    if not evidence and errors:
        raise MediaProcessingError(" | ".join(errors))
    return evidence, "+".join(modes) if modes else "unavailable"


def analyze_ocr_media(asset):
    """Use the OCR specialist on still images/covers; video reasoning stays separate."""
    media = asset.get("media") or {}
    local_paths = list(media.get("localImagePaths") or [])[:6]
    image_urls = list(media.get("imageUrls") or [])[:6]
    if not local_paths and not image_urls:
        return [], "unavailable"
    content = []
    for image_path in local_paths:
        path = Path(str(image_path or "")).expanduser().resolve()
        if not path.is_file() or path.stat().st_size > 8 * 1024 * 1024:
            raise MediaProcessingError("浏览器关键帧不可用")
        content.append({"type": "image_url", "image_url": {
            "url": "data:image/jpeg;base64," + base64.b64encode(path.read_bytes()).decode("ascii")}})
    content.extend({"type": "image_url", "image_url": {"url": _safe_public_url(url)}}
                   for url in image_urls[:max(0, 6 - len(content))])
    content.append({"type": "text", "text": (
        "逐张识别画面中真实可见文字。输出JSON：{\"texts\":[{\"imageIndex\":0,"
        "\"text\":\"...\"}]}。看不清则跳过，不推测品牌、车型或配置。"
    )})
    model = _config_value("MMN_CREATOR_OCR_MODEL", "qwen-vl-ocr")
    payload = _chat_completion(
        model, [{"role": "user", "content": content}], timeout=180,
        api_key_env="MMN_CREATOR_OCR_API_KEY")
    parsed = _json_object(_model_content(payload), list_field="texts")
    provenance = {"processor": "specialist_ocr", "provider": "qwen_ocr",
                  "model": payload.get("model") or model, "availability": "available",
                  "fetchTime": datetime.now(timezone.utc).isoformat()}
    evidence = []
    for index, row in enumerate(parsed.get("texts") or []):
        if isinstance(row, dict):
            quote = str(row.get("text") or "").strip()
            image_index = row.get("imageIndex")
        else:
            quote, image_index = str(row or "").strip(), None
        if quote:
            evidence.append({"source_id": str(asset["source_id"]),
                             "comment_id": f"media:qwen_ocr:{index}", "evidence_type": "ocr",
                             "quote_text": quote, "confidence": .9,
                             "provenance": {**provenance, "imageIndex": image_index}})
    return evidence, "qwen_vl_ocr"


def process_representative_media(assets, max_assets=3):
    all_evidence, errors = [], []
    processed = transcript_assets = visual_assets = cross_visual_assets = ocr_assets = shot_assets = 0
    for asset in list(assets)[:max(0, max_assets)]:
        asset_evidence, transcript, visual, ocr = [], [], [], []
        transcript_mode = visual_mode = ocr_mode = "unavailable"
        try:
            transcript, transcript_mode = transcribe_media(asset)
            asset_evidence.extend(transcript)
            if transcript:
                transcript_assets += 1
        except MediaProcessingError as exc:
            transcript_mode = "failed"
            errors.append(f"{asset['source_id']} 转写: {exc}")
        try:
            visual, visual_mode = analyze_visual_media(asset)
            asset_evidence.extend(visual)
            if visual:
                visual_assets += 1
            if {str((item.get("provenance") or {}).get("provider")) for item in visual} >= {"qwen", "kimi"}:
                cross_visual_assets += 1
            if any(item.get("evidence_type") == "shot" for item in visual):
                shot_assets += 1
        except MediaProcessingError as exc:
            visual_mode = "failed"
            errors.append(f"{asset['source_id']} 视觉: {exc}")
        try:
            ocr, ocr_mode = analyze_ocr_media(asset)
            asset_evidence.extend(ocr)
        except MediaProcessingError as exc:
            ocr_mode = "failed"
            errors.append(f"{asset['source_id']} OCR: {exc}")
        if asset_evidence:
            processed += 1
        if any(item.get("evidence_type") == "ocr" for item in asset_evidence):
            ocr_assets += 1
        asset["capabilities"] = {
            "metadata": True, "comments": False, "transcript": bool(transcript),
            "ocr": any(item.get("evidence_type") == "ocr" for item in asset_evidence),
            "visual": any(item.get("evidence_type", "").startswith(("visual", "shot")) for item in asset_evidence),
            "shots": any(item.get("evidence_type") == "shot" for item in asset_evidence),
            "transcriptMode": transcript_mode, "visualMode": visual_mode, "ocrMode": ocr_mode,
            "crossVisual": {str((item.get("provenance") or {}).get("provider"))
                            for item in visual} >= {"qwen", "kimi"},
        }
        all_evidence.extend(asset_evidence)
    return all_evidence, {"processedAssetCount": processed, "transcriptAssetCount": transcript_assets,
                          "visualAssetCount": visual_assets, "crossVisualAssetCount": cross_visual_assets,
                          "ocrAssetCount": ocr_assets,
                          "shotAssetCount": shot_assets}, errors
