import os
import pytest

from config import Settings, RpcSettings, LiquidityGateSettings, SpreadSettings, ConnectionSettings
from risk_engine import (
    passes_liquidity_gate,
    passes_spread_gate,
    calculate_expected_value,
    calculate_fractional_kelly,
    determine_position_size,
    Market,
)
from state_manager import StateManager


# Тесты для config.py
def test_settings_defaults():
    settings = Settings()
    assert settings.rpc is not None
    assert settings.liquidity_gate is not None
    assert settings.spread is not None
    assert settings.connection is not None


def test_rpc_settings_defaults():
    rpc = RpcSettings()
    assert rpc.endpoint == "https://polygon-rpc.com"
    assert rpc.chain_id == 137
    assert rpc.private_key == ""


def test_liquidity_gate_settings_defaults():
    gate = LiquidityGateSettings()
    assert gate.min_liquidity_usd == 1000.0
    assert gate.min_volume_24h == 0.0


def test_spread_settings_defaults():
    spread = SpreadSettings()
    assert spread.max_spread_pct == 0.1


def test_connection_settings_defaults():
    conn = ConnectionSettings()
    assert conn.gamma_api_base == "https://gamma-api.polymarket.com"
    assert conn.http_timeout == 30.0
    assert conn.scan_limit == 50


# Тесты для risk_engine.py
def _make_market(**kwargs):
    base = dict(id="test_market", liquidity=1000.0, spread=0.05, volume=500.0)
    base.update(kwargs)
    return Market(**base)


def test_passes_liquidity_gate():
    market = _make_market(liquidity=1000.0)
    assert passes_liquidity_gate(market, min_liquidity=500.0) is True
    assert passes_liquidity_gate(market, min_liquidity=1500.0) is False


def test_passes_spread_gate():
    market = _make_market(spread=0.05)
    assert passes_spread_gate(market, max_spread=0.03) is False
    assert passes_spread_gate(market, max_spread=0.1) is True


def test_calculate_expected_value():
    market = _make_market(liquidity=1000.0)
    ev = calculate_expected_value(market, {"win": 0.6, "loss": 0.4})
    assert ev == pytest.approx(200.0)


def test_calculate_expected_value_no_matching_outcomes():
    market = _make_market(liquidity=1000.0)
    ev = calculate_expected_value(market, {"yes": 0.6, "no": 0.4})
    assert ev == 0.0


def test_calculate_fractional_kelly_clamped():
    market = _make_market(liquidity=1000.0, spread=0.05)
    kelly = calculate_fractional_kelly(market, {"win": 0.6, "loss": 0.4})
    assert 0.0 <= kelly <= 1.0


def test_determine_position_size():
    market = _make_market(liquidity=1000.0, spread=0.05)
    size = determine_position_size(market, {"win": 0.6, "loss": 0.4}, 10000.0)
    assert size >= 0.0
    assert size == pytest.approx(10000.0 * calculate_fractional_kelly(market, {"win": 0.6, "loss": 0.4}))


# Тесты для state_manager.py
def test_state_manager_creation(tmp_path):
    db_path = str(tmp_path / "state.db")
    manager = StateManager(db_path=db_path)
    assert manager.db_path == db_path
    manager.close()


def test_save_and_get_event(tmp_path):
    db_path = str(tmp_path / "state.db")
    manager = StateManager(db_path=db_path)
    manager.save_event(event_type="test_event", data={"key": "value"})
    events = manager.get_events()
    assert len(events) == 1
    assert events[0]["event_type"] == "test_event"
    assert events[0]["data"] == "{'key': 'value'}"
    manager.close()


def test_get_events_by_type(tmp_path):
    db_path = str(tmp_path / "state.db")
    manager = StateManager(db_path=db_path)
    manager.save_event(event_type="a", data={"n": 1})
    manager.save_event(event_type="b", data={"n": 2})
    events = manager.get_events(event_type="a")
    assert len(events) == 1
    assert events[0]["event_type"] == "a"
    manager.close()
