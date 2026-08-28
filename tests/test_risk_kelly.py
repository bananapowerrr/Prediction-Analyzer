import unittest
from risk_engine import calculate_fractional_kelly, determine_position_size, assess_outcome
from core.models import Market

class TestRiskKelly(unittest.TestCase):
    """Тесты для функций риска иKelly."""

    def test_fractional_kelly_with_zero_spread(self):
        """Проверка расчета фракционного Kelly с нулевым разбросом."""
        market = Market(spread=0)
        result = calculate_fractional_kelly(market, {market.outcomes[0]: 0.5, market.outcomes[1]: 0.5})
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, float('inf'))

    def test_position_size_within_initial_capital(self):
        """Проверка размера позиции в пределах начального капитала."""
        market = Market(initial_capital=1000)
        result = determine_position_size(market, {market.outcomes[0]: 0.5, market.outcomes[1]: 0.5}, 1000)
        self.assertLessEqual(result, 1000)

    def test_assess_outcome_probability_in_range(self):
        """Проверка вероятности исхода в диапазоне от 0 до 1."""
        outcome_probabilities = {outcome: 0.5 for outcome in ['outcome1', 'outcome2']}
        result = assess_outcome(outcome_probabilities, 'outcome1', 100)
        self.assertGreaterEqual(result, 0)
        self.assertLessEqual(result, 1)

if __name__ == '__main__':
    unittest.main()
