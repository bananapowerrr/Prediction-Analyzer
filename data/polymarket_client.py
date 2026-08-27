import asyncio
import logging
from typing import List, Optional, Dict

from pydantic import ValidationError
from core.models import MarketSchema

logger = logging.getLogger(__name__)


class PolymarketClient:
    BASE = "https://api.polymarket.com"
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
    
    async def fetch_markets(self, limit: int = 50) -> List[Dict]:
        logger.debug("Fetching markets (limit=%d) from %s", limit, self.BASE)
        return []
    
    async def fetch_market_details(self, market_id: str) -> Optional[Dict]:
        logger.debug("Fetching market details for %s", market_id)
        return None
    
    async def fetch_prices(self) -> Dict[str, float]:
        return {}
    
    async def fetch_spreads(self) -> Dict[str, float]:
        return {}
    
    async def fetch_volumes(self) -> Dict[str, float]:
        return {}
    
    async def close(self):
        pass


class PolymarketAdapter:
    def __init__(self, client: PolymarketClient):
        self.client = client
    
    async def fetch_validated_markets(self, limit: int = 50) -> List[MarketSchema]:
        raw_markets = await self.client.fetch_markets(limit)
        validated: List[MarketSchema] = []
        for i, raw in enumerate(raw_markets):
            try:
                schema = MarketSchema(**raw)
                validated.append(schema)
            except ValidationError as e:
                logger.warning("Skipping invalid market #%d from API: %s", i, e.errors()[0]["msg"])
        return validated
    
    async def fetch_markets(self, limit: int = 50) -> List[Dict]:
        return await self.client.fetch_markets(limit)
    
    async def fetch_market_details(self, market_id: str) -> Optional[Dict]:
        return await self.client.fetch_market_details(market_id)
    
    async def fetch_prices(self) -> Dict[str, float]:
        return await self.client.fetch_prices()
    
    async def fetch_spreads(self) -> Dict[str, float]:
        return await self.client.fetch_spreads()
    
    async def fetch_volumes(self) -> Dict[str, float]:
        return await self.client.fetch_volumes()
    
    async def close(self):
        await self.client.close()
