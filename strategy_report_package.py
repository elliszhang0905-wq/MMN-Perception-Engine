"""Read-only cockpit snapshot and Codex handoff package export.

This module never recalculates MMN business metrics.  It freezes already
available cockpit data, gives the identical immutable payload to three blind
review channels, applies a deterministic evidence gate, and creates a ZIP
handoff package.  Provider identity stays outside every public/exported value.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
import zipfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timezone
from io import BytesIO

from mmn_model_governance import GOVERNANCE_VERSION, INDEPENDENCE_PROTOCOL, evidence_packet_fingerprint


PUBLIC_CHANNELS = ("独立整理A", "独立整理B", "独立整理C")
INTERNAL_ROLES = ("reasoning_lead", "business_editor", "evidence_auditor")
TOPICS = {
    "consumer_cognition", "competitive_position", "communication_efficiency",
    "product_evidence", "sales_observation", "strategy_execution",
}
STANCES = {"repair", "protect", "amplify", "monitor", "insufficient_evidence"}
SOURCE_TYPES = {"real", "user_imported", "cache", "demo", "degraded", "unknown"}


def utcnow():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _text(value, limit=2000):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(r"qwen|千问|deepseek|kimi|openai|chatgpt|tikhub", "MMN能力", text, flags=re.I)
    return text[:limit]


def _list(value, limit=30):
    return list(value)[:limit] if isinstance(value, list) else []


def _required(value, label):
    text = _text(value, 240)
    if not text:
        raise ValueError(f"缺少当前{label}，不能生成跨范围资料包")
    return text


def init_schema(conn):
    conn.executescript(
        """
        create table if not exists strategy_report_snapshots (
          id text primary key,
          org_id text not null,
          user_id text not null,
          edition text not null,
          project_id text not null,
          project text not null,
          brand text not null,
          model text not null,
          time_start text not null default '',
          time_end text not null default '',
          evidence_fingerprint text not null,
          snapshot_json text not null,
          created_at text not null
        );
        create unique index if not exists idx_strategy_report_snapshot_scope_fingerprint
          on strategy_report_snapshots(org_id, edition, project_id, model, evidence_fingerprint);
        create table if not exists strategy_report_packages (
          id text primary key,
          snapshot_id text not null,
          org_id text not null,
          version integer not null,
          status text not null,
          synthesis_json text not null,
          filename text not null,
          zip_bytes blob not null,
          created_at text not null,
          unique(snapshot_id, version),
          foreign key(snapshot_id) references strategy_report_snapshots(id)
        );
        """
    )


def _scope(body, org_id, edition):
    scope = dict((body or {}).get("scope") or {})
    project = _required(scope.get("project"), "项目")
    brand = _required(scope.get("brand"), "品牌")
    model = _required(scope.get("model"), "车型")
    project_id = _text(scope.get("projectId") or scope.get("project_id"), 240)
    if not project_id:
        project_id = "project-" + hashlib.sha256(f"{org_id}|{edition}|{project}".encode()).hexdigest()[:16]
    time_range = dict(scope.get("timeRange") or {})
    return {
        "orgId": str(org_id), "edition": str(edition), "projectId": project_id,
        "project": project, "brand": brand, "model": model,
        "timeStart": _text(time_range.get("start"), 40),
        "timeEnd": _text(time_range.get("end"), 40),
        "timeLabel": _text(time_range.get("label"), 200) or "当前证据时间范围未知",
        "tCycle": deepcopy(scope.get("tCycle") or {}),
        "cockpitVersion": _text(scope.get("cockpitVersion"), 120) or "unknown",
    }


def _source_type(value):
    value = _text(value, 60).lower()
    return value if value in SOURCE_TYPES else "unknown"


def _sanitize_sources(value):
    if isinstance(value, dict):
        cleaned = {str(key): _sanitize_sources(item) for key, item in value.items()}
        for key in list(cleaned):
            if key.lower() in {"provider", "modelprovider", "vendor", "plugin", "serviceprovider"}:
                cleaned.pop(key, None)
        if "sourceType" in cleaned:
            cleaned["sourceType"] = _source_type(cleaned["sourceType"])
        return cleaned
    if isinstance(value, list):
        return [_sanitize_sources(item) for item in value]
    return _text(value, 20000) if isinstance(value, str) else value


def _snapshot_evidence_payload(scope, body, server_data):
    return {
        "scope": scope,
        "moduleData": _sanitize_sources((body or {}).get("moduleData") or {}),
        "chartData": _sanitize_sources((body or {}).get("chartData") or {}),
        "evidence": _sanitize_sources((body or {}).get("evidence") or {}),
        "decisions": _sanitize_sources((body or {}).get("decisions") or {}),
        "moduleStatuses": _sanitize_sources((body or {}).get("moduleStatuses") or {}),
        "serverData": _sanitize_sources(server_data or {}),
    }


def create_or_reuse_snapshot(conn, body, *, org_id, user_id, edition, mmn_version, server_data=None):
    init_schema(conn)
    scope = _scope(body, org_id, edition)
    evidence_payload = _snapshot_evidence_payload(scope, body, server_data)
    fingerprint = evidence_packet_fingerprint(evidence_payload)
    existing = conn.execute(
        """select * from strategy_report_snapshots
           where org_id=? and edition=? and project_id=? and model=? and evidence_fingerprint=? limit 1""",
        (scope["orgId"], scope["edition"], scope["projectId"], scope["model"], fingerprint),
    ).fetchone()
    if existing:
        result = json.loads(existing["snapshot_json"])
        result["reused"] = True
        return result
    created_at = utcnow()
    snapshot_id = "srp-" + uuid.uuid4().hex
    snapshot = {
        "schemaVersion": "mmn-strategy-report-snapshot-v1",
        "snapshotId": snapshot_id,
        "immutable": True,
        "orgId": scope["orgId"],
        "projectId": scope["projectId"],
        "project": scope["project"],
        "brand": scope["brand"],
        "model": scope["model"],
        "edition": scope["edition"],
        "dataStart": scope["timeStart"],
        "dataEnd": scope["timeEnd"],
        "dataTimeRange": scope["timeLabel"],
        "tCycle": scope["tCycle"],
        "generatedAt": created_at,
        "mmnVersion": _text(mmn_version, 120) or "unknown",
        "cockpitVersion": scope["cockpitVersion"],
        "governanceVersion": GOVERNANCE_VERSION,
        "evidenceFingerprint": fingerprint,
        "includedScope": {
            "orgId": scope["orgId"], "projectId": scope["projectId"], "brand": scope["brand"],
            "model": scope["model"], "edition": scope["edition"], "dataTimeRange": scope["timeLabel"],
        },
        "moduleStatuses": evidence_payload["moduleStatuses"],
        "sourceTypeLegend": {
            "real": "已核验真实来源", "user_imported": "用户导入", "cache": "缓存",
            "demo": "演示", "degraded": "降级", "unknown": "未知",
        },
        "moduleData": evidence_payload["moduleData"],
        "chartData": evidence_payload["chartData"],
        "evidence": evidence_payload["evidence"],
        "decisions": evidence_payload["decisions"],
        "serverData": evidence_payload["serverData"],
        "reused": False,
    }
    conn.execute(
        """insert into strategy_report_snapshots
        (id,org_id,user_id,edition,project_id,project,brand,model,time_start,time_end,evidence_fingerprint,snapshot_json,created_at)
        values (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (snapshot_id, scope["orgId"], str(user_id), scope["edition"], scope["projectId"], scope["project"],
         scope["brand"], scope["model"], scope["timeStart"], scope["timeEnd"], fingerprint,
         json.dumps(snapshot, ensure_ascii=False), created_at),
    )
    conn.commit()
    return snapshot


