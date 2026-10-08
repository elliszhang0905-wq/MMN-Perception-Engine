"""One immutable configuration-file snapshot shared by every MMN consumer.

Explicit initialization wins, then MMN_ENV_FILE, then the checkout .env. Process
environment overrides remain live; file values never change during a process.
"""
import os
from pathlib import Path
from threading import Lock
from types import MappingProxyType

_LOCK = Lock()
_SNAPSHOT = None


def initialize_runtime_config(path=None, *, root=None):
    global _SNAPSHOT
    with _LOCK:
        if _SNAPSHOT is not None:
            return _SNAPSHOT
        root = Path(root) if root is not None else Path(__file__).resolve().parent
        source = Path(path if path is not None else os.getenv("MMN_ENV_FILE") or root / ".env").expanduser()
        source = (source if source.is_absolute() else root / source).resolve()
        values = {}
        if source.exists():
            for line in source.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key, value = stripped.split("=", 1)
                    values[key.strip()] = value.strip().strip('"').strip("'")
        _SNAPSHOT = MappingProxyType(values)
        return _SNAPSHOT


def env_value(key, default=""):
    return os.getenv(key) or initialize_runtime_config().get(key) or default
