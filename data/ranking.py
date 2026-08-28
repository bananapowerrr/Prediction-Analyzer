from core.scoring import score_market
from typing import List, Optional
from data.polymarket_client import Market

def rank_markets(markets: List[Market], limit: Optional[int] = None) -> List[Market]:
    """
    Сортирует рынки по их оценке в порядке убывания.

    :param markets: Список рынков для сортировки.
    :param limit: Опциональный параметр для ограничения количества возвращаемых рынков.
    :return: Отсортированный список рынков по оценке.
    """
    sorted_markets = sorted(markets, key=score_market, reverse=True)
    return sorted_markets[:limit] if limit is not None else sorted_markets
