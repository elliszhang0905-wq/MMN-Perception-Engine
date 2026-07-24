import hashlib
import json
from datetime import datetime, timezone


MAX_DATASET_BYTES = 4 * 1024 * 1024
MAX_MODELS = 100
MAX_ROWS = 50000
VALID_EDITIONS = {"china", "global"}


def _now():
    return datetime.now(timezone.utc).isoformat()


def init_schema(conn):
    conn.executescript(
        """
        create table if not exists product_evaluation_datasets (
            org_id text not null,
            edition text not null,
            source_model text not null,
            dataset_version text not null,
            fingerprint text not null,
            dataset_json text not null,
            created_by text,
            created_at text not null,
            updated_at text not null,
            primary key (org_id, edition, source_model)
        );
        create index if not exists idx_product_evaluation_datasets_updated
        on product_evaluation_datasets(org_id, edition, updated_at desc);
        """
    )


def _text(value, field, limit=160):
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field}不能为空。")
    if len(text) > limit:
        raise ValueError(f"{field}超出长度限制。")
    return text


def validate_dataset(dataset):
    if not isinstance(dataset, dict):
        raise ValueError("产品评价数据格式无效。")
    if (dataset.get("importQuality") or {}).get("kind") == "PRODUCT_EVALUATION_UNAVAILABLE":
        raise ValueError("空状态不能登记为产品评价数据。")
    config = dataset.get("config") if isinstance(dataset.get("config"), dict) else {}
    source_model = _text(dataset.get("productEvaluationSourceModel") or config.get("model"), "源车型")
    dataset_version = _text(dataset.get("datasetVersion"), "数据版本", 240)
    models = dataset.get("models")
    rows = dataset.get("rows")
    if not isinstance(models, list) or not models or len(models) > MAX_MODELS:
        raise ValueError("车型集合为空或超出限制。")
    normalized_models = []
    for model in models:
        name = _text(model, "车型")
        if name not in normalized_models:
            normalized_models.append(name)
    if source_model not in normalized_models:
        raise ValueError("源车型不在数据车型集合中。")
    if not isinstance(rows, list) or len(rows) > MAX_ROWS:
        raise ValueError("产品评价明细格式无效或超出限制。")
    summary_fields = ("summaryHeat", "summaryPlatformNsr", "summaryMetrics")
    if not rows and not any(isinstance(dataset.get(field), dict) and dataset.get(field) for field in summary_fields):
        raise ValueError("产品评价数据没有可用明细或汇总指标。")
    normalized = dict(dataset)
    normalized["config"] = dict(config)
    normalized["models"] = normalized_models
    normalized["productEvaluationSourceModel"] = source_model
    normalized.pop("productEvaluationBoundModel", None)
    raw = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    if len(raw.encode("utf-8")) > MAX_DATASET_BYTES:
        raise ValueError("产品评价数据包超出4MB限制。")
    fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return normalized, source_model, dataset_version, fingerprint, raw


def save_dataset(conn, *, org_id, edition, dataset, user_id=""):
    org_id = _text(org_id, "企业空间")
    edition = _text(edition, "版本", 20)
    if edition not in VALID_EDITIONS:
        raise ValueError("产品评价数据版本范围无效。")
    normalized, source_model, dataset_version, fingerprint, raw = validate_dataset(dataset)
    existing = conn.execute(
        """
        select updated_at from product_evaluation_datasets
        where org_id=? and edition=? and source_model=? and fingerprint=?
        """,
        (org_id, edition, source_model, fingerprint),
    ).fetchone()
    if existing:
        return {
            "sourceModel": source_model,
            "datasetVersion": dataset_version,
            "fingerprint": fingerprint,
            "dataset": normalized,
            "updatedAt": existing["updated_at"] if hasattr(existing, "keys") else existing[0],
        }
    timestamp = _now()
    conn.execute(
        """
        insert into product_evaluation_datasets(
            org_id,edition,source_model,dataset_version,fingerprint,dataset_json,
            created_by,created_at,updated_at
        ) values(?,?,?,?,?,?,?,?,?)
        on conflict(org_id,edition,source_model) do update set
            dataset_version=excluded.dataset_version,
            fingerprint=excluded.fingerprint,
            dataset_json=excluded.dataset_json,
            created_by=excluded.created_by,
            updated_at=excluded.updated_at
        """,
        (org_id, edition, source_model, dataset_version, fingerprint, raw, str(user_id or ""), timestamp, timestamp),
    )
    return {
        "sourceModel": source_model,
        "datasetVersion": dataset_version,
        "fingerprint": fingerprint,
        "dataset": normalized,
        "updatedAt": timestamp,
    }


def list_datasets(conn, *, org_id, edition):
    org_id = _text(org_id, "企业空间")
    edition = _text(edition, "版本", 20)
    if edition not in VALID_EDITIONS:
        raise ValueError("产品评价数据版本范围无效。")
    rows = conn.execute(
        """
        select source_model,dataset_version,fingerprint,dataset_json,updated_at
        from product_evaluation_datasets
        where org_id=? and edition=?
        order by updated_at desc, source_model
        """,
        (org_id, edition),
    ).fetchall()
    items = []
    for row in rows:
        try:
            dataset = json.loads(row["dataset_json"])
        except (TypeError, json.JSONDecodeError):
            continue
        items.append(
            {
                "sourceModel": row["source_model"],
                "datasetVersion": row["dataset_version"],
                "fingerprint": row["fingerprint"],
                "dataset": dataset,
                "updatedAt": row["updated_at"],
            }
        )
    return items
