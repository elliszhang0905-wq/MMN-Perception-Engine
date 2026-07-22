#!/usr/bin/env python3
"""Run the persistent MMN public-social evidence worker."""

import argparse
import signal
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from social_evidence import SocialEvidenceRepository, SocialEvidenceService, TikHubEvidenceAdapter


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Process at most one queued job")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    args = parser.parse_args()
    running = True

    def stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    repository = SocialEvidenceRepository()
    service = SocialEvidenceService(repository)
    adapter = TikHubEvidenceAdapter()

    while running:
        job = repository.claim_next_job()
        if not job:
            if args.once:
                return 0
            time.sleep(max(0.2, min(args.poll_seconds, 30)))
            continue
        try:
            service.run_job(job["jobId"], job["orgId"], adapter)
        except Exception:
            # The service has already persisted a neutral degraded/manual state.
            pass
        if args.once:
            return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
