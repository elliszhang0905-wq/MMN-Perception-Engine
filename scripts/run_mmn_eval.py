#!/usr/bin/env python3
"""Run MMN Eval against one candidate or a baseline/candidate pair."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mmn_eval.runner import compare_runs, evaluate_dataset, load_jsonl, render_markdown


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Run the offline MMN Eval release gate")
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--outputs", type=Path, required=True, help="candidate output JSONL")
    parser.add_argument("--baseline", type=Path, help="optional baseline output JSONL")
    parser.add_argument("--out", type=Path, required=True, help="JSON report path")
    parser.add_argument("--markdown", type=Path, help="optional Markdown report path")
    parser.add_argument("--name", default="candidate")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    cases = load_jsonl(args.cases)
    candidate_outputs = load_jsonl(args.outputs)
    if args.baseline:
        report = compare_runs(cases, load_jsonl(args.baseline), candidate_outputs)
    else:
        report = evaluate_dataset(cases, candidate_outputs, run_name=args.name)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({
        "report": str(args.out),
        "releaseVerdict": report["releaseVerdict"],
        "humanReviewCount": len(report.get("humanReviewQueue") or []),
    }, ensure_ascii=False))
    return 0 if report["releaseVerdict"] in {"pass", "human_review"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
