import unittest

from consulting_output import (
    CONSULTING_OUTPUT_INSTRUCTION,
    CONSULTING_OUTPUT_SECTIONS,
    inspect_consulting_output,
    render_consulting_output,
)
from server import fuse_strategy, llm_strategy_prompt, local_rag_strategy_answer, review_agent_strategy


class ConsultingOutputFrameworkTest(unittest.TestCase):
    def test_rendered_output_follows_pyramid_and_passes_mece_check(self):
        text = render_consulting_output(
            "应先修复核心购买疑虑，再扩大传播。",
            [
                "- 用户决策阻力高于声量不足。[Evidence: E1]",
                "- 核心平台已经具备承接条件。[Evidence: E2]",
            ],
            [
                "- E1：负向风险 62，高于正向分 41；来源为当前项目诊断。",
                "- E2：抖音为当前声量第一平台；来源为平台声量数据。",
            ],
            "若继续扩大泛曝光，预算会放大疑虑而非购买理由。",
            "P0：7天内上线疑虑实测内容；市场团队负责；以负向评论占比下降验证。",
        )

        result = inspect_consulting_output(text)

        self.assertTrue(result["passed"])
        self.assertTrue(result["mecePassed"])
        self.assertEqual(list(CONSULTING_OUTPUT_SECTIONS), result["sections"])
        self.assertEqual(["E1", "E2"], result["evidenceIds"])

    def test_check_rejects_missing_evidence_and_duplicate_findings(self):
        text = render_consulting_output(
            "先修复疑虑。",
            ["- 修复疑虑。[Evidence: E1]", "- 修复疑虑。[Evidence: E1]"],
            "- E2：样本量 100。",
            "影响转化。",
            "本周处理。",
        )

        result = inspect_consulting_output(text)

        self.assertFalse(result["passed"])
        self.assertFalse(result["mecePassed"])
        self.assertTrue(any("E1" in issue for issue in result["issues"]))
        self.assertTrue(any("重复" in issue for issue in result["issues"]))

    def test_prompt_contract_requires_all_five_sections_and_mece(self):
        for title in CONSULTING_OUTPUT_SECTIONS:
            self.assertIn(title, CONSULTING_OUTPUT_INSTRUCTION)
        self.assertIn("MECE", CONSULTING_OUTPUT_INSTRUCTION)

    def test_strategy_prompts_use_framework_without_legacy_heading_contracts(self):
        for drill_type in ("strategy_ppt_brief", "content_asset_strategy", "cognition_strategy", "general"):
            prompt = llm_strategy_prompt({"drillType": drill_type}, "MMN主控")[0]["content"]
            for title in CONSULTING_OUTPUT_SECTIONS:
                self.assertIn(title, prompt)
            self.assertNotIn("严格使用10个小标题", prompt)

    def test_local_rag_and_fusion_fallbacks_pass_framework_check(self):
        local_text = local_rag_strategy_answer(
            "下一步怎么做",
            {"model": "测试车型"},
            [{"title": "当前平台声量"}],
        )
        self.assertTrue(inspect_consulting_output(local_text)["passed"])

        contexts = [
            {"drillType": "strategy_ppt_brief", "project": {"model": "测试车型"}},
            {"drillType": "content_asset_strategy", "project": {"model": "测试车型"}},
            {"drillType": "cognition_strategy", "project": {"model": "测试车型"}},
            {"drillType": "general", "project": {"model": "测试车型"}},
        ]
        for context in contexts:
            text = fuse_strategy(context, rule_text="当前规则判断有证据支持。")
            self.assertTrue(inspect_consulting_output(text)["passed"], context["drillType"])

    def test_agent_review_exposes_framework_status(self):
        qa = review_agent_strategy(
            "普通AI总结",
            evidence=[{"platform": "抖音", "published_at": "2026-07-17"}],
            signal_summary={"diagnostic_count": 1},
            question="下一步怎么做",
        )

        self.assertFalse(qa["consultingFramework"]["passed"])
        self.assertTrue(any(item["category"] == "consulting_output" for item in qa["findings"]))


if __name__ == "__main__":
    unittest.main()
