from typing import List, Optional
from core.models import Market


def rank_markets(markets: List[Market], limit: Optional[int] = None) -> List[Market]:
    """
    Сортирует рынки по score (если есть атрибут) или liquidity в порядке убывания.

    :param markets: Список рынков для сортировки.
    :param limit: Опциональный параметр для ограничения количества возвращаемых рынков.
    :return: Отсортированный список рынков.
    """
    has_score = all(hasattr(m, "score") for m in markets) and all(
        m.score is not None for m in markets if hasattr(m, "score")
    )

    if has_score:
        sorted_markets = sorted(markets, key=lambda m: m.score, reverse=True)
    else:
        sorted_markets = sorted(markets, key=lambda m: m.liquidity, reverse=True)

    return sorted_markets[:limit] if limit is not None else sorted_markets
