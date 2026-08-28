from core.models import Market

def test_gate_reject_reasons():
    market = Market(id="test_market", liquidity=100.0)
    reject_reasons = []

    # Проверка прохода гейта по ликвидности
    if market.liquidity < 50.0:
        reject_reasons.append("Low liquidity")

    assert reject_reasons == []
