import math
from dataclasses import dataclass
from typing import Dict, Tuple, Optional

from core.models import Market
from core.utils import safe_float

"""
Модуль для расчетов и анализа рисков в Prediction Analyzer.

Включает в себя функции для расчета ожидаемого значения (EV), фракционного Келли, размера позиции и доверительных интервалов.
"""

__all__ = [
    "OutcomeAssessment",
    "passes_liquidity_gate",
    "passes_spread_gate",
    "calculate_expected_value",
    "calculate_fractional_kelly",
    "determine_position_size",
    "calculate_confidence_interval",
    "assess_outcome",
    "max_position_usd",
]

@dataclass
class OutcomeAssessment:
    outcome: str
    probability: float
    confidence_level: float
    interval_lower: float
    interval_upper: float

    def to_structured(self) -> Dict[str, float]:
        return {
            "outcome": self.outcome,
            "probability": self.probability,
            "confidence_level": self.confidence_level,
            "interval_lower": self.interval_lower,
            "interval_upper": self.interval_upper,
        }

def passes_liquidity_gate(market: Market, min_liquidity: Optional[float] = None) -> bool:
    min_liquidity = safe_float(min_liquidity, 0)
    return market.liquidity > min_liquidity

def passes_spread_gate(market: Market, max_spread: Optional[float] = None) -> bool:
    max_spread = safe_float(max_spread, float('inf'))
    return market.spread < max_spread

def calculate_expected_value(market: Market, outcome_probabilities: Dict[str, float]) -> float:
    """
    Рассчитывает ожидаемое значение (EV) для заданного рынка и вероятностей исходов.

    :param market: Маркет для расчета.
    :param outcome_probabilities: Словарь с вероятностями исходов.
    :return: Ожидаемое значение (EV).
    """
    if not outcome_probabilities:
        raise ValueError("Словарь вероятностей исходов не может быть пустым")

    ev = 0
    for outcome, probability in outcome_probabilities.items():
        if outcome == 'win':
            ev += market.liquidity * safe_float(probability, 0)
        elif outcome == 'loss':
            ev -= market.liquidity * safe_float(probability, 0)
    return ev

def calculate_fractional_kelly(market: Market, outcome_probabilities: Dict[str, float]) -> float:
    """
    Рассчитывает фракционный Келли для заданного рынка и вероятностей исходов.

    :param market: Маркет для расчета.
    :param outcome_probabilities: Словарь с вероятностями исходов.
    :return: Фракционный Келли в диапазоне [0.0, 0.25].
    """
    ev = calculate_expected_value(market, outcome_probabilities)
    risk_free_rate = 0.01  # Примерный риск-фрийный процент
    denominator = market.spread * market.liquidity
    if denominator == 0 or ev <= 0:
        return 0.0
    kelly_fraction = (ev - risk_free_rate * market.liquidity) / denominator
    if kelly_fraction < 0:
        return 0.0
    elif kelly_fraction > 0.25:
        return 0.25
    return kelly_fraction

def determine_position_size(market: Market, outcome_probabilities: Dict[str, float], initial_capital: float, max_fraction: float = 0.25) -> float:
    """
    Определяет размер позиции для заданного рынка и вероятностей исходов.

    :param market: Маркет для расчета.
    :param outcome_probabilities: Словарь с вероятностями исходов.
    :param initial_capital: Начальный капитал.
    :param max_fraction: Максимальная доля капитала, которую можно использовать для позиции (по умолчанию 0.25).
    :return: Размер позиции.
    """
    kelly_fraction = calculate_fractional_kelly(market, outcome_probabilities)
    position_size = min(initial_capital * kelly_fraction, initial_capital * max_fraction)
    return position_size

def calculate_confidence_interval(
    probability: float,
    sample_size: int,
    confidence_level: float = 0.95,
) -> Tuple[float, float]:
    """
    Оценивает доверительный интервал для заданной вероятности и размера выборки.

    :param probability: Вероятность исхода.
    :param sample_size: Размер выборки.
    :param confidence_level: Уровень доверия (по умолчанию 0.95).
    :return: Доверительный интервал в виде кортежа (нижняя граница, верхняя граница).
    """
    if sample_size <= 0:
        return (0.0, 0.0)  # Если размер выборки не положителен, возвращаем нулевой интервал
    p = min(max(probability, 0.0), 1.0)
    se = math.sqrt(p * (1.0 - p) / sample_size)
    z = _z_score(confidence_level)
    margin = z * se
    lower = max(0.0, p - margin)
    upper = min(1.0, p + margin)
    return (lower, upper)

def _z_score(confidence_level: float) -> float:
    """
    Возвращает значение z для заданного уровня доверия.

    :param confidence_level: Уровень доверия.
    :return: Значение z.
    """
    if confidence_level == 0.95:
        return 1.96
    elif confidence_level == 0.99:
        return 2.58
    else:
        raise ValueError("Поддерживается только 95% и 99% уровней доверия")

def estimate_outcome_probability(outcome_probabilities: Dict[str, float], outcome: str) -> float:
    """
    Оценивает вероятность исхода на основе словаря вероятностей исходов.

    :param outcome_probabilities: Словарь с вероятностями исходов.
    :param outcome: Ожидаемый исход.
    :return: Оценка вероятности исхода.
    """
    return outcome_probabilities.get(outcome, 0.0)

def assess_outcome(
    outcome_probabilities: Dict[str, float],
    outcome: str,
    sample_size: int,
    confidence_level: float = 0.95,
) -> OutcomeAssessment:
    """
    Оценивает вероятность исхода и доверительный интервал для заданного рынка и вероятностей исходов.

    :param outcome_probabilities: Словарь с вероятностями исходов.
    :param outcome: Ожидаемый исход.
    :param sample_size: Размер выборки.
    :param confidence_level: Уровень доверия (по умолчанию 0.95).
    :return: Оценка исхода с вероятностью, уровнем доверия и доверительным интервалом.
    """
    probability = estimate_outcome_probability(outcome_probabilities, outcome)
    lower, upper = calculate_confidence_interval(probability, sample_size, confidence_level)
    return OutcomeAssessment(
        outcome=outcome,
        probability=probability,
        confidence_level=confidence_level,
        interval_lower=lower,
        interval_upper=upper,
    )

def max_position_usd(bankroll: float, kelly_f: float) -> float:
    """
    Определяет максимальный размер позиции в долларах.

    :param bankroll: Начальный капитал.
    :param kelly_f: Фракционный Келли.
    :return: Максимальный размер позиции в долларах.
    """
    return min(bankroll, bankroll * kelly_f)
