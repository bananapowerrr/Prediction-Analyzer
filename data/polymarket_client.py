import logging
import time
from typing import List, Optional, Dict

import requests
from pydantic import ValidationError
from core.models import MarketSchema

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0

class PolymarketClient:
    """Клиент Gamma/Polymarket API для Prediction Analyzer."""

    BASE = "https://gamma-api.polymarket.com"

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout = timeout

    def _headers(self) -> Dict[str, str]:
        return {
            "User-Agent": "PredictionAnalyzer/0.1",
            "Accept": "application/json"
        }

    def fetch_markets(self, limit: int = 50) -> List[Dict]:
        logger.debug("Fetching markets (limit=%d) from %s", limit, self.BASE)
        params = {"limit": limit}
        try:
            response = requests.get(
                f"{self.BASE}/markets",
                params=params,
                headers=self._headers(),
                timeout=self.timeout
            )
        except requests.RequestException as e:
            logger.error("HTTP error while fetching markets: %s", e)
            return []
        if response.status_code != 200:
            logger.warning("Failed to fetch markets: HTTP %d", response.status_code)
            return []
        try:
            data = response.json()
        except ValueError:
            logger.warning("Received non-JSON response from API")
            return []
        if not isinstance(data, list):
            logger.warning("Received non-list response from API")
            return []
        return data

    def fetch_market_details(self, market_id: str) -> Optional[Dict]:
        logger.debug("Fetching market details for %s", market_id)
        try:
            response = requests.get(
                f"{self.BASE}/markets/{market_id}",
                headers=self._headers(),
                timeout=self.timeout
            )
        except requests.RequestException as e:
            logger.error("HTTP error while fetching market details: %s", e)
            return None
        if response.status_code != 200:
            logger.warning("Failed to fetch market details: HTTP %d", response.status_code)
            return None
        try:
            data = response.json()
        except ValueError:
            logger.warning("Received non-JSON response from API")
            return None
        if not isinstance(data, dict):
            logger.warning("Received non-dict response from API")
            return None
        return data

    def fetch_prices(self) -> Dict[str, float]:
        logger.debug("Fetching prices from %s", self.BASE)
        try:
            response = requests.get(
                f"{self.BASE}/prices",
                headers=self._headers(),
                timeout=self.timeout
            )
        except requests.RequestException as e:
            logger.error("HTTP error while fetching prices: %s", e)
            return {}
        if response.status_code != 200:
            logger.warning("Failed to fetch prices: HTTP %d", response.status_code)
            return {}
        try:
            data = response.json()
        except ValueError:
            logger.warning("Received non-JSON response from API")
            return {}
        if not isinstance(data, dict):
            logger.warning("Received non-dict response from API")
            return {}
        return data

    def fetch_spreads(self) -> Dict[str, float]:
        logger.debug("Fetching spreads from %s", self.BASE)
        try:
            response = requests.get(
                f"{self.BASE}/spreads",
                headers=self._headers(),
                timeout=self.timeout
            )
        except requests.RequestException as e:
            logger.error("HTTP error while fetching spreads: %s", e)
            return {}
        if response.status_code != 200:
            logger.warning("Failed to fetch spreads: HTTP %d", response.status_code)
            return {}
        try:
            data = response.json()
        except ValueError:
            logger.warning("Received non-JSON response from API")
            return {}
        if not isinstance(data, dict):
            logger.warning("Received non-dict response from API")
            return {}
        return data

    def fetch_volumes(self) -> Dict[str, float]:
        logger.debug("Fetching volumes from %s", self.BASE)
        try:
            response = requests.get(
                f"{self.BASE}/volumes",
                headers=self._headers(),
                timeout=self.timeout
            )
        except requests.RequestException as e:
            logger.error("HTTP error while fetching volumes: %s", e)
            return {}
        if response.status_code != 200:
            logger.warning("Failed to fetch volumes: HTTP %d", response.status_code)
            return {}
        try:
            data = response.json()
        except ValueError:
            logger.warning("Received non-JSON response from API")
            return {}
        if not isinstance(data, dict):
            logger.warning("Received non-dict response from API")
            return {}
        return data

    def close(self):
        pass


class PolymarketAdapter:
    def __init__(self, client: PolymarketClient):
        self.client = client

    def fetch_validated_markets(self, limit: int = 50) -> List[MarketSchema]:
        raw_markets = self.client.fetch_markets(limit)
        validated: List[MarketSchema] = []
        for i, raw in enumerate(raw_markets):
            try:
                schema = MarketSchema(**raw)
                validated.append(schema)
            except ValidationError as e:
                logger.warning("Skipping invalid market #%d from API: %s", i, e.errors()[0]["msg"])
        return validated

    def fetch_markets(self, limit: int = 50) -> List[Dict]:
        return self.client.fetch_markets(limit)

    def fetch_market_details(self, market_id: str) -> Optional[Dict]:
        return self.client.fetch_market_details(market_id)

    def fetch_prices(self) -> Dict[str, float]:
        return self.client.fetch_prices()

    def fetch_spreads(self) -> Dict[str, float]:
        return self.client.fetch_spreads()

    def fetch_volumes(self) -> Dict[str, float]:
        return self.client.fetch_volumes()

    def close(self):
        self.client.close()

    def parse_market_record(self, raw: dict) -> dict | None:
        if 'id' not in raw:
            return None
        return {
            'id': raw['id'],
            'question': raw.get('question', None),
            'liquidity': raw.get('liquidityNum') or raw.get('liquidity', None),
            'spread': raw.get('spread', None),
            'volume_24h': raw.get('volume24hr') or raw.get('volume', None)
        }
