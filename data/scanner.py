from core.models import Market
from data.filters import passes_liquidity_gate, passes_spread_gate
from data.polymarket_client import PolymarketClient

def run_scan(min_liquidity: float = 1000.0, max_spread: float = 0.1, limit: int = 50) -> list:
    client = PolymarketClient()
    raw = client.fetch_markets(limit=limit)
    return [
        Market(
            id=str(item.get("id", "")),
            question=str(item.get("question", "")),
            liquidity=float(item.get("liquidity") or 0),
            spread=float(item.get("spread") or 0),
            volume_24h=float(item.get("volume_24h") or item.get("volume24hr") or 0),
        )
        for item in raw
        if isinstance(item, dict)
        and passes_liquidity_gate(Market(**item), min_liquidity)
        and passes_spread_gate(Market(**item), max_spread)
    ]
