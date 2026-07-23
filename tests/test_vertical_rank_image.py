import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import server


def observation(text, x, y, confidence=1.0):
    return {
        "text": text,
        "x": x,
        "y": y,
        "width": 0.12,
        "height": 0.035,
        "confidence": confidence,
    }


def dongchedi_observations():
    rows = [
        ("ZEEKR 7X", 1, 1),
        ("问界M6", 2, 3),
        ("理想i6", 3, 11),
        ("小鹏MONA L03", 4, 42),
        ("岚图知音", 5, 1),
        ("阿维塔 07", 6, 1),
        ("小米YU7", 7, 16),
        ("理想L6", 8, 18),
        ("Model Y", 9, 25),
        ("小鹏G7", 10, 2),
    ]
    values = [
        observation("懂车帝（*本竞品均剔除的各自本品）", 0.02, 0.88),
        observation("2026-07-13到2026-07-19", 0.20, 0.82),
        observation("竞品", 0.12, 0.75),
        observation("正向排名", 0.40, 0.75),
        observation("反向排名", 0.73, 0.75),
    ]
    for index, (model, positive, negative) in enumerate(rows):
        y = 0.68 - index * 0.072
        values.extend(
            [
                observation(model, 0.06, y, 0.5 if index in {0, 3, 5, 8} else 1.0),
                observation(str(positive), 0.49, y),
                observation(str(negative), 0.82, y),
            ]
        )
    return values


class VerticalRankImageTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "vertical-image.db"
        self.db_patch = patch.object(server, "DB_PATH", self.db_path)
        self.db_patch.start()
        server.init_db()

    def tearDown(self):
        self.db_patch.stop()
        self.tempdir.cleanup()

    def table_counts(self):
        with server.db() as conn:
            return {
                table: conn.execute(f"select count(*) from {table}").fetchone()[0]
                for table in (
                    "vertical_import_batches",
                    "vehicle_assets",
                    "vertical_rank_assets",
                    "vertical_ai_learnings",
                )
            }

    def test_dongchedi_observations_become_a_manual_review_preview(self):
        preview = server.parse_vertical_rank_image_observations(
            dongchedi_observations(),
            "微信图片.png",
            own_model="智己LS6",
        )

        self.assertEqual(preview["platform"], "懂车帝")
        self.assertEqual(preview["periodStart"], "2026-07-13")
        self.assertEqual(preview["periodEnd"], "2026-07-19")
        self.assertEqual(preview["ownModel"], "智己LS6")
        self.assertFalse(preview["ownModelConfirmed"])
        self.assertEqual(len(preview["rows"]), 10)
        self.assertEqual(
            [(row["rawModel"], row["positiveRank"], row["negativeRank"]) for row in preview["rows"]],
            [
                ("ZEEKR 7X", 1, 1),
                ("问界M6", 2, 3),
                ("理想i6", 3, 11),
                ("小鹏MONA L03", 4, 42),
                ("岚图知音", 5, 1),
                ("阿维塔 07", 6, 1),
                ("小米YU7", 7, 16),
                ("理想L6", 8, 18),
                ("Model Y", 9, 25),
                ("小鹏G7", 10, 2),
            ],
        )
        self.assertEqual(preview["status"], "manual_required")

    def test_automotive_home_image_is_rejected_for_this_intake(self):
        observations = copy.deepcopy(dongchedi_observations())
        observations[0]["text"] = "汽车之家"

        with self.assertRaisesRegex(ValueError, "本项目仅采用懂车帝周榜"):
            server.parse_vertical_rank_image_observations(observations, "汽车之家.png")

    def test_complete_weekly_table_requires_manual_platform_confirmation_when_ocr_misses_brand(self):
        observations = copy.deepcopy(dongchedi_observations())
        observations[0]["text"] = "无法可靠识别的平台标题"

        preview = server.parse_vertical_rank_image_observations(
            observations,
            "微信图片.png",
            own_model="智己LS6",
        )

        self.assertEqual(len(preview["rows"]), 10)
        self.assertIn(
            "平台名称未被OCR可靠识别，请对照原图确认仅为懂车帝周榜",
            preview["warnings"],
        )

    def test_incomplete_table_without_platform_name_is_rejected(self):
        observations = copy.deepcopy(dongchedi_observations())
        observations[0]["text"] = "无法可靠识别的平台标题"
        observations = [
            item
            for item in observations
            if not (item["text"] == "小鹏G7" or item["text"] == "10")
        ]

        with self.assertRaisesRegex(ValueError, "未识别为懂车帝周榜"):
            server.parse_vertical_rank_image_observations(observations, "不完整图片.png")

    def test_preview_preserves_formal_vertical_tables(self):
        before = self.table_counts()
        preview = server.create_vertical_rank_image_preview(
            b"\x89PNG\r\n\x1a\nfixture",
            "懂车帝周榜.png",
            own_model="智己LS6",
            org_id="org-a",
            edition="china",
            observations=dongchedi_observations(),
        )
        after = self.table_counts()

        self.assertEqual(after, before)
        self.assertEqual(preview["status"], "manual_required")
        with server.db() as conn:
            review = conn.execute(
                "select status, platform, own_model, evidence_path from vertical_image_reviews where id=?",
                (preview["previewId"],),
            ).fetchone()
        self.assertEqual((review["status"], review["platform"], review["own_model"]), ("draft", "懂车帝", "智己LS6"))
        self.assertTrue(Path(review["evidence_path"]).is_file())

    def test_confirm_is_atomic_and_idempotent(self):
        preview = server.create_vertical_rank_image_preview(
            b"\x89PNG\r\n\x1a\nfixture",
            "懂车帝周榜.png",
            own_model="智己LS6",
            org_id="org-a",
            edition="china",
            observations=dongchedi_observations(),
        )
        payload = {
            "previewId": preview["previewId"],
            "ownModel": "智己LS6",
            "ownModelConfirmed": True,
            "periodStart": "2026-07-13",
            "periodEnd": "2026-07-19",
            "rows": [
                {
                    "rawModel": row["rawModel"],
                    "normalizedModel": "极氪7X" if row["rawModel"] == "ZEEKR 7X" else row["rawModel"].replace("阿维塔 07", "阿维塔07"),
                    "positiveRank": row["positiveRank"],
                    "negativeRank": row["negativeRank"],
                }
                for row in preview["rows"]
            ],
        }

        first = server.confirm_vertical_rank_image_preview(payload, org_id="org-a", edition="china")
        second = server.confirm_vertical_rank_image_preview(payload, org_id="org-a", edition="china")

        self.assertEqual(first["dataset"]["count"], 10)
        self.assertEqual(second["dataset"]["count"], 10)
        with server.db() as conn:
            self.assertEqual(
                conn.execute(
                    "select count(*) from vertical_rank_assets where org_id='org-a' and edition='china'"
                ).fetchone()[0],
                10,
            )
            self.assertEqual(
                conn.execute(
                    "select count(*) from vertical_import_batches where org_id='org-a' and edition='china'"
                ).fetchone()[0],
                1,
            )
            review = conn.execute(
                "select status, corrected_json, confirmed_at from vertical_image_reviews where id=?",
                (preview["previewId"],),
            ).fetchone()
        self.assertEqual(review["status"], "confirmed")
        self.assertTrue(review["corrected_json"])
        self.assertTrue(review["confirmed_at"])

    def test_invalid_confirmation_does_not_write_formal_rows(self):
        preview = server.create_vertical_rank_image_preview(
            b"\x89PNG\r\n\x1a\nfixture",
            "懂车帝周榜.png",
            own_model="智己LS6",
            org_id="org-a",
            edition="china",
            observations=dongchedi_observations(),
        )
        rows = copy.deepcopy(preview["rows"])
        rows[1]["positiveRank"] = 1

        with self.assertRaisesRegex(ValueError, "正向排名不能重复"):
            server.confirm_vertical_rank_image_preview(
                {
                    "previewId": preview["previewId"],
                    "ownModel": "智己LS6",
                    "ownModelConfirmed": True,
                    "periodStart": "2026-07-13",
                    "periodEnd": "2026-07-19",
                    "rows": rows,
                },
                org_id="org-a",
                edition="china",
            )

        self.assertEqual(self.table_counts()["vertical_rank_assets"], 0)

    def test_own_model_requires_explicit_confirmation(self):
        preview = server.create_vertical_rank_image_preview(
            b"\x89PNG\r\n\x1a\nfixture",
            "懂车帝周榜.png",
            own_model="智己LS6",
            org_id="org-a",
            edition="china",
            observations=dongchedi_observations(),
        )
        with self.assertRaisesRegex(ValueError, "请人工确认本品车型"):
            server.confirm_vertical_rank_image_preview(
                {
                    "previewId": preview["previewId"],
                    "ownModel": "智己LS6",
                    "periodStart": "2026-07-13",
                    "periodEnd": "2026-07-19",
                    "rows": preview["rows"],
                },
                org_id="org-a",
                edition="china",
            )
        self.assertEqual(self.table_counts()["vertical_rank_assets"], 0)


if __name__ == "__main__":
    unittest.main()
