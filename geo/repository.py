"""Versioned GEO project assets on MMN's existing database."""
import json
import re
from urllib.parse import urlparse

from .jobs import JobMixin
from .workflows import WorkflowMixin
from .store import Store, GeoError, decoded, dumps, fingerprint, integer, money_micro, stamp, text_value, uid

CATEGORIES = {"category", "scenario", "comparison", "recognition", "concern"}
DEFAULT_BUDGET = {"batch_budget": 0, "day_budget": 0, "max_questions": 50,
                  "max_repeats": 5, "max_concurrency": 1, "max_output_tokens": 2048}


def validate_entities(entities, target_key):
    if not isinstance(entities, list) or not 1 <= len(entities) <= 10:
        raise GeoError("请配置1至10个目标或竞品实体")
    output, keys = [], set()
    for item in entities:
        if not isinstance(item, dict):
            raise GeoError("实体格式错误")
        key = text_value(item.get("key"), "实体标识", 120, True)
        if key in keys or not re.fullmatch(r"[\w.:-]+", key):
            raise GeoError("实体标识重复或不合法")
        keys.add(key)
        aliases = item.get("aliases", [])
        if not isinstance(aliases, list) or len(aliases) > 20:
            raise GeoError("每个实体最多20个别名")
        output.append({"key": key, "name": text_value(item.get("name"), "车型或品牌", 120, True),
                       "aliases": list(dict.fromkeys(text_value(x, "别名", 80, True) for x in aliases)),
                       **{x: text_value(item.get(x), x, 120) for x in ("brand", "year", "trim", "market", "master_id")}})
    if target_key not in keys:
        raise GeoError("目标实体必须在项目范围中")
    return output


def validate_budget(values, original=None):
    if not isinstance(values, dict):
        raise GeoError("配额格式错误")
    budget = {**DEFAULT_BUDGET, **(original or {})}
    for field in ("batch_budget", "day_budget"):
        if field in values:
            budget[field] = money_micro(values[field]) / 1000000
    for field, high in [("max_questions", 50), ("max_repeats", 10), ("max_concurrency", 4), ("max_output_tokens", 8192)]:
        if field in values:
            budget[field] = integer(values[field], field, 1, high)
    return budget


