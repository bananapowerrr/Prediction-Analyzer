class PaperBroker:
    def __init__(self):
        self.orders = {}

    def place(self, side, size, price):
        order_id = str(len(self.orders) + 1)
        self.orders[order_id] = {
            'side': side,
            'size': size,
            'price': price,
            'status': 'filled'
        }
        return {'id': order_id, 'status': 'filled'}

    def list_orders(self):
        return list(self.orders.values())
