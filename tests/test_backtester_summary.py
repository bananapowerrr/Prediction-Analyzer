import unittest
from backtester import Backtester

class TestBacktesterSummary(unittest.TestCase):
    def test_summarize_trades_empty_list(self):
        backtester = Backtester()
        summary = backtester.summarize_trades([])
        self.assertEqual(summary, {'wins': 0, 'losses': 0})

    def test_summarize_trades_one_win_one_loss(self):
        backtester = Backtester()
        trades = [
            {'profit': 100},
            {'profit': -50}
        ]
        summary = backtester.summarize_trades(trades)
        self.assertEqual(summary, {'wins': 1, 'losses': 1})

if __name__ == '__main__':
    unittest.main()
