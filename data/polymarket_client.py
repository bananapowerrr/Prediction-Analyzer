import asyncio
import logging
import time
from typing import List, Optional, Dict
from aiohttp import ClientSession, ClientError, ClientResponse

from pydantic import ValidationError
from core.models import MarketSchema

logger = logging.getLogger(__name__)

class PolymarketClient:
    """Клиент Gamma/Polymarket API для Prediction Analyzer."""
    
    BASE = "https://api.polymarket.com"
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
    
    async def fetch_markets(self, limit: int = 50) -> List[Dict]:
        logger.debug("Fetching markets (limit=%d) from %s", limit, self.BASE)
        headers = {
            "User-Agent": "PredictionAnalyzer/1.0",
            "Accept": "application/json"
        }
        for attempt in range(3):
            try:
                async with ClientSession(timeout=asyncio.TimeoutError(self.timeout)) as session:
                    async with session.get(f"{self.BASE}/markets?limit={limit}", headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if isinstance(data, list):
                                return data
                            else:
                                logger.warning("Received non-JSON response from API")
                        else:
                            logger.warning("Failed to fetch markets: HTTP %d", response.status)
            except ClientError as e:
                logger.error("HTTP error while fetching markets: %s", e)
            if attempt < 2:
                logger.info("Retrying in 0.5 seconds...")
                time.sleep(0.5)
        return []
    
    async def fetch_market_details(self, market_id: str) -> Optional[Dict]:
        logger.debug("Fetching market details for %s", market_id)
        headers = {
            "User-Agent": "PredictionAnalyzer/1.0",
            "Accept": "application/json"
        }
        for attempt in range(3):
            try:
                async with ClientSession(timeout=asyncio.TimeoutError(self.timeout)) as session:
                    async with session.get(f"{self.BASE}/markets/{market_id}", headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if isinstance(data, dict):
                                return data
                            else:
                                logger.warning("Received non-JSON response from API")
                        else:
                            logger.warning("Failed to fetch market details: HTTP %d", response.status)
            except ClientError as e:
                logger.error("HTTP error while fetching market details: %s", e)
            if attempt < 2:
                logger.info("Retrying in 0.5 seconds...")
                time.sleep(0.5)
        return None
    
    async def fetch_prices(self) -> Dict[str, float]:
        logger.debug("Fetching prices from %s", self.BASE)
        headers = {
            "User-Agent": "PredictionAnalyzer/1.0",
            "Accept": "application/json"
        }
        for attempt in range(3):
            try:
                async with ClientSession(timeout=asyncio.TimeoutError(self.timeout)) as session:
                    async with session.get(f"{self.BASE}/prices", headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if isinstance(data, dict):
                                return data
                            else:
                                logger.warning("Received non-JSON response from API")
                        else:
                            logger.warning("Failed to fetch prices: HTTP %d", response.status)
            except ClientError as e:
                logger.error("HTTP error while fetching prices: %s", e)
            if attempt < 2:
                logger.info("Retrying in 0.5 seconds...")
                time.sleep(0.5)
        return {}
    
    async def fetch_spreads(self) -> Dict[str, float]:
        logger.debug("Fetching spreads from %s", self.BASE)
        headers = {
            "User-Agent": "PredictionAnalyzer/1.0",
            "Accept": "application/json"
        }
        for attempt in range(3):
            try:
                async with ClientSession(timeout=asyncio.TimeoutError(self.timeout)) as session:
                    async with session.get(f"{self.BASE}/spreads", headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if isinstance(data, dict):
                                return data
                            else:
                                logger.warning("Received non-JSON response from API")
                        else:
                            logger.warning("Failed to fetch spreads: HTTP %d", response.status)
            except ClientError as e:
                logger.error("HTTP error while fetching spreads: %s", e)
            if attempt < 2:
                logger.info("Retrying in 0.5 seconds...")
                time.sleep(0.5)
        return {}
    
    async def fetch_volumes(self) -> Dict[str, float]:
        logger.debug("Fetching volumes from %s", self.BASE)
        headers = {
            "User-Agent": "PredictionAnalyzer/1.0",
            "Accept": "application/json"
        }
        for attempt in range(3):
            try:
                async with ClientSession(timeout=asyncio.TimeoutError(self.timeout)) as session:
                    async with session.get(f"{self.BASE}/volumes", headers=headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if isinstance(data, dict):
                                return data
                            else:
                                logger.warning("Received non-JSON response from API")
                        else:
                            logger.warning("Failed to fetch volumes: HTTP %d", response.status)
            except ClientError as e:
                logger.error("HTTP error while fetching volumes: %s", e)
            if attempt < 2:
                logger.info("Retrying in 0.5 seconds...")
                time.sleep(0.5)
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
