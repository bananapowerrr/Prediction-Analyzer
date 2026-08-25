from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Market:
    id: str
    question: str
    liquidity: float
    spread: float
    volume_24h: float = 0.0
