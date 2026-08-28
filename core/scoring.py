# создано диспетчером для привязки Aider

from data.filters import passes_liquidity_gate, passes_spread_gate, passes_volume_gate

def score_market(market, min_liquidity=100000, max_spread=0.01, min_volume_24h=100000):
    """
    Оценивает качество рынка на основе ликвидности, спреда и объема за 24 часа.

    :param market: объект рынка
    :param min_liquidity: минимальная ликвидность для рынка
    :param max_spread: максимальный спред для рынка
    :param min_volume_24h: минимальный объем за 24 часа для рынка
    :return: оценка рынка в диапазоне [0, 1]
    """
    liquidity_score = passes_liquidity_gate(market, min_liquidity)
    spread_score = passes_spread_gate(market, max_spread)
    volume_score = passes_volume_gate(market, min_volume_24h)

    total_score = liquidity_score + spread_score + volume_score
    max_score = 3

    if total_score == 0:
        return 0

    return total_score / max_score
