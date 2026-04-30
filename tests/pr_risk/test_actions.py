"""Unit tests for pr_risk.actions and pr_risk.actions_priority."""

import pytest

from release_readiness_core.pr_risk.actions import compute_required_actions
from release_readiness_core.pr_risk.actions_priority import (
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_SUPPORTING,
    priority_for_action_id,
    sort_required_actions,
)
from release_readiness_core.pr_risk.types import RequiredAction, RiskFactor, Signals


def _fac(id_: str) -> RiskFactor:
    return RiskFactor(id=id_, label=id_, points=10.0)


@pytest.mark.parametrize(
    "action_id,expected",
    [
        ("ci_fetch_depth_zero", PRIORITY_HIGH),
        ("auth_e2e_gate", PRIORITY_HIGH),
        ("rag_qna_citations_gate", PRIORITY_HIGH),
        ("migrations_validation_gate", PRIORITY_HIGH),
        ("add_tests_or_evidence", PRIORITY_HIGH),
        ("workflow_config_validation", PRIORITY_MEDIUM),
        ("materials_processing_gate", PRIORITY_MEDIUM),
        ("context_align_pr_description", PRIORITY_MEDIUM),
        ("pr_review_summary", PRIORITY_SUPPORTING),
        ("context_scattered_review_plan", PRIORITY_SUPPORTING),
        ("context_improve_test_proximity", PRIORITY_SUPPORTING),
        ("context_hotspot_regression_focus", PRIORITY_SUPPORTING),
        ("brand_new_action", PRIORITY_MEDIUM),  # default
    ],
)
def test_priority_for_action_id(action_id: str, expected: str) -> None:
    assert priority_for_action_id(action_id) == expected


def test_sort_required_actions_orders_high_first() -> None:
    actions = [
        RequiredAction(id="pr_review_summary", title="z"),
        RequiredAction(id="auth_e2e_gate", title="z"),
        RequiredAction(id="workflow_config_validation", title="z"),
    ]
    sorted_ = sort_required_actions(actions)
    assert [a.id for a in sorted_] == [
        "auth_e2e_gate",
        "workflow_config_validation",
        "pr_review_summary",
    ]


def test_sort_required_actions_alphabetic_within_priority() -> None:
    actions = [
        RequiredAction(id="auth_e2e_gate", title="z"),
        RequiredAction(id="add_tests_or_evidence", title="z"),
    ]
    out = sort_required_actions(actions)
    # Both high priority → alphabetic.
    assert [a.id for a in out] == ["add_tests_or_evidence", "auth_e2e_gate"]


def test_compute_required_actions_emits_ci_fetch_depth_when_git_unavailable() -> None:
    s = Signals(git_error="bad ref")
    factors = [_fac("git_unavailable")]
    out = compute_required_actions(s, factors, [], 30, "medium", None)
    assert any(a.id == "ci_fetch_depth_zero" for a in out)


def test_compute_required_actions_emits_auth_gate_for_high_band() -> None:
    s = Signals(domain_hits={"auth": 1})
    factors = [_fac("domain_auth")]
    out = compute_required_actions(s, factors, [], 60, "high", None)
    assert any(a.id == "auth_e2e_gate" for a in out)


def test_compute_required_actions_no_auth_gate_for_medium_band() -> None:
    """Medium band doesn't trigger sensitive-domain gates (only critical/high)."""
    s = Signals(domain_hits={"auth": 1})
    factors = [_fac("domain_auth")]
    out = compute_required_actions(s, factors, [], 30, "medium", None)
    assert not any(a.id == "auth_e2e_gate" for a in out)


def test_compute_required_actions_emits_pr_review_summary_for_diff_size() -> None:
    s = Signals()
    factors = [_fac("diff_large")]
    out = compute_required_actions(s, factors, [], 30, "medium", None)
    assert any(a.id == "pr_review_summary" for a in out)


def test_compute_required_actions_dedupes_add_tests_or_evidence() -> None:
    """Both gate paths can add this action; dedup keeps it once."""
    s = Signals(domain_hits={"auth": 1})
    factors = [_fac("domain_auth"), _fac("tests_missing")]
    out = compute_required_actions(s, factors, [], 60, "high", None)
    matches = [a for a in out if a.id == "add_tests_or_evidence"]
    assert len(matches) == 1
