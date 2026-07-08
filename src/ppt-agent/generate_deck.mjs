import fs from "node:fs";
import path from "node:path";
import pptxgen from "pptxgenjs";
import { brandFrom, box, SLIDE } from "./theme.mjs";

function parseArgs() {
  const args = process.argv.slice(2);
  const out = {};
  for (let i = 0; i < args.length; i += 2) out[args[i].replace(/^--/, "")] = args[i + 1];
  return {
    input: out.input || "examples/input/page-structure.json",
    outdir: out.outdir || "examples/output"
  };
}

function addTrackedText(slide, manifestSlide, id, text, opts, role) {
  slide.addText(text, opts);
  manifestSlide.elements.push(box(id, role, opts.x, opts.y, opts.w, opts.h, {
    text: typeof text === "string" ? text : text.map((t) => t.text).join(""),
    fontSize: opts.fontSize || 14,
    color: opts.color,
    level: role === "title" ? 1 : undefined
  }));
}

function addTrackedShape(slide, pres, manifestSlide, id, shape, opts, role) {
  slide.addShape(shape || pres.ShapeType.rect, opts);
  manifestSlide.elements.push(box(id, role, opts.x, opts.y, opts.w, opts.h, {
    fill: opts.fill?.color,
    line: opts.line?.color
  }));
}

function addHeader(slide, manifestSlide, s, brand) {
  addTrackedText(slide, manifestSlide, `${s.id}-section`, s.section || "", {
    x: SLIDE.marginX,
    y: 0.22,
    w: 2.6,
    h: 0.22,
    fontFace: brand.fontFace,
    fontSize: 7.5,
    bold: true,
    color: brand.secondary,
    margin: 0
  }, "section-label");
  addTrackedText(slide, manifestSlide, `${s.id}-title`, s.title || "", {
    x: SLIDE.marginX,
    y: SLIDE.titleY,
    w: 10.2,
    h: 0.58,
    fontFace: brand.fontFace,
    fontSize: 19,
    bold: true,
    color: brand.primary,
    margin: 0,
    breakLine: false,
    fit: "shrink"
  }, "title");
}

function addFooter(pres, slide, manifestSlide, s, total, brand) {
  addTrackedShape(slide, pres, manifestSlide, `${s.id}-footer-line`, pres.ShapeType.line, {
    x: SLIDE.marginX,
    y: SLIDE.footerY - 0.12,
    w: SLIDE.width - SLIDE.marginX * 2,
    h: 0,
    line: { color: "D9DEE5", width: 0.7 }
  }, "divider");
  addTrackedText(slide, manifestSlide, `${s.id}-page`, `${s.pageNumber}/${total}`, {
    x: SLIDE.width - 1.2,
    y: SLIDE.footerY,
    w: 0.65,
    h: 0.18,
    fontFace: "Aptos",
    fontSize: 7.5,
    color: brand.muted,
    align: "right",
    margin: 0
  }, "page-number");
}

function drawCover(pres, slide, manifestSlide, s, brand) {
  slide.background = { color: brand.primary };
  addTrackedShape(slide, pres, manifestSlide, `${s.id}-gold-bar`, pres.ShapeType.rect, {
    x: 0,
    y: 0,
    w: 0.18,
    h: SLIDE.height,
    fill: { color: brand.secondary },
    line: { color: brand.secondary }
  }, "accent");
  addTrackedText(slide, manifestSlide, `${s.id}-kicker`, s.kicker || "", {
    x: 0.72,
    y: 0.62,
    w: 5.2,
    h: 0.25,
    fontFace: "Aptos",
    fontSize: 9,
    color: brand.secondary,
    bold: true,
    margin: 0
  }, "kicker");
  addTrackedText(slide, manifestSlide, `${s.id}-title`, s.title, {
    x: 0.72,
    y: 2.22,
    w: 8.8,
    h: 1.05,
    fontFace: brand.fontFace,
    fontSize: 28,
    color: "FFFFFF",
    bold: true,
    margin: 0,
    fit: "shrink"
  }, "title");
  addTrackedText(slide, manifestSlide, `${s.id}-subtitle`, s.subtitle || "", {
    x: 0.74,
    y: 3.45,
    w: 8.4,
    h: 0.54,
    fontFace: brand.fontFace,
    fontSize: 13,
    color: "E6EBF0",
    margin: 0,
    fit: "shrink"
  }, "subtitle");
  addTrackedShape(slide, pres, manifestSlide, `${s.id}-signal`, pres.ShapeType.rect, {
    x: 10.45,
    y: 1.08,
    w: 1.95,
    h: 4.6,
    fill: { color: brand.secondary, transparency: 10 },
    line: { color: brand.secondary, transparency: 100 }
  }, "visual");
}

