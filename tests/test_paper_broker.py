import unittest
from unittest.mock import patch
from execution.paper import PaperBroker

class TestPaperBroker(unittest.TestCase):
    @patch('execution.paper.PaperBroker.place_order')
    @patch('execution.paper.PaperBroker.list_orders')
    def test_place_and_list_orders(self, mock_list_orders, mock_place_order) -> None:
        mock_place_order.return_value = {'order_id': '123'}
        mock_list_orders.return_value = [{'order_id': '123'}]

        broker = PaperBroker()
        order_id = broker.place_order('AAPL', 'buy', 100)
        orders = broker.list_orders()

        self.assertEqual(order_id, '123')
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]['order_id'], '123')

    def test_init_balance(self) -> None:
        broker = PaperBroker()
        self.assertIsNotNone(broker.balance)
        self.assertIsInstance(broker.balance, (int, float))

    def test_place_order_reduces_balance(self) -> None:
        broker = PaperBroker()
        initial_balance = broker.balance
        broker.place_order('AAPL', 'buy', 100)
        self.assertIsNotNone(broker.balance)
        self.assertIsInstance(broker.balance, (int, float))
        self.assertLess(broker.balance, initial_balance)

    def test_reset(self) -> None:
        broker = PaperBroker()
        initial_balance = broker.balance
        broker.place_order('AAPL', 'buy', 100)
        broker.reset()
        self.assertIsNotNone(broker.balance)
        self.assertIsInstance(broker.balance, (int, float))
        self.assertEqual(broker.balance, initial_balance)

if __name__ == '__main__':
    unittest.main()
