from typing import List
from execution.state_machine import OrderStateMachine, OrderState
import asyncio

class TransactionSupervisor:
    def __init__(self, rpc1, rpc2):
        self.rpc1 = rpc1
        self.rpc2 = rpc2
        self.orders = {}

    async def submit_order(self, order_id: str, order_details: dict):
        if order_id in self.orders:
            raise ValueError(f"Order {order_id} already exists")
        self.orders[order_id] = OrderStateMachine()
        await self.orders[order_id].transition(OrderState.PENDING)
        # Здесь можно добавить логику для отправки ордера на RPC1 и RPC2
        # и отслеживания его состояния

    async def monitor_orders(self):
        while True:
            for order_id, order_state_machine in self.orders.items():
                current_state = order_state_machine.get_state()
                if current_state == OrderState.PENDING:
                    # Здесь можно добавить логику для отправки ордера на RPC1 и RPC2
                    # и отслеживания его состояния
                    pass
                elif current_state == OrderState.BROADCASTED:
                    # Здесь можно добавить логику для отслеживания состояния ордера на RPC1 и RPC2
                    pass
                elif current_state == OrderState.CONFIRMING:
                    # Здесь можно добавить логику для отслеживания состояния ордера на RPC1 и RPC2
                    pass
                elif current_state == OrderState.CLOSED:
                    # Здесь можно добавить логику для закрытия ордера
                    del self.orders[order_id]
                elif current_state == OrderState.FAILED:
                    # Здесь можно добавить логику для обработки отказа ордера
                    del self.orders[order_id]
            await asyncio.sleep(1)  # Проверка каждую секунду
