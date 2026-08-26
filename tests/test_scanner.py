from core.models import Market
from data.filters import passes_liquidity_gate, passes_spread_gate
from data.scanner import filter_by_volume_threshold


def _make_market(**kwargs) -> Market:
    base = dict(id="m1", question="q", liquidity=1000.0, spread=0.05, volume_24h=500.0)
    base.update(kwargs)
    return Market(**base)


def test_passes_liquidity_gate():
    """Market passes the liquidity gate only when liquidity >= threshold."""
    market = _make_market(liquidity=1000.0)
    assert passes_liquidity_gate(market, min_liquidity=500.0) is True
    assert passes_liquidity_gate(market, min_liquidity=1500.0) is False


def test_passes_spread_gate():
    """Market passes the spread gate only when spread <= threshold."""
    market = _make_market(spread=0.05)
    assert passes_spread_gate(market, max_spread=0.03) is False
    assert passes_spread_gate(market, max_spread=0.1) is True


def test_filter_by_volume_threshold():
    """Only markets with 24h volume >= min_volume are retained."""
    low = _make_market(id="low", volume_24h=100.0)
    high = _make_market(id="high", volume_24h=1000.0)
    markets = [low, high]

    assert filter_by_volume_threshold(markets, min_volume=500.0) == [high]
    assert filter_by_volume_threshold(markets, min_volume=2000.0) == []
    assert filter_by_volume_threshold(markets, min_volume=50.0) == [low, high]
