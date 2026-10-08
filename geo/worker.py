"""A bounded worker, sharing persistent claims with external MMN jobs."""
import random
import threading
from .analysis import analyze_answer
from .config import provider_hash
from .store import GeoError, stamp


class BatchCancelSignal:
    def __init__(self, worker, org, observation_id):
        self.worker, self.org, self.observation_id = worker, org, observation_id

    def is_set(self):
        return self.worker.stop.is_set() or not self.worker.repo.dispatch_allowed(self.org, self.observation_id, self.worker.owner)

    def wait(self, timeout=None):
        if self.is_set(): return True
        self.worker.stop.wait(min(timeout if timeout is not None else 0.2, 0.2))
        return self.is_set()


def measured_cost(result, price, condition):
    usage = result.get("usage")
    if not isinstance(price, dict) or not isinstance(usage, dict): return None
    try:
        inputs, outputs = usage.get("input_tokens", usage.get("prompt_tokens")), usage.get("output_tokens", usage.get("completion_tokens"))
        if any(isinstance(x, bool) or not isinstance(x, int) or x < 0 for x in (inputs, outputs)): return None
        total = inputs * float(price["input_per_million"]) / 1000000 + outputs * float(price["output_per_million"]) / 1000000
        tools = usage.get("tool_usage") or {}
        if condition["mode"] == "search_enabled":
            count = tools.get("web_search")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0 or price.get("search_per_call") is None: return None
            total += count * float(price["search_per_call"])
        if condition["surface"] == "ark_assistant_api":
            count = tools.get("doubao_app")
            if not isinstance(count, int) or isinstance(count, bool) or count < 0 or price.get("assistant_per_call") is None: return None
            total += count * float(price["assistant_per_call"])
        return total
    except (TypeError, ValueError, KeyError, OverflowError): return None


class GeoWorker:
    def __init__(self, repo, settings, provider=None, owner=None):
        from .provider import ArkProvider
        from .store import uid
        self.repo, self.settings = repo, settings
        self.provider = provider or ArkProvider(settings)
        self.owner = owner or uid("worker")
        self.stop = threading.Event()

    def tick(self):
        if self.stop.is_set() or not self.settings.get("enabled") or not self.settings.get("real_sampling_enabled"): return False
        claim = self.repo.claim_next(self.owner, global_concurrency=self.settings.get("max_concurrency", 1))
        if claim is None: return False
        obs, condition, manifest = claim["observation"], claim["condition"], claim["manifest"]
        org, project = obs["org_id"], obs["project_id"]
        cancel_signal = BatchCancelSignal(self, org, obs["id"])
        try:
            if cancel_signal.is_set():
                result = {"status": "cancelled", "cost": 0, "billing_uncertain": False, "error_class": "cancelled", "error": "发出请求前任务已停止"}
            elif condition.get("provider_config_hash") and condition["provider_config_hash"] != provider_hash(self.settings):
                result = {"status": "failed", "error_class": "configuration_missing", "error": "冻结模型条件与当前配置不匹配", "cost": 0, "billing_uncertain": False}
            else:
                result = self.provider.sample(claim["question"], condition, cancel_event=cancel_signal)
                result["cost"] = measured_cost(result, manifest.get("pricing"), condition)
                if result.get("status") == "cancelled" and not result.get("billing_uncertain"): result["cost"] = 0
            analysis = None
            if result.get("status") == "completed":
                try:
                    analysis = analyze_answer(result.get("answer", ""), manifest["entities"], manifest["facts"], observed_at=result.get("finished_at"), question=claim["question"])
                except Exception:
                    result["analysis_error"] = "analysis_failed"
            delay = min(60, (2 ** min(manifest["max_attempts"], 3)) + random.random())
            self.repo.finish_attempt(org, obs["id"], self.owner, result, analysis, retry_delay=delay)
            if (result.get("raw_response") or {}).get("evidence_origin") == "offline_fixture":
                with self.repo.connect(True) as conn:
                    conn.execute("UPDATE geo_observation SET evidence_origin='offline_fixture' WHERE org_id=? AND id=?", (org, obs["id"]))
            if result.get("error_class") in {"authentication", "permission", "quota", "configuration_missing"}:
                with self.repo.connect(True) as conn:
                    conn.execute("UPDATE geo_batch SET status='blocked',paused=1 WHERE org_id=? AND id=? AND status NOT IN ('completed','completed_with_errors','cancelled')", (org, obs["batch_id"]))
                    self.repo._audit(conn, org, project, "provider_access_blocked", obs["batch_id"], self.owner, {"error_class": result["error_class"]})
        except GeoError:
            # A lost lease is preserved as uncertain by the next recovery pass.
            pass
        except Exception:
            # An unexpected analysis/transport failure after issuance cannot be assumed unbilled.
            try:
                self.repo.finish_attempt(org, obs["id"], self.owner, {"status": "uncertain", "error_class": "parse_error", "error": "调用后处理未能确认完整结果，请人工核查原始调用", "billing_uncertain": True, "cost": None, "finished_at": stamp()})
            except GeoError: pass
        return True

    def run(self):
        while not self.stop.is_set():
            if not self.tick(): self.stop.wait(1)
