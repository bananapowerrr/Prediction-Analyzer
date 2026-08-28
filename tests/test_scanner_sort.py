"""Тесты для сортировки сканера по ликвидности (run_scan).

Эти тесты мокают MarketScanner.scan, чтобы не требовалось реального доступа к сети.
Когда это возможно, мы проверяем sort_by_liquidity напрямую; в качестве альтернативы мы также проверяем
сортировку через run_scan.
"""

import unittest
from unittest.mock import patch
from typing import List

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
    """Проверка сортировки сканированных рынков по ликвидности."""

    def setUp(self) -> None:
        self.markets = [
            _make_market("m1", 10.0),
            _make_market("m2", 5.0),
            _make_market("m3", 20.0),
        ]

    @patch.object(MarketScanner, "scan")
    def test_sorts_by_liquidity_descending(self, mock_scan: patch):
        mock_scan.return_value = self.markets
        result = run_scan(sort_by_liquidity=True)
        self.assertEqual([m.id for m in result], ["m3", "m1", "m2"])
        self.assertEqual([m.liquidity for m in result], [20.0, 10.0, 5.0])

    @patch.object(MarketScanner, "scan")
    def test_sort_is_default(self, mock_scan: patch):
        mock_scan.return_value = self.markets
        result = run_scan()
        self.assertEqual([m.id for m in result], ["m3", "m1", "m2"])

    @patch.object(MarketScanner, "scan")
    def test_disabled_sort_preserves_scan_order(self, mock_scan: patch):
        mock_scan.return_value = self.markets
        result = run_scan(sort_by_liquidity=False)
        self.assertEqual([m.id for m in result], ["m1", "m2", "m3"])

    @patch.object(MarketScanner, "scan")
    def test_limit_applied_after_sort(self, mock_scan: patch):
        mock_scan.return_value = self.markets
        result = run_scan(sort_by_liquidity=True, limit=2)
        self.assertEqual([m.id for m in result], ["m3", "m1"])

    @patch.object(MarketScanner, "scan")
    def test_stable_sort_keeps_relative_order_for_equal_liquidity(self, mock_scan: patch):
        mock_scan.return_value = [
            _make_market("a", 7.0),
            _make_market("b", 7.0),
            _make_market("c", 1.0),
        ]
        result = run_scan(sort_by_liquidity=True)
        self.assertEqual([m.id for m in result], ["a", "b", "c"])

    @patch.object(MarketScanner, "scan")
    def test_empty_scan_returns_empty_list(self, mock_scan: patch):
        mock_scan.return_value = []
        self.assertEqual(run_scan(sort_by_liquidity=True), [])


class TestScanConfigSortIntegration(unittest.TestCase):
    """ScanConfig, построенный run_scan, передается в MarketScanner."""

    @patch.object(MarketScanner, "scan")
    @patch("data.scanner.MarketScanner")
    def test_run_scan_passes_config_to_scanner(self, MockScanner: patch, mock_scan: patch):
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
    """Тест для логики сортировки по ликвидности в изоляции.

    Сопоставляется с точно таким же выражением, используемым в run_scan, чтобы помочь поддерживать
    согласованность даже если run_scan будет рефакториться, чтобы делегировать выполнение
    в отдельную функцию.
    """

    def _sort_by_liquidity(self, markets: List[Market]) -> List[Market]:
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
