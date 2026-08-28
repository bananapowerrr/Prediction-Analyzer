import pytest

from core.models import Market
from data.filters import (
    passes_liquidity_gate,
    passes_spread_gate,
    passes_volume_gate,
    passes_all_gates,
    gate_reject_reasons,
    filter_markets,
    passes_soft_gates,
)


def _make_market(**kwargs):
    base = dict(id="market-1", question="Test?", liquidity=1000.0, spread=0.01, volume_24h=500.0)
    base.update(kwargs)
    return Market(**base)


MIN_LIQ = 1000.0
MAX_SPREAD = 0.01
MIN_VOL = 500.0


# --- Market.is_tradeable ---

def test_market_tradeable_when_all_gates_pass():
    market = _make_market()
    assert market.is_tradeable(MIN_LIQ, MAX_SPREAD, MIN_VOL) is True


def test_market_tradeable_boundary_liquidity_equal():
    market = _make_market(liquidity=MIN_LIQ)
    assert market.is_tradeable(MIN_LIQ, MAX_SPREAD, MIN_VOL) is True


def test_market_tradeable_boundary_spread_equal():
    market = _make_market(spread=MAX_SPREAD)
    assert market.is_tradeable(MIN_LIQ, MAX_SPREAD, MIN_VOL) is True


def test_market_tradeable_boundary_volume_equal():
    market = _make_market(volume_24h=MIN_VOL)
    assert market.is_tradeable(MIN_LIQ, MAX_SPREAD, MIN_VOL) is True


def test_market_not_tradeable_low_liquidity():
    market = _make_market(liquidity=MIN_LIQ - 1.0)
    assert market.is_tradeable(MIN_LIQ, MAX_SPREAD, MIN_VOL) is False


def test_market_not_tradeable_wide_spread():
    market = _make_market(spread=MAX_SPREAD + 0.01)
    assert market.is_tradeable(MIN_LIQ, MAX_SPREAD, MIN_VOL) is False


def test_market_not_tradeable_low_volume():
    market = _make_market(volume_24h=MIN_VOL - 1.0)
    assert market.is_tradeable(MIN_LIQ, MAX_SPREAD, MIN_VOL) is False


def test_market_not_tradeable_zero_volume():
    market = _make_market(volume_24h=0.0)
    assert market.is_tradeable(MIN_LIQ, MAX_SPREAD, MIN_VOL) is False


def test_market_not_tradeable_when_liquidity_zero():
    market = _make_market(liquidity=0.0)
    assert market.is_tradeable(0.0, 1.0, 0.0) is True
    assert market.is_tradeable(1.0, 1.0, 0.0) is False


# --- data.filters single gates (inclusive) ---

def test_passes_liquidity_gate():
    market = _make_market(liquidity=500.0)
    assert passes_liquidity_gate(market, 500.0) is True
    assert passes_liquidity_gate(market, 500.01) is False


def test_passes_spread_gate():
    market = _make_market(spread=0.02)
    assert passes_spread_gate(market, 0.02) is True
    assert passes_spread_gate(market, 0.019) is False


def test_passes_volume_gate():
    market = _make_market(volume_24h=100.0)
    assert passes_volume_gate(market, 100.0) is True
    assert passes_volume_gate(market, 100.01) is False


# --- data.filters combined gates ---

def test_passes_all_gates_pass():
    market = _make_market()
    assert passes_all_gates(market, MIN_LIQ, MAX_SPREAD, MIN_VOL) is True


def test_passes_all_gates_fails_when_any_gate_fails():
    low_liq = _make_market(liquidity=MIN_LIQ - 1.0)
    wide_spread = _make_market(spread=MAX_SPREAD + 0.01)
    low_vol = _make_market(volume_24h=MIN_VOL - 1.0)
    assert passes_all_gates(low_liq, MIN_LIQ, MAX_SPREAD, MIN_VOL) is False
    assert passes_all_gates(wide_spread, MIN_LIQ, MAX_SPREAD, MIN_VOL) is False
    assert passes_all_gates(low_vol, MIN_LIQ, MAX_SPREAD, MIN_VOL) is False


def test_passes_all_gates_boundary():
    market = _make_market()
    assert passes_all_gates(market, MIN_LIQ, MAX_SPREAD, MIN_VOL) is True


