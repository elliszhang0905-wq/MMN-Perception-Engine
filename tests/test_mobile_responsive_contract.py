import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MobileResponsiveContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.style = (ROOT / "style.css").read_text(encoding="utf-8")

    def test_social_actions_and_thresholds_collapse_to_one_column(self):
        self.assertIn(".social-primary-actions{grid-column:1;grid-row:auto;flex-wrap:wrap}", self.style)
        self.assertIn(".social-thresholds>div{grid-template-columns:1fr}", self.style)

    def test_project_weights_do_not_keep_four_columns_on_mobile(self):
        self.assertIn(".weight-grid{grid-template-columns:repeat(2,minmax(0,1fr))}", self.style)

    def test_eval_grid_children_can_shrink_around_scrollable_table(self):
        self.assertIn(".mmn-eval-page>*,#mmn-eval-root{min-width:0}", self.style)
        self.assertIn(".mmn-eval-table-wrap{overflow:auto}", self.style)


if __name__ == "__main__":
    unittest.main()
