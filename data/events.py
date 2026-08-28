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

def parse_events(items: list) -> list[dict]:
    """Безопасно мапит элементы через normalize если есть, иначе возвращает items как есть с фильтром dict."""
    normalized_items = []
    for item in items:
        if isinstance(item, dict):
            normalized_item = normalize_event(item)
            if normalized_item:
                normalized_items.append(normalized_item)
        else:
            normalized_items.append(item)
    return normalized_items

def filter_events_by_type(events: list, type_name: str) -> list:
    """Фильтрует события по типу.

    Аргументы:
        events: список словарей с событиями.
        type_name: тип события для фильтрации.

    Возвращает:
        Список словарей с событиями, соответствующими заданному типу.
    """
    return [event for event in events if event.get('type') == type_name]
