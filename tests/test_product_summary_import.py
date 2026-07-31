import unittest

from server import build_dataset_from_summary_workbook


MODELS = ["小米YU7", "Model Y", "问界M7", "奥迪E7X", "奥迪Q6L e-tron"]


def product_summary_cells(include_attributes=True, include_platform_nsr=True):
    cells = {
        (9, 1): "数据时间段：",
        (9, 2): "2026.6.1 - 2026.6.30",
        (10, 1): "车型范围：",
        (10, 2): "、".join(MODELS),
        (11, 1): "声量",
        (11, 2): "全网",
        (11, 3): "抖音",
        (11, 4): "小红书",
        (11, 5): "微博",
        (11, 6): "bilibili",
        (11, 7): "视频号",
        (11, 8): "快手",
        (11, 9): "今日头条",
        (11, 10): "汽车垂媒",
        (11, 11): "其他",
        (11, 13): "全网",
        (11, 14): "正面",
        (11, 15): "中性",
        (11, 16): "负面",
        (11, 17): "NSR",
    }
    for offset, model in enumerate(MODELS):
        row = 12 + offset
        cells[(row, 1)] = model
        for col in range(2, 12):
            cells[(row, col)] = (offset + 1) * 100 + col
        cells[(row, 13)] = model
        cells[(row, 14)] = 0.7
        cells[(row, 15)] = 0.2
        cells[(row, 16)] = 0.1
        cells[(row, 17)] = 0.6 + offset * 0.03

    cells[(19, 1)] = "互动量"
    for col in range(2, 12):
        cells[(19, col)] = cells[(11, col)]
    for offset, model in enumerate(MODELS):
        cells[(20 + offset, 1)] = model
        for col in range(2, 12):
            cells[(20 + offset, col)] = (offset + 1) * 1000 + col

    if include_attributes:
        for start_row, source in ((11, "全网"), (29, "垂媒车主口碑"), (47, "抖音")):
            cells[(start_row, 22)] = source
            for offset, model in enumerate(MODELS):
                cells[(start_row, 23 + offset)] = model
            for label_offset, label in enumerate(("外观", "价格", "安全")):
                row = start_row + 1 + label_offset
                cells[(row, 22)] = label
                for offset in range(len(MODELS)):
                    cells[(row, 23 + offset)] = 0.8 - label_offset * 0.35 + offset * 0.01

    if include_platform_nsr:
        platform_nsr_headers = ["全网", "垂媒车主口碑", "抖音", "小红书", "微博", "bilibili", "视频号"]
        for offset, platform in enumerate(platform_nsr_headers):
            cells[(70, 13 + offset)] = platform
        for model_offset, model in enumerate(MODELS):
            row = 71 + model_offset
            cells[(row, 12)] = model
            for platform_offset in range(len(platform_nsr_headers)):
                cells[(row, 13 + platform_offset)] = 0.3 + model_offset * 0.1 + platform_offset * 0.01
    return cells


def add_attribute_block(cells, start_row, source):
    cells[(start_row, 22)] = source
    for offset, model in enumerate(MODELS):
        cells[(start_row, 23 + offset)] = model
    for label_offset, label in enumerate(("外观", "价格", "安全")):
        row = start_row + 1 + label_offset
        cells[(row, 22)] = label
        for offset in range(len(MODELS)):
            cells[(row, 23 + offset)] = 0.42 + label_offset * 0.1 + offset * 0.01
    return cells


