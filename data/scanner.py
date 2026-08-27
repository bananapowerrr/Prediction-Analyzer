from typing import List, Dict, Optional
from dataclasses import dataclass
from core.models import Market
from data.filters import passes_all_gates
import logging

logger = logging.getLogger(__name__)

@dataclass
class ScanConfig:
    min_liquidity: Optional[float] = None
    max_spread: Optional[float] = None
    min_volume: Optional[float] = None

class MarketScanner:
    """Base class for ingesting and filtering prediction-market data.
    
    Subclasses must implement :meth:`fetch_raw` (retrieve raw records from a
    data source) and :meth:`parse` (convert raw records into ``Market`` 
models).
    The :meth:`scan` method fetches, parses and applies the liquidity/spread/
    volume gates defined in ``data.filters``.
    """
    
    def __init__(self, scan_config: Optional[ScanConfig] = None):
        self.scan_config = scan_config or ScanConfig()
    
    def fetch_raw(self) -> list:
        raise NotImplementedError("Subclasses must implement this method")
    
    def parse(self, raw: list) -> List[Market]:
        raise NotImplementedError("Subclasses must implement this method")
    
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
