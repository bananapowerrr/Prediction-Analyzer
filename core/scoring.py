from typing import List, Dict, Any

def score_market(market: Dict[str, Any]) -> float:
    """
    Оценивает рынок на основе его ликвидности, объема за 24 часа и спреда.

    :param market: Объект рынка с атрибутами liquidity, volume_24h и spread.
    :return: Оценка рынка в виде числа.
    """
    liquidity = market.get("liquidity", 0) or 0
    volume_24h = market.get("volume_24h", 0) or 0
    spread = market.get("spread", 0) or 0

    score = liquidity * 0.5 + volume_24h * 0.3 - spread * 100
    return float(score)


def rank_markets(markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Сортирует рынки по их оценке в порядке убывания.

    :param markets: Список объектов рынка.
    :return: Отсортированный список рынков по убыванию оценки.
    """
    return sorted(markets, key=score_market, reverse=True)


__all__ = ["score_market", "rank_markets"]
