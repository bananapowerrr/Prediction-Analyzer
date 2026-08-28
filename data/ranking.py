from core.scoring import score_market
from typing import List
from data.polymarket_client import Market

def rank_markets(markets: List[Market]) -> List[Market]:
    """
    Сортирует рынки по их оценке в порядке убывания.

    :param markets: Список рынков для сортировки.
    :return: Отсортированный список рынков по оценке.
    """
    return sorted(markets, key=score_market, reverse=True)
