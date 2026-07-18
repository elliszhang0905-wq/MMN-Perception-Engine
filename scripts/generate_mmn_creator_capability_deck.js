const pptxgen = require('pptxgenjs');
const path = require('path');
const fs = require('fs');

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'MMN';
pptx.subject = 'MMN达人蒸馏与孵化能力介绍';
pptx.title = 'MMN达人蒸馏与孵化能力介绍';
pptx.company = 'MMN';
pptx.lang = 'zh-CN';
pptx.theme = {
  headFontFace: 'Hiragino Sans GB', bodyFontFace: 'Hiragino Sans GB', lang: 'zh-CN'
};
pptx.defineSlideMaster({
  title: 'MMN_MASTER',
  background: { color: '07162B' },
  objects: [
    { rect: { x: 0, y: 0, w: 13.333, h: 0.08, fill: { color: '23B7FF' }, line: { color: '23B7FF' } } },
    { text: { text: 'MMN · 汽车营销决策操作系统', options: { x: 0.5, y: 7.13, w: 4.5, h: 0.18, fontFace: 'Hiragino Sans GB', fontSize: 8, color: '7890AE', margin: 0 } } },
    { text: { text: '内部能力介绍 · 2026.07', options: { x: 10.6, y: 7.13, w: 2.2, h: 0.18, fontFace: 'Hiragino Sans GB', fontSize: 8, color: '7890AE', align: 'right', margin: 0 } } },
  ],
  slideNumber: { x: 12.85, y: 7.13, color: '7890AE', fontFace: 'Aptos', fontSize: 8 },
});

const C = {
  bg: '07162B', panel: '0C213D', panel2: '102A49', blue: '23B7FF', cyan: '40E0D0',
  orange: 'FFB24A', red: 'FF6B6B', green: '55D98A', white: 'F4F8FC', text: 'D7E4F1',
  muted: '8FA6BF', line: '244565', dark: '061121'
};

function addTitle(slide, kicker, title, subtitle) {
  slide.addText(kicker, { x: 0.55, y: 0.32, w: 5.2, h: 0.24, fontSize: 10, bold: true, color: C.blue, charSpacing: 1.2, margin: 0 });
  slide.addText(title, { x: 0.55, y: 0.62, w: 12.1, h: 0.52, fontSize: 25, bold: true, color: C.white, margin: 0, breakLine: false, fit: 'shrink' });
  if (subtitle) slide.addText(subtitle, { x: 0.57, y: 1.18, w: 11.9, h: 0.34, fontSize: 11, color: C.muted, margin: 0.02, fit: 'shrink' });
}

function card(slide, x, y, w, h, opts = {}) {
  slide.addShape(pptx.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.08,
    fill: { color: opts.fill || C.panel, transparency: opts.transparency || 0 },
    line: { color: opts.line || C.line, transparency: opts.lineTransparency || 0, width: opts.lineWidth || 1 },
    shadow: opts.shadow === false ? undefined : { type: 'outer', color: '000000', opacity: 0.18, blur: 1, angle: 45, distance: 1 }
  });
}

function label(slide, text, x, y, w, color = C.blue) {
  slide.addShape(pptx.ShapeType.roundRect, { x, y, w, h: 0.28, rectRadius: 0.05, fill: { color, transparency: 82 }, line: { color, transparency: 35 } });
  slide.addText(text, { x: x + 0.06, y: y + 0.055, w: w - 0.12, h: 0.14, fontSize: 8.5, bold: true, color, align: 'center', margin: 0, fit: 'shrink' });
}

function iconCircle(slide, text, x, y, color = C.blue, size = 0.48) {
  slide.addShape(pptx.ShapeType.ellipse, { x, y, w: size, h: size, fill: { color, transparency: 82 }, line: { color, width: 1.2 } });
  slide.addText(text, { x, y: y + size * 0.18, w: size, h: size * 0.35, fontSize: size * 20, bold: true, color, align: 'center', margin: 0, fit: 'shrink' });
}

function footerNote(slide, text) {
  slide.addText(text, { x: 0.58, y: 6.82, w: 11.9, h: 0.2, fontSize: 8, color: C.muted, italic: true, margin: 0, fit: 'shrink' });
}

