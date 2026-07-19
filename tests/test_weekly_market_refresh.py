import json
import tempfile
import unittest
from pathlib import Path

from weekly_market_refresh import (
    fetch_latest_official_market_payload,
    load_weekly_market_snapshot,
    refresh_weekly_market_snapshot,
)


BASELINE = {
    "facts": [
        {"id": "retail", "label": "乘用车零售", "value": 44.3, "unit": "万辆", "yoy": -0.15},
        {"id": "wholesale", "label": "乘用车厂商批发", "value": 37.9, "unit": "万辆", "yoy": -0.26},
        {"id": "nev_retail", "label": "新能源零售", "value": 28.0, "unit": "万辆", "yoy": -0.08},
        {"id": "nev_penetration", "label": "新能源零售渗透率", "value": 63.1, "unit": "%"},
    ],
    "source": {
        "label": "官方周报《车市扫描（2026年7月6日—7月12日）》",
        "url": "https://example.com/week-1",
        "period": "2026年7月1—12日",
        "naturalWeekEndDate": "2026-07-12",
    },
}


class WeeklyMarketRefreshTests(unittest.TestCase):
    def test_valid_batch_is_published_atomically(self):
        payload = json.loads(json.dumps(BASELINE, ensure_ascii=False))
        payload["facts"][0]["value"] = 51.0
        payload["source"] = {"label": "官方周报", "url": "https://example.com/week-2", "period": "2026年7月13—19日"}
        with tempfile.TemporaryDirectory() as directory:
            status = refresh_weekly_market_snapshot(directory, payload=payload, today=__import__("datetime").date(2026, 7, 13))
            snapshot, refresh = load_weekly_market_snapshot(directory, BASELINE)
        self.assertEqual(status["status"], "published")
        self.assertEqual(snapshot["source"]["period"], "2026年7月13—19日")
        self.assertEqual(snapshot["facts"][0]["value"], 51.0)
        self.assertEqual(refresh["batchId"], snapshot["batchId"])
        self.assertEqual(refresh["scope"], ["topKpis", "executiveBrief", "groupImplications", "raceEnvironment"])

    def test_incomplete_batch_never_overwrites_last_published_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            refresh_weekly_market_snapshot(directory, payload=BASELINE)
            invalid = {"facts": BASELINE["facts"][:-1], "source": BASELINE["source"]}
            status = refresh_weekly_market_snapshot(directory, payload=invalid)
            snapshot, refresh = load_weekly_market_snapshot(directory, BASELINE)
        self.assertEqual(status["status"], "carried_forward")
        self.assertEqual(refresh["statusLabel"], "数据校验未通过 · 当前显示上期月内累计")
        self.assertEqual(snapshot["source"]["period"], "截至2026年7月12日 · 7月月内累计")

    def test_official_page_is_parsed_as_month_to_date_not_natural_week(self):
        index = '<a href="/Trends/latest.html">【周度分析】车市扫描(2026年7月6日-7月12日)</a>'
        article = """<h1>车市扫描(2026年7月6日-7月12日)</h1><p>时间: 2026-07-15 16:51:14</p>
        <p>乘用车：7月1-12日，全国乘用车市场零售44.3万辆，同比去年7月同期下降15%；
        7月1-12日，全国乘用车厂商批发37.9万辆，同比去年7月同期下降26%。
        新能源：7月1-12日，全国乘用车市场新能源零售28万辆，同比去年7月同期下降8%。
        渗透率：7月1-12日，全国乘用车市场新能源零售渗透率63.1%。</p>"""
        payload = fetch_latest_official_market_payload(
            fetch_text=lambda url: article if url.endswith("latest.html") else index
        )
        self.assertEqual(payload["source"]["period"], "截至2026年7月12日 · 7月月内累计")
        self.assertEqual(payload["source"]["naturalWeekPeriod"], "2026年7月6—12日")
        self.assertEqual(payload["facts"][0]["value"], 44.3)

    def test_fixed_weekly_index_ignores_newer_non_market_scan_categories(self):
        index = """
        <a href="newslist.php?types=csjd&id=4273">【联合发布】一周新车快讯(2026年7月11日-7月17日）</a>
        <a href="newslist.php?types=csjd&id=4272">【周度分析】车市扫描(20260706-0712)</a>
        <a href="newslist.php?types=csjd&id=4270">【新能源周报】新能源汽车行业信息周报(2026年7月6日-7月12日)</a>
        """
        article = """<h1>【周度分析】车市扫描(20260706-0712)</h1><p>时间: 2026-07-15 16:28:21</p>
        <p>乘用车：7月1-12日，全国乘用车市场零售44.3万辆，同比去年7月同期下降15%；
        全国乘用车厂商批发37.9万辆，同比去年7月同期下降26%。
        新能源：全国乘用车市场新能源零售28万辆，同比去年7月同期下降8%。
        渗透率：新能源零售渗透率63.1%。</p>"""
        fetched = []

        def fetch(url):
            fetched.append(url)
            return article if "id=4272" in url else index

        payload = fetch_latest_official_market_payload(
            fetch_text=fetch,
            index_url="https://www.cpcaauto.com/news.php?types=csjd&anid=128",
        )
        self.assertEqual(payload["source"]["url"], "https://www.cpcaauto.com/newslist.php?types=csjd&id=4272")
        self.assertEqual(fetched[-1], "https://www.cpcaauto.com/newslist.php?types=csjd&id=4272")

    def test_association_syndication_is_used_when_primary_site_is_unreachable(self):
        index = '<a href="/news/itemid-283606.html">协会发布 | 车市扫描(2026年7月6日-7月12日)</a>'
        article = """<h1>协会发布 | 车市扫描(2026年7月6日-7月12日)</h1>
        <p>乘用车：7月1-12日，全国乘用车市场零售44.3万辆，同比去年7月同期下降15%；
        全国乘用车厂商批发37.9万辆，同比去年7月同期下降26%。
        新能源：全国乘用车市场新能源零售28万辆，同比去年7月同期下降8%。
        渗透率：新能源零售渗透率63.1%。</p>"""

        def fetch(url):
            if url == "https://www.cpcaauto.com/news.php?types=csjd&anid=128":
                raise OSError("primary unavailable")
            if url.endswith("page-1.html"):
                return "<html>暂无周报</html>"
            if url.endswith("page-2.html"):
                return index
            if url.endswith("itemid-283606.html"):
                return article
            raise AssertionError(f"unexpected URL: {url}")

        payload = fetch_latest_official_market_payload(fetch_text=fetch)
        self.assertEqual(payload["source"]["naturalWeekPeriod"], "2026年7月6—12日")
        self.assertEqual(payload["source"]["url"], "https://npo00410y.npoall.com/news/itemid-283606.html")
        self.assertEqual(payload["facts"][3]["value"], 63.1)

    def test_unpublished_latest_natural_week_is_explicit_not_a_fake_success(self):
        with tempfile.TemporaryDirectory() as directory:
            status = refresh_weekly_market_snapshot(
                directory,
                official_fetcher=lambda url: (
                    '<a href="newslist.php?types=csjd&id=4272">【周度分析】车市扫描(2026年7月6日-7月12日)</a>'
                    if "anid=128" in url
                    else """<h1>车市扫描(2026年7月6日-7月12日)</h1>
                    乘用车：7月1-12日，全国乘用车市场零售44.3万辆，同比去年7月同期下降15%；
                    全国乘用车厂商批发37.9万辆，同比去年7月同期下降26%。
                    新能源：全国乘用车市场新能源零售28万辆，同比去年7月同期下降8%。
                    渗透率：新能源零售渗透率63.1%。"""
                ),
                today=__import__("datetime").date(2026, 7, 20),
            )
        self.assertEqual(status["status"], "awaiting_publication")
        self.assertIn("最近自然周数据待发布", status["error"])


if __name__ == "__main__":
    unittest.main()
