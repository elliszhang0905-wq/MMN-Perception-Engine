import xml.etree.ElementTree as ET
import unittest
from unittest.mock import patch

import server


class DataReaderInvariantTest(unittest.TestCase):
    def test_inline_rich_text_cell_keeps_all_runs(self):
        cell = ET.fromstring(
            '<c xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" t="inlineStr">'
            '<is><r><t>奥迪</t></r><r><t>E7X</t></r></is></c>'
        )

        self.assertEqual(server.cell_value(cell, []), "奥迪E7X")

    def test_nullable_share_distinguishes_zero_missing_and_invalid_text(self):
        self.assertEqual(server.share_or_none(0), 0)
        self.assertEqual(server.share_or_none("0%"), 0)
        self.assertEqual(server.share_or_none("-38%"), -0.38)
        self.assertIsNone(server.share_or_none(None))
        self.assertIsNone(server.share_or_none("—"))
        self.assertIsNone(server.share_or_none("数据量级过小"))
        self.assertEqual(server.share_or_none(-38), -0.38)

    def test_number_parser_supports_export_abbreviations(self):
        self.assertEqual(server.number_or_none("1.2万"), 12000)
        self.assertEqual(server.number_or_none("3.5w"), 35000)
        self.assertEqual(server.number_or_none("2k"), 2000)
        self.assertEqual(server.number_or_none("1e3"), 1000)

    def test_excel_serial_date_is_rendered_as_datetime(self):
        self.assertEqual(server.excel_datetime_text(46136.45887731481), "2026-04-24 11:00:47")
        self.assertEqual(server.excel_datetime_text("2026-07-12"), "2026-07-12")

    def test_vertical_item_preserves_real_zero_share(self):
        items = []
        server.add_vertical_item(
            items,
            filename="fixture.xlsx",
            platform="汽车之家",
            sheet="7.2-7.8",
            period="7.2-7.8",
            own="奥迪E7X",
            comp="小米YU7",
            pos=1,
            neg=2,
            share=0,
        )

        self.assertEqual(items[0]["share"], 0)

    def test_yearless_vertical_period_uses_reference_year_instead_of_2026_constant(self):
        self.assertEqual(server.period_order("7.2-7.8", reference_year=2027), "2027-07-08")
        self.assertEqual(server.period_from_text("7月12日", reference_year=2028), "2028-07-12")

    def test_vertical_item_trims_sheet_name(self):
        items = []
        server.add_vertical_item(
            items,
            filename="fixture.xlsx",
            platform="汽车之家",
            sheet="  7.2-7.8  ",
            period="7.2-7.8",
            own="奥迪E7X",
            comp="小米YU7",
            pos=1,
        )

        self.assertEqual(items[0]["sheet"], "7.2-7.8")

    def test_autohome_week_sheet_is_not_read_twice_by_generic_parser(self):
        cells = {
            (1, 1): "本品车系名称",
            (1, 2): "正向排名",
            (1, 3): "竞品车系名称",
            (1, 4): "车系对比次数占比",
            (1, 5): "反向排名",
            (2, 1): "奥迪E7X",
            (2, 2): 1,
            (2, 3): "小米YU7",
            (2, 4): 0.0,
            (2, 5): 2,
        }
        with patch.object(server, "read_xlsx_cells", return_value={"7.2-7.8": cells}):
            dataset = server.build_vertical_media_dataset_from_workbook(b"fixture", "汽车之家周对比.xlsx")

        self.assertEqual(dataset["count"], 1)
        self.assertEqual(dataset["periods"], ["7.2-7.8"])
        self.assertEqual(dataset["items"][0]["share"], 0)

    def test_video_export_without_title_uses_traceable_social_text_fallback(self):
        cells = {
            (1, 1): "抖音视频导出",
            (2, 1): "视频ID",
            (2, 2): "视频链接",
            (2, 3): "大家都在搜",
            (2, 4): "所属合集",
            (2, 5): "视频话题",
            (2, 6): "发布时间",
            (2, 7): "点赞数",
            (2, 8): "评论数",
            (3, 1): "7390001",
            (3, 2): "https://www.douyin.com/video/7390001",
            (3, 3): "奥迪E7X底盘舒适吗",
            (3, 4): "E7X实测",
            (3, 5): "#奥迪E7X #底盘",
            (3, 6): 46136.45887731481,
            (3, 7): 12000,
            (3, 8): 320,
        }
        with patch.object(server, "read_xlsx_cells", return_value={"视频数据": cells}):
            dataset = server.build_video_dataset_from_workbook(b"fixture", "【社媒助手】视频数据.xlsx")

        self.assertEqual(dataset["count"], 1)
        item = dataset["items"][0]
        self.assertEqual(item["title"], "奥迪E7X底盘舒适吗")
        self.assertEqual(item["titleSource"], "大家都在搜")
        self.assertEqual(item["date"], "2026-04-24 11:00:47")
        self.assertEqual((item["likes"], item["comments"]), (12000, 320))

    def test_xiaohongshu_creator_export_uses_nickname_uid_and_profile_fields(self):
        cells = {
            (1, 1): "博主ID",
            (1, 2): "博主昵称",
            (1, 3): "粉丝数",
            (1, 4): "博主链接",
            (1, 5): "博主简介",
            (1, 6): "IP地址",
            (2, 1): "575412345678901234",
            (2, 2): "冷静的饺子",
            (2, 3): 22697,
            (2, 4): "https://www.xiaohongshu.com/user/profile/5754",
            (2, 5): "分享日常用车与城市生活",
            (2, 6): "上海",
        }
        with patch.object(server, "read_xlsx_cells", return_value={"博主数据": cells}):
            dataset = server.build_creator_dataset_from_workbook(
                b"fixture", "【社媒助手】冷静的饺子.xlsx", "xiaohongshu"
            )

        self.assertEqual(dataset["count"], 1)
        creator = dataset["creators"][0]
        self.assertEqual(creator["name"], "冷静的饺子")
        self.assertEqual(creator["uid"], "575412345678901234")
        self.assertEqual(creator["fans"], 22697)
        self.assertEqual(creator["profileUrl"], "https://www.xiaohongshu.com/user/profile/5754")
        self.assertEqual(creator["city"], "上海")
        self.assertEqual(creator["platform"], "xiaohongshu")

    def test_legacy_product_workbook_cannot_succeed_with_zero_business_rows(self):
        cells = {
            (10, 1): "数据时间段：",
            (11, 1): "数据范围：",
        }
        with patch.object(server, "read_xlsx_cells", return_value={"数据整理": cells}):
            with self.assertRaisesRegex(ValueError, "有效车型属性数据"):
                server.build_dataset_from_workbook(b"fixture", "旧格式产品评价.xlsx")


if __name__ == "__main__":
    unittest.main()
