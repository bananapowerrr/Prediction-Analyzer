from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from core.models import Market
from core.scanner import (
    MarketScanner,
    PolymarketScanner,
    ScanConfig,
    filter_by_volume_threshold,
)
from data.scanner import _to_float


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _raw_market(**overrides) -> dict:
    base = dict(id="m1", question="Will X happen?", liquidity=1000.0, spread=0.05, volume24hr=500.0)
    base.update(overrides)
    return base


def _make_market(**overrides) -> Market:
    base = dict(id="m1", question="q", liquidity=1000.0, spread=0.05, volume_24h=500.0)
    base.update(overrides)
    return Market(**base)


# ---------------------------------------------------------------------------
# _to_float utility
# ---------------------------------------------------------------------------

class TestToFloat:
    def test_normal_value(self):
        assert _to_float("3.14") == 3.14

    def test_int_value(self):
        assert _to_float(42) == 42.0

    def test_none_returns_default(self):
        assert _to_float(None) == 0.0

    def test_non_numeric_returns_default(self):
        assert _to_float("abc", default=-1.0) == -1.0

    def test_custom_default(self):
        assert _to_float(None, default=99.0) == 99.0


# ---------------------------------------------------------------------------
# ScanConfig
# ---------------------------------------------------------------------------

class TestScanConfig:
    def test_defaults_from_config(self):
        cfg = ScanConfig()
        assert cfg.min_liquidity > 0
        assert cfg.max_spread > 0
        assert cfg.limit > 0

    def test_custom_values(self):
        cfg = ScanConfig(min_liquidity=500.0, max_spread=0.03, min_volume=100.0, limit=10)
        assert cfg.min_liquidity == 500.0
        assert cfg.max_spread == 0.03
        assert cfg.min_volume == 100.0
        assert cfg.limit == 10


# ---------------------------------------------------------------------------
# MarketScanner (base class) – mocked fetch_raw
# ---------------------------------------------------------------------------

class TestMarketScanner:
    def test_scan_filters_markets(self):
        scanner = MarketScanner(scan_config=ScanConfig(min_liquidity=500.0, max_spread=0.1, min_volume=0.0, limit=10))
        good = _make_market(id="good", liquidity=1000.0, spread=0.05)
        bad = _make_market(id="bad", liquidity=100.0, spread=0.05)

        scanner.fetch_raw = MagicMock(return_value=[])
        scanner.parse = MagicMock(return_value=[good, bad])

        result = scanner.scan()
        assert len(result) == 1
        assert result[0].id == "good"

    def test_scan_empty_result(self):
        scanner = MarketScanner()
        scanner.fetch_raw = MagicMock(return_value=[])
        scanner.parse = MagicMock(return_value=[])
        assert scanner.scan() == []


# ---------------------------------------------------------------------------
# PolymarketScanner.parse
# ---------------------------------------------------------------------------

class TestPolymarketScannerParse:
    def setup_method(self):
        self.scanner = PolymarketScanner(scan_config=ScanConfig())

    def test_parse_valid_markets(self):
        raw = [_raw_market(id="a", liquidity=800.0, spread=0.02, volume24hr=300.0)]
        markets = self.scanner.parse(raw)
        assert len(markets) == 1
        assert markets[0].id == "a"
        assert markets[0].liquidity == 800.0
        assert markets[0].spread == 0.02
        assert markets[0].volume_24h == 300.0

    def test_parse_skips_non_dicts(self):
        raw = ["not_a_dict", 42, None]
        assert self.scanner.parse(raw) == []

    def test_parse_skips_missing_id(self):
        raw = [_raw_market(id=None)]
        assert self.scanner.parse(raw) == []

    def test_parse_skips_empty_id(self):
        raw = [_raw_market(id="")]
        assert self.scanner.parse(raw) == []

    def test_parse_defaults_for_missing_fields(self):
        raw = [{"id": "x"}]
        markets = self.scanner.parse(raw)
        assert len(markets) == 1
        assert markets[0].liquidity == 0.0
        assert markets[0].spread == 0.0
        assert markets[0].volume_24h == 0.0


# ---------------------------------------------------------------------------
# PolymarketScanner._extract_spread
# ---------------------------------------------------------------------------

class TestExtractSpread:
    def test_explicit_spread(self):
        assert PolymarketScanner._extract_spread({"spread": 0.07}) == 0.07

    def test_computed_from_bid_ask(self):
        item = {"bestBid": 0.45, "bestAsk": 0.50}
        assert PolymarketScanner._extract_spread(item) == pytest.approx(0.05)

    def test_missing_spread_and_bid_ask(self):
        assert PolymarketScanner._extract_spread({}) == 0.0

    def test_zero_bid(self):
        item = {"bestBid": 0.0, "bestAsk": 0.5}
        assert PolymarketScanner._extract_spread(item) == 0.0