def get_snapshot(conn, snapshot_id, *, org_id):
    row = conn.execute(
        "select snapshot_json from strategy_report_snapshots where id=? and org_id=?",
        (str(snapshot_id), str(org_id)),
    ).fetchone()
    return json.loads(row[0]) if row else None


def _walk_evidence(value, context=None):
    context = dict(context or {})
    if isinstance(value, dict):
        next_context = {
            **context,
            "time": value.get("timeWindow") or value.get("timeRange") or value.get("createdAt") or context.get("time"),
            "status": value.get("evidenceStatus") or value.get("status") or context.get("status"),
            "sourceType": value.get("sourceType") or context.get("sourceType"),
            "source": value.get("source") or value.get("sourceVersion") or context.get("source"),
            "dataType": value.get("surface") or value.get("category") or context.get("dataType"),
        }
        ids = value.get("evidenceIds") or value.get("citedEvidenceIds") or []
        if value.get("evidenceId"):
            ids = [value["evidenceId"], *ids]
        for evidence_id in ids:
            evidence_id = _text(evidence_id, 320)
            if evidence_id:
                yield evidence_id, next_context, value
        for child in value.values():
            yield from _walk_evidence(child, next_context)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_evidence(child, context)


def build_evidence_index(snapshot):
    found = {}
    for evidence_id, context, raw in _walk_evidence(snapshot):
        if evidence_id in found:
            continue
        if evidence_id.startswith("DB:"):
            source = "MMN当前组织数据库记录"
        elif evidence_id.startswith("FILE:"):
            source = "MMN当前项目文件证据"
        else:
            source = _text(context.get("source"), 300) or "当前冻结快照中的结构化引用"
        status = _text(context.get("status"), 80).lower()
        source_type = _source_type(context.get("sourceType"))
        if source_type == "unknown":
            source_type = "degraded" if status in {"limited", "degraded", "missing", "conflict"} else "unknown"
        found[evidence_id] = {
            "evidenceId": evidence_id,
            "source": source,
            "time": context.get("time") or "未知",
            "vehicle": snapshot["model"],
            "dataType": context.get("dataType") or "unknown",
            "authenticityStatus": status or "unknown",
            "sourceType": source_type,
            "evidenceFingerprint": evidence_packet_fingerprint(raw),
            "usableScope": snapshot["includedScope"],
        }
    return sorted(found.values(), key=lambda item: item["evidenceId"])


