"""Transactional sampling manifests, leases and attempt-level accounting."""
from datetime import datetime, timezone
import json
import time

from .store import GeoError, day_key, decoded, dumps, fingerprint, integer, money_micro, stamp, text_value, uid

TERMINAL = {"completed", "failed", "refused", "empty", "uncertain", "cancelled", "unanalysable"}


class JobMixin:
    def _freeze(self, conn, org, project_id, payload):
        project = self._get(conn, "geo_project", org, project_id)
        questions, conditions = [], []
        for field, table, target in [("question_version_ids", "geo_question_version", questions), ("condition_ids", "geo_condition", conditions)]:
            entries = payload.get(field)
            if not isinstance(entries, list) or not entries or len(entries) > (50 if field == "question_version_ids" else 8) or len(set(entries)) != len(entries):
                raise GeoError("问题或条件清单为空、重复或超限")
            for ident in entries:
                if not isinstance(ident, str): raise GeoError("关联标识格式错误")
                target.append(self._get(conn, table, org, ident, project_id))
        repeats = integer(payload.get("repeats", 3), "重复次数", 1, project["budget"]["max_repeats"])
        if len(questions) > project["budget"]["max_questions"] or len(questions) * len(conditions) * repeats > 1000:
            raise GeoError("单批次问题或观测超过项目配额")
        manual = [x["surface"] == "doubao_app_manual" for x in conditions]
        if any(manual) and not all(manual): raise GeoError("人工App样本请使用独立批次，与API渠道并列对照")
        return {"project_id": project_id, "questions": questions, "conditions": conditions, "repeats": repeats,
                "entities": project["entities"], "target_key": project["target_key"], "budget": project["budget"],
                "facts": self.latest_facts(conn, org, project_id),
                "question_set_hash": fingerprint(sorted(x["id"] for x in questions)),
                "entity_set_hash": fingerprint(project["entities"]), "frozen_at": stamp(), "manual": all(manual)}

    def _daily(self, conn, org, project, day, currency):
        conn.execute("INSERT OR IGNORE INTO geo_daily_budget(org_id,project_id,day,currency) VALUES(?,?,?,?)", (org, project, day, currency))
        return conn.execute("SELECT * FROM geo_daily_budget WHERE org_id=? AND project_id=? AND day=? AND currency=?", (org, project, day, currency)).fetchone()

    def _reserve(self, conn, org, project, day, currency, amount, budget):
        row = self._daily(conn, org, project, day, currency)
        if row["reserved_micro"] + row["spent_micro"] + amount > money_micro(budget):
            raise GeoError("项目日预算不足（包含并发任务预留与未知费用）", "budget_exhausted", 409)
        conn.execute("UPDATE geo_daily_budget SET reserved_micro=reserved_micro+? WHERE org_id=? AND project_id=? AND day=? AND currency=?", (amount, org, project, day, currency))

    def _create_batch(self, conn, org, project, payload, policy, actor="local", frozen=None):
        key = text_value(payload.get("idempotency_key"), "幂等标识", 160, True)
        normalized = {x: payload.get(x) for x in ("question_version_ids", "condition_ids", "repeats")}
        normalized["repeats"] = normalized["repeats"] if normalized["repeats"] is not None else 3
        request_hash = fingerprint(normalized)
        existing = conn.execute("SELECT * FROM geo_batch WHERE org_id=? AND project_id=? AND idempotency_key=?", (org, project, key)).fetchone()
        if existing:
            if existing["request_hash"] != request_hash: raise GeoError("同一幂等标识不能对应不同试验清单", "idempotency_conflict", 409)
            return decoded(existing)["id"]
        current_project = self._get(conn, "geo_project", org, project)
        manifest = json.loads(dumps(frozen)) if frozen is not None else self._freeze(conn, org, project, payload)
        if frozen is not None:
            manifest["budget"] = current_project["budget"]
            if len(manifest["questions"]) > manifest["budget"]["max_questions"] or manifest["repeats"] > manifest["budget"]["max_repeats"]:
                raise GeoError("关联新采样超过当前项目问题或重复配额")
        manual = manifest["manual"]
        reserve = int(policy.get("attempt_reserve_micro") or 0)
        attempts = integer(policy.get("max_attempts", 3), "最大尝试数", 1, 3)
        planned = len(manifest["questions"]) * len(manifest["conditions"]) * manifest["repeats"]
        queue = bool(policy.get("queue_allowed")) and not manual
        total = planned * reserve * attempts if queue else 0
        if queue and (reserve <= 0 or total > money_micro(manifest["budget"]["batch_budget"])):
            raise GeoError("批次预算不足或未配置可用调用成本上界", "budget_exhausted", 409)
        day, currency = day_key(), policy.get("currency", "CNY")
        if queue: self._reserve(conn, org, project, day, currency, total, manifest["budget"]["day_budget"])
        manifest.update({"max_attempts": attempts, "attempt_reserve_micro": reserve, "currency": currency,
                         "pricing": policy.get("pricing"), "blocked_reasons": [] if manual else policy.get("blocked_reasons", []),
                         "estimated_cost": (planned * reserve / 1000000) if queue else (0 if manual else None),
                         "max_reserved_cost": total / 1000000 if queue else (0 if manual else None)})
        ident, now = uid("batch"), stamp()
        self._insert(conn, "geo_batch", {"id": ident, "org_id": org, "project_id": project, "idempotency_key": key,
            "request_hash": request_hash, "status": "draft" if manual else ("queued" if queue else "blocked"),
            "manifest_json": dumps(manifest), "budget_day": day, "reserved_micro": total, "created_at": now, "updated_at": now})
        for question in manifest["questions"]:
            for condition in manifest["conditions"]:
                for repeat in range(1, manifest["repeats"] + 1):
                    self._insert(conn, "geo_observation", {"id": uid("observation"), "org_id": org, "project_id": project,
                        "batch_id": ident, "question_version_id": question["id"], "condition_id": condition["id"],
                        "repeat_index": repeat, "status": "draft" if manual else "queued", "channel": condition["surface"], "created_at": now})
        self._audit(conn, org, project, "batch_created", ident, actor, {"planned_calls": planned, "manifest_hash": fingerprint(manifest), "status": "draft" if manual else ("queued" if queue else "blocked")})
        return ident

    def create_batch(self, org, project_id, payload, policy=None, actor="local"):
        with self.connect(True) as conn:
            ident = self._create_batch(conn, org, project_id, payload, policy or {}, actor)
        return self.get_batch(org, ident)

    def _batch_summary(self, conn, batch):
        org, ident = batch["org_id"], batch["id"]
        counts = dict(conn.execute("SELECT status,count(*) FROM geo_observation WHERE org_id=? AND batch_id=? GROUP BY status", (org, ident)).fetchall())
        money = conn.execute("SELECT sum(a.cost_micro),sum(CASE WHEN a.cost_micro IS NULL OR a.billing_uncertain=1 THEN 1 ELSE 0 END) FROM geo_attempt a JOIN geo_observation o ON o.org_id=a.org_id AND o.id=a.observation_id WHERE o.org_id=? AND o.batch_id=?", (org, ident)).fetchone()
        batch.update({"paused": bool(batch["paused"]), "total_count": sum(counts.values()),
                      "done_count": sum(n for state, n in counts.items() if state in TERMINAL), "error_summary": counts,
                      "cost": (money[0] or 0) / 1000000 if money[1] == 0 else (money[0] / 1000000 if money[0] is not None else None),
                      "unknown_cost_items": money[1] or 0, "estimated_cost": batch["manifest"]["estimated_cost"],
                      "max_reserved_cost": batch["manifest"]["max_reserved_cost"],
                      "currency": batch["manifest"]["currency"],
                      "uncertain_observation_ids": [r[0] for r in conn.execute("SELECT id FROM geo_observation WHERE org_id=? AND batch_id=? AND status='uncertain'", (org, ident))]})
        return batch

    def get_batch(self, org, batch_id):
        with self.connect() as conn:
            return self._batch_summary(conn, self._get(conn, "geo_batch", org, batch_id))

    def list_batches(self, org, project_id, limit=20, offset=0):
        with self.connect() as conn:
            self._get(conn, "geo_project", org, project_id)
            result = self._page(conn, "geo_batch", org, project_id, limit, offset)
            result["items"] = [self._batch_summary(conn, x) for x in result["items"]]
            return result

    def _finalize(self, conn, org, batch_id):
        batch = self._get(conn, "geo_batch", org, batch_id)
        statuses = [r[0] for r in conn.execute("SELECT status FROM geo_observation WHERE org_id=? AND batch_id=?", (org, batch_id))]
        if any(x not in TERMINAL for x in statuses) and batch["status"] != "cancelled": return
        state = "cancelled" if batch["status"] == "cancelled" else ("completed" if all(x == "completed" for x in statuses) else "completed_with_errors")
        inflight = conn.execute("SELECT coalesce(sum(a.reserved_micro),0) FROM geo_attempt a JOIN geo_observation o ON o.org_id=a.org_id AND o.id=a.observation_id WHERE o.org_id=? AND o.batch_id=? AND a.status='running'", (org, batch_id)).fetchone()[0]
        release = max(0, batch["reserved_micro"] - inflight)
        if release:
            conn.execute("UPDATE geo_daily_budget SET reserved_micro=reserved_micro-? WHERE org_id=? AND project_id=? AND day=? AND currency=?", (release, org, batch["project_id"], batch["budget_day"], batch["manifest"]["currency"]))
        conn.execute("UPDATE geo_batch SET status=?,reserved_micro=?,updated_at=? WHERE org_id=? AND id=?", (state, inflight, stamp(), org, batch_id))
        if state != batch["status"]: self._audit(conn, org, batch["project_id"], "batch_state_changed", batch_id, "worker", {"status": state})

    def _settle(self, conn, observation, attempt, result):
        org, project = observation["org_id"], observation["project_id"]
        batch = self._get(conn, "geo_batch", org, observation["batch_id"])
        reserve = attempt["reserved_micro"]
        known = money_micro(result["cost"]) if result.get("cost") is not None else None
        uncertain = bool(result.get("billing_uncertain")) or known is None
        held = max(0, reserve - (known or 0)) if uncertain else 0
        released = reserve - held
        conn.execute("UPDATE geo_daily_budget SET reserved_micro=reserved_micro-?,spent_micro=spent_micro+? WHERE org_id=? AND project_id=? AND day=? AND currency=?", (released, known or 0, org, project, attempt["budget_day"], batch["manifest"]["currency"]))
        conn.execute("UPDATE geo_batch SET reserved_micro=reserved_micro-?,held_micro=held_micro+? WHERE org_id=? AND id=?", (reserve, held, org, batch["id"]))
        if known is not None and known > reserve:
            conn.execute("UPDATE geo_batch SET paused=1 WHERE org_id=? AND id=?", (org, batch["id"]))
            self._audit(conn, org, project, "cost_envelope_exceeded", batch["id"], "worker", {"attempt_id": attempt["id"], "reserve_micro": reserve, "cost_micro": known})
        return known, uncertain

    def claim_next(self, owner, now_epoch=None, lease_seconds=180, global_concurrency=None):
        owner = text_value(owner, "worker身份", 160, True)
        epoch = time.time() if now_epoch is None else now_epoch
        with self.connect(True) as conn:
            stale = conn.execute("SELECT * FROM geo_observation WHERE status='running' AND lease_expires<?", (epoch,)).fetchall()
            for row in stale:
                obs = decoded(row)
                attempt_row = conn.execute("SELECT * FROM geo_attempt WHERE org_id=? AND observation_id=? AND status='running' ORDER BY attempt_index DESC LIMIT 1", (obs["org_id"], obs["id"])).fetchone()
                if attempt_row:
                    attempt = decoded(attempt_row)
                    self._settle(conn, obs, attempt, {"cost": None, "billing_uncertain": True})
                    conn.execute("UPDATE geo_attempt SET status='uncertain',billing_uncertain=1,finished_at=?,payload_json=? WHERE org_id=? AND id=?", (stamp(), dumps({"error_class": "timeout", "error": "worker租约过期，调用是否完成未知"}), obs["org_id"], attempt["id"]))
                conn.execute("UPDATE geo_observation SET status='uncertain',lease_owner=NULL,lease_expires=NULL WHERE org_id=? AND id=?", (obs["org_id"], obs["id"]))
                self._audit(conn, obs["org_id"], obs["project_id"], "inflight_became_uncertain", obs["id"], "worker")
                self._finalize(conn, obs["org_id"], obs["batch_id"])
            candidates = conn.execute("SELECT o.* FROM geo_observation o JOIN geo_batch b ON b.org_id=o.org_id AND b.id=o.batch_id WHERE o.status='queued' AND o.next_attempt_at<=? AND b.status IN ('queued','running') AND b.paused=0 ORDER BY b.created_at,o.id LIMIT 100", (epoch,)).fetchall()
            for row in candidates:
                obs = decoded(row); org, project = obs["org_id"], obs["project_id"]
                batch = self._get(conn, "geo_batch", org, obs["batch_id"], project)
                manifest = batch["manifest"]
                # Project limits are read at execution; reducing concurrency takes effect immediately.
                current = self._get(conn, "geo_project", org, project)
                active = conn.execute("SELECT count(*) FROM geo_observation WHERE org_id=? AND project_id=? AND status='running'", (org, project)).fetchone()[0]
                concurrency = min(current["budget"]["max_concurrency"], global_concurrency) if global_concurrency else current["budget"]["max_concurrency"]
                if active >= concurrency: continue
                day = day_key()
                if day != batch["budget_day"]:
                    inflight = conn.execute("SELECT coalesce(sum(a.reserved_micro),0) FROM geo_attempt a JOIN geo_observation o ON o.org_id=a.org_id AND o.id=a.observation_id WHERE o.org_id=? AND o.batch_id=? AND a.status='running'", (org, batch["id"])).fetchone()[0]
                    moving = max(0, batch["reserved_micro"] - inflight)
                    try:
                        self._reserve(conn, org, project, day, manifest["currency"], moving, current["budget"]["day_budget"])
                    except GeoError:
                        conn.execute("UPDATE geo_batch SET status='blocked' WHERE org_id=? AND id=?", (org, batch["id"]))
                        self._audit(conn, org, project, "day_budget_blocked", batch["id"], "worker")
                        continue
                    conn.execute("UPDATE geo_daily_budget SET reserved_micro=reserved_micro-? WHERE org_id=? AND project_id=? AND day=? AND currency=?", (moving, org, project, batch["budget_day"], manifest["currency"]))
                    conn.execute("UPDATE geo_batch SET budget_day=? WHERE org_id=? AND id=?", (day, org, batch["id"]))
                daily = self._daily(conn, org, project, day, manifest["currency"])
                if daily["spent_micro"] + daily["reserved_micro"] > money_micro(current["budget"]["day_budget"]):
                    conn.execute("UPDATE geo_batch SET status='blocked',paused=1 WHERE org_id=? AND id=?", (org, batch["id"]))
                    self._audit(conn, org, project, "project_day_budget_exhausted", batch["id"], "worker")
                    continue
                question = next(x for x in manifest["questions"] if x["id"] == obs["question_version_id"])
                condition = next(x for x in manifest["conditions"] if x["id"] == obs["condition_id"])
                attempt_index = conn.execute("SELECT count(*) FROM geo_attempt WHERE org_id=? AND observation_id=?", (org, obs["id"])).fetchone()[0] + 1
                if attempt_index > manifest["max_attempts"]: continue
                attempt_id = uid("attempt")
                self._insert(conn, "geo_attempt", {"id": attempt_id, "org_id": org, "project_id": project, "observation_id": obs["id"], "attempt_index": attempt_index, "status": "running", "budget_day": day, "reserved_micro": manifest["attempt_reserve_micro"], "started_at": stamp()})
                duration = max(lease_seconds, condition.get("timeout_seconds", 60) + 30) if now_epoch is None else lease_seconds
                conn.execute("UPDATE geo_observation SET status='running',lease_owner=?,lease_expires=? WHERE org_id=? AND id=?", (owner, epoch + duration, org, obs["id"]))
                conn.execute("UPDATE geo_batch SET status='running',updated_at=? WHERE org_id=? AND id=?", (stamp(), org, batch["id"]))
                self._audit(conn, org, project, "attempt_started", attempt_id, owner, {"observation_id": obs["id"], "attempt_index": attempt_index})
                return {"observation": obs, "question": question, "condition": condition, "manifest": manifest, "attempt_id": attempt_id}
        return None

    def dispatch_allowed(self, org, observation_id, owner):
        with self.connect() as conn:
            row = conn.execute("SELECT b.status,b.paused,o.status observation_status,o.lease_owner FROM geo_observation o JOIN geo_batch b ON b.org_id=o.org_id AND b.id=o.batch_id WHERE o.org_id=? AND o.id=?", (org, observation_id)).fetchone()
            return bool(row and row["status"] in {"queued", "running"} and not row["paused"] and row["observation_status"] == "running" and row["lease_owner"] == owner)

    def finish_attempt(self, org, observation_id, owner, result, analysis=None, retry_delay=2):
        with self.connect(True) as conn:
            obs = self._get(conn, "geo_observation", org, observation_id)
            if obs["status"] != "running" or obs["lease_owner"] != owner:
                raise GeoError("调用租约已失效，不能覆盖原始证据", "lease_conflict", 409)
            attempt = decoded(conn.execute("SELECT * FROM geo_attempt WHERE org_id=? AND observation_id=? AND status='running' ORDER BY attempt_index DESC LIMIT 1", (org, observation_id)).fetchone())
            batch = self._get(conn, "geo_batch", org, obs["batch_id"])
            state = result.get("status", "failed")
            if state not in TERMINAL: raise GeoError("提供方状态不合法")
            known, uncertain = self._settle(conn, obs, attempt, result)
            raw = result.get("raw_response")
            raw_text = dumps(raw) if raw is not None else None
            info = {x: result.get(x) for x in ("usage", "error_class", "error", "retry_after", "search_requested", "search_observed", "actual_model", "capabilities", "started_at", "finished_at", "analysis_error")}
            conn.execute("UPDATE geo_attempt SET status=?,payload_json=?,request_id=?,raw_json=?,raw_hash=?,cost_micro=?,billing_uncertain=?,finished_at=? WHERE org_id=? AND id=?", (state, dumps(info), result.get("request_id"), raw_text, fingerprint(raw) if raw is not None else None, known, int(uncertain), stamp(), org, attempt["id"]))
            retry = state == "failed" and result.get("error_class") in {"rate_limit", "provider_error"} and not result.get("billing_uncertain") and attempt["attempt_index"] < batch["manifest"]["max_attempts"] and batch["status"] != "cancelled"
            final_state = "queued" if retry else state
            if state == "completed" and analysis is not None and not analysis.get("valid_answer"):
                final_state = "refused" if analysis.get("refusal") else "unanalysable"
            answer = result.get("answer") or ""
            evidence_raw = raw_text if state in {"completed", "refused", "empty", "unanalysable", "uncertain"} else None
            observation_info = {**info, "request_id": result.get("request_id")}
            conn.execute("UPDATE geo_observation SET status=?,answer=?,payload_json=?,raw_json=?,raw_hash=?,analysis_json=?,lease_owner=NULL,lease_expires=NULL,next_attempt_at=?,sampled_at=? WHERE org_id=? AND id=?", (final_state, answer, dumps(observation_info), evidence_raw, fingerprint(raw) if evidence_raw is not None else None, dumps(analysis) if analysis is not None else None, time.time() + max(float(result.get("retry_after") or 0), retry_delay) if retry else 0, result.get("finished_at") or stamp(), org, observation_id))
            for citation in result.get("citations") or []:
                self._insert(conn, "geo_citation", {"id": uid("citation"), "org_id": org, "project_id": obs["project_id"], "observation_id": observation_id, "payload_json": dumps(citation), "created_at": stamp()})
            self._audit(conn, org, obs["project_id"], "attempt_finished", attempt["id"], owner, {"status": state, "observation_status": final_state, "cost_unknown": uncertain})
            self._finalize(conn, org, batch["id"])
        return self.get_observation(org, observation_id)

    def control_batch(self, org, batch_id, command, actor="local", observation_id=None, reason="", policy=None):
        output_id = batch_id
        with self.connect(True) as conn:
            batch = self._get(conn, "geo_batch", org, batch_id)
            if command == "cancel":
                conn.execute("UPDATE geo_batch SET status='cancelled',paused=1 WHERE org_id=? AND id=?", (org, batch_id))
                conn.execute("UPDATE geo_observation SET status='cancelled' WHERE org_id=? AND batch_id=? AND status IN ('queued','draft')", (org, batch_id))
                self._finalize(conn, org, batch_id)
            elif command == "pause":
                conn.execute("UPDATE geo_batch SET paused=1 WHERE org_id=? AND id=?", (org, batch_id))
            elif command == "resume":
                if batch["status"] in {"cancelled", "completed", "completed_with_errors"}: raise GeoError("终态批次不能直接继续")
                if batch["status"] == "blocked": raise GeoError("阻塞计划需核查配置后创建新批次，原条件保留")
                conn.execute("UPDATE geo_batch SET paused=0 WHERE org_id=? AND id=?", (org, batch_id))
            elif command in {"retry", "resolve_uncertain"}:
                if not policy or not policy.get("queue_allowed"): raise GeoError("真实调用权限、配置或额度尚未满足", "sampling_blocked", 409)
                reason = text_value(reason, "重新采样原因", 1000, True)
                if batch["status"] == "cancelled": raise GeoError("已取消批次请新建关联复测")
                wanted = "uncertain" if command == "resolve_uncertain" else "failed"
                rows = conn.execute("SELECT * FROM geo_observation WHERE org_id=? AND batch_id=? AND status=?" + (" AND id=?" if observation_id else ""), [org, batch_id, wanted, *([observation_id] if observation_id else [])]).fetchall()
                if command == "resolve_uncertain" and not observation_id: raise GeoError("未知观测须逐条人工确认")
                if not rows: raise GeoError("没有符合条件的观测")
                if command == "resolve_uncertain":
                    observation = decoded(rows[0])
                    manifest = json.loads(dumps(batch["manifest"]))
                    manifest["questions"] = [x for x in manifest["questions"] if x["id"] == observation["question_version_id"]]
                    manifest["conditions"] = [x for x in manifest["conditions"] if x["id"] == observation["condition_id"]]
                    manifest.update({"repeats": 1, "linked_observation_id": observation_id,
                                     "resample_reason": reason, "frozen_at": stamp(),
                                     "question_set_hash": fingerprint([observation["question_version_id"]])})
                    request = {"question_version_ids": [observation["question_version_id"]], "condition_ids": [observation["condition_id"]], "repeats": 1,
                               "idempotency_key": "resample:" + fingerprint({"observation": observation_id, "reason": reason})}
                    output_id = self._create_batch(conn, org, batch["project_id"], request, policy, actor, frozen=manifest)
                else:
                    manifest = batch["manifest"]
                    for row in rows:
                        attempts = conn.execute("SELECT count(*) FROM geo_attempt WHERE org_id=? AND observation_id=?", (org, row["id"])).fetchone()[0]
                        if attempts >= manifest["max_attempts"]: raise GeoError("该观测已达到尝试上限，请创建关联新试验")
                    needed = 0
                    selected_ids = {row["id"] for row in rows}
                    for row in conn.execute("SELECT id,status FROM geo_observation WHERE org_id=? AND batch_id=?", (org, batch_id)):
                        if row["status"] in {"queued", "running"} or row["id"] in selected_ids:
                            attempts = conn.execute("SELECT count(*) FROM geo_attempt WHERE org_id=? AND observation_id=?", (org, row["id"])).fetchone()[0]
                            needed += (manifest["max_attempts"] - attempts + int(row["status"] == "running")) * manifest["attempt_reserve_micro"]
                    additional = max(0, needed - batch["reserved_micro"])
                    project = self._get(conn, "geo_project", org, batch["project_id"])
                    spent = conn.execute("SELECT coalesce(sum(a.cost_micro),0) FROM geo_attempt a JOIN geo_observation o ON o.org_id=a.org_id AND o.id=a.observation_id WHERE o.org_id=? AND o.batch_id=?", (org, batch_id)).fetchone()[0]
                    if spent + batch["held_micro"] + needed > money_micro(project["budget"]["batch_budget"]): raise GeoError("失败续跑超出批次预算")
                    day = batch["budget_day"]
                    self._reserve(conn, org, batch["project_id"], day, manifest["currency"], additional, project["budget"]["day_budget"])
                    conn.execute("UPDATE geo_batch SET status='queued',paused=0,reserved_micro=reserved_micro+? WHERE org_id=? AND id=?", (additional, org, batch_id))
                    for row in rows:
                        conn.execute("UPDATE geo_observation SET status='queued',next_attempt_at=0 WHERE org_id=? AND id=?", (org, row["id"]))
            else: raise GeoError("任务控制指令错误")
            self._audit(conn, org, batch["project_id"], "batch_" + command, batch_id, actor, {"reason": reason, "linked_batch_id": output_id if output_id != batch_id else None})
        return self.get_batch(org, output_id)

    def _observation_detail(self, conn, obs):
        org = obs["org_id"]
        batch = self._get(conn, "geo_batch", org, obs["batch_id"])
        obs["question"] = next(x for x in batch["manifest"]["questions"] if x["id"] == obs["question_version_id"])
        obs["condition"] = next(x for x in batch["manifest"]["conditions"] if x["id"] == obs["condition_id"])
        obs["question_set_hash"] = batch["manifest"]["question_set_hash"]
        obs["facts"] = batch["manifest"]["facts"]
        obs["fact_baseline_hash"] = fingerprint(batch["manifest"]["facts"])
        obs["entity_set_hash"] = batch["manifest"]["entity_set_hash"]
        obs["frozen_target_key"] = batch["manifest"]["target_key"]
        obs["frozen_entity_keys"] = [x["key"] for x in batch["manifest"]["entities"]]
        obs["entities"] = batch["manifest"]["entities"]
        obs["fixed_question_ids"] = [x["id"] for x in batch["manifest"]["questions"]]
        obs["citations"] = [decoded(x) for x in conn.execute("SELECT * FROM geo_citation WHERE org_id=? AND observation_id=? ORDER BY created_at,id", (org, obs["id"]))]
        obs["attempts"] = [decoded(x) for x in conn.execute("SELECT * FROM geo_attempt WHERE org_id=? AND observation_id=? ORDER BY attempt_index", (org, obs["id"]))]
        for attempt in obs["attempts"]:
            attempt["billing_uncertain"] = bool(attempt["billing_uncertain"])
            attempt["cost"] = attempt["cost_micro"] / 1000000 if attempt["cost_micro"] is not None else None
            attempt["cost_unknown"] = attempt["cost"] is None or attempt["billing_uncertain"]
        obs["reviews"] = [decoded(x) for x in conn.execute("SELECT * FROM geo_review WHERE org_id=? AND observation_id=? ORDER BY created_at,id", (org, obs["id"]))]
        obs["screenshots"] = [dict(x) for x in conn.execute("SELECT id,mime,sha256 FROM geo_screenshot WHERE org_id=? AND observation_id=?", (org, obs["id"]))]
        obs["reviewed"] = bool(obs["reviews"])
        return obs

    def get_observation(self, org, ident):
        with self.connect() as conn:
            return self._observation_detail(conn, self._get(conn, "geo_observation", org, ident))

    def list_observations(self, org, project_id, limit=20, offset=0, batch_id=None, channel=None, status=None, search="", condition_hash=None):
        with self.connect() as conn:
            self._get(conn, "geo_project", org, project_id)
            extra, args = "", []
            if batch_id: self._get(conn, "geo_batch", org, batch_id, project_id)
            for key, value in [("batch_id", batch_id), ("channel", channel), ("status", status)]:
                if value: extra += f" AND {key}=?"; args.append(text_value(value, key, 160))
            if search: extra += " AND instr(answer,?)>0"; args.append(text_value(search, "搜索", 300))
            if condition_hash:
                extra += " AND condition_id IN (SELECT id FROM geo_condition WHERE org_id=? AND project_id=? AND condition_hash=?)"; args.extend([org, project_id, condition_hash])
            page = self._page(conn, "geo_observation", org, project_id, limit, offset, extra, args)
            page["items"] = [self._observation_detail(conn, x) for x in page["items"]]
            return page
