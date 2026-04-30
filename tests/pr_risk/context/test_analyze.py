"""Tests for pr_risk.context.analyze (orchestration + factor contributions)."""

from release_readiness_core.pr_risk.context.analyze import (
    analyze,
    default_weights,
    has_sensitive_domain,
    should_flag_proximity,
)
from release_readiness_core.pr_risk.context.input import FileChange, Input
from release_readiness_core.pr_risk.context.types import ProximityInsight


def test_default_weights_match_go() -> None:
    w = default_weights()
    assert w.proximity_low_points == 5
    assert w.scattered_points == 5
    assert w.hotspot_points == 4
    assert w.intent_mismatch_points == 6


def test_has_sensitive_domain_true_for_each() -> None:
    for d in ("auth", "rag", "processing", "migrations", "api", "database"):
        assert has_sensitive_domain({d: 1}) is True


def test_has_sensitive_domain_false_for_others() -> None:
    assert has_sensitive_domain({"web": 1}) is False
    assert has_sensitive_domain({"workflows": 1}) is False
    assert has_sensitive_domain(None) is False


def test_should_flag_proximity_requires_distant_mode_and_sensitive_domain() -> None:
    inp = Input(domain_hits={"auth": 1})
    assert should_flag_proximity(
        inp, ProximityInsight(mode="distant", non_test_files=2)
    ) is True
    # Not distant
    assert should_flag_proximity(
        inp, ProximityInsight(mode="partial", non_test_files=2)
    ) is False
    # Too few non-test files
    assert should_flag_proximity(
        inp, ProximityInsight(mode="distant", non_test_files=1)
    ) is False
    # No sensitive domain
    assert should_flag_proximity(
        Input(domain_hits={"web": 1}), ProximityInsight(mode="distant", non_test_files=2)
    ) is False


def test_analyze_emits_proximity_factor_for_sensitive_distant_diff() -> None:
    files = [
        FileChange(path="internal/auth/login.go"),
        FileChange(path="internal/auth/session.go"),
    ]
    inp = Input(
        files=files,
        is_test=[False, False],
        is_untestable=[False, False],
        domain_hits={"auth": 2},
    )
    insights, factors = analyze(inp, default_weights())
    factor_ids = {f.id for f in factors}
    assert "context_test_proximity_distant" in factor_ids
    assert insights.proximity.mode == "distant"


def test_analyze_emits_scattered_factor_at_threshold() -> None:
    files = [
        FileChange(path=f"area{i}/sub/file.go", added=10, deleted=0) for i in range(10)
    ]
    inp = Input(
        files=files,
        is_test=[False] * 10,
        is_untestable=[False] * 10,
        domain_hits={"web": 10},
    )
    _, factors = analyze(inp, default_weights())
    factor_ids = {f.id for f in factors}
    assert "context_change_scattered" in factor_ids


def test_analyze_emits_intent_mismatch_factor() -> None:
    files = [FileChange(path="internal/auth/login.go")]
    inp = Input(
        files=files,
        is_test=[False],
        is_untestable=[False],
        domain_hits={"web": 1},
        pr_title="auth: tighten flow",
    )
    _, factors = analyze(inp, default_weights())
    factor_ids = {f.id for f in factors}
    assert "context_intent_mismatch" in factor_ids


def test_analyze_emits_no_factors_for_aligned_simple_diff() -> None:
    files = [
        FileChange(path="web/src/App.tsx"),
        FileChange(path="web/src/App.test.tsx"),
    ]
    inp = Input(
        files=files,
        is_test=[False, True],
        is_untestable=[False, False],
        domain_hits={"web": 1, "tests": 1},
        pr_title="web: tweak App layout",
    )
    insights, factors = analyze(inp, default_weights())
    assert insights.proximity.mode == "co_located"
    factor_ids = {f.id for f in factors}
    assert "context_test_proximity_distant" not in factor_ids
    assert "context_change_scattered" not in factor_ids
    assert "context_intent_mismatch" not in factor_ids