class ProductSummaryImportTest(unittest.TestCase):
    def test_summary_import_uses_only_real_blocks_and_preserves_metadata(self):
        dataset = build_dataset_from_summary_workbook(
            product_summary_cells(),
            "AUDI E7X等5车产品评价_0710_v2.xlsx",
            {"Read Me": product_summary_cells()},
        )

        self.assertEqual(dataset["config"]["model"], "奥迪E7X")
        self.assertEqual(dataset["models"], MODELS)
        self.assertEqual(dataset["importQuality"]["timeRange"], "2026.6.1 - 2026.6.30")
        self.assertEqual(dataset["importQuality"]["metricCoverage"], {"nsr": True, "ips": False, "intent": False, "risk": False})
        self.assertEqual({row[2] for row in dataset["rows"]}, {"全网", "垂媒车主口碑", "抖音"})
        self.assertEqual({row[4] for row in dataset["rows"]}, {"外观", "价格", "安全"})
        self.assertNotIn("正面", {row[2] for row in dataset["rows"]})
        self.assertAlmostEqual(dataset["summaryMetrics"]["奥迪E7X"]["overallNsr"], 0.69)
        self.assertEqual(
            dataset["summaryPlatformNsr"]["奥迪E7X"],
            {
                "全网": 0.6,
                "垂媒车主口碑": 0.61,
                "抖音": 0.62,
                "小红书": 0.63,
                "微博": 0.64,
                "B站": 0.65,
                "视频号": 0.66,
            },
        )
        self.assertEqual(dataset["importQuality"]["platformNsrSources"], ["全网", "垂媒车主口碑", "抖音", "小红书", "微博", "B站", "视频号"])
        self.assertEqual(
            dataset["summaryHeat"]["奥迪E7X"],
            {
                "volume": 402,
                "interaction": 4002,
                "platformVolume": {
                    "抖音": 403,
                    "小红书": 404,
                    "微博": 405,
                    "B站": 406,
                    "视频号": 407,
                    "快手": 408,
                    "今日头条": 409,
                    "汽车垂媒": 410,
                    "其他": 411,
                },
                "platformInteraction": {
                    "抖音": 4003,
                    "小红书": 4004,
                    "微博": 4005,
                    "B站": 4006,
                    "视频号": 4007,
                    "快手": 4008,
                    "今日头条": 4009,
                    "汽车垂媒": 4010,
                    "其他": 4011,
                },
            },
        )
        self.assertTrue(dataset["importQuality"]["platformVolumeAvailable"])
        self.assertTrue(dataset["importQuality"]["platformInteractionAvailable"])

    def test_summary_import_exposes_any_structurally_valid_attribute_platform(self):
        cells = add_attribute_block(product_summary_cells(), 60, "微博")

        dataset = build_dataset_from_summary_workbook(cells, "AUDI E7X等5车产品评价_0710_v2.xlsx")

        self.assertEqual(
            dataset["importQuality"]["attributeNsrSources"],
            ["全网", "垂媒车主口碑", "抖音", "微博"],
        )
        self.assertIn("微博", dataset["platforms"])
        weibo_exterior = next(
            row for row in dataset["rows"] if row[0] == "奥迪E7X" and row[2] == "微博" and row[4] == "外观"
        )
        self.assertAlmostEqual(weibo_exterior[14], 0.45)

    def test_summary_import_keeps_missing_attribute_nsr_as_absent(self):
        cells = product_summary_cells()
        q6_col = 27
        for row in range(30, 33):
            cells[(row, q6_col)] = "-"

        dataset = build_dataset_from_summary_workbook(cells, "AUDI E7X等5车产品评价_0710_v2.xlsx")

        q6_vertical = [
            row for row in dataset["rows"]
            if row[0] == "奥迪Q6L e-tron" and row[2] == "垂媒车主口碑"
        ]
        self.assertEqual(q6_vertical, [])

    def test_summary_import_preserves_zero_percent_attribute_nsr(self):
        cells = product_summary_cells()
        cells[(32, 23)] = 0

        dataset = build_dataset_from_summary_workbook(cells, "AUDI E7X等5车产品评价_0710_v2.xlsx")

        xiaomi_vertical_safety = next(
            row for row in dataset["rows"]
            if row[0] == "小米YU7" and row[2] == "垂媒车主口碑" and row[4] == "安全"
        )
        self.assertEqual(xiaomi_vertical_safety[14], 0)

    def test_summary_import_does_not_mix_adjacent_nsr_blocks_into_overall_nsr(self):
        cells = product_summary_cells()
        cells[(19, 13)] = "垂媒车主口碑"
        cells[(19, 14)] = "正面"
        cells[(19, 15)] = "中性"
        cells[(19, 16)] = "负面"
        cells[(19, 17)] = "NSR"
        for offset, model in enumerate(MODELS):
            row = 20 + offset
            cells[(row, 13)] = model
            cells[(row, 14)] = 0.8
            cells[(row, 15)] = 0.1
            cells[(row, 16)] = 0.1
            cells[(row, 17)] = 0.95 - offset * 0.05

        dataset = build_dataset_from_summary_workbook(cells, "AUDI E7X等5车产品评价_0710_v2.xlsx")

        self.assertAlmostEqual(dataset["summaryMetrics"]["小米YU7"]["overallNsr"], 0.6)
        self.assertAlmostEqual(dataset["summaryMetrics"]["奥迪E7X"]["overallNsr"], 0.69)

    def test_summary_import_rejects_missing_overall_nsr_instead_of_turning_it_into_zero(self):
        cells = product_summary_cells()
        cells[(12, 17)] = "—"

        with self.assertRaisesRegex(ValueError, "完整的全网NSR"):
            build_dataset_from_summary_workbook(cells, "AUDI E7X等5车产品评价_0710_v2.xlsx")

    def test_summary_import_preserves_real_zero_overall_nsr(self):
        cells = product_summary_cells()
        cells[(12, 17)] = 0

        dataset = build_dataset_from_summary_workbook(cells, "AUDI E7X等5车产品评价_0710_v2.xlsx")

        self.assertEqual(dataset["summaryMetrics"]["小米YU7"]["overallNsr"], 0)

    def test_summary_import_accepts_overall_metrics_when_attribute_blocks_are_missing(self):
        dataset = build_dataset_from_summary_workbook(
            product_summary_cells(include_attributes=False, include_platform_nsr=False),
            "AUDI E7X.xlsx",
        )

        self.assertEqual(dataset["config"]["model"], "奥迪E7X")
        self.assertEqual(dataset["rows"], [])
        self.assertEqual(dataset["aggregatedRowCount"], 0)
        self.assertAlmostEqual(dataset["summaryMetrics"]["奥迪E7X"]["overallNsr"], 0.69)
        self.assertEqual(dataset["summaryPlatformNsr"]["奥迪E7X"], {"全网": 0.69})
        self.assertEqual(dataset["summaryHeat"]["奥迪E7X"]["volume"], 402)
        self.assertEqual(dataset["summaryHeat"]["奥迪E7X"]["interaction"], 4002)
        self.assertFalse(dataset["importQuality"]["attributeNsrAvailable"])
        self.assertEqual(dataset["importQuality"]["attributeNsrSources"], [])
        self.assertIn("源表未提供属性NSR", dataset["importQuality"]["message"])
        self.assertIn("属性机会地图保持数据缺口", dataset["sourceNote"])


if __name__ == "__main__":
    unittest.main()
