"""Unit tests for pr_risk.evidence detectors."""

from release_readiness_core.pr_risk.evidence import (
    compute_evidence_status,
    evidence_aware_upgrade,
    evidence_blocking_reasons,
    evidence_for_action_id,
    evidence_status_icon,
)
from release_readiness_core.pr_risk.context.types import (
    ContextInsights,
    IntentInsight,
    ProximityInsight,
)
from release_readiness_core.pr_risk.types import (
    EVIDENCE_FAIL,
    EVIDENCE_MISSING,
    EVIDENCE_NOT_EVALUATED,
    EVIDENCE_PASS,
    EVIDENCE_UNKNOWN,
    RequiredAction,
    Result,
    Signals,
)


def _result(*, signals=None, actions=None, ci=None) -> Result:
    return Result(
        signals=signals or Signals(),
        required_actions=list(actions or []),
        context_insights=ci,
    )


def test_compute_evidence_status_always_emits_ci_baseline() -> None:
    r = _result()
    out, _ = compute_evidence_status(r)
    assert any(ev.id == "ci_baseline" for ev in out)


def test_ci_baseline_fail_when_git_error() -> None:
    r = _result(signals=Signals(git_error="bad ref"))
    out, _ = compute_evidence_status(r)
    ci_base = next(ev for ev in out if ev.id == "ci_baseline")
    assert ci_base.status == EVIDENCE_FAIL


def test_ci_fetch_depth_pass_when_no_git_error() -> None:
    r = _result(actions=[RequiredAction(id="ci_fetch_depth_zero", title="x")])
    ev = evidence_for_action_id("ci_fetch_depth_zero", "x", r)
    assert ev.status == EVIDENCE_PASS


def test_ci_fetch_depth_fail_when_git_error() -> None:
    r = _result(
        signals=Signals(git_error="bad ref"),
        actions=[RequiredAction(id="ci_fetch_depth_zero", title="x")],
    )
    ev = evidence_for_action_id("ci_fetch_depth_zero", "x", r)
    assert ev.status == EVIDENCE_FAIL


def test_pr_review_summary_pass_for_strong_intent() -> None:
    ci = ContextInsights(intent=IntentInsight(intent_strength="strong"))
    r = _result(ci=ci)
    ev = evidence_for_action_id("pr_review_summary", "x", r)
    assert ev.status == EVIDENCE_PASS


def test_pr_review_summary_missing_for_weak_intent() -> None:
    ci = ContextInsights(intent=IntentInsight(intent_strength="weak", title="wip"))
    r = _result(ci=ci)
    ev = evidence_for_action_id("pr_review_summary", "x", r)
    assert ev.status == EVIDENCE_MISSING


def test_workflow_config_pass_with_validation_note() -> None:
    r = _result(signals=Signals(validation_note_found=True, validation_note_snippet="ran ci"))
    ev = evidence_for_action_id("workflow_config_validation", "x", r)
    assert ev.status == EVIDENCE_PASS


def test_workflow_config_not_evaluated_without_note() -> None:
    r = _result()
    ev = evidence_for_action_id("workflow_config_validation", "x", r)
    assert ev.status == EVIDENCE_NOT_EVALUATED


def test_test_domain_pass_for_e2e_hits() -> None:
    r = _result(signals=Signals(test_e2e_domain_hits={"auth": 1}))
    ev = evidence_for_action_id("auth_e2e_gate", "x", r)
    assert ev.status == EVIDENCE_PASS


def test_test_domain_not_evaluated_for_unit_only() -> None:
    r = _result(signals=Signals(test_unit_domain_hits={"auth": 1}))
    ev = evidence_for_action_id("auth_e2e_gate", "x", r)
    assert ev.status == EVIDENCE_NOT_EVALUATED


def test_test_domain_missing_when_no_hits() -> None:
    r = _result()
    ev = evidence_for_action_id("auth_e2e_gate", "x", r)
    assert ev.status == EVIDENCE_MISSING


def test_unknown_action_is_not_evaluated() -> None:
    r = _result()
    ev = evidence_for_action_id("totally_unknown_action", "x", r)
    assert ev.status == EVIDENCE_NOT_EVALUATED


def test_evidence_aware_upgrade_block_on_high_priority_fail() -> None:
    actions = [RequiredAction(id="ci_fetch_depth_zero", title="x", priority="high")]
    out, _ = compute_evidence_status(_result(signals=Signals(git_error="bad"), actions=actions))
    rec = evidence_aware_upgrade("warn", out, actions)
    assert rec == "block"


def test_evidence_aware_upgrade_warn_on_high_priority_missing() -> None:
    actions = [RequiredAction(id="auth_e2e_gate", title="x", priority="high")]
    out, _ = compute_evidence_status(_result(actions=actions))
    rec = evidence_aware_upgrade("pass", out, actions)
    assert rec == "warn"


def test_evidence_status_icon_mapping() -> None:
    assert evidence_status_icon(EVIDENCE_PASS) == "✅"
    assert evidence_status_icon(EVIDENCE_MISSING) == "⚠️"
    assert evidence_status_icon(EVIDENCE_FAIL) == "❌"
    assert evidence_status_icon(EVIDENCE_NOT_EVALUATED) == "📋"
    assert evidence_status_icon(EVIDENCE_UNKNOWN) == "❓"


def test_evidence_blocking_reasons_includes_fail_for_any_priority() -> None:
    actions = [RequiredAction(id="ci_fetch_depth_zero", title="x", priority="high")]
    evidence, _ = compute_evidence_status(_result(signals=Signals(git_error="bad"), actions=actions))
    out = evidence_blocking_reasons(evidence, actions)
    assert any("Evidence FAIL" in s for s in out)
