"""BF原始文件的项目级安全存储。"""

import os
import re
from pathlib import Path


def _safe_part(value):
    value = Path(str(value or "unknown").replace("\\", "/")).name
    value = re.sub(r"[^\w.-]+", "_", value, flags=re.UNICODE).strip("._")
    return value[:80] or "unknown"


def sanitize_filename(filename):
    name = Path(str(filename or "upload.bin").replace("\\", "/")).name
    stem = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", Path(name).stem, flags=re.UNICODE).strip("._")
    suffix = re.sub(r"[^A-Za-z0-9.]", "", Path(name).suffix.lower())[:12]
    return f"{(stem[:100] or 'upload')}{suffix}"


def store_document(*, root, org_id, client_key, project_id, document_id, filename, data):
    root_path = Path(root).expanduser().resolve()
    directory = root_path.joinpath(
        _safe_part(org_id),
        _safe_part(client_key),
        _safe_part(project_id),
        _safe_part(document_id),
        "original",
    )
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = directory / sanitize_filename(filename)
    resolved = target.resolve()
    if root_path != resolved and root_path not in resolved.parents:
        raise ValueError("BF文件路径越界")
    with open(resolved, "wb") as handle:
        handle.write(bytes(data))
    os.chmod(resolved, 0o600)
    return resolved
