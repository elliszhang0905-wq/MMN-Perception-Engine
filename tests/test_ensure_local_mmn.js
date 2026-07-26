const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const source = fs.readFileSync(path.join(__dirname, "..", "scripts", "ensure_local_mmn.sh"), "utf8");
const watchdog = fs.readFileSync(path.join(__dirname, "..", "scripts", "run_local_mmn_watchdog.sh"), "utf8");

assert.match(source, /server_pid\(\) \{[\s\S]*?lsof[^\n]+\| head -n 1 \|\| true[\s\S]*?\}/);
assert.match(source, /SCRIPT_DIR="\$\(cd "\$\(dirname "\$0"\)" && pwd -P\)"/);
assert.match(source, /PROJECT_DIR="\$\(cd "\$\{SCRIPT_DIR\}\/\.\." && pwd -P\)"/);
assert.match(watchdog, /SCRIPT_DIR="\$\(cd "\$\(dirname "\$0"\)" && pwd -P\)"/);
assert.match(watchdog, /PROJECT_DIR="\$\(cd "\$\{SCRIPT_DIR\}\/\.\." && pwd -P\)"/);

function functionBody(name, nextName) {
  const start = source.indexOf(`${name}() {`);
  const end = nextName ? source.indexOf(`${nextName}() {`, start) : source.length;
  assert.ok(start >= 0 && end > start, `${name} should be discoverable`);
  return source.slice(start, end);
}

assert.match(functionBody("stop_stale_server", "stop_stuck_server"), /return 0\s*\n}\s*$/);
assert.match(functionBody("stop_stuck_server", "start_server"), /return 0\s*\n}\s*$/);
assert.match(source, /server_cwd\(\) \{[\s\S]*?lsof -a -p "\$\{pid\}" -d cwd -Fn/);
assert.match(source, /server_matches_project\(\) \{[\s\S]*?"\$\(server_cwd\)" == "\$\{PROJECT_DIR\}"/);
assert.match(functionBody("stop_foreign_server", "backend_code_is_newer"), /has_active_local_jobs/);
assert.match(functionBody("stop_foreign_server", "backend_code_is_newer"), /local_mmn_watchdog\.pid/);
assert.match(functionBody("start_server", ""), /is_healthy && server_matches_project/);
assert.match(source, /screen -dmS mmn_local_watchdog zsh scripts\/run_local_mmn_watchdog\.sh/);
assert.match(source, /local_mmn_watchdog\.pid/);
assert.match(watchdog, /echo "\$\$" >"\$\{WATCHDOG_PID_FILE\}"/);
assert.match(watchdog, /local_mmn_watchdog\.lock/);
assert.match(watchdog, /trap shutdown TERM INT HUP/);
assert.match(watchdog, /trap cleanup EXIT/);
assert.match(watchdog, /while true; do/);
assert.match(watchdog, /backend_code_is_newer/);
assert.match(watchdog, /activeLocalJobs/);
assert.match(watchdog, /检测到本地后端代码更新，正在自动同步服务/);
assert.match(watchdog, /kill "\$\{child_pid\}"/);
assert.match(source, /find \. -type f -name '\*\.py'/);
assert.match(watchdog, /exit_code=0\s+wait "\$\{child_pid\}" \|\| exit_code=\$\?/);
assert.match(watchdog, /sleep 2/);

console.log("local MMN ensure script: ok");
