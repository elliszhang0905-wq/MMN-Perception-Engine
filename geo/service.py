"""Module orchestration; no HTTP framework or parallel authentication layer."""
import csv
import io
import json
from .config import NEUTRAL_PROMPT, provider_hash
from .metrics import compute_metrics
from .store import GeoError, decoded, dumps, fingerprint, integer, money_micro, stamp, text_value, uid


class GeoService:
    def __init__(self, repo, settings, provider=None):
        self.repo, self.settings, self.provider = repo, settings, provider

    def create_project(self, org, body, actor):
        requested = body.get("budget") or {}
        quotas = {}
        for key, default in [("max_questions", 50), ("max_repeats", 5), ("max_concurrency", 1), ("max_output_tokens", 2048)]:
            ceiling = self.settings.get(key, default)
            quotas[key] = integer(requested.get(key) if requested.get(key) is not None else ceiling, key, 1, ceiling)
        for key in ("batch_budget", "day_budget"):
            ceiling = self.settings.get(key, 0)
            value = requested.get(key) if requested.get(key) is not None else ceiling
            if money_micro(value) > money_micro(ceiling): raise GeoError("项目预算超过后端允许额度")
            quotas[key] = value
        return self.repo.create_project(org, {**body, "budget": quotas}, actor)

    def add_condition(self, org, project_id, body, actor):
        from .provider import ArkProvider
        project = self.repo.get_project(org, project_id)
        surface = body.get("surface", "ark_model_api")
        api_mode = "manual" if surface == "doubao_app_manual" else ("assistant" if surface == "ark_assistant_api" else self.settings.get("api_mode", "responses"))
        if body.get("api_mode") and body["api_mode"] != api_mode: raise GeoError("接口条件须匹配后端当前配置")
        condition = {"surface": surface, "api_mode": api_mode, "mode": body.get("mode", "non_search"),
                     "model": "" if api_mode == "manual" else self.settings.get("model", ""),
                     "max_output_tokens": integer(body.get("max_output_tokens", project["budget"]["max_output_tokens"]), "输出上限", 1, min(project["budget"]["max_output_tokens"], self.settings.get("max_output_tokens", 2048))),
                     "timeout_seconds": integer(body.get("timeout_seconds", 60), "超时", 1, 120),
                     "system_prompt_version": "neutral-v1", "system_prompt": NEUTRAL_PROMPT,
                     "model_config_version": self.settings.get("model_config_version", "unverified"), "provider_config_hash": provider_hash(self.settings)}
        condition["capabilities"] = ArkProvider(self.settings).capabilities(condition)
        for field in ("temperature", "seed"):
            if body.get(field) is not None:
                if condition["capabilities"].get(field) is not True: raise GeoError(f"当前条件未验证{field}支持，不能固定该参数")
                condition[field] = body[field]
        return self.repo.add_condition(org, project_id, condition, actor)

    def policy(self, manifest):
        settings, pricing = self.settings, self.settings.get("pricing")
        reasons, unknown = list(settings.get("configuration_errors", [])), []
        if manifest["manual"]:
            return {"queue_allowed": False, "blocked_reasons": [], "attempt_reserve_micro": 0, "max_attempts": 1, "currency": "CNY", "pricing": None}
        for needed, value, label in [("real", settings.get("real_sampling_enabled"), "真实采样未获启用"), ("key", settings.get("api_key"), "缺少ARK_API_KEY"), ("model", settings.get("model"), "缺少GEO_MODEL_ID"), ("worker", settings.get("worker_mode") in {"thread", "external"}, "采样worker尚未启用")]:
            if not value: reasons.append(label)
        if not manifest["budget"]["batch_budget"] or not manifest["budget"]["day_budget"]: reasons.append("缺少明确批次及日预算")
        if len(manifest["questions"]) > settings.get("max_questions", 50) or manifest["repeats"] > settings.get("max_repeats", 5): reasons.append("试验超过后端配额")
        reserve = None
        if not isinstance(pricing, dict):
            reasons.append("缺少版本化模型单价和成本上界"); unknown.append("模型输入输出费用未计价")
        else:
            try:
                for key in ("version", "currency", "priced_at", "source_url", "model"):
                    text_value(pricing.get(key), key, 500, True)
                if pricing["model"] != settings.get("model"): raise GeoError("单价与模型配置不匹配")
                if pricing["currency"] not in {"CNY", "USD"}: raise GeoError("单价币种未支持")
                if pricing["currency"] != "CNY": reasons.append("首版项目预算币种为CNY，其他币种不可排队采样")
                input_ceiling = integer(pricing.get("input_token_ceiling"), "模型输入上界", 1, 2000000)
                input_unit = money_micro(pricing.get("input_per_million"))
                output_unit = money_micro(pricing.get("output_per_million"))
                reserve = 0
                for condition in manifest["conditions"]:
                    if condition.get("provider_config_hash") != provider_hash(settings): reasons.append("冻结条件与当前后端模型配置不匹配")
                    if condition["api_mode"] == "chat" and condition["mode"] == "search_enabled": reasons.append("普通对话接口不能证明实际联网")
                    if condition["max_output_tokens"] > settings.get("max_output_tokens", 2048): reasons.append("冻结输出上限超过当前配额")
                    if any(len(q["text"].encode()) + len(condition.get("system_prompt", "").encode()) + 1024 > input_ceiling for q in manifest["questions"]): reasons.append("输入预算上界不足")
                    amount = (input_ceiling * input_unit + condition["max_output_tokens"] * output_unit + 999999) // 1000000
                    if condition["mode"] == "search_enabled":
                        # No documented hard tool-call cap is assumed. Single live validation remains a separate approved operator task.
                        reasons.append("联网工具次数与费用上界尚未真实核验，批量采样保持阻塞")
                        unknown.append("联网工具费用及调用次数上界未知")
                    if condition["surface"] == "ark_assistant_api":
                        if pricing.get("assistant_per_call") is None: reasons.append("助手工具单价缺失"); unknown.append("助手工具费用未计价")
                        else: amount += money_micro(pricing["assistant_per_call"])
                    reserve = max(reserve, amount)
            except (GeoError, KeyError, TypeError, ValueError):
                reasons.append("单价记录或成本上界不完整"); unknown.append("调用费用未知"); reserve = None
        return {"queue_allowed": not reasons, "blocked_reasons": list(dict.fromkeys(reasons)), "unknown_cost_items": list(dict.fromkeys(unknown)), "attempt_reserve_micro": reserve,
                "max_attempts": settings.get("max_attempts", 3), "currency": (pricing or {}).get("currency", "CNY"), "pricing": pricing}

    def preview(self, org, project_id, body):
        with self.repo.connect() as conn:
            manifest = self.repo._freeze(conn, org, project_id, body)
        policy = self.policy(manifest)
        calls = len(manifest["questions"]) * len(manifest["conditions"]) * manifest["repeats"]
        reserve = policy["attempt_reserve_micro"]
        return {"question_count": len(manifest["questions"]), "condition_count": len(manifest["conditions"]), "repeats": manifest["repeats"], "planned_calls": calls,
                "estimated_cost": calls * reserve / 1000000 if reserve is not None else None,
                "max_reserved_cost": calls * reserve * policy["max_attempts"] / 1000000 if reserve is not None else None,
                "currency": policy["currency"], "unknown_cost_items": policy.get("unknown_cost_items", []), "blocked_reasons": policy["blocked_reasons"], "policy": policy}

    def create_batch(self, org, project_id, body, actor="local"):
        return self.repo.create_batch(org, project_id, body, self.preview(org, project_id, body)["policy"], actor)

    def project_records(self, org, project_id, **filters):
        self.repo.get_project(org, project_id)
        result, offset = [], 0
        while True:
            page = self.repo.list_observations(org, project_id, limit=100, offset=offset, **filters)
            if page["total"] > 10000: raise GeoError("项目样本超出本次聚合上限，请筛选批次导出", "scope_required", 409)
            for item in page["items"]:
                item = self.repo.apply_reviews(item)
                item["condition"] = {**item["condition"], "configured_model": item["condition"].get("model"), "model": item.get("actual_model") or "unknown"}
                item.pop("raw_response", None)
                for attempt in item.get("attempts", []): attempt.pop("raw_response", None)
                result.append(item)
            offset += 100
            if offset >= page["total"]: return result

    def metrics(self, org, project_id, **filters):
        project = self.repo.get_project(org, project_id)
        records = self.project_records(org, project_id, **filters)
        scopes = {}
        for item in records:
            key = (item["frozen_target_key"], tuple(item["frozen_entity_keys"]))
            scopes.setdefault(key, []).append(item)
        result = compute_metrics([], project["target_key"], [x["key"] for x in project["entities"]])
        for (target, keys), items in scopes.items():
            value = compute_metrics(items, target, list(keys))
            result["groups"].extend([{**group, "target_key": target, "fixed_entities": list(keys)} for group in value["groups"]])
        result["definition_version"] = result.get("version")
        for group in result["groups"]:
            group["evidence_filters"] = {key: value for key, value in filters.items() if key in {"batch_id", "channel"} and value}
            group["evidence_scope_hash"] = fingerprint({key: group.get(key) for key in (
                "channel", "surface", "mode", "model", "condition_hash", "question_set_hash",
                "entity_set_hash", "fact_baseline_hash", "target_key", "fixed_entities", "observation_ids", "evidence_filters")})
        result["statement_boundary"] = "仅反映固定问题与条件下的观测，不代表用户曝光、市场份额或因果效果"
        return result

    def metric_evidence(self, org, project_id, scope_hash, limit=20, offset=0, **filters):
        scope_hash = text_value(scope_hash, "统计证据范围", 64, True)
        groups = self.metrics(org, project_id, **filters)["groups"]
        group = next((value for value in groups if value["evidence_scope_hash"] == scope_hash), None)
        if group is None: raise GeoError("统计证据范围已变化，请刷新指标后重新查看", "stale_scope", 409)
        ids = group["observation_ids"]
        return {"items": [self.repo.apply_reviews(self.repo.get_observation(org, ident)) for ident in ids[offset:offset + limit]],
                "total": len(ids), "limit": limit, "offset": offset}

    def diagnostics(self, org, project_id, limit=20, offset=0, reviewed_only=False):
        project = self.repo.get_project(org, project_id)
        items = []
        records = self.project_records(org, project_id)
        by_id = {x["id"]: x for x in records}
        for obs in records:
            analysis = obs.get("analysis") or {}
            if not analysis.get("valid_answer"): continue
            target = next((x for x in analysis.get("entities", []) if x.get("entity_key") == project["target_key"]), {})
            if target.get("mentioned") is False:
                items.append({"id": obs["id"] + ":omission", "kind": "omission", "label": "本条回答未提及目标车型", "statement_type": "observation", "observation_ids": [obs["id"]], "evidence": obs["answer"][:300], "action_suggestion": "核对问题适用范围，再提出公开材料补充假设并复测"})
            for index, fact in enumerate(analysis.get("fact_checks", [])):
                if fact.get("verdict") in {"contradicted", "outdated", "unverified", "conflicting_sources"}:
                    items.append({"id": f"{obs['id']}:fact:{index}", "kind": "fact_gap", "label": "产品事实需补证或更新", "statement_type": "hypothesis" if fact["verdict"] == "unverified" else "observation", "observation_ids": [obs["id"]], "evidence": fact.get("evidence", ""), "action_suggestion": "先审核车型版本与权威事实，再安排内容补充；效果通过同条件复测观察"})
        with self.repo.connect() as conn:
            reviews = [decoded(x) for x in conn.execute("SELECT * FROM geo_diagnostic_review WHERE org_id=? AND project_id=? ORDER BY created_at,id", (org, project_id))]
        latest = {x["diagnostic_id"]: x for x in reviews}
        for item in items:
            original = dict(item)
            obs = by_id[item["observation_ids"][0]]
            item["evidence_hash"] = fingerprint({"diagnostic": original, "raw_hash": obs["raw_hash"], "question_version_id": obs["question_version_id"], "analysis": obs.get("analysis"), "review_ids": [x["id"] for x in obs["reviews"]], "fact_baseline_hash": obs["fact_baseline_hash"]})
            review = latest.get(item["id"])
            item["review_status"] = "unreviewed"
            item["evidence_origin"] = obs["evidence_origin"]
            if review:
                matched = (review.get("evidence_hash") or review["source_hash"]) == item["evidence_hash"]
                item["review_status"] = review["decision"] if matched else "stale_review"
                if matched and review["decision"] in {"accepted", "modified"}:
                    snapshot = review.get("snapshot") or {}
                    item.update({key: snapshot[key] for key in ("label", "action_suggestion", "statement_type") if key in snapshot})
                    item.update(review.get("changes", {}))
                    item["reviewer"], item["reviewed_at"] = review["actor"], review["created_at"]
            item["source_hash"] = fingerprint({"evidence_hash": item["evidence_hash"], "visible_snapshot": {key: item[key] for key in ("label", "action_suggestion", "statement_type")}, "prior_review_id": review["id"] if review else None})
        if reviewed_only: items = [x for x in items if x["review_status"] in {"accepted", "modified"}]
        limit, offset = integer(limit, "每页条数", 1, 100), integer(offset, "分页位置", 0, 1000000)
        return {"items": items[offset:offset + limit], "total": len(items), "limit": limit, "offset": offset}

    def review_diagnostic(self, org, project_id, body, actor):
        ident = text_value(body.get("diagnostic_id"), "诊断标识", 220, True)
        source_hash = text_value(body.get("source_hash"), "证据版本", 64, True)
        reason = text_value(body.get("reason"), "诊断复核理由", 2000, True)
        decision = body.get("decision")
        if decision not in {"accepted", "modified", "rejected"}: raise GeoError("诊断复核结果错误")
        item = None
        offset = 0
        while True:
            page = self.diagnostics(org, project_id, limit=100, offset=offset)
            item = next((x for x in page["items"] if x["id"] == ident), None)
            if item or offset + 100 >= page["total"]: break
            offset += 100
        if not item: raise GeoError("诊断不存在或不属于当前项目", "not_found", 404)
        if item["source_hash"] != source_hash: raise GeoError("诊断证据已变化，请刷新后重新复核", "stale_review", 409)
        changes = body.get("changes") or {}
        if not isinstance(changes, dict) or any(x not in {"label", "action_suggestion", "statement_type"} for x in changes): raise GeoError("诊断修订字段错误")
        changes = {key: text_value(value, key, 2000, True) for key, value in changes.items()}
        if changes.get("statement_type", item["statement_type"]) not in {"observation", "hypothesis"}: raise GeoError("诊断必须标明观察或待验证假设")
        if decision == "modified" and not changes: raise GeoError("修订审核须填写实际修改")
        review_id = uid("diagnostic_review")
        with self.repo.connect(True) as conn:
            self.repo._get(conn, "geo_project", org, project_id)
            # Recheck while holding the writer lock, so another review or evidence correction cannot race approval.
            current, check_offset = None, 0
            while True:
                page = self.diagnostics(org, project_id, limit=100, offset=check_offset)
                current = next((x for x in page["items"] if x["id"] == ident), None)
                if current or check_offset + 100 >= page["total"]: break
                check_offset += 100
            if current is None or current["source_hash"] != source_hash: raise GeoError("诊断或复核稿已变化，请刷新后重新复核", "stale_review", 409)
            self.repo._insert(conn, "geo_diagnostic_review", {"id": review_id, "org_id": org, "project_id": project_id,
                "diagnostic_id": ident, "source_hash": source_hash, "decision": decision, "payload_json": dumps({"snapshot": current, "changes": changes, "evidence_hash": current["evidence_hash"]}), "actor": actor, "reason": reason, "created_at": stamp()})
            self.repo._audit(conn, org, project_id, "diagnostic_reviewed", review_id, actor, {"diagnostic_id": ident, "source_hash": source_hash, "decision": decision})
        return {"id": review_id, "diagnostic_id": ident, "decision": decision}

    def cockpit_summary(self, org, project_id):
        project = self.repo.get_project(org, project_id)
        diagnosed = self.diagnostics(org, project_id, limit=100, reviewed_only=True)
        evidence_ids = {ident for item in diagnosed["items"] for ident in item["observation_ids"]}
        actions, offset = [], 0
        while True:
            page = self.repo.list_actions(org, project_id, limit=100, offset=offset)
            actions.extend({key: x.get(key) for key in ("id", "title", "status", "observation_ids", "executed_at")} for x in page["items"] if x.get("observation_ids") and set(x["observation_ids"]).issubset(evidence_ids))
            if offset + 100 >= page["total"]: break
            offset += 100
            if offset >= 10000: raise GeoError("请在GEO内缩小任务范围")
        return {"project_id": project_id, "project_name": project["name"], "reviewed_diagnostics": diagnosed["items"][:5], "actions": actions[:5], "reviewed_diagnostic_n": diagnosed["total"], "offline_fixture_n": sum(x.get("evidence_origin") == "offline_fixture" for x in diagnosed["items"]), "statement_boundary": "仅展示已人工复核诊断；建议及观测差异不代表因果效果"}

    def import_questions(self, org, project_id, content, actor):
        content = text_value(content, "CSV", 200000, True)
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames or "text" not in reader.fieldnames: raise GeoError("CSV必须包含text表头")
        rows, seen = [], set()
        allowed = {"text", "category", "intent", "budget", "scenario", "segment", "source", "unbranded", "recommendation_eligible", "ranking_eligible", "fact_eligible", "target_entities", "competitors", "year", "trim", "market"}
        if any(x not in allowed for x in reader.fieldnames): raise GeoError("CSV存在未支持字段")
        for line, row in enumerate(reader, 2):
            if len(rows) >= 1000 or None in row: raise GeoError("CSV行数或列数超限")
            value = {k: v for k, v in row.items() if v not in (None, "")}
            if not value.get("text") or value["text"] in seen: raise GeoError(f"CSV第{line}行问题为空或重复")
            seen.add(value["text"])
            for key in ("unbranded", "recommendation_eligible", "ranking_eligible", "fact_eligible"):
                if key in value:
                    raw = value[key].lower()
                    if raw not in {"true", "false", "1", "0"}: raise GeoError(f"CSV第{line}行布尔值错误")
                    value[key] = raw in {"true", "1"}
            for key in ("target_entities", "competitors"):
                if key in value: value[key] = [x.strip() for x in value[key].split("|") if x.strip()]
            rows.append(value)
        if not rows: raise GeoError("CSV没有有效问题")
        with self.repo.connect(True) as conn:
            project = self.repo._get(conn, "geo_project", org, project_id)
            existing = {json.loads(r[0])["text"] for r in conn.execute("SELECT payload_json FROM geo_question_version WHERE org_id=? AND project_id=?", (org, project_id))}
            if any(x["text"] in existing for x in rows): raise GeoError("CSV与现有问题重复")
            for row in rows: self.repo._question_payload(row, project)
            for row in rows: self.repo._add_question(conn, org, project, row, actor=actor)
        return {"created": len(rows)}

    def export(self, org, project_id, kind, actor, admin=False):
        self.repo.get_project(org, project_id)
        if kind == "metrics": data = self.metrics(org, project_id)["groups"]
        elif kind == "observations":
            data = [{k: v for k, v in item.items() if k in {"id", "batch_id", "question_version_id", "channel", "evidence_origin", "status", "answer", "sampled_at", "analysis", "citations", "request_id", "search_requested", "search_observed", "reviewed"}} for item in self.project_records(org, project_id)]
        elif kind in {"questions", "audit"}:
            data, offset = [], 0
            while True:
                getter = self.repo.list_questions if kind == "questions" else self.repo.list_audit
                page = getter(org, project_id, limit=100, offset=offset)
                if page["total"] > 10000: raise GeoError("导出超限，请缩小范围")
                data.extend(page["items"]); offset += 100
                if offset >= page["total"]: break
        else: raise GeoError("导出类型错误")
        if kind == "questions":
            fields = ["text", "category", "intent", "budget", "scenario", "segment", "source", "unbranded", "recommendation_eligible", "ranking_eligible", "fact_eligible", "target_entities", "competitors", "year", "trim", "market"]
        else: fields = sorted({key for row in data for key in row}) or ["id"]
        def cell(value, key):
            if isinstance(value, bool): value = "true" if value else "false"
            elif isinstance(value, (dict, list)):
                value = "|".join(value) if kind == "questions" and key in {"target_entities", "competitors"} else dumps(value)
            elif value is None: value = ""
            value = str(value)
            return "'" + value if value.lstrip(" \t\r\n").startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n")) else value
        stream = io.StringIO(); writer = csv.writer(stream)
        writer.writerow(fields)
        for row in data: writer.writerow([cell(row.get(key), key) for key in fields])
        with self.repo.connect(True) as conn: self.repo._audit(conn, org, project_id, "export", project_id, actor, {"kind": kind, "row_count": len(data)})
        return {"filename": f"MMN_GEO_{kind}.csv", "csv": stream.getvalue(), "format": "csv"}
