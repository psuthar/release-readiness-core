"""Tests for pr_risk.reducers."""

from release_readiness_core.pr_risk.reducers import (
    detect_reducers,
    short_snippet,
    validation_note_strength,
)
from release_readiness_core.pr_risk.types import (
    CATEGORY_CODE,
    CATEGORY_TEST_CONFIDENCE,
    CATEGORY_WORKFLOW,
    RiskFactor,
    Signals,
    default_weights,
)


def _fac(id_: str) -> RiskFactor:
    return RiskFactor(id=id_, label=id_, points=10.0)


# ---------------------------------------------------------------------------
# validation_note_strength

def test_validation_note_strength_strong_keywords() -> None:
    for s in [
        "ran e2e suite on staging",
        "smoke pass",
        "Playwright spec green",
        "end-to-end manual run",
    ]:
        assert validation_note_strength(s) == "strong"


def test_validation_note_strength_moderate_keywords() -> None:
    for s in [
        "deployed to staging",
        "workflow_dispatch run",
        "deploy validated",
        "tested in pipeline",
        "verified in CI today",  # Go matches " ci " — leading + trailing space required
    ]:
        assert validation_note_strength(s) == "moderate", s


def test_validation_note_strength_basic_default() -> None:
    assert validation_note_strength("looked good") == "basic"
    assert validation_note_strength("") == "basic"


# ---------------------------------------------------------------------------
# short_snippet

def test_short_snippet_short_unchanged() -> None:
    assert short_snippet("hello world") == "hello world"


def test_short_snippet_truncates_at_77_with_ellipsis() -> None:
    s = "a" * 100
    assert short_snippet(s) == "a" * 77 + "..."
    assert len(short_snippet(s)) == 80


def test_short_snippet_strips() -> None:
    assert short_snippet("   trimmed   ") == "trimmed"


def test_short_snippet_empty() -> None:
    assert short_snippet("") == ""
    assert short_snippet("   ") == ""


# ---------------------------------------------------------------------------
# detect_reducers — validation note tiers

def test_validation_note_strong_emits_strong_reducer() -> None:
    s = Signals(
        validation_note_found=True,
        validation_note_snippet="ran e2e on staging",
    )
    out = detect_reducers(s, [_fac("ci_workflows")], default_weights())
    ids = {r.id for r in out}
    assert "validation_note_strong" in ids


def test_validation_note_moderate_emits_moderate_reducer() -> None:
    s = Signals(
        validation_note_found=True,
        validation_note_snippet="deployed to staging",
    )
    out = detect_reducers(s, [_fac("deploy_config")], default_weights())
    ids = {r.id for r in out}
    assert "validation_note_moderate" in ids


def test_validation_note_basic_emits_basic_reducer() -> None:
    s = Signals(
        validation_note_found=True,
        validation_note_snippet="looked good locally",
    )
    out = detect_reducers(s, [_fac("go_mod_deps")], default_weights())
    ids = {r.id for r in out}
    assert "validation_note_basic" in ids


def test_validation_note_without_corresponding_factor_no_reducer() -> None:
    """validation note emits no reducer if none of {ci_workflows, deploy_config, go_mod_deps} are present."""
    s = Signals(validation_note_found=True, validation_note_snippet="ran e2e")
    out = detect_reducers(s, [_fac("domain_auth")], default_weights())
    assert all(not r.id.startswith("validation_note") for r in out)


# ---------------------------------------------------------------------------
# detect_reducers — domain test evidence

def test_e2e_test_evidence_per_domain() -> None:
    s = Signals(test_e2e_domain_hits={"auth": 1})
    out = detect_reducers(s, [_fac("domain_auth")], default_weights())
    ids = {r.id for r in out}
    assert "domain_auth_e2e_evidence" in ids
    assert "domain_auth_unit_evidence" not in ids


def test_unit_test_evidence_per_domain_when_no_e2e() -> None:
    s = Signals(test_unit_domain_hits={"rag": 1})
    out = detect_reducers(s, [_fac("domain_rag")], default_weights())
    ids = {r.id for r in out}
    assert "domain_rag_unit_evidence" in ids
    assert "domain_rag_e2e_evidence" not in ids


