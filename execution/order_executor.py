import asyncio
from typing import Any, Dict, Optional


class OrderValidationError(ValueError):
    """Raised when an order payload fails validation."""


class OrderExecutorError(Exception):
    """Raised when an order cannot be executed after all retries."""


class OrderExecutor:
    SIDES = ("buy", "sell")

    def __init__(self, rpc_client: Any = None, max_retries: int = 3, retry_delay: float = 0.1):
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if retry_delay < 0:
            raise ValueError("retry_delay must be >= 0")
        self.rpc_client = rpc_client
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.attempts = 0

    def build_payload(
        self,
        order_id: str,
        market_id: str,
        side: str,
        size: float,
        price: float,
        maker: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not order_id:
            raise OrderValidationError("order_id is required")
        if not market_id:
            raise OrderValidationError("market_id is required")
        if side not in self.SIDES:
            raise OrderValidationError(f"side must be one of {self.SIDES}")
        if not isinstance(size, (int, float)) or size <= 0:
            raise OrderValidationError("size must be a positive number")
        if not isinstance(price, (int, float)) or not (0.0 < price <= 1.0):
            raise OrderValidationError("price must be in the range (0, 1]")

        payload: Dict[str, Any] = {
            "order_id": order_id,
            "market_id": market_id,
            "side": side,
            "size": float(size),
            "price": float(price),
            "type": "limit",
        }
        if maker is not None:
            payload["maker"] = maker
        return payload

    def build_cancel_payload(self, order_id: str) -> Dict[str, Any]:
        if not order_id:
            raise OrderValidationError("order_id is required")
        return {"order_id": order_id, "type": "cancel"}

    async def _submit(self, payload: Dict[str, Any]) -> Any:
        if self.rpc_client is None:
            raise OrderExecutorError("No rpc_client configured")
        return await self.rpc_client.submit_order(payload)

    async def execute(self, payload: Dict[str, Any]) -> Any:
        self.attempts = 0
        last_error: Optional[BaseException] = None
        for attempt in range(self.max_retries + 1):
            self.attempts = attempt + 1
            try:
                return await self._submit(payload)
            except Exception as exc:  # noqa: BLE001 - retry on any submit failure
                last_error = exc
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
        raise OrderExecutorError(
            f"Order {payload.get('order_id')} failed after {self.attempts} attempts"
        ) from last_error

    async def place_order(
        self,
        order_id: str,
        market_id: str,
        side: str,
        size: float,
        price: float,
        maker: Optional[str] = None,
    ) -> Any:
        payload = self.build_payload(order_id, market_id, side, size, price, maker=maker)
        return await self.execute(payload)