function addArrow(slide, x1, y1, x2, y2, color = C.blue, width = 1.6) {
  slide.addShape(pptx.ShapeType.line, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color, width, beginArrowType: 'none', endArrowType: 'triangle' } });
}

// 1 Cover
{
  const slide = pptx.addSlide();
  slide.background = { color: C.bg };
  slide.addShape(pptx.ShapeType.rect, { x: 8.5, y: 0, w: 4.833, h: 7.5, fill: { color: '0B2948' }, line: { color: '0B2948' } });
  for (let i = 0; i < 7; i++) {
    slide.addShape(pptx.ShapeType.arc, { x: 8.45 + i * 0.25, y: 0.55 + i * 0.35, w: 4.1 - i * 0.25, h: 4.1 - i * 0.25, adjustPoint: 0.25, rotate: 15, fill: { color: C.bg, transparency: 100 }, line: { color: i % 2 ? C.cyan : C.blue, transparency: 35 + i * 6, width: 1.2 } });
  }
  slide.addShape(pptx.ShapeType.ellipse, { x: 9.45, y: 2.0, w: 2.25, h: 2.25, fill: { color: C.blue, transparency: 88 }, line: { color: C.blue, width: 2 } });
  slide.addText('MMN', { x: 9.72, y: 2.68, w: 1.7, h: 0.58, fontSize: 28, bold: true, color: C.white, align: 'center', margin: 0 });
  slide.addText('CREATOR INTELLIGENCE', { x: 9.3, y: 3.35, w: 2.55, h: 0.25, fontSize: 8.5, bold: true, color: C.cyan, charSpacing: 1.5, align: 'center', margin: 0 });
  slide.addText('MMN', { x: 0.65, y: 0.62, w: 1.4, h: 0.4, fontSize: 21, bold: true, color: C.blue, margin: 0 });
  slide.addText('达人蒸馏 / 孵化能力介绍', { x: 0.65, y: 1.65, w: 7.25, h: 0.82, fontSize: 32, bold: true, color: C.white, margin: 0, fit: 'shrink' });
  slide.addText('把达人从“资源名单”转化为有证据、可比较、可调用的企业内容资产', { x: 0.68, y: 2.63, w: 6.95, h: 0.65, fontSize: 15, color: C.text, breakLine: false, margin: 0, fit: 'shrink' });
  slide.addShape(pptx.ShapeType.line, { x: 0.68, y: 3.55, w: 6.6, h: 0, line: { color: C.line, width: 1.2 } });
  const tags = [['真实内容证据', C.blue], ['多模态理解', C.cyan], ['交叉质检', C.orange], ['人工审核边界', C.green]];
  tags.forEach((t, i) => label(slide, t[0], 0.68 + i * 1.72, 3.88, 1.5, t[1]));
  slide.addText('面向品牌、内容营销、媒介与用户洞察团队', { x: 0.68, y: 5.95, w: 6.4, h: 0.28, fontSize: 11, color: C.muted, margin: 0 });
  slide.addText('2026.07', { x: 0.68, y: 6.35, w: 1.3, h: 0.28, fontSize: 10, bold: true, color: C.blue, margin: 0 });
}

