from pathlib import Path
import json
import sqlite3
import unittest

import server


ROOT = Path(__file__).resolve().parents[1]


class BrandPenetrationModuleTest(unittest.TestCase):
    def test_navigation_and_page_are_registered(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn('data-page="brandpenetration">品牌穿透中心</button>', html)
        self.assertIn('class="page" id="brandpenetration"', html)
        self.assertIn('src="demo-brand-weekly-radar.html?', html)
        self.assertIn('sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox"', html)
        self.assertIn('brandpenetration:"品牌穿透中心"', app)
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
        self.assertIn("mmn-brand-penetration-project-config", demo)
        self.assertIn("mmn-brand-penetration-project-request", demo)

    def test_canonical_snapshot_contains_unique_validated_records(self):
        conn = sqlite3.connect(ROOT / "data" / "commercial_demo.db")
        row = conn.execute("select result_json from social_trend_snapshots where keyword=? order by created_at desc limit 1", ("上汽奥迪品牌传播穿透",)).fetchone()
        conn.close()
        self.assertIsNotNone(row)
        result = json.loads(row[0])
        items = result["items"]
        self.assertEqual(len(items), 194)
        self.assertEqual(len({item["id"] for item in items}), 194)
        self.assertEqual({platform: sum(item["platform"] == platform for item in items) for platform in ("douyin", "xiaohongshu", "weibo")}, {"douyin": 17, "xiaohongshu": 68, "weibo": 109})
        self.assertFalse(any(any(signal in item.get("text", "") for signal in ("奔驰卡车", "梅赛德斯奔驰卡车", "ABA6Plus")) for item in items))
        self.assertTrue(all(item.get("sourceUrl", "").startswith("https://") for item in items))
        glc_records = [item for item in items if item.get("brandName") == "奔驰" and "GLC" in item.get("text", "").upper()]
        glc_launch = [item for item in glc_records if any(signal in item.get("text", "") for signal in ("上市", "发布会", "预售"))]
        self.assertTrue(glc_launch)
        self.assertTrue({item["platform"] for item in glc_records}.issuperset({"weibo", "xiaohongshu"}))

    def test_official_snapshot_is_visible_to_logged_in_organizations(self):
        conn = sqlite3.connect(ROOT / "data" / "commercial_demo.db")
        conn.row_factory = sqlite3.Row
        result = server.brand_penetration_snapshot(conn, "customer-org", "china")
        conn.close()
        self.assertEqual(len(result["items"]), 194)

    def test_start_analysis_requests_a_real_parent_action(self):
        demo = (ROOT / "demo-brand-weekly-radar.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("mmn-brand-penetration-project-request',config:projectConfig", demo)
        self.assertIn("runBrandPenetrationProject", app)
        self.assertIn('event.data?.type==="mmn-brand-penetration-project-request"', app)
        self.assertIn('event.source!==frame?.contentWindow', app)
        self.assertIn('Array.isArray(config)', app)

    def test_collection_progress_is_visible_and_uses_async_job_polling(self):
        demo = (ROOT / "demo-brand-weekly-radar.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="projectProgressValue"', demo)
        self.assertIn('id="projectProgressBar"', demo)
        self.assertIn("mmn-brand-penetration-progress", demo)
        self.assertIn('api("/api/social-trends/jobs"', app)
        self.assertIn('/api/social-trends/jobs/${encodeURIComponent(job.jobId)}', app)
        self.assertIn('runToken!==brandPenetrationRunToken', app)
        self.assertIn('采集分析超过15分钟', app)

    def test_pulse_timeline_uses_actual_event_range_instead_of_fixed_thirty_days(self):
        demo = (ROOT / "demo-brand-weekly-radar.html").read_text(encoding="utf-8")
        self.assertIn('id="pulseDates"', demo)
        self.assertIn("const start=pulseDay(nodes[0].date),end=pulseDay(nodes.at(-1).date)", demo)
        self.assertIn("dates.style.gridTemplateColumns=`repeat(${ticks.length},1fr)`", demo)
        self.assertNotIn("start.setDate(start.getDate()-30)", demo)

    def test_brand_filters_follow_current_project_competitors(self):
        demo = (ROOT / "demo-brand-weekly-radar.html").read_text(encoding="utf-8")
        self.assertIn("names=[projectConfig.ownBrand,...projectConfig.competitors]", demo)
        self.assertIn("root.replaceChildren(...filters.map", demo)
        self.assertIn("renderBrandFilters()", demo)

    def test_all_selected_brand_results_are_used_by_the_snapshot(self):
        demo = (ROOT / "demo-brand-weekly-radar.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("function snapshotDisplayItems(result)", demo)
        self.assertIn("function snapshotEvidenceApproved(result)", demo)
        self.assertIn("qa?.legacyEvidence?.status==='aligned'", demo)
        self.assertIn("result?.verifiedComparisonItems||[]", demo)
        self.assertIn("item?.normalizedModel", demo)
        self.assertIn("const items=snapshotDisplayItems(result)", demo)
        self.assertIn("mentionedProjectBrands(text).length>1", demo)
        self.assertIn("item.validatedModelName", demo)
        self.assertIn("function brandPenetrationDisplayItems(result)", app)
        self.assertIn('qa?.legacyEvidence?.status==="aligned"', app)
        self.assertIn("result?.verifiedComparisonItems||[]", app)
        self.assertIn("本轮快照已拦截", demo)
        self.assertIn("function resetPlatformCounts()", demo)
        self.assertIn("'全部平台 · 0条'", demo)
        self.assertIn("function brandPenetrationSnapshotKeyword(config)", app)
        self.assertIn("encodeURIComponent(keyword)", app)
        self.assertIn("条品牌匹配内容", app)

    def test_three_review_brand_and_pairwise_conclusions_are_visible_and_neutral(self):
        demo = (ROOT / "demo-brand-weekly-radar.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn('id="brandDecisionGrid"', demo)
        self.assertIn('id="pairwiseDecisionList"', demo)
        self.assertIn('id="independentReviewStatus"', demo)
        self.assertIn("function renderBrandDecision(decision)", demo)
        self.assertIn("row.status==='aligned'", demo)
        self.assertIn("结论已拦截，不展示推测性建议", demo)
        self.assertIn('centerType:"brand_penetration"', app)
        self.assertIn("analysisOnly:isOfficial", app)
        self.assertIn('snapshotKeyword:isOfficial?"上汽奥迪品牌传播穿透":""', app)
        self.assertNotIn("MMN双模型验证", demo)
        self.assertNotIn("双模型共同证据", demo)

    def test_project_configuration_cannot_be_overwritten_by_a_late_snapshot(self):
        demo = (ROOT / "demo-brand-weekly-radar.html").read_text(encoding="utf-8")
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        config_post = 'postMessage({type:"mmn-brand-penetration-project-config",config},"*")'
        fetch_start = 'const data=await api(`/api/social-trends/latest?keyword='
        self.assertLess(app.index(config_post), app.index(fetch_start))
        self.assertEqual(app.count(config_post), 1)
        self.assertIn("品牌穿透中心</h1>", demo)
        self.assertNotIn("<h1>上汽奥迪与竞品", demo)

    def test_snapshot_query_and_result_are_scoped_to_the_current_brand_set(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("&competitor=${encodeURIComponent(brand)}", app)
        self.assertIn("brandPenetrationResultMatchesProject(result,config)", app)
        self.assertIn("已阻止旧结果覆盖", app)
        self.assertIn("新结果返回前不会继续展示旧项目数据", (ROOT / "demo-brand-weekly-radar.html").read_text(encoding="utf-8"))

    def test_latest_snapshot_can_select_an_exact_project_configuration(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        server.init_social_trend_schema(conn)
        base = {"keyword": "智己", "items": [], "modelComparisons": []}
        conn.execute("insert into social_trend_snapshots values (?, ?, ?, ?, ?, ?, ?, ?)", ("matching", "local", "china", "智己", json.dumps({"timeRange": "7d", "competitors": ["零跑", "问界"]}, ensure_ascii=False), json.dumps(base, ensure_ascii=False), "test", "2026-07-18T10:00:00+00:00"))
        conn.execute("insert into social_trend_snapshots values (?, ?, ?, ?, ?, ?, ?, ?)", ("newer-mismatch", "local", "china", "智己", json.dumps({"timeRange": "7d", "competitors": ["理想", "蔚来"]}, ensure_ascii=False), json.dumps(base, ensure_ascii=False), "test", "2026-07-18T11:00:00+00:00"))
        result = server.latest_social_trend_snapshot(conn, "智己", "local", "china", {"timeRange": "7d", "competitors": ["零跑", "问界"]})
        conn.close()
        self.assertEqual(result["snapshot"]["filters"]["competitors"], ["零跑", "问界"])


if __name__ == "__main__":
    unittest.main()
