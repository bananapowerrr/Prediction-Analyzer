import unittest
from ai_explanation import format_explanation

class TestAIExplanation(unittest.TestCase):
    def test_format_explanation(self):
        market_question = "What is the current price of Bitcoin?"
        action = "Buy"
        confidence = 0.95
        expected_output = "Action: Buy\nConfidence: 95%"
        self.assertEqual(format_explanation(market_question, action, confidence), expected_output)

if __name__ == '__main__':
    unittest.main()
