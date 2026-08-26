from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Market:
    id: str
    liquidity: float
    spread: float
    volume: float

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
