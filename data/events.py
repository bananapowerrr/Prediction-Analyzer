from pydantic import BaseModel, Field

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
