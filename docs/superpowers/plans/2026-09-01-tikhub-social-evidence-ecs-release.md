# TikHub Social Evidence ECS Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Push an auditable TikHub social-evidence release to GitHub `main`, enable the existing production V2 boundary, and run its external worker on ECS without copying local dirty-worktree code or local business data.

**Architecture:** Release from an isolated worktree based on `origin/main`, which already contains `TikHubClient`, `TikHubEvidenceAdapter`, the V2 API, and the profiled external worker. The Git commit changes only the release marker and production activation documentation; the ECS deployment preserves `.env` and Docker volumes, injects three non-code activation settings, deploys a SHA-256-verified commit archive, and retains a code/environment/database rollback bundle.

**Tech Stack:** Git/GitHub, Bash, Docker Compose, Python HTTP API, SQLite, SSH/SCP, TikHub REST API.

## Global Constraints

- Source branch: `origin/main` at `4dcf83f1614c19d17906cea3e69ef3fcd92c960c` or a fast-forward successor fetched before push.
- Production host: `root@121.40.60.90`; release directory: `/opt/mmn-perception-engine`.
- Never commit or print `TIKHUB_API_KEY`, authentication secrets, cookies, or the production `.env` contents.
- Do not copy the dirty primary worktree or any local SQLite/data assets to ECS.
- Preserve the production Docker volume and create verified source, environment, and SQLite backups before deployment.
- Enable `MMN_SOCIAL_EVIDENCE_V2_ENABLED=true`, `MMN_SOCIAL_EVIDENCE_WORKER_MODE=external`, and `COMPOSE_PROFILES=social-evidence-v2` only on ECS.
- The customer-facing API and UI must not expose TikHub, bearer tokens, prompts, or raw supplier errors.
- One post-deploy billed Douyin request is allowed; do not retry automatically.
- Roll back immediately on container health failure, SQLite integrity failure, public 5xx, secret leakage, or a failed authenticated business flow.

---

### Task 1: Create the Release Commit

**Files:**
- Modify: `server.py`
- Modify: `.env.example`
- Modify: `tests/test_all_surfaces_release_gate.py`
- Modify: `MMN_CURRENT_STATE.md`
- Modify: `release.md`
- Create: `docs/研发档案/2026-09-01_beta-1.03_TikHub公开社媒证据ECS启用.md`
- Create: `docs/superpowers/plans/2026-09-01-tikhub-social-evidence-ecs-release.md`

**Interfaces:**
- Consumes: the existing V2 feature flag, external worker profile, and production TikHub secret.
- Produces: application version `beta-1.03-20260901-tikhub-social-evidence-1` and documented activation settings.

- [ ] **Step 1: Set the release marker**

Change `APP_VERSION_CODE` in `server.py` to:

```python
APP_VERSION_CODE = "beta-1.03-20260901-tikhub-social-evidence-1"
```

- [ ] **Step 2: Document the opt-in production profile**

Add this inactive default to `.env.example` next to the worker mode:

```dotenv
COMPOSE_PROFILES=
```

Document that production sets it to `social-evidence-v2` only when the external worker is intentionally enabled.

- [ ] **Step 3: Run release gates**

Run:

```bash
python3 -m unittest -q tests.test_social_trends tests.test_social_evidence_v2 tests.test_social_evidence_v2_api
npm run release:gate
git diff --check
```

Expected: all tests and the complete isolated release gate pass; source business data is unchanged.

- [ ] **Step 4: Stage only release files and scan for secrets**

Run:

```bash
git add server.py .env.example tests/test_all_surfaces_release_gate.py MMN_CURRENT_STATE.md release.md docs/研发档案/2026-09-01_beta-1.03_TikHub公开社媒证据ECS启用.md docs/superpowers/plans/2026-09-01-tikhub-social-evidence-ecs-release.md
git diff --cached --check
git diff --cached --name-only
```

Expected: exactly the seven release paths listed in this task; `.env`, database files, raw responses, and local plans from other worktrees are absent.

- [ ] **Step 5: Commit and fast-forward push**

