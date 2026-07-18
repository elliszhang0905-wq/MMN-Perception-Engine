import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MmnEvalUiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.app = (ROOT / "app.js").read_text(encoding="utf-8")
        cls.css = (ROOT / "style.css").read_text(encoding="utf-8")

    def test_eval_navigation_and_page_are_registered_under_system_settings(self):
        system_start = self.html.index("<summary>系统设置</summary>")
        system_end = self.html.index("</details>", system_start)
        system_nav = self.html[system_start:system_end]
        self.assertIn('data-page="eval">Eval评测</button>', system_nav)
        self.assertIn('class="page" id="eval"', self.html)
        self.assertIn('id="mmn-eval-root"', self.html)
        self.assertIn('id="mmn-eval-review-dialog"', self.html)
        self.assertIn('eval:"Eval评测"', self.app)

    def test_eval_page_uses_real_api_routes_and_render_cycle(self):
        self.assertIn('let mmnEvalState={loading:false,running:false,data:null,error:"",filter:"all",activeCaseId:""}', self.app)
        self.assertIn('function loadMmnEvalDashboard()', self.app)
        self.assertIn('function runMmnEval()', self.app)
        self.assertIn('function renderMmnEval()', self.app)
        self.assertIn('function openMmnEvalReview(caseId)', self.app)
        self.assertIn('function saveMmnEvalReview(decision)', self.app)
        self.assertIn('api("/api/eval/report")', self.app)
        self.assertIn('api("/api/eval/run",{method:"POST",body:"{}"})', self.app)
        self.assertIn('api("/api/eval/human-review"', self.app)
        self.assertIn("renderMmnEval();", self.app)

    def test_eval_page_is_honest_about_seed_data_and_missing_baseline(self):
        self.assertIn("当前为种子验证集，只证明评测机制可工作，不代表 MMN 真实业务能力成绩", self.app)
        self.assertIn("尚无可对比基线", self.app)
        self.assertNotIn("v0.0-seed", self.app)
        self.assertNotIn("86.7", self.app)

    def test_eval_page_has_filters_accessible_review_and_error_states(self):
        self.assertIn('["human_review","待复核"]', self.app)
        self.assertIn('data-eval-filter="${key}"', self.app)
        self.assertIn('aria-label="MMN Eval结果筛选"', self.app)
        self.assertIn('id="mmn-eval-review-note"', self.html)
        self.assertIn('id="mmn-eval-review-message" aria-live="polite"', self.html)
        self.assertIn("MMN Eval 报告加载失败", self.app)
        self.assertIn("当前没有可展示的 Eval 报告", self.app)

    def test_eval_styles_follow_existing_mmn_tokens_and_responsive_layout(self):
        self.assertIn(".mmn-eval-page", self.css)
        self.assertIn(".mmn-eval-summary", self.css)
        self.assertIn(".mmn-eval-dimension-track", self.css)
        self.assertIn(".mmn-eval-review-banner", self.css)
        self.assertIn(".mmn-eval-table", self.css)
        self.assertIn("@media(max-width:900px)", self.css)


if __name__ == "__main__":
    unittest.main()
