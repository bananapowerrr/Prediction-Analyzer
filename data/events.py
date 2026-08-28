from pydantic import BaseModel, Field

"""Prediction Analyzer.

Нормализует сырые события (dict) к единому виду с ключами
id, type, ts, которые используются в предсказаниях анализатора.
"""

def normalize_event(raw: dict) -> dict:
    """Приводит сырой event к виду {'id', 'type', 'ts'}.

    Аргументы:
        raw: словарь с произвольными ключами (id, event_type/type, timestamp/ts).

    Возвращает:
        dict с ключами id, type, ts.
    """
    return {
        'id': raw.get('id'),
        'type': raw.get('event_type') or raw.get('type'),
        'ts': raw.get('timestamp', raw.get('ts')),
    }

class MarketQuote(BaseModel):
    market_id: str
    bid: float
    ask: float
    timestamp: float = Field(default_factory=float)

class BlockchainEvent(BaseModel):
    event_type: str
    data: dict
    timestamp: float = Field(default_factory=float)

class MarketEvent(BaseModel):
    symbol: str
    timestamp: float
    price: float
    volume: float
    source: str

class ChainMetric(BaseModel):
    metric_name: str
    value: float
    timestamp: float = Field(default_factory=float)
