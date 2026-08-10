import sqlite3
import unittest

from lead_dashboard_catalog import (
    build_datasets_from_rows,
    extract_rows_from_sheets,
    get_dataset,
    init_schema,
    list_models,
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


def legacy_phase_matrix(phases):
    rows = [["新车上市流量表现指标统计表"]]
    rows.extend([[] for _ in range(46)])
    for index, (phase, lead_target, lead_actual, order_target, order_actual) in enumerate(phases):
        category = "分阶段转化" if index == 0 else None
        rows.extend(
            [
                [category, phase, "线索目标", lead_target],
                [None, None, "线索达成", lead_actual],
                [None, None, "订单目标", order_target],
                [None, None, "订单达成", order_actual],
            ]
        )
    return rows


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

    def test_available_models_are_listed_by_scope_and_latest_update(self):
        datasets = build_datasets_from_rows(lead_rows("车型A") + lead_rows("车型B"), "双车型.xlsx")
        save_datasets(self.conn, org_id="org-a", edition="china", datasets=datasets)
        save_datasets(
            self.conn,
            org_id="org-b",
            edition="china",
            datasets=build_datasets_from_rows(lead_rows("车型C"), "另一企业.xlsx"),
        )

        self.assertEqual(list_models(self.conn, org_id="org-a", edition="china"), ["车型A", "车型B"])
        self.assertEqual(list_models(self.conn, org_id="org-b", edition="china"), ["车型C"])
        self.assertEqual(list_models(self.conn, org_id="org-a", edition="global"), [])

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

    def test_legacy_vertical_phase_matrix_supports_0716_and_0806_continuity(self):
        versions = {
            "0716": [
                ("小订期", 225000, 183822, 10000, 9419),
                ("大定期", 230208, 218414, 6000, 6375),
                ("平销期（6.16-6.30）", 143758, 169212, 2000, 1293),
                ("平销期（7.1-7.31）", 457142.857142856, 131838, 4000, 837),
            ],
            "0806": [
                ("小订期", 225000, 183822, 10000, 9419),
                ("大定期", 230208, 218414, 6000, 6375),
                ("平销期（6.16-6.30）", 143758, 169212, 2000, 1293),
                ("平销期（7.1-7.31）", 457142.857142856, 273736, 4000, 1867),
                ("平销期（8.1-8.31）", 377143, 40440, 3300, 272),
            ],
        }

        latest_dataset = None
        for version, phases in versions.items():
            with self.subTest(version=version):
                rows = extract_rows_from_sheets(
                    {"AUDI E7X": legacy_phase_matrix(phases)},
                    model_normalizer=lambda value: value.replace("AUDI ", "奥迪"),
                )
                datasets = build_datasets_from_rows(rows, f"E7X {version}.xlsx")

                self.assertEqual(len(rows), len(phases))
                self.assertEqual(datasets[0]["model"], "奥迪E7X")
                self.assertEqual(datasets[0]["source"]["template"], "vertical_phase_matrix")
                self.assertTrue(all(item["status"] == "completed" for item in datasets[0]["phases"][:-1]))
                self.assertEqual(datasets[0]["phases"][-1]["status"], "in_progress")
                latest_dataset = datasets[0]

        latest = latest_dataset["phases"][-1]
        self.assertEqual(latest["leadActual"], 40440)
        self.assertEqual(latest["orderActual"], 272)
        self.assertEqual(latest_dataset["source"]["asOf"], "2026-08-06")
        self.assertEqual(latest_dataset["source"]["year"], 2026)

    def test_legacy_vertical_phase_matrix_rejects_incomplete_phase(self):
        rows = legacy_phase_matrix([("平销期（8.1-8.31）", 377143, 40440, 3300, None)])

        with self.assertRaisesRegex(ValueError, "平销期（8.1-8.31）.*实际订单"):
            extract_rows_from_sheets({"AUDI E7X": rows})

    def test_invalid_legacy_update_does_not_overwrite_saved_dataset(self):
        original_rows = extract_rows_from_sheets(
            {"测试车型A": legacy_phase_matrix([("第一阶段", 1000, 900, 100, 92)])}
        )
        original = build_datasets_from_rows(original_rows, "第一版.xlsx")
        save_datasets(self.conn, org_id="org-a", edition="china", datasets=original)
        invalid_rows = legacy_phase_matrix([("第二阶段", 2000, 1500, 200, None)])

        with self.assertRaisesRegex(ValueError, "第二阶段.*实际订单"):
            extract_rows_from_sheets({"测试车型A": invalid_rows})

        restored = get_dataset(self.conn, org_id="org-a", edition="china", model="测试车型A")
        self.assertEqual(restored["source"]["label"], "第一版.xlsx")
        self.assertEqual(restored["phases"][0]["leadActual"], 900)

    def test_legacy_vertical_phase_matrix_requires_model_sheet_name(self):
        rows = legacy_phase_matrix([("第一阶段", 1000, 900, 100, 92)])

        with self.assertRaisesRegex(ValueError, "无法确认车型"):
            extract_rows_from_sheets({"Sheet1": rows})

    def test_mixed_workbook_keeps_template_metadata_scoped_to_vertical_model(self):
        standard_rows = [
            ["车型", "阶段", "线索目标", "实际线索", "订单目标", "实际订单", "阶段状态"],
            ["标准车型", "第一阶段", 1000, 900, 100, 92, "进行中"],
        ]
        rows = extract_rows_from_sheets(
            {
                "标准数据": standard_rows,
                "纵向车型": legacy_phase_matrix([("第一阶段", 2000, 1800, 200, 184)]),
            }
        )
        datasets = {item["model"]: item for item in build_datasets_from_rows(rows, "混合格式.xlsx")}

        self.assertNotIn("template", datasets["标准车型"]["source"])
        self.assertEqual(datasets["纵向车型"]["source"]["template"], "vertical_phase_matrix")


if __name__ == "__main__":
    unittest.main()
