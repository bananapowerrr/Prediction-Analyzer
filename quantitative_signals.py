from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class QuantitativeSignal:
    action: str
    confidence: float

    def __post_init__(self):
        if self.action not in ["buy", "sell", "hold"]:
            raise ValueError("Invalid action. Must be 'buy', 'sell', or 'hold'.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "confidence": self.confidence
        }

def generate_quantitative_signals(market_data: Dict[str, Any]) -> List[QuantitativeSignal]:
    # Пример логики для генерации сигналов
    signals = []
    if market_data["price"] > market_data["moving_average"]:
        signals.append(QuantitativeSignal(action="buy", confidence=0.8))
    elif market_data["price"] < market_data["moving_average"]:
        signals.append(QuantitativeSignal(action="sell", confidence=0.8))
    else:
        signals.append(QuantitativeSignal(action="hold", confidence=0.5))
    
    return signals
