"""Product-whitepaper evidence extraction helpers.

The model may propose evidence, but only verbatim, page-addressable claims that
survive a second-model review are eligible for the marketing match score.
"""

import re


PRODUCT_LABEL_KEYWORDS = {
    "用车场景": ("用车场景", "场景", "通勤", "出行", "家庭", "户外", "露营"),
    "外观": ("外观", "造型", "设计", "车灯", "灯光", "姿态"),
    "内饰": ("内饰", "材质", "饰板", "氛围灯"),
    "空间": ("空间", "轴距", "储物", "后备箱", "乘坐"),
    "舒适性": ("舒适", "座椅", "静谧", "空调", "按摩", "悬架"),
    "配置": ("配置", "标配", "选装", "装备"),
    "动力与操控": ("动力", "操控", "驾控", "底盘", "转向", "制动", "加速", "悬架"),
    "智能座舱": ("智能座舱", "座舱", "屏幕", "交互", "语音", "音响", "智能助手"),
    "辅助/自动驾驶": ("智能驾驶", "驾驶辅助", "激光雷达", "雷达", "摄像头", "泊车"),
    "质量": ("质量", "品质", "耐久", "可靠", "工艺"),
    "品牌口碑": ("奥迪", "品牌", "豪华", "品质承诺"),
    "价格": ("价格", "售价", "权益", "优惠", "版本"),
    "用户服务": ("服务", "售后", "交付", "保修", "客户"),
    "安全": ("安全", "碰撞", "电池安全", "气囊", "车身强度", "制动"),
    "用车成本": ("能耗", "续航", "充电", "电耗", "效率"),
}

PRODUCT_LABELS = tuple(PRODUCT_LABEL_KEYWORDS)


def _compact(value):
    return re.sub(r"\s+", "", str(value or "")).strip().lower()


def readable_pdf_pages(parsed):
    pages = {}
    for segment in parsed.get("segments") or []:
        page = segment.get("pageNo") or (segment.get("locator") or {}).get("pageNo")
        text = str(segment.get("text") or "").strip()
        if page and text:
            pages[int(page)] = (pages.get(int(page), "") + "\n" + text).strip()
    return pages


def product_page_candidates(pages, per_label=3):
    """Return traceable page candidates for every one of the 15 NSR labels."""
    output = {}
    for label, keywords in PRODUCT_LABEL_KEYWORDS.items():
        ranked = []
        for page, text in pages.items():
            score = sum(_compact(text).count(_compact(keyword)) for keyword in keywords)
            if score:
                ranked.append((score, page))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        output[label] = [page for _, page in ranked[:per_label]]
    return output


def select_product_pages(pages, per_label=3, max_pages=36, max_chars=48000):
    """Select a diverse, bounded set of pages rather than overloading one topic."""
    candidates = product_page_candidates(pages, per_label=per_label)
    selected = [page for page in (1, 2) if page in pages]
    # Round-robin selection prevents early labels from consuming the page cap.
    for rank in range(per_label):
        for label in PRODUCT_LABELS:
            rows = candidates.get(label) or []
            if rank < len(rows) and rows[rank] not in selected:
                selected.append(rows[rank])
            if len(selected) >= max_pages:
                break
        if len(selected) >= max_pages:
            break
    output, used = [], 0
    for page in selected:
        text = pages.get(page, "")
        remaining = max_chars - used
        if remaining <= 0:
            break
        clipped = text[:remaining]
        output.append({"page": page, "text": clipped})
        used += len(clipped)
    return output


def extraction_prompt(model, selected_pages):
    source = "\n\n".join(f"[PDF第{item['page']}页]\n{item['text']}" for item in selected_pages)
    labels = "、".join(PRODUCT_LABELS)
    return f"""你是汽车产品证据分析员。请从以下《{model}产品白皮书》原文中抽取可用于营销判断的产品能力事实。

严格要求：
1. 只能使用给出的原文，不补充常识，不做竞品推断。
2. 每条必须包含原文逐字引句 quote 和对应 PDF 页码 page；没有明确事实就不输出。
3. label 只能从以下标准标签中选择：{labels}。
4. claim 是对原文事实的简短归纳，不得扩大原文含义。
5. 按15个标准属性逐项检查；没有原文事实的属性保持缺失，严禁补齐。优先提取带参数、功能机制、配置或可验证结果的事实，最多 30 条。

只返回 JSON：
{{"capabilities":[{{"label":"安全","claim":"简短归纳","quote":"原文逐字引句","page":13}}]}}

白皮书原文：
{source}"""


def normalize_capabilities(raw, pages, limit=30):
    payload = raw if isinstance(raw, dict) else {}
    items = payload.get("capabilities") or []
    normalized = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or "").strip()
        claim = str(item.get("claim") or "").strip()
        quote = str(item.get("quote") or "").strip()
        try:
            page = int(item.get("page"))
        except (TypeError, ValueError):
            continue
        quote_key = _compact(quote)
        if label not in PRODUCT_LABELS or len(quote_key) < 8 or quote_key not in _compact(pages.get(page, "")):
            continue
        key = (page, quote_key)
        if key in seen:
            continue
        seen.add(key)
        normalized.append({"label": label, "claim": claim[:120] or quote[:120], "quote": quote[:220], "page": page})
        if len(normalized) >= limit:
            break
    return normalized


def review_prompt(model, capabilities, pages):
    referenced = sorted({item["page"] for item in capabilities})
    source = "\n\n".join(f"[PDF第{page}页]\n{pages.get(page, '')}" for page in referenced)
    return f"""你是第二位汽车产品证据审校员。请逐条复核通义千问从《{model}产品白皮书》中抽取的能力事实。

仅保留同时满足：页码正确、quote 在该页原文中逐字存在、claim 未扩大原意、label 合理的项目。
对保留项目必须原样返回 label、claim、quote、page；不允许改写 quote。最多 30 条。
只返回 JSON：{{"capabilities":[{{"label":"安全","claim":"...","quote":"原文逐字引句","page":13}}]}}

待复核项目：
{capabilities}

对应原文：
{source}"""


def dual_model_consensus(primary, reviewer):
    reviewed = {(item["page"], _compact(item["quote"])) for item in reviewer}
    return [item for item in primary if (item["page"], _compact(item["quote"])) in reviewed]
