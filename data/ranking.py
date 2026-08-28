from typing import List, Optional
from core.models import Market


def calculate_score(market: Market) -> float:
    return market.liquidity * 0.5 + market.volume_24h * 0.3 - market.spread * 1000 * 0.2


def rank_markets(markets: Optional[List[Market]] = None) -> List[Market]:
    if markets is None:
        return []

    for m in markets:
        setattr(m, "score", calculate_score(m))

    sorted_markets = sorted(markets, key=lambda m: m.score, reverse=True)

    return sorted_markets
