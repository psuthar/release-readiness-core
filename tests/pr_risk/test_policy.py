"""Unit tests for pr_risk.policy."""

import pytest

from release_readiness_core.pr_risk.policy import (
    compute_blocking_reasons,
    compute_enforcement,
    dedupe_strings,
    merge_rationale,
    merge_recommendation,
    review_requirements,
    review_strategy_for,
)
from release_readiness_core.pr_risk.types import (
    Result,
    RiskFactor,
    RiskReducer,
    ScoreMath,
    Signals,
)


def _result(
    *, band: str = "low", git_error: str = "", factors=None, reducers=None, score: float = 10.0
) -> Result:
    return Result(
        risk_score=score,
        risk_band=band,
        signals=Signals(git_error=git_error),
        factors=list(factors or []),
        reducers=list(reducers or []),
    )


# ---------------------------------------------------------------------------
# merge_recommendation

def test_merge_recommendation_block_on_git_error() -> None:
    assert merge_recommendation(_result(band="low", git_error="bad ref")) == "block"


def test_merge_recommendation_block_on_critical() -> None:
    assert merge_recommendation(_result(band="critical")) == "block"


def test_merge_recommendation_block_on_high() -> None:
    assert merge_recommendation(_result(band="high")) == "block"


def test_merge_recommendation_warn_on_medium() -> None:
    assert merge_recommendation(_result(band="medium")) == "warn"


def test_merge_recommendation_pass_on_low() -> None:
    assert merge_recommendation(_result(band="low")) == "pass"


def test_merge_recommendation_warn_on_low_with_tests_missing() -> None:
    factors = [RiskFactor(id="tests_missing", label="m", points=18)]
    assert merge_recommendation(_result(band="low", factors=factors)) == "warn"


def test_merge_recommendation_low_with_tests_missing_but_style_only_passes() -> None:
    """Style-only frontend changes waive the tests_missing low-band gate."""
    factors = [RiskFactor(id="tests_missing", label="m", points=18)]
    reducers = [RiskReducer(id="style_only_note", label="s", points=20)]
    assert (
        merge_recommendation(
            _result(band="low", factors=factors, reducers=reducers)
        )
        == "pass"
    )


# ---------------------------------------------------------------------------
# merge_rationale

def test_merge_rationale_git_error() -> None:
    out = merge_rationale(_result(band="low", git_error="bad"), "block")
    assert "Git diff could not be computed" in out


def test_merge_rationale_block_includes_score() -> None:
    out = merge_rationale(_result(band="critical", score=80), "block")
    assert "80" in out
    assert "merge-blocked" in out


def test_merge_rationale_warn_includes_score() -> None:
    out = merge_rationale(_result(band="medium", score=30), "warn")
    assert "30" in out


def test_merge_rationale_pass_includes_score() -> None:
    out = merge_rationale(_result(band="low", score=10), "pass")
    assert "10" in out
    assert "low" in out.lower()


# ---------------------------------------------------------------------------
# review_strategy_for

def test_review_strategy_block() -> None:
    assert "Do not merge" in review_strategy_for("block", "high")


def test_review_strategy_warn_medium_uses_checklist() -> None:
    assert "checklist-driven" in review_strategy_for("warn", "medium")


def test_review_strategy_warn_other_band() -> None:
    assert "Complete the required actions" in review_strategy_for("warn", "high")


def test_review_strategy_pass() -> None:
    assert "Single-pass" in review_strategy_for("pass", "low")


# ---------------------------------------------------------------------------
# review_requirements

def test_review_requirements_baseline() -> None:
    out = review_requirements("pass", "low", 10)
    assert any("approving review" in s for s in out)


def test_review_requirements_block_adds_explicit_signoff() -> None:
    out = review_requirements("block", "high", 60)
    assert any("Explicit sign-off" in s for s in out)


def test_review_requirements_high_band_adds_familiar_reviewer() -> None:
    out = review_requirements("warn", "high", 50)
    assert any("familiar with the touched subsystems" in s for s in out)


def test_review_requirements_high_score_adds_ci_check() -> None:
    out = review_requirements("warn", "medium", 50)
    assert any("CI is green" in s for s in out)


def test_review_requirements_dedupes() -> None:
    out = review_requirements("block", "critical", 80)
    assert len(out) == len(set(out))


# ---------------------------------------------------------------------------
# compute_blocking_reasons

def test_blocking_reasons_includes_git_error_first() -> None:
    out = compute_blocking_reasons(_result(band="low", git_error="bad"), "block")
    assert any("Git diff unavailable" in s for s in out)


def test_blocking_reasons_block_band() -> None:
    out = compute_blocking_reasons(_result(band="high", score=60), "block")
    assert any("Merge-block policy" in s for s in out)


def test_blocking_reasons_warn_band() -> None:
    out = compute_blocking_reasons(_result(band="medium", score=30), "warn")
    assert any("Elevated review" in s for s in out)


def test_blocking_reasons_floor_applied() -> None:
    r = Result(
        risk_score=20,
        risk_band="medium",
        signals=Signals(),
        score_math=ScoreMath(floor_applied=True, floor_reasons=["x"]),
    )
    out = compute_blocking_reasons(r, "warn")
    assert any("floor applied" in s.lower() for s in out)


# ---------------------------------------------------------------------------
# dedupe_strings

def test_dedupe_strings_preserves_order_and_strips() -> None:
    out = dedupe_strings(["a", "b ", " a", "", "c"])
    assert out == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# compute_enforcement (Phase-3 partial)

def test_compute_enforcement_populates_recommendation_and_strategy() -> None:
    r = _result(band="medium", score=30)
    e = compute_enforcement(r)
    assert e.merge_recommendation == "warn"
    assert "checklist-driven" in e.recommended_review.strategy
    # Phase 4 fields stay empty until SCRUM-236.
    assert e.required_validations == []
    assert e.recommended_review.routing_hints == []
    assert e.evidence_status == []
