const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.join(__dirname, "..");
const html = fs.readFileSync(path.join(root, "index.html"), "utf8");
const app = fs.readFileSync(path.join(root, "app.js"), "utf8");
const css = fs.readFileSync(path.join(root, "style.css"), "utf8");

assert.match(
  html,
  /data-file-target="vertical-image-file"[^>]*>导入懂车帝周榜图片<\/button>[\s\S]*?id="vertical-image-file"[^>]*accept="image\/png,image\/jpeg,image\/webp"/,
);
assert.match(html, /id="vertical-image-review-dialog"/);
assert.match(html, /id="vertical-image-original"/);
assert.match(html, /id="vertical-image-own-model"/);
assert.match(html, /id="vertical-image-own-confirmed"/);
assert.match(html, /我已确认原图为懂车帝周榜，且本品车型与当前项目一致/);
assert.match(html, /id="vertical-image-period-start"/);
assert.match(html, /id="vertical-image-period-end"/);
assert.match(html, /id="vertical-image-review-rows"/);
assert.match(html, /id="vertical-image-confirm"/);
assert.match(html, /id="vertical-image-confirm"[^>]*aria-describedby="vertical-image-review-message"[^>]*disabled/);

assert.match(app, /\/api\/vertical-rank-image\/preview/);
assert.match(app, /\/api\/vertical-rank-image\/confirm/);
assert.match(app, /ownModelConfirmed:true/);
assert.match(app, /function renderVerticalImagePreview\(/);
assert.match(app, /function verticalImageConfirmationPayload\(/);
assert.match(app, /function verticalImageConfirmState\(/);
assert.match(app, /function applyVerticalImportedDataset\(/);
assert.match(app, /还需完成：/);
const imageFlow = app.slice(
  app.indexOf("function closeVerticalImageReview("),
  app.indexOf('document.querySelector("#clear-vertical-data")'),
);
assert.doesNotMatch(imageFlow, /Tesseract|Vision|OpenAI|Qwen|DeepSeek/);
assert.doesNotMatch(imageFlow, /\besc\(/);

assert.match(css, /\.vertical-image-review-layout/);
assert.match(css, /@media \(max-width:\s*600px\)[\s\S]*?\.vertical-image-review-layout/);
assert.match(css, /#vertical-image-confirm:disabled\{[^}]*cursor:not-allowed[^}]*box-shadow:none/);

const confirmStateStart = app.indexOf("function verticalImageConfirmState(");
const confirmStateEnd = app.indexOf("function renderVerticalImagePreview(", confirmStateStart);
assert.ok(confirmStateStart >= 0 && confirmStateEnd > confirmStateStart, "image confirmation state helpers should be discoverable");
const fields = {
  own: {value: "智己LS6"},
  confirmed: {checked: false},
  start: {value: "2026-07-13"},
  end: {value: "2026-07-19"},
};
const button = {disabled: false};
const classes = new Set();
const message = {
  textContent: "",
  classList: {
    remove(...names) { names.forEach(name => classes.delete(name)); },
    toggle(name, force) { if(force)classes.add(name);else classes.delete(name); },
  },
};
const completeRow = {
  querySelector(selector) {
    if(selector.includes("normalizedModel"))return{value: "极氪7X"};
    return{value: "1"};
  },
};
const context = {
  Date,
  Number,
  verticalImagePreview: {previewId: "preview-1"},
  document: {
    querySelector(selector) {
      return {
        "#vertical-image-own-model": fields.own,
        "#vertical-image-own-confirmed": fields.confirmed,
        "#vertical-image-period-start": fields.start,
        "#vertical-image-period-end": fields.end,
        "#vertical-image-confirm": button,
        "#vertical-image-review-message": message,
      }[selector];
    },
    querySelectorAll() { return [completeRow]; },
  },
};
vm.runInNewContext(
  `${app.slice(confirmStateStart, confirmStateEnd)}\nthis.confirmStateApi={verticalImageConfirmState,updateVerticalImageConfirmState};`,
  context,
);
context.confirmStateApi.updateVerticalImageConfirmState();
assert.equal(button.disabled, true, "unchecked own-model confirmation must keep the action disabled");
assert.match(message.textContent, /勾选“我已确认原图为懂车帝周榜，且本品车型与当前项目一致”/);
assert.equal(classes.has("ready"), false);

fields.confirmed.checked = true;
context.confirmStateApi.updateVerticalImageConfirmState();
assert.equal(button.disabled, false, "complete confirmation data must enable the action");
assert.match(message.textContent, /可以纳入正式竞争格局/);
assert.equal(classes.has("ready"), true);

fields.end.value = "2026-07-20";
context.confirmStateApi.updateVerticalImageConfirmState();
assert.equal(button.disabled, true, "a period longer than seven days must disable the action");
assert.match(message.textContent, /将周期调整为连续7天/);

console.log("vertical rank image ui contract: ok");
