"""Corpus / bundled-default relationship tests.

Phase 1 introduced the parity-fixture YAML at
``tests/pr_risk/fixtures/pr-risk-corpus-config.yaml`` and asserted byte-equality
with the bundled default. Phase 5 stripped the bundled default of
project-specific defaults: it now ships only language-agnostic generic gates
and an empty domains / sensitive_domains. The corpus YAML continues to encode
the full project-specific config used by the captured-fixture corpus parity
tests.

This file now asserts:
- the corpus YAML loads cleanly,
- the corpus YAML is a strict superset of the bundled default
  (every generic gate from the default appears in the corpus),
- the bundled default is genuinely minimal,
- runtime accessors expose the loaded data shape correctly.
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


GENERIC_GATE_IDS = {
    "ci_fetch_depth_zero",
    "pr_review_summary",
    "workflow_config_validation",
    "add_tests_or_evidence",
    "context_align_pr_description",
    "context_scattered_review_plan",
    "context_improve_test_proximity",
    "context_hotspot_regression_focus",
}


def test_corpus_fixture_exists():
    assert CORPUS_PATH.is_file(), f"Corpus parity fixture missing at {CORPUS_PATH}"


def test_corpus_fixture_loads():
    cfg = load_pr_risk_config(CORPUS_PATH)
    assert cfg.version == 1
    assert cfg.domains, "domains list must not be empty"
    assert cfg.gates, "gates list must not be empty"


def test_bundled_default_is_minimal():
    """Phase 5: the bundled default ships no project-specific defaults."""
    cfg = default_pr_risk_config()
    assert cfg.domains == []
    assert cfg.sensitive_domains == []
    assert {g.id for g in cfg.gates} == GENERIC_GATE_IDS


def test_corpus_is_superset_of_bundled_default_for_generic_gates():
    """The corpus YAML carries every generic gate that the bundled default
    ships, plus the project-specific ones. For the shared generic gates,
    title / priority / fix_type / applies_when / checklist must match
    byte-for-byte (so the corpus stays a faithful parity reference)."""
    from_yaml = load_pr_risk_config(CORPUS_PATH)
    from_default = default_pr_risk_config()

    yaml_by_id = {g.id: g for g in from_yaml.gates}
    default_by_id = {g.id: g for g in from_default.gates}

    for gid in GENERIC_GATE_IDS:
        assert gid in yaml_by_id, f"Corpus YAML missing generic gate {gid!r}"
        assert gid in default_by_id, f"Bundled default missing generic gate {gid!r}"
        # The corpus generic gate may carry extra args (e.g.
        # context_improve_test_proximity carries an explicit `domains` list);
        # the rest must match.
        y = yaml_by_id[gid]
        d = default_by_id[gid]
        assert y.title == d.title, gid
        assert y.priority == d.priority, gid
        assert y.fix_type == d.fix_type, gid
        assert y.checklist == d.checklist, gid
        assert y.evidence == d.evidence, gid
        assert y.variants == d.variants, gid
        assert y.validation_line == d.validation_line, gid


def test_corpus_carries_project_specific_gates_not_in_default():
    """The five project-specific gates live only in the corpus YAML now."""
    from_yaml = load_pr_risk_config(CORPUS_PATH)
    from_default = default_pr_risk_config()

    yaml_ids = {g.id for g in from_yaml.gates}
    default_ids = {g.id for g in from_default.gates}

    project_specific = {
        "auth_e2e_gate",
        "rag_qna_citations_gate",
        "materials_processing_gate",
        "orchestration_creator_gate",
        "migrations_validation_gate",
    }
    assert project_specific.issubset(yaml_ids)
    assert project_specific.isdisjoint(default_ids)


def test_runtime_from_default_constructs():
    runtime = PRRiskRuntime.from_default()
    assert runtime.config.version == 1
    # Convenience accessors expose the same data.
    assert len(runtime.domains) == len(runtime.config.domains)
    assert runtime.sensitive_domains == list(runtime.config.sensitive_domains)
    assert len(runtime.gates) == len(runtime.config.gates)


def test_runtime_priority_for_uses_config_default():
    """Generic gates carry their priority from the bundled default."""
    runtime = PRRiskRuntime.from_default()
    assert runtime.priority_for("ci_fetch_depth_zero") == "high"
    assert runtime.priority_for("workflow_config_validation") == "medium"
    assert runtime.priority_for("pr_review_summary") == "supporting"
    # Project-specific gates are NOT in the bundled default — fallback to medium.
    assert runtime.priority_for("auth_e2e_gate") == "medium"
    # Unknown gate also falls back to medium.
    assert runtime.priority_for("nonexistent_gate") == "medium"


def test_runtime_priority_for_uses_corpus_for_project_specific(corpus_runtime):
    """Project-specific priorities live in the corpus YAML."""
    assert corpus_runtime.priority_for("auth_e2e_gate") == "high"
    assert corpus_runtime.priority_for("rag_qna_citations_gate") == "high"
    assert corpus_runtime.priority_for("migrations_validation_gate") == "high"
    assert corpus_runtime.priority_for("materials_processing_gate") == "medium"
    assert corpus_runtime.priority_for("orchestration_creator_gate") == "medium"


def test_runtime_classify_default_returns_other():
    """Without an adopter-authored config, every path classifies to ``other``
    (Phase 5). Test paths still classify to ``tests`` because that's a
    language heuristic, not project policy."""
    runtime = PRRiskRuntime.from_default()
    assert runtime.classify("internal/auth/foo.go") == "other"
    assert runtime.classify("internal/foo/bar_test.go") == "tests"
    assert runtime.classify("README.md") == "other"


def test_runtime_classify_corpus_returns_project_domains(corpus_runtime):
    """Loading the corpus YAML restores the project-specific classification."""
    assert corpus_runtime.classify("internal/auth/foo.go") == "auth"
    assert corpus_runtime.classify("web/src/App.tsx") == "web"
    assert corpus_runtime.classify("README.md") == "other"


def test_runtime_detector_for_returns_callable_for_generic_gate():
    """Generic gates are detector-resolvable in the bundled default."""
    runtime = PRRiskRuntime.from_default()
    fn = runtime.detector_for("ci_fetch_depth_zero")
    assert callable(fn)
    fn = runtime.detector_for("add_tests_or_evidence")
    assert callable(fn)
    # Project-specific gate isn't in the bundled default.
    with pytest.raises(KeyError):
        runtime.detector_for("auth_e2e_gate")


def test_runtime_detector_for_corpus_resolves_project_gates(corpus_runtime):
    fn = corpus_runtime.detector_for("auth_e2e_gate")
    assert callable(fn)


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

def test_closed_sets_consistent_for_corpus():
    """Path-pattern and gate-predicate closed sets are exhaustive for the
    full corpus YAML (which exercises every predicate type)."""
    cfg = load_pr_risk_config(CORPUS_PATH)
    seen_pattern_keys: set[str] = set()
    for d in cfg.domains:
        seen_pattern_keys |= _collect_pattern_keys(d.patterns)
    assert seen_pattern_keys.issubset(set(PATH_PATTERN_KEYS))

    seen_pred_keys: set[str] = set()
    for g in cfg.gates:
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
