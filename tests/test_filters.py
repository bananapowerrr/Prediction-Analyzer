from core.models import Market
from data.filters import passes_liquidity_gate, passes_spread_gate

def test_liquidity_and_spread():
    m = Market(id="1", question="q", liquidity=2000.0, spread=0.05, volume_24h=0.0)
    assert passes_liquidity_gate(m, 1000.0) is True
    assert passes_liquidity_gate(m, 3000.0) is False
    assert passes_spread_gate(m, 0.1) is True
    assert passes_spread_gate(m, 0.01) is False
