"""Проверка, что числовые константы конфигурации являются числами >= 0."""
import math
from numbers import Number

from config import (
    BASE_RPC_CHAIN_ID,
    BASE_RPC_COOLDOWN,
    CLOUD_MAX_CONCURRENT,
    CLOUD_TIMEOUT,
    HTTP_TIMEOUT,
    LOCAL_TEMPERATURE,
    LOCAL_TIMEOUT,
    MAX_SPREAD_PCT,
    MIN_LIQUIDITY_USD,
    MIN_VOLUME_24H,
    RPC_CHAIN_ID,
    RPC_COOLDOWN,
    RPC_MAX_RETRIES,
    RPC_REQUEST_TIMEOUT,
    RPC_TIMEOUT,
    SCAN_LIMIT,
)

NUMERIC_CONSTANTS = (
    MIN_LIQUIDITY_USD,
    MIN_VOLUME_24H,
    MAX_SPREAD_PCT,
    SCAN_LIMIT,
    HTTP_TIMEOUT,
    BASE_RPC_CHAIN_ID,
    RPC_CHAIN_ID,
    RPC_COOLDOWN,
    RPC_MAX_RETRIES,
    RPC_TIMEOUT,
    RPC_REQUEST_TIMEOUT,
    BASE_RPC_COOLDOWN,
    CLOUD_TIMEOUT,
    CLOUD_MAX_CONCURRENT,
    LOCAL_TIMEOUT,
    LOCAL_TEMPERATURE,
)


def test_all_numeric_constants_are_numbers():
    for constant in NUMERIC_CONSTANTS:
        assert isinstance(constant, Number), f"Ожидалось число, получено: {constant!r}"


def test_all_numeric_constants_are_finite():
    for constant in NUMERIC_CONSTANTS:
        assert math.isfinite(constant), f"Ожидалось конечное число, получено: {constant!r}"


def test_all_numeric_constants_are_non_negative():
    for constant in NUMERIC_CONSTANTS:
        assert constant >= 0, f"Ожидалось число >= 0, получено: {constant!r}"