// 2 Executive view
{
  const slide = pptx.addSlide('MMN_MASTER');
  addTitle(slide, '01 · BUSINESS VALUE', '让达人选择从“看流量”走向“看内容能力”', 'MMN回答三个业务问题：他擅长讲什么、怎么讲、适合承担什么营销任务。');
  const cols = [
    { x: 0.6, title: '传统做法的盲区', color: C.red, items: ['依赖粉丝量与互动率', '标签粗、代表作证据缺失', 'Brief与达人能力错配', '项目经验难以复用'] },
    { x: 4.5, title: 'MMN的处理方式', color: C.blue, items: ['核验账号身份与来源', '拆解代表作的内容结构', '识别专业与视觉表达', '共同证据质检后入库'] },
    { x: 8.4, title: '企业获得的结果', color: C.green, items: ['可比较的达人能力档案', '更贴合人选的Campaign Brief', '可复用的选题与结构方法', '持续积累企业内容Know-how'] },
  ];
  cols.forEach((col, idx) => {
    card(slide, col.x, 1.85, 3.55, 4.35, { line: col.color });
    iconCircle(slide, String(idx + 1), col.x + 0.25, 2.12, col.color, 0.52);
    slide.addText(col.title, { x: col.x + 0.92, y: 2.16, w: 2.25, h: 0.34, fontSize: 16, bold: true, color: C.white, margin: 0, fit: 'shrink' });
    col.items.forEach((item, i) => {
      slide.addShape(pptx.ShapeType.ellipse, { x: col.x + 0.34, y: 3.03 + i * 0.68, w: 0.12, h: 0.12, fill: { color: col.color }, line: { color: col.color } });
      slide.addText(item, { x: col.x + 0.62, y: 2.94 + i * 0.68, w: 2.55, h: 0.32, fontSize: 11.5, color: C.text, margin: 0, fit: 'shrink' });
    });
  });
  addArrow(slide, 4.2, 4.03, 4.42, 4.03, C.blue, 2);
  addArrow(slide, 8.1, 4.03, 8.32, 4.03, C.green, 2);
  footerNote(slide, '业务价值：减少达人选错、Brief错配和经验无法沉淀造成的重复投入。');
}

// 3 Capability loop
{
  const slide = pptx.addSlide('MMN_MASTER');
  addTitle(slide, '02 · CAPABILITY LOOP', '六步形成可追溯的达人内容能力资产', '每一步都有来源、状态和失败边界；证据不足时不生成确定性标签。');
  const steps = [
    ['01', '身份门禁', '主页ID与达人名称核验\n错配即停止'],
    ['02', '内容采集', '主页、作品、指标、评论\n保留缺失字段'],
    ['03', '代表作筛选', '综合表现、稳定性与差异性\n不是简单点赞Top N'],
    ['04', '多模态理解', '字幕 / ASR / OCR / 画面 / 镜头\n形成内容证据'],
    ['05', '模型交叉质检', '共同证据、结论一致、置信度门槛\n冲突转人工'],
    ['06', '资产沉淀与反馈', '能力档案、Brief建议、方法资产\n结果持续回流'],
  ];
  steps.forEach((s, i) => {
    const x = 0.55 + i * 2.08;
    card(slide, x, 2.05, 1.78, 3.2, { line: i === 4 ? C.orange : (i === 5 ? C.green : C.blue), fill: i % 2 ? C.panel2 : C.panel });
    slide.addText(s[0], { x: x + 0.17, y: 2.25, w: 0.46, h: 0.25, fontSize: 11, bold: true, color: i === 4 ? C.orange : C.blue, margin: 0 });
    slide.addText(s[1], { x: x + 0.17, y: 2.72, w: 1.43, h: 0.5, fontSize: 15, bold: true, color: C.white, margin: 0, fit: 'shrink' });
    slide.addShape(pptx.ShapeType.line, { x: x + 0.17, y: 3.42, w: 1.42, h: 0, line: { color: C.line, width: 1 } });
    slide.addText(s[2], { x: x + 0.17, y: 3.72, w: 1.42, h: 0.95, fontSize: 9.8, color: C.text, valign: 'mid', margin: 0.02, breakLine: false, fit: 'shrink' });
    if (i < steps.length - 1) addArrow(slide, x + 1.79, 3.65, x + 2.03, 3.65, C.muted, 1.2);
  });
  card(slide, 1.7, 5.6, 9.9, 0.73, { fill: C.dark, line: C.cyan, shadow: false });
  slide.addText('反馈闭环', { x: 1.95, y: 5.82, w: 0.9, h: 0.2, fontSize: 10, bold: true, color: C.cyan, margin: 0 });
  slide.addText('传播表现、内容审核与业务结果回流，修正达人标签、任务匹配规则和企业内容方法库', { x: 3.0, y: 5.78, w: 8.1, h: 0.28, fontSize: 10.5, color: C.text, margin: 0, fit: 'shrink' });
}

