"""Evidence detectors (port of evidence.go).

Each required action has a deterministic evidence detector that classifies the
state as pass / missing / fail / not_evaluated / unknown using only repo-local
signals. No LLM, no live API.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from release_readiness_core.pr_risk.actions_priority import (
    PRIORITY_HIGH,
    priority_for_action_id,
)
from release_readiness_core.pr_risk.context.types import ContextInsights
from release_readiness_core.pr_risk.types import (
    DOMAIN_AUTH,
    DOMAIN_MIGRATIONS,
    DOMAIN_ORCHESTRATION,
    DOMAIN_PROCESSING,
    DOMAIN_RAG,
    EVIDENCE_FAIL,
    EVIDENCE_MISSING,
    EVIDENCE_NOT_EVALUATED,
    EVIDENCE_PASS,
    EVIDENCE_UNKNOWN,
    EvidenceSummary,
    RequiredAction,
    Result,
    Signals,
    ValidationEvidence,
)


def _note_snippet(s: str) -> str:
    if s == "":
        return "(present)"
    if len(s) > 80:
        return s[:80] + "…"
    return s


def _ev_ci_baseline(s: Signals) -> ValidationEvidence:
    if s.git_error != "":
        return ValidationEvidence(
            id="ci_baseline",
            label="CI: required status checks",
            status=EVIDENCE_FAIL,
            source="git_signals",
            rationale="Git diff unavailable: " + s.git_error,
        )
    return ValidationEvidence(
        id="ci_baseline",
        label="CI: required status checks",
        status=EVIDENCE_NOT_EVALUATED,
        source="git_signals",
        rationale=(
            "CI pass/fail cannot be confirmed from diff signals alone; "
            "requires human/pipeline review."
        ),
    )


def _ev_ci_fetch_depth(label: str, s: Signals) -> ValidationEvidence:
    if s.git_error != "":
        return ValidationEvidence(
            id="ci_fetch_depth_zero",
            label=label,
            status=EVIDENCE_FAIL,
            source="git_signals",
            rationale="Git error detected: " + s.git_error,
        )
    return ValidationEvidence(
        id="ci_fetch_depth_zero",
        label=label,
        status=EVIDENCE_PASS,
        source="git_signals",
        rationale="No git error: diff range was computed successfully.",
    )


def _ev_pr_review_summary(label: str, ci: Optional[ContextInsights]) -> ValidationEvidence:
    id_ = "pr_review_summary"
    if ci is None:
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_UNKNOWN,
            source="intent",
            rationale="Context insights unavailable.",
        )
    strength = ci.intent.intent_strength
    if strength == "strong":
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_PASS,
            source="intent",
            rationale="PR title/body has strong keywords aligned with the diff.",
        )
    if strength == "weak":
        msg = "PR description does not adequately scope the change."
        if ci.intent.title == "":
            msg = "PR description is absent or too short to qualify as an evidence-backed review plan."
        return ValidationEvidence(
            id=id_, label=label, status=EVIDENCE_MISSING, source="intent", rationale=msg
        )
    return ValidationEvidence(
        id=id_,
        label=label,
        status=EVIDENCE_NOT_EVALUATED,
        source="intent",
        rationale=(
            "PR description quality could not be confirmed from available signals — "
            "requires human review."
        ),
    )


def _ev_workflow_config(label: str, s: Signals) -> ValidationEvidence:
    id_ = "workflow_config_validation"
    if s.validation_note_found:
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_PASS,
            source="git_signals",
            rationale="Validation note found in commit: " + _note_snippet(s.validation_note_snippet),
        )
    return ValidationEvidence(
        id=id_,
        label=label,
        status=EVIDENCE_NOT_EVALUATED,
        source="git_signals",
        rationale=(
            "No validation note in commit; CI result not confirmable from repo-local signals "
            "— requires human review."
        ),
    )


def _ev_test_domain(id_: str, label: str, domain: str, s: Signals) -> ValidationEvidence:
    if s.test_e2e_domain_hits.get(domain, 0) > 0:
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_PASS,
            source="test_domain_hits",
            rationale=(
                f'E2E test files touching "{domain}" domain in this diff '
                f'({s.test_e2e_domain_hits.get(domain, 0)} file(s)).'
            ),
        )
    if s.test_unit_domain_hits.get(domain, 0) > 0:
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_NOT_EVALUATED,
            source="test_domain_hits",
            rationale=(
                f'Unit test files touching "{domain}" domain in diff '
                f'({s.test_unit_domain_hits.get(domain, 0)} file(s)); E2E coverage not '
                f'confirmed — requires human review.'
            ),
        )
    return ValidationEvidence(
        id=id_,
        label=label,
        status=EVIDENCE_MISSING,
        source="test_domain_hits",
        rationale=f'No test domain hits for "{domain}" in this diff.',
    )


def _ev_migrations(label: str, s: Signals) -> ValidationEvidence:
    id_ = "migrations_validation_gate"
    if s.test_e2e_domain_hits.get(DOMAIN_MIGRATIONS, 0) > 0:
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_PASS,
            source="test_domain_hits",
            rationale="E2E test coverage for migrations domain detected in diff.",
        )
    if s.validation_note_found and s.migration_files > 0:
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_PASS,
            source="git_signals",
            rationale="Validation note present alongside migration file changes: "
            + _note_snippet(s.validation_note_snippet),
        )
    if s.migration_files > 0:
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_MISSING,
            source="git_signals",
            rationale=(
                f"{s.migration_files} migration file(s) changed; no validation note "
                f"or E2E coverage detected."
            ),
        )
    return ValidationEvidence(
        id=id_,
        label=label,
        status=EVIDENCE_UNKNOWN,
        source="git_signals",
        rationale="No migration files detected; validation state unknown.",
    )


def _ev_add_tests(label: str, s: Signals, ci: Optional[ContextInsights]) -> ValidationEvidence:
    id_ = "add_tests_or_evidence"
    if s.style_only_note_found:
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_PASS,
            source="git_signals",
            rationale="Style-only commit note present: purely cosmetic frontend change, no test required.",
        )
    if ci is not None and ci.proximity.behavioral_coverage == "adequate":
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_PASS,
            source="proximity",
            rationale="Behavioral coverage is adequate: E2E or non-sensitive domain with co-located tests.",
        )
    if s.test_loc_ratio >= 0.30 and s.test_files > 0:
        from release_readiness_core.pr_risk._round import round_half_away

        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_PASS,
            source="test_loc_ratio",
            rationale=(
                f"Test LOC ratio is {int(round_half_away(s.test_loc_ratio * 100))}% (≥30%) "
                f"with {s.test_files} test file(s) in diff."
            ),
        )
    if s.test_files == 0:
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_MISSING,
            source="test_loc_ratio",
            rationale="No test files in this diff.",
        )
    if ci is not None and ci.proximity.behavioral_coverage == "shallow":
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_NOT_EVALUATED,
            source="proximity",
            rationale=(
                "Behavioral coverage is shallow: unit tests present but E2E coverage for "
                "sensitive domains not confirmed — requires human review."
            ),
        )
    return ValidationEvidence(
        id=id_,
        label=label,
        status=EVIDENCE_NOT_EVALUATED,
        source="test_loc_ratio",
        rationale=(
            f"Test files present ({s.test_files}) but coverage depth could not be confirmed — "
            f"requires human review."
        ),
    )


def _ev_intent_alignment(label: str, ci: Optional[ContextInsights]) -> ValidationEvidence:
    id_ = "context_align_pr_description"
    if ci is None:
        return ValidationEvidence(
            id=id_, label=label, status=EVIDENCE_UNKNOWN, source="intent",
            rationale="Context insights unavailable.",
        )
    if ci.intent.mismatch:
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_FAIL,
            source="intent",
            rationale="PR title/body keywords imply domains not present in diff: " + ci.intent.detail,
        )
    if ci.intent.aligned:
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_PASS,
            source="intent",
            rationale="PR description keywords are aligned with diff domains.",
        )
    return ValidationEvidence(
        id=id_,
        label=label,
        status=EVIDENCE_NOT_EVALUATED,
        source="intent",
        rationale=(
            "Intent alignment could not be confirmed (no strong keywords matched) — "
            "requires human review."
        ),
    )


def _ev_scattered_review_plan(label: str, ci: Optional[ContextInsights]) -> ValidationEvidence:
    id_ = "context_scattered_review_plan"
    if ci is None:
        return ValidationEvidence(
            id=id_, label=label, status=EVIDENCE_UNKNOWN, source="intent",
            rationale="Context insights unavailable.",
        )
    if ci.intent.intent_strength == "strong" and ci.intent.aligned:
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_PASS,
            source="intent",
            rationale="Strong PR description present and aligned with scattered change domains.",
        )
    if ci.intent.intent_strength == "weak":
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_MISSING,
            source="intent",
            rationale="PR description is weak or generic for a scattered multi-area change.",
        )
    return ValidationEvidence(
        id=id_,
        label=label,
        status=EVIDENCE_NOT_EVALUATED,
        source="intent",
        rationale=(
            "Review plan coverage of scattered change could not be confirmed from available "
            "signals — requires human review."
        ),
    )


def _ev_test_proximity(label: str, ci: Optional[ContextInsights]) -> ValidationEvidence:
    id_ = "context_improve_test_proximity"
    if ci is None:
        return ValidationEvidence(
            id=id_, label=label, status=EVIDENCE_UNKNOWN, source="proximity",
            rationale="Context insights unavailable.",
        )
    if ci.proximity.behavioral_coverage == "adequate":
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_PASS,
            source="proximity",
            rationale="Tests are co-located or behaviorally adequate for changed code.",
        )
    if ci.proximity.mode == "distant" and ci.proximity.behavioral_coverage == "unknown":
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_MISSING,
            source="proximity",
            rationale=(
                f'Structural alignment is "{ci.proximity.mode}" with no test coverage '
                f'evidence for this diff.'
            ),
        )
    return ValidationEvidence(
        id=id_,
        label=label,
        status=EVIDENCE_NOT_EVALUATED,
        source="proximity",
        rationale=(
            f'Structural alignment is "{ci.proximity.mode}"; behavioral coverage is '
            f'"{ci.proximity.behavioral_coverage}" — requires human review.'
        ),
    )


def _ev_hotspot_regression(label: str, s: Signals) -> ValidationEvidence:
    id_ = "context_hotspot_regression_focus"
    if s.validation_note_found:
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_PASS,
            source="git_signals",
            rationale="Validation note present in commit: " + _note_snippet(s.validation_note_snippet),
        )
    return ValidationEvidence(
        id=id_,
        label=label,
        status=EVIDENCE_NOT_EVALUATED,
        source="git_signals",
        rationale=(
            "No validation note detected; targeted regression coverage cannot be "
            "confirmed from diff alone — requires human review."
        ),
    )


_DETECTORS = {
    "ci_fetch_depth_zero": lambda lbl, r: _ev_ci_fetch_depth(lbl, r.signals),
    "pr_review_summary": lambda lbl, r: _ev_pr_review_summary(lbl, r.context_insights),
    "workflow_config_validation": lambda lbl, r: _ev_workflow_config(lbl, r.signals),
    "auth_e2e_gate": lambda lbl, r: _ev_test_domain("auth_e2e_gate", lbl, DOMAIN_AUTH, r.signals),
    "rag_qna_citations_gate": lambda lbl, r: _ev_test_domain("rag_qna_citations_gate", lbl, DOMAIN_RAG, r.signals),
    "materials_processing_gate": lambda lbl, r: _ev_test_domain("materials_processing_gate", lbl, DOMAIN_PROCESSING, r.signals),
    "orchestration_creator_gate": lambda lbl, r: _ev_test_domain("orchestration_creator_gate", lbl, DOMAIN_ORCHESTRATION, r.signals),
    "migrations_validation_gate": lambda lbl, r: _ev_migrations(lbl, r.signals),
    "add_tests_or_evidence": lambda lbl, r: _ev_add_tests(lbl, r.signals, r.context_insights),
    "context_align_pr_description": lambda lbl, r: _ev_intent_alignment(lbl, r.context_insights),
    "context_scattered_review_plan": lambda lbl, r: _ev_scattered_review_plan(lbl, r.context_insights),
    "context_improve_test_proximity": lambda lbl, r: _ev_test_proximity(lbl, r.context_insights),
    "context_hotspot_regression_focus": lambda lbl, r: _ev_hotspot_regression(lbl, r.signals),
}


def evidence_for_action_id(id_: str, label: str, r: Result) -> ValidationEvidence:
    detector = _DETECTORS.get(id_)
    if detector is None:
        return ValidationEvidence(
            id=id_,
            label=label,
            status=EVIDENCE_NOT_EVALUATED,
            source="none",
            rationale=(
                "No repo-local evidence detector defined for this action; "
                "requires human review."
            ),
        )
    return detector(label, r)


def compute_evidence_status(r: Result) -> Tuple[List[ValidationEvidence], EvidenceSummary]:
    out: List[ValidationEvidence] = [_ev_ci_baseline(r.signals)]
    for a in r.required_actions:
        out.append(evidence_for_action_id(a.id, a.title, r))

    summary = EvidenceSummary()
    for e in out:
        if e.status == EVIDENCE_PASS:
            summary.pass_count += 1
        elif e.status == EVIDENCE_MISSING:
            summary.missing_count += 1
        elif e.status == EVIDENCE_FAIL:
            summary.fail_count += 1
        elif e.status == EVIDENCE_NOT_EVALUATED:
            summary.not_evaluated_count += 1
        else:
            summary.unknown_count += 1
    return out, summary


def evidence_aware_upgrade(
    rec: str, evidence: List[ValidationEvidence], actions: List[RequiredAction]
) -> str:
    """Upgrade a merge recommendation when high-priority evidence is fail/missing."""
    high_ids: set = set()
    for a in actions:
        prio = a.priority or priority_for_action_id(a.id)
        if prio == PRIORITY_HIGH:
            high_ids.add(a.id)
    for ev in evidence:
        if ev.id not in high_ids:
            continue
        if ev.status == EVIDENCE_FAIL and rec in ("pass", "warn"):
            return "block"
        if ev.status == EVIDENCE_MISSING and rec == "pass":
            return "warn"
    return rec


def evidence_blocking_reasons(
    evidence: List[ValidationEvidence], actions: List[RequiredAction]
) -> List[str]:
    """Subset of evidence entries that should appear in BlockingReasons."""
    high_ids: set = set()
    for a in actions:
        prio = a.priority or priority_for_action_id(a.id)
        if prio == PRIORITY_HIGH:
            high_ids.add(a.id)
    out: List[str] = []
    for ev in evidence:
        if ev.status == EVIDENCE_FAIL:
            out.append(f"Evidence FAIL [{ev.id}]: {ev.rationale}")
        elif ev.status == EVIDENCE_MISSING and ev.id in high_ids:
            out.append(f"Evidence MISSING [{ev.id}]: {ev.rationale}")
    return out


def evidence_status_icon(status: str) -> str:
    if status == EVIDENCE_PASS:
        return "✅"
    if status == EVIDENCE_MISSING:
        return "⚠️"
    if status == EVIDENCE_FAIL:
        return "❌"
    if status == EVIDENCE_NOT_EVALUATED:
        return "📋"
    return "❓"
