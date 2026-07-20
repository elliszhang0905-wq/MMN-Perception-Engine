import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import server
from scripts import sync_mmn_vehicle_assets as vehicle_sync


class CloudDemoReleaseConsistencyTest(unittest.TestCase):
    def test_monthly_vehicle_sync_matches_current_tenant_schema(self):
        conn = sqlite3.connect(":memory:")
        vehicle_sync.ensure_schema(conn)
        rows = [{
            "brand_name": "乐道",
            "model_name": "L60",
            "energy_type": "BEV",
            "brand_id": 1,
            "model_id": 2,
            "fct_name": "乐道",
            "state": 1,
            "spec_count": 1,
        }]
        updated = vehicle_sync.upsert_assets(
            conn,
            rows,
            "2026-07-20T00:00:00+08:00",
            "https://example.invalid/vehicle-tree",
            "fixture-hash",
        )
        repeated = vehicle_sync.upsert_assets(
            conn,
            rows,
            "2026-07-20T01:00:00+08:00",
            "https://example.invalid/vehicle-tree",
            "fixture-hash",
        )
        self.assertEqual(updated, 1)
        self.assertEqual(repeated, 1)
        asset = conn.execute(
            "select org_id, edition, brand_name, model_name, import_count from vehicle_assets"
        ).fetchone()
        identity = conn.execute(
            "select brand_name, normalized_name, canonical_key from model_identity_assets"
        ).fetchone()
        self.assertEqual(asset, ("local", "china", "乐道", "L60", 2))
        self.assertEqual(identity, ("乐道", "乐道L60", "乐道|乐道L60|BEV|"))

    def test_trial_can_run_model_analysis_but_management_defaults_to_admin(self):
        for path in (
            "/api/ai/creator-tags",
            "/api/ai/rag-strategy",
            "/api/ai/fusion-strategy",
            "/api/ai/model-identities",
            "/api/content-capability-kb/script-jobs/job-1/revise",
        ):
            self.assertIsNone(server.cloud_post_required_roles(path), path)
        for path in (
            "/api/import-voice-xlsx",
            "/api/import-vertical-xlsx",
            "/api/blogger-skill/import",
            "/api/group-dashboard/refresh-monthly-sales",
            "/api/policy-intelligence/import-source",
        ):
            self.assertEqual(server.cloud_post_required_roles(path), {"admin"}, path)

    def test_brand_model_rules_require_complete_identity(self):
        expected = {
            "乐道L60": ("乐道", "乐道L60"),
            "银河L6": ("吉利银河", "银河L6"),
            "智己L6": ("智己", "智己L6"),
            "智己LS7": ("智己", "智己LS7"),
        }
        for raw, pair in expected.items():
            identity = server.local_standard_model_identity(raw)
            self.assertEqual((identity["brandName"], identity["modelFamily"]), pair, raw)
            self.assertEqual(server.infer_brand_from_model(raw), pair[0], raw)
        self.assertIsNone(server.local_standard_model_identity("L60"))
        self.assertEqual(server.infer_brand_from_model("L60"), "待人工确认")

    def test_model_output_cannot_reintroduce_bare_l60_brand_pollution(self):
        with tempfile.TemporaryDirectory() as temp_dir, patch.object(server, "DB_PATH", Path(temp_dir) / "identity.db"):
            server.init_db()
            claimed = [{
                "rawName": "L60",
                "normalizedName": "乐道L60",
                "brandName": "乐道",
                "modelFamily": "乐道L60",
                "energyType": "BEV",
                "canonicalKey": "乐道|乐道L60|BEV|",
                "confidence": "high",
            }]
            first = server.normalize_model_identity_records(claimed, source="qwen")
            self.assertEqual(first[0]["brand_name"], "待人工确认")
            self.assertEqual(first[0]["canonical_key"], "待人工确认|L60|UNKNOWN|")
            with server.db() as conn:
                conn.execute(
                    "update model_identity_assets set brand_name='乐道', normalized_name='乐道L60', canonical_key='乐道|乐道L60|BEV|' where raw_name='L60'"
                )
            second = server.normalize_model_identity_records(claimed, source="qwen")
            self.assertEqual(second[0]["brand_name"], "待人工确认")
            with server.db() as conn:
                rows = conn.execute(
                    "select brand_name, normalized_name, canonical_key from model_identity_assets where raw_name='L60'"
                ).fetchall()
            self.assertEqual([tuple(row) for row in rows], [("待人工确认", "L60", "待人工确认|L60|UNKNOWN|")])


if __name__ == "__main__":
    unittest.main()
