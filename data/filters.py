"""
Фильтрует рынки Polymarket по ликвидности, спреду и объему.

Этот модуль содержит функции для проверки рынков на соответствие заданным критериям ликвидности, спреда и объема. Также включены функции для фильтрации рынков, которые проходят все три гейта и для получения причин отказа при непрохождении гейтов.
"""

from __future__ import annotations
from typing import List, Optional
from core.models import Market
import logging

logger = logging.getLogger(__name__)

def passes_liquidity_gate(market: Market, min_liquidity: Optional[float]) -> bool:
    """
    Проверяет, проходит ли рынок гейт ликвидности.

    :param market: Рынок для проверки.
    :param min_liquidity: Минимальная ликвидность для прохождения гейта ликвидности.
    :return: True, если рынок проходит гейт ликвидности, иначе False.
    """
    if min_liquidity is None:
        return True
    return market.liquidity >= min_liquidity

def passes_spread_gate(market: Market, max_spread: Optional[float]) -> bool:
    """
    Проверяет, проходит ли рынок гейт спреда.

    :param market: Рынок для проверки.
    :param max_spread: Максимальный спред для прохождения гейта спреда.
    :return: True, если рынок проходит гейт спреда, иначе False.
    """
    if max_spread is None:
        return True
    return market.spread <= max_spread

def passes_volume_gate(market: Market, min_volume: Optional[float]) -> bool:
    """
    Проверяет, проходит ли рынок гейт объема.

    :param market: Рынок для проверки.
    :param min_volume: Минимальный объем за 24 часа для прохождения гейта объема.
    :return: True, если рынок проходит гейт объема, иначе False.
    """
    if min_volume is None:
        return True
    return market.volume_24h >= min_volume

def passes_all_gates(market: Market, min_liquidity: Optional[float], max_spread: Optional[float], min_volume: Optional[float]) -> bool:
    """
    Проверяет, проходит ли рынок все три гейта (ликвидность, спред и объем).

    :param market: Рынок для проверки.
    :param min_liquidity: Минимальная ликвидность для прохождения гейта ликвидности.
    :param max_spread: Максимальный спред для прохождения гейта спреда.
    :param min_volume: Минимальный объем за 24 часа для прохождения гейта объема.
    :return: True, если рынок проходит все три гейта, иначе False.
    """
    if min_liquidity is None and max_spread is None and min_volume is None:
        return True
    return (passes_liquidity_gate(market, min_liquidity) and
            passes_spread_gate(market, max_spread) and
            passes_volume_gate(market, min_volume))

def gate_reject_reasons(market: Market, min_liquidity: Optional[float], max_spread: Optional[float], min_volume: Optional[float]) -> List[str]:
    """
    Возвращает список причин, по которым рынок не проходит гейты фильтрации.

    :param market: Рынок для проверки.
    :param min_liquidity: Минимальная ликвидность для прохождения гейта ликвидности.
    :param max_spread: Максимальный спред для прохождения гейта спреда.
    :param min_volume: Минимальный объем за 24 часа для прохождения гейта объема.
    :return: Список строк-причин отказа (low_liquidity, wide_spread, low_volume).
    """
    reasons = []
    if not passes_liquidity_gate(market, min_liquidity):
        reasons.append('low_liquidity')
    if not passes_spread_gate(market, max_spread):
        reasons.append('wide_spread')
    if not passes_volume_gate(market, min_volume):
        reasons.append('low_volume')
    return reasons

def filter_markets(markets: List[Market], min_liquidity: Optional[float], max_spread: Optional[float], min_volume: Optional[float]) -> List[Market]:
    """
    Фильтрует рынки, проходящие все три гейта.

    :param markets: Список рынков для фильтрации.
    :param min_liquidity: Минимальная ликвидность для прохождения гейта ликвидности.
    :param max_spread: Максимальный спред для прохождения гейта спреда.
    :param min_volume: Минимальный объем за 24 часа для прохождения гейта объема.
    :return: Список фильтрованных рынков.
    """
    if not markets:
        return []
    try:
        return [market for market in markets if passes_all_gates(market, min_liquidity, max_spread, min_volume)]
    except (AttributeError, TypeError) as e:
        logger.exception("Ошибка при фильтрации рынков")
        return []