def model_messages(snapshot):
    packet = deepcopy(snapshot)
    packet.pop("reused", None)
    schema = {
        "coreConclusions": [{"topic": "consumer_cognition", "stance": "repair", "statement": "", "evidenceIds": []}],
        "primaryMarketingProblem": {"statement": "", "evidenceIds": []},
        "keyEvidence": [{"evidenceId": "", "meaning": ""}],
        "consumerCognitionImpact": {"statement": "", "evidenceIds": []},
        "competitiveImpact": {"statement": "", "evidenceIds": []},
        "strategyJudgment": {"statement": "", "evidenceIds": []},
        "actions": {"stop": [], "continue": [], "add": []},
        "accountAndContentTasks": [{"accountRole": "", "contentTask": "", "evidenceIds": []}],
        "observableMetrics": [{"metric": "", "boundary": "只用于观察，不作销量因果归因"}],
        "evidenceGaps": [], "unknowns": [], "pptNarrativeOrder": [], "citedEvidenceIds": [],
    }
    system = (
        "你是MMN策略汇报资料整理通道。只能使用用户提供的不可变冻结快照，不得补充外部事实、"
        "不得重算指标、不得把传播或互动直接归因为销量、不得隐藏演示/缓存/降级/未知。"
        "每个重要判断必须引用快照中真实存在的证据ID；无证据就写入evidenceGaps或unknowns。"
        "输出严格JSON，不要Markdown。coreConclusions最多3条；topic只能取consumer_cognition、"
        "competitive_position、communication_efficiency、product_evidence、sales_observation、strategy_execution；"
        "stance只能取repair、protect、amplify、monitor、insufficient_evidence。"
    )
    return [
        {"role": "system", "content": system + "目标JSON结构：" + canonical_json(schema)},
        {"role": "user", "content": canonical_json(packet)},
    ]


def _evidence_ids(value, allowed):
    return list(dict.fromkeys(_text(item, 320) for item in _list(value, 80) if _text(item, 320) in allowed))


def _statement(value, allowed):
    item = value if isinstance(value, dict) else {}
    return {"statement": _text(item.get("statement"), 900), "evidenceIds": _evidence_ids(item.get("evidenceIds"), allowed)}


