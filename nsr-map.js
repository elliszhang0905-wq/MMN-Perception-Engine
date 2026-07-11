(function(root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  root.MmnNsrMap = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function() {
  const STATUS_LABELS = {
    strength: "优势，可巩固",
    neutral: "中性，需加强",
    risk: "风险，优先补强",
    data_missing: "数据不足",
  };

  function finite(value) {
    if (value === null || value === undefined) return null;
    const text = String(value).trim();
    if (!text || ["-", "—", "/", "n/a", "na", "null", "none"].includes(text.toLowerCase())) return null;
    const percent = text.endsWith("%");
    const number = Number(text.replace(/,/g, "").replace(/%$/, ""));
    return Number.isFinite(number) ? (percent ? number / 100 : number) : null;
  }

  function mean(values) {
    const valid = values.map(finite).filter(value => value !== null);
    return valid.length ? valid.reduce((sum, value) => sum + value, 0) / valid.length : null;
  }

  function unique(values) {
    return [...new Set((values || []).filter(Boolean))];
  }

  function statusFor(nsr, sourceScores, missingSources) {
    const sourceValues = Object.values(sourceScores);
    const expectedCount = sourceValues.length + missingSources.length;
    const minimumCount = Math.min(2, expectedCount);
    if (sourceValues.length < minimumCount) return "data_missing";
    if (nsr !== null && (nsr <= 0 || sourceValues.some(value => value <= -0.2))) return "risk";
    if (!missingSources.length && nsr !== null && nsr >= 0.6 && sourceValues.every(value => value >= 0.4)) return "strength";
    return "neutral";
  }

  function priorityFor(status, nsr, gap, impact) {
    const safeImpact = finite(impact) || 3;
    if (status === "risk") return 80 + Math.abs(Math.min(nsr || 0, 0)) * 30 + safeImpact * 5;
    if (status === "strength") return 50 + Math.max(nsr || 0, 0) * 30 + safeImpact * 4;
    if (status === "data_missing") return 20 + safeImpact * 3;
    return 30 + Math.abs(gap || 0) * 25 + safeImpact * 4;
  }

  function rankNsrLabel(result, label) {
    const ownModel = result?.ownModel || "";
    const items = (result?.items || []).filter(item => item.label === label);
    const isRanked = item => item.status !== "data_missing" && finite(item.nsr) !== null;
    const rankedCount = items.filter(isRanked).length;
    let rank = 0;
    return [...items]
      .sort((left, right) => {
        const leftMissing = isRanked(left) ? 0 : 1;
        const rightMissing = isRanked(right) ? 0 : 1;
        return leftMissing - rightMissing || (right.nsr || 0) - (left.nsr || 0) || left.model.localeCompare(right.model, "zh-CN");
      })
      .map(item => ({
        ...item,
        isOwn: item.model === ownModel,
        rank: isRanked(item) ? ++rank : null,
        rankTotal: rankedCount,
      }));
  }

  function buildDataFirstNsrMap({ rows = [], ownModel = "", selectedModels = [], expectedSources = [] } = {}) {
    const selected = unique([ownModel, ...selectedModels]);
    const usable = (rows || []).filter(row => selected.includes(row.model) && row.label && row.source && finite(row.nsr) !== null);
    const sources = unique(expectedSources.length ? expectedSources : usable.map(row => row.source));
    const buckets = new Map();

    for (const row of usable) {
      const key = `${row.model}\u0000${row.label}`;
      if (!buckets.has(key)) buckets.set(key, { model: row.model, label: row.label, category: row.category || "", values: [] });
      buckets.get(key).values.push(row);
    }

    const ownLabels = unique(usable.filter(row => row.model === ownModel).map(row => row.label));
    for (const model of selected) {
      for (const label of ownLabels) {
        const key = `${model}\u0000${label}`;
        if (!buckets.has(key)) buckets.set(key, { model, label, category: "", values: [] });
      }
    }

    const items = [...buckets.values()].map(bucket => {
      const sourceScores = {};
      for (const source of sources) {
        const value = mean(bucket.values.filter(row => row.source === source).map(row => row.nsr));
        if (value !== null) sourceScores[source] = value;
      }
      const nsr = mean(Object.values(sourceScores));
      const impact = mean(bucket.values.map(row => row.impact)) || 3;
      const coverageCount = Object.keys(sourceScores).length;
      const coverageTotal = sources.length;
      return {
        model: bucket.model,
        label: bucket.label,
        category: bucket.category,
        nsr,
        impact,
        sourceScores,
        coverageCount,
        coverageTotal,
        coverageLabel: coverageCount < Math.min(2, coverageTotal) ? `${coverageCount}/${coverageTotal}来源，不参与排名` : coverageCount < coverageTotal ? `${coverageCount}/${coverageTotal}来源，可参与排名` : `${coverageCount}/${coverageTotal}来源`,
        missingSources: sources.filter(source => sourceScores[source] === undefined),
      };
    });

    const ownByLabel = new Map(items.filter(item => item.model === ownModel).map(item => [item.label, item]));
    const completed = items.map(item => {
      const own = ownByLabel.get(item.label);
      const competitors = items.filter(candidate => candidate.label === item.label && candidate.model !== ownModel && candidate.model !== item.model);
      const competitorMean = mean(competitors.map(candidate => candidate.nsr));
      const gap = item.model === ownModel
        ? ((competitorMean ?? item.nsr ?? 0) - (item.nsr ?? 0))
        : ((item.nsr ?? 0) - (own?.nsr ?? item.nsr ?? 0));
      const status = statusFor(item.nsr, item.sourceScores, item.missingSources);
      return {
        ...item,
        gap,
        status,
        statusLabel: STATUS_LABELS[status],
        priority: priorityFor(status, item.nsr, gap, item.impact),
        basis: "imported_nsr_only",
      };
    }).sort((left, right) => right.priority - left.priority || left.label.localeCompare(right.label, "zh-CN"));

    return {
      basis: "imported_nsr_only",
      ownModel,
      selectedModels: selected,
      expectedSources: sources,
      items: completed,
      summary: completed.reduce((summary, item) => {
        summary[item.status] += 1;
        return summary;
      }, { strength: 0, neutral: 0, risk: 0, data_missing: 0 }),
    };
  }

  return { STATUS_LABELS, buildDataFirstNsrMap, rankNsrLabel };
});
