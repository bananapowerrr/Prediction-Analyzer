import unittest
from unittest.mock import patch
from mvp_client import MVPClient

class TestMVPClientParse(unittest.TestCase):
    @patch('mvp_client.MVPClient.fetch_market_details')
    def test_parse_market_record(self, mock_fetch_market_details):
        # Mock data
        mock_data = {
            'id': '123',
            'question': 'What will the weather be like tomorrow?',
            'liquidityNum': 100000,
            'volume24hr': 500000
        }
        
        # Mock the fetch_market_details method to return the mock data
        mock_fetch_market_details.return_value = mock_data
        
        # Create an instance of MVPClient
        client = MVPClient()
        
        # Call the parse_market_record method with a mock market ID
        market_record = client.parse_market_record('123')
        
        # Assert that the market_record is not None
        self.assertIsNotNone(market_record)
        
        # Assert that the market_record contains the expected data
        self.assertEqual(market_record['id'], '123')
        self.assertEqual(market_record['question'], 'What will the weather be like tomorrow?')
        self.assertEqual(market_record['liquidityNum'], 100000)
        self.assertEqual(market_record['volume24hr'], 500000)

if __name__ == '__main__':
    unittest.main()
