from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

import config
from core.models import Market
from data.filters import passes_all_gates
from data.polymarket_client import PolymarketClient

logger = logging.getLogger(__name__)


def _to_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass
class ScanConfig:
    min_liquidity: float = config.MIN_LIQUIDITY_USD
    max_spread: float = config.MAX_SPREAD_PCT
    min_volume: float = config.MIN_VOLUME_24H
    limit: int = config.SCAN_LIMIT


class MarketScanner:
    """Base class for ingesting and filtering prediction-market data.

    Subclasses must implement :meth:`fetch_raw` (retrieve raw records from a
    data source) and :meth:`parse` (convert raw records into ``Market`` models).
    The :meth:`scan` method fetches, parses and applies the liquidity/spread/
    volume gates defined in ``data.filters``.
    """

    def __init__(self, scan_config: Optional[ScanConfig] = None):
        self.config = scan_config or ScanConfig()

    def fetch_raw(self) -> list:
        raise NotImplementedError

    def parse(self, raw: list) -> List[Market]:
        raise NotImplementedError

    def filter_markets(self, markets: List[Market]) -> List[Market]:
        return [
            m
            for m in markets
            if passes_all_gates(
                m,
                self.config.min_liquidity,
                self.config.max_spread,
                self.config.min_volume,
            )
        ]

    def scan(self) -> List[Market]:
        raw = self.fetch_raw()
        markets = self.parse(raw)
        logger.info("Parsed %d markets; applying liquidity/spread/volume gates", len(markets))
        filtered = self.filter_markets(markets)
        logger.info("Passed gates: %d/%d", len(filtered), len(markets))
        return filtered


class PolymarketScanner(MarketScanner):
    """Scanner backed by the Polymarket Gamma API."""

    def __init__(
        self,
        client: Optional[PolymarketClient] = None,
        scan_config: Optional[ScanConfig] = None,
    ):
        super().__init__(scan_config)
        self.client = client or PolymarketClient(timeout=config.HTTP_TIMEOUT)

    def fetch_raw(self) -> list:
        return self.client.fetch_markets(limit=self.config.limit)

    def parse(self, raw: list) -> List[Market]:
        markets: List[Market] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            market_id = item.get("id")
            if not market_id:
                continue
            markets.append(
                Market(
                    id=str(market_id),
                    question=item.get("question", ""),
                    liquidity=_to_float(item.get("liquidity")),
                    spread=self._extract_spread(item),
                    volume_24h=_to_float(item.get("volume24hr")),
                )
            )
        return markets

    @staticmethod
    def _extract_spread(item: dict) -> float:
        if item.get("spread") is not None:
            return _to_float(item.get("spread"))
        try:
            best_bid = _to_float(item.get("bestBid"))
            best_ask = _to_float(item.get("bestAsk"))
            if best_ask > 0 and best_bid > 0:
                return best_ask - best_bid
        except (TypeError, ValueError):
            pass
        return 0.0


def scan_markets(
    min_liquidity: Optional[float] = None,
    max_spread: Optional[float] = None,
    min_volume: Optional[float] = None,
    limit: Optional[int] = None,
) -> List[Market]:
    """Convenience entry point for Phase I data ingestion."""
    cfg = ScanConfig(
        min_liquidity=min_liquidity if min_liquidity is not None else config.MIN_LIQUIDITY_USD,
        max_spread=max_spread if max_spread is not None else config.MAX_SPREAD_PCT,
        min_volume=min_volume if min_volume is not None else config.MIN_VOLUME_24H,
        limit=limit if limit is not None else config.SCAN_LIMIT,
    )
    return PolymarketScanner(scan_config=cfg).scan()
