import unittest
from unittest.mock import patch
from market_connector import MarketConnector

class TestMarketConnector(unittest.TestCase):
    @patch('market_connector.MarketConnector.fetch_markets')
    def test_fetch_markets(self, mock_fetch_markets):
        mock_fetch_markets.return_value = [{'id': 'market1'}, {'id': 'market2'}]
        connector = MarketConnector()
        markets = connector.fetch_markets()
        self.assertEqual(len(markets), 2)
        self.assertEqual(markets[0]['id'], 'market1')
        self.assertEqual(markets[1]['id'], 'market2')

if __name__ == '__main__':
    unittest.main()
