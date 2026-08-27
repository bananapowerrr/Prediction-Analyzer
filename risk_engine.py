import math
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple

@dataclass
class Market:
    id: str
    liquidity: float
    spread: float
    volume: float

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
    ev = 0
    for outcome, probability in outcome_probabilities.items():
        if outcome == 'win':
            ev += market.liquidity * probability
        elif outcome == 'loss':
            ev -= market.liquidity * probability
    return ev

def calculate_fractional_kelly(market: Market, outcome_probabilities: Dict[str, float]) -> float:
    ev = calculate_expected_value(market, outcome_probabilities)
    risk_free_rate = 0.01  # Примерный риск-фрийный процент
    kelly_fraction = (ev - risk_free_rate * market.liquidity) / (market.spread * market.liquidity)
    return max(0, min(1, kelly_fraction))

def determine_position_size(market: Market, outcome_probabilities: Dict[str, float], initial_capital: float) -> float:
    kelly_fraction = calculate_fractional_kelly(market, outcome_probabilities)
    position_size = initial_capital * kelly_fraction
    return position_size

def _z_score(confidence_level: float) -> float:
    import math
    tail = (1.0 - confidence_level) / 2.0
    return -math.sqrt(2.0) * _erf_inv(2.0 * tail - 1.0)

def _erf_inv(x: float) -> float:
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
    if sample_size <= 0:
        return (0.0, 0.0)
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
    probability = estimate_outcome_probability(outcome_probabilities, outcome)
    lower, upper = calculate_confidence_interval(probability, sample_size, confidence_level)
    return OutcomeAssessment(
        outcome=outcome,
        probability=probability,
        confidence_level=confidence_level,
        interval_lower=lower,
        interval_upper=upper,
    )
