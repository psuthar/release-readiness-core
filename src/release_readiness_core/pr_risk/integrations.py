"""PR-comment markdown + Jira hook (port of integrations.go)."""

from __future__ import annotations

from io import StringIO
from typing import List

from release_readiness_core.pr_risk.types import (
    Enforcement,
    Integrations,
    RequiredAction,
    RiskFactor,
    ScoreMath,
)
from release_readiness_core.pr_risk.version import report_version_string


ENV_JIRA_ISSUE_KEY = "PRRISK_JIRA_ISSUE_KEY"


def _display_rec(rec: str) -> str:
    if rec == "pass":
        return "PASS (low risk)"
    if rec == "warn":
        return "WARN"
    if rec == "block":
        return "BLOCK"
    return rec.upper()


def _polish_required_validation_line(line: str) -> str:
    """Currently a passthrough. Reserved for future polish (Go has same shape)."""
    return line


def _band(score_value: float) -> str:
    """Local copy of score.band to avoid circular import."""
    if score_value < 20:
        return "low"
    if score_value < 45:
        return "medium"
    if score_value < 70:
        return "high"
    return "critical"


def build_integrations(
    factors: List[RiskFactor],
    score_value: float,
    base_ref: str,
    jira_key: str,
    actions: List[RequiredAction],
    score_math: ScoreMath,
    enf: Enforcement,
) -> Integrations:
    """Build PR comment markdown + optional Jira link.

    Mirrors Go BuildIntegrations exactly, including %.1f / %.0f formatting,
    the 2-of-N truncation pattern, and conditional sections.
    """
    md = StringIO()
    md.write(f"## PR Risk ({report_version_string()})\n\n")
    md.write(f"**Score:** {score_value:.1f}/100 ({_band(score_value)}) · base `{base_ref}`\n\n")

    rec = _display_rec(enf.merge_recommendation)
    md.write(f"**PR risk assessment:** **{rec}**")
    if enf.rationale != "":
        md.write(f" — {enf.rationale}")
    md.write("\n\n")
    md.write(
        "_This is a PR-risk score. Normal merge prerequisites (CI, code review, targeted "
        "testing) still apply regardless of this assessment._\n\n"
    )

    es = enf.evidence_summary
    if es.pass_count + es.missing_count + es.fail_count + es.not_evaluated_count > 0:
        md.write(
            f"**Evidence:** {es.pass_count} pass · {es.missing_count} missing · "
            f"{es.fail_count} fail · {es.not_evaluated_count} not evaluated\n\n"
        )

    if factors:
        md.write("**Top risk drivers:**\n")
        max_f = min(2, len(factors))
        for i in range(max_f):
            f = factors[i]
            if f.detail != "":
                md.write(f"- {f.label} ({f.points:.0f} pts): {f.detail}\n")
            else:
                md.write(f"- {f.label} ({f.points:.0f} pts)\n")
        if len(factors) > max_f:
            md.write(f"_…and {len(factors) - max_f} more in `pr_risk.md`_\n")
        md.write("\n")

    if enf.required_validations:
        md.write("**Top required validations:**\n")
        max_v = min(2, len(enf.required_validations))
        for i in range(max_v):
            md.write(f"{i + 1}. {_polish_required_validation_line(enf.required_validations[i])}\n")
        if len(enf.required_validations) > max_v:
            md.write(f"_…and {len(enf.required_validations) - max_v} more in `pr_risk.md`_\n")
        md.write("\n")

    rh = enf.recommended_review.routing_hints
    if rh:
        md.write("**Review routing:**\n")
        max_h = min(2, len(rh))
        for i in range(max_h):
            md.write(f"- {rh[i]}\n")
        if len(rh) > max_h:
            md.write(f"_…and {len(rh) - max_h} more in `pr_risk.md`_\n")
        md.write("\n")

    if score_math.factors_subtotal > 0 or score_math.reducers_subtotal > 0 or score_math.floor_min_score > 0:
        md.write(
            f"**Score math:** factors {score_math.factors_subtotal:.1f} − "
            f"reducers {score_math.reducers_subtotal:.1f} → {score_math.final_score:.1f}"
        )
        if score_math.floor_applied:
            md.write(f" (floor {score_math.floor_min_score:.0f} applied)")
        md.write(f" · {score_math.final_band}\n\n")

    if jira_key != "":
        md.write(f"**Tracked:** {jira_key}\n\n")

    md.write("_Full checklist and analysis in artifact `pr_risk.md`._\n")

    return Integrations(jira_issue_key=jira_key, pr_comment_markdown=md.getvalue())
