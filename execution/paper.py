class PaperBroker:
    def __init__(self, balance: float = 10000.0):
        self._balance = balance
        self.orders = {}
        self.positions = {}

    @property
    def balance(self):
        return self._balance

    def place_order(self, market_id: str, side: str, size: float, price: float) -> dict:
        cost = size * price
        if self._balance < cost:
            raise ValueError("Недостаточно средств")
        order_id = str(len(self.orders) + 1)
        self.orders[order_id] = {
            'id': order_id,
            'market_id': market_id,
            'side': side,
            'size': size,
            'price': price,
            'status': 'filled'
        }
        self._balance -= cost
        self._update_position(market_id, side, size, price)
        return {'id': order_id, 'status': 'filled', 'pnl': 0}

    def _update_position(self, market_id: str, side: str, size: float, price: float):
        if market_id not in self.positions:
            self.positions[market_id] = {'size': 0, 'avg_price': 0, 'pnl': 0}
        pos = self.positions[market_id]
        if side == 'buy':
            total_cost = pos['size'] * pos['avg_price'] + size * price
            pos['size'] += size
            pos['avg_price'] = total_cost / pos['size'] if pos['size'] else 0
        elif side == 'sell':
            pnl = size * (price - pos['avg_price'])
            pos['pnl'] += pnl
            pos['size'] -= size
        if pos['size'] == 0:
            pos['avg_price'] = 0

    def get_positions(self) -> list:
        return [{'market_id': m, **p} for m, p in self.positions.items() if p['size'] != 0]

    def reset(self, balance: float = 10000.0):
        self._balance = balance
        self.orders = {}
        self.positions = {}

    def cancel(self, order_id: str) -> bool:
        if order_id in self.orders:
            order = self.orders[order_id]
            if order['status'] == 'filled':
                if order['side'] == 'buy':
                    self._balance += order['size'] * order['price']
                elif order['side'] == 'sell':
                    self._balance -= order['size'] * order['price']
            del self.orders[order_id]
            return True
        return False

    def snapshot(self) -> dict:
        return {
            'balance': self._balance,
            'positions': self.get_positions(),
            'orders': list(self.orders.values())
        }
