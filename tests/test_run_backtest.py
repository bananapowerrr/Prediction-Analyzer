import unittest
from unittest.mock import patch
from backtester import Backtester

class TestBacktester(unittest.TestCase):
    @patch('backtester.Backtester.filter_markets')
    @patch('backtester.Backtester.simulate_arbitrage')
    def test_run_pipeline_on_markets(self, mock_simulate_arbitrage, mock_filter_markets):
        # Arrange
        backtester = Backtester()
        mock_filter_markets.return_value = []
        mock_simulate_arbitrage.return_value = []

        # Act
        result = backtester.run_pipeline_on_markets([])

        # Assert
        self.assertEqual(result, [])
        mock_filter_markets.assert_called_once_with([])
        mock_simulate_arbitrage.assert_called_once_with([], {})

if __name__ == '__main__':
    unittest.main()
