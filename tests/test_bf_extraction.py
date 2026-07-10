import unittest

from bf_factory.extraction import (
    build_tags,
    classify_bf_profile,
    extract_brief,
)


def segment(text, page=1, block="TEXT"):
    return {
        "text": text,
        "blockType": block,
        "pageNo": page,
        "slideNo": None,
        "paragraphNo": page,
        "sheetName": None,
        "cellRange": None,
        "locator": {"pageNo": page, "paragraphNo": page},
    }


class BFExtractionTest(unittest.TestCase):
    def test_seed_profile_is_recognized_without_closing_the_type_system(self):
        result = classify_bf_profile(
            [
                segment("高质感摄影BF 视觉大片 Lifestyle拍摄"),
                segment("镜头语言 必拍镜头 车务流程 素材回传"),
            ]
        )
        self.assertEqual(result["primaryCode"], "HIGH_END_PHOTOGRAPHY")
        self.assertIn("SHOT_LIST", result["contentIntents"])

    def test_mixed_new_need_becomes_custom_profile_with_composable_intents(self):
        result = classify_bf_profile(
            [
                segment("车展期女性用户第一视角体验"),
                segment("需要与核心竞品做同场景对比，并采集动态路跑素材"),
                segment("最终输出达人短视频和评论区讨论方向"),
            ]
        )
        self.assertEqual(result["primaryCode"], "CUSTOM")
        self.assertIn("FEMALE_EXPERIENCE", result["contentIntents"])
        self.assertIn("COMPETITOR_COMPARISON", result["contentIntents"])
        self.assertIn("DYNAMIC_MATERIAL_CAPTURE", result["contentIntents"])
        self.assertIn("女性", result["suggestedName"])

    def test_extraction_populates_six_layers_tags_and_field_provenance(self):
        segments = [
            segment("BF名称：智己L6车展体验BF\n品牌：智己\n车型：智己L6\n竞品：小米SU7、蔚来ET5", 1),
            segment("项目阶段：车展期\n传播目标：种草、认知建立\n目标用户：年轻女性用户", 2),
            segment("核心产品卖点：灵蜥数字底盘、智慧灯光\n必须表达：底盘舒适与操控兼顾", 3),
            segment("内容方向：女性第一视角真实体验\n脚本框架：疑虑开场-体验证据-竞品对比-CTA", 4),
            segment("拍摄要求：必须完成静态体验和动态路跑素材回传\n交付格式：9:16竖屏视频", 5),
            segment("禁止表达：不得使用第一、唯一、绝对安全\n是否允许聊价格：否", 6),
            segment("官方资料：https://example.com/official", 7),
        ]
        payload = extract_brief(
            segments,
            document={
                "documentId": "doc-1",
                "projectId": "project-1",
                "clientKey": "client-a",
                "fileName": "brief.docx",
                "uploadedAt": "2026-07-10T10:00:00+00:00",
            },
        )

        self.assertEqual(payload["strategy"]["brand"], "智己")
        self.assertEqual(payload["strategy"]["competitors"], ["小米SU7", "蔚来ET5"])
        self.assertIn("灵蜥数字底盘", payload["product"]["coreSellingPoints"])
        self.assertIn("女性第一视角真实体验", payload["content"]["contentDirections"])
        self.assertTrue(payload["execution"]["dynamicMaterialRequirements"])
        self.assertFalse(payload["risk"]["isPriceAllowed"])
        self.assertEqual(payload["materials"][0]["url"], "https://example.com/official")
        self.assertEqual(payload["provenance"]["/strategy/brand"][0]["sourceLocator"], "第1页/段落1")
        self.assertIn("智己", payload["tags"]["brands"])
        self.assertIn("女性用户", " ".join(payload["tags"]["userPainPoints"] + payload["strategy"]["targetAudience"]))

    def test_build_tags_keeps_custom_profile_and_content_intents(self):
        payload = {
            "classification": {"bfType": "CUSTOM", "contentIntents": ["FEMALE_EXPERIENCE"]},
            "strategy": {"brand": "智己", "model": "智己L6", "competitors": ["小米SU7"], "projectStage": "车展期", "communicationGoals": ["种草"], "userPainPoints": []},
            "product": {"coreSellingPoints": ["底盘"]},
            "content": {"creatorTypes": ["女性生活方式"], "contentTypes": ["体验"], "topicDirections": ["女性体感"]},
            "execution": {"locationRequirements": ["车展"]},
            "risk": {"expressionRedLines": ["绝对化"]},
            "materials": [],
        }
        tags = build_tags(payload)
        self.assertEqual(tags["bfTypes"], ["CUSTOM"])
        self.assertIn("FEMALE_EXPERIENCE", tags["contentFormats"])


if __name__ == "__main__":
    unittest.main()
