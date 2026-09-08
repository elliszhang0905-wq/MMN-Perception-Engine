#!/usr/bin/env python3
"""Offline v4 replay. No DB, network or model calls; never creates Gold."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mmn_eval.brand_review import evaluate_brand_reviews


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('--approval', type=Path)
    parser.add_argument('--trusted-approval-sha256', help='Pin obtained separately from product owner, not dataset')
    args = parser.parse_args()
    if args.dataset.stat().st_size > 25_000_000 or (args.approval and args.approval.stat().st_size > 2_000_000):
        parser.error('input exceeds offline replay size limit')
    cases = json.loads(args.dataset.read_text(encoding='utf-8'))
    approval = json.loads(args.approval.read_text(encoding='utf-8')) if args.approval else None
    report = evaluate_brand_reviews(cases, approval=approval,
                                    trusted_approval_sha256=args.trusted_approval_sha256)
    print(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False))
    return 0 if report['status'] == 'passed' else 2 if report['status'] == 'not_ready' else 1


if __name__ == '__main__':
    sys.exit(main())
