from pathlib import Path
import json
import sqlite3
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BrandPenetrationModuleTest(unittest.TestCase):
    def test_navigation_and_page_are_registered(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn('data-page="brandpenetration">品牌传播穿透</button>', html)
        self.assertIn('class="page" id="brandpenetration"', html)
        self.assertIn('src="demo-brand-weekly-radar.html"', html)
        self.assertIn('sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox"', html)
        self.assertIn('brandpenetration:"品牌传播穿透"', app)
        self.assertIn('loadBrandPenetrationSnapshot()', app)

    def test_real_snapshot_is_preserved(self):
        demo = (ROOT / "demo-brand-weekly-radar.html").read_text(encoding="utf-8")
        for brand in ("上汽奥迪", "奔驰", "理想", "蔚来", "问界", "小米"):
            self.assertIn(f"data-brand=\"{brand}\"", demo)
        self.assertIn("LIVE SNAPSHOT", demo)
        self.assertNotIn('<section class="kpis">', demo)
        self.assertIn('id="pulseTrack"', demo)
        self.assertIn("renderPulse(events)", demo)
        self.assertIn("activeEvent=event", demo)
        self.assertNotIn('<article class="panel compare">', demo)
        self.assertNotIn('<footer class="footnote">', demo)
        self.assertNotIn(".slice(0,2).map(([p,n])", demo)
        self.assertIn('id="projectConfigForm"', demo)
        self.assertIn('id="competitorInput"', demo)
        self.assertIn("mmnBrandPenetrationProject", demo)
        self.assertIn("mmn-brand-penetration-project-request", demo)

    def test_canonical_snapshot_contains_unique_validated_records(self):
        conn = sqlite3.connect(ROOT / "data" / "commercial_demo.db")
        row = conn.execute("select result_json from social_trend_snapshots where keyword=? order by created_at desc limit 1", ("上汽奥迪品牌传播穿透",)).fetchone()
        conn.close()
        self.assertIsNotNone(row)
        result = json.loads(row[0])
        items = result["items"]
        self.assertEqual(len(items), 195)
        self.assertEqual(len({item["id"] for item in items}), 195)
        self.assertEqual({platform: sum(item["platform"] == platform for item in items) for platform in ("douyin", "xiaohongshu", "weibo")}, {"douyin": 17, "xiaohongshu": 68, "weibo": 110})
        self.assertTrue(all(item.get("sourceUrl", "").startswith("https://") for item in items))
        glc_records = [item for item in items if item.get("brandName") == "奔驰" and "GLC" in item.get("text", "").upper()]
        glc_launch = [item for item in glc_records if any(signal in item.get("text", "") for signal in ("上市", "发布会", "预售"))]
        self.assertTrue(glc_launch)
        self.assertTrue({item["platform"] for item in glc_records}.issuperset({"weibo", "xiaohongshu"}))


if __name__ == "__main__":
    unittest.main()