def test_e2e_takes_precedence_over_unit() -> None:
    s = Signals(
        test_e2e_domain_hits={"processing": 1},
        test_unit_domain_hits={"processing": 1},
    )
    out = detect_reducers(s, [_fac("domain_processing")], default_weights())
    ids = {r.id for r in out}
    assert "domain_processing_e2e_evidence" in ids
    assert "domain_processing_unit_evidence" not in ids


def test_no_evidence_reducer_without_domain_factor() -> None:
    s = Signals(test_e2e_domain_hits={"auth": 1})
    out = detect_reducers(s, [], default_weights())
    assert all("evidence" not in r.id for r in out)


# ---------------------------------------------------------------------------
# detect_reducers — style-only

def test_style_only_emits_when_no_backend_domain() -> None:
    s = Signals(
        style_only_note_found=True,
        style_only_note_snippet="Style-only: header padding",
        domain_hits={"web": 1},
        file_count=1,
    )
    out = detect_reducers(s, [], default_weights())
    ids = {r.id for r in out}
    assert "style_only_note" in ids


def test_style_only_suppressed_when_backend_touched() -> None:
    s = Signals(
        style_only_note_found=True,
        style_only_note_snippet="Style-only: x",
        domain_hits={"web": 1, "auth": 1},
    )
    out = detect_reducers(s, [], default_weights())
    ids = {r.id for r in out}
    assert "style_only_note" not in ids


# ---------------------------------------------------------------------------
# detect_reducers — test-only diff

def test_test_only_diff_emits_when_all_test_files() -> None:
    s = Signals(
        file_count=3,
        test_files=3,
        domain_hits={"tests": 3},
    )
    out = detect_reducers(s, [], default_weights())
    ids = {r.id for r in out}
    assert "test_only_diff" in ids


def test_test_only_diff_suppressed_when_sensitive_domain_present() -> None:
    s = Signals(
        file_count=2,
        test_files=2,
        domain_hits={"auth": 1},
    )
    out = detect_reducers(s, [], default_weights())
    ids = {r.id for r in out}
    assert "test_only_diff" not in ids


def test_test_only_diff_suppressed_when_not_all_tests() -> None:
    s = Signals(file_count=2, test_files=1)
    out = detect_reducers(s, [], default_weights())
    ids = {r.id for r in out}
    assert "test_only_diff" not in ids


# ---------------------------------------------------------------------------
# detect_reducers — test-heavy diff

def test_test_heavy_diff_emits_at_threshold() -> None:
    s = Signals(file_count=10, test_files=4, test_loc_ratio=0.5)
    out = detect_reducers(s, [], default_weights())
    ids = {r.id for r in out}
    assert "test_heavy_diff" in ids


def test_test_heavy_diff_suppressed_below_threshold() -> None:
    s = Signals(file_count=10, test_files=4, test_loc_ratio=0.30)
    out = detect_reducers(s, [], default_weights())
    ids = {r.id for r in out}
    assert "test_heavy_diff" not in ids


def test_test_heavy_diff_suppressed_when_all_tests() -> None:
    """test_heavy requires test_files < file_count; equal counts trigger test_only_diff instead."""
    s = Signals(file_count=4, test_files=4, test_loc_ratio=0.95)
    out = detect_reducers(s, [], default_weights())
    ids = {r.id for r in out}
    assert "test_heavy_diff" not in ids


# ---------------------------------------------------------------------------
# Category keys

def test_validation_note_reducer_category_workflow() -> None:
    s = Signals(validation_note_found=True, validation_note_snippet="ran e2e")
    out = detect_reducers(s, [_fac("ci_workflows")], default_weights())
    matches = [r for r in out if r.id.startswith("validation_note")]
    assert matches
    assert matches[0].category_key == CATEGORY_WORKFLOW


def test_e2e_evidence_reducer_category_test_confidence() -> None:
    s = Signals(test_e2e_domain_hits={"auth": 1})
    out = detect_reducers(s, [_fac("domain_auth")], default_weights())
    match = next(r for r in out if r.id == "domain_auth_e2e_evidence")
    assert match.category_key == CATEGORY_TEST_CONFIDENCE


def test_test_only_diff_category_code() -> None:
    s = Signals(file_count=1, test_files=1, domain_hits={"tests": 1})
    out = detect_reducers(s, [], default_weights())
    match = next(r for r in out if r.id == "test_only_diff")
    assert match.category_key == CATEGORY_CODE
