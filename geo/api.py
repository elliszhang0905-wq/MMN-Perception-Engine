"""GEO routes plugged into MMN's existing authenticated Handler."""
from copy import deepcopy
from contextlib import closing
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import threading
from urllib.parse import parse_qs

from .config import capabilities, load_settings
from .repository import GeoRepository
from .service import GeoService
from .store import GeoError, fingerprint, integer, text_value

_WORKERS = {}
_WORKER_LOCK = threading.Lock()


def _value(query, name, default=None):
    value = query.get(name, default)
    return value[0] if isinstance(value, list) and value else value


def _paging(query):
    return {"limit": integer(_value(query, "limit", 20), "每页条数", 1, 100), "offset": integer(_value(query, "offset", 0), "分页位置", 0, 1000000)}


def _scope_record(repo, table, org, ident):
    with repo.connect() as conn: return repo._get(conn, table, org, ident)


def _public_observation(value, admin):
    output = deepcopy(value)
    if not admin:
        output.pop("raw_response", None)
        for attempt in output.get("attempts", []): attempt.pop("raw_response", None)
    return output


def _catalog(db_path, org, query):
    page = _paging(query)
    edition = _value(query, "edition", "china")
    if edition not in {"china", "global"}: raise GeoError("版本范围错误")
    with closing(sqlite3.connect(Path(db_path).expanduser().resolve().as_uri() + "?mode=ro", uri=True, timeout=15)) as conn:
        conn.row_factory = sqlite3.Row
        table = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='vehicle_assets'").fetchone()
        if not table: return {"items": [], "total": 0, **page}
        where, args = "org_id=? AND edition=?", [org, edition]
        search = _value(query, "search")
        if search: where += " AND instr(model_name,?)>0"; args.append(text_value(search, "车型搜索", 160))
        group = f"FROM vehicle_assets WHERE {where} GROUP BY brand_name,model_name"
        total = conn.execute("SELECT count(*) FROM (SELECT 1 " + group + ")", args).fetchone()[0]
        rows = conn.execute("SELECT min(id) master_id,brand_name,model_name " + group + " ORDER BY model_name LIMIT ? OFFSET ?", [*args, page["limit"], page["offset"]]).fetchall()
    items = [{"key": "vehicle_" + hashlib.sha256((str(x["brand_name"]) + "|" + x["model_name"]).encode()).hexdigest()[:20],
              "master_id": x["master_id"], "name": x["model_name"], "brand": x["brand_name"] or "", "aliases": [], "year": "", "trim": "", "market": ""} for x in rows]
    return {"items": items, "total": total, **page}


def _ensure_worker(repo, settings):
    if not settings.get("real_sampling_enabled") or settings.get("worker_mode") != "thread": return
    from .worker import GeoWorker
    with _WORKER_LOCK:
        key = str(repo.db_path)
        if key in _WORKERS: return
        worker = GeoWorker(repo, settings)
        threads = [threading.Thread(target=worker.run, name=f"mmn-geo-{i}", daemon=True) for i in range(settings.get("max_concurrency", 1))]
        _WORKERS[key] = (worker, threads)
        for thread in threads: thread.start()


def _storage_path(settings, business_db):
    configured = settings.get("db_path")
    if not configured:
        raise GeoError("GEO工作区暂不可用，请联系管理员完成配置", "storage_unconfigured", 409)
    path = Path(configured).expanduser().resolve()
    business = Path(business_db).expanduser().resolve()
    if path == business or (path.exists() and business.exists() and path.samefile(business)):
        raise GeoError("GEO工作区配置冲突，请联系管理员检查", "storage_conflict", 409)
    return path