def test_is_tradeable_consistent_with_passes_all_gates():
    markets = [
        _make_market(liquidity=MIN_LIQ - 10, spread=MAX_SPREAD, volume_24h=MIN_VOL),
        _make_market(liquidity=MIN_LIQ, spread=MAX_SPREAD + 0.1, volume_24h=MIN_VOL),
        _make_market(liquidity=MIN_LIQ, spread=MAX_SPREAD, volume_24h=MIN_VOL - 10),
        _make_market(),
    ]
    for market in markets:
        assert market.is_tradeable(MIN_LIQ, MAX_SPREAD, MIN_VOL) == passes_all_gates(
            market, MIN_LIQ, MAX_SPREAD, MIN_VOL
        )


# --- filter_markets ---

def test_filter_markets_returns_only_tradeable():
    markets = [
        _make_market(id="good", liquidity=10000.0, spread=0.001, volume_24h=1000.0),
        _make_market(id="bad-liq", liquidity=100.0),
        _make_market(id="bad-spread", spread=0.99),
        _make_market(id="bad-vol", volume_24h=1.0),
    ]
    result = filter_markets(markets, MIN_LIQ, MAX_SPREAD, MIN_VOL)
    assert [m.id for m in result] == ["good"]
    assert all(m.is_tradeable(MIN_LIQ, MAX_SPREAD, MIN_VOL) for m in result)


def test_filter_markets_empty_input():
    assert filter_markets([], MIN_LIQ, MAX_SPREAD, MIN_VOL) == []


# --- gate_reject_reasons ---

def test_gate_reject_reasons_no_reasons_when_tradeable():
    market = _make_market()
    assert gate_reject_reasons(market, MIN_LIQ, MAX_SPREAD, MIN_VOL) == []


def test_gate_reject_reasons_low_liquidity():
    market = _make_market(liquidity=MIN_LIQ - 1.0)
    assert gate_reject_reasons(market, MIN_LIQ, MAX_SPREAD, MIN_VOL) == ["low_liquidity"]


def test_gate_reject_reasons_wide_spread():
    market = _make_market(spread=MAX_SPREAD + 0.01)
    assert gate_reject_reasons(market, MIN_LIQ, MAX_SPREAD, MIN_VOL) == ["wide_spread"]


def test_gate_reject_reasons_low_volume():
    market = _make_market(volume_24h=MIN_VOL - 1.0)
    assert gate_reject_reasons(market, MIN_LIQ, MAX_SPREAD, MIN_VOL) == ["low_volume"]


def test_gate_reject_reasons_multiple():
    market = _make_market(liquidity=0.0, spread=0.99, volume_24h=0.0)
    reasons = gate_reject_reasons(market, MIN_LIQ, MAX_SPREAD, MIN_VOL)
    assert reasons == ["low_liquidity", "wide_spread", "low_volume"]


# --- passes_soft_gates ---

def test_passes_soft_gates_tradeable_market():
    market = _make_market()
    assert passes_soft_gates(market, MIN_LIQ, MAX_SPREAD, MIN_VOL) is True


def test_passes_soft_gates_marginally_below_hard_gates():
    market = _make_market(
        liquidity=MIN_LIQ * 0.75,
        spread=MAX_SPREAD * 1.25,
        volume_24h=MIN_VOL * 0.75,
    )
    assert market.is_tradeable(MIN_LIQ, MAX_SPREAD, MIN_VOL) is False
    assert passes_soft_gates(market, MIN_LIQ, MAX_SPREAD, MIN_VOL) is True


def test_passes_soft_gates_fails_below_soft_thresholds():
    market = _make_market(liquidity=MIN_LIQ * 0.49)
    assert passes_soft_gates(market, MIN_LIQ, MAX_SPREAD, MIN_VOL) is False


# --- Boundary tests for Market.is_tradeable ---

def test_market_tradeable_boundary_liquidity_above():
    market = _make_market(liquidity=MIN_LIQ + 1.0)
    assert market.is_tradeable(MIN_LIQ, MAX_SPREAD, MIN_VOL) is True


def test_market_tradeable_boundary_spread_below():
    market = _make_market(spread=MAX_SPREAD - 0.01)
    assert market.is_tradeable(MIN_LIQ, MAX_SPREAD, MIN_VOL) is True


def test_market_tradeable_boundary_volume_above():
    market = _make_market(volume_24h=MIN_VOL + 1.0)
    assert market.is_tradeable(MIN_LIQ, MAX_SPREAD, MIN_VOL) is True
