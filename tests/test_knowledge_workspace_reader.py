import http.client
import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import knowledge_workspace_reader as reader
import server


class KnowledgeWorkspaceReaderTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "workspace.db"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """create table strategy_knowledge_assets (
                id text primary key, org_id text not null, edition text not null,
                asset_json text not null, source_snapshot_id text,
                created_at text not null, updated_at text not null)"""
            )

    def tearDown(self):
        self.tempdir.cleanup()

    def insert(self, item_id, org, edition, asset, updated="2026-09-08T08:00:00Z", source_snapshot_id=None):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "insert into strategy_knowledge_assets values (?,?,?,?,?,?,?)",
                (item_id, org, edition, json.dumps(asset, ensure_ascii=False), source_snapshot_id,
                 "2026-09-01T08:00:00Z", updated),
            )

    def snapshot(self):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(
                "select id,org_id,edition,asset_json,source_snapshot_id,created_at,updated_at "
                "from strategy_knowledge_assets order by id"
            ).fetchall()

    def test_read_is_logically_immutable_and_projects_only_controlled_fields(self):
        self.insert("shared", "org-a", "china", {
            "title": "真实标题", "body": "真实正文", "type": "方法论",
            "brand": "智己", "metadata": {"module": "NSR"},
            "sourceLabel": "客户资料", "sourceUrl": "https://example.com/source",
            "reviewStatus": "approved", "version": "v9", "mystery": "secret",
        })
        before = self.snapshot()
        payload = reader.read_knowledge_workspace(self.db_path, org_id="org-a", edition="china")
        after = self.snapshot()

        self.assertEqual(before, after)
        self.assertEqual(payload["scope"], "organization")
        self.assertEqual(payload["total"], 1)
        self.assertEqual(payload["items"], [{
            "id": "shared", "title": "真实标题", "body": "真实正文", "type": "方法论",
            "brand": "智己", "module": "NSR", "createdAt": "2026-09-01T08:00:00Z",
            "updatedAt": "2026-09-08T08:00:00Z", "sourceLabel": "客户资料",
            "sourceUrl": "https://example.com/source", "reviewStatus": "unavailable",
            "validity": "unknown",
        }])

    def test_missing_table_is_not_created(self):
        empty = Path(self.tempdir.name) / "empty.db"
        sqlite3.connect(empty).close()
        with self.assertRaises(reader.KnowledgeWorkspaceUnavailable):
            reader.read_knowledge_workspace(empty, org_id="org-a", edition="china")
        with sqlite3.connect(empty) as conn:
            self.assertEqual(conn.execute("select name from sqlite_master where type='table'").fetchall(), [])

    def test_falsy_non_object_metadata_fails_closed(self):
        for index, metadata in enumerate(([], False, 0, "")):
            with self.subTest(metadata=metadata):
                org = f"invalid-{index}"
                self.insert(f"invalid-{index}", org, "china", {
                    "title": "Invalid metadata", "body": "Body", "metadata": metadata,
                })
                with self.assertRaises(reader.KnowledgeWorkspaceDataError):
                    reader.read_knowledge_workspace(self.db_path, org_id=org, edition="china")

    def test_org_edition_search_type_and_pagination_are_consistent(self):
        self.insert("a1", "org-a", "china", {"title": "底盘研究", "body": "滤震结论", "type": "知识结论"}, "2026-09-08T03:00:00Z")
        self.insert("a2", "org-a", "china", {"title": "底盘案例", "body": "用户实测", "type": "案例"}, "2026-09-08T02:00:00Z")
        self.insert("b1", "org-b", "china", {"title": "底盘秘密", "body": "B", "type": "知识结论"})
        self.insert("g1", "org-a", "global", {"title": "底盘海外", "body": "G", "type": "知识结论"})
        result = reader.read_knowledge_workspace(
            self.db_path, org_id="org-a", edition="china", q="底盘", item_type="知识结论", limit=1,
        )
        self.assertEqual([item["id"] for item in result["items"]], ["a1"])
        self.assertEqual((result["total"], result["offset"], result["limit"], result["hasMore"]), (1, 0, 1, False))

    def test_project_assets_are_excluded_and_unknown_type_is_not_invented(self):
        self.insert("top-project", "org-a", "china", {"title": "P", "body": "P", "projectId": "p1", "type": "方法论"})
        self.insert("meta-project", "org-a", "china", {"title": "P2", "body": "P2", "metadata": {"project_id": "p2"}})
        self.insert("snapshot-project", "org-a", "china", {"title": "P3", "body": "P3"}, source_snapshot_id="snapshot-1")
        self.insert("shared", "org-a", "china", {"title": "S", "body": "S", "type": "车型洞察"})
        result = reader.read_knowledge_workspace(self.db_path, org_id="org-a", edition="china")
        self.assertEqual([item["id"] for item in result["items"]], ["shared"])
        self.assertEqual(result["items"][0]["type"], "未分类")

    def test_malformed_project_snapshot_row_cannot_break_shared_view(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "insert into strategy_knowledge_assets values (?,?,?,?,?,?,?)",
                ("bad-project", "org-a", "china", "{", "snapshot-1", "2026-09-01", "2026-09-08"),
            )
        self.insert("shared", "org-a", "china", {"title": "S", "body": "S"})
        result = reader.read_knowledge_workspace(self.db_path, org_id="org-a", edition="china")
        self.assertEqual([item["id"] for item in result["items"]], ["shared"])

    def test_unrecognized_raw_type_can_use_only_explicit_known_knowledge_type(self):
        self.insert("mapped", "org-a", "china", {
            "title": "T", "body": "B", "type": "汽车营销方法论",
            "metadata": {"knowledge_type": "framework"},
        })
        item = reader.read_knowledge_workspace(self.db_path, org_id="org-a", edition="china")["items"][0]
        self.assertEqual(item["type"], "方法论")

    def test_brand_module_filters_and_facets_use_full_shared_scope(self):
        self.insert("one", "org-a", "china", {
            "title": "T1", "body": "B1", "brand": "智己", "metadata": {"module": "NSR"},
        })
        self.insert("two", "org-a", "china", {
            "title": "T2", "body": "B2", "brand": "MG", "metadata": {"module": "内容打法"},
        })
        self.insert("project", "org-a", "china", {
            "title": "P", "body": "P", "brand": "不可见", "metadata": {"module": "X", "project": "p1"},
        })
        result = reader.read_knowledge_workspace(
            self.db_path, org_id="org-a", edition="china", brand="智己", module="NSR",
        )
        self.assertEqual([item["id"] for item in result["items"]], ["one"])
        self.assertEqual(result["total"], 1)
        self.assertEqual(result["facets"], {"brands": ["MG", "智己"], "modules": ["NSR", "内容打法"]})

    def test_malformed_json_fails_closed_instead_of_reporting_partial_success(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "insert into strategy_knowledge_assets values (?,?,?,?,?,?,?)",
                ("bad", "org-a", "china", "{", None, "2026-09-01", "2026-09-08"),
            )
        with self.assertRaises(reader.KnowledgeWorkspaceDataError):
            reader.read_knowledge_workspace(self.db_path, org_id="org-a", edition="china")

    def test_rejects_bad_inputs_and_unsafe_source_url(self):
        self.insert("unsafe", "org-a", "china", {
            "title": "T", "body": "B", "type": "原始材料",
            "sourceUrl": "https://user:password@example.com/private",
        })
        item = reader.read_knowledge_workspace(self.db_path, org_id="org-a", edition="china")["items"][0]
        self.assertIsNone(item["sourceUrl"])
        self.insert("malformed-url", "org-a", "china", {
            "title": "T2", "body": "B2", "sourceUrl": "https://[bad-ipv6/source",
        })
        result = reader.read_knowledge_workspace(self.db_path, org_id="org-a", edition="china")
        self.assertIsNone(next(x for x in result["items"] if x["id"] == "malformed-url")["sourceUrl"])
        self.insert("query-credential", "org-a", "china", {
            "title": "T3", "body": "B3", "sourceLabel": "/Users/alice/private/source.pdf",
            "sourceUrl": "https://example.com/source?token=secret",
        })
        self.insert("fragment-credential", "org-a", "china", {
            "title": "T4", "body": "B4", "sourceUrl": "https://example.com/source#access_token=secret",
        })
        self.insert("signed-or-internal", "org-a", "china", {
            "title": "T5", "body": "B5", "sourceUrl": "https://example.com/source?X-Amz-Signature=secret",
        })
        self.insert("loopback", "org-a", "china", {
            "title": "T6", "body": "B6", "sourceUrl": "http://127.0.0.1/private",
        })
        self.insert("client-secret", "org-a", "china", {
            "title": "T7", "body": "B7", "sourceUrl": "https://example.com/cb?client_secret=secret",
        })
        result = reader.read_knowledge_workspace(self.db_path, org_id="org-a", edition="china")
        self.assertIsNone(next(x for x in result["items"] if x["id"] == "query-credential")["sourceUrl"])
        self.assertIsNone(next(x for x in result["items"] if x["id"] == "query-credential")["sourceLabel"])
        self.assertIsNone(next(x for x in result["items"] if x["id"] == "fragment-credential")["sourceUrl"])
        self.assertIsNone(next(x for x in result["items"] if x["id"] == "signed-or-internal")["sourceUrl"])
        self.assertIsNone(next(x for x in result["items"] if x["id"] == "loopback")["sourceUrl"])
        self.assertIsNone(next(x for x in result["items"] if x["id"] == "client-secret")["sourceUrl"])
        for kwargs in ({"edition": "mars"}, {"item_type": "车型洞察"}, {"limit": 101}, {"offset": -1}):
            args = {"org_id": "org-a", "edition": "china", **kwargs}
            with self.assertRaises(reader.KnowledgeWorkspaceInputError):
                reader.read_knowledge_workspace(self.db_path, **args)

    def test_scan_budget_fails_closed(self):
        self.insert("one", "org-a", "china", {"title": "T", "body": "B"})
        self.insert("two", "org-a", "china", {"title": "T", "body": "B"})
        with patch.object(reader, "MAX_SCAN_ROWS", 1):
            with self.assertRaises(reader.KnowledgeWorkspaceDataError):
                reader.read_knowledge_workspace(self.db_path, org_id="org-a", edition="china")

    def test_connection_is_closed_on_success_and_invalid_row(self):
        original = reader.readonly_connection
        tracked = []

        class ConnectionProxy:
            def __init__(self, connection):
                self.connection = connection
                self.closed = False

            def execute(self, *args, **kwargs):
                return self.connection.execute(*args, **kwargs)

            def close(self):
                self.closed = True
                self.connection.close()

        def connect(path):
            proxy = ConnectionProxy(original(path))
            tracked.append(proxy)
            return proxy

        self.insert("good", "org-a", "china", {"title": "T", "body": "B"})
        with patch.object(reader, "readonly_connection", side_effect=connect):
            reader.read_knowledge_workspace(self.db_path, org_id="org-a", edition="china")
        self.assertTrue(tracked[-1].closed)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("update strategy_knowledge_assets set asset_json='{' where id='good'")
        with patch.object(reader, "readonly_connection", side_effect=connect):
            with self.assertRaises(reader.KnowledgeWorkspaceDataError):
                reader.read_knowledge_workspace(self.db_path, org_id="org-a", edition="china")
        self.assertTrue(tracked[-1].closed)


class KnowledgeWorkspaceHttpTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "http.db"
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                create table organizations(id text primary key,name text,created_at text);
                create table users(id text primary key,org_id text,email text,name text,created_at text);
                create table strategy_knowledge_assets(id text primary key,org_id text,edition text,asset_json text,source_snapshot_id text,created_at text,updated_at text);
                insert into organizations values('org-a','A','2026-09-01');
                insert into users values('user-a','org-a','alice@mmn.local','Alice','2026-09-01');
                insert into strategy_knowledge_assets values('one','org-a','china','{"title":"T","body":"B"}',null,'2026-09-01','2026-09-08');
            """)
        self.patchers = [
            patch.object(server, "DB_PATH", self.db_path),
            patch.object(server, "cloud_login_required", return_value=True),
            patch.object(server, "cloud_accounts", return_value={"Alice": {"org": "A", "role": "admin"}}),
            patch.dict(server.os.environ, {"MMN_AUTH_SECRET": "test-secret-with-at-least-thirty-two-characters"}, clear=False),
            patch.object(server, "ensure_legacy_vertical_claim", side_effect=AssertionError("read endpoint must not claim")),
        ]
        for item in self.patchers:
            item.start()
        self.httpd = server.http.server.ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.httpd.shutdown(); self.httpd.server_close(); self.thread.join(timeout=2)
        for item in reversed(self.patchers):
            item.stop()
        self.tempdir.cleanup()

    def get(self, query="", token=None):
        conn = http.client.HTTPConnection("127.0.0.1", self.httpd.server_port, timeout=3)
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        conn.request("GET", "/api/knowledge-workspace" + query, headers=headers)
        response = conn.getresponse()
        payload = json.loads(response.read().decode())
        status = response.status
        conn.close()
        return status, payload

    def test_requires_login_and_old_token_resolves_scope_without_claim(self):
        status, _ = self.get()
        self.assertEqual(status, 401)
        token = server.make_auth_token("Alice", "admin")
        status, payload = self.get("?edition=china", token)
        self.assertEqual(status, 200)
        self.assertEqual(payload["items"][0]["id"], "one")

    def test_rejects_client_org_and_project_scope(self):
        token = server.make_auth_token("Alice", "admin", "org-a", "user-a")
        self.assertEqual(self.get("?edition=china&org_id=org-b", token)[0], 422)
        self.assertEqual(self.get("?edition=china&projectId=p1", token)[0], 422)

    def test_route_accepts_exact_brand_and_module_filters(self):
        token = server.make_auth_token("Alice", "admin", "org-a", "user-a")
        status, payload = self.get("?edition=china&brand=&module=", token)
        self.assertEqual(status, 200)
        self.assertIn("facets", payload)


if __name__ == "__main__":
    unittest.main()
