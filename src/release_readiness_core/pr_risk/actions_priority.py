"""Action priority constants and sort (port of actions_priority.go)."""

from __future__ import annotations

from typing import List

from release_readiness_core.pr_risk.types import RequiredAction


PRIORITY_HIGH = "high"
PRIORITY_MEDIUM = "medium"
PRIORITY_SUPPORTING = "supporting"


_HIGH = {
    "ci_fetch_depth_zero",
    "auth_e2e_gate",
    "rag_qna_citations_gate",
    "migrations_validation_gate",
    "add_tests_or_evidence",
}
_MEDIUM = {
    "workflow_config_validation",
    "materials_processing_gate",
    "context_align_pr_description",
}
_SUPPORTING = {
    "pr_review_summary",
    "context_scattered_review_plan",
    "context_improve_test_proximity",
    "context_hotspot_regression_focus",
}


def priority_for_action_id(action_id: str) -> str:
    """Map action ID to priority tier (signal-derived defaults)."""
    if action_id in _HIGH:
        return PRIORITY_HIGH
    if action_id in _MEDIUM:
        return PRIORITY_MEDIUM
    if action_id in _SUPPORTING:
        return PRIORITY_SUPPORTING
    return PRIORITY_MEDIUM


_RANK = {PRIORITY_HIGH: 0, PRIORITY_MEDIUM: 1, PRIORITY_SUPPORTING: 2}


def sort_required_actions(actions: List[RequiredAction]) -> List[RequiredAction]:
    """Order actions high → medium → supporting, then by ID. Stable sort."""
    if len(actions) <= 1:
        return list(actions)

    def key(a: RequiredAction):
        prio = a.priority or priority_for_action_id(a.id)
        return (_RANK.get(prio, 2), a.id)

    return sorted(actions, key=key)
