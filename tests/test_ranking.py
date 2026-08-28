from core.models import Market
from data.ranking import calculate_score, rank_markets


def _m(id: str, liq: float = 0, vol: float = 0, sp: float = 0) -> Market:
    return Market(id=id, question=id, liquidity=liq, volume_24h=vol, spread=sp)


def test_empty_list_returns_empty():
    assert rank_markets([]) == []


def test_none_returns_empty():
    assert rank_markets(None) == []


def test_single_market():
    result = rank_markets([_m("A", liq=100)])
    assert len(result) == 1
    assert result[0].id == "A"


def test_sorts_by_score_over_liquidity_desc():
    a = _m("A", liq=100, vol=50)
    b = _m("B", liq=10, vol=500)
    result = rank_markets([a, b])
    ratios = [m.score / m.liquidity for m in result]
    assert ratios == sorted(ratios, reverse=True)


def test_zero_liquidity_pushed_to_end():
    zero = _m("Z", liq=0, vol=100)
    normal = _m("N", liq=10, vol=10)
    result = rank_markets([zero, normal])
    assert result[0].id == "N"
    assert result[1].id == "Z"


def test_score_attribute_set():
    m = _m("X", liq=50, vol=10)
    rank_markets([m])
    assert hasattr(m, "score")
    assert m.score == calculate_score(m)


def test_preserves_order_when_ratios_equal():
    a = _m("A", liq=100, vol=200, sp=0)
    b = _m("B", liq=100, vol=200, sp=0)
    result = rank_markets([a, b])
    ids = [m.id for m in result]
    assert ids == ["A", "B"]
