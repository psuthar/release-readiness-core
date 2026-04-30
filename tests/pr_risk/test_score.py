"""Unit tests for pr_risk.score (band, clamp_100, web_churn, score)."""

import pytest

from release_readiness_core.pr_risk.score import band, clamp_100, score, web_churn
from release_readiness_core.pr_risk.types import (
    FileChange,
    Signals,
    default_weights,
)


@pytest.mark.parametrize(
    "s,expected",
    [
        (0, "low"),
        (10, "low"),
        (19.99, "low"),
        (20, "medium"),
        (44.99, "medium"),
        (45, "high"),
        (69.99, "high"),
        (70, "critical"),
        (100, "critical"),
    ],
)
def test_band_thresholds(s: float, expected: str) -> None:
    assert band(s) == expected


def test_clamp_100_below_zero() -> None:
    assert clamp_100(-5) == 0.0


def test_clamp_100_above_hundred() -> None:
    assert clamp_100(150) == 100.0


def test_clamp_100_rounds_to_one_decimal_half_away() -> None:
    """Mirrors Go score.go::clamp100 — math.Round(x*10)/10."""
    assert clamp_100(50.05) == 50.1  # 0.05 → up via half-away
    assert clamp_100(50.04) == 50.0
    assert clamp_100(99.99) == 100.0


def test_web_churn_sums_only_web_paths() -> None:
    s = Signals(
        files=[
            FileChange(path="web/src/A.tsx", added=10, deleted=2),
            FileChange(path="internal/x.go", added=99, deleted=1),
            FileChange(path="web/tests/foo.test.tsx", added=3, deleted=0),
        ]
    )
    assert web_churn(s) == 15  # 12 + 3, ignores internal/


def test_web_churn_empty() -> None:
    assert web_churn(Signals()) == 0


# ---------------------------------------------------------------------------
# score() integration tests with synthetic signals.

def test_score_emits_domain_auth_factor() -> None:
    s = Signals(
        file_count=1,
        total_added=10,
        total_loc=10,
        files=[FileChange(path="internal/auth/login.go", added=10, deleted=0)],
        domain_hits={"auth": 1},
    )
    r = score(s, default_weights())
    ids = {f.id for f in r.factors}
    assert "domain_auth" in ids


def test_score_emits_diff_large_factor() -> None:
    s = Signals(
        file_count=1,
        total_added=500,
        total_loc=500,
        files=[FileChange(path="internal/foo.go", added=500, deleted=0)],
        domain_hits={"api": 1},
    )
    r = score(s, default_weights())
    ids = {f.id for f in r.factors}
    assert "diff_large" in ids


def test_score_emits_diff_very_large_factor() -> None:
    s = Signals(
        file_count=1,
        total_added=2500,
        total_loc=2500,
        files=[FileChange(path="internal/foo.go", added=2500, deleted=0)],
        domain_hits={"api": 1},
    )
    r = score(s, default_weights())
    ids = {f.id for f in r.factors}
    assert "diff_very_large" in ids
    assert "diff_large" not in ids  # very_large takes precedence


def test_score_emits_many_files_factor() -> None:
    s = Signals(
        file_count=40,
        total_added=200,
        total_loc=200,
        files=[FileChange(path=f"internal/x{i}.go", added=5, deleted=0) for i in range(40)],
        domain_hits={"api": 40},
    )
    r = score(s, default_weights())
    ids = {f.id for f in r.factors}
    assert "many_files" in ids


def test_score_git_unavailable_short_circuits_size_factors() -> None:
    s = Signals(
        file_count=10, total_added=1000, total_loc=1000, git_error="fatal: bad ref"
    )
    r = score(s, default_weights())
    ids = {f.id for f in r.factors}
    assert "git_unavailable" in ids
    # When git_error is set, diff size factors are NOT emitted (per Go score.go).
    assert "diff_large" not in ids
    assert "diff_very_large" not in ids


def test_score_emits_go_mod_deps_factor() -> None:
    s = Signals(
        file_count=1,
        total_added=1,
        total_loc=1,
        files=[FileChange(path="go.mod", added=1, deleted=0)],
        domain_hits={"other": 1},
    )
    r = score(s, default_weights())
    ids = {f.id for f in r.factors}
    assert "go_mod_deps" in ids


def test_score_emits_tests_missing_factor_for_sensitive_domain() -> None:
    s = Signals(
        file_count=1,
        total_added=10,
        total_loc=10,
        files=[FileChange(path="internal/auth/login.go", added=10, deleted=0)],
        domain_hits={"auth": 1},
    )
    r = score(s, default_weights())
    ids = {f.id for f in r.factors}
    assert "tests_missing" in ids


def test_score_no_tests_missing_when_tests_present() -> None:
    s = Signals(
        file_count=2,
        total_added=20,
        total_loc=20,
        test_files=1,
        test_unit_domain_hits={"auth": 1},
        files=[
            FileChange(path="internal/auth/login.go", added=10, deleted=0),
            FileChange(path="internal/auth/login_test.go", added=10, deleted=0),
        ],
        domain_hits={"auth": 1, "tests": 1},
    )
    r = score(s, default_weights())
    ids = {f.id for f in r.factors}
    assert "tests_missing" not in ids


def test_score_returns_low_band_for_trivial_diff() -> None:
    s = Signals(
        file_count=1,
        total_added=1,
        total_loc=1,
        files=[FileChange(path="README.md", added=1, deleted=0)],
        domain_hits={"other": 1},
    )
    r = score(s, default_weights())
    assert r.risk_band == "low"
    assert r.score_math.factors_subtotal == 0.0


def test_score_score_math_consistency() -> None:
    """factors_subtotal - reducers_subtotal == net_before_floor (clamped)."""
    s = Signals(
        file_count=1,
        total_added=10,
        total_loc=10,
        files=[FileChange(path="internal/auth/login.go", added=10, deleted=0)],
        domain_hits={"auth": 1},
    )
    r = score(s, default_weights())
    expected_net = max(0, min(100, r.score_math.factors_subtotal - r.score_math.reducers_subtotal))
    assert abs(r.score_math.net_before_floor - expected_net) < 0.11  # one-decimal clamp tolerance


def test_score_floor_applied_for_workflow_only_diff() -> None:
    """A diff that triggers ci_workflows but has lots of reducers should still hit the floor."""
    s = Signals(
        file_count=1,
        total_added=1,
        total_loc=1,
        files=[FileChange(path=".github/workflows/ci.yml", added=1, deleted=0)],
        domain_hits={"workflows": 1},
        config_files=1,
    )
    r = score(s, default_weights())
    # ci_workflows fires; floor=20 ensures band >= medium.
    assert r.risk_band != "low"
    assert r.score_math.floor_min_score == 20.0
