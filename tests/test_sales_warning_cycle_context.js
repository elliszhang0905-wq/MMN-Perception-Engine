const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const cycle = require("../t-cycle.js");
const adapter = require("../sales-warning-cycle-context.js");

const records = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "data", "sales_warning_cycles.json"), "utf8"));
for (const [seriesId, record] of Object.entries(records)) {
  const context = adapter.adapt({seriesId, model: record.model}, {serverCycles: records});
  assert.equal(context.status, "verified");
  assert.equal(context.source, "sales-warning-server");
  assert.equal(context.launchDate, record.launchDate);
  assert.equal(context.assessmentDate, record.assessmentDate);
  assert.equal(context.tLabel, record.tLabel);
  assert.equal(context.phaseKey, record.phaseKey);
  assert.equal(context.phaseRange, record.phaseRange);
  assert.equal(cycle.phases.map((phase) => cycle.phaseDates(context.launchDate, phase)).filter((dates) => dates.start).length, 7);
}

const item = {seriesId: "5828", model: "MG4"};
const server = records["5828"];
const wrongLocal = {...server, launchDate: "2026-01-01", assessmentDate: "2026-07-17", dayOffset: 197, tLabel: "T+197", phaseKey: "alwayson", phaseLabel: "常态经营期", phaseRange: "T+121起", reviewedAt: "2099-01-01"};
assert.equal(adapter.adapt(item, {serverCycles: {5828: server}, localCycles: {5828: wrongLocal}}).launchDate, "2026-04-24", "server verified record must outrank a newer local value");
assert.equal(adapter.adapt(item, {localCycles: {5828: server}}).source, "sales-warning-cache");
assert.equal(adapter.adapt(item, {serverCycles: {5828: {...server, model: "奥迪E7X"}}}).status, "missing", "a different model record must never cross-fill the selected vehicle");
assert.equal(adapter.adapt(item, {serverCycles: {5828: {...server, status: "pending_review"}}}).status, "pending_review");
assert.equal(adapter.adapt(item, {serverCycles: {5828: {...server, launchDate: "2026-02-30"}}}).status, "missing");
assert.equal(adapter.adapt(item).status, "missing");

console.log("sales warning cycle context: ok");
