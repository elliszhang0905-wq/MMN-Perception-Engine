import unittest

from bf_factory.generation import (
    compose_section_plan,
    generate_internal_strategy,
    render_adaptive_brief,
)
from bf_factory.schema import new_brief_payload


def base_payload(profile="STORE_VISIT", intents=None):
    payload = new_brief_payload("project-1", "client-a", "source.docx")
    payload["classification"].update(
        {
            "bfType": profile,
            "bfTypeLabel": profile,
            "confidence": 0.8,
            "reasons": ["测试"],
            "contentIntents": intents or [],
        }
    )
    payload["strategy"].update(
        {
            "bfName": "智己L6商业化BF",
            "bfType": profile,
            "brand": "智己",
            "model": "智己L6",
            "competitors": ["小米SU7"],
            "projectStage": "车展期",
            "communicationGoals": ["种草", "认知建立"],
            "targetAudience": ["年轻女性用户"],
            "currentCommunicationProblem": "卖点多但缺少可复述的用户利益",
            "finalContentDirection": "建立真实体验证据",
        }
    )
    payload["product"]["coreSellingPoints"] = ["灵蜥数字底盘", "智慧灯光"]
    payload["product"]["avoidLeadingWith"] = ["没有体验证据的参数堆砌"]
    payload["content"]["contentDirections"] = ["女性第一视角真实体验"]
    payload["content"]["mustShoot"] = ["底盘体验", "灯光演示"]
    payload["execution"]["dynamicMaterialRequirements"] = ["完成合规路段动态素材采集"]
    payload["risk"]["prohibitedExpressions"] = ["不得使用第一、唯一、绝对安全"]
    payload["provenance"]["/product/coreSellingPoints"] = [
        {
            "originType": "EXTRACTED",
            "sourceDocumentId": "doc-1",
            "sourceSegmentId": "seg-3",
            "sourceLocator": "第3页",
            "sourceFieldPath": "",
            "excerpt": "核心卖点",
            "confidence": 0.9,
            "isManual": False,
        }
    ]
    return payload


class BFGenerationTest(unittest.TestCase):
    def test_seed_profiles_have_distinct_section_plans(self):
        store = compose_section_plan(base_payload("STORE_VISIT"))
        cloud = compose_section_plan(base_payload("CLOUD_REVIEW"))
        photo = compose_section_plan(base_payload("HIGH_END_PHOTOGRAPHY"))

        self.assertIn("STORE_VISIT_SCRIPT", [item["intent"] for item in store])
        self.assertIn("TOPIC_MATRIX", [item["intent"] for item in cloud])
        self.assertIn("SHOT_LIST", [item["intent"] for item in photo])
        self.assertNotEqual([item["intent"] for item in store], [item["intent"] for item in cloud])

    def test_custom_mixed_need_composes_new_sections_instead_of_forcing_seed_template(self):
        payload = base_payload(
            "CUSTOM",
            ["FEMALE_EXPERIENCE", "COMPETITOR_COMPARISON", "DYNAMIC_MATERIAL_CAPTURE", "COMMENT_GUIDANCE"],
        )
        plan = compose_section_plan(payload)
        intents = [item["intent"] for item in plan]
        self.assertIn("FEMALE_EXPERIENCE", intents)
        self.assertIn("COMPETITOR_COMPARISON", intents)
        self.assertIn("DYNAMIC_MATERIAL_CAPTURE", intents)
        self.assertNotIn("STORE_VISIT_SCRIPT", intents)

        strategy = generate_internal_strategy(payload, retrieval_context=[])
        rendered = render_adaptive_brief(payload, strategy, plan)
        self.assertIn("女性用户体验任务", rendered["markdown"])
        self.assertIn("竞品同场景对比", rendered["markdown"])
        self.assertIn("动态素材采集", rendered["markdown"])

    def test_internal_strategy_has_decision_risk_and_execution_fields(self):
        payload = base_payload("STORE_VISIT")
        result = generate_internal_strategy(
            payload,
            retrieval_context=[{"title": "优质探店样本", "sample_grade": "QUALITY", "source": "brief-1"}],
        )
        self.assertEqual(
            set(result),
            {
                "currentCommunicationProblem",
                "bestAngle",
                "avoidLeadingWith",
                "competitorPressure",
                "creatorRole",
                "finalDirection",
                "riskAvoidance",
                "executionMusts",
                "evidenceRefs",
                "judgmentOrigin",
            },
        )
        self.assertEqual(result["judgmentOrigin"], "MMN_STRATEGY_INFERENCE")
        self.assertIn("brief-1", result["evidenceRefs"])

    def test_rendered_brief_marks_strategy_inference_and_source_locations(self):
        payload = base_payload("STORE_VISIT")
        strategy = generate_internal_strategy(payload, [])
        result = render_adaptive_brief(payload, strategy, compose_section_plan(payload))
        self.assertIn("策略推断", result["markdown"])
        self.assertIn("第3页", result["markdown"])
        self.assertGreater(len(result["sections"]), 5)


if __name__ == "__main__":
    unittest.main()
