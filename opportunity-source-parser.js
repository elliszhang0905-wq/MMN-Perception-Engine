(function (root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.parseOpportunityCompetitorSources = api.parseOpportunityCompetitorSources;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function parseOpportunityCompetitorSources(value) {
    const items = [];
    const errors = [];
    String(value || "").split(/\r?\n/).forEach((rawLine, index) => {
      const text = rawLine.trim();
      if (!text) return;
      const match = text.match(/https?:\/\/[^\s|，；]+/i);
      if (!match) {
        errors.push({ line: index + 1, text, reason: "未识别到HTTP(S)官网地址" });
        return;
      }
      const url = match[0].replace(/[。；;,，）)]+$/, "");
      const prefix = text.slice(0, match.index).replace(/[\s|｜:：—-]+$/, "").trim();
      try {
        const parsed = new URL(url);
        if (!/^https?:$/.test(parsed.protocol)) throw new Error("unsupported protocol");
      } catch (_) {
        errors.push({ line: index + 1, text, reason: "官网地址格式无效" });
        return;
      }
      items.push({ model: prefix || `竞品${items.length + 1}`, url });
    });
    return { items, errors };
  }

  return { parseOpportunityCompetitorSources };
});
