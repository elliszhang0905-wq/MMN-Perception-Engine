"""BF工厂应用服务：上传、抽取、检索、生成与模型编排。"""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .extraction import PROFILE_RULES, build_tags, classify_bf_profile, extract_brief
from .generation import compose_section_plan, generate_internal_strategy, render_adaptive_brief
from .parsers import parse_document, validate_upload
from .storage import store_document


class BFService:
    def __init__(self, repository, storage_root, model_gateway=None):
        self.repository = repository
        self.storage_root = Path(storage_root)
        self.model_gateway = model_gateway

    def ingest_document(self, *, project_id, org_id, client_key, filename, data, user_id):
        project = self.repository.get_project(project_id, org_id)
        if project["client_key"] != client_key:
            raise PermissionError("BF文件客户范围与项目不一致")
        info = validate_upload(filename, data)
        document_id = _uuid_from("document", project_id, hashlib.sha256(data).hexdigest(), datetime.now(timezone.utc).isoformat())
        storage_path = store_document(
            root=self.storage_root,
            org_id=org_id,
            client_key=client_key,
            project_id=project_id,
            document_id=document_id,
            filename=info["filename"],
            data=data,
        )
        document = self.repository.create_document(
            project_id=project_id,
            org_id=org_id,
            filename=info["filename"],
            extension=info["extension"],
            mime_type=_mime_for(info["extension"]),
            sha256=hashlib.sha256(data).hexdigest(),
            storage_path=str(storage_path),
            size_bytes=len(data),
            uploaded_by=user_id,
        )
        parsed = parse_document(filename, data)
        document = self.repository.save_parse_result(document["id"], project_id, parsed)
        payload = extract_brief(
            parsed["segments"],
            {
                "documentId": document["id"],
                "projectId": project_id,
                "clientKey": client_key,
                "fileName": document["filename"],
                "mimeType": document["mime_type"],
                "checksum": document["sha256"],
                "pageCount": document["page_count"],
                "uploadedAt": document["uploaded_at"],
            },
        )
        payload["extraction"]["warnings"] = parsed.get("warnings") or []
        brief = self.repository.create_brief(
            project_id=project_id,
            source_document_id=document["id"],
            origin_type="UPLOADED",
            bf_type=payload["classification"]["bfType"],
            title=payload["strategy"]["bfName"] or document["filename"],
            structured_payload=payload,
            created_by=user_id,
            status="REVIEW",
        )
        return {"document": document, "brief": brief, "payload": payload, "warnings": parsed.get("warnings") or []}

    def generate_brief(self, request):
        project_id = str(request.get("projectId") or "").strip()
        org_id = str(request.get("orgId") or "").strip()
        client_key = str(request.get("clientKey") or "").strip()
        user_id = str(request.get("userId") or "system").strip()
        project = self.repository.get_project(project_id, org_id)
        if project["client_key"] != client_key:
            raise PermissionError("BF生成条件与项目客户范围不一致")
        redact_before_external = request.get("redactBeforeExternal", True) is not False
        redaction_secrets = _redaction_secrets(request)
        external = lambda value: _redact(value, redaction_secrets) if redact_before_external else value
        direction_text = "\n".join(
            [
                " ".join(_list(request.get("contentDirections"))),
                " ".join(_list(request.get("creatorTypes"))),
                str(request.get("specialRequirements") or ""),
            ]
        )
        inferred = classify_bf_profile([{"text": direction_text}])
        requested_type = str(request.get("bfType") or "AUTO").strip().upper()
        bf_type = inferred["primaryCode"] if requested_type in {"", "AUTO"} else requested_type
        type_label = PROFILE_RULES.get(bf_type, {}).get("label") or inferred["suggestedName"]
        payload = self._payload_from_request(request, project, bf_type, type_label, inferred)
        retrieval = self._retrieve_context(project_id)
        internal = generate_internal_strategy(payload, retrieval["positive"])
        learned_profile = self.repository.find_matching_template_profile(
            payload["classification"].get("contentIntents") or []
        ) if bf_type == "CUSTOM" else None
        run = self.repository.create_generation_run(project_id=project_id, created_by=user_id, input_payload=_redact(request, redaction_secrets), bf_type=bf_type)
        model_trace = []
        errors = {}

        strategy_model, call = self._model_json(
            "DEEPSEEK",
            "STRATEGY_JUDGMENT",
            external({"input": request, "localStrategy": internal}),
            run["id"],
            redact_before_external,
        )
        if call:
            model_trace.append(call)
        if strategy_model:
            for key in internal:
                if key in strategy_model and key not in {"judgmentOrigin", "evidenceRefs"}:
                    internal[key] = strategy_model[key]
        elif self.model_gateway:
            errors["strategy"] = "MMN策略判断模型未返回有效JSON，已使用本地策略推断"

        plan = compose_section_plan(payload, learned_profile)
        rendered = render_adaptive_brief(payload, internal, plan)
        draft_model, call = self._model_json(
            "QWEN",
            "DRAFT",
            external({"structuredBrief": payload, "sectionPlan": plan, "localDraft": rendered["markdown"]}),
            run["id"],
            redact_before_external,
        )
        if call:
            model_trace.append(call)
        if isinstance(draft_model, dict):
            _apply_section_bodies(rendered, draft_model.get("sectionBodies") or {})
        elif self.model_gateway:
            errors["draft"] = "MMN内容生成模型未返回有效章节JSON，已保留结构化本地初稿"

        review, call = self._model_json(
            "DEEPSEEK",
            "RISK_REVIEW",
            external({"draft": rendered["markdown"], "riskRules": payload["risk"], "sourcePointers": list(payload["provenance"])}),
            run["id"],
            redact_before_external,
        )
        if call:
            model_trace.append(call)
        if not isinstance(review, dict):
            review = {"verdict": "needs_review", "findings": ["模型复核不可用，需人工审核"]}
            if self.model_gateway:
                errors["review"] = "MMN质量复核未返回有效JSON"
        payload["extraction"]["modelTrace"] = model_trace
        payload["strategy"]["coreStrategyJudgment"] = str(internal["bestAngle"])
        payload["strategy"]["currentCommunicationProblem"] = str(internal["currentCommunicationProblem"])
        payload["strategy"]["finalContentDirection"] = str(internal["finalDirection"])
        status = "EDITABLE" if self.model_gateway and len(model_trace) == 3 and review.get("verdict") == "pass" else "EDITABLE_DEGRADED"
        brief = self.repository.create_brief(
            project_id=project_id,
            origin_type="GENERATED",
            bf_type=bf_type,
            title=payload["strategy"]["bfName"],
            structured_payload=payload,
            created_by=user_id,
            status="DRAFT",
        )
        self.repository.complete_generation_run(
            run["id"],
            strategy=internal,
            retrieval=retrieval,
            output_brief_id=brief["id"],
            status=status,
            error=errors,
        )
        return {
            "runId": run["id"],
            "status": status,
            "brief": brief,
            "payload": payload,
            "internalStrategy": internal,
            "sectionPlan": plan,
            "sections": rendered["sections"],
            "markdown": rendered["markdown"],
            "review": review,
            "retrieval": retrieval,
            "learnedProfile": _public_template_profile(learned_profile),
            "errors": errors,
        }

    def finalize_brief(self, *, brief_id, project_id, base_version_no, payload, markdown, sample_grade, user_id, outcome, learned_profile_name=""):
        project = self.repository.get_project(project_id, str(outcome.get("orgId") or "") or self._project_org(project_id))
        version = self.repository.save_brief_version(
            brief_id=brief_id,
            project_id=project_id,
            structured_payload=payload,
            rendered_markdown=markdown,
            version_kind="FINAL",
            base_version_no=base_version_no,
            created_by=user_id,
            is_final=True,
        )
        brief = self.repository.update_brief_final_metadata(
            brief_id,
            project_id,
            sample_grade=sample_grade,
            outcome={key: value for key, value in (outcome or {}).items() if key != "orgId"},
        )
        chunks = _knowledge_chunks_from_payload(payload, markdown, sample_grade)
        chunk_count = self.repository.replace_knowledge_chunks(
            project_id=project_id,
            client_key=project["client_key"],
            brief_id=brief_id,
            version_id=version["id"],
            chunks=chunks,
            approved_by=user_id,
        )
        learned_profile = None
        classification = payload.get("classification") or {}
        intents = classification.get("contentIntents") or []
        if classification.get("bfType") == "CUSTOM" and sample_grade == "QUALITY" and intents:
            code = "LEARNED_" + hashlib.sha1((learned_profile_name + "|" + "|".join(intents)).encode("utf-8")).hexdigest()[:10].upper()
            profile_name = _deidentify_profile_name(
                learned_profile_name or classification.get("bfTypeLabel") or "优质自定义BF范式",
                project,
                payload,
            )
            learned_profile = self.repository.save_template_profile(
                code=code,
                name=profile_name,
                section_intents=[
                    item["intent"]
                    for item in compose_section_plan(payload)
                    if item["visibility"] == "DELIVERABLE" and item["intent"] != "SOURCE_APPENDIX"
                ],
                source="FINAL_BF",
                created_by=user_id,
            )
        return {
            "brief": brief,
            "version": version,
            "knowledgeChunkCount": chunk_count,
            "learnedProfile": learned_profile,
        }

    def _project_org(self, project_id):
        # Repository仍会执行最终项目范围校验；这里只读取项目自身的组织ID。
        with self.repository._connect() as conn:
            row = conn.execute("select org_id from bf_projects where id=?", (project_id,)).fetchone()
        if not row:
            from .repository import BFNotFoundError
            raise BFNotFoundError("BF项目不存在")
        return row["org_id"]

    def _payload_from_request(self, request, project, bf_type, type_label, inferred):
        from .schema import new_brief_payload

        payload = new_brief_payload(project["id"], project["client_key"], "generated")
        payload["classification"].update(
            {
                "bfType": bf_type,
                "bfTypeLabel": type_label,
                "confidence": inferred["confidence"] if bf_type == inferred["primaryCode"] else 1.0,
                "reasons": inferred["reasons"],
                "contentIntents": inferred["contentIntents"],
            }
        )
        brand = str(request.get("brand") or project.get("brand") or "").strip()
        model = str(request.get("model") or project.get("model") or "").strip()
        payload["strategy"].update(
            {
                "bfName": str(request.get("bfName") or f"{brand}{model}{type_label}").strip(),
                "bfType": bf_type,
                "brand": brand,
                "model": model,
                "competitors": _list(request.get("competitors")),
                "projectStage": str(request.get("projectStage") or "").strip(),
                "communicationGoals": _list(request.get("communicationGoals")),
                "targetAudience": _list(request.get("targetAudience")),
            }
        )
        payload["content"]["contentDirections"] = _list(request.get("contentDirections"))
        payload["content"]["creatorTypes"] = _list(request.get("creatorTypes"))
        payload["content"]["contentTypes"] = _list(request.get("contentForms"))
        special = str(request.get("specialRequirements") or "").strip()
        if special:
            payload["content"]["topicDirections"].append(special)
        payload["risk"].update(
            {
                "isPriceAllowed": _optional_bool(request.get("isPriceAllowed")),
                "isAdasAllowed": _optional_bool(request.get("isAdasAllowed")),
                "isDynamicDrivingAllowed": _optional_bool(request.get("isDynamicDrivingAllowed")),
                "isCompetitorNameAllowed": _optional_bool(request.get("isCompetitorNameAllowed")),
            }
        )
        payload["summary"] = f"{brand}{model}｜{type_label}｜{'、'.join(payload['strategy']['communicationGoals']) or '商业化内容执行'}"
        for pointer, value in (
            ("/strategy/brand", brand),
            ("/strategy/model", model),
            ("/strategy/competitors", payload["strategy"]["competitors"]),
            ("/strategy/projectStage", payload["strategy"]["projectStage"]),
            ("/strategy/communicationGoals", payload["strategy"]["communicationGoals"]),
            ("/content/contentDirections", payload["content"]["contentDirections"]),
        ):
            if value:
                payload["provenance"][pointer] = [_manual_citation()]
        payload["tags"] = build_tags(payload)
        return payload

    def _retrieve_context(self, project_id):
        positive = []
        for row in self.repository.list_retrieval_candidates(project_id, purpose="POSITIVE")[:8]:
            positive.append({"id": row["id"], "source": row["id"], "title": row["title"], "sample_grade": row["sample_grade"], "bf_type": row["bf_type"]})
        risk = []
        for row in self.repository.list_retrieval_candidates(project_id, purpose="RISK")[:8]:
            risk.append({"id": row["id"], "source": row["id"], "title": row["title"], "sample_grade": row["sample_grade"], "bf_type": row["bf_type"]})
        return {"positive": positive, "risk": risk}

    def _model_json(self, provider, step, request, run_id, redact_before_external=True):
        if not self.model_gateway:
            return None, None
        try:
            raw = self.model_gateway(provider, step, request)
            parsed = _parse_json(raw)
            output_hash = hashlib.sha256(str(raw or "").encode("utf-8")).hexdigest()
            call_id = self.repository.record_model_call(
                run_id=run_id,
                step=step,
                provider=provider,
                model="",
                redaction_mode="DEFAULT_ON" if redact_before_external else "EXPLICIT_OFF",
                redacted_input=_redact(request, _redaction_secrets(request)),
                output_hash=output_hash,
                status="PASS" if parsed is not None else "FAIL",
                error="" if parsed is not None else "INVALID_JSON",
            )
            return parsed, {"step": step, "provider": provider, "model": "", "status": "PASS" if parsed is not None else "FAIL", "callId": call_id}
        except Exception as exc:
            call_id = self.repository.record_model_call(
                run_id=run_id,
                step=step,
                provider=provider,
                model="",
                redaction_mode="DEFAULT_ON" if redact_before_external else "EXPLICIT_OFF",
                redacted_input=_redact(request, _redaction_secrets(request)),
                output_hash="",
                status="FAIL",
                error=type(exc).__name__,
            )
            return None, {"step": step, "provider": provider, "model": "", "status": "FAIL", "callId": call_id}


