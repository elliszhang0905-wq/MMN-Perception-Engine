import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from douyin_vehicle_radar import (
    RadarRepository,
    RadarService,
    build_profiles,
    build_queries,
    classify_candidate,
    date_window,
    init_schema,
    rank_items,
)


NOW = datetime(2026, 7, 29, 8, 0, tzinfo=timezone.utc)


class FakeAdapter:
    def __init__(self, items, statistics=None, fail_statistics=False):
        self.items = items
        self.statistics = statistics or {}
        self.fail_statistics = fail_statistics
        self.calls = []
        self.statistics_calls = []

    def search(self, platform, query, page, count, time_range, cursor=""):
        self.calls.append((platform, query, page, count, time_range))
        return {"items": self.items, "nextCursor": ""}

    def fetch_statistics(self, platform_item_ids):
        self.statistics_calls.append(list(platform_item_ids))
        if self.fail_statistics:
            raise RuntimeError("statistics unavailable")
        return {
            "items": {
                item_id: self.statistics[item_id]
                for item_id in platform_item_ids if item_id in self.statistics
            },
            "observedAt": datetime.now(timezone.utc).isoformat(),
        }


class DouyinVehicleRadarTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "radar.sqlite"

        def connection():
            return sqlite3.connect(self.db_path)

        self.repository = RadarRepository(connection)
        with connection() as conn:
            init_schema(conn)

    def tearDown(self):
        self.temp.cleanup()

    def item(self, text, published="2026-07-28T08:00:00+00:00", views=100):
        key = str(abs(hash((text, published))))
        return {
            "id": key,
            "platformItemId": key,
            "platform": "douyin",
            "sourceUrl": f"https://www.douyin.com/video/{key}",
            "text": text,
            "author": "汽车观察",
            "publishedAt": published,
            "nativeMetrics": {"views": views, "likes": 10, "comments": 2, "shares": 1},
            "viewsVerified": views is not None,
        }

    def test_full_model_is_verified_but_short_alias_requires_review(self):
        profiles = build_profiles("智己LS6", ["理想i6"])
        window = date_window(7, now_value=NOW)
        exact = classify_candidate(self.item("智己LS6深度测评"), profiles, [], window)
        short = classify_candidate(self.item("LS6深度测评"), profiles, [], window)
        self.assertEqual("verified", exact["verificationStatus"])
        self.assertEqual("pending_review", short["verificationStatus"])

    def test_missing_date_and_irrelevant_content_fail_closed(self):
        profiles = build_profiles("智己LS6", ["理想i6"])
        window = date_window(7, now_value=NOW)
        self.assertEqual(
            "missing_published_at",
            classify_candidate(self.item("智己LS6", published=""), profiles, [], window)["reason"],
        )
        self.assertEqual(
            "no_vehicle_evidence",
            classify_candidate(self.item("一条普通汽车资讯"), profiles, [], window)["reason"],
        )

    def test_comparison_and_attribute_buckets_are_deterministic(self):
        profiles = build_profiles("智己LS6", ["理想i6"])
        window = date_window(7, now_value=NOW)
        comparison = classify_candidate(
            self.item("智己LS6与理想i6怎么选"), profiles, ["动力与操控"], window
        )
        attribute = classify_candidate(
            self.item("智己LS6动力与操控实测"), profiles, ["动力与操控"], window
        )
        self.assertEqual("comparison", comparison["bucket"])
        self.assertEqual("attribute", attribute["bucket"])

    def test_query_plan_covers_each_vehicle_and_comparisons(self):
        queries = [item["query"] for item in build_queries(
            "智己LS6", ["理想i6", "问界M6", "极氪7X"], ["动力与操控"], max_queries=20
        )]
        self.assertIn("智己LS6", queries)
        self.assertIn("理想i6", queries)
        self.assertIn("智己LS6 理想i6", queries)
        self.assertIn("智己LS6 动力与操控", queries)

    def test_repository_is_tenant_and_edition_scoped(self):
        project = self.repository.upsert_project(
            "org-a", "china", "智己LS6", ["理想i6"], ["动力与操控"]
        )
        self.assertIsNotNone(self.repository.get_project(project["id"], "org-a", "china"))
        self.assertIsNone(self.repository.get_project(project["id"], "org-b", "china"))
        self.assertIsNone(self.repository.get_project(project["id"], "org-a", "global"))

    def test_manual_run_persists_results_and_ranks_by_views(self):
        project = self.repository.upsert_project(
            "org-a", "china", "智己LS6", ["理想i6"], ["动力与操控"]
        )
        run = self.repository.create_run(project, 7)
        adapter = FakeAdapter([
            self.item("智己LS6空间体验", views=200),
            self.item("智己LS6动力与操控实测", views=500),
            self.item("LS6只有短别名", views=900),
        ])
        result = RadarService(self.repository, adapter).run(run["id"], "org-a", "china")
        stored = self.repository.get_run(run["id"], "org-a", "china")
        self.assertEqual("completed", stored["status"])
        self.assertEqual(2, result["counts"]["verified"])
        self.assertEqual(1, result["counts"]["pendingReview"])
        self.assertEqual(500, result["lists"]["attribute"][0]["metrics"]["views"])

    def test_invalid_ranking_field_is_rejected(self):
        with self.assertRaises(ValueError):
            rank_items([], field="relevance")

    def test_missing_views_are_enriched_and_never_default_to_zero(self):
        project = self.repository.upsert_project(
            "org-a", "china", "智己LS6", ["理想i6"], ["动力与操控"]
        )
        run = self.repository.create_run(project, 7)
        missing = self.item("智己LS6动力与操控实测", views=None)
        adapter = FakeAdapter(
            [missing],
            statistics={missing["platformItemId"]: {"views": 4321}},
        )
        result = RadarService(self.repository, adapter).run(run["id"], "org-a", "china")
        self.assertEqual(4321, result["lists"]["attribute"][0]["metrics"]["views"])
        self.assertEqual("verified", result["lists"]["attribute"][0]["metricStatus"]["views"])
        self.assertEqual(1, result["counts"]["rankingEligible"])
        self.assertEqual(1, len(adapter.statistics_calls))

    def test_failed_view_enrichment_is_partial_and_excluded_from_formal_rank(self):
        project = self.repository.upsert_project(
            "org-a", "china", "智己LS6", ["理想i6"], []
        )
        run = self.repository.create_run(project, 7)
        missing = self.item("智己LS6真实体验", views=None)
        result = RadarService(
            self.repository, FakeAdapter([missing], fail_statistics=True)
        ).run(run["id"], "org-a", "china")
        stored = self.repository.get_run(run["id"], "org-a", "china")
        self.assertEqual("partial", stored["status"])
        self.assertEqual([], result["lists"]["own"])
        self.assertIsNone(result["lists"]["incompleteMetrics"][0]["metrics"]["views"])
        self.assertEqual("failed", result["lists"]["incompleteMetrics"][0]["metricStatus"]["views"])

    def test_metric_cache_prevents_duplicate_paid_lookup(self):
        project = self.repository.upsert_project("org-a", "china", "智己LS6", [], [])
        first = self.repository.create_run(project, 7, force=True)
        item = self.item("智己LS6真实体验", views=None)
        adapter = FakeAdapter([item], statistics={item["platformItemId"]: {"views": 900}})
        RadarService(self.repository, adapter).run(first["id"], "org-a", "china")
        second = self.repository.create_run(project, 7, force=True)
        RadarService(self.repository, adapter).run(second["id"], "org-a", "china")
        self.assertEqual(1, len(adapter.statistics_calls))

    def test_failed_batch_is_split_and_only_bad_item_stays_out_of_rank(self):
        class SplitAdapter(FakeAdapter):
            def fetch_statistics(self, platform_item_ids):
                self.statistics_calls.append(list(platform_item_ids))
                if "bad" in platform_item_ids:
                    raise RuntimeError("one invalid item poisoned the batch")
                return {
                    "items": {item_id: {"views": 100 + index} for index, item_id in enumerate(platform_item_ids)},
                    "observedAt": datetime.now(timezone.utc).isoformat(),
                }

        project = self.repository.upsert_project("org-a", "china", "智己LS6", [], [])
        run = self.repository.create_run(project, 7)
        good = self.item("智己LS6好内容", views=None)
        good["platformItemId"] = good["id"] = "good"
        bad = self.item("智己LS6坏链接", views=None)
        bad["platformItemId"] = bad["id"] = "bad"
        result = RadarService(
            self.repository, SplitAdapter([good, bad])
        ).run(run["id"], "org-a", "china")
        self.assertEqual(1, result["counts"]["rankingEligible"])
        self.assertEqual("good", result["lists"]["own"][0]["platformItemId"])
        self.assertEqual("bad", result["lists"]["incompleteMetrics"][0]["platformItemId"])


if __name__ == "__main__":
    unittest.main()
