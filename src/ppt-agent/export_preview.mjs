import fs from "node:fs";
import path from "node:path";
import sharp from "sharp";
import { brandFrom, SLIDE } from "./theme.mjs";

function parseArgs() {
  const args = process.argv.slice(2);
  const out = {};
  for (let i = 0; i < args.length; i += 2) out[args[i].replace(/^--/, "")] = args[i + 1];
  return {
    input: out.input || "output/ppt-agent/page-structure.generated.json",
    outdir: out.outdir || "output/ppt-agent/previews"
  };
}

function esc(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function wrap(text, maxChars) {
  const chars = Array.from(String(text || ""));
  const lines = [];
  for (let i = 0; i < chars.length; i += maxChars) lines.push(chars.slice(i, i + maxChars).join(""));
  return lines.length ? lines : [""];
}

function renderText(el, scale, brand) {
  const fontSize = (el.fontSize || 12) * scale;
  const maxChars = Math.max(6, Math.floor((el.w * scale * 96) / (fontSize * 0.64)));
  const lines = wrap(el.text, maxChars).slice(0, Math.max(1, Math.floor((el.h * scale * 96) / (fontSize * 1.25))));
  const x = el.x * scale * 96;
  const y = el.y * scale * 96 + fontSize;
  const weight = ["title", "subtitle", "metric-value", "metric-label"].includes(el.role) ? 700 : 400;
  return `<text x="${x}" y="${y}" fill="#${el.color || brand.text}" font-family="${brand.fontFace}, Arial" font-size="${fontSize}" font-weight="${weight}">${lines.map((line, idx) => `<tspan x="${x}" dy="${idx === 0 ? 0 : fontSize * 1.25}">${esc(line)}</tspan>`).join("")}</text>`;
}

function renderElement(el, scale, brand) {
  const x = el.x * scale * 96;
  const y = el.y * scale * 96;
  const w = el.w * scale * 96;
  const h = el.h * scale * 96;
  if (el.role === "divider") return `<line x1="${x}" y1="${y}" x2="${x + w}" y2="${y + h}" stroke="#D9DEE5" stroke-width="1"/>`;
  if (["accent", "visual", "insight-band", "metric-card", "phase-card"].includes(el.role)) {
    return `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="#${el.fill || brand.neutral}" stroke="#${el.line || el.fill || "D9DEE5"}" stroke-width="1"/>`;
  }
  if (el.role === "chart") {
    const values = el.values || [];
    const max = Math.max(...values, 1);
    const bars = values.map((value, idx) => {
      const barW = (w - 40) / values.length;
      const barH = (value / max) * (h - 48);
      const bx = x + 20 + idx * barW;
      const by = y + h - barH - 28;
      return `<rect x="${bx}" y="${by}" width="${barW * 0.55}" height="${barH}" fill="#${idx === values.length - 1 ? brand.secondary : brand.accent}"/><text x="${bx}" y="${y + h - 8}" font-size="12" fill="#${brand.muted}">${esc((el.categories || [])[idx] || "")}</text>`;
    }).join("");
    return `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="#FFFFFF" stroke="#D9DEE5"/>${bars}`;
  }
  return renderText(el, scale, brand);
}

async function main() {
  const args = parseArgs();
  const structure = JSON.parse(fs.readFileSync(args.input, "utf8"));
  const brand = brandFrom(structure);
  fs.mkdirSync(args.outdir, { recursive: true });
  const scale = 1.5;
  const width = SLIDE.width * scale * 96;
  const height = SLIDE.height * scale * 96;

  for (const slide of structure.slides) {
    const bg = slide.type === "cover" ? brand.primary : brand.background;
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><rect width="100%" height="100%" fill="#${bg}"/>${(slide.elements || []).map((el) => renderElement(el, scale, brand)).join("")}</svg>`;
    const file = path.join(args.outdir, `${String(slide.pageNumber).padStart(2, "0")}-${slide.id}.png`);
    await sharp(Buffer.from(svg)).png().toFile(file);
  }
  console.log(JSON.stringify({ previews: args.outdir, count: structure.slides.length }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
