"""Required validation lines (port of validations.go)."""

from __future__ import annotations

from typing import List, Optional, Tuple

from release_readiness_core.pr_risk.types import RequiredAction, Signals


_VALIDATION_FOR_ACTION = {
    "ci_fetch_depth_zero": "ci: full git history available for diff (fetch-depth: 0 or equivalent)",
    "pr_review_summary": "process: PR description with scoped, evidence-backed review plan",
    "workflow_config_validation": "config: workflow / deploy / go.mod changes validated against required checks",
    "auth_e2e_gate": "test: auth/session/invite flows exercised (E2E or equivalent evidence)",
    "rag_qna_citations_gate": "test: Q&A with citations validated for RAG-affecting changes",
    "materials_processing_gate": "test: materials upload + processing smoke for pipeline changes",
    "migrations_validation_gate": "db: migrations validated with rollback/reversal plan documented",
    "add_tests_or_evidence": "test: tests or recorded evidence for sensitive paths",
    "context_align_pr_description": "process: PR title/body aligned with actual diff (intent match)",
    "context_scattered_review_plan": "process: structured review map for scattered multi-area change",
    "context_improve_test_proximity": "test: tests co-located or explicitly linked for changed code",
    "context_hotspot_regression_focus": (
        "test: targeted regression for path prefixes with several recent commits "
        "overlapping this diff"
    ),
}


def validation_for_action(action_id: str) -> Optional[str]:
    return _VALIDATION_FOR_ACTION.get(action_id)


def compute_required_validations(s: Signals, actions: List[RequiredAction]) -> List[str]:
    """Build the deterministic ordered list of validation lines."""
    seen: set = set()
    out: List[str] = []

    def add(line: str) -> None:
        line = line.strip()
        if line == "":
            return
        if line in seen:
            return
        seen.add(line)
        out.append(line)

    if s.git_error == "":
        add("ci: required status checks must pass before merge")
    else:
        add("ci: restore reliable git diff before merge (see git error in report)")

    for a in actions:
        v = validation_for_action(a.id)
        if v:
            add(v)

    if s.validation_note_found:
        add("process: validation note present in commit — confirm it matches what was run")

    return out
