import copy
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import server


VERTICAL_TABLES = (
    "vertical_import_batches",
    "vehicle_assets",
    "vertical_rank_assets",
    "vertical_ai_learnings",
)


def vertical_fixture(share=0.12):
    return {
        "platform": "汽车之家",
        "periods": ["7.2-7.8"],
        "models": ["奥迪E7X", "小米YU7"],
        "items": [
            {
                "platform": "汽车之家",
                "period": "7.2-7.8",
                "ownModel": "奥迪E7X",
                "competitor": "小米YU7",
                "positiveRank": 1,
                "negativeRank": 2,
                "share": share,
                "sheet": "7.2-7.8",
                "parseMode": "fixture",
            }
        ],
    }


class TenantDataIsolationTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "tenant.db"
        self.db_patch = patch.object(server, "DB_PATH", self.db_path)
        self.db_patch.start()
        server.init_db()
        with server.OPPORTUNITY_JOB_LOCK:
            self.previous_jobs = dict(server.OPPORTUNITY_JOB_TASKS)
            server.OPPORTUNITY_JOB_TASKS.clear()

    def tearDown(self):
        with server.OPPORTUNITY_JOB_LOCK:
            server.OPPORTUNITY_JOB_TASKS.clear()
            server.OPPORTUNITY_JOB_TASKS.update(self.previous_jobs)
        self.db_patch.stop()
        self.tempdir.cleanup()

    def test_cloud_scope_and_token_bind_to_the_most_active_matching_org(self):
        with server.db() as conn:
            conn.executemany(
                "insert into organizations values (?,?,?)",
                [
                    ("org-old", "MMN管理空间", "2026-01-01T00:00:00Z"),
                    ("org-active", "MMN管理空间", "2026-02-01T00:00:00Z"),
                ],
            )
            conn.executemany(
                "insert into users values (?,?,?,?,?)",
                [
                    ("user-old", "org-old", "ellis@mmn.local", "Ellis", "2026-01-01T00:00:00Z"),
                    ("user-active", "org-active", "ellis@mmn.local", "Ellis", "2026-02-01T00:00:00Z"),
                ],
            )
            for index in range(2):
                conn.execute(
                    """insert into strategy_knowledge_assets
                    (id, org_id, edition, asset_json, source_snapshot_id, created_at, updated_at)
                    values (?, ?, 'china', '{}', null, ?, ?)""",
                    (f"asset-{index}", "org-active", f"2026-03-0{index + 1}T00:00:00Z", f"2026-03-0{index + 1}T00:00:00Z"),
                )

        with patch.object(
            server,
            "cloud_accounts",
            return_value={"Ellis": {"org": "MMN管理空间", "role": "admin"}},
        ):
            scope = server.resolve_cloud_auth_scope("Ellis")

        self.assertEqual(scope["org_id"], "org-active")
        self.assertEqual(scope["user_id"], "user-active")
        token = server.make_auth_token("Ellis", "admin", scope["org_id"], scope["user_id"])
        payload = server.parse_auth_token(token)
        self.assertEqual(payload["org_id"], "org-active")
        self.assertEqual(payload["user_id"], "user-active")

    def test_vertical_assets_are_isolated_by_org_and_edition(self):
        server.remember_vertical_dataset(
            b"same-source",
            "weekly.xlsx",
            copy.deepcopy(vertical_fixture(0.11)),
            org_id="org-a",
            edition="china",
        )
        server.remember_vertical_dataset(
            b"same-source",
            "weekly.xlsx",
            copy.deepcopy(vertical_fixture(0.22)),
            org_id="org-b",
            edition="china",
        )
        server.remember_vertical_dataset(
            b"same-source",
            "weekly.xlsx",
            copy.deepcopy(vertical_fixture(0.33)),
            org_id="org-a",
            edition="global",
        )

        org_a_china = server.vertical_assets_payload("汽车之家", org_id="org-a", edition="china")
        org_b_china = server.vertical_assets_payload("汽车之家", org_id="org-b", edition="china")
        org_a_global = server.vertical_assets_payload("汽车之家", org_id="org-a", edition="global")
        missing = server.vertical_assets_payload("汽车之家", org_id="org-c", edition="china")

        self.assertEqual([item["share"] for item in org_a_china["items"]], [0.11])
        self.assertEqual([item["share"] for item in org_b_china["items"]], [0.22])
        self.assertEqual([item["share"] for item in org_a_global["items"]], [0.33])
        self.assertEqual(missing["items"], [])
        self.assertEqual(missing["assetSummary"]["relationCount"], 0)

    def test_opportunity_job_cannot_be_read_from_another_org(self):
        with server.OPPORTUNITY_JOB_LOCK:
            server.OPPORTUNITY_JOB_TASKS["job-a"] = {
                "jobId": "job-a",
                "status": "running",
                "_org_id": "org-a",
                "_user_id": "user-a",
                "_started_monotonic": time.monotonic(),
            }

        own = server.get_opportunity_map_job("job-a", "org-a")
        other = server.get_opportunity_map_job("job-a", "org-b")

        self.assertEqual(own["jobId"], "job-a")
        self.assertNotIn("_org_id", own)
        self.assertNotIn("_user_id", own)
        self.assertIsNone(other)


class VerticalScopeMigrationTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "legacy.db"
        self.db_patch = patch.object(server, "DB_PATH", self.db_path)
        self.db_patch.start()

    def tearDown(self):
        self.db_patch.stop()
        self.tempdir.cleanup()

    def create_legacy_vertical_schema(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript(
            """
            create table vertical_import_batches (
                id text primary key, platform text not null, filename text not null, file_hash text not null,
                periods_json text not null, model_count integer not null default 0, item_count integer not null default 0,
                imported_at text not null, parser_version text not null, unique(platform, file_hash)
            );
            create table vehicle_assets (
                id text primary key, platform text not null, brand_name text, model_name text not null,
                first_seen_at text not null, last_seen_at text not null, first_source text, last_source text,
                period_first text, period_last text, import_count integer not null default 1,
                extra_json text not null default '{}', unique(platform, model_name)
            );
            create table vertical_rank_assets (
                id text primary key, platform text not null, period text not null, own_model text not null,
                competitor_model text not null, positive_rank integer, negative_rank integer, compare_share real,
                source_file text not null, file_hash text not null, sheet text, parse_mode text,
                first_seen_at text not null, updated_at text not null,
                unique(platform, period, own_model, competitor_model)
            );
            create unique index idx_vertical_rank_assets_unique
            on vertical_rank_assets(platform, period, own_model, competitor_model);
            create unique index idx_vehicle_assets_unique on vehicle_assets(platform, model_name);
            create table vertical_ai_learnings (
                id text primary key, platform text not null, model_name text not null, period text,
                source_file text, summary_text text not null, knowledge_json text not null, created_at text not null,
                unique(platform, model_name, period)
            );
            insert into vertical_import_batches values
                ('batch-1','汽车之家','weekly.xlsx','hash-1','["7.2-7.8"]',2,1,'2026-07-12T00:00:00Z','v2');
            insert into vehicle_assets values
                ('vehicle-1','汽车之家','奥迪','奥迪E7X','2026-07-12T00:00:00Z','2026-07-12T00:00:00Z',
                 'weekly.xlsx','weekly.xlsx','7.2-7.8','7.2-7.8',1,'{}');
            insert into vertical_rank_assets values
                ('rank-1','汽车之家','7.2-7.8','奥迪E7X','小米YU7',1,2,0.12,'weekly.xlsx','hash-1',
                 '7.2-7.8','fixture','2026-07-12T00:00:00Z','2026-07-12T00:00:00Z');
            insert into vertical_ai_learnings values
                ('learning-1','汽车之家','奥迪E7X','7.2-7.8','weekly.xlsx','结论','{}','2026-07-12T00:00:00Z');
            """
        )
        conn.commit()
        conn.close()

    def test_init_db_migrates_legacy_vertical_rows_without_loss(self):
        self.create_legacy_vertical_schema()

        server.init_db()

        with server.db() as conn:
            for table in VERTICAL_TABLES:
                columns = {row["name"] for row in conn.execute(f"pragma table_info({table})")}
                self.assertTrue({"org_id", "edition"}.issubset(columns), table)
                row = conn.execute(f"select org_id, edition from {table}").fetchone()
                self.assertEqual((row["org_id"], row["edition"]), ("local", "china"), table)
                legacy = conn.execute(
                    "select name from sqlite_master where type='table' and name=?",
                    (f"{table}_legacy_scope",),
                ).fetchone()
                self.assertIsNone(legacy, table)

            indexes = {
                row["name"]: row["sql"]
                for row in conn.execute(
                    "select name, sql from sqlite_master where type='index' and name in (?, ?)",
                    ("idx_vertical_rank_assets_unique", "idx_vehicle_assets_unique"),
                )
            }
            self.assertIn("org_id", indexes["idx_vertical_rank_assets_unique"])
            self.assertIn("edition", indexes["idx_vertical_rank_assets_unique"])
            self.assertIn("org_id", indexes["idx_vehicle_assets_unique"])
            self.assertIn("edition", indexes["idx_vehicle_assets_unique"])

    def test_legacy_rows_are_claimed_once_by_the_known_admin_org(self):
        self.create_legacy_vertical_schema()
        server.init_db()

        with server.db() as conn:
            first = server.claim_legacy_vertical_scope(conn, "org-admin")
            second = server.claim_legacy_vertical_scope(conn, "org-other")
            scopes = {
                table: conn.execute(f"select distinct org_id from {table}").fetchone()[0]
                for table in VERTICAL_TABLES
            }

        self.assertTrue(first["claimed"])
        self.assertEqual(first["targetOrgId"], "org-admin")
        self.assertFalse(second["claimed"])
        self.assertEqual(set(scopes.values()), {"org-admin"})

    def test_init_db_repairs_a_partially_scoped_vertical_schema(self):
        server.init_db()
        with server.db() as conn:
            conn.execute("drop index if exists idx_vehicle_assets_unique")
            conn.execute("drop table vehicle_assets")
            conn.executescript(
                """
                create table vehicle_assets (
                    id text primary key, platform text not null, brand_name text, model_name text not null,
                    first_seen_at text not null, last_seen_at text not null, first_source text, last_source text,
                    period_first text, period_last text, import_count integer not null default 1,
                    extra_json text not null default '{}', unique(platform, model_name)
                );
                insert into vehicle_assets values
                    ('vehicle-partial','汽车之家','奥迪','奥迪E7X','2026-07-12T00:00:00Z',
                     '2026-07-12T00:00:00Z','weekly.xlsx','weekly.xlsx','7.2-7.8','7.2-7.8',1,'{}');
                """
            )

        server.init_db()

        with server.db() as conn:
            columns = {row["name"] for row in conn.execute("pragma table_info(vehicle_assets)")}
            row = conn.execute("select org_id, edition, model_name from vehicle_assets").fetchone()
        self.assertTrue({"org_id", "edition"}.issubset(columns))
        self.assertEqual((row["org_id"], row["edition"], row["model_name"]), ("local", "china", "奥迪E7X"))

    def test_existing_admin_token_enrichment_claims_legacy_rows_without_relogin(self):
        self.create_legacy_vertical_schema()
        server.init_db()
        with server.db() as conn:
            conn.execute(
                "insert into organizations values (?,?,?)",
                ("org-admin", "MMN管理空间", "2026-07-12T00:00:00Z"),
            )
            conn.execute(
                "insert into users values (?,?,?,?,?)",
                ("user-admin", "org-admin", "ellis@mmn.local", "Ellis", "2026-07-12T00:00:00Z"),
            )
        old_token = server.make_auth_token("Ellis", "admin")
        request = SimpleNamespace(headers={"Authorization": f"Bearer {old_token}"})

        with patch.object(
            server,
            "cloud_accounts",
            return_value={"Ellis": {"org": "MMN管理空间", "role": "admin"}},
        ):
            payload = server.Handler.current_auth(request)
            again = server.Handler.current_auth(request)

        with server.db() as conn:
            scopes = {
                table: conn.execute(f"select distinct org_id from {table}").fetchone()[0]
                for table in VERTICAL_TABLES
            }
        self.assertEqual((payload["org_id"], payload["user_id"]), ("org-admin", "user-admin"))
        self.assertEqual((again["org_id"], again["user_id"]), ("org-admin", "user-admin"))
        self.assertEqual(set(scopes.values()), {"org-admin"})


if __name__ == "__main__":
    unittest.main()
