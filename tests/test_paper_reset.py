import unittest
from unittest.mock import patch
from execution.paper import PaperBroker

class TestPaperBroker(unittest.TestCase):
    def test_reset(self):
        paper_broker = PaperBroker()
        paper_broker.orders = {'order1': 'details1', 'order2': 'details2'}
        paper_broker.reset()
        self.assertEqual(paper_broker.orders, {})

if __name__ == '__main__':
    unittest.main()
