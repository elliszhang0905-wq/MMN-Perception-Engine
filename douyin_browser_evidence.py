"""Bounded browser-backed evidence extraction for one manually selected Douyin video."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from douyin_video_insights import canonical_douyin_video_url


class BrowserEvidenceError(RuntimeError):
    pass


def extract_browser_video_evidence(source_url, item_id, output_root, *,
                                   cdp_url="http://127.0.0.1:9225",
                                   node_binary="node", script_path=None, timeout=90,
                                   node_modules=None, browser_executable=None):
    item_id = str(item_id or "").strip()
    source_url = canonical_douyin_video_url(source_url, item_id)
    if not source_url:
        raise BrowserEvidenceError("原视频地址与当前榜单内容不匹配")
    root = Path(output_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    worker = Path(script_path or Path(__file__).resolve().parent / "scripts" / "douyin_video_browser_evidence.js")
    command = [str(node_binary), str(worker), str(cdp_url), source_url, item_id, str(root)]
    env = os.environ.copy()
    if node_modules:
        env["NODE_PATH"] = str(Path(node_modules).expanduser().resolve())
    if browser_executable:
        env["MMN_DOUYIN_BROWSER_EXECUTABLE"] = str(browser_executable)
    try:
        completed = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BrowserEvidenceError("浏览器取证任务未能完成") from exc
    if completed.returncode != 0:
        raise BrowserEvidenceError("浏览器未能读取视频本体")
    try:
        payload = json.loads(completed.stdout)
    except (json.JSONDecodeError, TypeError) as exc:
        raise BrowserEvidenceError("浏览器取证结果不可用") from exc
    frames, timestamps = [], []
    for row in payload.get("frames") or []:
        if not isinstance(row, dict):
            continue
        path = Path(str(row.get("path") or "")).expanduser().resolve()
        timestamp = row.get("timestampMs")
        try:
            path.relative_to(root)
        except ValueError:
            continue
        if path.is_file() and path.stat().st_size > 0 and isinstance(timestamp, int) and timestamp >= 0:
            frames.append(str(path)); timestamps.append(timestamp)
    if not payload.get("mediaAvailable") or not frames:
        raise BrowserEvidenceError("浏览器未能读取视频本体")
    return {
        "pageAvailable": bool(payload.get("pageAvailable")),
        "mediaAvailable": True,
        "durationMs": int(payload.get("durationMs") or 0),
        "imagePaths": frames[:6],
        "timestampsMs": timestamps[:6],
        "mediaFingerprint": str(payload.get("mediaFingerprint") or ""),
        "acquisitionMode": "browser_video_frames",
    }