def _apply_section_bodies(rendered, bodies):
    if not isinstance(bodies, dict):
        return
    allowed = {item["intent"] for item in rendered["sections"]}
    for section in rendered["sections"]:
        value = bodies.get(section["intent"])
        if section["intent"] in allowed and isinstance(value, str) and value.strip():
            section["body"] = value.strip()
    lines = [f"# {rendered['title']}", ""]
    for index, section in enumerate(rendered["sections"], 1):
        lines.extend([f"## {index}. {section['title']}", "", section["body"], ""])
    rendered["markdown"] = "\n".join(lines).strip() + "\n"


def _parse_json(raw):
    if isinstance(raw, dict):
        return raw
    text = str(raw or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I | re.S).strip()
    try:
        value = json.loads(text)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.S)
        if not match:
            return None
        try:
            value = json.loads(match.group(0))
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            return None


def _redaction_secrets(value):
    sensitive_keys = {
        "orgId", "projectId", "clientKey", "userId", "brand", "model", "competitors",
        "budget", "price", "internalPrice", "extractionCode", "contact", "phone", "email",
        "parameters", "officialClaims", "materials", "materialLinks", "sourceLinks",
    }
    secrets = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in sensitive_keys:
                values = item if isinstance(item, list) else [item]
                secrets.extend(str(entry).strip() for entry in values if str(entry).strip())
            secrets.extend(_redaction_secrets(item))
    elif isinstance(value, list):
        for item in value:
            secrets.extend(_redaction_secrets(item))
    return sorted(set(secrets), key=len, reverse=True)


