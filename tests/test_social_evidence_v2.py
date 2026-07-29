import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from social_evidence import (
    BudgetExceeded,
    SocialEvidenceRepository,
    SocialEvidenceService,
    TikHubEvidenceAdapter,
    _within_date_window,
    build_nsr_validation_mart,
    build_query_plan,
    normalize_observation,
)


class FakeEvidenceAdapter:
    def __init__(self):
        self.calls = []

    def search(self, platform, query, page, count, time_range, cursor=""):
        self.calls.append((platform, query, page, count, time_range, cursor))
        item_id = f"{platform}-{len(self.calls)}"
        return {
            "items": [{
                "id": item_id,
                "platformItemId": item_id,
                "platform": platform,
                "sourceUrl": f"https://example.test/{item_id}",
                "text": f"{query} 用户讨论智能座舱，也会比较竞品",
                "author": "公开用户",
                "publishedAt": "2026-07-21T10:00:00+00:00",
                "nativeMetrics": {"likes": 12, "comments": 3},
                "sourceRole": "user",
            }],
            "nextCursor": "",
            "requestMeta": {"endpoint": f"/{platform}/search", "status": 200, "cost": 1},
            "raw": {"data": [{"id": item_id}], "authorization": "must-not-persist"},
        }


class SocialEvidenceV2Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.repo = SocialEvidenceRepository(root / "social_evidence.sqlite", root / "raw")
        self.service = SocialEvidenceService(self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def test_default_repository_paths_follow_mmn_data_root(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(
            os.environ,
            {
                "MMN_DATA_ROOT": tmp,
                "MMN_SOCIAL_EVIDENCE_DB": "",
                "MMN_SOCIAL_EVIDENCE_RAW_DIR": "",
            },
            clear=False,
        ):
            repository = SocialEvidenceRepository()
            self.assertEqual(repository.db_path, Path(tmp) / "social_evidence.sqlite")
            self.assertEqual(repository.raw_dir, Path(tmp) / "social_evidence_raw")

    def plan(self, center_type="social_trend", **overrides):
        payload = {
            "projectId": "project-e7x",
            "centerType": center_type,
            "subject": {"brand": "上汽奥迪", "model": "AUDI E7X", "aliases": ["E7X"]},
            "competitors": ["奔驰", "蔚来"],
            "themes": ["智能座舱"],
            "scenes": ["家庭出行"],
            "issueTerms": ["值不值"],
            "eventTerms": ["上市"],
            "exclusionTerms": ["卡车"],
            "platforms": ["douyin", "xiaohongshu", "weibo"],
            "dateWindow": {"start": "2026-07-01", "end": "2026-07-22"},
            "sampling": {"maxPages": 1, "maxItemsPerPlatform": 10, "commentDepth": 0},
            "budget": {"maxRequests": 30, "maxEstimatedCost": 30},
        }
        payload.update(overrides)
        return build_query_plan(payload, "org-a", "china")

    def nsr_plan(self, **overrides):
        payload = {
            "projectId": "decision-audi-e7x",
            "centerType": "nsr_validation",
            "subject": {"brand": "上汽奥迪", "model": "AUDI E7X", "aliases": ["E7X"]},
            "vehicleContext": {
                "brand": "上汽奥迪", "model": "AUDI E7X", "modelCode": "audi-e7x",
                "contextSource": "decision_cockpit", "contextVersion": "ctx-20260723",
            },
            "nsrSource": {"datasetVersion": "nsr-20260722", "fingerprint": "sha256:real-nsr"},
            "validationTargets": [
                {
                    "targetId": "target-cockpit", "attributeId": "smart-cockpit",
                    "label": "智能座舱", "baselineNsr": 0.71,
                    "queryTerms": {
                        "canonical": ["智能座舱"], "userLanguage": ["车机好用"],
                        "scenes": ["家庭出行"], "support": ["流畅"],
                        "challenge": ["卡顿"], "comparison": ["比理想"],
                    },
                },
                {
                    "targetId": "target-luxury", "attributeId": "luxury",
                    "label": "豪华感", "baselineNsr": 0.64,
                    "queryTerms": {"canonical": ["豪华感"], "support": ["质感"], "challenge": ["塑料感"]},
                },
            ],
            "competitors": ["理想L9"],
            "platforms": ["douyin", "xiaohongshu", "weibo"],
            "dateWindow": {"start": "2026-07-17", "end": "2026-07-23"},
            "sampling": {
                "maxPages": 3, "pageSize": 20, "maxCandidatesPerPlatform": 60,
                "maxEvidencePerTargetPerPlatform": 20, "commentDepth": 0,
            },
            "budget": {"maxRequests": 60, "maxEstimatedCost": 60},
        }
        payload.update(overrides)
        return build_query_plan(payload, "org-a", "china")

    def test_query_plan_is_scoped_versioned_and_expands_business_terms(self):
        plan = self.plan()
        self.assertEqual(plan["orgId"], "org-a")
        self.assertEqual(plan["edition"], "china")
        self.assertEqual(plan["schemaVersion"], "social-evidence-query-v2")
        self.assertIn("AUDI E7X 智能座舱", plan["queries"])
        self.assertIn("AUDI E7X 值不值", plan["queries"])
        self.assertNotIn("卡车", " ".join(plan["queries"]))

    def test_nsr_query_plan_freezes_vehicle_source_targets_and_batched_shards(self):
        plan = self.nsr_plan()
        self.assertEqual(plan["planVersion"], "v2.1")
        self.assertEqual(plan["vehicleContext"]["modelCode"], "audi-e7x")
        self.assertEqual(plan["nsrSource"]["datasetVersion"], "nsr-20260722")
        self.assertEqual(len(plan["validationTargets"]), 2)
        self.assertEqual(len(plan["queryShards"]), 6)
        self.assertEqual({row["queryType"] for row in plan["queryShards"]}, {"directed", "counter", "broad"})
        self.assertEqual(len(plan["queries"]), 6)
        self.assertEqual(plan["sampling"]["pageSize"], 20)
        self.assertEqual(plan["sampling"]["maxCandidatesPerPlatform"], 60)
        self.assertEqual(plan["sampling"]["maxEvidencePerTargetPerPlatform"], 20)
        self.assertEqual(plan["controlQueries"]["vehicleRequired"], True)

    def test_nsr_query_plan_rejects_more_than_two_competitors(self):
        with self.assertRaisesRegex(ValueError, "竞品"):
            self.nsr_plan(competitors=["理想L9", "问界M9", "蔚来ES8"])

    def test_page_pagination_continues_without_cursor_until_empty_page(self):
        class PageAdapter(FakeEvidenceAdapter):
            def search(self, platform, query, page, count, time_range, cursor=""):
                response = super().search(platform, query, page, count, time_range, cursor)
                response["requestMeta"]["paginationMode"] = "page"
                if page == 3:
                    response["items"] = []
                return response

        plan = self.plan(
            subject={"brand": "上汽奥迪", "model": "AUDI E7X", "aliases": []},
            platforms=["xiaohongshu"], themes=[], scenes=[], issueTerms=[], eventTerms=[], competitors=[],
            sampling={"maxPages": 5, "pageSize": 20, "maxCandidatesPerPlatform": 60},
        )
        adapter = PageAdapter()
        job = self.service.create_job(plan)
        self.service.run_job(job["jobId"], "org-a", adapter)
        self.assertEqual([call[2] for call in adapter.calls], [1, 2, 3])

    def test_page_limit_is_reported_as_partial_instead_of_complete_coverage(self):
        class EndlessPageAdapter(FakeEvidenceAdapter):
            def search(self, platform, query, page, count, time_range, cursor=""):
                response = super().search(platform, query, page, count, time_range, cursor)
                response["requestMeta"]["paginationMode"] = "page"
                return response

        plan = self.plan(
            subject={"brand": "上汽奥迪", "model": "AUDI E7X", "aliases": []},
            platforms=["xiaohongshu"], themes=[], scenes=[], issueTerms=[], eventTerms=[], competitors=[],
            sampling={"maxPages": 2, "pageSize": 20, "maxCandidatesPerPlatform": 60},
        )
        job = self.service.create_job(plan)
        mart = self.service.run_job(job["jobId"], "org-a", EndlessPageAdapter())["mart"]
        self.assertEqual(mart["coverageStatus"], "partial_page_limit")
        self.assertEqual(mart["collectionCoverage"][0]["stopReason"], "partial_page_limit")

    def test_one_platform_failure_preserves_other_platform_evidence(self):
        class PartialAdapter(FakeEvidenceAdapter):
            def search(self, platform, *args, **kwargs):
                if platform == "xiaohongshu":
                    raise RuntimeError("private supplier failure")
                return super().search(platform, *args, **kwargs)

        plan = self.plan(
            subject={"brand": "上汽奥迪", "model": "AUDI E7X", "aliases": []},
            platforms=["douyin", "xiaohongshu"], themes=[], scenes=[], issueTerms=[], eventTerms=[], competitors=[],
        )
        job = self.service.create_job(plan)
        result = self.service.run_job(job["jobId"], "org-a", PartialAdapter())
        self.assertEqual(result["status"], "degraded")
        self.assertEqual(result["mart"]["coverageStatus"], "partial_platform_failure")
        self.assertGreater(result["mart"]["coverage"]["contentCount"], 0)
        xhs = next(row for row in result["mart"]["collectionCoverage"] if row["platform"] == "xiaohongshu")
        self.assertEqual(xhs["stopReason"], "platform_unavailable")
        self.assertNotIn("private supplier failure", str(result["mart"]))

    def test_nsr_job_builds_independent_validation_mart_without_rewriting_nsr(self):
        plan = self.nsr_plan(
            platforms=["douyin"], competitors=[],
            sampling={"maxPages": 1, "pageSize": 20, "maxCandidatesPerPlatform": 60,
                      "maxEvidencePerTargetPerPlatform": 20},
            budget={"maxRequests": 10, "maxEstimatedCost": 10},
        )
        job = self.service.create_job(plan)
        mart = self.service.run_job(job["jobId"], "org-a", FakeEvidenceAdapter())["mart"]
        self.assertEqual(mart["martType"], "nsr_validation")
        self.assertEqual(mart["schemaVersion"], "nsr-validation-mart-v1")
        self.assertEqual(mart["vehicleContext"]["modelCode"], "audi-e7x")
        self.assertEqual(mart["nsrSource"]["fingerprint"], "sha256:real-nsr")
        self.assertEqual(
            {row["verdict"] for row in mart["targetValidations"]},
            {"pending_adjudication", "insufficient_evidence"},
        )
        self.assertNotIn("updatedNsr", mart)

    def test_generic_stance_word_cannot_be_attributed_to_every_nsr_target(self):
        plan = self.nsr_plan(platforms=["douyin"], competitors=[])
        for target in plan["validationTargets"]:
            target["queryTerms"]["challenge"] = ["吐槽"]
        mart = build_nsr_validation_mart(plan, [{
            "canonicalContentId": "generic-complaint", "platform": "douyin",
            "sourceUrl": "https://example.test/generic-complaint",
            "publishedAt": "2026-07-21T10:00:00+00:00",
            "text": "AUDI E7X 吐槽一下，不好用", "nativeMetrics": {},
        }])
        self.assertEqual(
            [row["evidenceCount"] for row in mart["targetValidations"]],
            [0, 0],
        )
        self.assertTrue(all(row["verdict"] == "insufficient_evidence" for row in mart["targetValidations"]))

    def test_budget_gate_fails_before_any_external_request(self):
        adapter = FakeEvidenceAdapter()
        plan = self.plan(budget={"maxRequests": 1, "maxEstimatedCost": 1})
        job = self.service.create_job(plan)
        with self.assertRaises(BudgetExceeded):
            self.service.run_job(job["jobId"], "org-a", adapter)
        self.assertEqual(adapter.calls, [])
        stored = self.repo.get_job(job["jobId"], "org-a")
        self.assertEqual(stored["status"], "manual_required")
        self.assertEqual(stored["stage"], "budget_check")

    def test_same_fingerprint_active_job_is_idempotent(self):
        first = self.service.create_job(self.plan())
        second = self.service.create_job(self.plan())
        self.assertEqual(second["jobId"], first["jobId"])
        with self.repo.connect() as conn:
            self.assertEqual(conn.execute("select count(*) from evidence_jobs").fetchone()[0], 1)
            self.assertEqual(conn.execute("select count(*) from query_plans").fetchone()[0], 1)

    def test_job_raw_evidence_and_mart_survive_a_new_connection(self):
        plan = self.plan(platforms=["douyin"], themes=[] , scenes=[], issueTerms=[], eventTerms=[], competitors=[])
        job = self.service.create_job(plan)
        result = self.service.run_job(job["jobId"], "org-a", FakeEvidenceAdapter())
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["mart"]["martType"], "social_trend")
        self.assertGreater(result["mart"]["coverage"]["contentCount"], 0)

        reopened = SocialEvidenceRepository(self.repo.db_path, self.repo.raw_dir)
        stored = reopened.get_job(job["jobId"], "org-a")
        mart = reopened.latest_mart("project-e7x", "org-a", "china", "social_trend")
        self.assertEqual(stored["status"], "ready")
        self.assertEqual(mart["jobId"], job["jobId"])
        raw = list(self.repo.raw_dir.rglob("*.json"))
        self.assertTrue(raw)
        raw_text = raw[0].read_text(encoding="utf-8")
        self.assertNotIn("must-not-persist", raw_text)
        self.assertNotIn("authorization", raw_text.lower())

    def test_dual_source_observations_share_one_stable_canonical_content(self):
        plan = self.plan(platforms=["douyin"], themes=[], scenes=[], issueTerms=[], eventTerms=[], competitors=[])
        job = self.service.create_job(plan)
        first = {
            "platform": "douyin", "platformItemId": "same-video",
            "sourceUrl": "https://www.douyin.com/video/same-video",
            "text": "第一版文案", "publishedAt": "2026-07-21T10:00:00+00:00",
            "internalSource": "tikhub", "collectionMode": "api",
        }
        raw_a = self.repo.save_raw_request(
            job, "douyin", "manual-test", 1,
            {"items": [first], "raw": {}, "requestMeta": {"status": 200}},
        )
        stored_a = self.repo.upsert_content(job, first, raw_a)
        imported = self.repo.import_observations(job, [{
            **first, "text": "第二版文案", "observedAt": "2026-07-22T10:00:00+00:00",
        }])
        self.assertEqual(imported[0]["canonicalContentId"], stored_a["canonicalContentId"])
        with self.repo.connect() as conn:
            self.assertEqual(conn.execute("select count(*) from canonical_contents").fetchone()[0], 1)
            rows = conn.execute(
                "select internal_source,collection_mode from content_observations order by internal_source"
            ).fetchall()
        self.assertEqual(
            [(row["internal_source"], row["collection_mode"]) for row in rows],
            [("social_assistant", "file"), ("tikhub", "api")],
        )

    def test_observation_contract_rejects_private_or_incomplete_source_records(self):
        with self.assertRaises(ValueError):
            normalize_observation(
                {"platform": "douyin", "platformItemId": "1", "sourceUrl": "file:///private", "text": "x"},
                internal_source="social_assistant", collection_mode="file",
            )
        with self.assertRaises(ValueError):
            normalize_observation(
                {"platform": "douyin", "platformItemId": "1", "sourceUrl": "https://example.test/1", "text": "x"},
                internal_source="unknown", collection_mode="file",
            )

    def test_tenant_scope_blocks_cross_org_job_and_mart_reads(self):
        job = self.service.create_job(self.plan())
        self.assertIsNone(self.repo.get_job(job["jobId"], "org-b"))
        self.assertIsNone(self.repo.latest_mart("project-e7x", "org-b", "china", "social_trend"))

    def test_brand_and_trend_marts_have_distinct_contracts(self):
        trend_job = self.service.create_job(self.plan("social_trend", platforms=["douyin"], themes=[], scenes=[], issueTerms=[], eventTerms=[], competitors=[]))
        brand_job = self.service.create_job(self.plan("brand_penetration", platforms=["douyin"], themes=[], scenes=[], issueTerms=[], eventTerms=[], competitors=[]))
        trend = self.service.run_job(trend_job["jobId"], "org-a", FakeEvidenceAdapter())["mart"]
        brand = self.service.run_job(brand_job["jobId"], "org-a", FakeEvidenceAdapter())["mart"]
        self.assertEqual(trend["schemaVersion"], "social-trend-mart-v2")
        self.assertEqual(brand["schemaVersion"], "brand-penetration-mart-v2")
        self.assertIn("changeSignals", trend)
        self.assertNotIn("brandAssociations", trend)
        self.assertIn("brandAssociations", brand)
        self.assertIn("public social evidence", brand["boundary"]["scope"])

    def test_brand_mart_v3_persists_neutral_three_review_decision(self):
        job = self.service.create_job(self.plan(
            "brand_penetration", platforms=["douyin"], themes=[], scenes=[], issueTerms=[], eventTerms=[], competitors=[]
        ))
        decision = {
            "schemaVersion": "brand-penetration-analysis-v3",
            "validation": {"status": "aligned", "independentReviews": [
                {"role": "独立复核A", "status": "completed"},
                {"role": "独立复核B", "status": "completed"},
                {"role": "独立复核C", "status": "completed"},
            ]},
            "brandConclusions": [], "pairwiseConclusions": [],
        }
        result = self.service.run_job(
            job["jobId"], "org-a", FakeEvidenceAdapter(),
            brand_analysis_runner=lambda _plan, _items: decision,
        )
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["mart"]["schemaVersion"], "brand-penetration-mart-v3")
        self.assertEqual(result["mart"]["brandDecision"], decision)
        self.assertNotIn("qwen", json.dumps(result["mart"], ensure_ascii=False).lower())

    def test_recovery_marks_interrupted_jobs_as_degraded_without_deleting_evidence(self):
        job = self.service.create_job(self.plan())
        self.repo.update_job(job["jobId"], "org-a", status="running", stage="collecting_discovery", progress=35)
        recovered = self.repo.recover_interrupted_jobs()
        self.assertEqual(recovered, 1)
        stored = self.repo.get_job(job["jobId"], "org-a")
        self.assertEqual(stored["status"], "degraded")
        self.assertTrue(stored["retryable"])

    def test_recovery_preserves_queued_jobs_for_external_worker(self):
        job = self.service.create_job(self.plan())
        self.assertEqual(self.repo.recover_interrupted_jobs(), 0)
        self.assertEqual(self.repo.get_job(job["jobId"], "org-a")["status"], "queued")

    def test_actual_cost_stops_collection_when_supplier_cost_exceeds_budget(self):
        class ExpensiveAdapter(FakeEvidenceAdapter):
            def search(self, *args, **kwargs):
                response = super().search(*args, **kwargs)
                response["requestMeta"]["cost"] = 10
                return response

        plan = self.plan(subject={"brand": "上汽奥迪", "model": "AUDI E7X", "aliases": []}, platforms=["douyin"], themes=[], scenes=[], issueTerms=[], eventTerms=[], competitors=[], budget={"maxRequests": 5, "maxEstimatedCost": 5})
        job = self.service.create_job(plan)
        with patch.dict("os.environ", {"MMN_SOCIAL_EVIDENCE_ESTIMATED_UNIT_COST": "0"}):
            with self.assertRaises(BudgetExceeded):
                self.service.run_job(job["jobId"], "org-a", ExpensiveAdapter())
        stored = self.repo.get_job(job["jobId"], "org-a")
        self.assertEqual(stored["status"], "manual_required")
        self.assertEqual(stored["actualCost"], 10)

    def test_date_window_and_exclusions_are_hard_admission_rules(self):
        class BoundaryAdapter(FakeEvidenceAdapter):
            def search(self, platform, query, page, count, time_range, cursor=""):
                response = super().search(platform, query, page, count, time_range, cursor)
                response["items"].extend([
                    {**response["items"][0], "id": "old", "platformItemId": "old", "publishedAt": "2026-06-01T00:00:00+00:00"},
                    {**response["items"][0], "id": "truck", "platformItemId": "truck", "text": "AUDI E7X 卡车无关内容"},
                ])
                return response

        plan = self.plan(subject={"brand": "上汽奥迪", "model": "AUDI E7X", "aliases": []}, platforms=["douyin"], themes=[], scenes=[], issueTerms=[], eventTerms=[], competitors=[])
        job = self.service.create_job(plan)
        self.service.run_job(job["jobId"], "org-a", BoundaryAdapter())
        items = self.repo.list_contents(job["jobId"], "org-a")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["nativeMetrics"], {"likes": 12, "comments": 3})

    def test_date_window_uses_inclusive_shanghai_calendar_boundaries(self):
        window = {"start": "2026-07-01", "end": "2026-07-22"}
        self.assertTrue(_within_date_window("2026-06-30T16:00:00Z", window))
        self.assertFalse(_within_date_window("2026-06-30T15:59:59Z", window))
        self.assertTrue(_within_date_window("2026-07-22T15:59:59Z", window))
        self.assertFalse(_within_date_window("2026-07-22T16:00:00Z", window))

    def test_same_platform_content_is_deduplicated_across_query_terms(self):
        class DuplicateAdapter(FakeEvidenceAdapter):
            def search(self, platform, query, page, count, time_range, cursor=""):
                response = super().search(platform, query, page, count, time_range, cursor)
                response["items"][0]["id"] = "same"
                response["items"][0]["platformItemId"] = "same"
                response["items"][0]["text"] = "AUDI E7X 智能座舱 用户讨论"
                return response

        plan = self.plan(platforms=["douyin"], themes=["智能座舱"], scenes=[], issueTerms=[], eventTerms=[], competitors=[])
        job = self.service.create_job(plan)
        self.service.run_job(job["jobId"], "org-a", DuplicateAdapter())
        self.assertEqual(len(self.repo.list_contents(job["jobId"], "org-a")), 1)

    def test_source_role_quota_limits_mart_without_deleting_canonical_evidence(self):
        plan = self.plan(platforms=["douyin"], themes=["智能座舱"], scenes=[], issueTerms=[], eventTerms=[], competitors=[], sampling={"maxPages": 1, "maxItemsPerPlatform": 10, "sourceRoleQuotas": {"user": 1}})
        job = self.service.create_job(plan)
        result = self.service.run_job(job["jobId"], "org-a", FakeEvidenceAdapter())
        self.assertGreater(len(self.repo.list_contents(job["jobId"], "org-a")), 1)
        self.assertEqual(result["mart"]["coverage"]["contentCount"], 1)

    def test_tikhub_adapter_preserves_native_metrics_and_internal_raw_payload(self):
        class Client:
            def search(self, platform, keyword, page, count, time_range, cursor):
                self.args = (platform, keyword, page, count, time_range, cursor)
                return ({"data": [{
                    "aweme_id": "dy-1", "desc": "AUDI E7X 智能座舱",
                    "create_time": 1784599200,
                    "statistics": {"digg_count": 33, "comment_count": 4},
                    "share_info": {"share_url": "https://www.douyin.com/video/dy-1"},
                }]}, {"endpoint": "/douyin/search", "status": 200})

        client = Client()
        result = TikHubEvidenceAdapter(client).search(
            "douyin", "AUDI E7X", 1, 20,
            {"start": "2026-07-01", "end": "2026-07-22"}, "",
        )
        self.assertEqual(result["items"][0]["nativeMetrics"]["likes"], 33)
        self.assertIsNone(result["items"][0]["nativeMetrics"]["views"])
        self.assertEqual(result["items"][0]["platformItemId"], "dy-1")
        self.assertEqual(result["requestMeta"]["endpoint"], "/douyin/search")
        self.assertIn("data", result["raw"])

    def test_tikhub_adapter_fetches_verified_play_count_without_zero_fallback(self):
        class Client:
            def fetch_multi_video_statistics(self, aweme_ids):
                self.ids = aweme_ids
                return ({
                    "data": {
                        "aweme_list": [
                            {"aweme_id": "dy-1", "statistics": {"play_count": 0}},
                            {"aweme_id": "dy-2", "statistics": {"play_count": 9876}},
                            {"aweme_id": "dy-3", "statistics": {}},
                        ]
                    }
                }, {"status": 200})

        client = Client()
        result = TikHubEvidenceAdapter(client).fetch_statistics(["dy-1", "dy-2", "dy-3"])
        self.assertEqual(["dy-1", "dy-2", "dy-3"], client.ids)
        self.assertEqual(0, result["items"]["dy-1"]["views"])
        self.assertEqual(9876, result["items"]["dy-2"]["views"])
        self.assertNotIn("dy-3", result["items"])

    def test_persistent_worker_can_claim_exactly_one_queued_job(self):
        first = self.service.create_job(self.plan())
        second = self.service.create_job(self.plan(projectId="project-2"))
        claimed = self.repo.claim_next_job()
        self.assertEqual(claimed["jobId"], first["jobId"])
        self.assertEqual(claimed["status"], "planning")
        self.assertEqual(self.repo.get_job(second["jobId"], "org-a")["status"], "queued")
        self.assertEqual(self.repo.active_job_count(), 2)

    def test_enterprise_daily_budget_is_checked_before_external_requests(self):
        adapter = FakeEvidenceAdapter()
        job = self.service.create_job(self.plan(platforms=["douyin"], themes=[], scenes=[], issueTerms=[], eventTerms=[], competitors=[]))
        with patch.dict("os.environ", {"MMN_SOCIAL_EVIDENCE_ORG_DAILY_COST_LIMIT": "0"}):
            with self.assertRaises(BudgetExceeded):
                self.service.run_job(job["jobId"], "org-a", adapter)
        self.assertEqual(adapter.calls, [])
        self.assertEqual(self.repo.get_job(job["jobId"], "org-a")["status"], "manual_required")

    def test_request_cache_reuses_sanitized_response_across_jobs(self):
        plan = self.plan(subject={"brand": "上汽奥迪", "model": "AUDI E7X", "aliases": []}, platforms=["douyin"], themes=[], scenes=[], issueTerms=[], eventTerms=[], competitors=[])
        adapter = FakeEvidenceAdapter()
        first = self.service.create_job(plan)
        self.service.run_job(first["jobId"], "org-a", adapter)
        second_plan = self.plan(subject={"brand": "上汽奥迪", "model": "AUDI E7X", "aliases": []}, platforms=["douyin"], themes=[], scenes=[], issueTerms=[], eventTerms=[], competitors=[])
        second = self.service.create_job(second_plan)
        result = self.service.run_job(second["jobId"], "org-a", adapter)
        self.assertEqual(len(adapter.calls), 1)
        self.assertEqual(result["requestCount"], 0)
        self.assertEqual(result["mart"]["coverage"]["contentCount"], 1)


if __name__ == "__main__":
    unittest.main()
