import json
import tempfile
import unittest
from pathlib import Path

from weekly_market_refresh import (
    LatestArticleParseError,
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

    def test_latest_official_article_accepts_new_energy_market_word_order(self):
        index = '<a href="newslist.php?types=csjd&id=4279">【周度分析】车市扫描(20260713-0719)</a>'
        article = """<h1>【周度分析】车市扫描(20260713-0719)</h1><p>发布时间：2026-07-22 18:10:45</p>
        <p>乘用车：7月1-19日，全国乘用车市场零售77.0万辆，同比去年7月同期下降16%；
        全国乘用车厂商批发74.7万辆，同比去年7月同期下降17%。
        新能源：全国乘用车新能源市场零售48.5万辆，同比去年7月同期下降4%。
        渗透率：全国乘用车市场新能源零售渗透率63%。</p>"""
        payload = fetch_latest_official_market_payload(
            fetch_text=lambda url: article if "id=4279" in url else index
        )
        facts = {item["id"]: item for item in payload["facts"]}
        self.assertEqual(facts["retail"]["value"], 77.0)
        self.assertEqual(facts["wholesale"]["value"], 74.7)
        self.assertEqual(facts["nev_retail"]["value"], 48.5)
        self.assertEqual(facts["nev_penetration"]["value"], 63.0)
        self.assertEqual(payload["source"]["url"], "https://www.cpcaauto.com/newslist.php?types=csjd&id=4279")
        self.assertEqual(payload["source"]["naturalWeekPeriod"], "2026年7月13—19日")
        self.assertEqual(payload["source"]["period"], "截至2026年7月19日 · 7月月内累计")

    def test_latest_official_article_accepts_yoy_without_repeated_month(self):
        index = '<a href="newslist.php?types=csjd&id=4291">【周度分析】车市扫描(20260727-0731)</a>'
        article = """<h1>【周度分析】车市扫描(20260727-0731)</h1><p>发布时间：2026-08-05 16:20:12</p>
        <p>初步统计：7月1-31日，全国乘用车市场零售150.6万辆，同比去年同期下降18%；
        7月1-31日，全国乘用车厂商批发224.1万辆，同比去年同期增长1%。
        初步统计：7月1-31日，全国乘用车新能源市场零售97万辆，同比去年同期下降2%。
        渗透率：7月1-31日，全国新能源市场零售渗透率64.4%；
        全国乘用车厂商新能源批发渗透率65.3%。</p>"""
        payload = fetch_latest_official_market_payload(
            fetch_text=lambda url: article if "id=4291" in url else index
        )
        facts = {item["id"]: item for item in payload["facts"]}
        self.assertEqual(facts["retail"]["value"], 150.6)
        self.assertEqual(facts["retail"]["yoy"], -0.18)
        self.assertEqual(facts["wholesale"]["value"], 224.1)
        self.assertEqual(facts["wholesale"]["yoy"], 0.01)
        self.assertEqual(facts["nev_retail"]["value"], 97.0)
        self.assertEqual(facts["nev_retail"]["yoy"], -0.02)
        self.assertEqual(facts["nev_penetration"]["value"], 64.4)
        self.assertEqual(payload["source"]["naturalWeekPeriod"], "2026年7月27—31日")
        self.assertEqual(payload["source"]["period"], "截至2026年7月31日 · 7月月内累计")

    def test_month_end_truncated_week_is_publishable_for_that_completed_week(self):
        index = '<a href="newslist.php?types=csjd&id=4291">【周度分析】车市扫描(20260727-0731)</a>'
        article = """<h1>【周度分析】车市扫描(20260727-0731)</h1>
        7月1-31日，全国乘用车市场零售150.6万辆，同比去年同期下降18%；
        全国乘用车厂商批发224.1万辆，同比去年同期增长1%。
        全国乘用车新能源市场零售97万辆，同比去年同期下降2%。
        全国新能源市场零售渗透率64.4%。"""

        with tempfile.TemporaryDirectory() as directory:
            status = refresh_weekly_market_snapshot(
                directory,
                official_fetcher=lambda url: article if "id=4291" in url else index,
                today=__import__("datetime").date(2026, 8, 6),
            )
            snapshot, refresh = load_weekly_market_snapshot(directory, BASELINE)
        self.assertEqual(status["status"], "published")
        self.assertEqual(snapshot["source"]["naturalWeekEndDate"], "2026-07-31")
        self.assertEqual(refresh["naturalWeekPeriod"], "2026年7月27—31日")

    def test_month_end_snapshot_is_carried_forward_while_next_week_is_unpublished(self):
        payload = fetch_latest_official_market_payload(
            fetch_text=lambda url: (
                """<h1>【周度分析】车市扫描(20260727-0731)</h1>
                7月1-31日，全国乘用车市场零售150.6万辆，同比去年同期下降18%；
                全国乘用车厂商批发224.1万辆，同比去年同期增长1%。
                全国乘用车新能源市场零售97万辆，同比去年同期下降2%。
                全国新能源市场零售渗透率64.4%。"""
                if "id=4291" in url
                else '<a href="newslist.php?types=csjd&id=4291">【周度分析】车市扫描(20260727-0731)</a>'
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            first = refresh_weekly_market_snapshot(
                directory, payload=payload, today=__import__("datetime").date(2026, 8, 6)
            )
            second = refresh_weekly_market_snapshot(
                directory, payload=payload, today=__import__("datetime").date(2026, 8, 10)
            )
            snapshot, refresh = load_weekly_market_snapshot(directory, BASELINE)
        self.assertEqual(first["status"], "published")
        self.assertEqual(second["status"], "awaiting_publication")
        self.assertEqual(snapshot["source"]["naturalWeekEndDate"], "2026-07-31")
        self.assertEqual(refresh["naturalWeekPeriod"], "2026年7月27—31日")

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

    def test_latest_official_article_parse_failure_does_not_fall_back_to_an_older_source(self):
        index = '<a href="newslist.php?types=csjd&id=4279">【周度分析】车市扫描(20260713-0719)</a>'
        fetched = []

        def fetch(url):
            fetched.append(url)
            return "<p>字段结构发生变化</p>" if "id=4279" in url else index

        with self.assertRaises(LatestArticleParseError) as raised:
            fetch_latest_official_market_payload(fetch_text=fetch)
        self.assertEqual(raised.exception.url, "https://www.cpcaauto.com/newslist.php?types=csjd&id=4279")
        self.assertEqual(len(fetched), 2)

    def test_latest_parse_failure_preserves_snapshot_and_reports_true_state(self):
        index = '<a href="newslist.php?types=csjd&id=4279">【周度分析】车市扫描(20260713-0719)</a>'

        with tempfile.TemporaryDirectory() as directory:
            refresh_weekly_market_snapshot(directory, payload=BASELINE)
            status = refresh_weekly_market_snapshot(
                directory,
                official_fetcher=lambda url: "<p>字段结构发生变化</p>" if "id=4279" in url else index,
                today=__import__("datetime").date(2026, 7, 22),
            )
            snapshot, refresh = load_weekly_market_snapshot(directory, BASELINE)
        self.assertEqual(status["status"], "latest_parse_failed")
        self.assertEqual(status["statusLabel"], "最新一期已发布，数据处理未完成 · 当前显示上期月内累计")
        self.assertEqual(status["latestArticle"]["url"], "https://www.cpcaauto.com/newslist.php?types=csjd&id=4279")
        self.assertEqual(snapshot["source"]["naturalWeekEndDate"], "2026-07-12")
        self.assertEqual(refresh["status"], "latest_parse_failed")

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
