class PaperBroker:
    def __init__(self):
        self.orders = {}
        self.balance = 10000.0

    def place(self, side, size, price):
        if self.balance < size * price:
            raise ValueError("Insufficient balance")
        order_id = str(len(self.orders) + 1)
        self.orders[order_id] = {
            'side': side,
            'size': size,
            'price': price,
            'status': 'filled'
        }
        self.balance -= size * price
        return {'id': order_id, 'status': 'filled'}

    def list_orders(self):
        return list(self.orders.values())

    def get_balance(self):
        return self.balance
