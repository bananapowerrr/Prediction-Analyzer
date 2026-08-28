from dataclasses import dataclass, field
from typing import List, Dict, Any
from core.models import QuantitativeSignal

@dataclass
class QuantitativeSignal:
    action: str
    confidence: float
    indicators: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "confidence": self.confidence,
            "indicators": self.indicators
        }

def generate_quantitative_signals(market_data: Dict[str, Any]) -> List[QuantitativeSignal]:
    """
    Пример логики для генерации сигналов на основе данных рынка.
    """
    signals = []
    price = market_data.get("price", None)
    moving_average = market_data.get("moving_average", None)
    
    if price is None or moving_average is None:
        signals.append(QuantitativeSignal(action="hold", confidence=0.5))
    elif price > moving_average:
        signals.append(QuantitativeSignal(action="buy", confidence=0.8))
    elif price < moving_average:
        signals.append(QuantitativeSignal(action="sell", confidence=0.8))
    else:
        signals.append(QuantitativeSignal(action="hold", confidence=0.5))
    
    return signals

def build_signal(market_id: str, score: float, indicators: dict | None = None) -> QuantitativeSignal:
    """
    Создает сигнал на основе оценки и индикаторов.
    
    :param market_id: Идентификатор рынка
    :param score: Оценка сигнала
    :param indicators: Индикаторы
    :return: Сигнал
    """
    score = max(0.0, min(1.0, score))  # Clamp score to [0, 1]
    
    if score > 0.6:
        action = "buy"
    elif score < 0.4:
        action = "sell"
    else:
        action = "hold"
    
    confidence = min(1.0, max(0.0, abs(score - 0.5) * 2))
    
    return QuantitativeSignal(action=action, confidence=confidence, indicators=indicators or {})

def signal_to_dict(signal: QuantitativeSignal) -> Dict[str, Any]:
    """
    Преобразует сигнал в словарь.
    
    :param signal: Сигнал
    :return: Словарь с данными сигнала
    """
    return {
        "action": signal.action,
        "confidence": signal.confidence,
        "indicators": signal.indicators
    }
