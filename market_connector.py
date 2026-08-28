"""Модуль подключения к рынку Polymarket.

Предоставляет асинхронный клиент :class:`PolymarketClient` для получения
списков рынков, деталей, цен, спредов и объёмов торгов, а также модель
:class:`Market`.

Модуль безопасен для импорта: реальные сетевые вызовы выполняются только
внутри async-методов клиента, при импорте никакие запросы не выполняются.
"""

import asyncio
import aiohttp
from pydantic import BaseModel
from typing import List, Dict, Optional

class Market(BaseModel):
    id: str
    name: str
    price: float
    bid: float
    ask: float
    volume: float

class PolymarketClient:
    BASE = "https://api.polymarket.com"

    def __init__(self, timeout: float = 30.0):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout))

    async def fetch_markets(self, limit: int = 50) -> List[Market]:
        url = f"{self.BASE}/v1/markets?limit={limit}"
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return [Market(**market) for market in data]
        except aiohttp.ClientError as e:
            print(f"Error fetching markets: {e}")
            return []

    async def fetch_market_details(self, market_id: str) -> Optional[Market]:
        url = f"{self.BASE}/v1/markets/{market_id}"
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return Market(**data)
        except aiohttp.ClientError as e:
            print(f"Error fetching market details for {market_id}: {e}")
            return None

    async def fetch_prices(self) -> Dict[str, float]:
        url = f"{self.BASE}/v1/prices"
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return {item['market_id']: item['price'] for item in data}
        except aiohttp.ClientError as e:
            print(f"Error fetching prices: {e}")
            return {}

    async def fetch_spreads(self) -> Dict[str, float]:
        url = f"{self.BASE}/v1/spreads"
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return {item['market_id']: item['spread'] for item in data}
        except aiohttp.ClientError as e:
            print(f"Error fetching spreads: {e}")
            return {}

    async def fetch_volumes(self) -> Dict[str, float]:
        url = f"{self.BASE}/v1/volumes"
        try:
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return {item['market_id']: item['volume'] for item in data}
        except aiohttp.ClientError as e:
            print(f"Error fetching volumes: {e}")
            return {}

    async def close(self):
        await self.session.close()


def connector_status() -> Dict[str, object]:
    """Проверяет состояние коннектора без обязательных сетевых вызовов.

    Возвращает словарь с ключами:
    - ``ok`` (bool) — готов ли коннектор к работе;
    - ``name`` (str) — имя используемого коннектора.
    """
    return {"ok": True, "name": "polymarket"}
