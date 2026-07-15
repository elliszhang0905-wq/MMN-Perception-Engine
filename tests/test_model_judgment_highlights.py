import unittest

from server import (
    cross_checked_model_judgment_highlights,
    model_judgment_highlight_review_prompt,
    model_judgment_prompt,
    normalize_model_judgment_highlights,
)


class ModelJudgmentHighlightTest(unittest.TestCase):
    def test_prompt_requires_exact_structured_highlights(self):
        prompt = model_judgment_prompt("测试判断", {"model": "智己L6"})
        system = prompt[0]["content"]
        self.assertIn("highlights", system)
        self.assertIn("quote必须逐字存在于对应字段", system)
        self.assertIn("primary最多1条", system)

    def test_review_prompt_requires_an_independent_subset(self):
        prompt = model_judgment_highlight_review_prompt("原文", {"highlights": []}, {})
        system = prompt[0]["content"]
        self.assertIn("独立质检模型", system)
        self.assertIn("不得新增候选中没有的高亮", system)

    def test_normalizer_keeps_only_exact_non_overlapping_quotes(self):
        item = {
            "viewpoint": "不应继续只讲参数领先，而要把技术优势转译成用户愿意换购的豪华体验。",
            "strategy_implication": "优先强化试驾与真实车主证言。",
            "highlights": [
                {"field": "viewpoint", "quote": "用户愿意换购", "level": "primary", "reason": "商业结果"},
                {"field": "viewpoint", "quote": "技术优势转译成用户愿意换购", "level": "primary", "reason": "与已有片段重叠"},
                {"field": "strategy_implication", "quote": "真实车主证言", "level": "primary", "reason": "行动"},
                {"field": "attribution", "quote": "原文中不存在", "level": "secondary", "reason": "无效"},
            ],
        }
        normalized = normalize_model_judgment_highlights(item)["highlights"]
        self.assertEqual([entry["quote"] for entry in normalized], ["用户愿意换购", "真实车主证言"])
        self.assertEqual([entry["level"] for entry in normalized], ["primary", "secondary"])

    def test_normalizer_caps_each_field_highlight_coverage(self):
        item = {
            "viewpoint": "一二三四五六七八九十甲乙丙丁戊己庚辛壬癸",
            "highlights": [
                {"field": "viewpoint", "quote": "一二三四五六七八", "level": "primary"},
                {"field": "viewpoint", "quote": "九十甲乙丙丁戊己", "level": "secondary"},
            ],
        }
        normalized = normalize_model_judgment_highlights(item)["highlights"]
        self.assertEqual([entry["quote"] for entry in normalized], ["一二三四五六七八"])

    def test_cross_check_publishes_only_exact_consensus(self):
        item = normalize_model_judgment_highlights({
            "viewpoint": "把技术优势转译成用户愿意换购的理由。",
            "strategy_implication": "优先强化真实车主证言。",
            "highlights": [
                {"field": "viewpoint", "quote": "用户愿意换购", "level": "primary"},
                {"field": "strategy_implication", "quote": "真实车主证言", "level": "secondary"},
            ],
        })
        reviewer_raw = '{"approved":true,"issues":[],"highlights":[{"field":"viewpoint","quote":"用户愿意换购","level":"primary"}]}'
        result = cross_checked_model_judgment_highlights(item, reviewer_raw)
        self.assertEqual([entry["quote"] for entry in result], ["用户愿意换购"])

    def test_cross_check_fails_closed_when_reviewer_rejects(self):
        item = {"highlights": [{"field": "viewpoint", "quote": "用户愿意换购", "level": "primary"}]}
        self.assertIsNone(cross_checked_model_judgment_highlights(item, '{"approved":false,"issues":["不足"],"highlights":[]}'))


if __name__ == "__main__":
    unittest.main()
