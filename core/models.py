from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


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


@dataclass
class Market:
    id: str
    question: str
    liquidity: float
    spread: float
    volume_24h: float = 0.0

    def __repr__(self) -> str:
        return f"Market(id={self.id}, liquidity={self.liquidity}, spread={self.spread})"
