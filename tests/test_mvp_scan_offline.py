import unittest
from unittest.mock import patch
from data.scanner import MarketScanner, PolymarketClient
from data.filters import passes_all_gates

class TestMVPScanOffline(unittest.TestCase):
    @patch.object(PolymarketClient, 'fetch_markets')
    def test_run_scan_filter(self, mock_fetch_markets):
        # Mock fetch_markets to return 2 markets
        mock_fetch_markets.return_value = [
            {'id': 'market1', 'liquidity': 50000, 'spread': 0.02, 'volume_24h': 100000},
            {'id': 'market2', 'liquidity': 10000, 'spread': 0.01, 'volume_24h': 50000}
        ]

        # Mock passes_all_gates to return True for both markets
        with patch('data.filters.passes_all_gates') as mock_passes_all_gates:
            mock_passes_all_gates.return_value = [True, True]

            scanner = MarketScanner()
            result = scanner.scan(min_liquidity=10000, max_spread=0.01, min_volume=50000)

            # Check that both markets passed the filters
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0].id, 'market1')
            self.assertEqual(result[1].id, 'market2')
