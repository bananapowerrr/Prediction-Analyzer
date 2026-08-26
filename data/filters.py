from core.models import Market

def passes_liquidity_gate(market: Market, min_liquidity: float) -> bool:
    return market.liquidity >= min_liquidity

def passes_spread_gate(market: Market, max_spread: float) -> bool:
    return market.spread <= max_spread

def passes_volume_gate(market: Market, min_volume: float) -> bool:
    return market.volume_24h >= min_volume
