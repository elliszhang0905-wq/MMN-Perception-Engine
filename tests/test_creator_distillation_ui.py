import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CreatorDistillationUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = (ROOT / "app.js").read_text(encoding="utf-8")

    def test_content_distillation_and_opinion_validation_are_separate_surfaces(self):
        self.assertIn("博主内容能力蒸馏", self.app)
        self.assertIn("重点车型舆情辅助验证", self.app)
        self.assertIn('mediaEvidence=evidence.filter(x=>x.evidence_type!=="comment")', self.app)
        self.assertIn('comments=evidence.filter(x=>x.evidence_type==="comment")', self.app)

    def test_raw_comments_are_collapsed_and_not_described_as_creator_dna(self):
        self.assertIn("查看原始评论证据", self.app)
        self.assertIn("评论只用于车型营销监测的辅助验证，不进入博主内容 DNA", self.app)
        self.assertIn("双模型尚未在共同证据上达成一致", self.app)
        self.assertIn("当前重点车型", self.app)
        self.assertIn("不计入该车型正式监测结论", self.app)

    def test_each_asset_can_request_and_render_media_evidence(self):
        self.assertIn('data-creator-action="media"', self.app)
        self.assertIn('/media`,{method:"POST"', self.app)
        self.assertIn("获取媒体证据", self.app)
        self.assertIn("mediaProcessing.message", self.app)

    def test_content_dna_surface_exposes_cross_validation_release_gate(self):
        self.assertIn("dna.contentValidation?.status", self.app)
        self.assertIn("双模型共同证据质检通过", self.app)
        self.assertIn("模型质检未通过，禁止发布", self.app)


if __name__ == "__main__":
    unittest.main()
