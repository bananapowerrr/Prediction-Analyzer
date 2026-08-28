from typing import List, Optional
from core.models import Market


def calculate_score(market: Market) -> float:
    return market.liquidity * 0.5 + market.volume_24h * 0.3 - market.spread * 1000 * 0.2


def rank_markets(markets: Optional[List[Market]] = None) -> List[Market]:
    """
    Сортирует рынки по их оценке.

    Оценка вычисляется по формуле:
    score = liquidity * 0.5 + volume_24h * 0.3 - spread * 1000 * 0.2

    Рынки с наибольшей оценкой будут первыми в списке.

    :param markets: Список рынков для сортировки. Если None, возвращает пустой список.
    :return: Отсортированный список рынков по оценке.
    """
    if not markets:
        return []

    for m in markets:
        setattr(m, "score", calculate_score(m))

    def _ratio(m: Market) -> float:
        if m.liquidity == 0:
            return float("-inf")
        return m.score / m.liquidity

    return sorted(markets, key=_ratio, reverse=True)
