import os
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from social_trends import TikHubClient, _aggregate, _parse_import_date, apply_history, attach_competitor_rankings, collect, import_records, init_schema, latest_snapshot, normalize_item, save_snapshot


class SocialTrendsTest(unittest.TestCase):
    def test_social_assistant_aliases_and_excel_date_are_imported(self):
        result = import_records([{
            "视频ID": "7631825727737892130", "视频链接": "https://www.douyin.com/video/7631825727737892130",
            "视频描述": "第一时间带你看看奥迪E7X内饰", "点赞量": 35079, "收藏量": 846,
            "评论量": 740, "分享量": 2246, "发布时间": 46136.45887731481, "达人昵称": "秋晨同学",
        }], "奥迪E7X", ["douyin"], {"douyin": 8000}, "90d")
        self.assertEqual(result["admission"]["admittedCount"], 1)
        self.assertEqual(result["items"][0]["metrics"]["likes"], 35079)

    def test_normalizes_heat_sentiment_matrix_and_evidence(self):
        item = normalize_item("douyin", {"aweme_id": "123", "desc": "智己L6 舒适稳定，官方推荐",
            "author": {"nickname": "智己汽车官方"}, "statistics": {"digg_count": 1000, "comment_count": 100,
            "share_count": 50, "collect_count": 80, "play_count": 30000}}, "智己L6", "2026-07-11T00:00:00Z")
        self.assertEqual(item["sentiment"], "positive")
        self.assertTrue(item["matrixContent"])
        self.assertGreater(item["heat"], 0)
        self.assertTrue(item["sourceUrl"].endswith("/123"))
        self.assertEqual(len(item["evidence"]["contentHash"]), 64)

    def test_xiaohongshu_timestamp_is_preserved_as_publish_time(self):
        item = normalize_item("xiaohongshu", {
            "id": "xhs-1", "title": "上汽奥迪A5L 提车", "timestamp": 1783575238,
        }, "上汽奥迪", "2026-07-11T00:00:00Z")
        self.assertEqual(item["publishedAt"], "1783575238")

    def test_weibo_rfc2822_publish_time_is_parseable(self):
        parsed = _parse_import_date("Sat Jul 11 13:37:51 +0800 2026")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.isoformat(), "2026-07-11T13:37:51+08:00")

    def test_collect_always_applies_relevance_and_rolling_time_window(self):
        now = datetime.now(timezone.utc)
        payload = {"data": [
            {"aweme_id": "valid", "desc": "上汽奥迪 近30天内容", "create_time": int((now - timedelta(days=2)).timestamp())},
            {"aweme_id": "old", "desc": "上汽奥迪 过期内容", "create_time": int((now - timedelta(days=31)).timestamp())},
            {"aweme_id": "missing", "desc": "上汽奥迪 时间缺失"},
            {"aweme_id": "irrelevant", "desc": "其他品牌内容", "create_time": int((now - timedelta(days=1)).timestamp())},
        ]}
        with patch.object(TikHubClient, "search", return_value=(payload, {"endpoint": "test", "status": 200})):
            result = collect("上汽奥迪", platforms=["douyin"], time_range="30d", include_enrichment=False)
        self.assertEqual([item["platformItemId"] for item in result["items"]], ["valid"])
        self.assertEqual(result["admission"]["rejectedReasons"], {
            "model_not_relevant": 1, "outside_time_range": 1, "publish_time_unverified": 1,
        })

    def test_collect_rejects_future_publish_time(self):
        future = int((datetime.now(timezone.utc) + timedelta(days=2)).timestamp())
        payload = {"data": [{"aweme_id": "future", "desc": "上汽奥迪 未来内容", "create_time": future}]}
        with patch.object(TikHubClient, "search", return_value=(payload, {"endpoint": "test", "status": 200})):
            result = collect("上汽奥迪", platforms=["douyin"], time_range="30d", include_enrichment=False)
        self.assertEqual(result["items"], [])
        self.assertEqual(result["admission"]["rejectedReasons"]["outside_time_range"], 1)

    def test_weibo_rfc2822_publish_time_is_bucketed_in_timeline(self):
        item = normalize_item("weibo", {
            "mid": "w-time", "text": "上汽奥迪 权益", "created_at": "Sat Jul 11 13:37:51 +0800 2026",
        }, "上汽奥迪", "2026-07-11T00:00:00Z")
        result = _aggregate([item], "上汽奥迪", [], [], selected_platforms=["weibo"])
        self.assertEqual(result["timeline"][0]["date"], "2026-07-11")
        self.assertEqual(result["timelineUndated"]["contentCount"], 0)

    def test_aggregate_deduplicates_and_exposes_low_confidence(self):
        item = normalize_item("weibo", {"mid": "a", "text": "某车型问题和投诉", "comments_count": 2}, "某车型", "now")
        result = _aggregate([item, item], "某车型", [], [])
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["confidenceLabel"], "低")
        self.assertEqual(result["statusHint"], "未形成高热度")
        self.assertTrue(result["qa"]["evidenceTraceable"])

    def test_snapshot_round_trip_is_scoped(self):
        conn = sqlite3.connect(":memory:"); conn.row_factory = sqlite3.Row; init_schema(conn)
        result = _aggregate([], "车型A", [], [])
        saved = save_snapshot(conn, result, "org-a", "china", {"platforms": ["douyin"]})
        loaded = latest_snapshot(conn, "车型A", "org-a", "china")
        self.assertEqual(loaded["snapshot"]["id"], saved["id"])
        self.assertIsNone(latest_snapshot(conn, "车型A", "org-b", "china"))

    def test_api_key_is_only_read_from_server_environment(self):
        with patch.dict(os.environ, {"TIKHUB_API_KEY": "server-secret"}):
            self.assertEqual(TikHubClient().key, "server-secret")

    def test_weibo_html_is_cleaned_before_hot_word_analysis(self):
        raw = '<a href="https://weibo.com/x" data-hide=""><span class="surl-text">#奥迪E7X#</span></a> 豪华纯电设计很优秀<br>值得推荐'
        item = normalize_item("weibo", {"mid": "html-1", "text": raw}, "奥迪E7X", "now")
        result = _aggregate([item], "奥迪E7X", [], [])
        self.assertNotIn("<", item["text"])
        self.assertIn("奥迪E7X", item["text"])
        self.assertFalse({"span", "class", "https", "href", "data-hide", "surl-text"} & {x["word"] for x in result["hotWords"]})

    def test_selected_competitors_are_ranked_by_real_positive_heat(self):
        own = _aggregate([], "奥迪E7X", [], [])
        model_y = _aggregate([normalize_item("weibo", {"mid": "m1", "text": "Model Y 优秀推荐", "attitudes_count": 200}, "Model Y", "now")], "Model Y", [], [])
        es6 = _aggregate([normalize_item("weibo", {"mid": "m2", "text": "蔚来ES6 推荐", "attitudes_count": 20}, "蔚来ES6", "now")], "蔚来ES6", [], [])
        result = attach_competitor_rankings(own, [model_y, es6])
        self.assertEqual([x["model"] for x in result["positiveCompetitorsTop5"]], ["Model Y", "蔚来ES6"])
        self.assertGreater(result["positiveCompetitorsTop5"][0]["positiveHeat"], result["positiveCompetitorsTop5"][1]["positiveHeat"])
        self.assertEqual([x["role"] for x in result["modelComparisons"]], ["own", "competitor", "competitor"])
        self.assertEqual(result["modelComparisons"][1]["model"], "Model Y")
        self.assertTrue(result["comparisonEvidence"])

    def test_dashboard_aggregation_includes_platform_creator_risk_and_comments(self):
        positive = normalize_item("douyin", {"aweme_id": "p1", "desc": "车型A 舒适推荐", "author": {"nickname": "车型A官方"}, "digg_count": 100}, "车型A", "2026-07-11T00:00:00Z")
        negative = normalize_item("weibo", {"mid": "n1", "text": "车型A 异响问题投诉", "user": {"name": "用户甲"}, "attitudes_count": 50}, "车型A", "2026-07-11T00:00:00Z")
        comments = [{"text": "确实有异响问题", "sentiment": "negative", "platform": "weibo"}]
        result = _aggregate([positive, negative], "车型A", [], [], comments, [{"platform": "weibo", "items": ["汽车热榜"]}])
        self.assertAlmostEqual(sum(x["share"] for x in result["platformShare"]), 100, places=1)
        self.assertTrue(result["creatorRanking"][0]["author"])
        self.assertTrue(result["riskTopics"])
        self.assertEqual(result["commentInsights"]["negative"], 1)
        self.assertEqual(result["hotLists"][0]["items"], ["汽车热榜"])

    def test_history_comparison_exposes_deltas(self):
        current = _aggregate([normalize_item("weibo", {"mid": "a", "text": "车型A 推荐", "attitudes_count": 10}, "车型A", "now")], "车型A", [], [])
        previous = _aggregate([], "车型A", [], [])
        previous["snapshot"] = {"id": "old"}
        result = apply_history(current, previous)
        self.assertTrue(result["historyComparison"]["available"])
        self.assertEqual(result["historyComparison"]["delta"]["contentCount"], 1)

    def test_unselected_platforms_are_not_returned_to_dashboard(self):
        item = normalize_item("douyin", {"aweme_id": "d1", "desc": "车型A 推荐", "digg_count": 10}, "车型A", "now")
        result = _aggregate([item], "车型A", [], [], selected_platforms=["douyin", "xiaohongshu"])
        self.assertEqual([x["platform"] for x in result["platforms"]], ["douyin", "xiaohongshu"])
        self.assertNotIn("weibo", [x["platform"] for x in result["platformShare"]])

    def test_missing_publish_dates_are_not_misreported_as_collection_day(self):
        item = normalize_item("douyin", {"aweme_id": "d2", "desc": "车型A 推荐", "digg_count": 10}, "车型A", "2026-07-11T00:00:00Z")
        result = _aggregate([item], "车型A", [], [], selected_platforms=["douyin"])
        self.assertEqual(result["timeline"], [])
        self.assertEqual(result["timelineUndated"]["contentCount"], 1)
        self.assertEqual(result["timelineUndated"]["platforms"][0]["platform"], "douyin")

    def test_social_assistant_import_applies_relevance_time_and_threshold_rules(self):
        rows = [
            {"平台": "抖音", "作品ID": "d1", "作品标题": "奥迪E7X 深度体验", "发布时间": "2026-07-10 12:00:00", "点赞数": "9000", "评论数": "100", "作品链接": "https://www.douyin.com/video/d1"},
            {"平台": "抖音", "作品ID": "d2", "作品标题": "奥迪E7X 到店", "发布时间": "2026-07-10 13:00:00", "点赞数": "7999"},
            {"平台": "小红书", "作品ID": "x1", "作品标题": "奥迪E7X 试驾", "发布时间": "2026-07-10 14:00:00", "点赞数": "600", "评论数": "30"},
            {"平台": "微博", "作品ID": "w1", "作品标题": "其他车型", "发布时间": "2026-07-10 14:00:00", "点赞数": "900"},
        ]
        result = import_records(rows, "奥迪E7X", ["douyin", "xiaohongshu", "weibo"], time_range="7d", filename="assistant.xlsx")
        self.assertEqual([x["platformItemId"] for x in result["contentRanking"]], ["d1", "x1"])
        self.assertEqual(result["admission"]["admittedCount"], 2)
        self.assertEqual(result["admission"]["rejectedReasons"]["below_like_threshold"], 1)
        self.assertEqual(result["admission"]["rejectedReasons"]["model_not_relevant"], 1)
        self.assertEqual(result["items"][0]["evidence"]["source"], "社媒助手导入")


if __name__ == "__main__":
    unittest.main()
