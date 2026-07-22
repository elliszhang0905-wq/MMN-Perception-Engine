import sqlite3
import unittest

from product_evaluation_catalog import init_schema, list_datasets, save_dataset, validate_dataset


def dataset(model="智己L6", version="l6-v1"):
    return {
        "datasetVersion": version,
        "config": {"model": model},
        "models": [model, "Model 3"],
        "rows": [[model, "本品", "全网", "智能化", "智能座舱"]],
        "summaryHeat": {},
        "summaryPlatformNsr": {},
        "summaryMetrics": {},
        "productEvaluationSourceModel": model,
    }


class ProductEvaluationCatalogTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        init_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_same_vehicle_is_replaced_without_crossing_scope(self):
        save_dataset(self.conn, org_id="org-a", edition="china", dataset=dataset(version="v1"), user_id="u1")
        save_dataset(self.conn, org_id="org-a", edition="china", dataset=dataset(version="v2"), user_id="u1")
        self.assertEqual(len(list_datasets(self.conn, org_id="org-a", edition="china")), 1)
        self.assertEqual(list_datasets(self.conn, org_id="org-a", edition="china")[0]["datasetVersion"], "v2")
        self.assertEqual(list_datasets(self.conn, org_id="org-b", edition="china"), [])
        self.assertEqual(list_datasets(self.conn, org_id="org-a", edition="global"), [])

    def test_empty_state_cannot_overwrite_real_data(self):
        save_dataset(self.conn, org_id="org-a", edition="china", dataset=dataset())
        empty = dataset(version="empty")
        empty["rows"] = []
        empty["importQuality"] = {"kind": "PRODUCT_EVALUATION_UNAVAILABLE"}
        with self.assertRaisesRegex(ValueError, "空状态"):
            save_dataset(self.conn, org_id="org-a", edition="china", dataset=empty)
        self.assertEqual(list_datasets(self.conn, org_id="org-a", edition="china")[0]["datasetVersion"], "l6-v1")

    def test_source_model_must_belong_to_dataset(self):
        invalid = dataset()
        invalid["productEvaluationSourceModel"] = "奥迪E7X"
        with self.assertRaisesRegex(ValueError, "源车型不在"):
            validate_dataset(invalid)

    def test_fingerprint_is_deterministic(self):
        first = save_dataset(self.conn, org_id="org-a", edition="china", dataset=dataset())
        second = save_dataset(self.conn, org_id="org-a", edition="china", dataset=dataset())
        self.assertEqual(first["fingerprint"], second["fingerprint"])


if __name__ == "__main__":
    unittest.main()
