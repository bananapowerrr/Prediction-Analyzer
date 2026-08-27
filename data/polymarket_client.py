import asyncio
from dataclasses import dataclass
from typing import List, Optional, Dict

class PolymarketClient:
    BASE = "https://api.polymarket.com"
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
    
    async def fetch_markets(self, limit: int = 50) -> List[Dict]:
        # Пример реализации метода для получения данных
        pass
    
    async def fetch_market_details(self, market_id: str) -> Optional[Dict]:
        # Пример реализации метода для получения деталей конкретного рынка
        pass
    
    async def fetch_prices(self) -> Dict[str, float]:
        # Пример реализации метода для получения цен
        pass
    
    async def fetch_spreads(self) -> Dict[str, float]:
        # Пример реализации метода для получения спредов
        pass
    
    async def fetch_volumes(self) -> Dict[str, float]:
        # Пример реализации метода для получения объемов
        pass
    
    async def close(self):
        # Пример реализации метода для закрытия клиента
        pass

class PolymarketAdapter:
    def __init__(self, client: PolymarketClient):
        self.client = client
    
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
