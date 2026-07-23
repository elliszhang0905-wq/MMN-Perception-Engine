import json
import os
import sqlite3
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from social_trends import TikHubClient, _aggregate, _parse_import_date, apply_history, attach_competitor_rankings, collect, douyin_next_cursor, douyin_pagination_state, ensure_tikhub_success, import_records, init_schema, latest_snapshot, normalize_item, passenger_vehicle_scope_exclusion_reason, sanitize_competitor_models, save_snapshot, vehicle_identity_key, vehicle_search_aliases


class SocialTrendsTest(unittest.TestCase):
    def test_vehicle_search_aliases_cover_chinese_english_brand_and_short_model(self):
        self.assertEqual(vehicle_search_aliases("奥迪E7X"), ["奥迪E7X", "AUDI E7X", "E7X"])

    def test_vehicle_search_aliases_cover_reviewed_chinese_electric_glc_wording(self):
        self.assertEqual(vehicle_search_aliases("奔驰GLC EV"), [
            "奔驰GLC EV",
            "奔驰纯电GLC",
            "全新奔驰纯电GLC",
            "奔驰全新纯电GLC",
            "奔驰GLC纯电",
            "纯电GLC",
            "Mercedes-Benz GLC EV",
            "GLC EV",
            "GLCEV",
        ])

    def test_vehicle_identity_normalization_excludes_own_and_duplicate_competitors(self):
        self.assertEqual(vehicle_identity_key(" 奥迪 E7x "), vehicle_identity_key("奥迪E7X"))
        self.assertEqual(
            sanitize_competitor_models("奥迪 E7X", ["奥迪E7X", " 奔驰GLC EV ", "奔驰GLC  EV", "问界M7", "问界M7"]),
            ["奔驰GLC EV", "问界M7"],
        )

    def test_social_assistant_aliases_and_excel_date_are_imported(self):
        result = import_records([{
            "视频ID": "7631825727737892130", "视频链接": "https://www.douyin.com/video/7631825727737892130",
            "视频描述": "第一时间带你看看奥迪E7X内饰", "点赞量": 35079, "收藏量": 846,
            "评论量": 740, "分享量": 2246, "发布时间": 46136.45887731481, "达人昵称": "秋晨同学",
        }], "奥迪E7X", ["douyin"], {"douyin": 8000}, "custom", "2026-04-24", "2026-04-24")
        self.assertEqual(result["admission"]["admittedCount"], 1)
        self.assertEqual(result["items"][0]["metrics"]["likes"], 35079)

    def test_normalizes_heat_sentiment_matrix_and_evidence(self):
        item = normalize_item("douyin", {"aweme_id": "123", "desc": "智己L6 舒适稳定，官方推荐",
            "author": {"nickname": "智己汽车官方"}, "statistics": {"digg_count": 1000, "comment_count": 100,
            "share_count": 50, "collect_count": 80, "play_count": 30000},
            "video": {"cover": {"url_list": ["https://p3.example.com/cover.jpeg"]},
                      "dynamic_cover": {"url_list": ["https://p3.example.com/cover.webp"]}},
            "share_info": {"share_url": "https://www.douyin.com/video/123"}}, "智己L6", "2026-07-11T00:00:00Z")
        self.assertEqual(item["sentiment"], "positive")
        self.assertTrue(item["matrixContent"])
        self.assertGreater(item["heat"], 0)
        self.assertTrue(item["sourceUrl"].endswith("/123"))
        self.assertEqual(item["coverUrl"], "https://p3.example.com/cover.jpeg")
        self.assertEqual(item["dynamicCoverUrl"], "https://p3.example.com/cover.webp")
        self.assertEqual(len(item["evidence"]["contentHash"]), 64)

    def test_normalizes_title_description_hashtags_and_match_fields(self):
        item = normalize_item("douyin", {
            "aweme_id": "structured-1", "title": "AUDI E7X 海外首秀",
            "desc": "奥迪E7X 设计解析 #E7X# #奥迪#",
            "cha_list": [{"cha_name": "纯电SUV"}],
        }, "奥迪E7X", "now")
        self.assertEqual(item["title"], "AUDI E7X 海外首秀")
        self.assertIn("奥迪E7X", item["description"])
        self.assertEqual(set(item["hashtags"]), {"E7X", "奥迪", "纯电SUV"})

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

    def test_collect_accepts_reviewed_electric_glc_wording_without_absorbing_fuel_glc(self):
        now = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
        relevant_titles = [
            "全新纯电GLC依然很奔驰 #奔驰纯电GLC",
            "纯电GLC：奔驰电车这次终于行了吗",
            "奔驰纯电GLC到底值不值 #奔驰GLC纯电",
            "纯电GLC再交付，三电续航扎实",
            "全新奔驰纯电GLC现车到店",
            "奔驰认真了，纯电GLC惊喜真不少",
            "奔驰全新纯电GLC上市发售",
            "奔驰纯电GLC外观展示",
            "首台奔驰纯电GLC交付 #奔驰glc纯电",
            "全新奔驰纯电GLC三电硬核答疑",
            "实测分享，带你了解奔驰纯电GLC优缺点",
        ]
        payload = {"data": [
            *[
                {"aweme_id": f"ev-{index}", "desc": title, "create_time": now}
                for index, title in enumerate(relevant_titles, 1)
            ],
            {"aweme_id": "fuel-1", "desc": "奔驰GLC燃油版长测", "create_time": now},
            {"aweme_id": "brand-only", "desc": "奔驰纯电旗舰车型发布", "create_time": now},
        ]}
        with patch.object(TikHubClient, "search", return_value=(payload, {"endpoint": "test", "status": 200})):
            result = collect("奔驰GLC EV", platforms=["douyin"], time_range="7d", include_enrichment=False)
        self.assertEqual(
            {item["platformItemId"] for item in result["items"]},
            {f"ev-{index}" for index in range(1, 12)},
        )
        self.assertEqual(result["admission"]["rejectedReasons"], {"model_not_relevant": 2})
        self.assertEqual(result["collectionStatus"]["aliasCoverage"]["status"], "verified")
        self.assertTrue(all(item["evidence"]["relevance"]["matched"] for item in result["items"]))

    def test_collection_is_partial_when_ev_wording_has_no_reviewed_alias_coverage(self):
        with patch.object(TikHubClient, "search", return_value=({"data": []}, {"endpoint": "test", "status": 200})):
            result = collect("示例X EV", platforms=["douyin"], time_range="7d", include_enrichment=False)
        self.assertEqual(result["collectionStatus"]["status"], "partial")
        self.assertEqual(result["collectionStatus"]["aliasCoverage"]["status"], "partial")
        self.assertIn("中文表达", result["collectionStatus"]["reason"])

    def test_collect_rejects_future_publish_time(self):
        future = int((datetime.now(timezone.utc) + timedelta(days=2)).timestamp())
        payload = {"data": [{"aweme_id": "future", "desc": "上汽奥迪 未来内容", "create_time": future}]}
        with patch.object(TikHubClient, "search", return_value=(payload, {"endpoint": "test", "status": 200})):
            result = collect("上汽奥迪", platforms=["douyin"], time_range="30d", include_enrichment=False)
        self.assertEqual(result["items"], [])
        self.assertEqual(result["admission"]["rejectedReasons"]["outside_time_range"], 1)

    def test_collect_honors_custom_dates_after_broad_tikhub_search(self):
        now = datetime.now(timezone.utc)
        payload = {"data": [
            {"aweme_id": "in-window", "desc": "车型A 自定义窗口内容", "create_time": int((now - timedelta(days=4)).timestamp())},
            {"aweme_id": "out-window", "desc": "车型A 窗口外内容", "create_time": int((now - timedelta(days=1)).timestamp())},
        ]}
        search_ranges = []
        def search(platform, keyword, page, count, time_range, cursor, search_context=None):
            search_ranges.append(time_range)
            return payload, {"endpoint": "test", "status": 200}
        with patch.object(TikHubClient, "search", side_effect=search):
            result = collect("车型A", platforms=["douyin"], time_range="custom",
                             start_date=(now - timedelta(days=5)).date().isoformat(),
                             end_date=(now - timedelta(days=3)).date().isoformat(), include_enrichment=False)
        self.assertEqual([item["platformItemId"] for item in result["items"]], ["in-window"])
        self.assertEqual(search_ranges, ["90d"])
        self.assertTrue(result["admission"]["dateWindow"]["endExclusive"])
        self.assertEqual(result["admission"]["rejectedReasons"]["outside_time_range"], 1)

    def test_custom_import_date_includes_the_entire_end_day(self):
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()
        result = import_records([{
            "平台": "微博", "作品ID": "same-day", "作品标题": "车型A 当天内容",
            "发布时间": f"{today} 18:00:00", "点赞数": 600,
        }], "车型A", ["weibo"], time_range="custom", start_date=today, end_date=today)
        self.assertEqual(result["admission"]["admittedCount"], 1)
        self.assertTrue(result["admission"]["dateWindow"]["endExclusive"])

    def test_commercial_vehicle_entity_is_excluded_from_passenger_vehicle_scope(self):
        truck_text = "第六代主动制动辅助系统增强版 #梅赛德斯奔驰卡车##奔驰卡车##ABA6Plus#"
        self.assertEqual(passenger_vehicle_scope_exclusion_reason(truck_text), "commercial_vehicle_entity")
        self.assertEqual(passenger_vehicle_scope_exclusion_reason("全新奔驰纯电GLC正式上市"), "")
        now = datetime.now(timezone.utc).isoformat()
        result = import_records([{
            "平台": "微博", "作品ID": "truck-1", "作品标题": f"奔驰 {truck_text}",
            "发布时间": now, "点赞数": 900, "作品链接": "https://weibo.com/detail/truck-1",
        }], "奔驰", ["weibo"], time_range="7d")
        self.assertEqual(result["items"], [])
        self.assertEqual(result["admission"]["rejectedReasons"], {"commercial_vehicle_entity": 1})

    def test_snapshot_write_fails_closed_for_commercial_vehicle_content(self):
        conn = sqlite3.connect(":memory:"); init_schema(conn)
        result = _aggregate([normalize_item("weibo", {
            "mid": "truck-2", "text": "奔驰卡车 ABA6Plus 主动制动系统", "attitudes_count": 900,
        }, "奔驰", datetime.now(timezone.utc).isoformat())], "奔驰", [], [])
        with self.assertRaisesRegex(ValueError, "商用车实体内容"):
            save_snapshot(conn, result)

    def test_collection_progress_reports_real_completed_stages(self):
        now = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
        payload = {"data": [{"aweme_id": "p1", "desc": "车型A 推荐", "create_time": now}]}
        updates = []
        with patch.object(TikHubClient, "search", return_value=(payload, {"endpoint": "test", "status": 200})):
            collect("车型A", platforms=["douyin"], include_enrichment=False,
                    progress_callback=lambda stage, progress, message: updates.append((stage, progress, message)))
        self.assertEqual([progress for _, progress, _ in updates], [33, 67, 100])
        self.assertEqual(updates[-1][0], "aggregate")

    def test_douyin_collection_uses_response_cursor_instead_of_an_offset(self):
        payloads = [
            {"data": {"business_data": [{"data": {"has_more": 1, "cursor": 8}}]}},
            {"data": {"business_data": [{"data": {"has_more": 0, "cursor": 16}}]}},
        ]
        calls = []
        def search(platform, keyword, page, count, time_range, cursor, search_context=None):
            calls.append((page, cursor))
            return payloads[len(calls) - 1], {"endpoint": "test", "status": 200}
        with patch.object(TikHubClient, "search", side_effect=search):
            collect("车型A", platforms=["douyin"], pages=2, include_enrichment=False)
        self.assertEqual(calls, [(1, ""), (2, "8")])
        self.assertEqual(douyin_next_cursor(payloads[0]), "8")
        self.assertEqual(douyin_next_cursor(payloads[1]), "")

    def test_douyin_exhaustive_collection_preserves_search_context_and_deduplicates_aliases(self):
        now = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
        calls = []
        def search(platform, alias, page, count, time_range, cursor, search_context=None):
            calls.append((alias, page, cursor, dict(search_context or {})))
            if page == 1:
                return {"data": {"business_data": [{"data": {
                    "has_more": 1, "cursor": 8, "search_id": f"sid-{alias}", "backtrace": "trace-1",
                    "aweme_id": "same", "desc": "奥迪E7X 普通体验", "create_time": now,
                }}]}}, {"endpoint": "test", "status": 200}
            return {"data": {"business_data": [{"data": {
                "has_more": 0, "cursor": 16, "search_id": f"sid-{alias}", "backtrace": "trace-2",
                "aweme_id": f"{alias}-2", "desc": f"{alias} 深度体验", "create_time": now,
            }}]}}, {"endpoint": "test", "status": 200}
        with patch.object(TikHubClient, "search", side_effect=search):
            result = collect("奥迪E7X", platforms=["douyin"], pages=0, include_enrichment=False)
        aliases = vehicle_search_aliases("奥迪E7X")
        self.assertEqual([call[0] for call in calls[::2]], aliases)
        self.assertTrue(all(call[2] == "8" for call in calls[1::2]))
        self.assertTrue(all(call[3]["searchId"].startswith("sid-") for call in calls[1::2]))
        self.assertEqual(result["collectionStatus"]["status"], "complete")
        self.assertEqual(len(result["items"]), 1 + len(aliases))
        shared = next(item for item in result["items"] if item["platformItemId"] == "same")
        self.assertEqual(set(shared["matchedAliases"]), set(aliases))
        self.assertIn("description", shared["matchedFields"])

    def test_douyin_pagination_state_reads_cursor_and_context(self):
        state = douyin_pagination_state({"data": {"cursor": 8, "has_more": 1, "search_id": "sid", "backtrace": "trace"}})
        self.assertEqual(state, {"hasMore": True, "cursor": "8", "searchId": "sid", "backtrace": "trace"})

    def test_low_popularity_content_stays_in_related_pool_but_not_hot_pool(self):
        now = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
        payload = {"data": [{
            "aweme_id": "fallback-1", "desc": "上汽奥迪 新车体验",
            "create_time": now, "statistics": {"digg_count": 120},
        }]}
        with patch.object(TikHubClient, "search", return_value=(payload, {"endpoint": "test", "status": 200})):
            result = collect("上汽奥迪", platforms=["douyin"], include_enrichment=False,
                             thresholds={"douyin": 8000})
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["hotItems"], [])
        self.assertEqual(result["contentRanking"], [])
        self.assertEqual(result["admission"]["admittedCount"], 1)
        self.assertEqual(result["hotAdmission"]["qualifiedCount"], 0)

    def test_popularity_threshold_only_controls_hot_pool(self):
        now = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
        payload = {"data": [
            {"aweme_id": "hot-1", "desc": "上汽奥迪 热门发布", "create_time": now,
             "statistics": {"digg_count": 9000}},
            {"aweme_id": "cool-1", "desc": "上汽奥迪 普通体验", "create_time": now,
             "statistics": {"digg_count": 120}},
        ]}
        with patch.object(TikHubClient, "search", return_value=(payload, {"endpoint": "test", "status": 200})):
            result = collect("上汽奥迪", platforms=["douyin"], include_enrichment=False,
                             thresholds={"douyin": 8000})
        self.assertEqual({item["platformItemId"] for item in result["items"]}, {"hot-1", "cool-1"})
        self.assertEqual([item["platformItemId"] for item in result["hotItems"]], ["hot-1"])
        self.assertNotIn("below_like_threshold", result["admission"]["rejectedReasons"])

    def test_low_popularity_negative_content_enters_risk_pool(self):
        now = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
        payload = {"data": [{"aweme_id": "risk-low", "desc": "奥迪E7X 异响问题投诉", "create_time": now,
                              "statistics": {"digg_count": 3}}]}
        with patch.object(TikHubClient, "search", return_value=(payload, {"endpoint": "test", "status": 200})):
            result = collect("奥迪E7X", platforms=["douyin"], pages=1, include_enrichment=False,
                             thresholds={"douyin": 8000})
        self.assertEqual(result["hotItems"], [])
        self.assertEqual([item["platformItemId"] for item in result["riskItems"]], ["risk-low"])
        self.assertEqual(result["analysisCoverage"]["risk"]["analyzed"], 1)

    def test_collection_keeps_low_heat_evidence_for_a_platform_without_any_qualified_sample(self):
        now = int((datetime.now(timezone.utc) - timedelta(days=1)).timestamp())
        payloads = {
            "douyin": {"data": [{"aweme_id": "douyin-low", "desc": "车型A 普通体验", "create_time": now, "statistics": {"digg_count": 120}}]},
            "weibo": {"data": [{"mid": "weibo-hot", "text": "车型A 热门体验", "created_at": now, "attitudes_count": 900}]},
        }
        with patch.object(TikHubClient, "search", side_effect=lambda platform, *_: (payloads[platform], {"endpoint": "test", "status": 200})):
            result = collect("车型A", platforms=["douyin", "weibo"], include_enrichment=False,
                             thresholds={"douyin": 8000, "weibo": 500})
        self.assertEqual({item["platformItemId"] for item in result["items"]}, {"douyin-low", "weibo-hot"})
        self.assertEqual([item["platformItemId"] for item in result["hotItems"]], ["weibo-hot"])
        self.assertEqual(result["hotAdmission"]["belowThresholdCount"], 1)
        self.assertEqual(result["admission"]["rejectedByPlatform"]["douyin"], {})

    def test_weibo_rfc2822_publish_time_is_bucketed_in_timeline(self):
        item = normalize_item("weibo", {
            "mid": "w-time", "text": "上汽奥迪 权益", "created_at": "Sat Jul 11 13:37:51 +0800 2026",
        }, "上汽奥迪", "2026-07-11T00:00:00Z")
        result = _aggregate([item], "上汽奥迪", [], [], selected_platforms=["weibo"])
        self.assertEqual(result["timeline"][0]["date"], "2026-07-11")
        self.assertEqual(result["timelineUndated"]["contentCount"], 0)

    def test_aggregate_deduplicates_and_exposes_analysis_coverage_instead_of_confidence(self):
        item = normalize_item("weibo", {"mid": "a", "text": "某车型问题和投诉", "comments_count": 2}, "某车型", "now")
        result = _aggregate([item, item], "某车型", [], [])
        self.assertEqual(len(result["items"]), 1)
        self.assertNotIn("confidenceLabel", result)
        self.assertEqual(result["analysisCoverage"]["sentiment"]["rate"], 100)
        self.assertEqual(result["statusHint"], "未形成高热度")
        self.assertTrue(result["qa"]["evidenceTraceable"])

    def test_snapshot_round_trip_is_scoped(self):
        conn = sqlite3.connect(":memory:"); conn.row_factory = sqlite3.Row; init_schema(conn)
        result = _aggregate([], "车型A", [], [])
        saved = save_snapshot(conn, result, "org-a", "china", {"platforms": ["douyin"]})
        loaded = latest_snapshot(conn, "车型A", "org-a", "china")
        self.assertEqual(loaded["snapshot"]["id"], saved["id"])
        self.assertIsNone(latest_snapshot(conn, "车型A", "org-b", "china"))

    def test_read_time_normalization_downgrades_false_aligned_review_when_evidence_disagrees(self):
        result = _aggregate([], "车型A", [], [])
        result["qa"]["threeFlagships"] = {"status": "aligned", "reviewedEvidenceCount": 10,
                                                 "verifiedEvidenceIds": [f"e-{index}" for index in range(9)]}
        result["unifiedInsight"] = {"validationStatus": "aligned", "publicationStatus": "published", "limitations": []}
        from social_trends import normalize_comparison_result
        normalized = normalize_comparison_result(result)
        self.assertEqual(normalized["qa"]["threeFlagships"]["status"], "disagreement")
        self.assertEqual(normalized["unifiedInsight"]["publicationStatus"], "conditional")
        self.assertIn("1 条证据存在分歧", normalized["unifiedInsight"]["limitations"][0])

    def test_latest_snapshot_normalizes_a_legacy_own_model_competitor_without_rewriting_history(self):
        conn = sqlite3.connect(":memory:"); conn.row_factory = sqlite3.Row; init_schema(conn)
        own_item = normalize_item("weibo", {"mid": "own", "text": "奥迪E7X 推荐"}, "奥迪E7X", "now")
        competitor_item = normalize_item("weibo", {"mid": "m7", "text": "问界M7 推荐"}, "问界M7", "now")
        result = attach_competitor_rankings(
            _aggregate([own_item], "奥迪E7X", [], []),
            [_aggregate([competitor_item], "问界M7", [], [])],
        )
        legacy = json.loads(json.dumps(result, ensure_ascii=False))
        legacy["modelComparisons"].insert(1, {**legacy["modelComparisons"][0], "model": "奥迪 E7X", "role": "competitor"})
        legacy["comparisonEvidence"].append(dict(legacy["comparisonEvidence"][0]))
        saved = save_snapshot(conn, legacy, "org-a", "china", {
            "platforms": ["weibo"], "competitors": ["奥迪 E7X", "问界M7"],
        })
        stored_json = conn.execute("select result_json from social_trend_snapshots where id=?", (saved["id"],)).fetchone()[0]
        loaded = latest_snapshot(conn, "奥迪E7X", "org-a", "china", {"competitors": ["问界M7"]})
        self.assertEqual([row["model"] for row in loaded["modelComparisons"]], ["奥迪E7X", "问界M7"])
        self.assertEqual(loaded["snapshot"]["filters"]["competitors"], ["问界M7"])
        self.assertEqual(len(loaded["comparisonEvidence"]), 2)
        self.assertEqual(
            conn.execute("select result_json from social_trend_snapshots where id=?", (saved["id"],)).fetchone()[0],
            stored_json,
        )

    def test_api_key_is_only_read_from_server_environment(self):
        with patch.dict(os.environ, {"TIKHUB_API_KEY": "server-secret"}):
            self.assertEqual(TikHubClient().key, "server-secret")

    def test_tikhub_business_error_is_not_silently_treated_as_an_empty_result(self):
        with self.assertRaisesRegex(RuntimeError, "TikHub API 400"):
            ensure_tikhub_success({"code": 400, "message": "invalid request"}, "/api/test")
        self.assertEqual(ensure_tikhub_success({"code": 200, "data": {}}, "/api/test")["code"], 200)

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
        self.assertEqual({x["brandName"] for x in result["comparisonItems"]}, {"Model Y", "蔚来ES6"})
        self.assertTrue(all(x["brandName"] == x["normalizedModel"] for x in result["comparisonItems"]))

    def test_competitor_comparison_preserves_platform_collection_diagnostics(self):
        own = _aggregate([], "奥迪E7X", [], [])
        competitor = _aggregate([], "Model Y", [{"platform": "douyin", "itemCount": 4}], [{"platform": "xiaohongshu", "message": "upstream failed"}], selected_platforms=["douyin", "xiaohongshu"])
        competitor["admission"] = {"rejectedByPlatform": {"douyin": {"below_like_threshold": 4}, "xiaohongshu": {}}}
        competitor["hotAdmission"] = {"qualifiedCount": 0, "belowThresholdCount": 4}
        result = attach_competitor_rankings(own, [competitor])
        collection = result["modelComparisons"][1]["collection"]
        self.assertEqual(collection["sources"][0]["itemCount"], 4)
        self.assertEqual(collection["warnings"][0]["platform"], "xiaohongshu")
        self.assertEqual(collection["admission"]["rejectedByPlatform"]["douyin"]["below_like_threshold"], 4)
        self.assertEqual(collection["hotAdmission"]["qualifiedCount"], 0)

    def test_comparison_drops_a_legacy_own_model_competitor_and_duplicate_evidence(self):
        own_item = normalize_item("weibo", {"mid": "same", "text": "奥迪E7X 推荐", "attitudes_count": 100}, "奥迪E7X", "now")
        own = _aggregate([own_item], "奥迪E7X", [], [])
        duplicate_own = _aggregate([dict(own_item)], "奥迪 E7X", [], [])
        competitor = _aggregate(
            [normalize_item("weibo", {"mid": "m7", "text": "问界M7 推荐", "attitudes_count": 80}, "问界M7", "now")],
            "问界M7", [], [],
        )
        result = attach_competitor_rankings(own, [duplicate_own, competitor])
        self.assertEqual([row["model"] for row in result["modelComparisons"]], ["奥迪E7X", "问界M7"])
        self.assertEqual([row["model"] for row in result["modelHeatRanking"]], ["奥迪E7X", "问界M7"])
        evidence_keys = [(vehicle_identity_key(item["normalizedModel"]), item["platform"], item["id"]) for item in result["comparisonEvidence"]]
        self.assertEqual(len(evidence_keys), len(set(evidence_keys)))

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
        published_day = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
        rows = [
            {"平台": "抖音", "作品ID": "d1", "作品标题": "奥迪E7X 深度体验", "发布时间": f"{published_day} 12:00:00", "点赞数": "9000", "评论数": "100", "作品链接": "https://www.douyin.com/video/d1"},
            {"平台": "抖音", "作品ID": "d2", "作品标题": "奥迪E7X 到店", "发布时间": f"{published_day} 13:00:00", "点赞数": "7999"},
            {"平台": "小红书", "作品ID": "x1", "作品标题": "奥迪E7X 试驾", "发布时间": f"{published_day} 14:00:00", "点赞数": "600", "评论数": "30"},
            {"平台": "微博", "作品ID": "w1", "作品标题": "其他车型", "发布时间": f"{published_day} 14:00:00", "点赞数": "900"},
        ]
        result = import_records(rows, "奥迪E7X", ["douyin", "xiaohongshu", "weibo"], time_range="7d", filename="assistant.xlsx")
        self.assertEqual([x["platformItemId"] for x in result["contentRanking"]], ["d1", "x1"])
        self.assertEqual({x["platformItemId"] for x in result["items"]}, {"d1", "d2", "x1"})
        self.assertEqual(result["admission"]["admittedCount"], 3)
        self.assertEqual(result["hotAdmission"]["belowThresholdCount"], 1)
        self.assertEqual(result["admission"]["rejectedReasons"]["model_not_relevant"], 1)
        self.assertEqual(result["items"][0]["evidence"]["source"], "社媒助手导入")


if __name__ == "__main__":
    unittest.main()
