import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NsrValidationUiContractTest(unittest.TestCase):
    def test_vehicle_decision_exposes_same_model_nsr_validation_flow(self):
        source = (ROOT / "vehicle-decision.js").read_text(encoding="utf-8")
        self.assertIn("/api/social-evidence/nsr-context", source)
        self.assertIn("/api/social-evidence/query-plans/preview", source)
        self.assertIn("/api/social-evidence/jobs/latest", source)
        self.assertIn('centerType:"nsr_validation"', source)
        self.assertIn("最近 7 天", source)
        self.assertIn("最近 30 天", source)
        self.assertIn("自定义日期", source)
        self.assertIn("自定义时间窗最长为90天", source)
        self.assertIn('maxPages:10', source)
        self.assertIn("社媒结果不会回写或重算 NSR", source)
        self.assertIn("data-nsr-adjudicate", source)
        self.assertIn("partial_page_limit", source)
        self.assertIn("collectionCoverage", source)

    def test_nsr_typography_uses_inherited_family_and_consistent_weight_scale(self):
        css = (ROOT / "vehicle-decision.css").read_text(encoding="utf-8")
        start = css.index(".vehicle-nsr-validation{")
        section = css[start:css.index("@media(max-width:1000px)", start)]
        self.assertIn("font-family:inherit", section)
        self.assertNotIn("font-weight:800", section)
        self.assertNotIn("font-weight:900", section)

    def test_vehicle_decision_script_has_valid_javascript_syntax(self):
        completed = subprocess.run(
            ["node", "--check", str(ROOT / "vehicle-decision.js")],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
