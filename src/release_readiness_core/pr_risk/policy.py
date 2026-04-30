"""Merge recommendation policy (port of internal/prrisk/policy.go).

The Go ComputeEnforcement aggregates required validations, routing hints,
and evidence status — all of which depend on Phase 4 functions
(ComputeRequiredValidations, ComputeRoutingHints, ComputeEvidenceStatus).

Phase 3 (SCRUM-235) ports the parts that don't need Phase 4: the merge
recommendation, rationale, review strategy / requirements, blocking-reason
helpers, policy-trace reasons. Phase 4 (SCRUM-236) will replace
``compute_enforcement`` with the full evidence-aware version.
"""

from __future__ import annotations

from typing import List

from release_readiness_core.pr_risk._internal import factor_ids, ok_bool
from release_readiness_core.pr_risk._round import round_half_away
from release_readiness_core.pr_risk.evidence import (
    compute_evidence_status,
    evidence_aware_upgrade,
    evidence_blocking_reasons,
)
from release_readiness_core.pr_risk.reducers import reducer_ids
from release_readiness_core.pr_risk.routing import compute_routing_hints
from release_readiness_core.pr_risk.types import (
    Enforcement,
    RecommendedReview,
    Result,
)
from release_readiness_core.pr_risk.validations import compute_required_validations


def _fmt0(x: float) -> str:
    """Format like Go fmt.Sprintf('%.0f', x)."""
    return str(int(round_half_away(x)))


def merge_recommendation(r: Result) -> str:
    """Return 'pass' | 'warn' | 'block' for the result. Mirrors Go mergeRecommendation."""
    if r.signals.git_error != "":
        return "block"
    band = r.risk_band
    if band == "critical":
        return "block"
    if band == "high":
        return "block"
    if band == "medium":
        return "warn"
    if band == "low":
        if ok_bool(factor_ids(r.factors), "tests_missing"):
            # Style-only frontend changes explicitly waive the tests_missing gate.
            if not ok_bool(reducer_ids(r.reducers), "style_only_note"):
                return "warn"
        return "pass"
    return "warn"


def merge_rationale(r: Result, rec: str) -> str:
    if r.signals.git_error != "":
        return (
            "Git diff could not be computed; merge risk is unknown until "
            "CI checkout/history is fixed."
        )
    if rec == "block":
        return (
            f"Risk band is {r.risk_band} (score {_fmt0(r.risk_score)}/100); "
            "treat as merge-blocked until required actions and validations are satisfied."
        )
    if rec == "warn":
        return (
            f"Risk band is {r.risk_band} (score {_fmt0(r.risk_score)}/100); "
            "merge only after completing checklist items and review."
        )
    return (
        f"PR risk is low (score {_fmt0(r.risk_score)}/100). Normal prerequisites — "
        "CI checks, required reviews, and any targeted testing — still apply before merging."
    )


def review_strategy_for(rec: str, band: str) -> str:
    if rec == "block":
        return (
            "Do not merge until required validations pass and reviewers confirm "
            "mitigation of listed risks. Re-run prrisk after substantive changes."
        )
    if rec == "warn":
        if band == "medium":
            return (
                "Use a checklist-driven review: walk factors and required actions, "
                "then approve when evidence matches."
            )
        return (
            "Complete the required actions and validations below, then proceed "
            "with normal approval."
        )
    return "Single-pass review is enough; spot-check touched paths if helpful."


def review_requirements(rec: str, band: str, score: float) -> List[str]:
    seen: set = set()
    out: List[str] = []

    def add(s: str) -> None:
        s = s.strip()
        if s == "":
            return
        if s in seen:
            return
        seen.add(s)
        out.append(s)

    add("At least one approving review on the changed code.")
    if rec == "block":
        add(
            "Explicit sign-off that required actions and validations are complete before merge."
        )
    if band == "high" or band == "critical":
        add(
            "Prefer a reviewer familiar with the touched subsystems "
            "(see recommended_review.routing_hints)."
        )
    if score >= 45 and rec != "pass":
        add("Confirm CI is green for all required checks tied to this branch.")
    return out


def compute_blocking_reasons(r: Result, rec: str) -> List[str]:
    out: List[str] = []
    if r.signals.git_error != "":
        out.append("Git diff unavailable — change scope cannot be verified from history.")
    if rec == "block" and r.signals.git_error == "":
        out.append(
            f'Merge-block policy: risk band "{r.risk_band}" (score {_fmt0(r.risk_score)}) '
            "requires completing high-priority actions before merge."
        )
    elif rec == "warn":
        out.append(
            f'Elevated review: risk band "{r.risk_band}" — complete listed validations before merge.'
        )
    if r.score_math.floor_applied and len(r.score_math.floor_reasons) > 0:
        out.append("Risk floor applied so trust-critical changes are not masked by reducers.")
    return dedupe_strings(out)


def compute_policy_reasons(r: Result, rec: str) -> List[str]:
    out: List[str] = [
        "Deterministic policy: merge recommendation derives from risk band, "
        "git availability, and tests_missing in low band."
    ]
    if rec == "block" or rec == "warn":
        out.append(
            "Required validations are distinct from mitigations: validations are "
            "merge gates; mitigations are factor-specific guidance."
        )
    if len(r.required_actions) > 0:
        out.append(
            "Required actions prioritized as high / medium / supporting by action ID and risk class."
        )
    if (
        r.context_insights is not None
        and r.context_insights.intent.intent_strength == "weak"
    ):
        out.append(
            "PR title/body treated as weak intent — alignment scoring was limited."
        )
    return dedupe_strings(out)


def dedupe_strings(ss: List[str]) -> List[str]:
    seen: set = set()
    out: List[str] = []
    for s in ss:
        s = s.strip()
        if s == "":
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def compute_enforcement(r: Result) -> Enforcement:
    """Full evidence-aware enforcement (Phase 4 — mirrors Go ComputeEnforcement)."""
    validations = compute_required_validations(r.signals, r.required_actions)
    hints = compute_routing_hints(r.signals, r.factors, r.context_insights)

    evidence_status, evidence_summary = compute_evidence_status(r)

    rec = merge_recommendation(r)
    rec = evidence_aware_upgrade(rec, evidence_status, r.required_actions)

    strategy = review_strategy_for(rec, r.risk_band)
    reqs = review_requirements(rec, r.risk_band, r.risk_score)
    blocking = compute_blocking_reasons(r, rec)
    if rec != "pass":
        blocking = dedupe_strings(
            blocking + evidence_blocking_reasons(evidence_status, r.required_actions)
        )
    else:
        blocking = dedupe_strings(blocking)
    reasons = compute_policy_reasons(r, rec)

    return Enforcement(
        merge_recommendation=rec,
        rationale=merge_rationale(r, rec),
        recommended_review=RecommendedReview(strategy=strategy, routing_hints=hints),
        required_validations=validations,
        review_requirements=reqs,
        blocking_reasons=blocking,
        reasons=reasons,
        evidence_status=evidence_status,
        evidence_summary=evidence_summary,
    )
