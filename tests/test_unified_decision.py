# создано диспетчером для привязки Aider

import unittest
from unified_decision import UnifiedDecision

class TestUnifiedDecision(unittest.TestCase):
    def test_decide_with_empty_analyses(self):
        unified_decision = UnifiedDecision(cloud_analyses=[])
        result = unified_decision.decide()
        self.assertIsNone(result)

    def test_decide_with_single_analysis(self):
        unified_decision = UnifiedDecision(cloud_analyses=[{'decision': 'buy'}])
        result = unified_decision.decide()
        self.assertEqual(result, 'buy')

    def test_decide_with_multiple_analyses_majority_buy(self):
        unified_decision = UnifiedDecision(cloud_analyses=[{'decision': 'buy'}, {'decision': 'buy'}, {'decision': 'sell'}])
        result = unified_decision.decide()
        self.assertEqual(result, 'buy')

    def test_decide_with_multiple_analyses_majority_sell(self):
        unified_decision = UnifiedDecision(cloud_analyses=[{'decision': 'sell'}, {'decision': 'sell'}, {'decision': 'buy'}])
        result = unified_decision.decide()
        self.assertEqual(result, 'sell')

if __name__ == '__main__':
    unittest.main()
