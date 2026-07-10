import unittest

from server import build_dataset_from_summary_workbook


MODELS = ["小米YU7", "Model Y", "问界M7", "奥迪E7X", "奥迪Q6L e-tron"]


def product_summary_cells(include_attributes=True):
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
    for offset, model in enumerate(MODELS):
        cells[(20 + offset, 1)] = model
        cells[(20 + offset, 2)] = (offset + 1) * 1000

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
        self.assertEqual(dataset["summaryHeat"]["奥迪E7X"], {"volume": 402, "interaction": 4000})

    def test_summary_import_rejects_when_attribute_blocks_are_missing(self):
        with self.assertRaisesRegex(ValueError, "属性NSR区块"):
            build_dataset_from_summary_workbook(product_summary_cells(include_attributes=False), "AUDI E7X.xlsx")


if __name__ == "__main__":
    unittest.main()
