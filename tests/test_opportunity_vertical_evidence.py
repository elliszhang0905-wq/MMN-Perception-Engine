import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import server


class OpportunityVerticalEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.original_db_path = server.DB_PATH
        self.tempdir = tempfile.TemporaryDirectory()
        server.DB_PATH = Path(self.tempdir.name) / "opportunity-vertical-evidence.db"
        server.init_db()
        with server.db() as conn:
            conn.executemany(
                """insert into vertical_rank_assets
                (id, platform, period, own_model, competitor_model, positive_rank, negative_rank,
                 compare_share, source_file, file_hash, sheet, parse_mode, first_seen_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    ("ah-old", "汽车之家", "2026-05", "本品车型", "竞品A", 3, 8, .22, "autohome-may.xlsx", "a", "排名", "test", "2026-05-01T00:00:00Z", "2026-05-01T00:00:00Z"),
                    ("ah-new", "汽车之家", "2026-06", "本品车型", "竞品A", 1, 5, .34, "autohome-june.xlsx", "b", "排名", "test", "2026-06-01T00:00:00Z", "2026-06-01T00:00:00Z"),
                    ("dcd-new", "懂车帝", "2026-06", "本品车型", "竞品A", 2, 7, .29, "dcd-june.xlsx", "c", "排名", "test", "2026-06-01T00:00:00Z", "2026-06-01T00:00:00Z"),
                    ("missing-share", "汽车之家", "2026-06", "本品车型", "竞品C", 4, 9, None, "autohome-june.xlsx", "e", "排名", "test", "2026-06-01T00:00:00Z", "2026-06-01T00:00:00Z"),
                    ("other", "汽车之家", "2026-06", "其他本品", "竞品A", 1, 1, .5, "other.xlsx", "d", "排名", "test", "2026-06-01T00:00:00Z", "2026-06-01T00:00:00Z"),
                ],
            )

    def tearDown(self):
        server.DB_PATH = self.original_db_path
        self.tempdir.cleanup()

    def test_uses_only_latest_relevant_vertical_relationship_per_platform(self):
        evidence = server.build_opportunity_vertical_evidence("本品车型", ["竞品A", "竞品B"])

        self.assertEqual(len(evidence), 2)
        self.assertEqual({item["platform"] for item in evidence}, {"汽车之家", "懂车帝"})
        autohome = next(item for item in evidence if item["platform"] == "汽车之家")
        self.assertEqual(autohome["period"], "2026-06")
        self.assertEqual(autohome["competitor"], "竞品A")
        self.assertEqual(autohome["source_type"], "vertical_media")
        self.assertIn("正向第 1", autohome["claim"])
        self.assertIn("反向第 5", autohome["claim"])

    def test_model_packet_exposes_vertical_evidence_as_relation_support_only(self):
        vertical = [{"id": "vertical-1", "platform": "汽车之家", "competitor": "竞品A", "claim": "汽车之家 2026-06：本品车型 对比 竞品A，正向第 1，反向第 5。"}]
        with patch.object(server, "qwen_config", return_value={"configured": True}), patch.object(server, "call_qwen", return_value='{"items": []}') as call:
            items, mode, error = server._opportunity_model_analysis(
                "qwen",
                {"own": {}, "marketSignals": [], "competitorSources": [], "competitorFacts": [], "verticalEvidence": vertical},
                [],
            )

        self.assertEqual((items, mode, error), ([], "model", ""))
        prompt = call.call_args.args[0]
        self.assertIn("不能单独推导某个产品属性", prompt[0]["content"])
        self.assertEqual(prompt[1]["content"].count("垂媒正反向交叉验证"), 1)
        self.assertIn("vertical-1", prompt[1]["content"])

    def test_missing_compare_share_is_not_fabricated_as_zero_percent(self):
        evidence = server.build_opportunity_vertical_evidence("本品车型", ["竞品C"])

        self.assertEqual(len(evidence), 1)
        self.assertIsNone(evidence[0]["payload"]["compareShare"])
        self.assertIn("对比占比 未提供", evidence[0]["claim"])
        self.assertNotIn("0.0%", evidence[0]["claim"])


if __name__ == "__main__":
    unittest.main()
