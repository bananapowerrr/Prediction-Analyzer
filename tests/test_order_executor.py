import asyncio

import pytest

from core.models import Order
from execution.order_executor import (
    OrderExecutor,
    OrderExecutorError,
    OrderValidationError,
)


# ---------------------------------------------------------------------------
# Order model
# ---------------------------------------------------------------------------
def test_order_creation():
    order = Order("o1", "m1", "buy", 10.0, 0.5)
    assert order.order_id == "o1"
    assert order.market_id == "m1"
    assert order.side == "buy"
    assert order.size == 10.0
    assert order.price == 0.5


def test_order_rejects_bad_side():
    with pytest.raises(ValueError):
        Order("o1", "m1", "hold", 10, 0.5)


def test_order_rejects_non_positive_size():
    with pytest.raises(ValueError):
        Order("o1", "m1", "buy", 0, 0.5)
    with pytest.raises(ValueError):
        Order("o1", "m1", "buy", -1, 0.5)


def test_order_rejects_out_of_range_price():
    with pytest.raises(ValueError):
        Order("o1", "m1", "buy", 10, 0.0)
    with pytest.raises(ValueError):
        Order("o1", "m1", "buy", 10, 1.5)


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------
def test_init_defaults():
    executor = OrderExecutor(api_key="k")
    assert executor.clob_base == "https://clob.polymarket.com"
    assert executor.max_retries == 5
    assert executor.backoff_base == 0.5
    assert executor._session is None


def test_init_rejects_empty_api_key():
    with pytest.raises(OrderValidationError):
        OrderExecutor(api_key="")


def test_init_rejects_negative_max_retries():
    with pytest.raises(ValueError):
        OrderExecutor(api_key="k", max_retries=-1)


def test_init_rejects_negative_backoff():
    with pytest.raises(ValueError):
        OrderExecutor(api_key="k", backoff_base=-0.5)


# ---------------------------------------------------------------------------
# Payload building
# ---------------------------------------------------------------------------
def test_build_payload_valid():
    executor = OrderExecutor(api_key="k")
    order = Order("o1", "m1", "buy", 10.0, 0.5)
    payload = executor._build_payload(order)
    assert payload == {
        "order_id": "o1",
        "market": "m1",
        "side": "buy",
        "size": 10.0,
        "price": 0.5,
        "type": "limit",
    }


def test_build_payload_includes_maker():
    executor = OrderExecutor(api_key="k")
    order = Order("o3", "m1", "buy", 5, 0.4, maker="0xabc")
    assert executor._build_payload(order)["maker"] == "0xabc"


def test_build_payload_sell_side():
    executor = OrderExecutor(api_key="k")
    payload = executor._build_payload(Order("o2", "m1", "sell", 1, 0.99))
    assert payload["side"] == "sell"
    assert payload["size"] == 1.0
    assert payload["price"] == 0.99


def test_build_payload_rejects_bad_type():
    executor = OrderExecutor(api_key="k")
    with pytest.raises(OrderValidationError):
        executor._build_payload({"order_id": "o1"})  # type: ignore[arg-type]


def test_build_payload_rejects_bad_side():
    executor = OrderExecutor(api_key="k")
    order = Order("o1", "m1", "buy", 10, 0.5)
    order.side = "hold"
    with pytest.raises(OrderValidationError):
        executor._build_payload(order)


def test_build_payload_rejects_non_positive_size():
    executor = OrderExecutor(api_key="k")
    order = Order("o1", "m1", "buy", 10, 0.5)
    order.size = 0
    with pytest.raises(OrderValidationError):
        executor._build_payload(order)


def test_build_payload_rejects_out_of_range_price():
    executor = OrderExecutor(api_key="k")
    order = Order("o1", "m1", "buy", 10, 0.5)
    order.price = 0.0
    with pytest.raises(OrderValidationError):
        executor._build_payload(order)


