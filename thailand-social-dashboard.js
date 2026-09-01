(() => {
  "use strict";

  const DATA_URL = "data/thailand_social_market_latest.json";
  const state = { data: null, metric: "monthly", tier: "all", loading: false, error: "" };
  const confidenceLabels = { high: "高可信", medium: "中可信", medium_low: "待持续核验" };
  const tierLabels = { core: "核心覆盖", support: "重点补充", emerging: "增量观察" };

  function escapeHtml(value) {
    return String(value ?? "").replace(/[&<>'"]/g, (char) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"
    })[char]);
  }

  function escapeAttr(value) {
    return escapeHtml(value).replace(/`/g, "&#96;");
  }

  function root() {
    return document.querySelector("#thailand-social-dashboard-root");
  }

  function metricValue(platform) {
    return state.metric === "monthly" ? platform.monthly_usage_pct : platform.ad_reach_internet_pct;
  }

  function metricLabel() {
    return state.metric === "monthly" ? "月度用户渗透率" : "广告可触达率";
  }

  function selectedPlatforms() {
    const platforms = state.data?.platforms || [];
    return state.tier === "all" ? platforms : platforms.filter((item) => item.tier === state.tier);
  }

  function renderLoading() {
    const container = root();
    if (!container) return;
    container.innerHTML = '<div class="th-social-loading" role="status"><b>泰国媒体证据加载中</b><span></span><span></span><span></span></div>';
  }

  function renderError() {
    const container = root();
    if (!container) return;
    container.innerHTML = `<section class="th-social-fail" role="status"><span>DATA GATE</span><h2>证据暂不可用</h2><p>没有通过本地数据合同读取，因此不显示平台数值。请检查静态数据文件后重试。</p><button type="button" data-th-social-retry>重新加载</button></section>`;
  }

  function renderPlatformRows() {
    return selectedPlatforms().map((platform) => {
      const value = metricValue(platform);
      const display = value === null || value === undefined ? "未公开" : `${Number(value).toFixed(1)}%`;
      const width = value === null || value === undefined ? 0 : Math.max(0, Math.min(100, Number(value)));
      const range = Array.isArray(platform.corroborated_range_pct)
        ? `交叉区间 ${platform.corroborated_range_pct[0].toFixed(1)}–${platform.corroborated_range_pct[1].toFixed(1)}%`
        : "暂无同口径区间";
      return `<article class="th-social-platform-row ${value === null || value === undefined ? "is-missing" : ""}" data-platform="${escapeAttr(platform.id)}">
        <div class="th-social-platform-name"><i aria-hidden="true"></i><div><b>${escapeHtml(platform.name)}</b><small>${escapeHtml(tierLabels[platform.tier] || platform.tier)} · ${platform.source_count}类证据</small></div></div>
        <div class="th-social-platform-track" aria-label="${escapeAttr(platform.name)} ${escapeAttr(metricLabel())} ${escapeAttr(display)}"><span style="width:${width}%"></span><em>${escapeHtml(display)}</em></div>
        <div class="th-social-platform-proof"><b>${escapeHtml(confidenceLabels[platform.confidence] || platform.confidence)}</b><small>${escapeHtml(range)}</small></div>
        <div class="th-social-platform-role"><b>${escapeHtml(platform.role)}</b><small>${escapeHtml(platform.decision_note)}</small></div>
      </article>`;
    }).join("");
  }

  function renderDecisionLayers() {
    return (state.data?.decision_layers || []).map((item) => `<article class="th-social-decision-card ${escapeAttr(item.key)}">
      <span>${escapeHtml(item.label)}</span>
      <b>${escapeHtml(item.platforms.join(" + "))}</b>
      <p>${escapeHtml(item.objective)}</p>
    </article>`).join("");
  }

  function renderSources() {
    return (state.data?.source_classes || []).map((item) => `<article class="th-social-source-card">
      <div><span>${escapeHtml(item.period)}</span><b>${escapeHtml(item.label)}</b></div>
      <p>${escapeHtml(item.grain)}</p>
      <small>${escapeHtml(item.use)}</small>
      <a href="${escapeAttr(item.url)}" target="_blank" rel="noopener">查看原始证据 ↗</a>
    </article>`).join("");
  }

  function render() {
    const container = root();
    const data = state.data;
    if (!container || !data) return;
    const population = data.population || {};
    const highConfidence = data.platforms.filter((item) => item.confidence === "high").length;
    const coreOver80 = data.platforms.filter((item) => item.monthly_usage_pct >= 80).length;
    container.innerHTML = `<div class="th-social-shell">
      <section class="th-social-hero" aria-labelledby="th-social-title">
        <div class="th-social-hero-copy">
          <span>THAILAND · SOCIAL DECISION SYSTEM</span>
          <h2 id="th-social-title">泰国不是单平台市场，四个平台共同构成规模入口</h2>
          <p>主排序使用同口径的月度用户渗透率；广告触达、新闻使用和外部引流只作为旁证。所有策略推论均保留数据边界。</p>
        </div>
        <div class="th-social-hero-seal" aria-label="数据核验状态"><small>最新可比受众期</small><b>${escapeHtml(data.audience_period)}</b><em>多源交叉核验</em></div>
      </section>

      <section class="th-social-kpis" aria-label="泰国社交媒体市场核心指标">
        <article><span>互联网用户</span><b>${Number(population.internet_users_million).toFixed(1)}<small>百万</small></b><em>市场规模母体</em></article>
        <article><span>社媒用户身份</span><b>${Number(population.social_user_identities_million).toFixed(1)}<small>百万</small></b><em>非严格唯一人数</em></article>
        <article><span>80%以上平台</span><b>${coreOver80}<small>个</small></b><em>Facebook / LINE / TikTok / YouTube</em></article>
        <article><span>高可信平台</span><b>${highConfidence}<small>个</small></b><em>至少三类证据支持</em></article>
      </section>

      <section class="th-social-board" aria-labelledby="th-social-board-title">
        <header class="th-social-board-head">
          <div><span>01 · AUDIENCE REACH</span><h3 id="th-social-board-title">平台覆盖轨道</h3><p>${escapeHtml(metricLabel())} · 用户可同时使用多个平台，数值不能相加。</p></div>
          <div class="th-social-controls">
            <div role="group" aria-label="指标口径">
              <button type="button" data-th-social-metric="monthly" class="${state.metric === "monthly" ? "active" : ""}" aria-pressed="${state.metric === "monthly"}">月度用户渗透率</button>
              <button type="button" data-th-social-metric="ad" class="${state.metric === "ad" ? "active" : ""}" aria-pressed="${state.metric === "ad"}">广告可触达率</button>
            </div>
            <div role="group" aria-label="平台分层">
              ${[["all", "全部"], ["core", "核心"], ["support", "补充"], ["emerging", "观察"]].map(([key, label]) => `<button type="button" data-th-social-tier="${key}" class="${state.tier === key ? "active" : ""}" aria-pressed="${state.tier === key}">${label}</button>`).join("")}
            </div>
          </div>
        </header>
        <div class="th-social-axis" aria-hidden="true"><span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span></div>
        <div class="th-social-platform-list">${renderPlatformRows()}</div>
      </section>

      <section class="th-social-decision" aria-labelledby="th-social-decision-title">
        <header><span>02 · MEDIA ROLE</span><h3 id="th-social-decision-title">从覆盖数据到媒介任务</h3><p>这是策略推论，不是预算分配结果；预算仍需结合车型、人群、素材和真实转化数据。</p></header>
        <div>${renderDecisionLayers()}</div>
      </section>

      <section class="th-social-audit" aria-labelledby="th-social-audit-title">
        <header><span>03 · EVIDENCE AUDIT</span><h3 id="th-social-audit-title">多源核验与指标边界</h3><p>来源类别、样本时间和可使用范围分别保留，避免“多来源”被误解为同口径平均。</p></header>
        <div class="th-social-source-grid">${renderSources()}</div>
        <aside class="th-social-guardrails"><b>使用前必须保留</b>${data.guardrails.map((item) => `<span>${escapeHtml(item)}</span>`).join("")}</aside>
      </section>
    </div>`;
  }

  async function load() {
    if (state.loading) return;
    state.loading = true;
    state.error = "";
    renderLoading();
    try {
      const response = await fetch(DATA_URL, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (data?.market?.code !== "TH" || !Array.isArray(data.platforms) || !data.platforms.length) throw new Error("invalid contract");
      state.data = data;
      render();
    } catch (error) {
      state.error = error?.message || "load failed";
      state.data = null;
      renderError();
    } finally {
      state.loading = false;
    }
  }

  function bind() {
    const container = root();
    if (!container) return;
    container.addEventListener("click", (event) => {
      const retry = event.target.closest("[data-th-social-retry]");
      if (retry) { load(); return; }
      const metric = event.target.closest("[data-th-social-metric]");
      if (metric) { state.metric = metric.dataset.thSocialMetric; render(); return; }
      const tier = event.target.closest("[data-th-social-tier]");
      if (tier) { state.tier = tier.dataset.thSocialTier; render(); }
    });
  }

  function init() {
    if (!root()) return;
    bind();
    load();
  }

  window.MMNThailandSocialDashboard = { load, render };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init, { once: true });
  else init();
})();
