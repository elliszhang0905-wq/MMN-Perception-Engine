from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SocialEvidenceV2UiContractTest(unittest.TestCase):
    def test_client_loads_neutral_v2_capability_and_uses_persistent_jobs(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("loadSocialEvidenceCapabilities", app)
        self.assertIn('api("/api/social-evidence/capabilities")', app)
        self.assertIn('api("/api/social-evidence/jobs"', app)
        self.assertIn('/api/social-evidence/jobs/${encodeURIComponent(jobId)}', app)
        self.assertIn('"/api/social-evidence/marts/latest?"', app)
        self.assertIn("供应商信息仅保留在内部运维层", app)

    def test_social_trend_and_brand_penetration_have_distinct_v2_mart_renderers(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        demo = (ROOT / "demo-brand-weekly-radar.html").read_text(encoding="utf-8")
        self.assertIn("function renderSocialTrendEvidenceMart", app)
        self.assertIn('martType!=="social_trend"', app)
        self.assertIn('type:"mmn-brand-penetration-mart"', app)
        self.assertIn("function renderBrandPenetrationMart", demo)
        self.assertIn("mmn-brand-penetration-mart", demo)
        self.assertIn('martType!=="brand_penetration"', demo)

    def test_v2_query_plan_and_coverage_are_visible_before_and_after_collection(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="social-evidence-plan"', html)
        self.assertIn('id="social-evidence-coverage"', html)
        self.assertIn("renderSocialEvidencePlan", app)
        self.assertIn("证据覆盖", app)
        self.assertIn("缺失平台", app)

    def test_v2_copy_preserves_evidence_boundary(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        demo = (ROOT / "demo-brand-weekly-radar.html").read_text(encoding="utf-8")
        boundary = "公开平台传播证据不能单独证明市场需求、购买意愿或成交因果"
        self.assertIn(boundary, html)
        self.assertIn("传播关联不等于市场渗透或销售因果", demo)


if __name__ == "__main__":
    unittest.main()