class GeoRepository(WorkflowMixin, JobMixin, Store):
    def create_project(self, org_id, payload, actor="local"):
        org_id = text_value(org_id, "客户空间", 160, True)
        target = text_value(payload.get("target_key"), "目标标识", 120, True)
        edition = payload.get("edition", "china")
        if edition not in {"china", "global"}:
            raise GeoError("版本范围错误")
        value = {"name": text_value(payload.get("name"), "项目名称", 160, True),
                 "target_key": target, "entities": validate_entities(payload.get("entities"), target),
                 "budget": validate_budget(payload.get("budget", {}))}
        ident, now = uid("project"), stamp()
        with self.connect(True) as conn:
            self._insert(conn, "geo_project", {"id": ident, "org_id": org_id, "edition": edition,
                         "payload_json": dumps(value), "created_at": now, "updated_at": now})
            self._audit(conn, org_id, ident, "project_created", ident, actor)
        return self.get_project(org_id, ident)

    def get_project(self, org_id, project_id):
        with self.connect() as conn:
            return self._get(conn, "geo_project", org_id, project_id)

    def list_projects(self, org_id, limit=20, offset=0, edition="china"):
        limit, offset = integer(limit, "每页条数", 1, 100), integer(offset, "分页位置", 0, 1000000)
        with self.connect() as conn:
            total = conn.execute("SELECT count(*) FROM geo_project WHERE org_id=? AND edition=?", (org_id, edition)).fetchone()[0]
            items = conn.execute("SELECT * FROM geo_project WHERE org_id=? AND edition=? ORDER BY created_at DESC LIMIT ? OFFSET ?", (org_id, edition, limit, offset)).fetchall()
        return {"items": [decoded(x) for x in items], "total": total, "limit": limit, "offset": offset}

    def update_entities(self, org_id, project_id, entities, actor="local"):
        with self.connect(True) as conn:
            project = self._get(conn, "geo_project", org_id, project_id)
            project["entities"] = validate_entities(entities, project["target_key"])
            value = {x: project[x] for x in ("name", "target_key", "entities", "budget")}
            conn.execute("UPDATE geo_project SET payload_json=?,updated_at=? WHERE org_id=? AND id=?", (dumps(value), stamp(), org_id, project_id))
            self._audit(conn, org_id, project_id, "entity_mapping_updated", project_id, actor, {"entity_keys": [x["key"] for x in entities]})
        return self.get_project(org_id, project_id)

    def update_budget(self, org_id, project_id, budget, actor="local"):
        with self.connect(True) as conn:
            project = self._get(conn, "geo_project", org_id, project_id)
            value = {x: project[x] for x in ("name", "target_key", "entities", "budget")}
            value["budget"] = validate_budget(budget, project["budget"])
            conn.execute("UPDATE geo_project SET payload_json=?,updated_at=? WHERE org_id=? AND id=?", (dumps(value), stamp(), org_id, project_id))
            self._audit(conn, org_id, project_id, "project_budget_updated", project_id, actor, value["budget"])
        return self.get_project(org_id, project_id)

    def _question_payload(self, payload, project, original=None):
        value = {**(original or {}), **payload}
        result = {x: text_value(value.get(x), x, 2000 if x == "text" else 300, x == "text")
                  for x in ("text", "intent", "budget", "scenario", "segment", "source")}
        result["category"] = value.get("category", "category")
        if result["category"] not in CATEGORIES:
            raise GeoError("问题类别错误")
        keys = {x["key"] for x in project["entities"]}
        for field in ("target_entities", "competitors"):
            entries = value.get(field, [project["target_key"]] if field == "target_entities" else [])
            if not isinstance(entries, list) or len(entries) > 10 or any(x not in keys for x in entries):
                raise GeoError("问题关联实体不属于项目")
            result[field] = list(dict.fromkeys(entries))
        for field, default in [("unbranded", False), ("recommendation_eligible", False), ("ranking_eligible", False), ("fact_eligible", False)]:
            result[field] = value.get(field, default)
            if not isinstance(result[field], bool):
                raise GeoError(f"{field}必须为布尔值")
        for field in ("year", "trim", "market"):
            result[field] = text_value(value.get(field), field, 100)
        result["temperature"] = text_value(value.get("temperature"), "适用温度", 100)
        return result

    def _add_question(self, conn, org, project, payload, question_id=None, actor="local"):
        original = None
        if question_id:
            q = self._get(conn, "geo_question", org, question_id, project["id"])
            original = decoded(conn.execute("SELECT * FROM geo_question_version WHERE org_id=? AND question_id=? AND version=?", (org, question_id, q["latest_version"])).fetchone())
            version = q["latest_version"] + 1
        else:
            question_id, version = uid("question"), 1
            self._insert(conn, "geo_question", {"id": question_id, "org_id": org, "project_id": project["id"], "active": 1, "latest_version": 1, "created_at": stamp()})
        value = self._question_payload(payload, project, original)
        version_id = uid("qv")
        self._insert(conn, "geo_question_version", {"id": version_id, "org_id": org, "project_id": project["id"], "question_id": question_id, "version": version, "payload_json": dumps(value), "created_at": stamp()})
        conn.execute("UPDATE geo_question SET latest_version=? WHERE org_id=? AND id=?", (version, org, question_id))
        self._audit(conn, org, project["id"], "question_version_created", version_id, actor, {"question_id": question_id, "version": version})
        return {**value, "id": question_id, "version_id": version_id, "version": version, "active": True}

    def add_question(self, org_id, project_id, payload, question_id=None, actor="local"):
        with self.connect(True) as conn:
            return self._add_question(conn, org_id, self._get(conn, "geo_project", org_id, project_id), payload, question_id, actor)

    def list_questions(self, org_id, project_id, limit=20, offset=0, category=None, active=None, search=""):
        self.get_project(org_id, project_id)
        limit, offset = integer(limit, "每页条数", 1, 100), integer(offset, "分页位置", 0, 1000000)
        where, args = "q.org_id=? AND q.project_id=?", [org_id, project_id]
        if category:
            if category not in CATEGORIES: raise GeoError("问题类别错误")
            where += " AND json_extract(v.payload_json,'$.category')=?"; args.append(category)
        if active is not None:
            if not isinstance(active, bool): raise GeoError("启用状态错误")
            where += " AND q.active=?"; args.append(int(active))
        if search:
            where += " AND instr(json_extract(v.payload_json,'$.text'),?)>0"; args.append(text_value(search, "搜索", 300))
        join = "FROM geo_question q JOIN geo_question_version v ON v.org_id=q.org_id AND v.question_id=q.id AND v.version=q.latest_version WHERE " + where
        with self.connect() as conn:
            total = conn.execute("SELECT count(*) " + join, args).fetchone()[0]
            rows = conn.execute("SELECT v.*,q.active " + join + " ORDER BY q.created_at DESC LIMIT ? OFFSET ?", [*args, limit, offset]).fetchall()
        items = []
        for row in rows:
            item = decoded(row); item["version_id"], item["id"] = item["id"], item["question_id"]; item["active"] = bool(item["active"]); items.append(item)
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    def question_versions(self, org, question_id, limit=20, offset=0):
        with self.connect() as conn:
            q = self._get(conn, "geo_question", org, question_id)
            page = self._page(conn, "geo_question_version", org, q["project_id"], limit, offset, " AND question_id=?", [question_id])
        for item in page["items"]:
            item["version_id"], item["id"] = item["id"], question_id
        return page

    def set_question_state(self, org, question_id, active, actor="local"):
        if not isinstance(active, bool): raise GeoError("启用状态必须为布尔值")
        with self.connect(True) as conn:
            q = self._get(conn, "geo_question", org, question_id)
            conn.execute("UPDATE geo_question SET active=? WHERE org_id=? AND id=?", (int(active), org, question_id))
            self._audit(conn, org, q["project_id"], "question_state_changed", question_id, actor, {"active": active})
        return {"id": question_id, "active": active}

    def seed_examples(self, org, project_id, actor="local"):
        project = self.get_project(org, project_id)
        target = next(x["name"] for x in project["entities"] if x["key"] == project["target_key"])
        other = next((x["name"] for x in project["entities"] if x["key"] != project["target_key"]), "另一候选车型")
        topics = ["日常通勤", "长途出行", "家庭接送", "停车便利", "补能便利", "使用成本", "空间", "舒适性", "驾驶体验", "质量疑虑", "售后服务", "智能功能", "安全", "保值", "周末出游"]
        texts = [("category", f"计划购买汽车，主要关注{topic}，有哪些候选值得了解？") for topic in topics]
        texts += [("scenario", f"经常需要{topic}，选择车型时有哪些取舍？") for topic in topics[:10]]
        texts += [("comparison", f"{target}和{other}在{topic}方面如何比较和选择？") for topic in topics[:10]]
        texts += [("recognition", f"了解{target}的{topic}时，应核对哪些产品事实和版本条件？") for topic in topics[:10]]
        texts += [("concern", f"对{target}的{topic}存在疑虑，需要查阅哪些证据？") for topic in topics[9:14]]
        with self.connect(True) as conn:
            for category, content in texts:
                self._add_question(conn, org, project, {"text": content, "category": category,
                    "source": "editable_example_not_user_research", "unbranded": category in {"category", "scenario"},
                    "recommendation_eligible": category in {"category", "scenario", "comparison"}, "fact_eligible": category in {"recognition", "concern"}}, actor=actor)
        return {"created": 50}

    def add_condition(self, org, project_id, payload, actor="local"):
        surface, mode, api_mode = payload.get("surface"), payload.get("mode"), payload.get("api_mode")
        modes = {"non_search", "search_enabled", "unknown"} if surface == "doubao_app_manual" else {"non_search", "search_enabled"}
        if surface not in {"ark_model_api", "ark_assistant_api", "doubao_app_manual"} or mode not in modes or api_mode not in {"chat", "responses", "assistant", "manual"}:
            raise GeoError("采样渠道或模式错误")
        if (surface == "doubao_app_manual") != (api_mode == "manual") or (surface == "ark_assistant_api") != (api_mode == "assistant"):
            raise GeoError("渠道与接口条件不一致")
        value = {x: payload.get(x) for x in ("surface", "mode", "api_mode", "temperature", "seed", "capabilities", "provider_config_hash", "model_config_version")}
        value.update({"model": text_value(payload.get("model"), "模型标识", 200),
                      "system_prompt_version": text_value(payload.get("system_prompt_version", "neutral-v1"), "提示版本", 80, True),
                      "system_prompt": text_value(payload.get("system_prompt"), "系统提示", 2000),
                      "max_output_tokens": integer(payload.get("max_output_tokens", 2048), "输出上限", 1, 8192),
                      "timeout_seconds": integer(payload.get("timeout_seconds", 60), "超时", 1, 120)})
        hash_value = fingerprint(value)
        with self.connect(True) as conn:
            self._get(conn, "geo_project", org, project_id)
            existing = conn.execute("SELECT * FROM geo_condition WHERE org_id=? AND project_id=? AND condition_hash=?", (org, project_id, hash_value)).fetchone()
            if existing: return decoded(existing)
            ident = uid("condition")
            self._insert(conn, "geo_condition", {"id": ident, "org_id": org, "project_id": project_id, "condition_hash": hash_value, "payload_json": dumps(value), "created_at": stamp()})
            self._audit(conn, org, project_id, "condition_created", ident, actor, {"condition_hash": hash_value})
            return self._get(conn, "geo_condition", org, ident)

    def list_conditions(self, org, project_id, limit=20, offset=0):
        with self.connect() as conn:
            self._get(conn, "geo_project", org, project_id)
            return self._page(conn, "geo_condition", org, project_id, limit, offset)

    def add_fact(self, org, project_id, payload, actor="local"):
        with self.connect(True) as conn:
            project = self._get(conn, "geo_project", org, project_id)
            logical_id = payload.get("logical_id") or uid("fact_key")
            previous = conn.execute("SELECT * FROM geo_fact_baseline WHERE org_id=? AND logical_id=? ORDER BY version DESC LIMIT 1", (org, logical_id)).fetchone()
            if payload.get("logical_id") and not previous: raise GeoError("事实标识不存在", "not_found", 404)
            if previous and previous["project_id"] != project_id: raise GeoError("事实不属于项目")
            value = {x: payload.get(x, "") for x in ("entity_key", "year", "trim", "market", "field", "value", "unit", "cycle", "conditions", "effective_from", "effective_to", "source_url", "source_excerpt", "state")}
            if value["entity_key"] not in {x["key"] for x in project["entities"]}: raise GeoError("事实实体不属于项目")
            value["field"] = text_value(value["field"], "事实字段", 100, True)
            value["state"] = value["state"] or "draft"
            if value["state"] not in {"draft", "approved", "rejected"}: raise GeoError("事实审核状态错误")
            value["reviewer"] = actor if value["state"] == "approved" else ""
            if len(dumps(value)) > 16000: raise GeoError("事实内容过长")
            if value["state"] == "approved":
                for key in ("year", "trim", "market", "effective_from", "source_url", "source_excerpt"):
                    text_value(value[key], key, 5000, True)
                parsed = urlparse(value["source_url"])
                if parsed.scheme != "https" or not parsed.hostname or parsed.username: raise GeoError("事实来源必须为HTTPS公开来源")
                from datetime import date
                try:
                    start = date.fromisoformat(value["effective_from"])
                    if value["effective_to"] and date.fromisoformat(value["effective_to"]) < start: raise ValueError()
                except ValueError: raise GeoError("事实有效日期错误") from None
            ident, version = uid("fact"), previous["version"] + 1 if previous else 1
            self._insert(conn, "geo_fact_baseline", {"id": ident, "org_id": org, "project_id": project_id, "logical_id": logical_id, "version": version, "payload_json": dumps(value), "created_at": stamp()})
            self._audit(conn, org, project_id, "fact_version_created", ident, actor, {"logical_id": logical_id, "version": version, "state": value["state"]})
            return self._get(conn, "geo_fact_baseline", org, ident)

    def list_facts(self, org, project_id, limit=20, offset=0):
        with self.connect() as conn:
            self._get(conn, "geo_project", org, project_id)
            return self._page(conn, "geo_fact_baseline", org, project_id, limit, offset)

    def latest_facts(self, conn, org, project_id):
        return [decoded(row) for row in conn.execute("SELECT f.* FROM geo_fact_baseline f WHERE f.org_id=? AND f.project_id=? AND f.version=(SELECT max(v.version) FROM geo_fact_baseline v WHERE v.org_id=f.org_id AND v.logical_id=f.logical_id)", (org, project_id))]
