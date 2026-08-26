import asyncio

import pytest

from execution.order_executor import (
    OrderExecutor,
    OrderExecutorError,
    OrderValidationError,
)


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------
def test_init_defaults():
    executor = OrderExecutor()
    assert executor.rpc_client is None
    assert executor.max_retries == 3
    assert executor.retry_delay == 0.1
    assert executor.attempts == 0


def test_init_with_rpc_client():
    client = object()
    executor = OrderExecutor(rpc_client=client, max_retries=5, retry_delay=0.0)
    assert executor.rpc_client is client
    assert executor.max_retries == 5
    assert executor.retry_delay == 0.0


def test_init_rejects_negative_max_retries():
    with pytest.raises(ValueError):
        OrderExecutor(max_retries=-1)


def test_init_rejects_negative_retry_delay():
    with pytest.raises(ValueError):
        OrderExecutor(retry_delay=-0.5)


# ---------------------------------------------------------------------------
# Payload building
# ---------------------------------------------------------------------------
def test_build_payload_valid():
    executor = OrderExecutor()
    payload = executor.build_payload("o1", "m1", "buy", 10.0, 0.5)
    assert payload == {
        "order_id": "o1",
        "market_id": "m1",
        "side": "buy",
        "size": 10.0,
        "price": 0.5,
        "type": "limit",
    }


def test_build_payload_sell_side():
    executor = OrderExecutor()
    payload = executor.build_payload("o2", "m1", "sell", 1, 0.99)
    assert payload["side"] == "sell"
    assert payload["size"] == 1.0
    assert payload["price"] == 0.99


def test_build_payload_includes_maker():
    executor = OrderExecutor()
    payload = executor.build_payload("o3", "m1", "buy", 5, 0.4, maker="0xabc")
    assert payload["maker"] == "0xabc"


def test_build_payload_rejects_bad_side():
    executor = OrderExecutor()
    with pytest.raises(OrderValidationError):
        executor.build_payload("o1", "m1", "hold", 10, 0.5)


def test_build_payload_rejects_non_positive_size():
    executor = OrderExecutor()
    with pytest.raises(OrderValidationError):
        executor.build_payload("o1", "m1", "buy", 0, 0.5)
    with pytest.raises(OrderValidationError):
        executor.build_payload("o1", "m1", "buy", -1, 0.5)


def test_build_payload_rejects_out_of_range_price():
    executor = OrderExecutor()
    with pytest.raises(OrderValidationError):
        executor.build_payload("o1", "m1", "buy", 10, 0.0)
    with pytest.raises(OrderValidationError):
        executor.build_payload("o1", "m1", "buy", 10, 1.5)


def test_build_payload_rejects_missing_ids():
    executor = OrderExecutor()
    with pytest.raises(OrderValidationError):
        executor.build_payload("", "m1", "buy", 10, 0.5)
    with pytest.raises(OrderValidationError):
        executor.build_payload("o1", "", "buy", 10, 0.5)


def test_build_cancel_payload():
    executor = OrderExecutor()
    payload = executor.build_cancel_payload("o1")
    assert payload == {"order_id": "o1", "type": "cancel"}


def test_build_cancel_payload_rejects_empty_id():
    executor = OrderExecutor()
    with pytest.raises(OrderValidationError):
        executor.build_cancel_payload("")


# ---------------------------------------------------------------------------
# Exception / retry handling (async via asyncio.run)
# ---------------------------------------------------------------------------
class FakeRpc:
    def __init__(self, fail_times=0, explode=False):
        self.fail_times = fail_times
        self.explode = explode
        self.calls = 0

    async def submit_order(self, payload):
        self.calls += 1
        if self.explode:
            raise RuntimeError("boom")
        if self.calls <= self.fail_times:
            raise ConnectionError("transient")
        return {"status": "ok", "calls": self.calls}


def _run(coro):
    return asyncio.run(coro)


def test_execute_success_first_try():
    rpc = FakeRpc(fail_times=0)
    executor = OrderExecutor(rpc_client=rpc, max_retries=3, retry_delay=0.0)
    result = _run(executor.execute({"order_id": "o1"}))
    assert result == {"status": "ok", "calls": 1}
    assert executor.attempts == 1
    assert rpc.calls == 1


def test_execute_retries_then_succeeds():
    rpc = FakeRpc(fail_times=2)
    executor = OrderExecutor(rpc_client=rpc, max_retries=3, retry_delay=0.0)
    result = _run(executor.execute({"order_id": "o1"}))
    assert result["status"] == "ok"
    assert executor.attempts == 3
    assert rpc.calls == 3


def test_execute_exhausts_retries_and_raises():
    rpc = FakeRpc(explode=True)
    executor = OrderExecutor(rpc_client=rpc, max_retries=2, retry_delay=0.0)
    with pytest.raises(OrderExecutorError) as excinfo:
        _run(executor.execute({"order_id": "o1"}))
    assert executor.attempts == 3
    assert rpc.calls == 3
    assert isinstance(excinfo.value.__cause__, RuntimeError)


def test_execute_without_rpc_client_raises():
    executor = OrderExecutor(rpc_client=None, max_retries=0, retry_delay=0.0)
    with pytest.raises(OrderExecutorError):
        _run(executor.execute({"order_id": "o1"}))


def test_place_order_combines_build_and_execute():
    rpc = FakeRpc(fail_times=0)
    executor = OrderExecutor(rpc_client=rpc, max_retries=1, retry_delay=0.0)
    result = _run(executor.place_order("o1", "m1", "buy", 10, 0.5))
    assert result["status"] == "ok"
    assert rpc.calls == 1


def test_place_order_propagates_validation_error():
    executor = OrderExecutor(rpc_client=FakeRpc())
    with pytest.raises(OrderValidationError):
        _run(executor.place_order("o1", "m1", "buy", -1, 0.5))
