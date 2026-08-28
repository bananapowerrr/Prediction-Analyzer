import unittest
from unittest.mock import Mock
from prediction_analyzer.scoring import score_market

class TestScoring(unittest.TestCase):
    def test_score_market(self):
        # Создаем два фиктивных рынка
        market1 = Mock()
        market1.id = "market1"
        market1.score = 0.8

        market2 = Mock()
        market2.id = "market2"
        market2.score = 0.9

        # Создаем список рынков
        markets = [market1, market2]

        # Вызываем функцию score_market
        result = score_market(markets)

        # Проверяем, что лучший рынок имеет более высокий score
        self.assertEqual(result, market2)

if __name__ == '__main__':
    unittest.main()
