import unittest

from server import collect_opportunity_official_sources


class OpportunityOfficialSourcesTest(unittest.TestCase):
    def test_one_failed_official_page_does_not_abort_other_competitors(self):
        sources = [
            {"model": "小米YU7", "url": "https://example.com/yu7"},
            {"model": "Model Y", "url": "https://example.com/model-y"},
        ]

        def fetcher(url, allowed_domains=None):
            if url.endswith("model-y"):
                raise ValueError("官网响应超过大小限制")
            return {"body": "<h1>小米YU7</h1><p>智能座舱</p>", "url": url, "finalUrl": url, "fetchedAt": "2026-07-11T00:00:00Z", "sha256": "ok", "status": "verified"}

        facts, results = collect_opportunity_official_sources(sources, fetcher=fetcher)
        self.assertTrue(facts)
        self.assertEqual([item["status"] for item in results], ["verified", "manual_required"])
        self.assertIn("超过大小限制", results[1]["failureReason"])

    def test_source_progress_is_reported_after_each_competitor(self):
        sources = [
            {"model": "小米YU7", "url": "https://example.com/yu7"},
            {"model": "Model Y", "url": "https://example.com/model-y"},
        ]
        events = []

        def fetcher(url, allowed_domains=None):
            return {"body": "<h1>车型产品页</h1>", "url": url, "finalUrl": url, "fetchedAt": "2026-07-11T00:00:00Z", "sha256": "ok", "status": "verified"}

        collect_opportunity_official_sources(
            sources,
            fetcher=fetcher,
            progress_callback=lambda current, total, result: events.append((current, total, result["model"], result["status"])),
        )

        self.assertEqual(events, [
            (1, 2, "小米YU7", "verified"),
            (2, 2, "Model Y", "verified"),
        ])


if __name__ == "__main__":
    unittest.main()
