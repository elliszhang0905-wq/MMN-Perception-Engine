import unittest

from product_whitepaper import (
    dual_model_consensus,
    normalize_capabilities,
    product_page_candidates,
    PRODUCT_LABELS,
    readable_pdf_pages,
    select_product_pages,
)


class ProductWhitepaperTest(unittest.TestCase):
    def setUp(self):
        self.pages = {
            1: "AUDI E7X 产品白皮书",
            2: "目录 外观设计 智能座舱 动力与操控 安全",
            13: "数字矩阵LED大灯可实现多种迎宾灯语，并支持自定义灯光签名。",
            80: "高性能制动系统缩短制动响应时间，车身采用高强度材料。",
        }

    def test_readable_pages_ignores_scanned_placeholder(self):
        parsed = {"segments": [
            {"pageNo": 1, "text": "第一页", "locator": {}},
            {"pageNo": 2, "text": "", "locator": {"ocrRequired": True}},
        ]}
        self.assertEqual(readable_pdf_pages(parsed), {1: "第一页"})

    def test_page_selection_is_bounded_and_keeps_traceable_pages(self):
        selected = select_product_pages(self.pages, per_label=1, max_pages=3, max_chars=200)
        self.assertLessEqual(len(selected), 3)
        self.assertEqual(selected[0]["page"], 1)
        self.assertTrue(all(item["page"] in self.pages for item in selected))

    def test_targeted_candidates_cover_all_fifteen_nsr_labels_without_invention(self):
        pages = {index + 10: keyword for index, keyword in enumerate((
            "通勤场景", "外观造型", "内饰材质", "后排空间", "舒适座椅",
            "标配装备", "底盘操控", "智能座舱", "驾驶辅助", "可靠品质",
            "奥迪品牌", "售价权益", "售后服务", "碰撞安全", "充电能耗",
        ))}
        candidates = product_page_candidates(pages, per_label=1)
        self.assertEqual(tuple(candidates), PRODUCT_LABELS)
        self.assertEqual(len(PRODUCT_LABELS), 15)
        self.assertTrue(all(candidates[label] for label in PRODUCT_LABELS))

    def test_normalizer_rejects_hallucinated_quote_and_page(self):
        raw = {"capabilities": [
            {"label": "外观", "claim": "支持灯光签名", "quote": "支持自定义灯光签名", "page": 13},
            {"label": "安全", "claim": "不存在", "quote": "白皮书从未出现的事实", "page": 80},
            {"label": "外观", "claim": "错页", "quote": "支持自定义灯光签名", "page": 80},
        ]}
        result = normalize_capabilities(raw, self.pages)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["page"], 13)

    def test_dual_model_consensus_requires_same_page_and_quote(self):
        primary = [
            {"label": "外观", "claim": "灯光签名", "quote": "支持自定义灯光签名", "page": 13},
            {"label": "安全", "claim": "制动响应", "quote": "缩短制动响应时间", "page": 80},
        ]
        reviewer = [
            {"label": "外观", "claim": "灯光签名", "quote": "支持自定义灯光签名", "page": 13},
            {"label": "安全", "claim": "制动响应", "quote": "缩短制动响应时间", "page": 13},
        ]
        self.assertEqual(dual_model_consensus(primary, reviewer), primary[:1])


if __name__ == "__main__":
    unittest.main()
