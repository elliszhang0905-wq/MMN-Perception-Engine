(() => {
  "use strict";

  const causalChainLabel = "政策 → 购车门槛 → 车型竞争力 → 营销机会";
  const profiles = {};
  const regions = ["北京", "天津", "上海", "重庆", "河北", "山西", "辽宁", "吉林", "黑龙江", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南", "广东", "海南", "四川", "贵州", "云南", "陕西", "甘肃", "青海", "内蒙古", "广西", "西藏", "宁夏", "新疆"];
  const regionLabels = { 北京: "北京市", 天津: "天津市", 上海: "上海市", 重庆: "重庆市", 河北: "河北省", 山西: "山西省", 辽宁: "辽宁省", 吉林: "吉林省", 黑龙江: "黑龙江省", 江苏: "江苏省", 浙江: "浙江省", 安徽: "安徽省", 福建: "福建省", 江西: "江西省", 山东: "山东省", 河南: "河南省", 湖北: "湖北省", 湖南: "湖南省", 广东: "广东省", 海南: "海南省", 四川: "四川省", 贵州: "贵州省", 云南: "云南省", 陕西: "陕西省", 甘肃: "甘肃省", 青海: "青海省", 内蒙古: "内蒙古自治区", 广西: "广西壮族自治区", 西藏: "西藏自治区", 宁夏: "宁夏回族自治区", 新疆: "新疆维吾尔自治区" };
  const state = { loaded: false, loading: false, loadRequest: 0, model: "奥迪E7X", focusModel: "", region: "上海", scenario: "置换更新", data: null, comparisons: [], analysisId: "", strategyValidation: null, strategyLoading: false, strategyError: "", strategyRequest: 0 };
  const root = () => document.querySelector("#policy-intelligence-root");
  const esc = value => String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
  const money = value => value !== null && value !== undefined && value !== "" && Number.isFinite(Number(value)) ? `¥${Math.round(Number(value)).toLocaleString("zh-CN")}` : "—";
  const unresolvedPolicyImpact = item => ["vehicle_profile_incomplete", "variant_required"].includes(item?.evidenceStatus);
  const benefitOf = item => unresolvedPolicyImpact(item) ? null : Number(item?.maxVerifiedBenefit || item?.maxConditionalBenefit || 0);
  const priceOf = item => unresolvedPolicyImpact(item) ? null : Number(item?.maxVerifiedBenefit || 0) > 0 ? item?.postPolicyReferencePrice : item?.postPolicyConditionalPrice;
  const priceBasisNote = item => Number(item?.profile?.baasDiscount || 0) > 0 ? `BaaS起售价 ${money(item.profile.price)}（含电池参考价 ${money(item.profile.listPrice)}，已减${money(item.profile.baasDiscount)}）` : "";
  const edition = () => { try { return activeEdition(); } catch (_) { return "china"; } };
  const headers = () => {
    try { return authHeaders({ "Content-Type": "application/json" }); }
    catch (_) { return { "Content-Type": "application/json" }; }
  };

  async function jsonFetch(url, options = {}) {
    const response = await fetch(url, { ...options, headers: { ...headers(), ...(options.headers || {}) } });
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(typeof data.error === "string" ? data.error : "政策分析服务暂不可用");
    return data;
  }

  function syncProfiles(options = []) {
    options.forEach(item => {
      const model = String(item?.model || "").trim(), price = Number(item?.price || 0);
      if (!model || !Number.isFinite(price) || price <= 0) return;
      profiles[model] = {
        ...profiles[model],
        ...item,
        role: "own",
        price,
        energyType: item.energyType || "待核验",
        bodyType: item.bodyType || "待核验",
      };
    });
  }

  function dashboardUrl(model, region = state.region, scenario = state.scenario) {
    const profile = profiles[model];
    if (!profile) throw new Error("所选车型缺少销量预警政策输入，暂不能测算。");
    const query = Object.fromEntries(Object.entries({ edition: edition(), model, region, scenario, ...profile })
      .filter(([, value]) => value !== undefined && value !== null && value !== ""));
    return `/api/policy-intelligence/dashboard?${new URLSearchParams(query)}`;
  }

  function comparisonUrl(model, region = state.region, scenario = state.scenario) {
    return `/api/group-dashboard-demo?${new URLSearchParams({ edition: edition(), policy_model: model, policy_region: region, policy_scenario: scenario })}`;
  }

  async function load(force = false) {
    if (!force && (state.loading || state.loaded)) return;
    const requestId = ++state.loadRequest;
    const selection = { model: state.model, region: state.region, scenario: state.scenario };
    state.loading = true;
    if (root()) root().innerHTML = '<div class="policy-loading"><b>正在关联官方规则与车型价格</b><span></span><span></span><span></span></div>';
    try {
      const group = await jsonFetch(comparisonUrl(selection.model, selection.region, selection.scenario));
      if (requestId !== state.loadRequest) return;
      const comparisons = group?.policyIntelligence?.models || [];
      if (!comparisons.some(item => item?.role === "own" && item?.model === selection.model)) throw new Error("所选车型未进入当前销量预警细分市场，无法生成同场对比。");
      syncProfiles(group?.policyIntelligence?.ownModelOptions || []);
      const own = await jsonFetch(dashboardUrl(selection.model, selection.region, selection.scenario));
      if (requestId !== state.loadRequest) return;
      state.data = own;
      state.comparisons = comparisons.map(item => item.vehicleImpact).filter(Boolean);
      state.loaded = true;
      render();
      if (!state.strategyValidation && !state.strategyLoading) void startEvaluation(false);
    } catch (error) {
      if (requestId !== state.loadRequest) return;
      if (root()) root().innerHTML = `<div class="policy-error"><b>政策环境分析未完成</b><p>${esc(error.message)}</p><button type="button" data-policy-retry>重新加载</button></div>`;
      root()?.querySelector("[data-policy-retry]")?.addEventListener("click", () => load(true));
    } finally { if (requestId === state.loadRequest) state.loading = false; }
  }

  function renderControls() {
    return `<form class="policy-controls" id="policy-controls">
      <label><span>上汽重点监测车型（本品）</span><select name="model">${Object.entries(profiles).filter(([, profile]) => profile.role === "own").map(([name]) => `<option ${name === state.model ? "selected" : ""}>${esc(name)}</option>`).join("")}</select></label>
      <label><span>重点区域（省／直辖市）</span><select name="region">${regions.map(name => `<option value="${name}" ${name === state.region ? "selected" : ""}>${regionLabels[name]}</option>`).join("")}</select></label>
      <label><span>购车情景</span><select name="scenario">${["直接购车", "置换更新", "报废更新"].map(name => `<option ${name === state.scenario ? "selected" : ""}>${name}</option>`).join("")}</select></label>
      <button type="submit">重新计算</button>
    </form>`;
  }

  function renderMap(items) {
    const positions = { 北京: [69, 27], 上海: [78, 55], 广东: [63, 79], 浙江: [75, 60], 四川: [38, 61], 湖北: [57, 58], 江苏: [71, 52] };
    return `<section class="policy-panel policy-map-panel"><div class="policy-panel-head"><div><span>NATIONAL POLICY MAP</span><h3>全国政策强度</h3></div><em>点击省／直辖市切换车型影响</em></div>
      <div class="policy-map-layout"><div class="policy-map-canvas" role="group" aria-label="全国重点区域政策强度地图">
        <svg viewBox="0 0 100 90" aria-hidden="true"><path d="M15 25L28 14 43 17 51 10 65 17 83 22 89 38 81 48 84 60 73 67 67 80 52 76 43 84 32 72 18 69 22 57 10 48Z"/></svg>
        ${items.map(item => { const [x, y] = positions[item.region] || [50, 50]; const size = 30 + item.policyStrength * .22; return `<button type="button" class="policy-city-bubble ${item.region === state.region ? "active" : ""}" data-policy-region="${item.region}" style="left:${x}%;top:${y}%;--bubble-size:${size}px;--strength:${item.policyStrength}%" title="${regionLabels[item.region] || item.region}：${item.activePolicyCount}项，参考优惠${money(item.averageBenefit)}"><b>${regionLabels[item.region] || item.region}</b><span>${item.policyStrength}</span></button>`; }).join("")}
      </div><div class="policy-map-rank">${[...items].sort((a,b) => b.policyStrength-a.policyStrength).map(item => `<button type="button" data-policy-region="${item.region}" class="${item.region === state.region ? "active" : ""}"><span>${regionLabels[item.region] || item.region}<small>${item.activePolicyCount}项有效规则</small></span><i><u style="width:${item.policyStrength}%"></u></i><b>${money(item.averageBenefit)}</b></button>`).join("")}</div></div></section>`;
  }

  function renderTrend(items) {
    const max = Math.max(1, ...items.map(item => item.averageBenefit));
    return `<section class="policy-panel policy-trend-panel"><div class="policy-panel-head"><div><span>12-MONTH SIGNAL</span><h3>政策数量与力度变化</h3></div><em>按政策发布时间</em></div><div class="policy-trend-chart">${items.map(item => `<div title="${item.month}：${item.policyCount}项，${money(item.averageBenefit)}"><span>${item.policyCount ? item.policyCount : ""}</span><i style="height:${Math.max(3, item.averageBenefit / max * 100)}%"></i><small>${item.month.slice(5)}</small></div>`).join("")}</div><div class="policy-trend-legend"><span><i></i>平均可计算权益</span><span>新能源规则仅作为政策覆盖口径，不推断销量</span></div></section>`;
  }

  function renderComparison(items) {
    if (!items.some(item => item.model !== state.model)) return "";
    const chartItems = items.filter(item => !unresolvedPolicyImpact(item) && priceOf(item) !== null);
    const maxBenefit = Math.max(1, ...chartItems.map(benefitOf));
    const prices = chartItems.map(priceOf).filter(value => value !== null && value !== undefined);
    if (!chartItems.length || !prices.length) return `<section class="policy-panel policy-competition"><div class="policy-panel-head"><div><span>MODEL IMPACT</span><h3>车型竞争力对比</h3></div><em>待补充车型档案</em></div><p class="policy-empty">当前对比车型缺少精确动力形式、车身形式或价格，暂不计算权益与政策后价格。</p></section>`;
    const minPrice = Math.min(...prices) * .96, maxPrice = Math.max(...prices) * 1.04;
    return `<section class="policy-panel policy-competition"><div class="policy-panel-head"><div><span>MODEL IMPACT</span><h3>资格满足后的车型竞争力气泡</h3></div><em>${esc(state.region)} · ${esc(state.scenario)} · 点击仅查看对比</em></div>
      <div class="policy-causal-chain" aria-label="${causalChainLabel}"><span>已审核政策规则</span><b>→</b><span>测算购车成本变化</span><b>→</b><span>同场车型位置</span><b>→</b><span>可验证营销动作</span></div>
      <div class="policy-bubble-chart"><div class="policy-axis-y"><span>条件满足后参考价高</span><span>条件满足后参考价低</span></div><div class="policy-bubble-stage">${chartItems.map(item => { const price = priceOf(item); const basis = priceBasisNote(item); const x = 12 + (benefitOf(item) / maxBenefit) * 72; const y = 12 + ((price - minPrice) / Math.max(1,maxPrice-minPrice)) * 72; const size = 58 + Number(item.verifiedPolicyCount || 0) * 12; return `<button type="button" class="policy-model-bubble ${item.model === state.model ? "own" : ""} ${item.model === state.focusModel ? "focus" : ""}" aria-pressed="${item.model === state.focusModel}" title="${esc(basis ? `${basis}；` : "")}点击只查看对比，不会切换本品" style="left:${x}%;top:${y}%;--model-size:${size}px" data-policy-model="${esc(item.model)}"><span>${item.model === state.model ? "本品" : "竞品"}</span><b>${esc(item.model)}</b><small>${money(price)}</small></button>`; }).join("")}</div><div class="policy-axis-x"><span>条件权益低</span><span>条件权益高</span></div></div>
      <div class="policy-comparison-table">${items.map(item => { const basis = priceBasisNote(item), incomplete = item.evidenceStatus === "vehicle_profile_incomplete", variantRequired = item.evidenceStatus === "variant_required", unresolved = incomplete || variantRequired; return `<article class="${item.model === state.model ? "own" : ""} ${item.model === state.focusModel ? "focus" : ""}"><div><span>${item.model === state.model ? "本品" : "同场竞品"}</span><b>${esc(item.model)}</b></div><strong>${money(benefitOf(item))}<small>${incomplete ? "车型档案待补充" : variantRequired ? "需选择具体动力版本" : "满足条件时权益上限"}</small></strong><strong>${money(priceOf(item))}<small>${unresolved ? "暂不计算" : "条件满足后参考价"}</small></strong><em>${incomplete ? "待补充精确动力／车身／价格" : variantRequired ? `${item.variantRequiredPolicyCount || 0}项版本相关规则待确认` : `${item.verifiedPolicyCount}项规则`}${basis ? `<small>${esc(basis)}</small>` : ""}</em></article>`; }).join("")}</div></section>`;
  }

  function renderImpact(impact) {
    const incomplete = impact.evidenceStatus === "vehicle_profile_incomplete";
    const variantRequired = impact.evidenceStatus === "variant_required";
    const emptyMessage = incomplete
      ? "车型档案未满足审核门槛，暂不计算；补充后会自动重新审核。"
      : variantRequired
        ? `当前有${impact.variantRequiredPolicyCount || 0}项规则只适用于部分动力版本，需选择具体动力版本后计算。`
        : "当前车型与购车情景未匹配到已审核政策规则。";
    const variantNotice = variantRequired ? `<p class="policy-empty">${esc(emptyMessage)}</p>` : "";
    return `<section class="policy-panel policy-impact"><div class="policy-panel-head"><div><span>CAUSAL TRACE</span><h3>${esc(impact.model)}在${esc(impact.region)}的规则影响链</h3></div><em>${money(benefitOf(impact))} 条件上限</em></div>
      <p class="policy-scenario-note">${esc(impact.scenarioLabel)}</p>
      <div class="policy-effect-list">${variantNotice}${impact.policyEffects.length ? impact.policyEffects.map(effect => `<article><div class="policy-effect-value"><span>${esc(effect.policyType)}</span><strong>${money(effect.benefit)}</strong><small>${variantRequired ? "具体版本确认后计入" : effect.counted ? "计入本情景" : "同组规则未重复计入"}</small></div><div><b>${esc(effect.policyName)}</b><p>${esc(effect.sourceQuote)}</p><small>适用条件：${esc([...effect.consumerConditions, ...effect.vehicleConditions].join("；"))}</small><a href="${esc(effect.sourceUrl)}" target="_blank" rel="noopener">查看官方原文核对</a></div><time>${esc(effect.expiresAt || "长期有效")}</time></article>`).join("") : variantRequired ? "" : `<p class="policy-empty">${esc(emptyMessage)}</p>`}</div>
      <div class="policy-boundary"><b>因果边界</b><span>${esc(impact.causalBoundary)}</span></div></section>`;
  }

  function renderOpportunities(items) {
    const validation = state.strategyValidation;
    const final = validation?.finalStrategy;
    const canEvaluate = state.analysisId && ["aligned", "manual_required"].includes(validation?.status);
    const statusLabel = validation?.status === "aligned" ? "多方审核一致" : validation?.status === "manual_required" ? "审核冲突·待人工判断" : validation?.status === "incomplete" ? "独立审核未完成" : validation?.status === "insufficient_evidence" ? "证据不足" : "等待交叉复核";
    const strategyPanel = `<div class="policy-three-model" id="policy-eval-panel" aria-live="polite"><div class="policy-three-model-head"><div><span>MMN交叉验证结论 · ${esc(state.region)}</span><b>${statusLabel}</b></div><button type="button" class="policy-eval-start" ${state.strategyLoading ? "disabled" : ""}>${state.strategyLoading ? "独立审核中…" : "重新运行交叉复核"}</button></div>
      ${state.strategyError ? `<p class="policy-eval-status error">${esc(state.strategyError)}</p>` : state.strategyLoading ? '<p class="policy-eval-status">正在基于同一组已审核政策证据独立分析并交叉验证…</p>' : final ? `<div class="policy-final-strategy"><span>${esc(final.policyJudgement)} · ${esc(final.strategyDirection)} · 最低置信度 ${Math.round(Number(final.confidence || 0) * 100)}%</span><h4>${esc(final.conclusion)}</h4><dl><div><dt>目标人群</dt><dd>${esc(final.targetAudience)}</dd></div><div><dt>区域动作</dt><dd>${esc(final.action)}</dd></div><div><dt>领先指标</dt><dd>${esc(final.leadingIndicator)}</dd></div><div><dt>转化指标</dt><dd>${esc(final.conversionIndicator)}</dd></div><div><dt>停止条件</dt><dd>${esc(final.stopCondition)}</dd></div><div><dt>不确定性</dt><dd>${esc(final.uncertainty)}</dd></div></dl><small>共同政策证据：${final.evidenceIds.length}项 · ${esc(final.modelAgreement)}</small></div>` : `<div class="policy-strategy-boundary"><b>${statusLabel}</b><p>${esc((validation?.reasons || ["选择区域后自动生成多方交叉验证策略。"])[0])}</p></div>`}
      ${canEvaluate ? `<form class="policy-eval-form"><div><b>Policy Eval · 五维各20分</b><span>三模型一致可直接评分；模型冲突须由人工裁决；总分80分以上才进入可用知识版本</span></div>${[["sourceReliability","政策来源可靠性"],["parsingAccuracy","政策解析准确性"],["vehicleMatch","车型匹配合理性"],["marketingLogic","营销建议逻辑"],["actionValue","行动价值"]].map(([key,label]) => `<label><span>${label}</span><input name="${key}" type="number" min="0" max="20" step="1" value="16" required></label>`).join("")}<label class="policy-eval-note"><span>修改记录</span><input name="note" placeholder="写下评分依据或修改要求"></label><button type="submit">提交人工评分</button><p data-eval-message></p></form>` : state.analysisId ? '<p class="policy-eval-status">当前结果未通过完整性硬门槛，不能提交Policy Eval；请重新运行三模型复核。</p>' : ""}</div>`;
    return `<section class="policy-panel policy-opportunities"><div class="policy-panel-head"><div><span>POLICY OPPORTUNITY MAP</span><h3>政策变化对营销意味着什么</h3></div><em>${esc(regionLabels[state.region] || state.region)} · ${esc(state.scenario)}</em></div>${items.map(item => `<article><div class="policy-opportunity-tag"><span>窗口至</span><b>${esc(item.windowEnd)}</b><em>规则引擎草案</em></div><div class="policy-opportunity-body"><h4>${esc(item.label)}</h4><dl><div><dt>已知事实</dt><dd>${esc(item.inference)}</dd></div><div><dt>待验证假设</dt><dd>${esc(item.hypothesis)}</dd></div><div><dt>建议动作</dt><dd>${esc(item.action)}</dd></div></dl><div class="policy-metrics"><span>领先指标：${esc(item.leadingIndicator)}</span><span>转化指标：${esc(item.conversionIndicator)}</span><span>停止条件：${esc(item.stopCondition)}</span></div></div></article>`).join("") || '<p class="policy-empty">暂无满足证据门槛的政策营销机会；三模型不会在无证据时补写结论。</p>'}${strategyPanel}</section>`;
  }

  function renderGovernance(data) {
    return `<section class="policy-panel policy-governance"><div class="policy-panel-head"><div><span>HUMAN IN THE LOOP</span><h3>政策审核与证据治理</h3></div><em>${data.reviewQueue.length}项待核验</em></div>${data.reviewQueue.length ? data.reviewQueue.map(item => `<article><div><b>${esc(item.policyName)}</b><p>${esc(item.sourceQuote || "来源引句待补充")}</p><small>${esc(item.policyType)} · ${esc(item.effectiveAt)}—${esc(item.expiresAt)} · 金额${money(item.subsidyAmount)} / 比例${item.subsidyRate ?? "—"} / 封顶${money(item.subsidyCap)} · 叠加${esc(item.stackMode)}:${esc(item.stackGroup)}</small><a href="${esc(item.originalUrl)}" target="_blank" rel="noopener">打开完整官方原文核对</a></div><span>${esc(item.sourceConfidence)}</span><button type="button" data-policy-review="${esc(item.id)}" data-decision="approved">通过</button><button type="button" class="secondary" data-policy-review="${esc(item.id)}" data-decision="needs_revision">退回</button></article>`).join("") : `<div class="policy-governance-empty"><b>当前无待核验政策，不等于没有政策证据</b><p>${data.summary.activePolicyCount}项已审核政策可进入分析；当前三模型状态：${esc(state.strategyValidation?.status || "分析中")}。仅冲突、缺证据或低置信度案例需要人工介入。</p></div>`}</section>`;
  }

  function render() {
    const data = state.data;
    if (!root() || !data) return;
    root().innerHTML = `${renderControls()}<div class="policy-boundary-strip"><span>${esc(data.meta.positioning)}</span><b>${esc(data.meta.asOf)} 口径</b><p>${esc(data.meta.dataBoundary)}</p></div>
      <div class="policy-kpis"><article><span>当前有效政策</span><b>${data.summary.activePolicyCount}</b><small>仅人工审核通过</small></article><article><span>当前购车方式权益上限</span><b>${money(data.summary.scenarioConditionalBenefit)}</b><small>${esc(data.summary.purchaseScenario)} · 满足列示条件时</small></article><article><span>新能源覆盖率</span><b>${Math.round(data.summary.nevCoverageRate * 100)}%</b><small>已审核规则口径</small></article><article><span>待人工核验</span><b>${data.summary.pendingReviewCount}</b><small>不进入车型分析</small></article></div>
      <div class="policy-grid policy-grid-top">${renderMap(data.map)}${renderTrend(data.trend)}</div>${renderComparison(state.comparisons)}${renderImpact(data.vehicleImpact)}${renderOpportunities(data.opportunities)}${renderGovernance(data)}
      <div class="policy-method-note"><b>方法边界</b><span>${esc(data.meta.causalBoundary)}</span><span>车型补贴后价格是规则测算参考，不是经销商成交价。</span></div>`;
    bind();
  }

  function bind() {
    root()?.querySelector("#policy-controls")?.addEventListener("submit", event => {
      event.preventDefault();
      const form = new FormData(event.currentTarget);
      state.model = form.get("model"); state.focusModel = ""; state.region = form.get("region"); state.scenario = form.get("scenario"); resetStrategy(); state.loaded = false; load(true);
    });
    root()?.querySelector('select[name="region"]')?.addEventListener("change", event => event.currentTarget.form?.requestSubmit());
    root()?.querySelector('select[name="model"]')?.addEventListener("change", event => event.currentTarget.form?.requestSubmit());
    root()?.querySelector('select[name="scenario"]')?.addEventListener("change", event => event.currentTarget.form?.requestSubmit());
    root()?.querySelectorAll("[data-policy-region]").forEach(button => button.addEventListener("click", () => { state.region = button.dataset.policyRegion; resetStrategy(); state.loaded = false; load(true); }));
    root()?.querySelectorAll("[data-policy-model]").forEach(button => button.addEventListener("click", () => { state.focusModel = button.dataset.policyModel; render(); }));
    root()?.querySelectorAll("[data-policy-review]").forEach(button => button.addEventListener("click", () => review(button.dataset.policyReview, button.dataset.decision)));
    root()?.querySelector(".policy-eval-start")?.addEventListener("click", () => startEvaluation(true));
    root()?.querySelector(".policy-eval-form")?.addEventListener("submit", submitEvaluation);
  }

  function resetStrategy() {
    state.strategyRequest += 1; state.analysisId = ""; state.strategyValidation = null; state.strategyLoading = false; state.strategyError = "";
  }

  async function review(policyId, decision) {
    try {
      await jsonFetch("/api/policy-intelligence/review", { method: "POST", body: JSON.stringify({ policyId, decision, note: "Policy Intelligence Dashboard人工复核" }) });
      state.loaded = false; await load(true);
    } catch (error) { window.toast?.(`政策审核失败：${error.message}`); }
  }

  async function startEvaluation(force = false) {
    if (state.strategyLoading || (!force && state.strategyValidation)) return;
    const requestId = ++state.strategyRequest;
    const profile = profiles[state.model];
    const panel = root()?.querySelector("#policy-eval-panel");
    state.strategyLoading = true; state.strategyError = "";
    if (panel) panel.innerHTML = '<p class="policy-eval-status">正在基于同一组已审核政策证据独立分析并交叉验证…</p>';
    try {
      const result = await jsonFetch("/api/policy-intelligence/analyze", { method: "POST", body: JSON.stringify({ edition: edition(), model: state.model, region: state.region, scenario: state.scenario, persist: force, ...profile }) });
      if (requestId !== state.strategyRequest) return;
      state.analysisId = result.analysis?.analysisId || "";
      state.strategyValidation = result.strategyValidation;
      state.data = result.result || state.data;
    } catch (error) { if (requestId === state.strategyRequest) state.strategyError = error.message; }
    finally { if (requestId === state.strategyRequest) { state.strategyLoading = false; render(); } }
  }

  async function submitEvaluation(event) {
    event.preventDefault();
    const target = event.currentTarget;
    if (target.dataset.submitting === "true" || target.dataset.submitted === "true") return;
    const form = new FormData(target), scores = {};
    ["sourceReliability","parsingAccuracy","vehicleMatch","marketingLogic","actionValue"].forEach(key => { scores[key] = Number(form.get(key)); });
    const message = target.querySelector("[data-eval-message]");
    const button = target.querySelector('button[type="submit"]');
    const idleLabel = button?.textContent || "提交人工评分";
    target.dataset.submitting = "true";
    target.setAttribute("aria-busy", "true");
    if (button) { button.disabled = true; button.textContent = "评分提交中…"; }
    message.className = "pending";
    message.textContent = "正在保存评分与修改记录…";
    try {
      const result = await jsonFetch("/api/policy-intelligence/evaluate", { method: "POST", body: JSON.stringify({ analysisId: state.analysisId, scores, note: form.get("note") || "" }) });
      const evaluation = result.evaluation;
      target.dataset.submitted = "true";
      message.className = evaluation.reviewStatus === "evaluated" ? "success" : "needs-revision";
      message.textContent = evaluation.reviewStatus === "evaluated"
        ? `评分已保存并通过：${evaluation.totalScore}/100 · v${evaluation.finalVersion}，已进入可用知识版本。`
        : `评分已保存但未通过：${evaluation.totalScore}/100 · v${evaluation.finalVersion}。修改要求已记录，当前结果未进入可用知识版本。`;
      if (button) button.textContent = "评分已提交";
    } catch (error) {
      message.className = "error";
      message.textContent = `提交失败：${error.message}`;
      if (button) { button.disabled = false; button.textContent = idleLabel; }
    } finally {
      delete target.dataset.submitting;
      target.removeAttribute("aria-busy");
    }
  }

  window.PolicyIntelligenceModule = {
    load,
    select(model, region) {
      if (String(model || "").trim()) state.model = String(model).trim();
      if (regions.includes(region)) state.region = region;
      resetStrategy();
      state.loaded = false;
      return load(true);
    },
    reload: () => { state.loaded = false; return load(true); },
  };
})();
