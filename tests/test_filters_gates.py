import unittest
from data.filters import passes_all_gates, filter_markets
from core.models import Market

class TestFiltersGates(unittest.TestCase):
    def test_market_passes_gates(self):
        market = Market(
            id="market1",
            liquidity=1000000,
            spread=0.01,
            volume=100000
        )
        self.assertTrue(passes_all_gates(market, min_liquidity=100000, max_spread=0.02, min_volume=10000))

    def test_market_fails_liquidity_gate(self):
        market = Market(
            id="market2",
            liquidity=0,
            spread=0.01,
            volume=100000
        )
        self.assertFalse(passes_all_gates(market, min_liquidity=100000, max_spread=0.02, min_volume=10000))

    def test_market_passes_spread_gate(self):
        market = Market(
            id="market3",
            liquidity=1000000,
            spread=0.01,
            volume=100000
        )
        self.assertTrue(passes_all_gates(market, min_liquidity=100000, max_spread=0.02, min_volume=10000))

    def test_market_fails_spread_gate(self):
        market = Market(
            id="market4",
            liquidity=1000000,
            spread=0.03,
            volume=100000
        )
        self.assertFalse(passes_all_gates(market, min_liquidity=100000, max_spread=0.02, min_volume=10000))

    def test_market_passes_volume_gate(self):
        market = Market(
            id="market5",
            liquidity=1000000,
            spread=0.01,
            volume=100000
        )
        self.assertTrue(passes_all_gates(market, min_liquidity=100000, max_spread=0.02, min_volume=10000))

    def test_market_fails_volume_gate(self):
        market = Market(
            id="market6",
            liquidity=1000000,
            spread=0.01,
            volume=5000
        )
        self.assertFalse(passes_all_gates(market, min_liquidity=100000, max_spread=0.02, min_volume=10000))

    def test_filter_markets_returns_subset(self):
        markets = [
            Market(
                id="market7",
                liquidity=1000000,
                spread=0.01,
                volume=100000
            ),
            Market(
                id="market8",
                liquidity=0,
                spread=0.01,
                volume=100000
            ),
            Market(
                id="market9",
                liquidity=1000000,
                spread=0.03,
                volume=100000
            ),
            Market(
                id="market10",
                liquidity=1000000,
                spread=0.01,
                volume=5000
            )
        ]
        filtered_markets = filter_markets(markets, min_liquidity=100000, max_spread=0.02, min_volume=10000)
        self.assertEqual(len(filtered_markets), 1)
        self.assertEqual(filtered_markets[0].id, "market7")

if __name__ == '__main__':
    unittest.main()
