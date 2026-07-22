import os
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import server
from social_evidence import SocialEvidenceRepository


class Adapter:
    def search(self, platform, query, page, count, time_range, cursor=""):
        return {
            "items": [{
                "id": "one", "platformItemId": "one", "platform": platform,
                "sourceUrl": "https://example.test/one", "text": f"{query} 用户公开讨论",
                "publishedAt": "2026-07-21T00:00:00+00:00", "nativeMetrics": {"likes": 1},
                "sourceRole": "user",
            }],
            "nextCursor": "", "requestMeta": {"endpoint": "/search", "status": 200, "cost": 1},
            "raw": {"data": [{"id": "one"}]},
        }


class SocialEvidenceV2ApiTest(unittest.TestCase):
    def payload(self):
        return {
            "projectId": "p1", "centerType": "social_trend",
            "subject": {"brand": "上汽奥迪", "model": "AUDI E7X", "aliases": []},
            "competitors": [], "themes": [], "scenes": [], "issueTerms": [], "eventTerms": [],
            "exclusionTerms": [], "platforms": ["douyin"],
            "dateWindow": {"start": "2026-07-01", "end": "2026-07-22"},
            "sampling": {"maxPages": 1, "maxItemsPerPlatform": 10},
            "budget": {"maxRequests": 5, "maxEstimatedCost": 5},
        }

    def test_feature_flag_is_disabled_by_default_and_explicitly_enabled(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("MMN_SOCIAL_EVIDENCE_V2_ENABLED", None)
            self.assertFalse(server.social_evidence_v2_enabled())
        with patch.dict(os.environ, {"MMN_SOCIAL_EVIDENCE_V2_ENABLED": "true"}):
            self.assertTrue(server.social_evidence_v2_enabled())

    def test_sync_execution_returns_tenant_scoped_persistent_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SocialEvidenceRepository(Path(tmp) / "evidence.sqlite", Path(tmp) / "raw")
            job = server.start_social_evidence_v2_job(
                self.payload(), org_id="org-a", edition="china", repository=repo,
                adapter=Adapter(), async_mode=False,
            )
            self.assertEqual(job["status"], "ready")
            self.assertEqual(job["orgId"], "org-a")
            self.assertIsNone(repo.get_job(job["jobId"], "org-b"))

    def test_server_registers_v2_job_and_mart_routes(self):
        source = Path(server.__file__).read_text(encoding="utf-8")
        self.assertIn('"/api/social-evidence/jobs"', source)
        self.assertIn(r'/api/social-evidence/jobs/([^/]+)', source)
        self.assertIn('"/api/social-evidence/marts/latest"', source)
        self.assertIn('"/api/social-evidence/query-plans/preview"', source)
        self.assertIn('"/api/social-evidence/nsr-context"', source)
        self.assertIn(r'/api/social-evidence/jobs/([^/]+)/retry', source)

    def test_public_job_does_not_expose_internal_supplier_error(self):
        public = server.public_social_evidence_job({
            "jobId": "j1", "status": "degraded", "message": "部分平台暂时不可用",
            "error": "TikHub HTTP 500 /api/private", "_private": "secret",
        })
        self.assertNotIn("error", public)
        self.assertNotIn("_private", public)
        self.assertNotIn("TikHub", str(public))

    def test_capabilities_are_neutral_and_expose_worker_mode(self):
        with patch.dict(os.environ, {
            "MMN_SOCIAL_EVIDENCE_V2_ENABLED": "true",
            "MMN_SOCIAL_EVIDENCE_WORKER_MODE": "external",
        }):
            capabilities = server.social_evidence_capabilities()
        self.assertEqual(capabilities, {
            "enabled": True,
            "clientEnabled": True,
            "shadowMode": False,
            "workerMode": "external",
            "supportedCenters": ["brand_penetration", "nsr_validation", "social_trend"],
            "schemaVersion": "social-evidence-query-v2",
        })
        self.assertNotIn("TikHub", str(capabilities))

    def test_nsr_resolver_uses_latest_same_model_snapshot_and_preserves_source_identity(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "business.sqlite"):
            with sqlite3.connect(server.DB_PATH) as conn:
                conn.execute("""create table project_snapshots (
                    id text primary key, org_id text, user_id text, edition text, brand text,
                    model text, project text, data_version text, payload_json text, created_at text)""")
                payload = {"state": {
                    "config": {"brand": "上汽奥迪", "model": "AUDI E7X"},
                    "rows": [
                        ["AUDI E7X", "", "懂车帝", "智能", "智能座舱", "", "", "", "", 5, "", "", "", "", 0.71],
                        ["AUDI E7X", "", "小红书", "豪华", "豪华感", "", "", "", "", 4, "", "", "", "", 0.64],
                        ["理想L9", "", "懂车帝", "智能", "智能座舱", "", "", "", "", 5, "", "", "", "", 0.82],
                    ],
                }, "importQuality": {"attributeNsrSources": ["懂车帝", "小红书"]}}
                conn.execute("insert into project_snapshots values (?,?,?,?,?,?,?,?,?,?)", (
                    "snap-e7x", "org-a", "u1", "china", "上汽奥迪", "AUDI E7X", "E7X项目",
                    "dataset-real-1", json.dumps(payload, ensure_ascii=False), "2026-07-23T08:00:00+00:00",
                ))
            resolved = server.resolve_vehicle_nsr_validation_context("AUDI E7X", "org-a", "china")
            plan = server.preview_social_evidence_query_plan({
                "projectId": "p-nsr", "centerType": "nsr_validation",
                "subject": {"model": "AUDI E7X"}, "vehicleContext": {"model": "AUDI E7X"},
                "validationTargets": [{**resolved["validationTargets"][0], "baselineNsr": -1}],
                "competitors": [], "platforms": ["douyin"],
                "dateWindow": {"start": "2026-07-17", "end": "2026-07-23"},
                "sampling": {"maxPages": 1, "pageSize": 20},
                "budget": {"maxRequests": 3, "maxEstimatedCost": 3},
            }, "org-a", "china")
            with self.assertRaises(server.StaleNsrSource):
                server.preview_social_evidence_query_plan({
                    "projectId": "p-nsr", "centerType": "nsr_validation",
                    "subject": {"model": "AUDI E7X"}, "vehicleContext": {"model": "AUDI E7X"},
                    "nsrSource": {"fingerprint": "sha256:stale"},
                    "platforms": ["douyin"], "competitors": [],
                    "dateWindow": {"start": "2026-07-17", "end": "2026-07-23"},
                }, "org-a", "china")
        self.assertEqual(resolved["vehicleContext"]["contextVersion"], "snap-e7x")
        self.assertEqual(resolved["nsrSource"]["datasetVersion"], "dataset-real-1")
        self.assertEqual({row["label"] for row in resolved["validationTargets"]}, {"智能座舱", "豪华感"})
        self.assertTrue(all(row["baselineNsr"] != 0.82 for row in resolved["validationTargets"]))
        self.assertTrue(resolved["nsrSource"]["fingerprint"].startswith("sha256:"))
        self.assertNotEqual(plan["validationTargets"][0]["baselineNsr"], -1)

    def test_shadow_mode_keeps_backend_available_without_switching_client(self):
        with patch.dict(os.environ, {
            "MMN_SOCIAL_EVIDENCE_V2_ENABLED": "true",
            "MMN_SOCIAL_EVIDENCE_SHADOW_MODE": "true",
        }):
            capabilities = server.social_evidence_capabilities()
        self.assertTrue(capabilities["enabled"])
        self.assertTrue(capabilities["shadowMode"])
        self.assertFalse(capabilities["clientEnabled"])

    def test_nsr_adjudication_is_tenant_scoped_and_rejects_foreign_evidence(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "business.sqlite"):
            repo = SocialEvidenceRepository(Path(tmp) / "evidence.sqlite", Path(tmp) / "raw")
            mart = {
                "martId": "mart-1", "jobId": "job-1", "martType": "nsr_validation",
                "schemaVersion": "nsr-validation-mart-v1", "targetValidations": [{
                    "targetId": "target-1", "evidence": [{"evidenceId": "evidence-1"}],
                }],
            }
            with repo.connect() as conn:
                conn.execute("insert into evidence_marts values (?,?,?,?,?,?,?,?,?)", (
                    "mart-1", "job-1", "org-a", "china", "p1", "nsr_validation",
                    "nsr-validation-mart-v1", json.dumps(mart, ensure_ascii=False), "2026-07-23T09:00:00+00:00",
                ))
            saved = server.save_nsr_validation_adjudication(
                "mart-1", {"targetId": "target-1", "decision": "supported", "reason": "原文一致", "evidenceIds": ["evidence-1"]},
                org_id="org-a", user_id="ellis", repository=repo,
            )
            self.assertEqual(saved["decision"], "supported")
            with self.assertRaisesRegex(ValueError, "至少需要一条"):
                server.save_nsr_validation_adjudication(
                    "mart-1", {"targetId": "target-1", "decision": "supported", "reason": "没有原文", "evidenceIds": []},
                    org_id="org-a", user_id="ellis", repository=repo,
                )
            with self.assertRaisesRegex(KeyError, "不存在"):
                server.get_nsr_validation_mart("mart-1", "org-b", repo)
            with self.assertRaisesRegex(ValueError, "不属于"):
                server.save_nsr_validation_adjudication(
                    "mart-1", {"targetId": "target-1", "decision": "supported", "reason": "错误证据", "evidenceIds": ["foreign"]},
                    org_id="org-a", user_id="ellis", repository=repo,
                )

    def test_only_supported_nsr_adjudication_enters_new_decision_surface(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(server, "DB_PATH", Path(tmp) / "business.sqlite"):
            server.init_db()
            repo = SocialEvidenceRepository(Path(tmp) / "evidence.sqlite", Path(tmp) / "raw")
            mart = {
                "martId": "mart-decision", "jobId": "job-1", "martType": "nsr_validation",
                "schemaVersion": "nsr-validation-mart-v1", "vehicleContext": {"model": "AUDI E7X"},
                "nsrSource": {"datasetVersion": "real-1", "fingerprint": "sha256:one"},
                "queryScope": {"dateWindow": {"start": "2026-07-17", "end": "2026-07-23"}},
                "targetValidations": [
                    {"targetId": "supported", "label": "智能座舱", "evidenceCount": 2,
                     "evidence": [{"evidenceId": "ev-1"}]},
                    {"targetId": "mixed", "label": "豪华感", "evidenceCount": 1,
                     "evidence": [{"evidenceId": "ev-2"}]},
                ],
            }
            with repo.connect() as conn:
                conn.execute("insert into evidence_marts values (?,?,?,?,?,?,?,?,?)", (
                    "mart-decision", "job-1", "org-a", "china", "nsr_validation:china:AUDI E7X",
                    "nsr_validation", "nsr-validation-mart-v1", json.dumps(mart, ensure_ascii=False),
                    "2026-07-23T09:00:00+00:00",
                ))
            with patch.object(server, "SOCIAL_EVIDENCE_REPOSITORY", repo):
                server.save_nsr_validation_adjudication(
                    "mart-decision", {"targetId": "supported", "decision": "supported", "reason": "原文支持", "evidenceIds": ["ev-1"]},
                    org_id="org-a", user_id="ellis", repository=repo,
                )
                server.save_nsr_validation_adjudication(
                    "mart-decision", {"targetId": "mixed", "decision": "mixed", "reason": "正反并存", "evidenceIds": ["ev-2"]},
                    org_id="org-a", user_id="ellis", repository=repo,
                )
                inputs = server.vehicle_decision_surface_inputs("AUDI E7X", "org-a", "china")
        conclusions = " ".join(item["conclusion"] for item in inputs["product_voice"])
        self.assertIn("智能座舱", conclusions)
        self.assertNotIn("豪华感", conclusions)
        accepted = next(item for item in inputs["product_voice"] if "智能座舱" in item["conclusion"])
        self.assertIn("SOCIAL_MART:mart-decision", accepted["evidenceIds"])
        self.assertIn("ev-1", accepted["evidenceIds"])

    def test_external_worker_mode_leaves_async_job_in_persistent_queue(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {
            "MMN_SOCIAL_EVIDENCE_WORKER_MODE": "external",
        }):
            repo = SocialEvidenceRepository(Path(tmp) / "evidence.sqlite", Path(tmp) / "raw")
            job = server.start_social_evidence_v2_job(
                self.payload(), org_id="org-a", edition="china", repository=repo,
                adapter=Adapter(), async_mode=True,
            )
        self.assertEqual(job["status"], "queued")
        self.assertEqual(job["stage"], "awaiting_worker")

    def test_retry_creates_a_new_job_from_the_frozen_query_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = SocialEvidenceRepository(Path(tmp) / "evidence.sqlite", Path(tmp) / "raw")
            prior = server.start_social_evidence_v2_job(
                self.payload(), org_id="org-a", edition="china", repository=repo,
                adapter=Adapter(), async_mode=False,
            )
            repo.update_job(prior["jobId"], "org-a", status="degraded", stage="recovery", retryable=True)
            retried = server.retry_social_evidence_v2_job(
                prior["jobId"], org_id="org-a", repository=repo,
                adapter=Adapter(), async_mode=False,
            )
            prior_plan = repo.get_plan(prior["planId"], "org-a")
            retried_plan = repo.get_plan(retried["planId"], "org-a")
        self.assertNotEqual(retried["jobId"], prior["jobId"])
        self.assertEqual(retried["status"], "ready")
        self.assertEqual(retried_plan["fingerprint"], prior_plan["fingerprint"])
        self.assertEqual(retried_plan["queries"], prior_plan["queries"])
        self.assertIsNone(server.cloud_post_required_roles(f'/api/social-evidence/jobs/{prior["jobId"]}/retry'))


if __name__ == "__main__":
    unittest.main()
