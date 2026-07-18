const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");

const app = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");

assert.match(app, /function consultingOutputText\(/);
assert.match(app, /"### Executive Conclusion"/);
assert.match(app, /"### Key Findings"/);
assert.match(app, /"### Evidence"/);
assert.match(app, /"### Strategic Implication"/);
assert.match(app, /"### Action Recommendation"/);
assert.match(app, /\[Evidence: E1\]/);
assert.match(app, /consultingMarkdown\(String\(result\.text\|\|""\)\)/);
assert.match(app, /requiredSections:\["Executive Conclusion","Key Findings","Evidence","Strategic Implication","Action Recommendation"\]/);

console.log("consulting output UI tests passed");
