from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, List

from pydantic import BaseModel, Field, field_validator


"""
Модели Market, Order, сигналы и pydantic-схемы валидации.
"""

@dataclass
class Order:
    order_id: str
    market_id: str
    side: str
    size: float
    price: float
    maker: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.order_id:
            raise ValueError("order_id is required")
        if not self.market_id:
            raise ValueError("market_id is required")
        if self.side not in ("buy", "sell"):
            raise ValueError("side must be 'buy' or 'sell'")
        if not isinstance(self.size, (int, float)) or self.size <= 0:
            raise ValueError("size must be a positive number")
        if not isinstance(self.price, (int, float)) or not (0.0 < self.price <= 1.0):
            raise ValueError("price must be in the range (0, 1]")

    def __repr__(self) -> str:
        return (
            f"Order(id={self.order_id}, market={self.market_id}, "
            f"side={self.side}, size={self.size}, price={self.price})"
        )

    def to_dict(self) -> dict:
        return {
            "order_id": self.order_id,
            "market_id": self.market_id,
            "side": self.side,
            "size": self.size,
            "price": self.price,
            "maker": self.maker,
        }


@dataclass
class Market:
    id: str
    question: str
    liquidity: float = 0.0
    spread: float = 0.0
    volume_24h: float = 0.0

    def __repr__(self) -> str:
        return (
            f"Market(id={self.id}, liquidity={self.liquidity}, spread={self.spread}, "
            f"volume_24h={self.volume_24h})"
        )

    def is_tradeable(self, min_liq: float, max_sp: float, min_vol: float) -> bool:
        return (
            self.liquidity >= min_liq
            and self.spread <= max_sp
            and self.volume_24h >= min_vol
        )


@dataclass
class QuantitativeSignal:
    action: str
    confidence: float
    indicators: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.action not in ("buy", "sell", "hold"):
            raise ValueError("action must be 'buy', 'sell', or 'hold'")
        if not isinstance(self.confidence, (int, float)):
            raise ValueError("confidence must be a number")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in the range [0, 1]")

    def __repr__(self) -> str:
        return (
            f"QuantitativeSignal(action={self.action}, "
            f"confidence={self.confidence}, indicators={self.indicators})"
        )


class RawMarketData(BaseModel):
    id: str
    question: str
    liquidity: float = Field(ge=0)
    spread: float = Field(ge=0)
    volume_24h: float = Field(default=0.0, ge=0)

    @field_validator("id")
    @classmethod
    def id_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("id must not be empty")
        return v.strip()

    @field_validator("question")
    @classmethod
    def question_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be empty")
        return v.strip()


class MarketSchema(BaseModel):
    id: str
    question: str
    liquidity: float = Field(ge=0)
    spread: float = Field(ge=0, le=1)
    volume_24h: float = Field(default=0.0, ge=0)

    def to_market(self) -> Market:
        return Market(
            id=self.id,
            question=self.question,
            liquidity=self.liquidity,
            spread=self.spread,
            volume_24h=self.volume_24h,
        )


class OrderSchema(BaseModel):
    order_id: str
    market_id: str
    side: str
    size: float = Field(gt=0)
    price: float = Field(gt=0, le=1)
    maker: Optional[str] = None

    @field_validator("side")
    @classmethod
    def side_valid(cls, v: str) -> str:
        if v not in ("buy", "sell"):
            raise ValueError("side must be 'buy' or 'sell'")
        return v

    def to_order(self) -> Order:
        return Order(
            order_id=self.order_id,
            market_id=self.market_id,
            side=self.side,
            size=self.size,
            price=self.price,
            maker=self.maker,
        )


class QuantitativeSignalSchema(BaseModel):
    action: str
    confidence: float = Field(ge=0, le=1)
    indicators: Dict[str, float] = Field(default_factory=dict)

    @field_validator("action")
    @classmethod
    def action_valid(cls, v: str) -> str:
        if v not in ("buy", "sell", "hold"):
            raise ValueError("action must be 'buy', 'sell', or 'hold'")
        return v

    def to_signal(self) -> QuantitativeSignal:
        return QuantitativeSignal(
            action=self.action,
            confidence=self.confidence,
            indicators=self.indicators,
        )


def validate_market_data(data: Dict) -> Market:
    schema = MarketSchema(**data)
    return schema.to_market()


def validate_order_data(data: Dict) -> Order:
    schema = OrderSchema(**data)
    return schema.to_order()


def validate_signal_data(data: Dict) -> QuantitativeSignal:
    schema = QuantitativeSignalSchema(**data)
    return schema.to_signal()
