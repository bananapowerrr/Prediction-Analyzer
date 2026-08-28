"""Tests for the scanner's sort-by-liquidity behaviour (run_scan).

These tests mock MarketScanner.scan so no real network access is performed.
When mocking is possible we verify sort_by_liquidity directly; as a fallback
we also exercise the sorted logic through run_scan itself.
"""

import unittest
from unittest.mock import patch

from core.models import Market
from data.scanner import MarketScanner, ScanConfig, run_scan


def _make_market(market_id: str, liquidity: float) -> Market:
    return Market(
        id=market_id,
        question=f"Will {market_id} happen?",
        liquidity=liquidity,
        spread=0.05,
        volume_24h=100.0,
    )


class TestRunScanSortByLiquidity(unittest.TestCase):
    """Verify that run_scan sorts the scanned markets by liquidity."""

    def setUp(self) -> None:
        self.markets = [
            _make_market("m1", 10.0),
            _make_market("m2", 5.0),
            _make_market("m3", 20.0),
        ]

    @patch.object(MarketScanner, "scan")
    def test_sorts_by_liquidity_descending(self, mock_scan):
        mock_scan.return_value = self.markets
        result = run_scan(sort_by_liquidity=True)
        self.assertEqual([m.id for m in result], ["m3", "m1", "m2"])
        self.assertEqual([m.liquidity for m in result], [20.0, 10.0, 5.0])

    @patch.object(MarketScanner, "scan")
    def test_sort_is_default(self, mock_scan):
        mock_scan.return_value = self.markets
        result = run_scan()
        self.assertEqual([m.id for m in result], ["m3", "m1", "m2"])

    @patch.object(MarketScanner, "scan")
    def test_disabled_sort_preserves_scan_order(self, mock_scan):
        mock_scan.return_value = self.markets
        result = run_scan(sort_by_liquidity=False)
        self.assertEqual([m.id for m in result], ["m1", "m2", "m3"])

    @patch.object(MarketScanner, "scan")
    def test_limit_applied_after_sort(self, mock_scan):
        mock_scan.return_value = self.markets
        result = run_scan(sort_by_liquidity=True, limit=2)
        self.assertEqual([m.id for m in result], ["m3", "m1"])

    @patch.object(MarketScanner, "scan")
    def test_stable_sort_keeps_relative_order_for_equal_liquidity(self, mock_scan):
        mock_scan.return_value = [
            _make_market("a", 7.0),
            _make_market("b", 7.0),
            _make_market("c", 1.0),
        ]
        result = run_scan(sort_by_liquidity=True)
        self.assertEqual([m.id for m in result], ["a", "b", "c"])

    @patch.object(MarketScanner, "scan")
    def test_empty_scan_returns_empty_list(self, mock_scan):
        mock_scan.return_value = []
        self.assertEqual(run_scan(sort_by_liquidity=True), [])


class TestScanConfigSortIntegration(unittest.TestCase):
    """ScanConfig built by run_scan is forwarded to MarketScanner."""

    @patch.object(MarketScanner, "scan")
    @patch("data.scanner.MarketScanner")
    def test_run_scan_passes_config_to_scanner(self, MockScanner, mock_scan):
        MockScanner.return_value.scan.return_value = []
        run_scan(
            min_liquidity=500.0,
            max_spread=0.05,
            min_volume=100.0,
            limit=10,
            sort_by_liquidity=True,
        )
        args, kwargs = MockScanner.call_args
        cfg = kwargs["scan_config"] if "scan_config" in kwargs else args[0]
        self.assertIsInstance(cfg, ScanConfig)
        self.assertEqual(cfg.min_liquidity, 500.0)
        self.assertEqual(cfg.max_spread, 0.05)
        self.assertEqual(cfg.min_volume, 100.0)


class TestSortedLogicHelper(unittest.TestCase):
    """Unit test for the sorted-by-liquidity logic in isolation.

    Mirrors the exact expression used by run_scan so the helper stays in
    sync even if run_scan is refactored to delegate to a dedicated function.
    """

    def _sort_by_liquidity(self, markets):
        return sorted(markets, key=lambda m: m.liquidity, reverse=True)

    def test_helper_sorts_descending(self):
        markets = [
            _make_market("x", 3.0),
            _make_market("y", 9.0),
            _make_market("z", 1.0),
        ]
        result = self._sort_by_liquidity(markets)
        self.assertEqual([m.id for m in result], ["y", "x", "z"])

    def test_helper_is_stable_for_equal_liquidity(self):
        markets = [_make_market("a", 4.0), _make_market("b", 4.0), _make_market("c", 2.0)]
        result = self._sort_by_liquidity(markets)
        self.assertEqual([m.id for m in result], ["a", "b", "c"])

    def test_helper_empty(self):
        self.assertEqual(self._sort_by_liquidity([]), [])


if __name__ == "__main__":
    unittest.main()
