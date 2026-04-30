"""Closed-set evidence detector templates.

Each gate's ``evidence: { template, args }`` block is compiled into a callable
of shape ``(action_id, label, result) -> ValidationEvidence`` by the template
functions in this module. The templates are the public contract of evidence
detection: adding a new template is a minor-version change; removing or
changing one is not.

The wording produced by each template mirrors the wording of the previous
hardcoded ``_ev_*`` helpers in ``evidence.py`` so the captured-fixture corpus
parity tests (``test_parity_full.py``: 81/81) hold byte-for-byte.

Adopters with custom detector logic that doesn't fit the closed set use
``PRRiskRuntime.register_detector(template_name, fn)`` to plug in a callable
of the same shape; the gate's ``evidence.template`` references the template
name and the runtime resolves the callable at compile time.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, TYPE_CHECKING

from release_readiness_core.pr_risk._round import round_half_away
from release_readiness_core.pr_risk.types import (
    EVIDENCE_FAIL,
    EVIDENCE_MISSING,
    EVIDENCE_NOT_EVALUATED,
    EVIDENCE_PASS,
    EVIDENCE_UNKNOWN,
    Result,
    Signals,
    ValidationEvidence,
)

if TYPE_CHECKING:
    from release_readiness_core.pr_risk.context.types import ContextInsights


# ---------------------------------------------------------------------------
# Helpers (private to this module).

def _note_snippet(s: str) -> str:
    if s == "":
        return "(present)"
    if len(s) > 80:
        return s[:80] + "…"
    return s


# ---------------------------------------------------------------------------
# Template registry.
#
# Each template is invoked as ``template(action_id, label, args, result)`` and
# returns a ``ValidationEvidence``.

def template_signal_check(
    action_id: str, label: str, args: Dict[str, Any], r: Result
) -> ValidationEvidence:
    """Generic Signals-field check: FAIL when the named signal field is non-empty.

    ``args.signal_field`` selects the field. Wording today is git-error-specific
    (``signal_field: git_error``) for parity; if/when adopters point this at a
    different field, the rationale text generalizes via the field name.
    """
    field = args.get("signal_field", "")
    val = getattr(r.signals, field, "") if field else ""
    if val:
        rationale = (
            "Git error detected: " + str(val)
            if field == "git_error"
            else f"{field} signal present: {val}"
        )
        return ValidationEvidence(
            id=action_id,
            label=label,
            status=EVIDENCE_FAIL,
            source="git_signals",
            rationale=rationale,
        )
    rationale = (
        "No git error: diff range was computed successfully."
        if field == "git_error"
        else f"No {field} signal: check passed."
    )
    return ValidationEvidence(
        id=action_id,
        label=label,
        status=EVIDENCE_PASS,
        source="git_signals",
        rationale=rationale,
    )


def template_intent_strength(
    action_id: str, label: str, args: Dict[str, Any], r: Result
) -> ValidationEvidence:
    """PR-review-summary detector: maps intent strength to PASS / MISSING /
    NOT_EVALUATED with the original review-summary wording."""
    del args
    ci = r.context_insights
    if ci is None:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_UNKNOWN, source="intent",
            rationale="Context insights unavailable.",
        )
    strength = ci.intent.intent_strength
    if strength == "strong":
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_PASS, source="intent",
            rationale="PR title/body has strong keywords aligned with the diff.",
        )
    if strength == "weak":
        msg = "PR description does not adequately scope the change."
        if ci.intent.title == "":
            msg = (
                "PR description is absent or too short to qualify as an evidence-backed "
                "review plan."
            )
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_MISSING, source="intent",
            rationale=msg,
        )
    return ValidationEvidence(
        id=action_id, label=label, status=EVIDENCE_NOT_EVALUATED, source="intent",
        rationale=(
            "PR description quality could not be confirmed from available signals — "
            "requires human review."
        ),
    )


def template_validation_note(
    action_id: str, label: str, args: Dict[str, Any], r: Result
) -> ValidationEvidence:
    """Workflow / config validation: PASS when commit message includes a
    ``Validation:`` note; otherwise NOT_EVALUATED."""
    del args
    s = r.signals
    if s.validation_note_found:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_PASS, source="git_signals",
            rationale="Validation note found in commit: " + _note_snippet(s.validation_note_snippet),
        )
    return ValidationEvidence(
        id=action_id, label=label, status=EVIDENCE_NOT_EVALUATED, source="git_signals",
        rationale=(
            "No validation note in commit; CI result not confirmable from repo-local signals "
            "— requires human review."
        ),
    )


def template_test_domain(
    action_id: str, label: str, args: Dict[str, Any], r: Result
) -> ValidationEvidence:
    """Test-coverage check for a configured domain. ``args.domain`` selects."""
    domain = args.get("domain", "")
    s = r.signals
    if s.test_e2e_domain_hits.get(domain, 0) > 0:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_PASS, source="test_domain_hits",
            rationale=(
                f'E2E test files touching "{domain}" domain in this diff '
                f'({s.test_e2e_domain_hits.get(domain, 0)} file(s)).'
            ),
        )
    if s.test_unit_domain_hits.get(domain, 0) > 0:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_NOT_EVALUATED, source="test_domain_hits",
            rationale=(
                f'Unit test files touching "{domain}" domain in diff '
                f'({s.test_unit_domain_hits.get(domain, 0)} file(s)); E2E coverage not '
                f'confirmed — requires human review.'
            ),
        )
    return ValidationEvidence(
        id=action_id, label=label, status=EVIDENCE_MISSING, source="test_domain_hits",
        rationale=f'No test domain hits for "{domain}" in this diff.',
    )


def template_migrations(
    action_id: str, label: str, args: Dict[str, Any], r: Result
) -> ValidationEvidence:
    del args
    s = r.signals
    if s.test_e2e_domain_hits.get("migrations", 0) > 0:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_PASS, source="test_domain_hits",
            rationale="E2E test coverage for migrations domain detected in diff.",
        )
    if s.validation_note_found and s.migration_files > 0:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_PASS, source="git_signals",
            rationale="Validation note present alongside migration file changes: "
            + _note_snippet(s.validation_note_snippet),
        )
    if s.migration_files > 0:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_MISSING, source="git_signals",
            rationale=(
                f"{s.migration_files} migration file(s) changed; no validation note "
                f"or E2E coverage detected."
            ),
        )
    return ValidationEvidence(
        id=action_id, label=label, status=EVIDENCE_UNKNOWN, source="git_signals",
        rationale="No migration files detected; validation state unknown.",
    )


def template_add_tests(
    action_id: str, label: str, args: Dict[str, Any], r: Result
) -> ValidationEvidence:
    del args
    s = r.signals
    ci = r.context_insights
    if s.style_only_note_found:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_PASS, source="git_signals",
            rationale=(
                "Style-only commit note present: purely cosmetic frontend change, "
                "no test required."
            ),
        )
    if ci is not None and ci.proximity.behavioral_coverage == "adequate":
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_PASS, source="proximity",
            rationale=(
                "Behavioral coverage is adequate: E2E or non-sensitive domain with "
                "co-located tests."
            ),
        )
    if s.test_loc_ratio >= 0.30 and s.test_files > 0:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_PASS, source="test_loc_ratio",
            rationale=(
                f"Test LOC ratio is {int(round_half_away(s.test_loc_ratio * 100))}% (≥30%) "
                f"with {s.test_files} test file(s) in diff."
            ),
        )
    if s.test_files == 0:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_MISSING, source="test_loc_ratio",
            rationale="No test files in this diff.",
        )
    if ci is not None and ci.proximity.behavioral_coverage == "shallow":
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_NOT_EVALUATED, source="proximity",
            rationale=(
                "Behavioral coverage is shallow: unit tests present but E2E coverage for "
                "sensitive domains not confirmed — requires human review."
            ),
        )
    return ValidationEvidence(
        id=action_id, label=label, status=EVIDENCE_NOT_EVALUATED, source="test_loc_ratio",
        rationale=(
            f"Test files present ({s.test_files}) but coverage depth could not be confirmed — "
            f"requires human review."
        ),
    )


def template_intent_alignment(
    action_id: str, label: str, args: Dict[str, Any], r: Result
) -> ValidationEvidence:
    del args
    ci = r.context_insights
    if ci is None:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_UNKNOWN, source="intent",
            rationale="Context insights unavailable.",
        )
    if ci.intent.mismatch:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_FAIL, source="intent",
            rationale="PR title/body keywords imply domains not present in diff: " + ci.intent.detail,
        )
    if ci.intent.aligned:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_PASS, source="intent",
            rationale="PR description keywords are aligned with diff domains.",
        )
    return ValidationEvidence(
        id=action_id, label=label, status=EVIDENCE_NOT_EVALUATED, source="intent",
        rationale=(
            "Intent alignment could not be confirmed (no strong keywords matched) — "
            "requires human review."
        ),
    )


def template_intent_aligned_or_weak(
    action_id: str, label: str, args: Dict[str, Any], r: Result
) -> ValidationEvidence:
    del args
    ci = r.context_insights
    if ci is None:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_UNKNOWN, source="intent",
            rationale="Context insights unavailable.",
        )
    if ci.intent.intent_strength == "strong" and ci.intent.aligned:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_PASS, source="intent",
            rationale="Strong PR description present and aligned with scattered change domains.",
        )
    if ci.intent.intent_strength == "weak":
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_MISSING, source="intent",
            rationale="PR description is weak or generic for a scattered multi-area change.",
        )
    return ValidationEvidence(
        id=action_id, label=label, status=EVIDENCE_NOT_EVALUATED, source="intent",
        rationale=(
            "Review plan coverage of scattered change could not be confirmed from available "
            "signals — requires human review."
        ),
    )


def template_proximity(
    action_id: str, label: str, args: Dict[str, Any], r: Result
) -> ValidationEvidence:
    del args
    ci = r.context_insights
    if ci is None:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_UNKNOWN, source="proximity",
            rationale="Context insights unavailable.",
        )
    if ci.proximity.behavioral_coverage == "adequate":
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_PASS, source="proximity",
            rationale="Tests are co-located or behaviorally adequate for changed code.",
        )
    if ci.proximity.mode == "distant" and ci.proximity.behavioral_coverage == "unknown":
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_MISSING, source="proximity",
            rationale=(
                f'Structural alignment is "{ci.proximity.mode}" with no test coverage '
                f'evidence for this diff.'
            ),
        )
    return ValidationEvidence(
        id=action_id, label=label, status=EVIDENCE_NOT_EVALUATED, source="proximity",
        rationale=(
            f'Structural alignment is "{ci.proximity.mode}"; behavioral coverage is '
            f'"{ci.proximity.behavioral_coverage}" — requires human review.'
        ),
    )


def template_hotspot(
    action_id: str, label: str, args: Dict[str, Any], r: Result
) -> ValidationEvidence:
    del args
    s = r.signals
    if s.validation_note_found:
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_PASS, source="git_signals",
            rationale="Validation note present in commit: " + _note_snippet(s.validation_note_snippet),
        )
    return ValidationEvidence(
        id=action_id, label=label, status=EVIDENCE_NOT_EVALUATED, source="git_signals",
        rationale=(
            "No validation note detected; targeted regression coverage cannot be "
            "confirmed from diff alone — requires human review."
        ),
    )


# ---------------------------------------------------------------------------
# Public registry.

BUILTIN_TEMPLATES = {
    "signal_check": template_signal_check,
    "intent_strength": template_intent_strength,
    "validation_note": template_validation_note,
    "test_domain": template_test_domain,
    "migrations": template_migrations,
    "add_tests": template_add_tests,
    "intent_alignment": template_intent_alignment,
    "intent_aligned_or_weak": template_intent_aligned_or_weak,
    "proximity": template_proximity,
    "hotspot": template_hotspot,
}
