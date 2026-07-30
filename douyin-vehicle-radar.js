(() => {
  const mount = document.querySelector("#douyin-vehicle-radar-mount");
  if (!mount) return;

  const state = {
    context: window.MMNVehicleRadarContext || {},
    mode: "single_model_rank",
    queryModel: window.MMNVehicleRadarContext?.subject || "",
    rangeDays: 7,
    topN: 20,
    fullOpen: false,
    run: null,
    strategy: null,
    tab: "own",
    loading: false,
    error: "",
    pollTimer: 0,
    insightJobs: new Map(),
  };
  const activeStatuses = new Set(["queued", "running"]);
  const insightActive = new Set([
    "queued", "resolving_video", "extracting_media", "transcribing",
    "building_evidence", "analyzing", "cross_validating",
  ]);
  const tabLabels = {
    own: "本品内容",
    competitor: "竞品内容",
    comparison: "本竞品对比",
    attribute: "属性内容",
    incompleteMetrics: "待补热度",
    pending: "待复核",
  };

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>"']/g, char => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    })[char]);
  }
  function headers(extra = {}) {
    return typeof authHeaders === "function"
      ? authHeaders({ "Content-Type": "application/json", ...extra })
      : { "Content-Type": "application/json", ...extra };
  }
  async function request(path, options = {}) {
    const response = await fetch(path, { ...options, headers: headers(options.headers || {}) });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload.ok === false) throw new Error(payload.error || "请求失败");
    return payload;
  }
  function formatNumber(value) {
    const number = Number(value || 0);
    if (number >= 100000000) return `${(number / 100000000).toFixed(1)}亿`;
    if (number >= 10000) return `${(number / 10000).toFixed(1)}万`;
    return Math.round(number).toLocaleString();
  }
  function edition() {
    return state.context.edition || "china";
  }
  function activeSubject() {
    return state.mode === "single_model_rank"
      ? String(state.queryModel || "").trim()
      : String(state.context.subject || "").trim();
  }
  function currentItems() {
    const lists = state.run?.result?.lists || {};
    if (state.mode === "single_model_rank") {
      return (lists.own || lists.all || []).slice(0, state.topN);
    }
    return lists[state.tab] || [];
  }
  function statusLabel(run) {
    if (!run) return "尚未抓取";
    if (run.status === "completed") return "已完成";
    if (run.status === "partial") return "部分完成";
    if (run.status === "failed") return "未完成";
    return run.message || "正在抓取";
  }
  function collectionLabel(collection = {}) {
    const labels = {
      source_exhausted: "公开检索结果已遍历",
      page_cap: "达到单词分页上限",
      request_cap: "达到本轮请求上限",
      candidate_cap: "达到候选内容上限",
      source_error: "部分公开检索暂不可用",
      cursor_cycle: "检索游标异常，已安全停止",
    };
    return labels[collection.stopReason] || "等待检索";
  }
  function stageProgress() {
    const run = state.run;
    if (!run || !activeStatuses.has(run.status)) return "";
    const steps = [
      ["preparing", "准备口径"], ["searching", "检索内容"], ["filtering", "过滤窗口"],
      ["verifying", "核验车型"], ["deduplicating", "内容去重"],
      ["enriching_metrics", "核验热度"], ["ranking", "生成榜单"],
    ];
    const currentIndex = Math.max(0, steps.findIndex(([key]) => key === run.stage));
    return `<div class="dvr-progress" role="progressbar" aria-valuenow="${Number(run.progress) || 0}" aria-valuemin="0" aria-valuemax="100">
      <div class="dvr-progress__bar"><i style="width:${Number(run.progress) || 0}%"></i></div>
      <div class="dvr-progress__steps">${steps.map(([key, label], index) =>
        `<span class="${index < currentIndex ? "done" : index === currentIndex ? "active" : ""}"><i></i>${escapeHtml(label)}</span>`
      ).join("")}</div>
    </div>`;
  }
  function sourceLink(item) {
    const url = String(item.sourceUrl || "");
    return /^https?:\/\//.test(url)
      ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">打开原视频 ↗</a>`
      : `<span class="muted">原视频地址缺失</span>`;
  }
  function insightBlock(item) {
    const id = String(item.platformItemId || item.itemId || "");
    const job = state.insightJobs.get(id);
    if (!job) return `<button type="button" class="ghost" data-dvr-insight="${escapeHtml(id)}">生成逐视频洞察</button>`;
    const running = insightActive.has(job.status);
    const insight = job.result?.validation?.finalInsight || {};
    const evidence = job.evidencePackage || {};
    const transcriptCount = (evidence.transcriptSegments || []).length;
    const visualCount = (evidence.keyframes || []).length + (evidence.visualSegments || []).length;
    const ocrCount = (evidence.ocrSegments || []).length;
    const missing = [];
    if (!transcriptCount) missing.push("字幕或转写");
    if (!visualCount) missing.push("关键画面");
    if (!ocrCount) missing.push("画面文字");
    const analysisStarted = (job.runStatus || []).some(row => row.status && row.status !== "pending");
    const statusTitle = {
      limited_analysis: "视频内容未读取完整",
      incomplete: analysisStarted ? "部分分析未完成" : "分析尚未启动",
      manual_required: "核心判断等待人工复核",
      failed: "逐视频洞察未完成",
      completed: "逐视频洞察已完成",
    }[job.status] || job.message || "当前未形成可发布洞察";
    const evidenceNote = job.status === "limited_analysis"
      ? `${missing.length ? `缺失：${missing.join("、")}；` : ""}${analysisStarted ? "部分分析已运行" : "三路分析尚未启动"}`
      : "";
    const failedReview = (job.result?.validation?.runs || []).find(row => row.status === "failed");
    const actionLabel = job.status === "limited_analysis" && !analysisStarted
      ? "补取视频证据并分析"
      : job.status === "incomplete" && failedReview
        ? `重试未完成分析 ${failedReview.slot}`
        : job.status === "incomplete" ? "重试未完成分析" : "重新分析";
    return `<div class="dvr-insight ${escapeHtml(job.status || "")}">
      <div><b>${running ? `${Number(job.progress) || 0}% · ${escapeHtml(job.message || "分析中")}` : escapeHtml(insight.contentSummary || statusTitle)}</b>
      ${evidenceNote ? `<small>${escapeHtml(evidenceNote)}</small>` : ""}
      ${!running && insight.marketingImplications?.length ? `<p>${escapeHtml(insight.marketingImplications[0])}</p>` : ""}</div>
      <button type="button" class="ghost" data-dvr-insight="${escapeHtml(id)}" data-dvr-retry-slot="${escapeHtml(failedReview?.slot || "")}" ${running ? "disabled" : ""}>${running ? "分析中…" : escapeHtml(actionLabel)}</button>
    </div>`;
  }
  function resultRow(item, index, pendingOverride = false) {
    const metrics = item.metrics || {};
    const models = (item.matchedModels || []).join(" / ") || "待确认车型";
    const pending = pendingOverride || state.tab === "pending";
    const itemId = String(item.platformItemId || item.itemId || "");
    const viewStatus = item.metricStatus?.views;
    const formal = viewStatus === "verified" && item.rankingEligible !== false;
    const roleLabel = item.sourceRole === "brand_or_matrix" ? "官方/矩阵"
      : item.sourceRole === "media" ? "媒体" : "用户/其他";
    const viewText = formal ? formatNumber(metrics.views)
      : viewStatus === "failed" ? "补抓失败" : "未取得";
    return `<li class="dvr-row">
      <span class="dvr-rank">${formal ? (item.rank || index + 1) : "—"}</span>
      <div class="dvr-row__body">
        <div class="dvr-row__head"><h4>${escapeHtml(item.text || "未取得标题")}</h4><span>${escapeHtml(roleLabel)}</span></div>
        <p>${escapeHtml(item.author || "作者未知")} · ${escapeHtml(models)} · ${escapeHtml(String(item.publishedAt || "").slice(0, 10))}</p>
        <div class="dvr-metrics">
          <span>播放 <b>${escapeHtml(viewText)}</b></span>
          <span>点赞 <b>${formatNumber(metrics.likes)}</b></span>
          <span>评论 <b>${formatNumber(metrics.comments)}</b></span>
          <span>分享 <b>${formatNumber(metrics.shares)}</b></span>
        </div>
        <div class="dvr-row__actions">
          ${sourceLink(item)}
          ${pending ? `<button type="button" class="primary" data-dvr-review="${escapeHtml(itemId)}" data-verdict="include">确认纳入</button><button type="button" class="ghost" data-dvr-review="${escapeHtml(itemId)}" data-verdict="exclude">排除</button>` : ""}
        </div>
        ${pending ? "" : insightBlock(item)}
      </div>
    </li>`;
  }
  function strategyPanel() {
    if (!state.run || !["completed", "partial"].includes(state.run.status)) return "";
    const strategy = state.strategy?.result || {};
    const readiness = state.run.result?.strategyReadiness || {};
    const insight = strategy.unifiedInsight || {};
    const review = strategy.qa?.threeFlagships || {};
    const status = review.status === "aligned" ? "三路复核一致"
      : review.status === "pending_configuration" ? "分析能力待配置"
      : review.status === "insufficient_evidence" ? "证据不足"
      : review.status ? "存在分歧或边界" : "尚未生成";
    return `<section class="dvr-strategy">
      <div>
        <span>MMN 窗口策略输出</span>
        <h3>${escapeHtml(insight.headline || "基于本轮榜单生成车型内容策略")}</h3>
        <p>${escapeHtml((insight.limitations || [])[0] || "只基于本轮已核验公开内容，不把热度直接解释为需求、销量或线索。")}</p>
      </div>
      <div class="dvr-strategy__actions"><em>${escapeHtml(readiness.ready ? status : readiness.message || "证据不足")}</em><button type="button" class="primary" data-dvr-strategy ${state.loading || !readiness.ready ? "disabled" : ""}>${state.strategy ? "重新生成策略" : "生成本轮策略"}</button></div>
    </section>`;
  }
  function results() {
    const run = state.run;
    if (!run) return `<div class="dvr-empty">
      <b>${state.mode === "single_model_rank" ? "输入车型，建立内容热度榜" : "建立本竞品内容证据榜"}</b>
      <p>${state.mode === "single_model_rank"
        ? "系统只对所选时间窗内、车型关联和播放量均已核验的视频进行排名。不会自动运行。"
        : "系统会按本品、竞品、对比关系和产品属性建立 7 / 14 / 30 天榜单。不会自动运行。"}</p>
    </div>`;
    if (run.status === "failed") return `<div class="dvr-empty error">
      <b>本轮采集未完成</b><p>${escapeHtml(run.error || run.message || "可安全重试，不会覆盖已完成榜单。")}</p>
      <button type="button" class="primary" data-dvr-retry>重试本轮</button>
    </div>`;
    if (activeStatuses.has(run.status)) return `<div class="dvr-running"><b>${escapeHtml(run.message || "正在抓取")}</b><p>浏览器可继续进行其他工作；本模块只在本次手动任务内运行。</p></div>`;
    const counts = run.result?.counts || {};
    const collection = run.result?.collection || {};
    const items = currentItems();
    const pendingItems = run.result?.lists?.pending || [];
    const incompleteItems = run.result?.lists?.incompleteMetrics || [];
    const partialTitle = incompleteItems.length
      ? "部分内容未取得可核验播放量"
      : collection.status === "partial"
        ? "本轮为公开检索范围内的部分结果"
        : "本轮证据尚未达到正式发布条件";
    const partialBody = incompleteItems.length
      ? "缺失热度的视频不会进入正式榜，也不会显示为0播放。"
      : `${collectionLabel(collection)}；当前排名只覆盖已成功召回并完成核验的内容。`;
    const visibleItems = state.mode === "single_model_rank" && !state.fullOpen
      ? items.slice(0, 5)
      : items;
    const singleList = `
      <div class="dvr-list-head">
        <span>正式榜单仅按已核验播放量排序</span>
        <span>${escapeHtml(collectionLabel(collection))}</span>
      </div>
      ${visibleItems.length
        ? `<ol class="dvr-list">${visibleItems.map((item, index) => resultRow(item, index)).join("")}</ol>`
        : `<div class="dvr-empty small"><b>当前没有可正式入榜的视频</b><p>这不代表所选周期没有相关内容，只代表本轮公开检索结果未同时通过车型、时间和播放量核验。</p></div>`}
      <div class="dvr-full-actions">
        ${items.length > 5 || pendingItems.length
          ? `<button type="button" class="ghost" data-dvr-full aria-expanded="${state.fullOpen}">${state.fullOpen ? "收起完整榜单" : "查看完整榜单"}</button>`
          : `<span class="muted">已展示全部正式结果</span>`}
        <small>当前展示 Top ${state.topN} · ${Number(counts.pendingReview) || 0} 条待复核</small>
      </div>
      ${state.fullOpen && pendingItems.length ? `
        <section class="dvr-review-queue" aria-label="待人工复核视频">
          <h3>待人工复核</h3>
          <p>短车型名或名称冲突不会自动进入正式榜。</p>
          <ol class="dvr-list">${pendingItems.slice(0, 10).map((item, index) => resultRow(item, index, true)).join("")}</ol>
        </section>` : ""}`;
    const groupList = `
      <div class="dvr-tabs" role="tablist">${Object.entries(tabLabels).map(([key, label]) => {
        const count = run.result?.lists?.[key]?.length || 0;
        return `<button type="button" role="tab" data-dvr-tab="${key}" class="${state.tab === key ? "active" : ""}" aria-selected="${state.tab === key}">${escapeHtml(label)} <i>${count}</i></button>`;
      }).join("")}</div>
      <div class="dvr-list-head"><span>正式榜单仅按已核验播放量排序</span><span>热度缺失内容单列，不参与排名</span></div>
      ${items.length ? `<ol class="dvr-list">${items.map((item, index) => resultRow(item, index)).join("")}</ol>` : `<div class="dvr-empty small"><b>当前分组暂无已核验内容</b><p>这不代表周期内没有相关内容，只代表本轮返回证据未通过该分组门槛。</p></div>`}
      ${strategyPanel()}`;
    return `<div class="dvr-summary">
      <div><span>正式入榜</span><b>${Number(counts.rankingEligible) || 0}</b></div>
      <div><span>播放量覆盖</span><b>${Number(counts.viewCoveragePct) || 0}%</b></div>
      <div><span>已检索页面</span><b>${Number(collection.pagesVisited) || 0}</b></div>
      <div><span>榜单周期</span><b>${Number(run.rangeDays)}天</b></div>
    </div>
    <div class="dvr-coverage ${escapeHtml(collection.status || "")}">
      <b>${escapeHtml(collectionLabel(collection))}</b>
      <span>召回 ${Number(collection.rawCandidateCount) || 0} 条 · 去重后 ${Number(collection.deduplicatedCount) || 0} 条 · 播放量核验 ${Number(counts.viewsVerified) || 0} 条</span>
    </div>
    ${run.status === "partial" ? `<div class="dvr-running"><b>${escapeHtml(partialTitle)}</b><p>${escapeHtml(partialBody)}</p><button type="button" class="primary" data-dvr-retry>${incompleteItems.length ? "重试未完成项" : "重新检索"}</button></div>` : ""}
    ${state.mode === "single_model_rank" ? singleList : groupList}`;
  }
  function render() {
    const context = state.context || {};
    const competitors = context.competitors || [];
    const running = state.loading || activeStatuses.has(state.run?.status);
    const available = state.mode === "single_model_rank" ? Boolean(activeSubject()) : Boolean(context.available);
    mount.innerHTML = `<article class="panel dvr-panel">
      <header class="dvr-head">
        <div><span>CONTENT HEAT EVIDENCE</span><h2 id="douyin-vehicle-radar-title">${state.mode === "single_model_rank" ? "车型内容热度证据" : "本竞品抖音内容雷达"}</h2><p>${state.mode === "single_model_rank" ? "在公开可检索范围内，按已核验播放量查看车型热视频。" : "围绕当前产品评价数据，手动抓取本品与竞品的热门内容并形成可追溯策略。"}</p></div>
        <em class="${state.run?.status || ""}"><i></i>${escapeHtml(statusLabel(state.run))}</em>
      </header>
      <div class="dvr-mode" role="tablist" aria-label="选择内容证据模式">
        <button type="button" role="tab" data-dvr-mode="single_model_rank" class="${state.mode === "single_model_rank" ? "active" : ""}" aria-selected="${state.mode === "single_model_rank"}">车型热榜</button>
        <button type="button" role="tab" data-dvr-mode="vehicle_group" class="${state.mode === "vehicle_group" ? "active" : ""}" aria-selected="${state.mode === "vehicle_group"}">本竞品研判</button>
      </div>
      ${state.mode === "single_model_rank" ? `
        <div class="dvr-query">
          <label><span>车型名称</span><input type="search" data-dvr-model value="${escapeHtml(state.queryModel)}" placeholder="例如：智己LS6" maxlength="80" ${running ? "disabled" : ""}></label>
          <label><span>榜单数量</span><select data-dvr-topn ${running ? "disabled" : ""}>${[10, 20, 50].map(value => `<option value="${value}" ${state.topN === value ? "selected" : ""}>Top ${value}</option>`).join("")}</select></label>
          <small>临时查询不会修改驾驶舱本品或竞品配置。</small>
        </div>` : `
        <div class="dvr-scope">
          <div><span>本品</span><b>${escapeHtml(context.subject || "等待产品评价数据")}</b></div>
          <div><span>核心竞品</span><b>${escapeHtml(competitors.join(" / ") || "等待竞品车型")}</b></div>
        </div>`}
      <div class="dvr-controls">
        <div class="dvr-range" aria-label="选择抓取时间范围">${[7, 14, 30].map(days =>
          `<button type="button" data-dvr-range="${days}" class="${state.rangeDays === days ? "active" : ""}" ${running ? "disabled" : ""}>${days}天</button>`
        ).join("")}</div>
        <button type="button" class="primary dvr-run" data-dvr-run ${!available || running ? "disabled" : ""}>${activeStatuses.has(state.run?.status) ? "抓取进行中…" : "生成热榜"}</button>
      </div>
      ${state.error ? `<p class="dvr-error">${escapeHtml(state.error)}</p>` : ""}
      ${stageProgress()}
      <div class="dvr-results" aria-live="polite">${results()}</div>
      <footer><span>仅手动运行 · 车型全称自动核验 · 短别名进入人工复核</span><span>14天为 MMN 自定义观察窗口，不是抖音官方榜单周期</span></footer>
    </article>`;
    bind();
  }
  function bind() {
    mount.querySelectorAll("[data-dvr-mode]").forEach(button => button.onclick = () => {
      const nextMode = button.dataset.dvrMode;
      if (nextMode === state.mode) return;
      state.mode = nextMode;
      state.run = null; state.strategy = null; state.error = ""; state.fullOpen = false;
      clearTimeout(state.pollTimer);
      render();
      loadLatest();
    });
    const modelInput = mount.querySelector("[data-dvr-model]");
    if (modelInput) modelInput.onchange = () => {
      const next = modelInput.value.trim();
      if (next === state.queryModel) return;
      state.queryModel = next;
      state.run = null; state.strategy = null; state.error = ""; state.fullOpen = false;
      render();
      loadLatest();
    };
    const topN = mount.querySelector("[data-dvr-topn]");
    if (topN) topN.onchange = () => {
      state.topN = Number(topN.value) || 20;
      state.fullOpen = false;
      render();
    };
    mount.querySelectorAll("[data-dvr-range]").forEach(button => button.onclick = () => {
      state.rangeDays = Number(button.dataset.dvrRange);
      state.run = null; state.strategy = null; state.error = ""; state.fullOpen = false; render();
    });
    mount.querySelector("[data-dvr-run]")?.addEventListener("click", startRun);
    mount.querySelector("[data-dvr-retry]")?.addEventListener("click", retryRun);
    mount.querySelectorAll("[data-dvr-tab]").forEach(button => button.onclick = () => {
      state.tab = button.dataset.dvrTab; render();
    });
    mount.querySelector("[data-dvr-full]")?.addEventListener("click", () => {
      state.fullOpen = !state.fullOpen;
      render();
    });
    mount.querySelectorAll("[data-dvr-review]").forEach(button => button.onclick = () =>
      reviewItem(button.dataset.dvrReview, button.dataset.verdict));
    mount.querySelectorAll("[data-dvr-insight]").forEach(button => button.onclick = () =>
      startInsight(
        button.dataset.dvrInsight,
        Boolean(state.insightJobs.get(button.dataset.dvrInsight)),
        button.dataset.dvrRetrySlot || "",
      ));
    mount.querySelector("[data-dvr-strategy]")?.addEventListener("click", runStrategy);
  }
  async function startRun() {
    const subject = activeSubject();
    if (!subject) {
      state.error = "请输入车型名称后再生成热榜。";
      render();
      return;
    }
    state.loading = true; state.error = ""; state.strategy = null; render();
    try {
      const payload = await request("/api/douyin-vehicle-radar/runs", {
        method: "POST",
        body: JSON.stringify({
          edition: edition(),
          subject,
          competitors: state.mode === "vehicle_group" ? state.context.competitors || [] : [],
          topics: state.mode === "vehicle_group" ? state.context.topics || [] : [],
          mode: state.mode,
          rangeDays: state.rangeDays,
          topN: state.topN,
          maxPages: 10,
          maxRequests: 30,
          maxCandidates: 300,
          force: false,
        }),
      });
      state.run = payload.run;
      pollRun();
    } catch (error) {
      state.error = error.message || String(error);
    } finally {
      state.loading = false; render();
    }
  }
  async function retryRun() {
    if (!state.run) return;
    state.loading = true; state.error = ""; render();
    try {
      const payload = await request(`/api/douyin-vehicle-radar/runs/${encodeURIComponent(state.run.id)}/retry`, {
        method: "POST", body: JSON.stringify({ edition: edition() }),
      });
      state.run = payload.run; pollRun();
    } catch (error) { state.error = error.message || String(error); }
    finally { state.loading = false; render(); }
  }
  async function pollRun() {
    clearTimeout(state.pollTimer);
    if (!state.run) return;
    try {
      const payload = await request(`/api/douyin-vehicle-radar/runs/${encodeURIComponent(state.run.id)}?edition=${encodeURIComponent(edition())}`);
      state.run = payload.run;
      state.strategy = payload.strategy;
      state.error = "";
      render();
      if (activeStatuses.has(state.run.status)) state.pollTimer = setTimeout(pollRun, 1200);
    } catch (error) {
      state.error = error.message || String(error); render();
    }
  }
  async function loadLatest() {
    const subject = activeSubject();
    if (!subject || (state.mode === "vehicle_group" && !state.context.available)) return;
    try {
      const scope = state.mode === "single_model_rank" ? "&scope=single" : "";
      const payload = await request(`/api/douyin-vehicle-radar/latest?edition=${encodeURIComponent(edition())}&subject=${encodeURIComponent(subject)}${scope}`);
      state.run = payload.run;
      state.strategy = payload.strategy;
      if (state.run) state.rangeDays = Number(state.run.rangeDays) || state.rangeDays;
      render();
      if (activeStatuses.has(state.run?.status)) pollRun();
    } catch (error) {
      state.error = error.message || String(error); render();
    }
  }
  async function reviewItem(platformItemId, verdict) {
    const reason = window.prompt(verdict === "include" ? "请填写确认纳入理由" : "请填写排除理由");
    if (!reason?.trim()) return;
    try {
      const payload = await request("/api/douyin-vehicle-radar/items/review", {
        method: "POST",
        body: JSON.stringify({
          edition: edition(), runId: state.run.id, platformItemId, verdict,
          model: activeSubject(), reason: reason.trim(),
        }),
      });
      state.run.result = payload.result; render();
    } catch (error) { state.error = error.message || String(error); render(); }
  }
  async function startInsight(platformItemId, force, retrySlot = "") {
    try {
      const payload = await request("/api/douyin-vehicle-radar/video-insights/jobs", {
        method: "POST",
        body: JSON.stringify({
          edition: edition(), runId: state.run.id, platformItemId, force, retrySlot,
        }),
      });
      state.insightJobs.set(String(platformItemId), payload.job); render();
      pollInsight(platformItemId, payload.job.jobId);
    } catch (error) { state.error = error.message || String(error); render(); }
  }
  async function pollInsight(platformItemId, jobId) {
    try {
      const payload = await request(`/api/douyin-hot/video-insights/jobs/${encodeURIComponent(jobId)}`);
      state.insightJobs.set(String(platformItemId), payload.job); render();
      if (insightActive.has(payload.job.status)) setTimeout(() => pollInsight(platformItemId, jobId), 1400);
    } catch (error) { state.error = error.message || String(error); render(); }
  }
  async function runStrategy() {
    state.loading = true; state.error = ""; render();
    try {
      const payload = await request("/api/douyin-vehicle-radar/strategies", {
        method: "POST",
        body: JSON.stringify({ edition: edition(), runId: state.run.id }),
      });
      state.strategy = payload.strategy;
    } catch (error) { state.error = error.message || String(error); }
    finally { state.loading = false; render(); }
  }

  window.addEventListener("mmn:vehicle-radar-context", event => {
    const next = event.detail || {};
    const identityChanged = next.subject !== state.context.subject
      || JSON.stringify(next.competitors || []) !== JSON.stringify(state.context.competitors || []);
    state.context = next;
    if (identityChanged) {
      state.queryModel = next.subject || "";
      state.run = null; state.strategy = null; state.tab = "own";
      state.fullOpen = false;
      clearTimeout(state.pollTimer);
    }
    render();
    if (identityChanged) loadLatest();
  });
  render();
  loadLatest();
})();
