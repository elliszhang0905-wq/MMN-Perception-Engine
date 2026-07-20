#!/usr/bin/env python3
"""把产品评价原始 Excel 无损登记到统一数据根目录。"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mmn_data import module_dir, module_path  # noqa: E402
from server import build_dataset_from_workbook  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--asset-name", default="e7x_product_evaluation_2026-06.json")
    parser.add_argument("--legacy-metadata", type=Path)
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    raw_dir = module_dir("imports_raw", create=True) / "product_evaluation"
    raw_dir.mkdir(parents=True, exist_ok=True)
    archived_source = raw_dir / f"{digest[:12]}_{source.name}"
    if not archived_source.exists():
        shutil.copy2(source, archived_source)

    dataset = build_dataset_from_workbook(raw, source.name)
    legacy = {}
    if args.legacy_metadata and args.legacy_metadata.exists():
        legacy = json.loads(args.legacy_metadata.read_text(encoding="utf-8"))
    own_model = dataset["config"]["model"]
    models = dataset["models"]
    legacy.setdefault("source", {"fileName": source.name, "period": dataset["importQuality"]["timeRange"]})
    legacy.setdefault("ownModel", own_model)
    legacy.setdefault("models", [
        {
            "model": model,
            "voice": dataset["summaryHeat"][model]["volume"],
            "engagement": dataset["summaryHeat"][model]["interaction"],
            "overallNsr": dataset["summaryMetrics"][model]["overallNsr"],
            "verticalNsr": dataset["summaryPlatformNsr"].get(model, {}).get("垂媒车主口碑"),
            "douyinNsr": dataset["summaryPlatformNsr"].get(model, {}).get("抖音"),
        }
        for model in models
    ])
    legacy.setdefault("platforms", [
        {
            "platform": platform,
            "voice": dataset["summaryHeat"][own_model]["volume"] if platform == "全网" else dataset["summaryHeat"][own_model]["platformVolume"].get(platform, 0),
            "nsr": nsr,
        }
        for platform, nsr in dataset["summaryPlatformNsr"][own_model].items()
    ])
    full_network = {}
    for row in dataset["rows"]:
        if row[2] == "全网" and row[4] and isinstance(row[14], (int, float)):
            full_network.setdefault(row[4], {})[row[0]] = row[14]
    legacy.setdefault("attributes", [
        {
            "attribute": label,
            "ownNsr": scores[own_model],
            "averageNsr": sum(scores.values()) / len(scores),
        }
        for label, scores in full_network.items()
        if own_model in scores
    ])
    payload = {
        **legacy,
        "sourceAsset": {
            "fileName": source.name,
            "sha256": digest,
            "archivedPath": str(archived_source.relative_to(module_dir("imports_raw"))),
        },
        "dataset": dataset,
    }
    destination = module_path("product_evaluation", args.asset_name, for_write=True)
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "source": str(archived_source), "destination": str(destination), "rows": len(dataset["rows"]), "sha256": digest}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
