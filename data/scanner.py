"""
Сканер получает рынки через клиент Polymarket и отфильтровывает их гейтами Prediction Analyzer.
"""

import asyncio
import inspect
import logging
from dataclasses import dataclass
from typing import List, Optional

from pydantic import ValidationError

import telemetry
from config import MAX_SPREAD_PCT, MIN_LIQUIDITY_USD, MIN_VOLUME_24H, SCAN_LIMIT
from core.models import Market, MarketSchema
from data.filters import passes_all_gates
from data.polymarket_client import PolymarketClient

logger = logging.getLogger(__name__)


def _to_float(value, default: float = 0.0) -> float:
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
                logger.warning("Пропускаю некорректную запись рынка #%d: %s", i, e.errors()[0]["msg"])
            except Exception as e:
                logger.warning("Пропускаю некорректную запись рынка #%d: %s", i, e)
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
        logger.info("Парсинг %d рынков; применение гейтов ликвидности/разброса/объема", len(markets))
        filtered = self.filter_markets(markets)
        logger.info("Прошло гейты: %d/%d", len(filtered), len(markets))
        return filtered


class PolymarketScanner(MarketScanner):
    """Рабочий сканер Polymarket: получает сырые рынки через PolymarketClient, парсит их в ``Market``."""

    def __init__(self, client: Optional[PolymarketClient] = None, scan_config: Optional[ScanConfig] = None):
        super().__init__(scan_config)
        self.client = client or PolymarketClient()

    @staticmethod
    def _extract_spread(raw: dict) -> float:
        spread = _to_float(raw.get("spread"), default=None)
        if spread is not None and spread > 0:
            return spread
        bid = _to_float(raw.get("bestBid"), default=0.0)
        ask = _to_float(raw.get("bestAsk"), default=0.0)
        if bid <= 0 or ask <= 0:
            return 0.0
        return round(ask - bid, 4)

    def fetch_raw(self, limit: Optional[int] = None) -> list:
        limit = limit if limit is not None else self.scan_config.limit
        try:
            result = self.client.fetch_markets(limit=limit)
            if inspect.isawaitable(result):
                result = asyncio.run(result)
        except Exception as e:
            logger.warning("Не удалось получить рынки с Polymarket API (limit=%d): %s", limit, e)
            return []
        if not isinstance(result, list):
            logger.warning("Polymarket API вернул не список, игнорирую результат")
            return []
        logger.info("Получено %d сырых рынков с Polymarket API (limit=%d)", len(result), limit)
        return result

    def parse(self, raw: list) -> List[Market]:
        markets: List[Market] = []
        for i, record in enumerate(raw):
            if not isinstance(record, dict):
                logger.debug("Пропускаю запись рынка #%d: не является словарем", i)
                continue
            market_id = record.get("id")
            if not market_id:
                logger.debug("Пропускаю запись рынка #%d: отсутствует id", i)
                continue
            volume_24h = record.get("volume_24h")
            if volume_24h is None:
                volume_24h = record.get("volume24hr")
            normalized = {
                "id": str(market_id),
                "question": record.get("question") or "Unknown",
                "liquidity": _to_float(record.get("liquidity"), default=0.0),
                "spread": self._extract_spread(record),
                "volume_24h": _to_float(volume_24h, default=0.0),
            }
            try:
                market = MarketSchema(**normalized).to_market()
                markets.append(market)
            except ValidationError as e:
                logger.warning("Пропускаю некорректную запись рынка #%d: %s", i, e.errors()[0]["msg"])
            except Exception as e:
                logger.warning("Пропускаю некорректную запись рынка #%d: %s", i, e)
        return markets


def filter_by_volume_threshold(markets: List[Market], min_volume: float) -> List[Market]:
    """Возвращает рынки, чей объём за 24 часа не ниже порога."""
    return [m for m in markets if m.volume_24h >= min_volume]


def scan_markets(min_liquidity: Optional[float] = None, max_spread: Optional[float] = None, min_volume: Optional[float] = None, limit: Optional[int] = None) -> List[Market]:
    """Удобная обёртка: создаёт PolymarketScanner с переданными гейтами и запускает скан."""
    scanner = PolymarketScanner(scan_config=ScanConfig(
        min_liquidity=min_liquidity,
        max_spread=max_spread,
        min_volume=min_volume,
        limit=limit if limit is not None else SCAN_LIMIT,
    ))
    return scanner.scan()


def run_scan(min_liquidity: Optional[float] = None, max_spread: Optional[float] = None, min_volume: Optional[float] = None, limit: Optional[int] = None, sort_by_liquidity: bool = True) -> List[Market]:
    """Запускает скан рынков Polymarket через рабочего сканера PolymarketScanner."""
    scan_config = ScanConfig(
        min_liquidity=min_liquidity,
        max_spread=max_spread,
        min_volume=min_volume,
        limit=limit if limit is not None else SCAN_LIMIT,
    )
    logger.info("Запуск скана: min_liquidity=%s, max_spread=%s, min_volume=%s, limit=%d",
                min_liquidity, max_spread, min_volume, scan_config.limit)
    scanner = PolymarketScanner(scan_config=scan_config)
    markets = scanner.scan()
    if not markets:
        logger.warning("Нет рынков после фильтрации.")
    if sort_by_liquidity:
        markets = sorted(markets, key=lambda m: m.liquidity, reverse=True)
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