// 4 Capability map
{
  const slide = pptx.addSlide('MMN_MASTER');
  addTitle(slide, '03 · CAPABILITY MAP', '四层能力地图：从数据事实到营销调用', '底层能力不直接外显；甲方看到的是有证据的业务结论和可执行资产。');
  const layers = [
    { y: 5.25, h: 0.82, name: '数据与身份层', color: C.blue, items: '账号身份核验 · 平台来源 · 作品与互动指标 · 评论证据 · 缺失值保留' },
    { y: 4.18, h: 0.82, name: '内容理解层', color: C.cyan, items: '平台字幕 · 短/长视频转写 · 专用OCR · 视觉场景 · 镜头结构 · 产品实体' },
    { y: 3.11, h: 0.82, name: '判断与质检层', color: C.orange, items: '账号定位 · 内容DNA · 视觉形态 · 共同证据门禁 · 冲突拦截 · 人工复核' },
    { y: 2.04, h: 0.82, name: '业务应用层', color: C.green, items: '达人初筛 · Campaign匹配 · Brief建议 · 新账号孵化 · 方法论沉淀 · 舆情辅助验证' },
  ];
  layers.forEach((l, i) => {
    const inset = i * 0.52;
    card(slide, 0.75 + inset, l.y, 11.8 - inset * 2, l.h, { fill: C.panel, line: l.color, shadow: false });
    slide.addText(l.name, { x: 1.03 + inset, y: l.y + 0.23, w: 1.62, h: 0.28, fontSize: 13, bold: true, color: l.color, margin: 0, fit: 'shrink' });
    slide.addText(l.items, { x: 2.82 + inset, y: l.y + 0.23, w: 8.65 - inset * 2, h: 0.28, fontSize: 10.5, color: C.text, margin: 0, fit: 'shrink' });
  });
  slide.addText('MMN多模态策略输出', { x: 4.3, y: 1.5, w: 4.75, h: 0.34, fontSize: 15, bold: true, color: C.white, align: 'center', margin: 0 });
  addArrow(slide, 6.67, 5.15, 6.67, 2.92, C.blue, 1.3);
  footerNote(slide, '模型名称属于内部质检配置；对客户统一呈现为MMN多模态策略输出。');
}

// 5 Scenario matrix
{
  const slide = pptx.addSlide('MMN_MASTER');
  addTitle(slide, '04 · CLIENT SCENARIOS', '六类甲方场景可以直接调用', '同一套达人证据可以被品牌、内容、媒介和洞察团队复用。');
  const scenarios = [
    ['达人初筛与建档', '判断账号真实性、内容赛道、代表作和基础风险', '候选达人档案'],
    ['车型上市Campaign', '按传播任务匹配技术解释、体验或生活方式达人', '达人组合与Brief'],
    ['内容能力诊断', '拆解选题、开场、叙事、证据使用和视觉表达', '内容DNA'],
    ['新账号孵化', '沉淀固定栏目、首批选题和30天验证节奏', '孵化方案'],
    ['竞品达人研究', '比较不同账号的专业能力与表达方式', '能力对标图谱'],
    ['舆情辅助验证', '识别评论中的车型疑问、争议和专业纠偏', '平台级候选信号'],
  ];
  scenarios.forEach((s, i) => {
    const col = i % 3, row = Math.floor(i / 3), x = 0.62 + col * 4.12, y = 1.85 + row * 2.18;
    const colors = [C.blue, C.cyan, C.orange, C.green, C.blue, C.orange];
    card(slide, x, y, 3.72, 1.82, { line: colors[i], fill: row ? C.panel2 : C.panel });
    iconCircle(slide, String(i + 1), x + 0.2, y + 0.22, colors[i], 0.42);
    slide.addText(s[0], { x: x + 0.78, y: y + 0.24, w: 2.55, h: 0.28, fontSize: 14, bold: true, color: C.white, margin: 0, fit: 'shrink' });
    slide.addText(s[1], { x: x + 0.22, y: y + 0.82, w: 3.26, h: 0.48, fontSize: 9.7, color: C.text, margin: 0, fit: 'shrink' });
    label(slide, s[2], x + 2.16, y + 1.43, 1.28, colors[i]);
  });
  footerNote(slide, '边界：达人评论只代表当前账号与样本范围，不外推为全市场需求。');
}