function drawToc(pres, slide, manifestSlide, s, brand) {
  addHeader(slide, manifestSlide, s, brand);
  (s.items || []).forEach((item, idx) => {
    const y = 1.62 + idx * 1.05;
    addTrackedText(slide, manifestSlide, `${s.id}-toc-num-${idx + 1}`, String(idx + 1).padStart(2, "0"), {
      x: 1.0,
      y,
      w: 0.48,
      h: 0.3,
      fontFace: "Aptos",
      fontSize: 12,
      bold: true,
      color: brand.secondary,
      margin: 0
    }, "toc-number");
    addTrackedText(slide, manifestSlide, `${s.id}-toc-${idx + 1}`, item.label, {
      x: 1.62,
      y: y - 0.04,
      w: 7.8,
      h: 0.4,
      fontFace: brand.fontFace,
      fontSize: 16,
      bold: true,
      color: brand.text,
      margin: 0,
      fit: "shrink"
    }, "toc-item");
    addTrackedText(slide, manifestSlide, `${s.id}-toc-target-${idx + 1}`, item.targetSlideId, {
      x: 9.8,
      y,
      w: 1.35,
      h: 0.24,
      fontFace: "Aptos",
      fontSize: 8,
      color: brand.muted,
      margin: 0
    }, "toc-target");
  });
}

function drawSummary(pres, slide, manifestSlide, s, brand) {
  addHeader(slide, manifestSlide, s, brand);
  addTrackedShape(slide, pres, manifestSlide, `${s.id}-insight-bg`, pres.ShapeType.rect, {
    x: 0.72,
    y: 1.28,
    w: 11.9,
    h: 1.0,
    fill: { color: brand.neutral },
    line: { color: brand.neutral }
  }, "insight-band");
  addTrackedText(slide, manifestSlide, `${s.id}-insight`, s.insight, {
    x: 1.0,
    y: 1.54,
    w: 11.1,
    h: 0.34,
    fontFace: brand.fontFace,
    fontSize: 15,
    bold: true,
    color: brand.primary,
    margin: 0,
    fit: "shrink"
  }, "insight");
  (s.cards || []).forEach((card, idx) => {
    const x = 0.72 + idx * 4.05;
    addTrackedShape(slide, pres, manifestSlide, `${s.id}-card-${idx + 1}`, pres.ShapeType.rect, {
      x,
      y: 2.78,
      w: 3.55,
      h: 2.45,
      fill: { color: "FFFFFF" },
      line: { color: "D9DEE5", width: 0.8 }
    }, "metric-card");
    addTrackedText(slide, manifestSlide, `${s.id}-card-label-${idx + 1}`, card.label, {
      x: x + 0.28,
      y: 3.08,
      w: 2.65,
      h: 0.22,
      fontFace: brand.fontFace,
      fontSize: 9,
      bold: true,
      color: brand.muted,
      margin: 0
    }, "metric-label");
    addTrackedText(slide, manifestSlide, `${s.id}-card-value-${idx + 1}`, card.value, {
      x: x + 0.28,
      y: 3.55,
      w: 2.4,
      h: 0.55,
      fontFace: "Aptos",
      fontSize: 26,
      bold: true,
      color: idx === 0 ? brand.accent : brand.primary,
      margin: 0
    }, "metric-value");
    addTrackedText(slide, manifestSlide, `${s.id}-card-note-${idx + 1}`, card.note, {
      x: x + 0.28,
      y: 4.36,
      w: 2.9,
      h: 0.42,
      fontFace: brand.fontFace,
      fontSize: 9.5,
      color: brand.text,
      margin: 0,
      fit: "shrink"
    }, "body");
  });
}

function drawChart(pres, slide, manifestSlide, s, brand) {
  addHeader(slide, manifestSlide, s, brand);
  const chart = s.chart || {};
  const data = [{ name: chart.unit || "value", labels: chart.categories || [], values: chart.values || [] }];
  slide.addChart(pres.ChartType.bar, data, {
    x: 0.78,
    y: 1.35,
    w: 7.7,
    h: 4.45,
    catAxisLabelFontFace: brand.fontFace,
    catAxisLabelFontSize: 8,
    valAxisLabelFontSize: 8,
    showLegend: false,
    showTitle: false,
    valAxisMinVal: 0,
    showValue: true,
    dataLabelPosition: "outEnd",
    dataLabelFontSize: 8,
    chartColors: [brand.accent, brand.secondary, brand.primary]
  });
  manifestSlide.elements.push(box(`${s.id}-chart`, "chart", 0.78, 1.35, 7.7, 4.45, {
    categories: chart.categories || [],
    values: chart.values || [],
    fontSize: 8,
    color: brand.text
  }));
  (s.notes || []).forEach((note, idx) => {
    addTrackedText(slide, manifestSlide, `${s.id}-note-${idx + 1}`, note, {
      x: 9.05,
      y: 1.55 + idx * 1.15,
      w: 3.0,
      h: 0.72,
      fontFace: brand.fontFace,
      fontSize: 10.5,
      color: brand.text,
      margin: 0.05,
      fit: "shrink",
      breakLine: false
    }, "body");
  });
}

