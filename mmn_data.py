"""MMN 统一数据根目录与模块路径契约。"""

from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
DATA_ROOT = Path(
    os.getenv("MMN_DATA_ROOT", os.getenv("MMN_DATA_DIR", str(REPO_ROOT / "data")))
).expanduser().resolve()
BACKUP_ROOT = Path(
    os.getenv("MMN_BACKUP_ROOT", str(REPO_ROOT / "backups"))
).expanduser().resolve()

MODULE_DIRS = {
    "core": "core",
    "product_evaluation": "modules/product_evaluation",
    "sales_warning": "modules/sales_warning",
    "market_intelligence": "modules/market_intelligence",
    "policy_intelligence": "modules/policy_intelligence",
    "creator_assets": "modules/creator_assets",
    "opportunity": "modules/opportunity",
    "rag": "modules/rag",
    "eval": "modules/eval",
    "imports_raw": "imports/raw",
    "imports_processed": "imports/processed",
    "runtime": "runtime",
    "reports": "reports",
}


def module_dir(module: str, *, create: bool = False) -> Path:
    """返回模块规范目录；未知模块不得静默写入数据根目录。"""
    if module not in MODULE_DIRS:
        raise KeyError(f"未知 MMN 数据模块：{module}")
    path = DATA_ROOT / MODULE_DIRS[module]
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def module_path(
    module: str,
    *parts: str,
    legacy: tuple[str, ...] = (),
    for_write: bool = False,
) -> Path:
    """统一解析模块文件；读取期兼容旧路径，所有新写入只返回规范路径。"""
    canonical = module_dir(module, create=for_write).joinpath(*parts)
    if for_write or canonical.exists():
        return canonical
    for relative in legacy:
        candidate = DATA_ROOT / relative
        if candidate.exists():
            return candidate
    return canonical


def required_layout() -> dict[str, str]:
    return {name: relative for name, relative in MODULE_DIRS.items()}
