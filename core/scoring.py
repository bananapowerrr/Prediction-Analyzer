def score_market(market):
    liquidity = getattr(market, "liquidity", 0) or 0
    volume_24h = getattr(market, "volume_24h", 0) or 0
    spread = getattr(market, "spread", 0) or 0

    score = liquidity * 0.5 + volume_24h * 0.3 - spread * 100
    return float(score)


def rank_markets(markets):
    return sorted(markets, key=score_market, reverse=True)


__all__ = ["score_market", "rank_markets"]
