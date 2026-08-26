import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.utils import clamp


def test_clamp_below_lower():
    assert clamp(-5, 0, 10) == 0


def test_clamp_above_upper():
    assert clamp(15, 0, 10) == 10


def test_clamp_within_range():
    assert clamp(5, 0, 10) == 5


def test_clamp_at_lower_bound():
    assert clamp(0, 0, 10) == 0


def test_clamp_at_upper_bound():
    assert clamp(10, 0, 10) == 10


def test_clamp_equal_bounds():
    assert clamp(5, 3, 3) == 3


def test_clamp_floats():
    assert clamp(1.5, 0.0, 1.0) == 1.0
    assert clamp(-0.5, 0.0, 1.0) == 0.0
    assert clamp(0.5, 0.0, 1.0) == 0.5


def test_clamp_reversed_bounds():
    assert clamp(5, 10, 0) == 10


def test_clamp_negative_range():
    assert clamp(-3, -10, -1) == -3
    assert clamp(-20, -10, -1) == -10
    assert clamp(0, -10, -1) == -1
