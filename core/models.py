from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Any

from pydantic import BaseModel, Field, field_validator


"""
Модели Market, Order, сигналы и pydantic-схемы валидации.
"""

@dataclass
class Order:
    """
    Модель заказа.
    """
    order_id: str
    market_id: str
    side: str
    size: float
    price: float
    maker: Optional[str] = None

    def __repr__(self) -> str:
        return f"Order(id={self.order_id}, market={self.market_id}, side={self.side}, size={self.size}, price={self.price})"

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
    """
    Модель рынка.
    """
    id: str
    question: str
    liquidity: float = 0.0
    spread: float = 0.0
    volume_24h: float = 0.0

    def __repr__(self) -> str:
        return f"Market(id={self.id}, liquidity={self.liquidity}, spread={self.spread}, volume_24h={self.volume_24h})"

    def is_tradeable(self, min_liq: float, max_sp: float, min_vol: float) -> bool:
        return (
            self.liquidity >= min_liq
            and self.spread <= max_sp
            and self.volume_24h >= min_vol
        )


@dataclass
class QuantitativeSignal:
    """
    Модель количественного сигнала.
    """
    action: str
    confidence: float
    indicators: Dict[str, float] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"QuantitativeSignal(action={self.action}, confidence={self.confidence}, indicators={self.indicators})"


class RawMarketData(BaseModel):
    """
    Схема для сырых данных рынка.
    """
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
    """
    Схема для данных рынка.
    """
    id: str
    question: str
    liquidity: float = Field(ge=0)
    spread: float = Field(ge=0, le=1)
    volume_24h: float = Field(default=0.0, ge=0)

    class Config:
        extra = 'ignore'

    def to_market(self) -> Market:
        return Market(
            id=self.id,
            question=self.question,
            liquidity=self.liquidity,
            spread=self.spread,
            volume_24h=self.volume_24h,
        )


class OrderSchema(BaseModel):
    """
    Схема для данных заказа.
    """
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
    """
    Схема для количественного сигнала.
    """
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


def validate_market_data(data: Dict[str, Any]) -> Market:
    """
    Валидация данных рынка.
    """
    schema = MarketSchema(**data)
    return schema.to_market()


def validate_order_data(data: Dict[str, Any]) -> Order:
    """
    Валидация данных заказа.
    """
    schema = OrderSchema(**data)
    return schema.to_order()


def validate_signal_data(data: Dict[str, Any]) -> QuantitativeSignal:
    """
    Валидация количественного сигнала.
    """
    schema = QuantitativeSignalSchema(**data)
    return schema.to_signal()
