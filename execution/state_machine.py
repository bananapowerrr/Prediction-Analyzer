from enum import Enum, auto
from typing import Optional
import asyncio

class OrderState(Enum):
    IDLE = auto()
    PENDING = auto()
    BROADCASTED = auto()
    CONFIRMING = auto()
    CLOSED = auto()
    FAILED = auto()

class OrderStateMachine:
    def __init__(self):
        self.state = OrderState.IDLE
        self.transitions = {
            OrderState.IDLE: [OrderState.PENDING],
            OrderState.PENDING: [OrderState.BROADCASTED],
            OrderState.BROADCASTED: [OrderState.CONFIRMING],
            OrderState.CONFIRMING: [OrderState.CLOSED, OrderState.FAILED],
        }
        self.timeout_tasks = {}

    async def transition(self, new_state: OrderState):
        if self.state not in self.transitions or new_state not in self.transitions[self.state]:
            raise ValueError(f"Invalid transition from {self.state} to {new_state}")
        if self.state != new_state:
            self.state = new_state
            if new_state == OrderState.CONFIRMING:
                self.timeout_tasks[new_state] = asyncio.create_task(self._confirming_timeout())
            elif new_state == OrderState.CLOSED or new_state == OrderState.FAILED:
                self.timeout_tasks[new_state] = asyncio.create_task(self._close_or_fail_timeout())

    async def _confirming_timeout(self):
        await asyncio.sleep(10)  # Пример таймаута для подтверждения
        if self.state == OrderState.CONFIRMING:
            await self.transition(OrderState.CLOSED)

    async def _close_or_fail_timeout(self):
        await asyncio.sleep(5)  # Пример таймаута для закрытия или отказа
        if self.state == OrderState.CLOSED or self.state == OrderState.FAILED:
            await self.transition(OrderState.CLOSED)

    def get_state(self):
        return self.state
