import hashlib
import json
import math
from datetime import datetime, timezone


MAX_MODELS = 100
MAX_PHASES_PER_MODEL = 120
VALID_EDITIONS = {"china", "global"}
REQUIRED_FIELDS = {
    "model": ("车型", "车型名称", "model", "vehicle"),
    "phase": ("阶段", "阶段名称", "phase", "stage"),
    "lead_target": ("线索目标", "目标线索", "leadTarget", "lead_target"),
    "lead_actual": ("实际线索", "线索实际", "leadActual", "lead_actual"),
    "order_target": ("订单目标", "目标订单", "orderTarget", "order_target"),
    "order_actual": ("实际订单", "订单实际", "orderActual", "order_actual"),
    "status": ("阶段状态", "状态", "status", "phaseStatus"),
}
STATUS_ALIASES = {
    "已完成": "completed",
    "完成": "completed",
    "completed": "completed",
    "进行中": "in_progress",
    "当前": "in_progress",
    "in_progress": "in_progress",
    "in progress": "in_progress",
}


def _now():
    return datetime.now(timezone.utc).isoformat()


def _text(value, field, limit=160):
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field}不能为空。")
    if len(text) > limit:
        raise ValueError(f"{field}超出长度限制。")
    return text


def _canonical_header(value):
    return "".join(str(value or "").strip().lower().replace("-", "_").split())


def _row_value(row, aliases):
    headers = {_canonical_header(key): value for key, value in row.items()}
    for alias in aliases:
        key = _canonical_header(alias)
        if key in headers:
            return headers[key]
    return None


def _lead_header_fields(row):
    normalized = {_canonical_header(value) for value in row if str(value or "").strip()}
    return {
        field
        for field, aliases in REQUIRED_FIELDS.items()
        if any(_canonical_header(alias) in normalized for alias in aliases)
    }


def extract_rows_from_sheets(sheets):
    """Extract lead rows from worksheet matrices without assuming row 1 is the header."""
    if not isinstance(sheets, dict):
        raise ValueError("线索工作簿结构无效。")
    records = []
    for sheet, rows in sheets.items():
        if not isinstance(rows, list):
            continue
        header_index = next(
            (
                index
                for index, row in enumerate(rows[:50])
                if isinstance(row, (list, tuple))
                and _lead_header_fields(row) == set(REQUIRED_FIELDS)
            ),
            None,
        )
        if header_index is None:
            continue
        headers = [str(value or "").strip() for value in rows[header_index]]
        for row in rows[header_index + 1:]:
            if not isinstance(row, (list, tuple)) or not any(str(value or "").strip() for value in row):
                continue
            records.append(
                {
                    "_sheet": str(sheet or ""),
                    **{
                        header or f"col_{index + 1}": row[index] if index < len(row) else ""
                        for index, header in enumerate(headers)
                    },
                }
            )
    if not records:
        raise ValueError("未找到线索数据表头，请检查必需字段。")
    return records


def _positive_number(value, field):
    if isinstance(value, bool):
        raise ValueError(f"{field}必须是大于0的数值。")
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        raise ValueError(f"{field}必须是大于0的数值。") from None
    if not math.isfinite(number) or number <= 0:
        raise ValueError(f"{field}必须是大于0的数值。")
    return int(number) if number.is_integer() else number


def _nonnegative_number(value, field):
    if isinstance(value, bool):
        raise ValueError(f"{field}必须是大于等于0的数值。")
    try:
        number = float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        raise ValueError(f"{field}必须是大于等于0的数值。") from None
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{field}必须是大于等于0的数值。")
    return int(number) if number.is_integer() else number


def init_schema(conn):
    conn.executescript(
        """
        create table if not exists lead_dashboard_datasets (
            org_id text not null,
            edition text not null,
            model text not null,
            dataset_version text not null,
            fingerprint text not null,
            dataset_json text not null,
            created_by text,
            created_at text not null,
            updated_at text not null,
            primary key (org_id, edition, model)
        );
        create index if not exists idx_lead_dashboard_datasets_updated
        on lead_dashboard_datasets(org_id, edition, updated_at desc);
        """
    )


