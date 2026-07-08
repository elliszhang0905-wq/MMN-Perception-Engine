import fs from "node:fs";
import JSZip from "jszip";
import { XMLParser } from "fast-xml-parser";
import { brandFrom, normalizeHex, SLIDE } from "./theme.mjs";

function parseArgs() {
  const args = process.argv.slice(2);
  const out = {};
  for (let i = 0; i < args.length; i += 2) out[args[i].replace(/^--/, "")] = args[i + 1];
  return {
    structure: out.structure || "examples/output/page-structure.generated.json",
    pptx: out.pptx || "output/ppt-agent/mmn-strategy-deck.pptx",
    out: out.out || "output/ppt-agent/validation-report.json"
  };
}

function fail(issues, slide, rule, message, severity = "error", elementId = null) {
  issues.push({ severity, slideId: slide?.id, pageNumber: slide?.pageNumber, elementId, rule, message });
}

function boxesOverlap(a, b) {
  const pad = 0.015;
  return a.x + pad < b.x + b.w && a.x + a.w > b.x + pad && a.y + pad < b.y + b.h && a.y + a.h > b.y + pad;
}

function isText(el) {
  return typeof el.text === "string" && el.text.trim();
}

function chineseChars(text) {
  return Array.from(text).filter((ch) => /[\u3400-\u9fff]/.test(ch)).length;
}

function capacity(el) {
  const fontSize = el.fontSize || 12;
  const charsPerLine = Math.max(4, Math.floor((el.w * 96) / (fontSize * 0.82)));
  const lines = Math.max(1, Math.floor((el.h * 96) / (fontSize * 1.35)));
  return charsPerLine * lines;
}

function validateStructure(structure) {
  const issues = [];
  const brand = brandFrom(structure);
  const allowedColors = new Set(Object.values(brand).filter((v) => /^[0-9a-fA-F]{6}$/.test(String(v))).map(normalizeHex));
  const slides = structure.slides || [];
  const ids = new Set(slides.map((s) => s.id));

  slides.forEach((slide, idx) => {
    if (slide.pageNumber !== idx + 1) fail(issues, slide, "page-number-sequence", `页码应为 ${idx + 1}，当前为 ${slide.pageNumber}`);
    const titles = (slide.elements || []).filter((el) => el.role === "title");
    if (titles.length !== 1) fail(issues, slide, "title-hierarchy", `每页必须有且仅有一个一级标题，当前为 ${titles.length}`);
    const textEls = (slide.elements || []).filter(isText);
    textEls.forEach((el) => {
      const zh = chineseChars(el.text);
      const max = capacity(el);
      if (zh > max) fail(issues, slide, "chinese-overflow", `中文文本估算 ${zh} 字，文本框容量约 ${max} 字`, "error", el.id);
      if (el.color && !allowedColors.has(normalizeHex(el.color)) && normalizeHex(el.color) !== "FFFFFF" && normalizeHex(el.color) !== "E6EBF0") {
        fail(issues, slide, "brand-color", `文本颜色 ${el.color} 不在品牌色板中`, "warning", el.id);
      }
    });
    const meaningful = (slide.elements || []).filter((el) => !["divider", "page-number", "section-label"].includes(el.role));
    for (let i = 0; i < meaningful.length; i += 1) {
      for (let j = i + 1; j < meaningful.length; j += 1) {
        const a = meaningful[i];
        const b = meaningful[j];
        const allowContainer = ["metric-card", "phase-card", "insight-band"].includes(a.role) || ["metric-card", "phase-card", "insight-band"].includes(b.role);
        if (!allowContainer && boxesOverlap(a, b)) fail(issues, slide, "element-overlap", `${a.id} 与 ${b.id} 可能重叠`, "error", `${a.id},${b.id}`);
      }
    }
    const charts = (slide.elements || []).filter((el) => el.role === "chart");
    charts.forEach((chart) => {
      if ((chart.categories || []).length > 7) fail(issues, slide, "chart-readability", "图表分类超过 7 个，建议拆页或改表格", "warning", chart.id);
      if ((chart.fontSize || 0) < 8) fail(issues, slide, "chart-readability", "图表字号低于 8pt", "error", chart.id);
      if (chart.w < 5 || chart.h < 3) fail(issues, slide, "chart-readability", "图表区域过小，可能不可读", "error", chart.id);
    });
    const page = (slide.elements || []).find((el) => el.role === "page-number");
    if (!page || page.x + page.w > SLIDE.width || page.y + page.h > SLIDE.height) {
      fail(issues, slide, "page-number", "页码缺失或超出页面范围");
    }
  });

  const toc = slides.find((slide) => slide.type === "toc");
  if (toc) {
    (toc.items || []).forEach((item) => {
      if (!ids.has(item.targetSlideId)) fail(issues, toc, "toc-consistency", `目录目标不存在：${item.targetSlideId}`);
    });
  } else {
    fail(issues, slides[0], "toc-consistency", "缺少目录页");
  }
  return issues;
}

async function validatePptx(pptxPath, expectedSlides, issues) {
  const zip = await JSZip.loadAsync(fs.readFileSync(pptxPath));
  const slideFiles = Object.keys(zip.files).filter((name) => /^ppt\/slides\/slide\d+\.xml$/.test(name));
  if (slideFiles.length !== expectedSlides) {
    issues.push({ severity: "error", rule: "pptx-slide-count", message: `PPTX 实际页数 ${slideFiles.length} 与结构 JSON ${expectedSlides} 不一致` });
  }
  const parser = new XMLParser({ ignoreAttributes: false });
  const presXml = await zip.file("ppt/presentation.xml")?.async("string");
  if (!presXml) issues.push({ severity: "error", rule: "pptx-readable", message: "无法读取 ppt/presentation.xml" });
  else parser.parse(presXml);
}

async function main() {
  const args = parseArgs();
  const structure = JSON.parse(fs.readFileSync(args.structure, "utf8"));
  const issues = validateStructure(structure);
  await validatePptx(args.pptx, structure.slides.length, issues);
  const report = {
    ok: !issues.some((issue) => issue.severity === "error"),
    checkedAt: new Date().toISOString(),
    rules: [
      "chinese-overflow",
      "element-overlap",
      "title-hierarchy",
      "chart-readability",
      "brand-color",
      "page-number-sequence",
      "toc-consistency",
      "pptx-slide-count"
    ],
    issueCount: issues.length,
    issues
  };
  fs.writeFileSync(args.out, JSON.stringify(report, null, 2));
  console.log(JSON.stringify({ ok: report.ok, issueCount: report.issueCount, report: args.out }, null, 2));
  if (!report.ok) process.exit(1);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
