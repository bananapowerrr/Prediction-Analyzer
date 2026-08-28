import unittest

from core.models import Market
from data.filters import filter_markets, passes_all_gates


class TestFiltersGates(unittest.TestCase):
    """Тесты фильтрации рынков по гейтам."""

    def test_market_passes_gates(self) -> None:
        market = Market(
            id="market1",
            question="Q1",
            liquidity=1000000,
            spread=0.01,
            volume_24h=100000,
        )
        self.assertTrue(
            passes_all_gates(market, min_liquidity=100000, max_spread=0.02, min_volume=10000)
        )

    def test_market_fails_liquidity_gate(self) -> None:
        market = Market(
            id="market2",
            question="Q2",
            liquidity=0,
            spread=0.01,
            volume_24h=100000,
        )
        self.assertFalse(
            passes_all_gates(market, min_liquidity=100000, max_spread=0.02, min_volume=10000)
        )

    def test_market_fails_spread_gate(self) -> None:
        market = Market(
            id="market3",
            question="Q3",
            liquidity=1000000,
            spread=0.03,
            volume_24h=100000,
        )
        self.assertFalse(
            passes_all_gates(market, min_liquidity=100000, max_spread=0.02, min_volume=10000)
        )

    def test_market_fails_volume_gate(self) -> None:
        market = Market(
            id="market4",
            question="Q4",
            liquidity=1000000,
            spread=0.01,
            volume_24h=5000,
        )
        self.assertFalse(
            passes_all_gates(market, min_liquidity=100000, max_spread=0.02, min_volume=10000)
        )

    def test_filter_markets_returns_subset(self) -> None:
        markets = [
            Market(id="market5", question="Q5", liquidity=1000000, spread=0.01, volume_24h=100000),
            Market(id="market6", question="Q6", liquidity=0, spread=0.01, volume_24h=100000),
            Market(id="market7", question="Q7", liquidity=1000000, spread=0.03, volume_24h=100000),
            Market(id="market8", question="Q8", liquidity=1000000, spread=0.01, volume_24h=5000),
        ]
        filtered_markets = filter_markets(markets, min_liquidity=100000, max_spread=0.02, min_volume=10000)
        self.assertEqual(len(filtered_markets), 1)
        self.assertEqual(filtered_markets[0].id, "market5")


if __name__ == "__main__":
    unittest.main()