def build_datasets_from_rows(rows, filename):
    if not isinstance(rows, list) or not rows:
        raise ValueError("线索数据文件没有可用记录。")
    source_label = _text(filename, "文件名", 240)
    grouped = {}
    missing_fields = set()
    for row_number, row in enumerate(rows, start=2):
        if not isinstance(row, dict):
            raise ValueError(f"第{row_number}行格式无效。")
        values = {field: _row_value(row, aliases) for field, aliases in REQUIRED_FIELDS.items()}
        row_missing = {field for field, value in values.items() if value is None}
        missing_fields.update(row_missing)
        if row_missing:
            continue
        model = _text(values["model"], f"第{row_number}行车型")
        phase_name = _text(values["phase"], f"第{row_number}行阶段")
        status_key = _canonical_header(values["status"])
        status = STATUS_ALIASES.get(status_key)
        if not status:
            raise ValueError(f"第{row_number}行阶段状态必须为已完成或进行中。")
        lead_target = _positive_number(values["lead_target"], f"第{row_number}行线索目标")
        lead_actual = _nonnegative_number(values["lead_actual"], f"第{row_number}行实际线索")
        order_target = _positive_number(values["order_target"], f"第{row_number}行订单目标")
        order_actual = _nonnegative_number(values["order_actual"], f"第{row_number}行实际订单")
        grouped.setdefault(model, []).append(
            {
                "name": phase_name,
                "leadTarget": lead_target,
                "leadActual": lead_actual,
                "leadRate": lead_actual / lead_target,
                "orderTarget": order_target,
                "orderActual": order_actual,
                "orderRate": order_actual / order_target,
                "status": status,
            }
        )
    if missing_fields:
        labels = {
            "model": "车型",
            "phase": "阶段",
            "lead_target": "线索目标",
            "lead_actual": "实际线索",
            "order_target": "订单目标",
            "order_actual": "实际订单",
            "status": "阶段状态",
        }
        raise ValueError("缺少必需字段：" + "、".join(labels[field] for field in sorted(missing_fields)))
    if not grouped or len(grouped) > MAX_MODELS:
        raise ValueError("车型数量为空或超出100个限制。")
    datasets = []
    for model, phases in grouped.items():
        if len(phases) > MAX_PHASES_PER_MODEL:
            raise ValueError(f"{model}阶段数量超出{MAX_PHASES_PER_MODEL}个限制。")
        names = [phase["name"] for phase in phases]
        if len(names) != len(set(names)):
            raise ValueError(f"{model}存在阶段重复。")
        if sum(phase["status"] == "in_progress" for phase in phases) > 1:
            raise ValueError(f"{model}只能有一个进行中阶段。")
        dataset = {
            "model": model,
            "source": {
                "label": source_label,
                "scope": "阶段目标、实际线索与实际订单",
                "asOf": "文件导入时间",
            },
            "phases": phases,
        }
        canonical = json.dumps(dataset, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        dataset["datasetVersion"] = f"lead_{fingerprint[:16]}"
        dataset["fingerprint"] = fingerprint
        datasets.append(dataset)
    return sorted(datasets, key=lambda item: item["model"])


def save_datasets(conn, *, org_id, edition, datasets, user_id=""):
    org_id = _text(org_id, "企业空间")
    edition = _text(edition, "版本", 20)
    if edition not in VALID_EDITIONS:
        raise ValueError("线索数据版本范围无效。")
    if not isinstance(datasets, list) or not datasets:
        raise ValueError("没有可保存的线索车型数据。")
    timestamp = _now()
    saved = []
    for dataset in datasets:
        model = _text(dataset.get("model"), "车型")
        raw = json.dumps(dataset, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        conn.execute(
            """
            insert into lead_dashboard_datasets(
                org_id,edition,model,dataset_version,fingerprint,dataset_json,
                created_by,created_at,updated_at
            ) values(?,?,?,?,?,?,?,?,?)
            on conflict(org_id,edition,model) do update set
                dataset_version=excluded.dataset_version,
                fingerprint=excluded.fingerprint,
                dataset_json=excluded.dataset_json,
                created_by=excluded.created_by,
                updated_at=excluded.updated_at
            """,
            (
                org_id,
                edition,
                model,
                dataset["datasetVersion"],
                dataset["fingerprint"],
                raw,
                str(user_id or ""),
                timestamp,
                timestamp,
            ),
        )
        saved.append({"model": model, "dataset": dataset, "updatedAt": timestamp})
    return saved


def get_dataset(conn, *, org_id, edition, model):
    org_id = _text(org_id, "企业空间")
    edition = _text(edition, "版本", 20)
    model = _text(model, "车型")
    if edition not in VALID_EDITIONS:
        raise ValueError("线索数据版本范围无效。")
    row = conn.execute(
        """
        select dataset_json,updated_at
        from lead_dashboard_datasets
        where org_id=? and edition=? and model=?
        """,
        (org_id, edition, model),
    ).fetchone()
    if not row:
        return None
    try:
        dataset = json.loads(row["dataset_json"])
    except (TypeError, json.JSONDecodeError):
        return None
    dataset["updatedAt"] = row["updated_at"]
    return dataset
