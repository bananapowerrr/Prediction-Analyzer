"""
Файл фильтрует рынки Polymarket по ликвидности, спреду и объёму.
passes_all_gates объединяет три гейта.
"""

from core.models import Market

def passes_liquidity_gate(market: Market, min_liquidity: float) -> bool:
    return market.liquidity >= min_liquidity

def passes_spread_gate(market: Market, max_spread: float) -> bool:
    return market.spread <= max_spread

def passes_volume_gate(market: Market, min_volume: float) -> bool:
    return market.volume_24h >= min_volume

def passes_all_gates(market: Market, min_liquidity: float, max_spread: float, min_volume: float) -> bool:
    return (passes_liquidity_gate(market, min_liquidity) and
            passes_spread_gate(market, max_spread) and
            passes_volume_gate(market, min_volume))
