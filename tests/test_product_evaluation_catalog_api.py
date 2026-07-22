import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER = (ROOT / "server.py").read_text(encoding="utf-8")


class ProductEvaluationCatalogApiContractTest(unittest.TestCase):
    def test_catalog_get_and_post_routes_are_registered(self):
        self.assertGreaterEqual(SERVER.count('parsed.path == "/api/product-evaluation-catalog"'), 2)
        self.assertIn("list_product_evaluation_datasets", SERVER)
        self.assertIn("save_product_evaluation_dataset", SERVER)

    def test_catalog_write_is_admin_only_in_cloud_mode(self):
        allowed = re.search(r"TRIAL_POST_ALLOWED_PATHS = frozenset\(\{([\s\S]*?)\}\)", SERVER)
        self.assertIsNotNone(allowed)
        self.assertNotIn("/api/product-evaluation-catalog", allowed.group(1))

    def test_catalog_upload_has_size_and_validation_failures(self):
        self.assertIn("4 * 1024 * 1024 + 65536", SERVER)
        self.assertIn("产品评价数据包超出上传限制", SERVER)
        self.assertIn("except ValueError as exc", SERVER)
        self.assertIn("422", SERVER)


if __name__ == "__main__":
    unittest.main()
