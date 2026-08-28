"""
Сканер получает рынки через клиент Polymarket и отфильтровывает их гейтами Prediction Analyzer.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass
from core.models import Market, MarketSchema
from data.filters import passes_all_gates
import logging
from pydantic import ValidationError
import telemetry

logger = logging.getLogger(__name__)

@dataclass
class ScanConfig:
    min_liquidity: Optional[float] = None
    max_spread: Optional[float] = None
    min_volume: Optional[float] = None

class MarketScanner:
    """Сканер получает рынки через клиент Polymarket и отфильтровывает их гейтами Prediction Analyzer.
    
    Подклассы должны реализовать метод :meth:`fetch_raw` (получение сырых записей из источника данных)
    и метод :meth:`parse` (конвертация сырых записей в модели ``Market``).
    Метод :meth:`scan` выполняет получение, парсинг и применение гейтов ликвидности/разброса/объема, определенных в ``data.filters``.
    """
    
    def __init__(self, scan_config: Optional[ScanConfig] = None):
        self.scan_config = scan_config or ScanConfig()
    
    def fetch_raw(self) -> list:
        raise NotImplementedError("Subclasses must implement this method")
    
    def parse(self, raw: list) -> List[Market]:
        markets: List[Market] = []
        for i, record in enumerate(raw):
            try:
                schema = MarketSchema(**record)
                markets.append(schema.to_market())
            except ValidationError as e:
                logger.warning("Skipping invalid market record #%d: %s", i, e.errors()[0]["msg"])
            except Exception as e:
                logger.warning("Skipping malformed market record #%d: %s", i, e)
        return markets
    
    def filter_markets(self, markets: List[Market]) -> List[Market]:
        if self.scan_config.min_liquidity is not None:
            markets = [m for m in markets if passes_all_gates(
                m,
                self.scan_config.min_liquidity,
                self.scan_config.max_spread,
                self.scan_config.min_volume,
            )]
        return markets
    
    def scan(self) -> List[Market]:
        raw = self.fetch_raw()
        markets = self.parse(raw)
        logger.info("Parsed %d markets; applying liquidity/spread/volume gates", len(markets))
        filtered = self.filter_markets(markets)
        logger.info("Passed gates: %d/%d", len(filtered), len(markets))
        return filtered

def run_scan(min_liquidity: Optional[float] = None, max_spread: Optional[float] = None, min_volume: Optional[float] = None, limit: Optional[int] = None, sort_by_liquidity: bool = True) -> List[Market]:
    scanner = MarketScanner(ScanConfig(min_liquidity=min_liquidity, max_spread=max_spread, min_volume=min_volume))
    markets = scanner.scan()
    if not markets:
        logger.warning("No markets found after filtering.")
    if sort_by_liquidity:
        markets = sorted(markets, key=lambda m: m.liquidity, reverse=True)
    if limit is not None:
        markets = markets[:limit]
    
    try:
        total = len(markets)
        passed = len([m for m in markets if passes_all_gates(m, min_liquidity, max_spread, min_volume)])
        telemetry.record_scan(total, passed)
    except ImportError:
        logger.debug("telemetry module not available, skipping record_scan")
    
    return markets
