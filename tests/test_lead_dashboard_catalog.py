import sqlite3
import unittest

from lead_dashboard_catalog import (
    build_datasets_from_rows,
    extract_rows_from_sheets,
    get_dataset,
    init_schema,
    save_datasets,
)


def lead_rows(model="测试车型A"):
    return [
        {
            "车型": model,
            "阶段": "预售",
            "线索目标": 1000,
            "实际线索": 900,
            "订单目标": 100,
            "实际订单": 92,
            "阶段状态": "已完成",
        },
        {
            "车型": model,
            "阶段": "上市首月",
            "线索目标": 2000,
            "实际线索": 2300,
            "订单目标": 200,
            "实际订单": 110,
            "阶段状态": "进行中",
        },
    ]


class LeadDashboardCatalogTest(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        init_schema(self.conn)

    def tearDown(self):
        self.conn.close()

    def test_any_model_rows_are_normalized_and_rates_are_derived(self):
        datasets = build_datasets_from_rows(lead_rows(), "测试线索.csv")
        self.assertEqual([item["model"] for item in datasets], ["测试车型A"])
        self.assertAlmostEqual(datasets[0]["phases"][1]["leadRate"], 1.15)
        self.assertAlmostEqual(datasets[0]["phases"][1]["orderRate"], 0.55)
        self.assertEqual(datasets[0]["phases"][1]["status"], "in_progress")

    def test_multiple_models_are_saved_and_read_in_isolated_scopes(self):
        rows = lead_rows("车型A") + lead_rows("车型B")
        datasets = build_datasets_from_rows(rows, "双车型.xlsx")
        save_datasets(self.conn, org_id="org-a", edition="china", datasets=datasets, user_id="u1")

        self.assertEqual(get_dataset(self.conn, org_id="org-a", edition="china", model="车型A")["model"], "车型A")
        self.assertEqual(get_dataset(self.conn, org_id="org-a", edition="china", model="车型B")["model"], "车型B")
        self.assertIsNone(get_dataset(self.conn, org_id="org-b", edition="china", model="车型A"))
        self.assertIsNone(get_dataset(self.conn, org_id="org-a", edition="global", model="车型A"))

    def test_invalid_import_does_not_overwrite_existing_model(self):
        original = build_datasets_from_rows(lead_rows(), "第一版.csv")
        save_datasets(self.conn, org_id="org-a", edition="china", datasets=original)
        invalid = lead_rows()
        invalid[0]["线索目标"] = 0

        with self.assertRaisesRegex(ValueError, "线索目标"):
            build_datasets_from_rows(invalid, "错误版.csv")

        restored = get_dataset(self.conn, org_id="org-a", edition="china", model="测试车型A")
        self.assertEqual(restored["source"]["label"], "第一版.csv")
        self.assertEqual(restored["phases"][0]["leadTarget"], 1000)

    def test_duplicate_phase_and_multiple_current_phases_are_rejected(self):
        duplicate = lead_rows()
        duplicate.append(dict(duplicate[0]))
        with self.assertRaisesRegex(ValueError, "阶段重复"):
            build_datasets_from_rows(duplicate, "重复.csv")

        multiple_current = lead_rows()
        multiple_current[0]["阶段状态"] = "进行中"
        with self.assertRaisesRegex(ValueError, "只能有一个进行中"):
            build_datasets_from_rows(multiple_current, "多当前.csv")

    def test_missing_required_columns_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "缺少必需字段"):
            build_datasets_from_rows([{"车型": "车型A", "阶段": "预售"}], "缺列.csv")

    def test_xlsx_title_rows_before_header_are_supported(self):
        sheets = {
            "线索看板": [
                ["2026年车型线索阶段复盘"],
                ["说明：阶段状态只能填写已完成或进行中"],
                [],
                ["车型", "阶段", "线索目标", "实际线索", "订单目标", "实际订单", "阶段状态"],
                ["车型C", "预售", 1200, 1080, 120, 105, "已完成"],
                ["车型C", "上市首月", 2400, 2700, 240, 130, "进行中"],
            ]
        }

        rows = extract_rows_from_sheets(sheets)
        datasets = build_datasets_from_rows(rows, "含标题行.xlsx")

        self.assertEqual(len(rows), 2)
        self.assertEqual(datasets[0]["model"], "车型C")
        self.assertAlmostEqual(datasets[0]["phases"][1]["leadRate"], 1.125)


if __name__ == "__main__":
    unittest.main()
