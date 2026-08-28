import unittest
from unittest.mock import patch
from quantitative_signals import build_signal

class TestBuildSignalsBatch(unittest.TestCase):
    @patch('quantitative_signals.Market')
    def test_build_signal(self, mock_market):
        mock_market.id = 'market123'
        mock_market.score = 0.8
        mock_market.indicators = {'volume': 10000, 'spread': 0.01}

        signal = build_signal(mock_market.id, mock_market.score, mock_market.indicators)

        self.assertEqual(signal.market_id, 'market123')
        self.assertEqual(signal.score, 0.8)
        self.assertEqual(signal.indicators, {'volume': 10000, 'spread': 0.01})

if __name__ == '__main__':
    unittest.main()