Commit message:

```text
release: enable TikHub social evidence on ECS
```

Fetch `origin/main`, require the release branch to fast-forward it, then push with `git push origin HEAD:main`. Never force-push.

### Task 2: Back Up and Deploy the Exact Commit

**Files:**
- Read: committed Git tree
- Preserve: `/opt/mmn-perception-engine/.env`
- Create on ECS: `/opt/mmn-perception-engine/backups/releases/tikhub_social_evidence_<timestamp>_pre/`

**Interfaces:**
- Consumes: the pushed release commit and its Git archive SHA-256.
- Produces: ECS source tree matching the archive, healthy application containers, and a running `mmn-social-evidence-worker`.

- [ ] **Step 1: Create production rollback evidence**

Before changing source or environment, save the current source archive, `.env` copy with mode `600`, Docker Compose configuration, container state, and SQLite online backups. Run `PRAGMA quick_check` on each protected SQLite database and record SHA-256 hashes.

- [ ] **Step 2: Build and verify the release archive**

Create `git archive` from the pushed commit, calculate local SHA-256, transfer with SCP, calculate remote SHA-256, and require exact equality before extraction.

- [ ] **Step 3: Apply source without replacing runtime state**

Extract the verified archive into `/opt/mmn-perception-engine` while preserving `.env`, `backups/`, logs, and Docker volumes. Do not copy local `data/` or SQLite files.

- [ ] **Step 4: Enable the production boundary**

Update only these production `.env` keys without printing values:

```dotenv
MMN_SOCIAL_EVIDENCE_V2_ENABLED=true
MMN_SOCIAL_EVIDENCE_WORKER_MODE=external
COMPOSE_PROFILES=social-evidence-v2
```

Require `TIKHUB_API_KEY` to remain present and non-empty.

- [ ] **Step 5: Deploy**

Run:

```bash
MMN_SKIP_GIT_PULL=true bash deploy.sh
```

Expected: the original six services plus `mmn-social-evidence-worker`; health-checked services are healthy and the web proxy is reachable.

### Task 3: Prove Production and Close the Release

**Files:**
- Modify after evidence: `release.md`
- Read-only verification: production API, logs, Docker volume SQLite files.

**Interfaces:**
- Consumes: administrator-authenticated public API and one bounded Douyin query.
- Produces: public capability proof, one ready evidence job, non-empty normalized evidence, clean logs, database integrity, and a rollback-ready release record.

- [ ] **Step 1: Verify infrastructure and version**

Require public `/api/health` HTTP 200 with exact version code, `/api/social-evidence/capabilities` showing `enabled=true`, `clientEnabled=true`, `workerMode=external`, and seven running Compose services including the worker.

- [ ] **Step 2: Authenticate through the public boundary**

Use existing production credentials without printing them. Require login success and use the returned session only for the bounded acceptance flow.

- [ ] **Step 3: Run one billed Douyin job**

Preview a one-platform, one-page, one-request `social_trend` plan, submit it once, and poll the job to `ready` or an explicit evidence-bounded terminal state. Do not retry.

- [ ] **Step 4: Validate evidence and leakage boundaries**

Require a non-empty public Mart plus persisted item ID, source URL, publication time, text, and native metrics. Scan public API/UI responses for supplier names, bearer data, API-key labels, prompts, and internal stack traces.

- [ ] **Step 5: Verify integrity and logs**

Require `PRAGMA quick_check=ok` for the main and social-evidence databases. Scan application, worker, scheduler, and proxy logs for new Traceback, ERROR, 5xx, authorization leakage, or secret fragments.

- [ ] **Step 6: Record closure and rollback**

Append the pushed application commit, archive SHA-256, backup paths, container state, capability result, job ID, Mart ID, test totals, data-integrity result, and residual billing limitation to `release.md`; push the documentation-only closure commit to `main` without redeploying application code.

Rollback uses the pre-release source and `.env` backups plus Docker volume/database backups, followed by `MMN_SKIP_GIT_PULL=true bash deploy.sh` and the same health/integrity checks.
