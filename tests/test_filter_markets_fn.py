import unittest
from data.filters import passes_liquidity_gate, passes_spread_gate, passes_volume_gate, passes_all_gates

class TestFilterMarkets(unittest.TestCase):
    def test_filter_markets(self):
        # Создаем два рынка для теста
        market1 = {
            "liquidity": 1000,
            "spread": 0.01,
            "volume": 10000
        }
        market2 = {
            "liquidity": 500,
            "spread": 0.02,
            "volume": 5000
        }

        # Параметры для фильтрации
        min_liquidity = 500
        max_spread = 0.015
        min_volume = 5000

        # Проверяем первый рынок
        self.assertTrue(passes_liquidity_gate(market1, min_liquidity))
        self.assertTrue(passes_spread_gate(market1, max_spread))
        self.assertTrue(passes_volume_gate(market1, min_volume))
        self.assertTrue(passes_all_gates(market1, min_liquidity, max_spread, min_volume))

        # Проверяем второй рынок
        self.assertFalse(passes_liquidity_gate(market2, min_liquidity))
        self.assertTrue(passes_spread_gate(market2, max_spread))
        self.assertFalse(passes_volume_gate(market2, min_volume))
        self.assertFalse(passes_all_gates(market2, min_liquidity, max_spread, min_volume))

if __name__ == '__main__':
    unittest.main()
