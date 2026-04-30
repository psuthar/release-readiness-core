"""Parity tests for the half-away-from-zero rounding helper."""

import math

import pytest

from release_readiness_core.pr_risk._round import round_half_away


@pytest.mark.parametrize(
    "x,expected",
    [
        # Positive halves round up (away from zero)
        (0.5, 1.0),
        (1.5, 2.0),
        (2.5, 3.0),
        (3.5, 4.0),
        # Negative halves round down (away from zero)
        (-0.5, -1.0),
        (-1.5, -2.0),
        (-2.5, -3.0),
        (-3.5, -4.0),
        # Non-halves behave normally
        (0.0, 0.0),
        (1.4, 1.0),
        (1.6, 2.0),
        (-1.4, -1.0),
        (-1.6, -2.0),
        # Larger values
        (42.5, 43.0),
        (-42.5, -43.0),
        (99.999, 100.0),
    ],
)
def test_round_half_away_matches_go_math_round(x: float, expected: float) -> None:
    assert round_half_away(x) == expected


def test_round_half_away_diverges_from_python_round_on_halves() -> None:
    # Documents the reason this helper exists: Python's round() uses
    # banker's rounding (round-half-to-even), Go uses half-away-from-zero.
    assert round(2.5) == 2  # Python banker's
    assert round_half_away(2.5) == 3  # Go-compatible


def test_round_half_away_propagates_nan_inf() -> None:
    assert math.isnan(round_half_away(float("nan")))
    assert round_half_away(float("inf")) == float("inf")
    assert round_half_away(float("-inf")) == float("-inf")