def normalize_model_output(raw, snapshot):
    if not isinstance(raw, dict):
        raise ValueError("整理结果不是JSON对象")
    allowed = {item["evidenceId"] for item in build_evidence_index(snapshot)}
    conclusions = []
    for item in _list(raw.get("coreConclusions"), 3):
        if not isinstance(item, dict):
            continue
        topic = _text(item.get("topic"), 60)
        stance = _text(item.get("stance"), 60)
        statement = _text(item.get("statement"), 900)
        evidence_ids = _evidence_ids(item.get("evidenceIds"), allowed)
        if topic in TOPICS and stance in STANCES and statement:
            conclusions.append({"topic": topic, "stance": stance, "statement": statement, "evidenceIds": evidence_ids})
    result = {
        "schemaVersion": "mmn-strategy-report-model-output-v1",
        "evidenceFingerprint": snapshot["evidenceFingerprint"],
        "coreConclusions": conclusions,
        "primaryMarketingProblem": _statement(raw.get("primaryMarketingProblem"), allowed),
        "keyEvidence": [
            {"evidenceId": _text(item.get("evidenceId"), 320), "meaning": _text(item.get("meaning"), 700)}
            for item in _list(raw.get("keyEvidence"), 20)
            if isinstance(item, dict) and _text(item.get("evidenceId"), 320) in allowed
        ],
        "consumerCognitionImpact": _statement(raw.get("consumerCognitionImpact"), allowed),
        "competitiveImpact": _statement(raw.get("competitiveImpact"), allowed),
        "strategyJudgment": _statement(raw.get("strategyJudgment"), allowed),
        "actions": {},
        "accountAndContentTasks": [],
        "observableMetrics": [],
        "evidenceGaps": [_text(item, 500) for item in _list(raw.get("evidenceGaps"), 20) if _text(item, 500)],
        "unknowns": [_text(item, 500) for item in _list(raw.get("unknowns"), 20) if _text(item, 500)],
        "pptNarrativeOrder": [_text(item, 300) for item in _list(raw.get("pptNarrativeOrder"), 15) if _text(item, 300)],
    }
    for action_type in ("stop", "continue", "add"):
        result["actions"][action_type] = [
            _statement(item, allowed) for item in _list((raw.get("actions") or {}).get(action_type), 12)
            if _statement(item, allowed)["statement"]
        ]
    for item in _list(raw.get("accountAndContentTasks"), 15):
        if not isinstance(item, dict):
            continue
        role, task = _text(item.get("accountRole"), 200), _text(item.get("contentTask"), 600)
        if role or task:
            result["accountAndContentTasks"].append({"accountRole": role, "contentTask": task, "evidenceIds": _evidence_ids(item.get("evidenceIds"), allowed)})
    for item in _list(raw.get("observableMetrics"), 15):
        if isinstance(item, dict) and _text(item.get("metric"), 240):
            result["observableMetrics"].append({"metric": _text(item.get("metric"), 240), "boundary": _text(item.get("boundary"), 500) or "只用于观察，不作销量因果归因"})
    cited = set(_evidence_ids(raw.get("citedEvidenceIds"), allowed))
    for value in _walk_evidence(result):
        cited.add(value[0])
    result["citedEvidenceIds"] = sorted(cited)
    unsupported = [item for item in conclusions if item["stance"] != "insufficient_evidence" and not item["evidenceIds"]]
    if unsupported:
        result["evidenceGaps"].append("部分核心判断没有有效证据ID，不能进入管理层推荐结论。")
    return result


