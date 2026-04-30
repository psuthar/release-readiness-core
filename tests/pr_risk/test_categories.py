"""Unit tests for pr_risk.categories."""

from release_readiness_core.pr_risk.categories import (
    compute_categories,
    lane_for_factor_id,
)
from release_readiness_core.pr_risk.categories import (
    test_confidence_score as compute_test_confidence,
)
from release_readiness_core.pr_risk.context.types import (
    ContextInsights,
    ProximityInsight,
)
from release_readiness_core.pr_risk.types import (
    CATEGORY_CODE,
    CATEGORY_TEST_CONFIDENCE,
    CATEGORY_WORKFLOW,
    RiskFactor,
    RiskReducer,
    Signals,
)


# ---------------------------------------------------------------------------
# lane_for_factor_id

def test_lane_for_factor_id_code_lane() -> None:
    for fid in [
        "git_unavailable",
        "diff_very_large",
        "diff_large",
        "many_files",
        "domain_auth",
        "domain_migrations",
        "domain_rag",
        "domain_processing",
        "domain_orchestration",
        "web_large",
    ]:
        assert lane_for_factor_id(fid) == CATEGORY_CODE


def test_lane_for_factor_id_workflow_lane() -> None:
    for fid in ["ci_workflows", "deploy_config", "go_mod_deps"]:
        assert lane_for_factor_id(fid) == CATEGORY_WORKFLOW


def test_lane_for_factor_id_test_confidence_lane() -> None:
    assert lane_for_factor_id("tests_missing") == CATEGORY_TEST_CONFIDENCE


def test_lane_for_factor_id_context_prefix_routes_to_code() -> None:
    for fid in [
        "context_test_proximity_distant",
        "context_change_scattered",
        "context_hotspot_overlap",
        "context_intent_mismatch",
    ]:
        assert lane_for_factor_id(fid) == CATEGORY_CODE


def test_lane_for_factor_id_unknown_defaults_to_code() -> None:
    assert lane_for_factor_id("brand_new_factor") == CATEGORY_CODE


# ---------------------------------------------------------------------------
# test_confidence_score

def test_test_confidence_high_when_no_sensitive_domains() -> None:
    s = Signals(domain_hits={"web": 1})
    score, bd = compute_test_confidence(s, None)
    assert score == 85.0  # base 50 + 35
    assert bd.base_score == 50.0


def test_test_confidence_low_when_sensitive_no_tests() -> None:
    s = Signals(domain_hits={"auth": 1})
    score, _ = compute_test_confidence(s, None)
    assert score == 25.0  # 50 - 10 - 15


def test_test_confidence_with_e2e_for_sensitive() -> None:
    s = Signals(domain_hits={"auth": 1}, e2e_test_files=1)
    score, _ = compute_test_confidence(s, None)
    assert score == 80.0  # 50 - 10 + 40


def test_test_confidence_with_unit_for_sensitive() -> None:
    s = Signals(domain_hits={"auth": 1}, unit_test_files=1)
    score, _ = compute_test_confidence(s, None)
    assert score == 60.0  # 50 - 10 + 20


def test_test_confidence_proximity_distant_penalty() -> None:
    s = Signals(domain_hits={"web": 1})
    ci = ContextInsights(
        proximity=ProximityInsight(mode="distant", structural_alignment="distant"),
    )
    score, _ = compute_test_confidence(s, ci)
    # No sensitive: 85; -15 distant; behavioral_coverage="" so no further adjust.
    assert score == 70.0


def test_test_confidence_proximity_partial_penalty() -> None:
    s = Signals(domain_hits={"web": 1})
    ci = ContextInsights(
        proximity=ProximityInsight(mode="partial", structural_alignment="partial"),
    )
    score, _ = compute_test_confidence(s, ci)
    assert score == 77.0  # 85 - 8


def test_test_confidence_clamped_at_zero() -> None:
    """Heavy penalties cannot drive score below 0."""
    s = Signals(domain_hits={"auth": 1})  # already -10 - 15 = -25
    ci = ContextInsights(
        proximity=ProximityInsight(
            mode="distant",
            structural_alignment="distant",
            behavioral_coverage="unknown",
        ),
    )
    score, _ = compute_test_confidence(s, ci)
    assert score >= 0.0


# ---------------------------------------------------------------------------
# compute_categories

def test_compute_categories_returns_three_lanes() -> None:
    s = Signals(domain_hits={"web": 1})
    cats = compute_categories(s, [], [], None)
    keys = [c.key for c in cats]
    assert keys == [CATEGORY_CODE, CATEGORY_WORKFLOW, CATEGORY_TEST_CONFIDENCE]


def test_compute_categories_factors_routed_per_lane() -> None:
    s = Signals(domain_hits={"web": 1})
    factors = [
        RiskFactor(id="domain_auth", label="auth", points=14),
        RiskFactor(id="ci_workflows", label="ci", points=12),
        RiskFactor(id="tests_missing", label="missing", points=18),
    ]
    cats = compute_categories(s, factors, [], None)
    code = next(c for c in cats if c.key == CATEGORY_CODE)
    wf = next(c for c in cats if c.key == CATEGORY_WORKFLOW)
    tc = next(c for c in cats if c.key == CATEGORY_TEST_CONFIDENCE)
    assert "domain_auth" in code.factors
    assert "ci_workflows" in wf.factors
    assert "tests_missing" in tc.factors


def test_compute_categories_reducers_routed_by_category_key() -> None:
    s = Signals(domain_hits={"web": 1})
    reducers = [
        RiskReducer(id="r1", label="x", points=4, category_key=CATEGORY_WORKFLOW),
        RiskReducer(id="r2", label="y", points=5, category_key=""),  # default to code
    ]
    cats = compute_categories(s, [], reducers, None)
    code = next(c for c in cats if c.key == CATEGORY_CODE)
    wf = next(c for c in cats if c.key == CATEGORY_WORKFLOW)
    assert "r2" in code.reducers
    assert "r1" in wf.reducers


def test_compute_categories_git_error_decreases_confidence() -> None:
    s = Signals(domain_hits={"auth": 1}, git_error="bad ref")
    cats = compute_categories(s, [], [], None)
    tc = next(c for c in cats if c.key == CATEGORY_TEST_CONFIDENCE)
    # Confidence further dropped by -10 due to git_error.
    assert any("Git error" in adj.reason for adj in tc.breakdown.adjustments)
