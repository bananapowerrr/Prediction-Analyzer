from core.models import Market
from data.filters import passes_liquidity_gate, passes_spread_gate
from data.polymarket_client import PolymarketClient

def run_scan(min_liquidity: float = 1000.0, max_spread: float = 0.1, limit: int = 50) -> list:
    client = PolymarketClient()
    raw = client.fetch_markets(limit=limit)
    out = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        m = Market(
            id=item.get("id", ""),
            question=item.get("question", ""),
            liquidity=float(item.get("liquidity", 0)),
            spread=float(item.get("spread", 0)),
            volume_24h=float(item.get("volume_24h", item.get("volume24hr", 0))),
        )
        if passes_liquidity_gate(m, min_liquidity) and passes_spread_gate(m, max_spread):
            out.append(m)
    return out
