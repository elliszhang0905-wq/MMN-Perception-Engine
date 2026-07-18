import unittest

from opportunity_pipeline import (
    align_fact_label,
    build_competitor_product_summaries,
    build_opportunity_map,
    cross_validate_model_analyses,
    extract_document_version_conflicts,
    heat_scores,
    is_public_official_url,
    normalize_market_signals,
)


class OpportunityPipelineTest(unittest.TestCase):
    def test_version_conflict_is_manual_review(self):
        conflicts = extract_document_version_conflicts(
            "AUDI E7X 产品白皮书 V260410.pdf",
            ["AUDI E7X 产品白皮书", "Ver.260309"],
        )
        self.assertEqual(conflicts["status"], "manual_required")
        self.assertIn("V260410", conflicts["candidates"])
        self.assertIn("Ver.260309", conflicts["candidates"])

    def test_product_points_align_to_one_or_manual_label(self):
        self.assertEqual(align_fact_label("285/40 R22轮胎与22英寸轮毂"), {"label": "外观", "status": "aligned"})
        self.assertEqual(align_fact_label("不明的概念卖点")["status"], "unmatched")
        self.assertEqual(align_fact_label("座椅通风与后排空间")["status"], "ambiguous")

    def test_heat_is_normalized_with_log_volume_and_interaction(self):
        rows = [
            {"label": "外观", "volume": 0, "interaction": 0},
            {"label": "智能座舱", "volume": 100, "interaction": 1000},
        ]
        scored = heat_scores(rows)
        self.assertEqual(scored["外观"], 0.0)
        self.assertGreater(scored["智能座舱"], 0.9)

    def test_heat_aggregates_repeated_labels_and_is_order_independent(self):
        rows = [
            {"label": "舒适性", "volume": 100, "interaction": 10},
            {"label": "配置", "volume": 50, "interaction": 50},
            {"label": "舒适性", "volume": 1, "interaction": 100},
        ]

        forward = heat_scores(rows)
        reversed_rows = heat_scores(list(reversed(rows)))

        self.assertEqual(forward, reversed_rows)
        self.assertEqual(forward["舒适性"], 1.0)
        self.assertLess(forward["配置"], forward["舒适性"])

    def test_market_signals_align_by_unified_label(self):
        result = normalize_market_signals([
            {"attribute": "座舱智能", "nsr": 0.6, "volume": 10, "interaction": 20, "platform": "抖音"}
        ])
        self.assertEqual(result[0]["label"], "智能座舱")
        self.assertEqual(result[0]["platform"], "抖音")

    def test_model_conflict_needs_human_and_aligned_models_can_publish(self):
        base = {"label": "外观", "factStrength": 0.8, "direction": "seize", "evidenceIds": ["fact-1"], "confidence": 0.9}
        aligned = cross_validate_model_analyses({"qwen": [base], "deepseek": [dict(base)]}, {"fact-1"})
        self.assertEqual(aligned["status"], "aligned")
        self.assertEqual(aligned["items"][0]["commonEvidenceIds"], ["fact-1"])
        conflict = dict(base)
        conflict["direction"] = "repair"
        checked = cross_validate_model_analyses({"qwen": [base], "deepseek": [conflict]}, {"fact-1"})
        self.assertEqual(checked["status"], "manual_required")
        self.assertIn("外观", [item["label"] for item in checked["manualItems"]])

    def test_cross_validation_rejects_labels_outside_the_unified_taxonomy(self):
        invented = {
            "label": "豪华科技感",
            "factStrength": 0.9,
            "direction": "seize",
            "evidenceIds": ["fact-1"],
            "confidence": 0.9,
        }

        checked = cross_validate_model_analyses(
            {"qwen": [invented], "deepseek": [dict(invented)]},
            {"fact-1"},
        )

        self.assertEqual(checked["status"], "manual_required")
        self.assertIn("标签不在MMN统一标签中", checked["manualItems"][0]["reasons"])

    def test_cross_validation_keeps_only_evidence_cited_by_both_models(self):
        qwen = {"label": "舒适性", "factStrength": 0.8, "direction": "seize", "evidenceIds": ["fact-1", "fact-2"], "confidence": 0.9}
        deepseek = {"label": "舒适性", "factStrength": 0.75, "direction": "seize", "evidenceIds": ["fact-2", "fact-3"], "confidence": 0.85}

        checked = cross_validate_model_analyses(
            {"qwen": [qwen], "deepseek": [deepseek]},
            {"fact-1", "fact-2", "fact-3"},
        )

        self.assertEqual(checked["status"], "aligned")
        self.assertEqual(checked["items"][0]["commonEvidenceIds"], ["fact-2"])

    def test_cross_validation_rejects_disjoint_model_evidence(self):
        qwen = {"label": "舒适性", "factStrength": 0.8, "direction": "seize", "evidenceIds": ["fact-1"], "confidence": 0.9}
        deepseek = {"label": "舒适性", "factStrength": 0.75, "direction": "seize", "evidenceIds": ["fact-2"], "confidence": 0.85}

        checked = cross_validate_model_analyses(
            {"qwen": [qwen], "deepseek": [deepseek]},
            {"fact-1", "fact-2"},
        )

        self.assertEqual(checked["status"], "manual_required")
        self.assertEqual(checked["items"], [])
        self.assertIn("双模型缺少共同证据", checked["manualItems"][0]["reasons"])

    def test_cross_validation_requires_each_model_to_cite_evidence(self):
        no_evidence = {
            "label": "舒适性", "factStrength": 0.8, "direction": "seize",
            "evidenceIds": [], "confidence": 0.9,
        }

        checked = cross_validate_model_analyses(
            {"qwen": [no_evidence], "deepseek": [dict(no_evidence)]},
            {"fact-1"},
        )

        self.assertEqual(checked["status"], "manual_required")
        self.assertIn("模型未引用可核验证据", checked["manualItems"][0]["reasons"])

    def test_opportunity_map_is_evidence_aware(self):
        rows = build_opportunity_map(
            [{"label": "外观", "factStrength": 0.9, "recognition": 0.2, "heat": 0.1, "competitorPressure": 0.5, "evidenceStatus": "aligned"}],
            validated=True,
        )
        self.assertEqual(rows[0]["category"], "seize")
        self.assertGreater(rows[0]["opportunityScore"], 40)
        pending = build_opportunity_map(
            [{"label": "智能座舱", "factStrength": 0.9, "recognition": 0.2, "heat": 0.1, "competitorPressure": 0.5, "evidenceStatus": "manual_required"}],
            validated=False,
        )
        self.assertEqual(pending[0]["category"], "manual_required")

    def test_aligned_items_keep_their_quadrants_when_other_labels_need_review(self):
        rows = build_opportunity_map([
            {"label": "质量", "factStrength": 0.35, "recognition": 0.2, "heat": 0.8, "competitorPressure": 0.3, "competitorLead": 0.3, "purchaseImpact": 5, "direction": "repair", "evidenceStatus": "aligned"},
            {"label": "空间", "factStrength": 0.85, "recognition": 0.35, "heat": 0.3, "competitorPressure": 0.25, "competitorLead": 0.25, "purchaseImpact": 4, "direction": "seize", "evidenceStatus": "aligned"},
            {"label": "智能座舱", "evidenceStatus": "manual_required", "manualReasons": ["双模型方向冲突"], "competitorLead": -0.1, "purchaseImpact": 4},
        ], validated=True)

        by_label = {item["label"]: item for item in rows}
        self.assertEqual(by_label["质量"]["categoryLabel"], "优先修复")
        self.assertEqual(by_label["空间"]["categoryLabel"], "抢占空位")
        self.assertEqual(by_label["智能座舱"]["categoryLabel"], "待人工确认")
        self.assertEqual(by_label["质量"]["mapX"], 0.3)
        self.assertEqual(by_label["质量"]["mapY"], 5.0)
        self.assertEqual(by_label["智能座舱"]["mapX"], -0.1)

    def test_competitor_product_summaries_expose_only_dual_model_verified_nsr_strengths(self):
        sources = [
            {"model": "竞品A", "status": "verified", "finalUrl": "https://example.com/a"},
            {"model": "竞品B", "status": "manual_required", "finalUrl": "https://example.com/b", "failureReason": "官网限制访问"},
        ]
        facts = [
            {"id": "a-space", "sourceModel": "竞品A", "sourceUrl": "https://example.com/a", "label": "空间", "alignmentStatus": "aligned", "claim": "轴距 3000mm，后排空间更充裕", "confidence": 0.85},
            {"id": "a-comfort", "sourceModel": "竞品A", "sourceUrl": "https://example.com/a", "label": "舒适性", "alignmentStatus": "aligned", "claim": "前后排座椅通风加热", "confidence": 0.85},
            {"id": "a-unverified", "sourceModel": "竞品A", "sourceUrl": "https://example.com/a", "label": "价格", "alignmentStatus": "aligned", "claim": "限时优惠", "confidence": 0.85},
        ]
        validation = {
            "items": [
                {"label": "空间", "factStrength": 0.91, "evidenceStatus": "aligned", "commonEvidenceIds": ["a-space"]},
                {"label": "舒适性", "factStrength": 0.82, "evidenceStatus": "aligned", "commonEvidenceIds": ["a-comfort"]},
                {"label": "价格", "factStrength": 0.95, "evidenceStatus": "manual_required", "commonEvidenceIds": ["a-unverified"]},
            ],
        }

        summaries = build_competitor_product_summaries(sources, facts, validation)

        verified = summaries[0]
        self.assertEqual(verified["model"], "竞品A")
        self.assertEqual([item["label"] for item in verified["coreProductStrengths"]], ["空间", "舒适性"])
        self.assertEqual(verified["coreProductStrengths"][0]["claim"], "轴距 3000mm，后排空间更充裕")
        self.assertEqual(summaries[1]["coreProductStrengths"], [])
        self.assertEqual(summaries[1]["failureReason"], "官网限制访问")

    def test_private_and_non_http_official_urls_are_rejected(self):
        self.assertFalse(is_public_official_url("http://127.0.0.1:8765/product"))
        self.assertFalse(is_public_official_url("file:///tmp/product.html"))
        self.assertFalse(is_public_official_url("https://192.168.1.3/product"))
        resolver = lambda host, port, type=None: [(None, None, None, None, ("93.184.216.34", port))]
        self.assertTrue(is_public_official_url("https://www.audi.cn/product", resolver=resolver))

    def test_https_domains_work_behind_macos_fake_ip_proxy_without_allowing_direct_fake_ip(self):
        fake_ip_resolver = lambda host, port, type=None: [(None, None, None, None, ("198.18.0.25", port))]
        self.assertTrue(is_public_official_url("https://www.audi.cn/product", resolver=fake_ip_resolver))
        self.assertFalse(is_public_official_url("https://198.18.0.25/product", resolver=fake_ip_resolver))


if __name__ == "__main__":
    unittest.main()
