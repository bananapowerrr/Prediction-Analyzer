def score_market(m):
    liquidity = getattr(m, "liquidity", 0) or 0
    volume_24h = getattr(m, "volume_24h", 0) or 0
    spread = getattr(m, "spread", 0) or 0

    score = liquidity * 0.5 + volume_24h * 0.3 - spread * 100
    return float(score)


def rank_markets(markets):
    return sorted(markets, key=score_market, reverse=True)