// 6 Deliverables
{
  const slide = pptx.addSlide('MMN_MASTER');
  addTitle(slide, '05 · DELIVERABLES', '一次达人诊断，形成四类可复用交付物', '交付不是黑盒分数，而是结论、证据、建议与边界同时存在。');
  const blocks = [
    { n: 'A', title: '达人能力档案', color: C.blue, items: ['身份与来源记录', '账号定位与内容赛道', '代表作与入选理由', '专业能力与表达特征'] },
    { n: 'B', title: '内容DNA', color: C.cyan, items: ['核心选题与内容支柱', '开场和叙事结构', '视觉形态与镜头特征', '证据使用和语言方式'] },
    { n: 'C', title: '营销调用建议', color: C.orange, items: ['适用车型与传播阶段', '适合承担的营销任务', 'Campaign Brief建议', '合作前复核事项'] },
    { n: 'D', title: '企业内容资产', color: C.green, items: ['可检索的能力标签', '可复用的选题方法', '脚本结构和内容规则', '项目结果反馈记录'] },
  ];
  blocks.forEach((b, i) => {
    const x = 0.62 + i * 3.12;
    card(slide, x, 1.88, 2.82, 4.4, { line: b.color });
    slide.addText(b.n, { x: x + 0.25, y: 2.13, w: 0.5, h: 0.42, fontSize: 24, bold: true, color: b.color, margin: 0 });
    slide.addText(b.title, { x: x + 0.25, y: 2.78, w: 2.28, h: 0.37, fontSize: 15, bold: true, color: C.white, margin: 0, fit: 'shrink' });
    slide.addShape(pptx.ShapeType.line, { x: x + 0.25, y: 3.35, w: 2.28, h: 0, line: { color: C.line, width: 1 } });
    b.items.forEach((item, j) => {
      slide.addText('•', { x: x + 0.25, y: 3.68 + j * 0.52, w: 0.15, h: 0.2, fontSize: 11, bold: true, color: b.color, margin: 0 });
      slide.addText(item, { x: x + 0.48, y: 3.65 + j * 0.52, w: 2.02, h: 0.27, fontSize: 10.2, color: C.text, margin: 0, fit: 'shrink' });
    });
  });
}

// 7 Comparison
{
  const slide = pptx.addSlide('MMN_MASTER');
  addTitle(slide, '06 · DIFFERENTIATION', 'MMN不是另一张达人名单', '传统达人库负责资源管理；MMN补足内容能力判断和策略调用。');
  const rows = [
    ['主要回答', '有哪些达人', '为什么适合当前任务'],
    ['核心数据', '粉丝、互动、报价、合作记录', '代表作、内容结构、视听证据、受众反馈'],
    ['标签方式', '平台标签或人工经验', '证据支持的能力标签与适用任务'],
    ['使用环节', '资源搜索与采购管理', '人选判断、Brief、内容策略与复盘'],
    ['风险控制', '依赖人工抽查', '身份门禁、模型冲突拦截、人工审核'],
    ['沉淀结果', '项目级名单', '跨项目复用的企业内容资产'],
  ];
  const x0 = 0.75, widths = [2.1, 4.4, 5.25], headerY = 1.85, rowH = 0.67;
  ['比较维度', '传统达人库', 'MMN达人内容能力资产'].forEach((t, i) => {
    slide.addShape(pptx.ShapeType.rect, { x: x0 + widths.slice(0, i).reduce((a,b)=>a+b,0), y: headerY, w: widths[i], h: 0.62, fill: { color: i === 2 ? '124F78' : C.panel2 }, line: { color: C.line } });
    slide.addText(t, { x: x0 + widths.slice(0, i).reduce((a,b)=>a+b,0) + 0.15, y: headerY + 0.18, w: widths[i] - 0.3, h: 0.22, fontSize: 11.5, bold: true, color: i === 2 ? C.white : C.text, margin: 0, fit: 'shrink' });
  });
  rows.forEach((r, ri) => {
    r.forEach((t, ci) => {
      const x = x0 + widths.slice(0, ci).reduce((a,b)=>a+b,0), y = headerY + 0.62 + ri * rowH;
      slide.addShape(pptx.ShapeType.rect, { x, y, w: widths[ci], h: rowH, fill: { color: ri % 2 ? C.panel2 : C.panel, transparency: ci === 2 ? 0 : 10 }, line: { color: C.line, transparency: 20 } });
      slide.addText(t, { x: x + 0.15, y: y + 0.16, w: widths[ci] - 0.3, h: 0.28, fontSize: ci === 0 ? 10 : 10.3, bold: ci === 0 || ci === 2, color: ci === 2 ? C.white : (ci === 0 ? C.blue : C.text), margin: 0, fit: 'shrink' });
    });
  });
  footerNote(slide, '两者是互补关系：现有达人库可继续承载报价、合同与合作管理，MMN负责内容能力判断。');
}

