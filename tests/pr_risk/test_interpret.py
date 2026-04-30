"""Tests for pr_risk.interpret (port of Go interpret_test.go)."""

from release_readiness_core.pr_risk.interpret import build_interpretation
from release_readiness_core.pr_risk.types import Result, ScoreMath


def test_low_band_returns_low_language() -> None:
    r = Result(risk_score=10, risk_band="low")
    interp = build_interpretation(r)
    assert interp != ""
    assert "low" in interp.lower()


def test_medium_band_returns_medium_language() -> None:
    r = Result(risk_score=30, risk_band="medium")
    interp = build_interpretation(r)
    assert interp != ""
    assert "medium" in interp.lower()


def test_high_band_returns_high_language() -> None:
    r = Result(risk_score=60, risk_band="high")
    interp = build_interpretation(r)
    assert "high" in interp.lower()


def test_critical_band_returns_critical_language() -> None:
    r = Result(risk_score=85, risk_band="critical")
    interp = build_interpretation(r)
    assert "critical" in interp.lower()


def test_score_embedded_in_high_band() -> None:
    r = Result(risk_score=55, risk_band="high")
    interp = build_interpretation(r)
    assert "55" in interp


def test_floor_note_present_when_applied_medium() -> None:
    r = Result(
        risk_score=20,
        risk_band="medium",
        score_math=ScoreMath(floor_applied=True, net_before_floor=6, final_score=20),
    )
    interp = build_interpretation(r)
    assert "floor" in interp
    assert "6" in interp
    assert "20" in interp


def test_floor_note_absent_when_not_applied() -> None:
    r = Result(
        risk_score=40,
        risk_band="medium",
        score_math=ScoreMath(floor_applied=False, net_before_floor=40, final_score=40),
    )
    interp = build_interpretation(r)
    assert "floor" not in interp


def test_floor_note_present_high_band() -> None:
    r = Result(
        risk_score=50,
        risk_band="high",
        score_math=ScoreMath(floor_applied=True, net_before_floor=15, final_score=50),
    )
    interp = build_interpretation(r)
    assert "high" in interp.lower()
    assert "floor" in interp


def test_unknown_band_returns_empty_string() -> None:
    r = Result(risk_score=0, risk_band="")
    assert build_interpretation(r) == ""


def test_low_band_does_not_include_score() -> None:
    """Low band's text is constant — no formatted score embedded.

    Mirrors Go: the low-band branch uses a fixed string with no Sprintf."""
    r = Result(risk_score=10, risk_band="low")
    interp = build_interpretation(r)
    assert "10" not in interp


def test_score_rounding_half_away_from_zero() -> None:
    """The %.0f format uses half-away-from-zero rounding (Go math.Round semantics)."""
    r = Result(risk_score=42.5, risk_band="medium")
    interp = build_interpretation(r)
    assert "43" in interp  # 42.5 -> 43 (half-away), not 42 (banker's)
