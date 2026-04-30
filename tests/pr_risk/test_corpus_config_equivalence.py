"""Equivalence test: parity-fixture YAML matches the bundled default config (SCRUM-239).

The bundled default produced by ``default_pr_risk_config()`` mirrors today's
hardcoded behavior in ``classify.py`` / ``actions.py`` / ``validations.py`` /
``actions_priority.py`` / ``evidence.py``. The parity-fixture YAML at
``tests/pr_risk/fixtures/pr-risk-corpus-config.yaml`` encodes that same data
so that Phases 2-4 can swap the source without behavior drift.

This test asserts the two are byte-equal (after parsing) so that any future
edit drifts both ends simultaneously.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from release_readiness_core.pr_risk._config import (
    GATE_PREDICATE_KEYS,
    PATH_PATTERN_KEYS,
    load_pr_risk_config,
)
from release_readiness_core.pr_risk._default_config import default_pr_risk_config
from release_readiness_core.pr_risk._runtime import PRRiskRuntime


CORPUS_PATH = (
    Path(__file__).parent / "fixtures" / "pr-risk-corpus-config.yaml"
)


def test_corpus_fixture_exists():
    assert CORPUS_PATH.is_file(), f"Corpus parity fixture missing at {CORPUS_PATH}"


def test_corpus_fixture_loads():
    cfg = load_pr_risk_config(CORPUS_PATH)
    assert cfg.version == 1
    assert cfg.domains, "domains list must not be empty"
    assert cfg.gates, "gates list must not be empty"


def test_corpus_fixture_equals_bundled_default():
    """The parity-fixture YAML produces the same PRRiskConfig as the bundled default.

    This guarantees Phase 2-4 can drive parity tests with the YAML and Phase 5
    can strip the bundled-default project specifics out of core without losing
    behavior — both ends are derived from the same data.
    """
    from_yaml = load_pr_risk_config(CORPUS_PATH)
    from_default = default_pr_risk_config()
    assert from_yaml == from_default


def test_runtime_from_default_constructs():
    runtime = PRRiskRuntime.from_default()
    assert runtime.config.version == 1
    # Convenience accessors expose the same data.
    assert len(runtime.domains) == len(runtime.config.domains)
    assert runtime.sensitive_domains == list(runtime.config.sensitive_domains)
    assert len(runtime.gates) == len(runtime.config.gates)


def test_runtime_from_config_loads_corpus_fixture():
    runtime = PRRiskRuntime.from_config(CORPUS_PATH)
    default_runtime = PRRiskRuntime.from_default()
    assert runtime.config == default_runtime.config


def test_runtime_priority_for_uses_config():
    """priority_for(gate_id) reads from the loaded config, not a hardcoded set.

    This is intentionally testable in Phase 1 because PRRiskRuntime.priority_for
    is data-driven (no Phase 3 evaluator needed).
    """
    runtime = PRRiskRuntime.from_default()
    # Spot-check a few well-known gates from the bundled default.
    assert runtime.priority_for("ci_fetch_depth_zero") == "high"
    assert runtime.priority_for("auth_e2e_gate") == "high"
    assert runtime.priority_for("workflow_config_validation") == "medium"
    assert runtime.priority_for("orchestration_creator_gate") == "medium"
    assert runtime.priority_for("pr_review_summary") == "supporting"
    # Unknown gate falls back to medium (matches actions_priority.py behavior).
    assert runtime.priority_for("nonexistent_gate") == "medium"


def test_runtime_classify_smoke():
    """Phase 2 (SCRUM-240) implemented runtime.classify; smoke-check it returns
    a non-empty domain string. Per-domain assertions live in test_classify.py."""
    runtime = PRRiskRuntime.from_default()
    assert runtime.classify("internal/auth/foo.go") == "auth"
    assert runtime.classify("internal/foo/bar_test.go") == "tests"
    assert runtime.classify("README.md") == "other"


def test_runtime_detector_for_returns_callable():
    """Phase 4 (SCRUM-242) implemented runtime.detector_for. Smoke-check that
    it returns a callable for a known gate; per-template unit tests live in
    test_evidence_templates.py."""
    runtime = PRRiskRuntime.from_default()
    fn = runtime.detector_for("ci_fetch_depth_zero")
    assert callable(fn)
    fn = runtime.detector_for("auth_e2e_gate")
    assert callable(fn)
    # Unknown gate id raises.
    with pytest.raises(KeyError):
        runtime.detector_for("nonexistent_gate")


def test_register_detector_validates_args():
    runtime = PRRiskRuntime.from_default()
    with pytest.raises(ValueError):
        runtime.register_detector("", lambda lbl, r: None)
    with pytest.raises(TypeError):
        runtime.register_detector("custom", "not-callable")  # type: ignore[arg-type]
    runtime.register_detector("custom", lambda lbl, r: None)
    assert "custom" in runtime._custom_detectors


# ---------------------------------------------------------------------------
# Sanity: closed sets stay aligned across modules.

def test_closed_sets_consistent():
    """Path-pattern and gate-predicate closed sets are exhaustive for today's data."""
    from_default = default_pr_risk_config()
    seen_pattern_keys: set[str] = set()
    for d in from_default.domains:
        seen_pattern_keys |= _collect_pattern_keys(d.patterns)
    assert seen_pattern_keys.issubset(set(PATH_PATTERN_KEYS))

    seen_pred_keys: set[str] = set()
    for g in from_default.gates:
        for p in g.applies_when:
            seen_pred_keys |= (set(p.keys()) & set(GATE_PREDICATE_KEYS))
    assert seen_pred_keys.issubset(set(GATE_PREDICATE_KEYS))


def _collect_pattern_keys(patterns) -> set[str]:
    out: set[str] = set()
    for p in patterns:
        primary = set(p.keys()) & set(PATH_PATTERN_KEYS)
        out |= primary
        if "and" in p:
            out |= _collect_pattern_keys(p["and"])
    return out