# ---------------------------------------------------------------------------
# PolymarketScanner.scan – mocked client
# ---------------------------------------------------------------------------

class TestPolymarketScannerScan:
    def test_scan_with_mocked_client(self):
        mock_client = MagicMock()
        mock_client.fetch_markets.return_value = [
            _raw_market(id="pass", liquidity=2000.0, spread=0.01, volume24hr=1000.0),
            _raw_market(id="fail_liq", liquidity=1.0, spread=0.01, volume24hr=1000.0),
        ]

        scanner = PolymarketScanner(
            client=mock_client,
            scan_config=ScanConfig(min_liquidity=500.0, max_spread=0.1, min_volume=0.0, limit=10),
        )
        result = scanner.scan()
        assert len(result) == 1
        assert result[0].id == "pass"
        mock_client.fetch_markets.assert_called_once_with(limit=10)

    def test_scan_calls_client_with_limit(self):
        mock_client = MagicMock()
        mock_client.fetch_markets.return_value = []

        scanner = PolymarketScanner(
            client=mock_client,
            scan_config=ScanConfig(min_liquidity=0.0, max_spread=1.0, min_volume=0.0, limit=25),
        )
        scanner.scan()
        mock_client.fetch_markets.assert_called_once_with(limit=25)


# ---------------------------------------------------------------------------
# PolymarketClient API mock (requests.get level)
# ---------------------------------------------------------------------------

class TestPolymarketClientAPI:
    @patch("data.polymarket_client.requests.get")
    def test_fetch_markets_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"id": "api_m1", "question": "Q1?", "liquidity": 1500, "spread": 0.03, "volume24hr": 800}
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        from data.polymarket_client import PolymarketClient
        client = PolymarketClient(timeout=5.0)
        markets = client.fetch_markets(limit=1)

        assert len(markets) == 1
        mock_get.assert_called_once()

    @patch("data.polymarket_client.requests.get")
    def test_fetch_markets_http_error(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("timeout")

        from data.polymarket_client import PolymarketClient
        client = PolymarketClient()
        markets = client.fetch_markets()
        assert markets == []

    @patch("data.polymarket_client.requests.get")
    def test_fetch_markets_non_list_response(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"unexpected": "dict"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        from data.polymarket_client import PolymarketClient
        client = PolymarketClient()
        markets = client.fetch_markets()
        assert markets == []


# ---------------------------------------------------------------------------
# scan_markets convenience function – mocked
# ---------------------------------------------------------------------------

class TestScanMarkets:
    @patch("data.scanner.PolymarketScanner")
    def test_scan_markets_delegates_to_scanner(self, MockScanner):
        mock_instance = MagicMock()
        mock_instance.scan.return_value = [_make_market(id="s1")]
        MockScanner.return_value = mock_instance

        from data.scanner import scan_markets
        result = scan_markets(min_liquidity=200.0, max_spread=0.05, min_volume=50.0, limit=5)

        assert len(result) == 1
        MockScanner.assert_called_once()
        call_cfg = MockScanner.call_args[1]["scan_config"]
        assert call_cfg.min_liquidity == 200.0
        assert call_cfg.max_spread == 0.05
        assert call_cfg.min_volume == 50.0
        assert call_cfg.limit == 5

    @patch("data.scanner.PolymarketScanner")
    def test_scan_markets_empty(self, MockScanner):
        mock_instance = MagicMock()
        mock_instance.scan.return_value = []
        MockScanner.return_value = mock_instance

        from data.scanner import scan_markets
        result = scan_markets()
        assert result == []


# ---------------------------------------------------------------------------
# filter_by_volume_threshold
# ---------------------------------------------------------------------------

class TestFilterByVolume:
    def test_keeps_high_volume(self):
        markets = [_make_market(id="low", volume_24h=100.0), _make_market(id="high", volume_24h=1000.0)]
        assert filter_by_volume_threshold(markets, 500.0) == [markets[1]]

    def test_keeps_all_when_threshold_low(self):
        markets = [_make_market(id="a", volume_24h=100.0), _make_market(id="b", volume_24h=200.0)]
        assert filter_by_volume_threshold(markets, 50.0) == markets

    def test_empty_when_threshold_high(self):
        markets = [_make_market(volume_24h=10.0)]
        assert filter_by_volume_threshold(markets, 999.0) == []

    def test_empty_list_input(self):
        assert filter_by_volume_threshold([], 100.0) == []