// 8 QA gate
{
  const slide = pptx.addSlide('MMN_MASTER');
  addTitle(slide, '07 · QUALITY GATE', '从“模型给答案”改为“证据达到门槛才发布”', '底层采用多模型独立观察与共同证据校验；客户侧统一看到MMN质检状态。');
  const flow = [
    ['真实内容证据', '字幕、画面、OCR、镜头、作品来源', C.blue],
    ['独立多模态观察', '不同模型分别看同一素材', C.cyan],
    ['共同证据审计', '结论、证据ID和置信度必须达标', C.orange],
  ];
  flow.forEach((f, i) => {
    const x = 0.65 + i * 3.25;
    card(slide, x, 2.12, 2.82, 1.62, { line: f[2] });
    slide.addText(f[0], { x: x + 0.22, y: 2.42, w: 2.38, h: 0.32, fontSize: 14, bold: true, color: C.white, margin: 0, fit: 'shrink' });
    slide.addText(f[1], { x: x + 0.22, y: 3.0, w: 2.38, h: 0.36, fontSize: 9.5, color: C.text, margin: 0, fit: 'shrink' });
    if (i < 2) addArrow(slide, x + 2.84, 2.93, x + 3.18, 2.93, C.muted, 1.3);
  });
  addArrow(slide, 9.95, 2.93, 10.34, 2.93, C.muted, 1.3);
  card(slide, 10.38, 1.85, 2.25, 1.15, { line: C.green, fill: '0E3A35' });
  slide.addText('一致', { x: 10.62, y: 2.12, w: 0.7, h: 0.27, fontSize: 14, bold: true, color: C.green, margin: 0 });
  slide.addText('形成待审核结论', { x: 10.62, y: 2.52, w: 1.55, h: 0.22, fontSize: 9.5, color: C.text, margin: 0 });
  card(slide, 10.38, 3.25, 2.25, 1.15, { line: C.red, fill: '3A202A' });
  slide.addText('不一致', { x: 10.62, y: 3.52, w: 0.9, h: 0.27, fontSize: 14, bold: true, color: C.red, margin: 0 });
  slide.addText('禁止发布，转人工复核', { x: 10.62, y: 3.92, w: 1.62, h: 0.22, fontSize: 9.5, color: C.text, margin: 0, fit: 'shrink' });
  addArrow(slide, 9.95, 3.07, 10.34, 3.72, C.red, 1.3);
  card(slide, 1.15, 4.85, 10.95, 1.05, { fill: C.dark, line: C.line, shadow: false });
  slide.addText('四条硬门槛', { x: 1.45, y: 5.19, w: 1.1, h: 0.25, fontSize: 11, bold: true, color: C.orange, margin: 0 });
  ['身份一致', '来源可追溯', '共同证据存在', '冲突已处理'].forEach((t, i) => {
    label(slide, t, 2.8 + i * 2.12, 5.12, 1.62, i === 3 ? C.green : C.orange);
  });
  footerNote(slide, '双模型一致不等于事实；最终结论仍需在企业业务语境下由人工确认。');
}

