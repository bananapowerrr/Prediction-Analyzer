"""
Сканер получает рынки через клиент Polymarket и отфильтровывает их гейтами Prediction Analyzer.
"""

import asyncio
import inspect
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from pydantic import ValidationError

import telemetry
from config import MAX_SPREAD_PCT, MIN_LIQUIDITY_USD, MIN_VOLUME_24H, SCAN_LIMIT
from core.models import Market, MarketSchema
from data.filters import passes_all_gates
from data.polymarket_client import PolymarketClient

logger = logging.getLogger(__name__)

def _to_float(value: object, default: float = 0.0) -> float:
    """Безопасно приводит значение к float, при ошибке возвращает default."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

@dataclass
class ScanConfig:
    min_liquidity: Optional[float] = MIN_LIQUIDITY_USD
    max_spread: Optional[float] = MAX_SPREAD_PCT
    min_volume: Optional[float] = MIN_VOLUME_24H
    limit: int = SCAN_LIMIT

class MarketScanner:
    """Сканер получает рынки через клиент Polymarket и отфильтровывает их гейтами Prediction Analyzer.

    Подклассы должны реализовать метод :meth:`fetch_raw` (получение сырых записей из источника данных)
    и метод :meth:`parse` (конвертация сырых записей в модели ``Market``).
    Метод :meth:`scan` выполняет получение, парсинг и применение гейтов ликвидности/разброса/объема, определенных в ``data.filters``.
    """

    def __init__(self, scan_config: Optional[ScanConfig] = None) -> None:
        self.scan_config = scan_config or ScanConfig()

    def fetch_raw(self) -> List[Dict[str, object]]:
        raise NotImplementedError("Subclasses must implement this method")

    def _parse_record(self, index: int, record: Dict[str, object]) -> Optional[Market]:
        """Парсит одну запись в Market, при ошибке логирует и возвращает None."""
        try:
            return MarketSchema(**record).to_market()
        except ValidationError as e:
            logger.warning(f"Пропускаю некорректную запись рынка #{index}: {e.errors()[0]['msg']}")
        except Exception as e:
            logger.warning(f"Пропускаю некорректную запись рынка #{index}: {e}")
        return None

    def parse(self, raw: List[Dict[str, object]]) -> List[Market]:
        markets: List[Market] = []
        for i, record in enumerate(raw):
            market = self._parse_record(i, record)
            if market is not None:
                markets.append(market)
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
        logger.info(f"Парсинг {len(markets)} рынков; применение гейтов ликвидности/разброса/объема")
        filtered = self.filter_markets(markets)
        logger.info(f"Прошло гейты: {len(filtered)}/{len(markets)}")
        return filtered


class PolymarketScanner(MarketScanner):
    """Рабочий сканер Polymarket: получает сырые рынки через PolymarketClient, парсит их в ``Market``."""

    def __init__(self, client: Optional["PolymarketClient"] = None, scan_config: Optional[ScanConfig] = None) -> None:
        super().__init__(scan_config)
        self.client = client or PolymarketClient()

    @staticmethod
    def _extract_spread(raw: Dict[str, object]) -> float:
        spread = _to_float(raw.get("spread"), default=None)
        if spread is not None and spread > 0:
            return spread
        bid = _to_float(raw.get("bestBid"), default=0.0)
        ask = _to_float(raw.get("bestAsk"), default=0.0)
        if bid <= 0 or ask <= 0:
            return 0.0
        return round(ask - bid, 4)

    def fetch_raw(self, limit: Optional[int] = None) -> List[Dict[str, object]]:
        limit = limit if limit is not None else self.scan_config.limit
        limit = max(1, min(200, limit))  # Clamp limit to [1, 200]
        try:
            result = self.client.fetch_markets(limit=limit)
            if inspect.isawaitable(result):
                if inspect.iscoroutine(result):
                    result = asyncio.run(result)
        except Exception as e:
            logger.warning(f"Не удалось получить рынки с Polymarket API (limit={limit}): {e}")
            return []
        if not isinstance(result, list):
            logger.warning(f"Polymarket API вернул не список, игнорирую результат")
            return []
        logger.info(f"Получено {len(result)} сырых рынков с Polymarket API (limit={limit})")
        return result

    def parse(self, raw: List[Dict[str, object]]) -> List[Market]:
        markets: List[Market] = []
        for i, record in enumerate(raw):
            if not isinstance(record, dict):
                logger.debug(f"Пропускаю запись рынка #{i}: не является словарем")
                continue
            market_id = record.get("id")
            if not market_id:
                logger.debug(f"Пропускаю запись рынка #{i}: отсутствует id")
                continue
            volume_24h = record.get("volume_24h")
            if volume_24h is None:
                volume_24h = record.get("volume24hr")
            normalized = {
                "id": str(market_id),
                "question": record.get("question") or "Unknown",
                "liquidity": _to_float(record.get('liquidity') or record.get('liquidityNum'), default=0.0),
                "spread": self._extract_spread(record),
                "volume_24h": _to_float(volume_24h, default=0.0),
            }
            market = self._parse_record(i, normalized)
            if market is not None:
                markets.append(market)
        return markets


def scan_markets(min_liquidity: Optional[float] = None, max_spread: Optional[float] = None, min_volume: Optional[float] = None, limit: Optional[int] = None) -> List[Market]:
    """Удобная обёртка: создаёт PolymarketScanner с переданными гейтами и запускает скан.

    :param min_liquidity: Минимальная ликвидность рынка
    :param max_spread: Максимальный разброс рынка
    :param min_volume: Минимальный объем за 24 часа
    :param limit: Ограничение на количество рынков
    :return: Список отфильтрованных рынков
    """
    scanner = PolymarketScanner(scan_config=ScanConfig(
        min_liquidity=min_liquidity,
        max_spread=max_spread,
        min_volume=min_volume,
        limit=limit if limit is not None else SCAN_LIMIT,
    ))
    return scanner.scan()


def run_scan(min_liquidity: Optional[float] = None, max_spread: Optional[float] = None, min_volume: Optional[float] = None, limit: Optional[int] = None, sort_by_liquidity: bool = True) -> List[Market]:
    """Запускает скан рынков Polymarket через рабочего сканера PolymarketScanner.

    :param min_liquidity: Минимальная ликвидность рынка
    :param max_spread: Максимальный разброс рынка
    :param min_volume: Минимальный объем за 24 часа
    :param limit: Ограничение на количество рынков
    :param sort_by_liquidity: Сортировать по ликвидности
    :return: Список отфильтрованных и отсортированных рынков
    """
    logger.info(f"Запуск скана: минимальная ликвидность={min_liquidity}, максимальный разброс={max_spread}, минимальный объем={min_volume}, ограничение={limit if limit is not None else SCAN_LIMIT}")
    markets = scan_markets(min_liquidity, max_spread, min_volume, limit)
    if not markets:
        logger.warning("Нет рынков после фильтрации.")
    if sort_by_liquidity:
        markets = sorted(
            markets,
            key=lambda m: (m.liquidity or 0.0, m.volume_24h or 0.0),
            reverse=True,
        )
    if limit is not None:
        markets = markets[:limit]

    try:
        total = len(markets)
        passed = len([m for m in markets if passes_all_gates(m, min_liquidity, max_spread, min_volume)])
        telemetry_record = getattr(telemetry, "record_scan", None)
        if callable(telemetry_record):
            telemetry_record(total, passed)
    except Exception:
        logger.debug("Не удалось записать метрики скана в telemetry", exc_info=True)

    return markets


__all__ = [
    "MarketScanner",
    "PolymarketScanner",
    "ScanConfig",
    "scan_markets",
    "run_scan",
]