def _redact(value, secrets=None):
    sensitive_keys = {
        "orgId", "projectId", "clientKey", "userId", "brand", "model", "competitors",
        "budget", "price", "internalPrice", "extractionCode", "contact", "phone", "email",
        "parameters", "officialClaims", "materials", "materialLinks", "sourceLinks",
    }
    secrets = secrets or _redaction_secrets(value)
    if isinstance(value, dict):
        return {key: "[REDACTED]" if key in sensitive_keys else _redact(item, secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact(item, secrets) for item in value]
    if isinstance(value, str):
        text = value
        for secret in secrets:
            if len(secret) >= 2:
                text = text.replace(secret, "[SENSITIVE]")
        text = re.sub(r"https?://[^\s，,；;]+", "[URL]", text, flags=re.I)
        text = re.sub(r"(?<!\d)1[3-9]\d{9}(?!\d)", "[PHONE]", text)
        text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)
        text = re.sub(r"(?:提取码|密码)\s*[:：]?\s*[A-Za-z0-9]{4,}", "提取码[REDACTED]", text, flags=re.I)
        text = re.sub(r"(?:内部价|内部价格|预算|报价|底价)\s*[:：]?\s*\d+(?:\.\d+)?\s*(?:万|万元|元)?", "[PRICE]", text)
        return text
    return value


