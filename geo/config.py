"""Backend-only settings. No credentials or invented prices in projections."""
import json
import os
from .store import GeoError, integer, money_micro, fingerprint

NEUTRAL_PROMPT = "请根据可用信息回答购车咨询，对未知或不能核实的事实明确说明。"


def load_settings():
    from runtime_config import env_value
    def value(key, default=""):
        return os.environ[key] if key in os.environ else env_value(key, default)
    enabled = lambda key: value(key, "false").strip().lower() in {"1", "true", "yes", "on"}
    errors = []
    def numeric(key, default, low, high):
        try: return integer(value(key, str(default)), key, low, high)
        except GeoError:
            errors.append(key + "配置无效")
            return default
    def budget(key):
        try: return money_micro(value(key, "0")) / 1000000
        except GeoError:
            errors.append(key + "配置无效")
            return 0
    pricing = None
    if value("GEO_PRICE_CONFIG_JSON"):
        try:
            pricing = json.loads(value("GEO_PRICE_CONFIG_JSON"))
            if not isinstance(pricing, dict): raise ValueError()
        except (ValueError, TypeError): errors.append("GEO_PRICE_CONFIG_JSON格式错误")
    mode = value("MMN_GEO_WORKER_MODE", "off").strip().lower()
    if mode not in {"off", "thread", "external"}: errors.append("MMN_GEO_WORKER_MODE无效"); mode = "off"
    return {"enabled": enabled("MMN_GEO_ENABLED"), "real_sampling_enabled": enabled("MMN_GEO_REAL_SAMPLING_ENABLED"),
            "db_path": value("MMN_GEO_DB_PATH").strip(),
            "worker_mode": mode, "api_key": value("ARK_API_KEY").strip(),
            "base_url": value("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3").strip(),
            "model": value("GEO_MODEL_ID").strip(), "api_mode": value("GEO_API_MODE", "responses").strip(),
            "supports_seed": enabled("GEO_SUPPORTS_SEED"), "supports_temperature": enabled("GEO_SUPPORTS_TEMPERATURE"),
            "model_config_version": value("GEO_MODEL_CONFIG_VERSION", "unverified"),
            "max_questions": numeric("GEO_MAX_QUESTIONS", 50, 1, 50),
            "max_repeats": numeric("GEO_MAX_REPEATS", 5, 1, 10),
            "max_concurrency": numeric("GEO_MAX_CONCURRENCY", 1, 1, 4),
            "max_output_tokens": numeric("GEO_MAX_OUTPUT_TOKENS", 2048, 1, 8192),
            "batch_budget": budget("MMN_GEO_BATCH_BUDGET"), "day_budget": budget("MMN_GEO_DAY_BUDGET"),
            "max_attempts": numeric("GEO_MAX_ATTEMPTS", 3, 1, 3), "pricing": pricing, "configuration_errors": errors}


def provider_hash(settings):
    return fingerprint({key: settings.get(key) for key in ("base_url", "model", "model_config_version", "api_mode", "supports_seed", "supports_temperature")})


def capabilities(settings, role="viewer"):
    from .provider import ArkProvider
    missing = [key for key, value in [("ARK_API_KEY", settings.get("api_key")), ("GEO_MODEL_ID", settings.get("model"))] if not value]
    result = {"enabled": bool(settings.get("enabled")), "real_sampling_enabled": bool(settings.get("real_sampling_enabled")),
              "worker_mode": settings.get("worker_mode", "off"), "role": role,
              "missing": missing, "quotas": {key: settings.get(key, 0) for key in ("max_questions", "max_repeats", "max_concurrency", "max_output_tokens", "batch_budget", "day_budget")},
              "pricing": {"configured": bool(settings.get("pricing")), "currency": (settings.get("pricing") or {}).get("currency"), "version": (settings.get("pricing") or {}).get("version")},
              "blocked_reasons": list(settings.get("configuration_errors", []))}
    if role == "admin":
        result["provider"] = {"configured": not missing, "api_mode": settings.get("api_mode", "responses"), "model": settings.get("model") or None, "capabilities": ArkProvider(settings).capabilities({"api_mode": settings.get("api_mode", "responses"), "mode": "non_search", "surface": "ark_model_api"})}
    return result
