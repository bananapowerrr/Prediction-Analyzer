from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from core.models import Order

logger = logging.getLogger(__name__)

DEFAULT_CLOB_BASE = "https://clob.polymarket.com"
DEFAULT_MAX_RETRIES = 5
DEFAULT_BACKOFF_BASE = 0.5
MAX_BACKOFF = 30.0


class OrderExecutorError(Exception):
    """Raised when an order related request fails after all retries."""


class OrderValidationError(ValueError):
    """Raised when an order fails payload validation."""


class LiquidityGateError(OrderExecutorError):
    """Raised when an order is rejected by the risk engine liquidity gate."""


# A risk checker is a callable ``(order, market_liquidity) -> None`` that raises
# :class:`LiquidityGateError` (or any exception) when the order must be blocked.
RiskChecker = "Callable[[Order, Optional[float]], None]"


def make_liquidity_gate(min_liquidity: float) -> "RiskChecker":
    """Build a risk checker that enforces the Liquidity Gate via ``risk_engine``.

    The returned callable raises :class:`LiquidityGateError` when the order's
    market liquidity is known and falls below ``min_liquidity``. It is a no-op
    when liquidity is not supplied (``None``), so callers that cannot resolve
    liquidity at submit time are not forced to fail.
    """
    def _gate(order: Order, market_liquidity: "Optional[float]") -> None:
        if market_liquidity is None:
            return
        from risk_engine import Market as RiskMarket, passes_liquidity_gate

        market = RiskMarket(
            id=order.market_id,
            liquidity=float(market_liquidity),
            spread=0.0,
            volume=0.0,
        )
        if not passes_liquidity_gate(market, min_liquidity):
            raise LiquidityGateError(
                f"Liquidity gate rejected {order.order_id}: liquidity "
                f"{market_liquidity:.2f} <= min {min_liquidity:.2f}"
            )

    return _gate


