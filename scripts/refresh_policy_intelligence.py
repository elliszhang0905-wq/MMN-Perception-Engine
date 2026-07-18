#!/usr/bin/env python3
"""Run the controlled Policy Intelligence collection workflow.

The manifest contains exact official URLs; this adapter does not discover or
publish policy facts automatically. Parsing creates a draft for human review.
"""

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from policy_intelligence import (  # noqa: E402
    fetch_policy_source,
    parse_policy_with_gateway,
    save_policy_document,
    save_policy_fetch_run,
    save_policy_record,
)
from server import (  # noqa: E402
    db,
    fetch_opportunity_official_page,
    init_db,
    now,
    policy_model_gateway,
)


def run(manifest_path, *, org_id="local", edition="china", parse_drafts=False):
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    items = manifest.get("items") if isinstance(manifest, dict) else manifest
    if not isinstance(items, list):
        raise ValueError("政策采集清单必须是JSON数组或包含items数组")
    init_db()
    results = []
    for item in items:
        if item.get("enabled") is False:
            continue
        source = dict(item.get("source") or {})
        started_at = now()
        try:
            fetched = fetch_policy_source(
                source,
                lambda url, max_bytes: fetch_opportunity_official_page(
                    url,
                    allowed_domains=source.get("allowedDomains"),
                    max_bytes=max_bytes,
                ),
            )
            with db() as conn:
                document = save_policy_document(
                    conn,
                    org_id=org_id,
                    edition=edition,
                    source=source,
                    raw_text=fetched["rawText"],
                    metadata={**dict(item.get("metadata") or {}), "finalUrl": fetched["finalUrl"], "fetchedAt": fetched["fetchedAt"], "acquisitionMethod": "network_fetched"},
                )
                run_item = save_policy_fetch_run(
                    conn,
                    source=source,
                    source_url=fetched["sourceUrl"],
                    status="fetched",
                    document_id=document["id"],
                    started_at=started_at,
                    finished_at=now(),
                    org_id=org_id,
                    edition=edition,
                )
                policy = None
                if parse_drafts:
                    parsed = parse_policy_with_gateway(fetched["rawText"], source, policy_model_gateway)
                    policy = save_policy_record(conn, document["id"], parsed)
            results.append({"ok": True, "document": document, "fetchRun": run_item, "policyDraft": policy})
        except Exception as exc:
            with db() as conn:
                failed = save_policy_fetch_run(
                    conn,
                    source=source,
                    source_url=source.get("url") or source.get("baseUrl") or "",
                    status="failed",
                    error=str(exc),
                    started_at=started_at,
                    finished_at=now(),
                    org_id=org_id,
                    edition=edition,
                )
            results.append({"ok": False, "fetchRun": failed, "error": str(exc)})
    return {"ok": all(item["ok"] for item in results), "processed": len(results), "results": results}


def main():
    parser = argparse.ArgumentParser(description="采集指定官方汽车政策URL并保留原文")
    parser.add_argument("--manifest", default=str(ROOT / "data" / "policy_source_urls.json"))
    parser.add_argument("--org-id", default="local")
    parser.add_argument("--edition", default="china")
    parser.add_argument("--parse-drafts", action="store_true", help="调用MMN模型生成待人工审核草稿")
    args = parser.parse_args()
    result = run(args.manifest, org_id=args.org_id, edition=args.edition, parse_drafts=args.parse_drafts)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
