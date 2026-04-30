"""Evidence resolution (config-driven detectors).

Each required action has a deterministic evidence detector that classifies the
state as pass / missing / fail / not_evaluated / unknown using only repo-local
signals. No LLM, no live API.

Phase 4 replaced the hand-written ``_DETECTORS`` dict with a
closed-set template registry in ``_evidence_templates.py``. Each gate's
``evidence: { template, args }`` block compiles to a callable via
``runtime.detector_for(action_id)``. The CI-baseline detector
(``_ev_ci_baseline``) stays in this module — it isn't a per-gate detector;
it's a preface added to every evidence list regardless of gates.
"""

from __future__ import annotations

from typing import List, Tuple

from release_readiness_core.pr_risk.actions_priority import (
    PRIORITY_HIGH,
    priority_for_action_id,
)
from release_readiness_core.pr_risk.types import (
    EVIDENCE_FAIL,
    EVIDENCE_MISSING,
    EVIDENCE_NOT_EVALUATED,
    EVIDENCE_PASS,
    EvidenceSummary,
    RequiredAction,
    Result,
    Signals,
    ValidationEvidence,
)


def _ev_ci_baseline(s: Signals) -> ValidationEvidence:
    """CI baseline detector: prepended to every evidence list. Not config-driven —
    the CI-baseline check applies regardless of which gates fired."""
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


def evidence_for_action_id(id_: str, label: str, r: Result, *, runtime=None) -> ValidationEvidence:
    """Resolve the evidence detector for a gate id.

    Looks up the gate in ``runtime.config.gates``, compiles its
    ``evidence: { template, args }`` block via ``runtime.detector_for(id_)``,
    and invokes it. Falls back to a NOT_EVALUATED placeholder when the gate
    has no evidence binding (e.g. a custom gate added by an adopter without
    selecting a detector template).
    """
    runtime = runtime or _default_runtime()
    try:
        detector = runtime.detector_for(id_)
    except (KeyError, ValueError):
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


def compute_evidence_status(
    r: Result, *, runtime=None
) -> Tuple[List[ValidationEvidence], EvidenceSummary]:
    """Compute evidence status for every required action plus the CI baseline."""
    out: List[ValidationEvidence] = [_ev_ci_baseline(r.signals)]
    for a in r.required_actions:
        out.append(evidence_for_action_id(a.id, a.title, r, runtime=runtime))

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


def _default_runtime():
    from release_readiness_core.pr_risk.classify import _default_runtime as _rt

    return _rt()
