import logging
import time
from typing import List, Optional, Dict

import requests
from pydantic import ValidationError

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0

from .models import MarketSchema

class PolymarketClient:
    """Клиент API Gamma/Polymarket для Prediction Analyzer."""

    BASE = "https://gamma-api.polymarket.com"

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout = timeout
        self.session = requests.Session()

    def _headers(self) -> Dict[str, str]:
        """Возвращает заголовки для запросов."""
        return {
            "User-Agent": "PredictionAnalyzer/0.1",
            "Accept": "application/json"
        }

    def fetch_markets(self, limit: int = 50) -> List[Dict]:
        """Получает список рынков с ограничением на количество."""
        logger.debug("Загружаем рынки (лимит=%d) с %s", limit, self.BASE)
        attempts = 3
        response = None
        for attempt in range(1, attempts + 1):
            try:
                limit = max(1, min(500, limit))
                response = self.session.get(
                    f"{self.BASE}/markets",
                    params={"limit": limit},
                    headers=self._headers(),
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, list):
                    logger.warning("Получен некорректный список от API")
                    return []
                return data
            except requests.RequestException as e:
                if response is not None and getattr(response, 'status_code', None) in (429, 500, 502, 503, 504):
                    logger.warning(f"HTTP ошибка при загрузке рынков (попытка {attempt}): {e}")
                    time.sleep(0.5 * attempt)
                else:
                    logger.error(f"HTTP ошибка при загрузке рынков: {e}")
                    return []
            except ValueError:
                logger.warning("Получен некорректный JSON от API")
                return []

    def fetch_market_details(self, market_id: str) -> Optional[Dict]:
        """Получает детали конкретного рынка."""
        if not market_id:
            return None
        logger.debug("Загружаем детали рынка %s", market_id)
        attempts = 3
        response = None
        for attempt in range(1, attempts + 1):
            try:
                response = self.session.get(
                    f"{self.BASE}/markets/{market_id}",
                    headers=self._headers(),
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    logger.warning("Получен некорректный словарь от API")
                    return None
                return data
            except requests.RequestException as e:
                if response is not None and getattr(response, 'status_code', None) in (429, 500, 502, 503, 504):
                    logger.warning(f"HTTP ошибка при загрузке деталей рынка (попытка {attempt}): {e}")
                    time.sleep(0.5 * attempt)
                else:
                    logger.error(f"HTTP ошибка при загрузке деталей рынка: {e}")
                    return None
            except ValueError:
                logger.warning("Получен некорректный JSON от API")
                return None

    def fetch_prices(self) -> Dict[str, float]:
        """Получает текущие цены на рынках."""
        logger.debug("Загружаем текущие цены с %s", self.BASE)
        attempts = 3
        response = None
        for attempt in range(1, attempts + 1):
            try:
                response = self.session.get(
                    f"{self.BASE}/prices",
                    headers=self._headers(),
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    logger.warning("Получен некорректный словарь от API")
                    return {}
                return data
            except requests.RequestException as e:
                if response is not None and getattr(response, 'status_code', None) in (429, 500, 502, 503, 504):
                    logger.warning(f"HTTP ошибка при загрузке цен (попытка {attempt}): {e}")
                    time.sleep(0.5 * attempt)
                else:
                    logger.error(f"HTTP ошибка при загрузке цен: {e}")
                    return {}
            except ValueError:
                logger.warning("Получен некорректный JSON от API")
                return {}

    def fetch_spreads(self) -> Dict[str, float]:
        """Получает разбросы на рынках."""
        logger.debug("Загружаем разбросы с %s", self.BASE)
        attempts = 3
        response = None
        for attempt in range(1, attempts + 1):
            try:
                response = self.session.get(
                    f"{self.BASE}/spreads",
                    headers=self._headers(),
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    logger.warning("Получен некорректный словарь от API")
                    return {}
                return data
            except requests.RequestException as e:
                if response is not None and getattr(response, 'status_code', None) in (429, 500, 502, 503, 504):
                    logger.warning(f"HTTP ошибка при загрузке разбросов (попытка {attempt}): {e}")
                    time.sleep(0.5 * attempt)
                else:
                    logger.error(f"HTTP ошибка при загрузке разбросов: {e}")
                    return {}
            except ValueError:
                logger.warning("Получен некорректный JSON от API")
                return {}

    def fetch_volumes(self) -> Dict[str, float]:
        """Получает объемы на рынках."""
        logger.debug("Загружаем объемы с %s", self.BASE)
        attempts = 3
        response = None
        for attempt in range(1, attempts + 1):
            try:
                response = self.session.get(
                    f"{self.BASE}/volumes",
                    headers=self._headers(),
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                if not isinstance(data, dict):
                    logger.warning("Получен некорректный словарь от API")
                    return {}
                return data
            except requests.RequestException as e:
                if response is not None and getattr(response, 'status_code', None) in (429, 500, 502, 503, 504):
                    logger.warning(f"HTTP ошибка при загрузке объемов (попытка {attempt}): {e}")
                    time.sleep(0.5 * attempt)
                else:
                    logger.error(f"HTTP ошибка при загрузке объемов: {e}")
                    return {}
            except ValueError:
                logger.warning("Получен некорректный JSON от API")
                return {}

    def close(self):
        """Закрывает сессию."""
        self.session.close()


class PolymarketAdapter:
    def __init__(self, client: PolymarketClient):
        self.client = client

    def fetch_validated_markets(self, limit: int = 50) -> List[Dict]:
        """Получает список валидированных рынков."""
        raw_markets = self.client.fetch_markets(limit)
        validated: List[Dict] = []
        for i, raw in enumerate(raw_markets):
            try:
                schema = MarketSchema(**raw)
                validated.append(schema.dict())
            except ValidationError as e:
                logger.warning("Пропускаем невалидный рынок #%d от API: %s", i, e.errors()[0]["msg"])
        return validated

    def fetch_markets(self, limit: int = 50) -> List[Dict]:
        """Получает список рынков."""
        return self.client.fetch_markets(limit)

    def fetch_market_details(self, market_id: str) -> Optional[Dict]:
        """Получает детали конкретного рынка."""
        return self.client.fetch_market_details(market_id)

    def fetch_prices(self) -> Dict[str, float]:
        """Получает текущие цены на рынках."""
        return self.client.fetch_prices()

    def fetch_spreads(self) -> Dict[str, float]:
        """Получает разбросы на рынках."""
        return self.client.fetch_spreads()

    def fetch_volumes(self) -> Dict[str, float]:
        """Получает объемы на рынках."""
        return self.client.fetch_volumes()

    def close(self):
        """Закрывает сессию."""
        self.client.close()
