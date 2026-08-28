import unittest
from data.filters import passes_all_gates
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

if __name__ == '__main__':
    unittest.main()
