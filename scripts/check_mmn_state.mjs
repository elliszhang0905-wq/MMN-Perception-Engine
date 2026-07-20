#!/usr/bin/env node

import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const STATE_FILE = "MMN_CURRENT_STATE.md";
const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

function fail(message) {
  console.error(`MMN 状态包检查失败：${message}`);
  process.exit(1);
}

function git(args, { allowFailure = false } = {}) {
  const result = spawnSync("git", args, {
    cwd: repoRoot,
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  });
  if (result.status !== 0 && !allowFailure) {
    fail((result.stderr || result.stdout || `git ${args.join(" ")} 执行失败`).trim());
  }
  return result;
}

function lines(output) {
  return String(output || "")
    .split(/\r?\n/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseArgs(argv) {
  let base = process.env.MMN_STATE_BASE_REF || "";
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--help" || arg === "-h") {
      console.log("用法：npm run check:mmn-state -- [--base <git-ref>]\n也可设置 MMN_STATE_BASE_REF。");
      process.exit(0);
    }
    if (arg === "--base") {
      base = argv[index + 1] || "";
      if (!base) fail("--base 后必须提供 Git ref。");
      index += 1;
      continue;
    }
    fail(`未知参数 ${arg}`);
  }
  return { base };
}

function hasCommit(ref = "HEAD") {
  return git(["rev-parse", "--verify", `${ref}^{commit}`], { allowFailure: true }).status === 0;
}

function changedFiles(base) {
  const files = new Set();
  const headExists = hasCommit();

  if (base) {
    if (!hasCommit(base)) fail(`比较基线不存在或不是提交：${base}`);
    if (headExists) {
      lines(git(["-c", "core.quotePath=false", "diff", "--name-only", "--diff-filter=ACMRD", `${base}...HEAD`]).stdout)
        .forEach((file) => files.add(file));
      lines(git(["-c", "core.quotePath=false", "diff", "--name-only", "--diff-filter=ACMRD", "HEAD"]).stdout)
        .forEach((file) => files.add(file));
    }
  } else if (headExists) {
    lines(git(["-c", "core.quotePath=false", "diff", "--name-only", "--diff-filter=ACMRD", "HEAD"]).stdout)
      .forEach((file) => files.add(file));
  } else {
    lines(git(["-c", "core.quotePath=false", "diff", "--cached", "--name-only", "--diff-filter=ACMRD"]).stdout)
      .forEach((file) => files.add(file));
  }

  lines(git(["-c", "core.quotePath=false", "ls-files", "--others", "--exclude-standard"]).stdout)
    .forEach((file) => files.add(file));
  return [...files].sort();
}

const LOCK_FILES = new Set([
  "package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock",
  "bun.lock", "bun.lockb", "poetry.lock", "uv.lock", "Pipfile.lock",
]);

function isTestFile(file) {
  return /(^|\/)(tests?|__tests__|fixtures?|snapshots?)(\/|$)/i.test(file)
    || /(^|\/)(test_|qa_)/i.test(file)
    || /\.(test|spec)\.[^.]+$/i.test(file);
}

function isOrdinaryDocumentation(file) {
  return file !== STATE_FILE && (/^docs\//i.test(file) || /(^|\/)README[^/]*$/i.test(file) || /\.md$/i.test(file));
}

function isRelevantChange(file) {
  const normalized = file.replaceAll("\\", "/");
  if (!normalized || normalized === STATE_FILE || normalized === "AGENTS.md") return false;
  if (/^(data|output|tmp|backups|logs)\//i.test(normalized)) return false;
  if (LOCK_FILES.has(normalized) || isTestFile(normalized) || isOrdinaryDocumentation(normalized)) return false;
  if (normalized === "scripts/check_mmn_state.mjs") return false;

  if (/^(package\.json|pyproject\.toml|Pipfile|requirements(?:-[^/]+)?\.txt)$/i.test(normalized)) return true;
  if (/^(Dockerfile(?:\..*)?|docker-compose(?:\.[^/]+)?\.ya?ml|compose(?:\.[^/]+)?\.ya?ml|\.env\.example)$/i.test(normalized)) return true;
  if (/^(deploy|infra|migrations|\.github\/workflows)\//i.test(normalized)) return true;
  if (/^(src|bf_factory|creator_distillation|mmn_eval)\//i.test(normalized)) return true;
  if (/^scripts\//i.test(normalized)) return true;
  if (/\.(py|js|mjs|cjs|ts|tsx|jsx|vue|svelte|css|scss|sass|less|html|sql)$/i.test(normalized)) return true;
  return false;
}

git(["rev-parse", "--is-inside-work-tree"]);
const { base } = parseArgs(process.argv.slice(2));
if (!fs.existsSync(path.join(repoRoot, STATE_FILE))) {
  fail(`根目录缺少 ${STATE_FILE}。`);
}
const files = changedFiles(base);
const relevant = files.filter(isRelevantChange);
const stateUpdated = files.includes(STATE_FILE);

if (relevant.length > 0 && !stateUpdated) {
  console.error("检测到需要同步系统状态包的改动：");
  relevant.forEach((file) => console.error(`  - ${file}`));
  fail(`请基于真实代码更新根目录 ${STATE_FILE} 后重新运行 npm run check:mmn-state。`);
}

if (files.length === 0) {
  console.log("MMN 状态包检查通过：当前没有改动。");
} else if (relevant.length === 0) {
  console.log(`MMN 状态包检查通过：${files.length} 个改动仅涉及测试、普通文档、锁文件或状态机制本身，无需更新状态包。`);
} else {
  console.log(`MMN 状态包检查通过：检测到 ${relevant.length} 个相关改动，且 ${STATE_FILE} 已同步修改。`);
}

if (base) console.log(`比较基线：${base}`);
