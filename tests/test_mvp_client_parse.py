import unittest
from unittest.mock import patch
from mvp_client import MVPClient

class TestMVPClientParse(unittest.TestCase):
    @patch('mvp_client.MVPClient.fetch_market_details')
    def test_parse_market_record(self, mock_fetch_market_details) -> None:
        """Тестирование метода parse_market_record."""
        mock_data = {
            'id': '123',
            'question': 'What will the weather be like tomorrow?',
            'liquidityNum': 100000,
            'volume24hr': 500000
        }
        
        mock_fetch_market_details.return_value = mock_data
        
        client = MVPClient()
        market_record = client.parse_market_record('123')
        
        self.assertIsNotNone(market_record)
        self.assertEqual(market_record['id'], '123')
        self.assertEqual(market_record['question'], 'What will the weather be like tomorrow?')
        self.assertIsInstance(market_record['liquidityNum'], float)
        self.assertIsInstance(market_record['volume24hr'], float)
        self.assertEqual(market_record['liquidityNum'], 100000.0)
        self.assertEqual(market_record['volume24hr'], 500000.0)

if __name__ == '__main__':
    unittest.main()
