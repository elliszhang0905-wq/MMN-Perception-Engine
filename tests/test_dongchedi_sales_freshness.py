import json
import unittest
from unittest.mock import patch

import server


def _write_feed(path, month, *, crawl_at):
    path.write_text(json.dumps({
        "ok": True,
        "crawl_at": crawl_at,
        "records": [{
            "segment": "微型车",
            "month": month,
            "items": [{"rank": 1, "series_name": "测试车型", "sales": 100}],
        }],
    }, ensure_ascii=False), encoding="utf-8")


class DongchediSalesFreshnessTest(unittest.TestCase):
    def setUp(self):
        server.SALES_CACHE.clear()

    def tearDown(self):
        server.SALES_CACHE.clear()

    def test_filters_mixed_history_to_latest_valid_month(self):
        payload = {
            "items": [
                {"period_start": "2026-05-01", "rank": 1, "series_name": "五月车型"},
                {"period_start": "2026-06-01", "rank": 1, "series_name": "六月车型"},
                {"period_start": "2026-99-01", "rank": 1, "series_name": "无效月份"},
            ],
            "records": [
                {"month": "2026年05月", "segment": "五月榜"},
                {"month": "2026年06月", "segment": "六月榜"},
            ],
        }

        rows = server.dongchedi_latest_period_items(payload)

        self.assertEqual(server.dongchedi_sales_period(payload), "2026-06")
        self.assertEqual([row["series_name"] for row in rows], ["六月车型"])
        self.assertEqual(
            [record["segment"] for record in server.dongchedi_latest_period_records(payload)],
            ["六月榜"],
        )

    def test_selects_newest_sales_period_instead_of_first_existing_file(self):
        with self.subTest("newer period wins"):
            from tempfile import TemporaryDirectory
            from pathlib import Path
            with TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                stale = tmp_path / "stale.json"
                fresh = tmp_path / "fresh.json"
                _write_feed(stale, "2026年05月", crawl_at="2026-06-25T01:00:00")
                _write_feed(fresh, "2026年06月", crawl_at="2026-07-13T09:00:00")

                selected = server.latest_dongchedi_sales_source([stale, fresh])

                self.assertIsNotNone(selected)
                self.assertEqual(selected[0], fresh)
                self.assertEqual(selected[1]["records"][0]["month"], "2026年06月")

    def test_sales_source_signature_changes_when_file_is_replaced(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as tmp:
            feed = Path(tmp) / "latest.json"
            _write_feed(feed, "2026年05月", crawl_at="2026-06-25T01:00:00")
            first = server.latest_dongchedi_sales_source([feed])

            _write_feed(feed, "2026年06月", crawl_at="2026-07-13T09:00:00")
            second = server.latest_dongchedi_sales_source([feed])

            self.assertIsNotNone(first)
            self.assertIsNotNone(second)
            self.assertNotEqual(first[2], second[2])

    def test_formatted_counts_do_not_invalidate_local_feed_and_duplicate_segments_are_removed(self):
        payload = {
            "crawl_at": "2026-07-13T09:00:00",
            "items": [{
                "period_start": "2026-06-01", "rank_type": "series", "rank": 1,
                "series_name": "安全车型", "sales_volume": "12,345", "brand_name": "测试品牌",
            }],
            "records": [{
                "month": "2026年06月", "segment": "全国零售榜",
                "items": [{"rank": 1, "series_name": "重复车型", "sales": "9,999"}],
            }],
        }
        with patch.object(server, "latest_dongchedi_sales_source", return_value=(None, payload, "signature")):
            result = server.dongchedi_sales_payload()
        self.assertEqual(result["status"], "local")
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["top10Total"], 12345)
        self.assertEqual(result["items"][0]["top3"][0]["sales"], 12345)

    def test_sales_count_supports_common_crawler_number_formats(self):
        self.assertEqual(server.dongchedi_sales_count("1.2万"), 12000)
        self.assertEqual(server.dongchedi_sales_count("3,456"), 3456)
        self.assertEqual(server.dongchedi_sales_count("bad"), 0)
