# Thailand Social Dashboard Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release only the Thailand Social Media core dashboard from an isolated clean main-based worktree to GitHub and the MMN ECS environment.

**Architecture:** Keep the dashboard as a static JSON contract plus standalone JavaScript and CSS, wired into the existing global-edition cockpit. Build a commit archive, verify its SHA-256 remotely, preserve production environment and persistent data, then rebuild the existing Compose stack and verify the live proxy flow.

**Tech Stack:** HTML, CSS, browser JavaScript, Python HTTP server, Node/Python release gates, Git archive, SSH, Docker Compose.

## Global Constraints

- Exclude every unrelated dirty-worktree change and every local database, backup, output, and experiment file.
- Preserve production `.env`, `/app/data`, database contents, and rollback backups.
- Keep the dashboard hidden in the China edition and keep missing metrics fail-closed.
- Do not modify Sales Credo or MMN Essence.

---

### Task 1: Build the isolated release candidate

**Files:**
- Create: `data/thailand_social_market_latest.json`
- Create: `thailand-social-dashboard.js`
- Create: `thailand-social-dashboard.css`
- Modify: `index.html`
- Modify: `server.py`
- Test: `tests/test_thailand_social_dashboard_ui.js`

- [ ] Copy only the audited dashboard contract, renderer, stylesheet, focused test, and exact HTML/server integration points.
- [ ] Update the application version to `beta-1.03-20260901-thailand-social-dashboard-1`.
- [ ] Run the focused test, syntax checks, static boundary test, full release gate, and state gate.

### Task 2: Create the auditable release commit

**Files:**
- Modify: `release.md`
- Create: `docs/研发档案/2026-09-01_beta-1.03_泰国Social-Media核心看板.md`

- [ ] Review the exact diff and secret scan.
- [ ] Commit the release candidate, push the release branch, fast-forward `main`, and create the exact version tag.
- [ ] Generate `git archive` from the release commit and record its SHA-256.

### Task 3: Deploy with data protection

**Files:**
- Deploy: `/opt/mmn-perception-engine`

- [ ] Capture production container, health, data-table and application-file baselines.
- [ ] Back up source, `.env`, and persistent databases before extraction.
- [ ] Upload the archive, compare remote SHA-256 with the local expected value, and stop on mismatch.
- [ ] Extract the verified archive while preserving runtime data and environment, then run the existing deployment script.

### Task 4: Verify and close the release

**Files:**
- Modify: `release.md`
- Modify: `docs/研发档案/2026-09-01_beta-1.03_泰国Social-Media核心看板.md`

- [ ] Verify exact version, six Compose services, proxy health, static resource MIME and source/container hashes.
- [ ] Exercise the authenticated global-edition dashboard at 1440px and 390px; verify metric switching, missing-value display, China-edition isolation, console and network.
- [ ] Compare production database logic and `quick_check` before/after, and inspect recent app/web/scheduler logs for severe errors and 5xx.
- [ ] Add exact commit, archive hash, backup paths, live-flow evidence and residual risks to the release records; commit and push the documentation closure.
