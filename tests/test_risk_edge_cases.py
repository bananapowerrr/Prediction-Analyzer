import math
import pytest

from risk_engine import (
    Market,
    OutcomeAssessment,
    passes_liquidity_gate,
    passes_spread_gate,
    calculate_expected_value,
    calculate_fractional_kelly,
    determine_position_size,
    estimate_outcome_probability,
    calculate_confidence_interval,
    assess_outcome,
)


def _make_market(**kwargs):
    base = dict(id="test_market", question="Test?", liquidity=1000.0, spread=0.05, volume_24h=500.0)
    base.update(kwargs)
    return Market(**base)


# --- Negative EV ---

def test_negative_ev_high_loss_probability():
    market = _make_market(liquidity=1000.0)
    ev = calculate_expected_value(market, {"win": 0.1, "loss": 0.9})
    assert ev == pytest.approx(-800.0)


def test_negative_ev_equal_probabilities():
    market = _make_market(liquidity=1000.0)
    ev = calculate_expected_value(market, {"win": 0.5, "loss": 0.5})
    assert ev == pytest.approx(0.0)


def test_negative_ev_no_win_outcome():
    market = _make_market(liquidity=500.0)
    ev = calculate_expected_value(market, {"loss": 1.0})
    assert ev == pytest.approx(-500.0)


def test_negative_ev_no_loss_outcome():
    market = _make_market(liquidity=500.0)
    ev = calculate_expected_value(market, {"win": 1.0})
    assert ev == pytest.approx(500.0)


def test_kelly_fraction_clamped_zero_for_negative_ev():
    market = _make_market(liquidity=1000.0, spread=0.05)
    kelly = calculate_fractional_kelly(market, {"win": 0.1, "loss": 0.9})
    assert kelly == 0.0


def test_position_size_zero_for_negative_ev():
    market = _make_market(liquidity=1000.0, spread=0.05)
    size = determine_position_size(market, {"win": 0.1, "loss": 0.9}, 10000.0)
    assert size == 0.0


# --- Zero liquidity ---

def test_zero_liquidity_ev():
    market = _make_market(liquidity=0.0)
    ev = calculate_expected_value(market, {"win": 0.6, "loss": 0.4})
    assert ev == 0.0


def test_zero_liquidity_kelly():
    market = _make_market(liquidity=0.0, spread=0.05)
    kelly = calculate_fractional_kelly(market, {"win": 0.6, "loss": 0.4})
    assert kelly == 0.0


def test_zero_liquidity_position_size():
    market = _make_market(liquidity=0.0, spread=0.05)
    size = determine_position_size(market, {"win": 0.6, "loss": 0.4}, 10000.0)
    assert size == 0.0


def test_zero_liquidity_fails_gate():
    market = _make_market(liquidity=0.0)
    assert passes_liquidity_gate(market, min_liquidity=0.0) is False


def test_zero_spread_division_by_zero():
    market = _make_market(liquidity=1000.0, spread=0.0)
    kelly = calculate_fractional_kelly(market, {"win": 0.6, "loss": 0.4})
    assert kelly == 0.0


# --- estimate_outcome_probability ---

def test_estimate_outcome_probability_empty_dict():
    assert estimate_outcome_probability({}, "win") == 0.0


def test_estimate_outcome_probability_zero_total():
    assert estimate_outcome_probability({"win": 0.0, "loss": 0.0}, "win") == 0.0


def test_estimate_outcome_probability_missing_outcome():
    result = estimate_outcome_probability({"win": 0.7, "loss": 0.3}, "draw")
    assert result == pytest.approx(0.0)


def test_estimate_outcome_probability_normalizes():
    result = estimate_outcome_probability({"win": 2.0, "loss": 3.0}, "win")
    assert result == pytest.approx(0.4)


# --- calculate_confidence_interval ---

def test_confidence_interval_zero_sample():
    lower, upper = calculate_confidence_interval(0.5, sample_size=0)
    assert lower == 0.0
    assert upper == 0.0


def test_confidence_interval_negative_sample():
    lower, upper = calculate_confidence_interval(0.5, sample_size=-10)
    assert lower == 0.0
    assert upper == 0.0


def test_confidence_interval_probability_clamped_below_zero():
    lower, upper = calculate_confidence_interval(-0.5, sample_size=100)
    assert lower >= 0.0
    assert upper <= 1.0


def test_confidence_interval_probability_clamped_above_one():
    lower, upper = calculate_confidence_interval(1.5, sample_size=100)
    assert lower >= 0.0
    assert upper <= 1.0


def test_confidence_interval_narrow_with_large_sample():
    lo_small, hi_small = calculate_confidence_interval(0.5, sample_size=10)
    lo_large, hi_large = calculate_confidence_interval(0.5, sample_size=10000)
    assert (hi_large - lo_large) < (hi_small - lo_small)


def test_confidence_interval_boundaries():
    lower, upper = calculate_confidence_interval(0.5, sample_size=100, confidence_level=0.99)
    assert lower >= 0.0
    assert upper <= 1.0
    assert lower < 0.5
    assert upper > 0.5


# --- assess_outcome ---

def test_assess_outcome_basic():
    result = assess_outcome({"win": 0.6, "loss": 0.4}, "win", sample_size=100)
    assert result.outcome == "win"
    assert result.probability == pytest.approx(0.6)
    assert result.interval_lower <= result.probability <= result.interval_upper


def test_assess_outcome_zero_sample():
    result = assess_outcome({"win": 0.6, "loss": 0.4}, "win", sample_size=0)
    assert result.probability == pytest.approx(0.6)
    assert result.interval_lower == 0.0
    assert result.interval_upper == 0.0


# --- Liquidity gate edge cases ---

def test_liquidity_gate_boundary():
    market = _make_market(liquidity=1000.0)
    assert passes_liquidity_gate(market, min_liquidity=1000.0) is False
    assert passes_liquidity_gate(market, min_liquidity=999.99) is True


def test_spread_gate_boundary():
    market = _make_market(spread=0.05)
    assert passes_spread_gate(market, max_spread=0.05) is False
    assert passes_spread_gate(market, max_spread=0.05001) is True
