from core.models import Market
from data.filters import passes_liquidity_gate, passes_spread_gate
from data.polymarket_client import PolymarketClient
from config import MIN_LIQUIDITY_USD, MAX_SPREAD_PCT, SCAN_LIMIT

def _f(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default

def run_scan(min_liquidity: float = MIN_LIQUIDITY_USD, max_spread: float = MAX_SPREAD_PCT, limit: int = SCAN_LIMIT) -> list:
    client = PolymarketClient()
    raw = client.fetch_markets(limit=limit)
    out = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        m = Market(
            id=item.get("id", ""),
            question=item.get("question", ""),
            liquidity=_f(item.get("liquidity", 0)),
            spread=_f(item.get("spread", 0)),
            volume_24h=_f(item.get("volume_24h", item.get("volume24hr", 0))),
        )
        if passes_liquidity_gate(m, min_liquidity) and passes_spread_gate(m, max_spread):
            out.append(m)
    out.sort(key=lambda m: m.liquidity, reverse=True)
    return out
