import unittest
from unittest.mock import patch
from paper_broker import PaperBroker

class TestPaperBroker(unittest.TestCase):
    @patch('paper_broker.PaperBroker.place_order')
    @patch('paper_broker.PaperBroker.list_orders')
    def test_place_and_list_orders(self, mock_list_orders, mock_place_order):
        mock_place_order.return_value = {'order_id': '123'}
        mock_list_orders.return_value = [{'order_id': '123'}]

        broker = PaperBroker()
        order_id = broker.place_order('AAPL', 'buy', 100)
        orders = broker.list_orders()

        self.assertEqual(order_id, '123')
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]['order_id'], '123')

if __name__ == '__main__':
    unittest.main()