def deterministic_synthesis(outputs, errors, fingerprint):
    groups = defaultdict(list)
    for channel, output in outputs.items():
        for item in output.get("coreConclusions") or []:
            key = (item["topic"], item["stance"])
            groups[key].append((channel, item))
    common, two_way, single, unsupported = [], [], [], []
    disagreements = []
    topics = defaultdict(set)
    for (topic, stance), rows in groups.items():
        topics[topic].add(stance)
        evidence_sets = [set(item["evidenceIds"]) for _, item in rows]
        shared = sorted(set.intersection(*evidence_sets)) if evidence_sets and all(evidence_sets) else []
        entry = {
            "topic": topic, "stance": stance, "channelCount": len(rows),
            "channels": [channel for channel, _ in rows],
            "statements": [item["statement"] for _, item in rows],
            "sharedEvidenceIds": shared,
        }
        if not shared:
            unsupported.append(entry)
        elif len(rows) == 3:
            common.append(entry)
        elif len(rows) == 2:
            two_way.append(entry)
        else:
            single.append(entry)
    for topic, stances in topics.items():
        if len(stances) > 1:
            disagreements.append({"topic": topic, "stances": sorted(stances), "requiresHumanJudgment": True})
    completed = len(outputs)
    status = "completed" if completed == 3 else "partial_completed"
    recommended = common + two_way
    return {
        "schemaVersion": "mmn-strategy-report-synthesis-v1",
        "evidenceFingerprint": fingerprint,
        "status": status,
        "completedChannelCount": completed,
        "failedChannels": [{"label": channel, "state": "failed", "error": _text(error, 300)} for channel, error in errors.items()],
        "commonConclusions": common,
        "twoWayConclusions": two_way,
        "disagreements": disagreements,
        "singleChannelJudgments": single,
        "withoutCommonEvidence": unsupported,
        "requiresHumanJudgment": disagreements + unsupported,
        "recommendedForManagement": recommended,
        "confidenceRule": "仅共同证据支持的三路共同或两路一致判断可进入推荐；通道失败不提高置信度。",
    }


def _safe_filename(value):
    return re.sub(r"[^0-9A-Za-z一-龥._-]+", "_", _text(value, 120)).strip("_.") or "unknown"


def _bullets(items, empty="当前证据不足"):
    return "\n".join(f"- {item}" for item in items if item) or f"- {empty}"


