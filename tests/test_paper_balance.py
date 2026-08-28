import unittest
from execution.paper import PaperBroker


class TestPaperBalance(unittest.TestCase):

    def test_initial_balance(self):
        broker = PaperBroker()
        self.assertEqual(broker.get_balance(), 10000.0)

    def test_balance_decreases_after_buy(self):
        broker = PaperBroker()
        initial = broker.get_balance()
        broker.place('buy', size=100, price=0.5)
        expected = initial - 100 * 0.5
        self.assertAlmostEqual(broker.get_balance(), expected)

    def test_balance_decreases_after_sell(self):
        broker = PaperBroker()
        initial = broker.get_balance()
        broker.place('sell', size=50, price=0.3)
        expected = initial - 50 * 0.3
        self.assertAlmostEqual(broker.get_balance(), expected)

    def test_multiple_trades_decrease_balance(self):
        broker = PaperBroker()
        broker.place('buy', size=100, price=0.5)
        broker.place('sell', size=20, price=0.2)
        expected = 10000.0 - 100 * 0.5 - 20 * 0.2
        self.assertAlmostEqual(broker.get_balance(), expected)

    def test_insufficient_balance_raises(self):
        broker = PaperBroker()
        with self.assertRaises(ValueError):
            broker.place('buy', size=100000, price=1.0)

    def test_balance_never_goes_negative(self):
        broker = PaperBroker()
        broker.place('buy', size=5000, price=1.0)
        self.assertGreaterEqual(broker.get_balance(), 0)
        with self.assertRaises(ValueError):
            broker.place('buy', size=6000, price=1.0)

    def test_order_recorded_on_fill(self):
        broker = PaperBroker()
        result = broker.place('buy', size=10, price=0.7)
        self.assertEqual(result['status'], 'filled')
        orders = broker.list_orders()
        self.assertEqual(len(orders), 1)
        self.assertAlmostEqual(orders[0]['size'], 10)

    def test_partial_drain(self):
        broker = PaperBroker()
        broker.place('buy', size=19999, price=0.5)
        self.assertAlmostEqual(broker.get_balance(), 10000.0 - 19999 * 0.5)


if __name__ == '__main__':
    unittest.main()
