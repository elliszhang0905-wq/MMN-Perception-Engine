import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import server


class FakeAdapter:
    def search(self, platform, query, page, count, time_range, cursor="", search_context=None):
        model = query.split()[0]
        item_id = str(abs(hash(query)))
        return {
            "items": [{
                "id": item_id,
                "platformItemId": item_id,
                "platform": "douyin",
                "sourceUrl": f"https://www.douyin.com/video/{item_id}",
                "text": f"{model} 真实体验",
                "author": "测试汽车号",
                "publishedAt": time_range["end"],
                "nativeMetrics": {
                    "views": 1000 + len(query),
                    "likes": 100,
                    "comments": 12,
                    "shares": 5,
                },
                "viewsVerified": True,
            }],
            "nextCursor": "",
        }


class DouyinVehicleRadarApiTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "commercial.sqlite"
        self.original_db = server.DB_PATH
        self.original_repository = server.DOUYIN_VEHICLE_RADAR_REPOSITORY
        server.DB_PATH = self.db_path
        server.DOUYIN_VEHICLE_RADAR_REPOSITORY = None
        server.init_db()

    def tearDown(self):
        server.DB_PATH = self.original_db
        server.DOUYIN_VEHICLE_RADAR_REPOSITORY = self.original_repository
        self.temp.cleanup()

    def test_server_registers_manual_run_review_strategy_and_insight_routes(self):
        source = Path(server.__file__).read_text(encoding="utf-8")
        for route in (
            "/api/douyin-vehicle-radar/runs",
            "/api/douyin-vehicle-radar/items/review",
            "/api/douyin-vehicle-radar/strategies",
            "/api/douyin-vehicle-radar/video-insights/jobs",
        ):
            self.assertIn(route, source)

    def test_latest_radar_collects_unique_video_ids_for_insight_restore(self):
        run = {
            "result": {
                "lists": {
                    "own": [
                        {"platformItemId": "video-1"},
                        {"platformItemId": "video-2"},
                    ],
                    "all": [
                        {"itemId": "video-1"},
                        {"platformItemId": ""},
                        "invalid",
                    ],
                },
            },
        }
        self.assertEqual(
            ["video-1", "video-2"],
            server.douyin_vehicle_radar_item_ids(run),
        )

    def test_async_manual_run_reaches_persistent_completed_state(self):
        run = server.create_douyin_vehicle_radar_run({
            "subject": "智己LS6",
            "competitors": ["理想i6", "问界M6", "极氪7X"],
            "topics": ["动力与操控"],
            "rangeDays": 7,
            "maxQueries": 8,
            "count": 5,
        }, org_id="org-a", edition="china", adapter=FakeAdapter())
        for _ in range(50):
            stored = server.douyin_vehicle_radar_repository().get_run(
                run["id"], "org-a", "china"
            )
            if stored["status"] in {"completed", "failed"}:
                break
            time.sleep(0.02)
        self.assertEqual("completed", stored["status"])
        self.assertGreater(stored["result"]["counts"]["verified"], 0)
        self.assertEqual("智己LS6", stored["result"]["subject"])
        self.assertEqual(["理想i6", "问界M6", "极氪7X"], stored["result"]["competitors"])

    def test_single_model_request_keeps_temporary_query_out_of_competitor_context(self):
        run = server.create_douyin_vehicle_radar_run({
            "subject": "蔚来ET5T",
            "competitors": ["不应写入的竞品"],
            "topics": ["不应写入的属性"],
            "mode": "single_model_rank",
            "rangeDays": 14,
            "topN": 20,
            "maxQueries": 2,
            "maxPages": 3,
            "maxRequests": 6,
            "maxCandidates": 60,
            "count": 5,
        }, org_id="org-a", edition="china", adapter=FakeAdapter())
        for _ in range(50):
            stored = server.douyin_vehicle_radar_repository().get_run(
                run["id"], "org-a", "china"
            )
            if stored["status"] in {"completed", "partial", "failed"}:
                break
            time.sleep(0.02)
        self.assertNotEqual("failed", stored["status"])
        self.assertEqual("蔚来ET5T", stored["result"]["subject"])
        self.assertEqual([], stored["result"]["competitors"])
        self.assertEqual(20, stored["result"]["topN"])
        self.assertEqual("single_model_rank", stored["result"]["mode"])

    def test_single_model_request_rejects_missing_model_and_illegal_top_n(self):
        with self.assertRaisesRegex(ValueError, "车型名称"):
            server.create_douyin_vehicle_radar_run({
                "subject": "",
                "mode": "single_model_rank",
                "rangeDays": 7,
            }, org_id="org-a", edition="china", adapter=FakeAdapter())
        with self.assertRaisesRegex(ValueError, "Top 10"):
            server.create_douyin_vehicle_radar_run({
                "subject": "智己LS6",
                "mode": "single_model_rank",
                "rangeDays": 7,
                "topN": 999,
            }, org_id="org-a", edition="china", adapter=FakeAdapter())

    def test_strategy_fails_closed_when_three_review_capability_is_unavailable(self):
        repository = server.douyin_vehicle_radar_repository()
        project = repository.upsert_project("org-a", "china", "智己LS6", ["理想i6"], [])
        run = repository.create_run(project, 7)
        from douyin_vehicle_radar import RadarService
        RadarService(repository, FakeAdapter()).run(run["id"], "org-a", "china", max_queries=2)
        completed = repository.get_run(run["id"], "org-a", "china")
        with patch.object(server, "qwen_config", return_value={"configured": False}), \
             patch.object(server, "deepseek_config", return_value={"configured": False}), \
             patch.object(server, "kimi_config", return_value={"configured": False}):
            strategy = server.douyin_vehicle_radar_strategy(
                completed, org_id="org-a", edition="china"
            )
        self.assertEqual(
            "insufficient_evidence",
            strategy["result"]["qa"]["threeFlagships"]["status"],
        )
        self.assertEqual(
            "withheld",
            strategy["result"]["unifiedInsight"]["publicationStatus"],
        )


if __name__ == "__main__":
    unittest.main()