def _deidentify_profile_name(name, project, payload):
    strategy = payload.get("strategy") or {}
    sensitive = [
        project.get("client_key"),
        project.get("brand"),
        project.get("model"),
        strategy.get("brand"),
        strategy.get("model"),
        *(strategy.get("competitors") or []),
    ]
    text = str(name or "").strip()
    for value in sorted({str(item).strip() for item in sensitive if str(item or "").strip()}, key=len, reverse=True):
        text = re.sub(re.escape(value), "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip(" ·|｜_-—")
    return text if len(text) >= 3 else "优质自定义BF范式"


def _public_template_profile(profile):
    if not profile:
        return None
    return {
        "code": profile.get("code"),
        "name": profile.get("name"),
        "section_intents": list(profile.get("section_intents") or []),
        "source": profile.get("source"),
    }


def _manual_citation():
    return {
        "originType": "MANUAL",
        "sourceDocumentId": "",
        "sourceSegmentId": "",
        "sourceLocator": "生成条件",
        "sourceFieldPath": "",
        "excerpt": "用户输入",
        "confidence": 1.0,
        "isManual": True,
    }


def _optional_bool(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    return str(value).lower() in {"1", "true", "yes", "是", "允许"}


def _list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item or "").strip()]
    return [item.strip() for item in re.split(r"[、,，/|｜;；]+", str(value)) if item.strip()]


