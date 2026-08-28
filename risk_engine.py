import math
from dataclasses import dataclass
from typing import Dict, Tuple

from core.models import Market

"""
Модуль для расчетов и анализа рисков в Prediction Analyzer.

Включает в себя функции для расчета ожидаемого значения (EV), фракционного Келли, размера позиции и доверительных интервалов.
"""

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

def passes_liquidity_gate(market: Market, min_liquidity: float) -> bool:
    return market.liquidity > min_liquidity

def passes_spread_gate(market: Market, max_spread: float) -> bool:
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
            ev += market.liquidity * probability
        elif outcome == 'loss':
            ev -= market.liquidity * probability
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
    return max(0, min(0.25, kelly_fraction))

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

def _z_score(confidence_level: float) -> float:
    """
    Вычисляет z-оценку для заданного уровня доверия.

    :param confidence_level: Уровень доверия.
    :return: Значение z-оценки.
    """
    tail = (1.0 - confidence_level) / 2.0
    return -math.sqrt(2.0) * _erf_inv(2.0 * tail - 1.0)

def _erf_inv(x: float) -> float:
    """
    Вычисляет обратную функцию ошибок для заданного значения x.

    :param x: Значение x.
    :return: Значение обратной функции ошибок.
    """
    a = 0.147
    ln = math.log(1.0 - x * x)
    term = 2.0 / (math.pi * a) + ln / 2.0
    return math.copysign(math.sqrt(math.sqrt(term * term - ln / a) - term), x)

def estimate_outcome_probability(outcome_probabilities: Dict[str, float], outcome: str) -> float:
    total = sum(outcome_probabilities.values())
    if total <= 0:
        return 0.0
    return outcome_probabilities.get(outcome, 0.0) / total

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