// 9 Maturity
{
  const slide = pptx.addSlide('MMN_MASTER');
  addTitle(slide, '08 · CURRENT MATURITY', '当前能力成熟度：已运行、已实现、待真实验收', '客观区分实装状态，避免把单元测试或配置完成描述为生产可用。');
  const groups = [
    { y: 1.9, title: '已实际运行并形成数据', color: C.green, items: ['身份校验与TikHub采集', '代表作筛选与证据入库', '平台字幕与Qwen VL视觉证据', '达人档案、作品拆解和舆情辅助页面'] },
    { y: 3.35, title: '代码已实现并通过相关测试', color: C.blue, items: ['Qwen 3.7主视觉与3.6降级', 'Kimi独立视觉复核', '专用OCR与长视频异步ASR', 'Qwen+DeepSeek共同证据门禁与页面拦截'] },
    { y: 4.8, title: '上线前仍需完成', color: C.orange, items: ['轮换后新Key的真实调用', '达人完整业务流端到端验收', '生产环境时延、成本与并发验证', '企业Gold Set与人工阈值确认'] },
  ];
  groups.forEach(g => {
    card(slide, 0.7, g.y, 11.95, 1.1, { line: g.color, fill: C.panel });
    slide.addShape(pptx.ShapeType.rect, { x: 0.7, y: g.y, w: 0.11, h: 1.1, fill: { color: g.color }, line: { color: g.color } });
    slide.addText(g.title, { x: 1.02, y: g.y + 0.22, w: 2.55, h: 0.32, fontSize: 13, bold: true, color: g.color, margin: 0, fit: 'shrink' });
    g.items.forEach((item, i) => {
      const x = 3.75 + (i % 2) * 4.25, y = g.y + 0.19 + Math.floor(i / 2) * 0.42;
      slide.addText('•', { x, y, w: 0.16, h: 0.2, fontSize: 10, bold: true, color: g.color, margin: 0 });
      slide.addText(item, { x: x + 0.22, y: y - 0.01, w: 3.7, h: 0.24, fontSize: 9.6, color: C.text, margin: 0, fit: 'shrink' });
    });
  });
  footerNote(slide, '当前对外状态建议：核心达人资产流程可演示；新增多模型链路完成真实API验收后再标记为生产可用。');
}

// 10 Closing
{
  const slide = pptx.addSlide('MMN_MASTER');
  addTitle(slide, '09 · PILOT PROPOSAL', '建议从一个车型项目开始验证', '先在有限达人和真实任务中验证判断质量，再逐步扩大企业内容资产范围。');
  const weeks = [
    ['第1周', '口径与样本', '确定车型、传播阶段、达人范围和人工审核标准'],
    ['第2周', '采集与诊断', '建立达人档案，提取代表作与多模态内容证据'],
    ['第3周', '任务匹配', '形成达人组合、内容DNA和Campaign Brief建议'],
    ['第4周', '人工复核与沉淀', '确认可用标签、争议案例和企业方法资产'],
  ];
  weeks.forEach((w, i) => {
    const x = 0.68 + i * 3.08;
    card(slide, x, 2.02, 2.78, 2.45, { line: i === 3 ? C.green : C.blue });
    label(slide, w[0], x + 0.22, 2.28, 0.86, i === 3 ? C.green : C.blue);
    slide.addText(w[1], { x: x + 0.22, y: 2.88, w: 2.25, h: 0.36, fontSize: 15, bold: true, color: C.white, margin: 0, fit: 'shrink' });
    slide.addText(w[2], { x: x + 0.22, y: 3.54, w: 2.25, h: 0.56, fontSize: 9.8, color: C.text, margin: 0, fit: 'shrink' });
    if (i < 3) addArrow(slide, x + 2.8, 3.22, x + 3.02, 3.22, C.muted, 1.2);
  });
  card(slide, 1.55, 5.02, 10.25, 1.02, { fill: '0B2B47', line: C.cyan, shadow: false });
  slide.addText('试点验收看什么', { x: 1.88, y: 5.37, w: 1.35, h: 0.23, fontSize: 11, bold: true, color: C.cyan, margin: 0 });
  slide.addText('身份错配率 · 证据完整度 · 人工认可率 · Brief可执行性 · 单达人处理成本与时延', { x: 3.48, y: 5.32, w: 7.85, h: 0.3, fontSize: 11, color: C.white, margin: 0, fit: 'shrink' });
  slide.addText('MMN把碎片化达人信息转化为可执行的内容决策，并通过反馈持续沉淀汽车营销Know-how。', { x: 1.05, y: 6.35, w: 11.25, h: 0.34, fontSize: 12, bold: true, color: C.blue, align: 'center', margin: 0, fit: 'shrink' });
}

const out = process.argv[2] || path.join(process.cwd(), 'output', 'pptx', 'MMN-达人蒸馏与孵化能力介绍-20260718.pptx');
fs.mkdirSync(path.dirname(out), { recursive: true });
pptx.writeFile({ fileName: out });
