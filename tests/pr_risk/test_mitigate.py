"""Tests for pr_risk.mitigate."""

from release_readiness_core.pr_risk.mitigate import (
    MITIGATION_MAP,
    go_mod_changed,
    mitigate,
)
from release_readiness_core.pr_risk.types import FileChange, RiskFactor, Signals


def _fac(id_: str) -> RiskFactor:
    return RiskFactor(id=id_, label=id_.replace("_", " "), points=10.0)


def test_mitigate_returns_actions_for_known_factor() -> None:
    out = mitigate([_fac("domain_auth")])
    assert len(out) == 1
    assert out[0].factor_id == "domain_auth"
    assert any("auth" in a.lower() for a in out[0].actions)


def test_mitigate_default_fallback_for_unknown_factor() -> None:
    out = mitigate([_fac("totally_made_up_factor_id")])
    assert len(out) == 1
    assert out[0].factor_id == "totally_made_up_factor_id"
    assert len(out[0].actions) == 1
    assert "Review this factor" in out[0].actions[0]


def test_mitigate_dedups_repeated_factor_ids() -> None:
    out = mitigate([_fac("domain_auth"), _fac("domain_auth"), _fac("domain_rag")])
    assert [m.factor_id for m in out] == ["domain_auth", "domain_rag"]


def test_mitigate_preserves_input_order() -> None:
    out = mitigate([_fac("domain_rag"), _fac("ci_workflows"), _fac("tests_missing")])
    assert [m.factor_id for m in out] == ["domain_rag", "ci_workflows", "tests_missing"]


def test_mitigate_returns_independent_action_lists() -> None:
    """Mutating one mitigation's actions must not affect the next call."""
    out1 = mitigate([_fac("domain_auth")])
    out1[0].actions.append("MUTATED")
    out2 = mitigate([_fac("domain_auth")])
    assert "MUTATED" not in out2[0].actions


def test_mitigation_map_has_known_factors() -> None:
    expected = {
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
        "ci_workflows",
        "deploy_config",
        "go_mod_deps",
        "tests_missing",
        "context_test_proximity_distant",
        "context_change_scattered",
        "context_hotspot_overlap",
        "context_intent_mismatch",
    }
    assert expected.issubset(MITIGATION_MAP.keys())


def test_go_mod_changed_true_when_go_mod() -> None:
    s = Signals(files=[FileChange(path="go.mod"), FileChange(path="internal/x.go")])
    assert go_mod_changed(s) is True


def test_go_mod_changed_true_when_go_sum() -> None:
    s = Signals(files=[FileChange(path="go.sum")])
    assert go_mod_changed(s) is True


def test_go_mod_changed_false_when_neither() -> None:
    s = Signals(files=[FileChange(path="internal/x.go"), FileChange(path="README.md")])
    assert go_mod_changed(s) is False


def test_go_mod_changed_with_nested_path() -> None:
    """Only basename is checked — vendored go.mod under subdirs still matches."""
    s = Signals(files=[FileChange(path="vendor/foo/go.mod")])
    assert go_mod_changed(s) is True