def render_handoff(snapshot, synthesis, outputs, evidence_index):
    recommended = [row["statements"][0] for row in synthesis["recommendedForManagement"] if row.get("statements")]
    disputes = [f"{row['topic']}：{', '.join(row['stances'])}" for row in synthesis["disagreements"]]
    gaps = []
    for output in outputs.values():
        gaps.extend(output.get("evidenceGaps") or [])
        gaps.extend(output.get("unknowns") or [])
    actions = {key: [] for key in ("stop", "continue", "add")}
    roles, metrics, narratives = [], [], []
    for output in outputs.values():
        for key in actions:
            actions[key].extend(item["statement"] for item in output["actions"][key])
        roles.extend(f"{item['accountRole']}：{item['contentTask']}" for item in output["accountAndContentTasks"])
        metrics.extend(f"{item['metric']}（{item['boundary']}）" for item in output["observableMetrics"])
        narratives.extend(output["pptNarrativeOrder"])
    evidence_lines = [f"{item['evidenceId']}｜{item['source']}｜{item['time']}｜{item['authenticityStatus']}" for item in evidence_index]
    return f"""# MMN策略汇报资料包

## 1. 给Codex的任务

请基于本资料包制作一份面向车企集团管理层、品牌负责人或车型负责人的策略汇报PPT。

PPT不是MMN系统介绍，不展示底层模型、插件、数据服务商或技术架构，不把客户引导到购买看板系统。PPT需要让客户发现问题、看清问题、认可问题、理解策略，并进入账号采买和内容执行决策。

建议控制在8至12页，先结论、后证据，每页只表达一个核心问题，避免大段文字和空泛策略。所有事实必须来自资料包；资料不足时明确写“待补充”，不得自行编造。

Codex制作边界：不补充未经提供的市场事实；不将热度、声量、互动直接写成销量原因；不隐藏分歧和数据缺失；不把分析结论扩张为无法证明的用户级路径；最终必须落到策略、内容任务、账号角色和下一步决策。

## 2. 项目与车型背景

- 当前组织：{snapshot['orgId']}
- 当前项目：{snapshot['project']}（{snapshot['projectId']}）
- 当前品牌 / 车型：{snapshot['brand']} / {snapshot['model']}
- 当前T周期：{_text((snapshot.get('tCycle') or {}).get('display') or (snapshot.get('tCycle') or {}).get('phaseLabel')) or '未知'}
- 驾驶舱版本：{snapshot['cockpitVersion']}

## 3. 数据范围和真实性说明

- 数据范围：{snapshot['dataTimeRange']}
- 快照ID：{snapshot['snapshotId']}
- 证据指纹：{snapshot['evidenceFingerprint']}
- 生成时间：{snapshot['generatedAt']}
- 三路状态：{synthesis['status']}（完成 {synthesis['completedChannelCount']}/3）
- 演示、缓存、降级和未知内容均保留原状态，不得作为真实事实扩写。

## 4. 管理层核心结论

{_bullets(recommended)}

## 5. 当前最需要解决的问题

{_bullets([output['primaryMarketingProblem']['statement'] for output in outputs.values()])}

## 6. 支撑问题的关键证据

{_bullets(evidence_lines[:30], '无有效数据')}

## 7. 消费者认知影响

{_bullets([output['consumerCognitionImpact']['statement'] for output in outputs.values()])}

## 8. 竞争影响

{_bullets([output['competitiveImpact']['statement'] for output in outputs.values()])}

## 9. 三路共同判断

{_bullets([row['statements'][0] for row in synthesis['commonConclusions'] if row.get('statements')])}

## 10. 三路分歧与待人工判断

{_bullets(disputes + [row['statements'][0] for row in synthesis['withoutCommonEvidence'] if row.get('statements')], '无已识别分歧；仍需人工最终判断')}

## 11. 建议策略

{_bullets([output['strategyJudgment']['statement'] for output in outputs.values()])}

## 12. 停止、继续和新增的行动

### 停止
{_bullets(list(dict.fromkeys(actions['stop'])))}

### 继续
{_bullets(list(dict.fromkeys(actions['continue'])))}

### 新增
{_bullets(list(dict.fromkeys(actions['add'])))}

## 13. 账号角色与内容任务

{_bullets(list(dict.fromkeys(roles)), '当前没有真实账号商业数据；仅可补充账号角色和能力要求，不得编造具体账号、报价或档期')}

## 14. 投放及结果观察指标

{_bullets(list(dict.fromkeys(metrics)))}

## 15. 销量背景与因果边界

销量仅作为经营背景与结果观察，不把曝光、热度、声量、互动或情绪直接写成销量原因。若资料包没有共同证据支持，只能写“待验证”，不能建立用户级因果路径。

## 16. 建议PPT结构

{_bullets(list(dict.fromkeys(narratives))[:12], '先结论、后证据、再策略与行动，建议8至12页')}

## 17. 证据索引

{_bullets(evidence_lines, '无有效数据')}

## 18. 缺失数据和未知项

{_bullets(list(dict.fromkeys(gaps)), '当前未额外识别；仍应以cockpit_snapshot.json中的模块状态为准')}
"""


def build_zip(snapshot, outputs, errors, synthesis):
    evidence_index = build_evidence_index(snapshot)
    model_synthesis = {
        "schemaVersion": "mmn-strategy-report-model-synthesis-v1",
        "snapshotId": snapshot["snapshotId"],
        "evidenceFingerprint": snapshot["evidenceFingerprint"],
        "independence": {
            "sameEvidencePacket": INDEPENDENCE_PROTOCOL["sameEvidencePacket"],
            "blindIndependentFirstPass": INDEPENDENCE_PROTOCOL["blindIndependentFirstPass"],
            "modelsMaySeePeerOutputBeforeFirstPass": False,
        },
        "channels": [
            {
                "label": channel,
                "state": "completed" if channel in outputs else "failed",
                "output": outputs.get(channel),
                "error": errors.get(channel),
            }
            for channel in PUBLIC_CHANNELS
        ],
        "synthesis": synthesis,
    }
    handoff = render_handoff(snapshot, synthesis, outputs, evidence_index)
    readme = (
        "MMN策略汇报资料包\n\n"
        "主入口：MMN_CODEX_PPT_HANDOFF.md\n"
        "cockpit_snapshot.json：不可变驾驶舱快照\n"
        "model_synthesis.json：三路独立整理与确定性综合\n"
        "evidence_index.json：证据索引、状态与可用范围\n"
        "chart_data.json：驾驶舱当前图表的结构化数据\n"
        "assets/：当前项目允许导出的素材；没有合法素材时不会自动生成。\n"
    )
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("MMN_CODEX_PPT_HANDOFF.md", handoff.encode("utf-8"))
        archive.writestr("cockpit_snapshot.json", json.dumps(snapshot, ensure_ascii=False, indent=2).encode("utf-8"))
        archive.writestr("model_synthesis.json", json.dumps(model_synthesis, ensure_ascii=False, indent=2).encode("utf-8"))
        archive.writestr("evidence_index.json", json.dumps(evidence_index, ensure_ascii=False, indent=2).encode("utf-8"))
        archive.writestr("chart_data.json", json.dumps(snapshot.get("chartData") or {}, ensure_ascii=False, indent=2).encode("utf-8"))
        archive.writestr("assets/README.txt", "当前冻结快照没有可确认合法且属于本项目的可导出素材，因此未自动生成或补齐素材。\n".encode("utf-8"))
        archive.writestr("README.txt", readme.encode("utf-8"))
    return buffer.getvalue(), model_synthesis


