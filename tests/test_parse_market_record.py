import unittest
from prediction_analyzer.parse_market_record import parse_market_record

class TestParseMarketRecord(unittest.TestCase):
    def test_valid_record(self):
        record = "AAPL,150.75,152.00,149.50,151.25,1000000"
        expected = {
            "symbol": "AAPL",
            "open": 150.75,
            "high": 152.00,
            "low": 149.50,
            "close": 151.25,
            "volume": 1000000
        }
        self.assertEqual(parse_market_record(record), expected)

    def test_invalid_record(self):
        record = "AAPL,150.75,152.00,149.50,151.25"
        with self.assertRaises(ValueError):
            parse_market_record(record)

if __name__ == '__main__':
    unittest.main()