class OrderExecutor:
    """Executes orders against the Polymarket CLOB REST API.

    The async HTTP session is injectable so the executor can be tested without
    real network access. When no session is supplied a :class:`aiohttp.ClientSession`
    is created lazily on first use.
    """

    def __init__(
        self,
        api_key: str,
        clob_base: str = DEFAULT_CLOB_BASE,
        session: Optional[Any] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base: float = DEFAULT_BACKOFF_BASE,
        risk_checker: "Optional[RiskChecker]" = None,
    ) -> None:
        if not api_key:
            raise OrderValidationError("api_key is required")
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if backoff_base < 0:
            raise ValueError("backoff_base must be >= 0")

        self.api_key = api_key
        self.clob_base = clob_base.rstrip("/")
        self._session = session
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.risk_checker = risk_checker

    async def _get_session(self) -> Any:
        if self._session is None:
            try:
                import aiohttp
            except ImportError as exc:  # pragma: no cover - environment dependent
                raise OrderExecutorError(
                    "aiohttp is required for live requests; inject a session or "
                    "install aiohttp"
                ) from exc
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    # ------------------------------------------------------------------ payload
    def _build_payload(self, order: Order) -> Dict[str, Any]:
        if not isinstance(order, Order):
            raise OrderValidationError("order must be an Order instance")
        if not order.order_id:
            raise OrderValidationError("order_id is required")
        if not order.market_id:
            raise OrderValidationError("market_id is required")
        if order.side not in ("buy", "sell"):
            raise OrderValidationError("side must be 'buy' or 'sell'")
        if not isinstance(order.size, (int, float)) or order.size <= 0:
            raise OrderValidationError("size must be a positive number")
        if not isinstance(order.price, (int, float)) or not (0.0 < order.price <= 1.0):
            raise OrderValidationError("price must be in the range (0, 1]")

        payload: Dict[str, Any] = {
            "order_id": order.order_id,
            "market": order.market_id,
            "side": order.side,
            "size": float(order.size),
            "price": float(order.price),
            "type": "limit",
        }
        if order.maker:
            payload["maker"] = order.maker
        return payload

    # --------------------------------------------------- additional validation
    def validate_order(self, order: Order) -> None:
        """Run extended parameter validation before sending to CLOB.

        This complements :meth:`_build_payload` with trading-specific rules:
        prices must sit on Polymarket's 1-cent tick grid and order size must be
        within sane bounds. Raises :class:`OrderValidationError` on violation.
        """
        if not isinstance(order, Order):
            raise OrderValidationError("order must be an Order instance")
        # Polymarket quotes prices in cents, so enforce a 0.01 tick grid.
        if round(order.price, 2) != order.price:
            raise OrderValidationError(
                f"price {order.price} must be on a 0.01 tick grid"
            )
        if order.size > 1_000_000:
            raise OrderValidationError(
                f"size {order.size} exceeds the maximum allowed (1_000_000)"
            )

    # ----------------------------------------------------------------- requests
    def _backoff_delay(self, attempt: int, retry_after: Optional[float]) -> float:
        if retry_after is not None:
            return min(retry_after, MAX_BACKOFF)
        delay = self.backoff_base * (2 ** attempt)
        return min(delay, MAX_BACKOFF)

    async def _request_with_retry(
        self, method: str, url: str, **kwargs: Any
    ) -> Dict[str, Any]:
        session = await self._get_session()
        last_exc: Optional[BaseException] = None

        for attempt in range(self.max_retries + 1):
            try:
                async with session.request(method, url, **kwargs) as resp:
                    if resp.status == 429:
                        retry_after = self._parse_retry_after(resp)
                        if attempt < self.max_retries:
                            delay = self._backoff_delay(attempt, retry_after)
                            logger.warning(
                                "429 Too Many Requests from %s (attempt %d/%d); "
                                "backing off %.2fs",
                                url, attempt + 1, self.max_retries + 1, delay,
                            )
                            await asyncio.sleep(delay)
                            continue
                        raise OrderExecutorError(
                            f"Rate limited (429) by {url} after "
                            f"{self.max_retries + 1} attempts"
                        )
                    if 400 <= resp.status < 500:
                        raise OrderExecutorError(
                            f"Client error {resp.status} for {method} {url}"
                        )
                    if resp.status >= 500:
                        if attempt < self.max_retries:
                            delay = self._backoff_delay(attempt, None)
                            logger.warning(
                                "Server error %d from %s (attempt %d/%d); "
                                "backing off %.2fs",
                                resp.status, url, attempt + 1,
                                self.max_retries + 1, delay,
                            )
                            await asyncio.sleep(delay)
                            continue
                        raise OrderExecutorError(
                            f"Server error {resp.status} from {url} after "
                            f"{self.max_retries + 1} attempts"
                        )
                    if resp.status == 204:
                        return {}
                    data = await resp.json()
                    return data if isinstance(data, dict) else {"result": data}
            except OrderExecutorError:
                raise
            except Exception as exc:  # noqa: BLE001 - retry transient failures
                last_exc = exc
                if attempt < self.max_retries:
                    delay = self._backoff_delay(attempt, None)
                    logger.warning(
                        "Request %s %s failed (attempt %d/%d): %s; backing off %.2fs",
                        method, url, attempt + 1, self.max_retries + 1, exc, delay,
                    )
                    await asyncio.sleep(delay)
                    continue
                break

        raise OrderExecutorError(
            f"Request {method} {url} failed after "
            f"{self.max_retries + 1} attempts"
        ) from last_exc

    @staticmethod
    def _parse_retry_after(resp: Any) -> Optional[float]:
        raw = getattr(resp, "headers", {}).get("Retry-After")
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    # ------------------------------------------------------------------- public
    async def submit_order(
        self, order: Order, market_liquidity: "Optional[float]" = None
    ) -> Dict[str, Any]:
        self.validate_order(order)
        if self.risk_checker is not None:
            self.risk_checker(order, market_liquidity)
        payload = self._build_payload(order)
        url = f"{self.clob_base}/order"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        logger.info("Submitting %s order %s on %s", order.side, order.order_id, order.market_id)
        result = await self._request_with_retry(
            "POST", url, headers=headers, json=payload
        )
        logger.info("Order %s submitted: %s", order.order_id, result)
        return result

    async def cancel_order(self, order_id: str) -> bool:
        if not order_id:
            raise OrderValidationError("order_id is required")
        url = f"{self.clob_base}/order/{order_id}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        logger.info("Cancelling order %s", order_id)
        try:
            result = await self._request_with_retry(
                "DELETE", url, headers=headers
            )
        except OrderExecutorError as exc:
            logger.warning("Failed to cancel order %s: %s", order_id, exc)
            return False
        success = bool(result.get("success", True)) if isinstance(result, dict) else True
        if success:
            logger.info("Order %s cancelled", order_id)
        else:
            logger.warning("Order %s cancel reported failure", order_id)
        return success
