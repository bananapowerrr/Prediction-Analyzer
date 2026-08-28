import unittest
from dataclasses import dataclass
from typing import Dict

from quantitative_signals import QuantitativeSignal, build_signal

@dataclass
class MockMarket:
    score: float

class TestQuantitativeSignals(unittest.TestCase):
    def test_build_signal(self):
        market = MockMarket(score=0.8)
        signal = build_signal(market)
        self.assertEqual(signal.action, 'buy')
        self.assertIn('confidence', signal.to_dict())
        self.assertIn('action', signal.to_dict())
        self.assertTrue(0 <= signal.to_dict()['confidence'] <= 1)

        market = MockMarket(score=0.2)
        signal = build_signal(market)
        self.assertEqual(signal.action, 'sell')
        self.assertIn('confidence', signal.to_dict())
        self.assertIn('action', signal.to_dict())
        self.assertTrue(0 <= signal.to_dict()['confidence'] <= 1)

        market = MockMarket(score=0.5)
        signal = build_signal(market)
        self.assertEqual(signal.action, 'hold')
        self.assertIn('confidence', signal.to_dict())
        self.assertIn('action', signal.to_dict())
        self.assertTrue(0 <= signal.to_dict()['confidence'] <= 1)

if __name__ == '__main__':
    unittest.main()
