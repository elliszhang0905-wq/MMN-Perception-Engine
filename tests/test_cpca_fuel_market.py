import json
import unittest
from unittest.mock import patch

import server


VALID_PAYLOAD = [{"dataList": [
    {"月份": "2026-5月", "ICE": [86.2828, 55.9863, 39.0, 37.1]},
    {"月份": "2026-6月", "ICE": [87.5515, 59.5171, 37.1, 37.2]},
]}]


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self, _limit):
        return self.body


class CpcaFuelMarketTest(unittest.TestCase):
    def setUp(self):
        self.original_cache = dict(server.CPCA_FUEL_MARKET_CACHE)
        server.CPCA_FUEL_MARKET_CACHE.update({
            "expires": "",
            "staleUntil": "",
            "fetchedAt": "",
            "payload": None,
        })

    def tearDown(self):
        server.CPCA_FUEL_MARKET_CACHE.clear()
        server.CPCA_FUEL_MARKET_CACHE.update(self.original_cache)

    def test_success_is_cached_and_failure_is_marked_stale(self):
        response = FakeResponse(json.dumps(VALID_PAYLOAD).encode("utf-8"))
        with patch.object(server, "urlopen", return_value=response):
            fresh = server.cpca_fuel_market_payload()

        self.assertFalse(fresh["stale"])
        self.assertEqual(fresh["payload"], VALID_PAYLOAD)
        self.assertTrue(fresh["fetchedAt"])

        server.CPCA_FUEL_MARKET_CACHE["expires"] = ""
        with patch.object(server, "urlopen", side_effect=server.URLError("offline")):
            stale = server.cpca_fuel_market_payload()

        self.assertTrue(stale["stale"])
        self.assertEqual(stale["payload"], VALID_PAYLOAD)

    def test_failure_does_not_return_expired_stale_cache(self):
        server.CPCA_FUEL_MARKET_CACHE.update({
            "expires": "",
            "staleUntil": "2000-01-01T00:00:00Z",
            "fetchedAt": "2000-01-01T00:00:00Z",
            "payload": VALID_PAYLOAD,
        })

        with patch.object(server, "urlopen", side_effect=server.URLError("offline")):
            self.assertIsNone(server.cpca_fuel_market_payload())

    def test_invalid_or_oversized_response_fails_closed_without_cache(self):
        invalid = FakeResponse(json.dumps([{"dataList": [{"月份": "2026-13月", "ICE": [1, 1, 1, 1]}]}]).encode("utf-8"))
        with patch.object(server, "urlopen", return_value=invalid):
            self.assertIsNone(server.cpca_fuel_market_payload())

        oversized = FakeResponse(b"x" * 2_000_001)
        with patch.object(server, "urlopen", return_value=oversized):
            self.assertIsNone(server.cpca_fuel_market_payload())


if __name__ == "__main__":
    unittest.main()