def execute(method, path, query, body, auth, db_path, settings=None):
    settings = settings if settings is not None else load_settings()
    if not auth or not auth.get("org_id"): raise GeoError("请先登录并绑定客户空间", "unauthorized", 401)
    org, actor = str(auth["org_id"]), str(auth.get("user_id") or auth.get("username") or "local")
    admin = auth.get("role") == "admin"
    if not isinstance(body, dict): raise GeoError("请求必须为JSON对象")
    if any(body.get(key) and body[key] != org for key in ("org_id", "tenant_id")) or any(_value(query, key) and _value(query, key) != org for key in ("org_id", "tenant_id")):
        raise GeoError("不能访问其他客户空间", "forbidden", 403)
    if method == "GET" and path == "/api/geo/capabilities": return capabilities(settings, auth.get("role", "viewer")), 200
    if not settings.get("enabled"): raise GeoError("GEO模块尚未启用", "module_disabled", 409)
    if method not in {"GET", "POST"}: raise GeoError("请求方法不支持", "method_not_allowed", 405)
    if method == "POST" and not admin: raise GeoError("当前权限只支持查看与导出", "forbidden", 403)
    storage = _storage_path(settings, db_path)
    if path == "/api/geo/catalog" and method == "GET": return _catalog(db_path, org, query), 200
    repo = GeoRepository(storage)
    service = GeoService(repo, settings)
    _ensure_worker(repo, settings)
    if path == "/api/geo/projects":
        if method == "GET": return repo.list_projects(org, edition=_value(query, "edition", "china"), **_paging(query)), 200
        return service.create_project(org, body, actor), 201
    match = re.fullmatch(r"/api/geo/projects/([^/]+)/(entities|budget|questions(?:/(?:examples|import))?|conditions|batches(?:/preview)?|observations|metrics|diagnostics(?:/reviews)?|cockpit-summary|actions|retests|app-imports|app-comparisons|facts|audit|export)", path)
    if match:
        project_id, resource = match.groups()
        repo.get_project(org, project_id)
        if method == "GET":
            page = _paging(query)
            if resource == "questions":
                active = _value(query, "active")
                if active not in {None, "", "true", "false"}: raise GeoError("启用筛选错误")
                return repo.list_questions(org, project_id, category=_value(query, "category"), active=None if active in {None, ""} else active == "true", search=_value(query, "search", ""), **page), 200
            if resource == "observations":
                if _value(query, "metric_scope"):
                    result = service.metric_evidence(org, project_id, _value(query, "metric_scope"), **page,
                        **{key: _value(query, key) for key in ("batch_id", "channel") if _value(query, key)})
                    result["items"] = [_public_observation(x, admin) for x in result["items"]]
                    return result, 200
                filters = {key: _value(query, key) for key in ("batch_id", "channel", "status", "search", "condition_hash") if _value(query, key)}
                if filters.get("status") == "needs_review":
                    filters.pop("status")
                    records = service.project_records(org, project_id, **filters)
                    records = [x for x in records if (x["status"] == "completed" and x.get("analysis") is None) or any(v.get("needs_review") for v in (x.get("analysis") or {}).get("entities", []))]
                    result = {"items": records[page["offset"]:page["offset"] + page["limit"]], "total": len(records), **page}
                else:
                    result = repo.list_observations(org, project_id, **filters, **page)
                    result["items"] = [repo.apply_reviews(x) for x in result["items"]]
                result["items"] = [_public_observation(x, admin) for x in result["items"]]
                return result, 200
            if resource == "metrics": return service.metrics(org, project_id, **{key: _value(query, key) for key in ("batch_id", "channel") if _value(query, key)}), 200
            if resource == "diagnostics": return service.diagnostics(org, project_id, reviewed_only=not admin, **page), 200
            if resource == "cockpit-summary": return service.cockpit_summary(org, project_id), 200
            if resource == "export": return service.export(org, project_id, _value(query, "kind", "observations"), actor, admin), 200
            getter = {"conditions": repo.list_conditions, "batches": repo.list_batches, "facts": repo.list_facts,
                      "actions": repo.list_actions, "retests": repo.list_retests, "app-comparisons": repo.app_comparisons, "audit": repo.list_audit}.get(resource)
            if getter: return getter(org, project_id, **page), 200
        else:
            if resource == "entities": return repo.update_entities(org, project_id, body.get("entities"), actor), 200
            if resource == "budget":
                for field in ("batch_budget", "day_budget"):
                    from .store import money_micro
                    if field in body and money_micro(body[field]) > money_micro(settings.get(field, 0)): raise GeoError("项目预算超过后端额度")
                for field, maximum in [("max_questions", 50), ("max_repeats", 5), ("max_concurrency", 1), ("max_output_tokens", 2048)]:
                    if field in body: integer(body[field], field, 1, settings.get(field, maximum))
                return repo.update_budget(org, project_id, body, actor), 200
            if resource == "questions": return repo.add_question(org, project_id, body, actor=actor), 201
            if resource == "questions/examples": return repo.seed_examples(org, project_id, actor), 201
            if resource == "questions/import": return service.import_questions(org, project_id, body.get("csv"), actor), 201
            if resource == "conditions": return service.add_condition(org, project_id, body, actor), 201
            if resource == "batches/preview":
                result = service.preview(org, project_id, body); result.pop("policy", None)
                return result, 200
            if resource == "batches": return service.create_batch(org, project_id, body, actor), 202
            if resource == "app-imports": return _public_observation(repo.apply_reviews(repo.import_app(org, project_id, body, actor)), admin), 201
            if resource == "facts": return repo.add_fact(org, project_id, body, actor), 201
            if resource == "actions": return repo.save_action(org, project_id, body, actor), 201
            if resource == "diagnostics/reviews": return service.review_diagnostic(org, project_id, body, actor), 201
    match = re.fullmatch(r"/api/geo/questions/([^/]+)/(versions|state)", path)
    if match:
        ident, suffix = match.groups(); q = _scope_record(repo, "geo_question", org, ident)
        if method == "GET" and suffix == "versions": return repo.question_versions(org, ident, **_paging(query)), 200
        if method == "POST" and suffix == "versions": return repo.add_question(org, q["project_id"], body, ident, actor), 201
        if method == "POST" and suffix == "state": return repo.set_question_state(org, ident, body.get("active"), actor), 200
    match = re.fullmatch(r"/api/geo/observations/([^/]+)(?:/(reviews|screenshots/([^/]+)))?", path)
    if match:
        ident, suffix, screenshot = match.groups()
        if method == "GET" and not suffix: return _public_observation(repo.apply_reviews(repo.get_observation(org, ident)), admin), 200
        if method == "GET" and screenshot: return repo.get_screenshot(org, ident, screenshot), 200
        if method == "POST" and suffix == "reviews": return repo.add_review(org, ident, body, actor), 201
    match = re.fullmatch(r"/api/geo/batches/([^/]+)(?:/(control))?", path)
    if match:
        ident, suffix = match.groups(); batch = repo.get_batch(org, ident)
        if method == "GET" and not suffix: return batch, 200
        if method == "POST" and suffix:
            policy = service.policy(batch["manifest"])
            return repo.control_batch(org, ident, body.get("command"), actor, body.get("observation_id"), body.get("reason", ""), policy), 200
    match = re.fullmatch(r"/api/geo/actions/([^/]+)(?:/(retest))?", path)
    if match and method == "POST":
        ident, suffix = match.groups(); action = _scope_record(repo, "geo_action", org, ident)
        if not suffix: return repo.save_action(org, action["project_id"], body, actor, ident), 200
        baseline = repo.get_batch(org, body.get("baseline_batch_id"))
        if baseline["project_id"] != action["project_id"]: raise GeoError("基线与动作项目不匹配")
        candidate = deepcopy(baseline["manifest"])
        candidate["budget"] = repo.get_project(org, action["project_id"])["budget"]
        if body.get("condition_ids") is not None:
            ids = body["condition_ids"]
            if not isinstance(ids, list) or not ids or len(ids) > 8 or any(not isinstance(x, str) for x in ids) or len(set(ids)) != len(ids): raise GeoError("复测条件清单错误")
            with repo.connect() as conn:
                candidate["conditions"] = [repo._get(conn, "geo_condition", org, cid, action["project_id"]) for cid in ids]
            flags = [x["surface"] == "doubao_app_manual" for x in candidate["conditions"]]
            if any(flags) and not all(flags): raise GeoError("复测不可混用人工与接口采样")
            candidate["manual"] = all(flags)
        return repo.create_retest(org, ident, body, service.policy(candidate), actor), 201
    raise GeoError("未找到GEO接口", "not_found", 404)


def dispatch(handler, parsed, db_path):
    auth = handler.require_brand_review_auth(write=handler.command == "POST")
    if not auth: return
    try:
        body = handler.read_json() if handler.command == "POST" else {}
        data, status = execute(handler.command, parsed.path, parse_qs(parsed.query), body, auth, db_path)
        handler.send_json({"ok": True, "data": data}, status)
    except GeoError as error:
        handler.send_json({"ok": False, "error": str(error), "code": error.code}, error.status)
    except (ValueError, TypeError, KeyError, OverflowError):
        handler.send_json({"ok": False, "error": "GEO请求字段无效，请核对格式与版本", "code": "invalid_request"}, 400)
    except Exception:
        handler.send_json({"ok": False, "error": "GEO服务暂时无法完成请求，原始证据保留，请检查本地运行状态", "code": "internal_error"}, 500)