function drawRoadmap(pres, slide, manifestSlide, s, brand) {
  addHeader(slide, manifestSlide, s, brand);
  (s.phases || []).forEach((phase, idx) => {
    const x = 0.72 + idx * 4.08;
    addTrackedShape(slide, pres, manifestSlide, `${s.id}-phase-${idx + 1}`, pres.ShapeType.rect, {
      x,
      y: 1.52,
      w: 3.55,
      h: 4.6,
      fill: { color: idx === 0 ? brand.neutral : "FFFFFF" },
      line: { color: idx === 1 ? brand.secondary : "D9DEE5", width: idx === 1 ? 1.2 : 0.8 }
    }, "phase-card");
    addTrackedText(slide, manifestSlide, `${s.id}-phase-name-${idx + 1}`, phase.name, {
      x: x + 0.28,
      y: 1.88,
      w: 1.6,
      h: 0.24,
      fontFace: "Aptos",
      fontSize: 9,
      bold: true,
      color: brand.secondary,
      margin: 0
    }, "phase-label");
    addTrackedText(slide, manifestSlide, `${s.id}-phase-headline-${idx + 1}`, phase.headline, {
      x: x + 0.28,
      y: 2.34,
      w: 2.8,
      h: 0.38,
      fontFace: brand.fontFace,
      fontSize: 16,
      bold: true,
      color: brand.primary,
      margin: 0,
      fit: "shrink"
    }, "subtitle");
    const bullets = (phase.items || []).map((item, bulletIdx) => ({
      text: item,
      options: { bullet: true, breakLine: bulletIdx < phase.items.length - 1 }
    }));
    addTrackedText(slide, manifestSlide, `${s.id}-phase-items-${idx + 1}`, bullets, {
      x: x + 0.38,
      y: 3.18,
      w: 2.72,
      h: 1.42,
      fontFace: brand.fontFace,
      fontSize: 10.2,
      color: brand.text,
      breakLine: true,
      fit: "shrink",
      margin: 0.02,
      paraSpaceAfterPt: 8
    }, "body");
  });
}

async function main() {
  const args = parseArgs();
  const structure = JSON.parse(fs.readFileSync(args.input, "utf8"));
  fs.mkdirSync(args.outdir, { recursive: true });

  const brand = brandFrom(structure);
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.author = structure.meta?.author || "Codex";
  pres.company = "Codex";
  pres.subject = "Commercial consulting deck";
  pres.title = structure.meta?.title || "Consulting Deck";
  pres.lang = "zh-CN";
  pres.theme = {
    headFontFace: brand.fontFace,
    bodyFontFace: brand.fontFace,
    lang: "zh-CN"
  };
  pres.defineLayout({ name: "LAYOUT_WIDE", width: SLIDE.width, height: SLIDE.height });

  const manifest = { ...structure, generatedAt: new Date().toISOString(), slides: [] };
  const total = structure.slides.length;
  for (const s of structure.slides) {
    const slide = pres.addSlide();
    slide.background = { color: brand.background };
    const manifestSlide = { ...s, elements: [] };
    if (s.type === "cover") drawCover(pres, slide, manifestSlide, s, brand);
    else if (s.type === "toc") drawToc(pres, slide, manifestSlide, s, brand);
    else if (s.type === "summary") drawSummary(pres, slide, manifestSlide, s, brand);
    else if (s.type === "chart") drawChart(pres, slide, manifestSlide, s, brand);
    else if (s.type === "roadmap") drawRoadmap(pres, slide, manifestSlide, s, brand);
    else addHeader(slide, manifestSlide, s, brand);
    addFooter(pres, slide, manifestSlide, s, total, brand);
    manifest.slides.push(manifestSlide);
  }

  const pptxPath = path.join(args.outdir, "mmn-strategy-deck.pptx");
  const jsonPath = path.join(args.outdir, "page-structure.generated.json");
  await pres.writeFile({ fileName: pptxPath });
  fs.writeFileSync(jsonPath, JSON.stringify(manifest, null, 2));
  fs.copyFileSync(new URL(import.meta.url), path.join(args.outdir, "generated-source.generate_deck.mjs"));
  console.log(JSON.stringify({ pptx: pptxPath, structure: jsonPath }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
