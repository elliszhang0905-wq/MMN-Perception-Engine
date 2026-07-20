const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const source = fs.readFileSync(path.join(__dirname, "..", "scripts", "ensure_local_mmn.sh"), "utf8");
const watchdog = fs.readFileSync(path.join(__dirname, "..", "scripts", "run_local_mmn_watchdog.sh"), "utf8");

assert.match(source, /server_pid\(\) \{[\s\S]*?lsof[^\n]+\| head -n 1 \|\| true[\s\S]*?\}/);

function functionBody(name, nextName) {
  const start = source.indexOf(`${name}() {`);
  const end = source.indexOf(`${nextName}() {`, start);
  assert.ok(start >= 0 && end > start, `${name} should be discoverable`);
  return source.slice(start, end);
}

assert.match(functionBody("stop_stale_server", "stop_stuck_server"), /return 0\s*\n}\s*$/);
assert.match(functionBody("stop_stuck_server", "start_server"), /return 0\s*\n}\s*$/);
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