def _mime_for(extension):
    return {
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".csv": "text/csv",
        ".txt": "text/plain",
        ".md": "text/markdown",
    }.get(extension, "application/octet-stream")


def _uuid_from(*parts):
    import uuid

    return str(uuid.uuid5(uuid.NAMESPACE_URL, ":".join(str(part) for part in parts)))


def _knowledge_chunks_from_payload(payload, markdown, sample_grade):
    strategy = payload.get("strategy") or {}
    product = payload.get("product") or {}
    execution = payload.get("execution") or {}
    risk = payload.get("risk") or {}
    materials = payload.get("materials") or []
    chunks = [
        {
            "assetType": "METHOD",
            "text": "\n".join(filter(None, [payload.get("summary"), strategy.get("coreStrategyJudgment"), strategy.get("finalContentDirection")])),
            "payload": {"bfType": (payload.get("classification") or {}).get("bfType"), "tags": payload.get("tags") or {}},
            "allowPositive": sample_grade in {"QUALITY", "NORMAL"},
        },
        {
            "assetType": "CLIENT_CLAIM",
            "text": "\n".join((product.get("officialClaims") or []) + (product.get("mustSay") or [])),
            "payload": {"sourcePointers": [key for key in (payload.get("provenance") or {}) if key.startswith("/product/")]},
            "allowPositive": sample_grade in {"QUALITY", "NORMAL"},
        },
        {
            "assetType": "SHOOTING_STANDARD",
            "text": "\n".join(item.get("item") or "" for item in execution.get("executionChecklist") or []) + "\n" + "\n".join(execution.get("dynamicMaterialRequirements") or []),
            "payload": {"execution": execution},
            "allowPositive": sample_grade in {"QUALITY", "NORMAL"},
        },
        {
            "assetType": "EXPRESSION_RED_LINE",
            "text": "\n".join((risk.get("prohibitedExpressions") or []) + (risk.get("expressionRedLines") or [])),
            "payload": {"risk": risk},
            "allowPositive": False,
        },
    ]
    if materials:
        chunks.append({"assetType": "MATERIAL_LINK", "text": "\n".join(item.get("name") or "素材" for item in materials), "payload": {"materials": materials}, "allowPositive": False})
    if sample_grade == "NEGATIVE":
        for item in chunks:
            item["allowPositive"] = False
    return [item for item in chunks if item.get("text") or item.get("payload")]
