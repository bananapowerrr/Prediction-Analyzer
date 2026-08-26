from core.models import Market
from data.filters import passes_liquidity_gate, passes_spread_gate, passes_volume_gate, passes_all_gates

def test_liquidity_and_spread():
    m = Market(id="1", question="q", liquidity=2000.0, spread=0.05, volume_24h=0.0)
    assert passes_liquidity_gate(m, 1000.0) is True
    assert passes_liquidity_gate(m, 3000.0) is False
    assert passes_spread_gate(m, 0.1) is True
    assert passes_spread_gate(m, 0.01) is False

def test_volume_gate():
    m = Market(id="1", question="q", liquidity=1000.0, spread=0.05, volume_24h=100.0)
    assert passes_volume_gate(m, 50.0) is True
    assert passes_volume_gate(m, 200.0) is False

def test_passes_all_gates():
    m = Market(id="1", question="q", liquidity=2000.0, spread=0.05, volume_24h=100.0)
    assert passes_all_gates(m, 1000.0, 0.1, 50.0) is True
    assert passes_all_gates(m, 3000.0, 0.01, 200.0) is False
    assert passes_all_gates(m, 1000.0, 0.1, 200.0) is False
    assert passes_all_gates(m, 3000.0, 0.01, 50.0) is False