# ---------------------------------------------------------------------------
# Fake async HTTP session
# ---------------------------------------------------------------------------
class FakeResponse:
    def __init__(self, status=200, json_data=None, headers=None):
        self.status = status
        self._json = json_data if json_data is not None else {}
        self.headers = headers or {}

    async def json(self):
        return self._json

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class FakeSession:
    def __init__(self, statuses=(200,), json_data=None):
        # cycle through statuses across calls
        self._statuses = list(statuses)
        self._json_data = json_data
        self.calls = 0
        self.requests = []

    def request(self, method, url, **kwargs):
        status = self._statuses[min(self.calls, len(self._statuses) - 1)]
        self.calls += 1
        self.requests.append((method, url, kwargs))
        data = self._json_data(self.calls) if callable(self._json_data) else (self._json_data or {})
        return FakeResponse(status=status, json_data=data)


def _run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# submit_order
# ---------------------------------------------------------------------------
def test_submit_order_success():
    session = FakeSession(statuses=(200,), json_data={"orderID": "o1", "status": "open"})
    executor = OrderExecutor(api_key="k", session=session, max_retries=3, backoff_base=0.0)
    result = _run(executor.submit_order(Order("o1", "m1", "buy", 10, 0.5)))
    assert result["status"] == "open"
    assert session.calls == 1
    assert session.requests[0][0] == "POST"
    assert session.requests[0][1].endswith("/order")


def test_submit_order_retries_on_429_then_succeeds():
    session = FakeSession(
        statuses=(429, 429, 200),
        json_data={"orderID": "o1", "status": "open"},
    )
    executor = OrderExecutor(api_key="k", session=session, max_retries=5, backoff_base=0.01)
    result = _run(executor.submit_order(Order("o1", "m1", "buy", 10, 0.5)))
    assert result["status"] == "open"
    assert session.calls == 3


def test_submit_order_exhausts_retries_on_429():
    session = FakeSession(statuses=(429, 429, 429, 429))
    executor = OrderExecutor(api_key="k", session=session, max_retries=3, backoff_base=0.0)
    with pytest.raises(OrderExecutorError):
        _run(executor.submit_order(Order("o1", "m1", "buy", 10, 0.5)))
    assert session.calls == 4


def test_submit_order_propagates_4xx_without_retry():
    session = FakeSession(statuses=(400,))
    executor = OrderExecutor(api_key="k", session=session, max_retries=3, backoff_base=0.0)
    with pytest.raises(OrderExecutorError):
        _run(executor.submit_order(Order("o1", "m1", "buy", 10, 0.5)))
    assert session.calls == 1


def test_submit_order_validation_error():
    executor = OrderExecutor(api_key="k", session=FakeSession())
    order = Order("o1", "m1", "buy", 10, 0.5)
    order.size = -1
    with pytest.raises(OrderValidationError):
        _run(executor.submit_order(order))


# ---------------------------------------------------------------------------
# cancel_order
# ---------------------------------------------------------------------------
def test_cancel_order_success():
    session = FakeSession(statuses=(200,), json_data={"success": True})
    executor = OrderExecutor(api_key="k", session=session, max_retries=3, backoff_base=0.0)
    assert _run(executor.cancel_order("o1")) is True
    assert session.requests[0][0] == "DELETE"
    assert session.requests[0][1].endswith("/order/o1")


def test_cancel_order_204_returns_true():
    session = FakeSession(statuses=(204,))
    executor = OrderExecutor(api_key="k", session=session, max_retries=3, backoff_base=0.0)
    assert _run(executor.cancel_order("o1")) is True


def test_cancel_order_failure_returns_false():
    session = FakeSession(statuses=(404,))
    executor = OrderExecutor(api_key="k", session=session, max_retries=3, backoff_base=0.0)
    assert _run(executor.cancel_order("o1")) is False


def test_cancel_order_exhausts_retries_returns_false():
    session = FakeSession(statuses=(429, 429, 429, 429))
    executor = OrderExecutor(api_key="k", session=session, max_retries=3, backoff_base=0.0)
    assert _run(executor.cancel_order("o1")) is False


def test_cancel_order_rejects_empty_id():
    executor = OrderExecutor(api_key="k", session=FakeSession())
    with pytest.raises(OrderValidationError):
        _run(executor.cancel_order(""))


def test_cancel_order_retries_on_429_then_succeeds():
    session = FakeSession(statuses=(429, 200), json_data={"success": True})
    executor = OrderExecutor(api_key="k", session=session, max_retries=3, backoff_base=0.01)
    assert _run(executor.cancel_order("o1")) is True
    assert session.calls == 2
