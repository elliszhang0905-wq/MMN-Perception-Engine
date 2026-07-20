import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const sourceRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const checkerSource = path.join(sourceRoot, "scripts", "check_mmn_state.mjs");
const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "mmn-state-check-"));

function run(cwd, command, args = []) {
  return spawnSync(command, args, { cwd, encoding: "utf8" });
}

function git(cwd, ...args) {
  const result = run(cwd, "git", args);
  assert.equal(result.status, 0, result.stderr || result.stdout);
  return result.stdout.trim();
}

function write(repo, relativePath, body = "fixture\n") {
  const target = path.join(repo, relativePath);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, body, "utf8");
}

function repo(name, { commit = true } = {}) {
  const root = path.join(tempRoot, name);
  fs.mkdirSync(path.join(root, "scripts"), { recursive: true });
  fs.copyFileSync(checkerSource, path.join(root, "scripts", "check_mmn_state.mjs"));
  git(root, "init", "-q");
  git(root, "config", "user.email", "mmn-state@example.invalid");
  git(root, "config", "user.name", "MMN State Test");
  if (commit) {
    write(root, "README.md");
    write(root, "MMN_CURRENT_STATE.md");
    git(root, "add", ".");
    git(root, "commit", "-qm", "initial");
  }
  return root;
}

function check(root, ...args) {
  return run(root, process.execPath, ["scripts/check_mmn_state.mjs", ...args]);
}

try {
  const worktree = repo("worktree");
  assert.equal(check(worktree).status, 0, "无改动场景应通过");
  write(worktree, "docs/note.md");
  write(worktree, "package-lock.json", "{}\n");
  write(worktree, "output/generated.mjs");
  write(worktree, "data/runtime.json", "{}\n");
  assert.equal(check(worktree).status, 0, "普通文档、锁文件和运行产物不应误报");
  write(worktree, "app.js");
  const missingState = check(worktree);
  assert.notEqual(missingState.status, 0, "业务源码改动且状态包未更新时应失败");
  assert.match(missingState.stderr, /app\.js/);
  write(worktree, "MMN_CURRENT_STATE.md", "updated state\n");
  assert.equal(check(worktree).status, 0, "业务源码与状态包同步修改时应通过");

  const firstCommit = repo("first-commit", { commit: false });
  write(firstCommit, "server.py");
  assert.notEqual(check(firstCommit).status, 0, "首次提交前的业务源码应被识别");
  write(firstCommit, "MMN_CURRENT_STATE.md");
  assert.equal(check(firstCommit).status, 0, "首次提交前同步状态包时应通过");

  const baseline = repo("baseline");
  write(baseline, "app.js", "baseline\n");
  write(baseline, "MMN_CURRENT_STATE.md", "baseline\n");
  git(baseline, "add", ".");
  git(baseline, "commit", "-qm", "baseline state");
  const baseRef = git(baseline, "rev-parse", "HEAD");
  write(baseline, "app.js", "changed\n");
  git(baseline, "add", "app.js");
  git(baseline, "commit", "-qm", "business change only");
  assert.notEqual(check(baseline, "--base", baseRef).status, 0, "指定基线时缺少状态更新应失败");
  write(baseline, "MMN_CURRENT_STATE.md", "updated\n");
  git(baseline, "add", "MMN_CURRENT_STATE.md");
  git(baseline, "commit", "-qm", "state update");
  assert.equal(check(baseline, "--base", baseRef).status, 0, "指定基线包含状态更新时应通过");

  const deletion = repo("deletion");
  write(deletion, "server.py");
  git(deletion, "add", ".");
  git(deletion, "commit", "-qm", "add server");
  fs.rmSync(path.join(deletion, "server.py"));
  assert.notEqual(check(deletion).status, 0, "删除业务源码也应要求状态更新");
  write(deletion, "MMN_CURRENT_STATE.md", "server removed\n");
  assert.equal(check(deletion).status, 0, "删除业务源码并同步状态包时应通过");

  console.log("MMN 状态包检查脚本测试通过：无改动、忽略项、缺失状态、首次提交、删除源码和指定基线场景均符合预期。");
} finally {
  fs.rmSync(tempRoot, { recursive: true, force: true });
}
