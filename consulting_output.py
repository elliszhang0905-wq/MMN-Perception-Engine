"""Consulting-style presentation contract for MMN strategy outputs.

This module deliberately knows nothing about collection, analysis, routing, or
model providers.  It only defines and checks the final presentation boundary.
"""

import re


CONSULTING_OUTPUT_SECTIONS = (
    "Executive Conclusion",
    "Key Findings",
    "Evidence",
    "Strategic Implication",
    "Action Recommendation",
)

CONSULTING_OUTPUT_INSTRUCTION = (
    "最终交付必须使用 Consulting Output Framework，并严格按以下顺序使用且只使用这五个三级标题："
    "### Executive Conclusion；### Key Findings；### Evidence；"
    "### Strategic Implication；### Action Recommendation。"
    "先给结论，再给解释；Key Findings 中每个判断必须标注关联证据编号，如 [Evidence: E1]，"
    "Evidence 中必须给出对应编号、数据/事实、来源或口径，不得把推断写成事实。"
    "Strategic Implication 必须说明商业影响和取舍，Action Recommendation 必须按优先级给出动作、责任对象、时点和验证指标。"
    "避免描述性复述和空泛形容词。输出前执行 MECE 检查：合并重复判断，确认关键问题、证据、商业影响和行动方向无遗漏；"
    "不要把 MECE 检查过程或底层模型名称写入最终交付。"
)


def render_consulting_output(
    executive_conclusion,
    key_findings,
    evidence,
    strategic_implication,
    action_recommendation,
):
    """Render already-derived content without changing analytical semantics."""
    values = (
        executive_conclusion,
        key_findings,
        evidence,
        strategic_implication,
        action_recommendation,
    )
    blocks = []
    for title, value in zip(CONSULTING_OUTPUT_SECTIONS, values):
        if isinstance(value, (list, tuple)):
            body = "\n".join(str(item).strip() for item in value if str(item).strip())
        else:
            body = str(value or "").strip()
        blocks.append(f"### {title}\n{body}")
    return "\n\n".join(blocks)


def inspect_consulting_output(text):
    """Return deterministic structure and MECE checks for a final output."""
    raw = str(text or "").strip()
    matches = list(re.finditer(r"(?m)^###\s+(.+?)\s*$", raw))
    headings = [match.group(1).strip() for match in matches]
    issues = []

    if headings != list(CONSULTING_OUTPUT_SECTIONS):
        issues.append("五层金字塔标题缺失、顺序错误或包含额外三级标题。")

    sections = {}
    for index, match in enumerate(matches):
        title = match.group(1).strip()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        sections[title] = raw[match.end():end].strip()

    for title in CONSULTING_OUTPUT_SECTIONS:
        if not sections.get(title):
            issues.append(f"{title} 为空。")

    findings = sections.get("Key Findings", "")
    evidence = sections.get("Evidence", "")
    cited_ids = set(re.findall(r"\[Evidence:\s*(E\d+)\]", findings, flags=re.I))
    evidence_ids = set(re.findall(r"(?m)^\s*(?:[-*]\s*)?(E\d+)\s*[:：]", evidence, flags=re.I))
    if findings and not cited_ids:
        issues.append("Key Findings 未将判断关联到证据编号。")
    missing_ids = sorted(cited_ids - evidence_ids)
    if missing_ids:
        issues.append("Evidence 缺少被判断引用的编号：" + "、".join(missing_ids) + "。")

    normalized_findings = []
    for line in findings.splitlines():
        normalized = re.sub(r"\[Evidence:\s*E\d+\]", "", line, flags=re.I)
        normalized = re.sub(r"^[\s\-*\d.、]+", "", normalized).strip().lower()
        if normalized:
            normalized_findings.append(normalized)
    if len(normalized_findings) != len(set(normalized_findings)):
        issues.append("Key Findings 存在重复判断，未通过 MECE 不重复检查。")

    mece_issues = [issue for issue in issues if "重复" in issue or "缺失" in issue or "为空" in issue or "顺序" in issue]
    return {
        "passed": not issues,
        "mecePassed": not mece_issues,
        "sections": headings,
        "evidenceIds": sorted(cited_ids),
        "issues": issues,
    }