def run_package(conn, snapshot_id, *, org_id, user_id, role_runner, force=False):
    init_schema(conn)
    snapshot = get_snapshot(conn, snapshot_id, org_id=org_id)
    if not snapshot:
        raise ValueError("当前组织中不存在该冻结快照")
    existing = conn.execute(
        "select * from strategy_report_packages where snapshot_id=? and org_id=? order by version desc limit 1",
        (snapshot_id, str(org_id)),
    ).fetchone()
    if existing and not force:
        return package_metadata(existing, cached=True)
    messages = model_messages(snapshot)
    outputs, errors = {}, {}

    def run_one(role):
        return normalize_model_output(role_runner(role, deepcopy(messages)), snapshot)

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {label: executor.submit(run_one, role) for label, role in zip(PUBLIC_CHANNELS, INTERNAL_ROLES)}
        for label, future in futures.items():
            try:
                outputs[label] = future.result()
            except Exception as exc:
                errors[label] = _text(exc, 300) or "整理通道未完成"
    synthesis = deterministic_synthesis(outputs, errors, snapshot["evidenceFingerprint"])
    zip_bytes, model_synthesis = build_zip(snapshot, outputs, errors, synthesis)
    version = int(existing["version"] + 1) if existing else 1
    package_id = "srpkg-" + uuid.uuid4().hex
    stamp = utcnow()
    time_label = snapshot["dataEnd"] or snapshot["dataStart"] or stamp[:10]
    filename = "MMN_策略汇报资料包_{}_{}_{}_v{}.zip".format(
        _safe_filename(snapshot["brand"]), _safe_filename(snapshot["model"]), _safe_filename(time_label), version
    )
    conn.execute(
        """insert into strategy_report_packages
        (id,snapshot_id,org_id,version,status,synthesis_json,filename,zip_bytes,created_at)
        values (?,?,?,?,?,?,?,?,?)""",
        (package_id, snapshot_id, str(org_id), version, synthesis["status"], json.dumps(model_synthesis, ensure_ascii=False), filename, sqlite3.Binary(zip_bytes), stamp),
    )
    conn.commit()
    row = conn.execute("select * from strategy_report_packages where id=?", (package_id,)).fetchone()
    return package_metadata(row, cached=False)


def package_metadata(row, cached=False):
    synthesis = json.loads(row["synthesis_json"] or "{}")
    summary = synthesis.get("synthesis") or {}
    return {
        "packageId": row["id"], "snapshotId": row["snapshot_id"], "version": row["version"],
        "status": row["status"], "filename": row["filename"], "createdAt": row["created_at"],
        "completedChannelCount": summary.get("completedChannelCount", 0),
        "failedChannels": summary.get("failedChannels") or [], "cached": bool(cached),
    }


def get_package_bytes(conn, package_id, *, org_id):
    row = conn.execute(
        "select filename, zip_bytes from strategy_report_packages where id=? and org_id=?",
        (str(package_id), str(org_id)),
    ).fetchone()
    return (row["filename"], bytes(row["zip_bytes"])) if row else None
