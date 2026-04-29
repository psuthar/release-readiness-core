"""Markdown rendering for :class:`~release_readiness_core.readiness_engine.ReadinessResult`."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .readiness_engine import ReadinessResult


def _score_band(r: ReadinessResult) -> str:
    if r.score >= r.pass_threshold:
        return f"PASS range (>={r.pass_threshold:.0f})"
    if r.score >= r.warn_threshold:
        return f"WARN range ({r.warn_threshold:.0f}-{r.pass_threshold:.0f})"
    return f"BLOCK range (<{r.warn_threshold:.0f})"


def _outcome_rationale(r: ReadinessResult) -> str:
    if r.outcome == "BLOCK":
        if r.blockers:
            n = len(r.blockers)
            label = r.blockers[0] if n == 1 else f"{n} hard blockers"
            return f"Blocked by hard blocker(s): {label}"
        return (
            f"Score {r.score:.1f} < {r.warn_threshold:.0f} (warn threshold) - "
            "insufficient evidence to reach minimum bar"
        )
    if r.outcome == "PASS":
        return f"Score {r.score:.1f} >= {r.pass_threshold:.0f} (pass threshold) with no warnings"
    if r.score >= r.pass_threshold and r.warnings:
        return (
            f"Score {r.score:.1f} is in PASS range (>={r.pass_threshold:.0f}), "
            f"but {len(r.warnings)} warning(s) suppress promotion to PASS"
        )
    return (
        f"Score {r.score:.1f} is below PASS threshold ({r.pass_threshold:.0f}) - "
        "no blockers but review required before deploy"
    )


def render_readiness_result_markdown(r: ReadinessResult, config_version: Any, title: str | None = None) -> str:
    """Human-readable report for CI logs and ``report.md``."""
    heading = title or "Release readiness report"
    lines = [
        f"# {heading}",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        f"**Config version:** {config_version}",
        "",
        f"## Result: **{r.outcome}** (score {r.score:.1f})",
        "",
        "### Outcome determination",
        "",
        "| Factor | Value |",
        "|--------|-------|",
        f"| Score | **{r.score:.1f} / {r.max_score:.0f}** |",
        f"| Score band | {_score_band(r)} |",
        f"| Blockers | {len(r.blockers)} |",
        f"| Warnings | {len(r.warnings)} |",
        f"| **Final outcome** | **{r.outcome}** |",
    ]
    if r.outcome_overrides:
        lines.append(f"| Outcome override | {r.outcome_overrides[0]} |")
    # SCRUM-209 (gap #5): only show the row when a note is present, since
    # adopters who don't use the validation-note convention have no idea what
    # it is and "no" produces a visible-but-meaningless row.
    note_present = r.evidence.get("validation_note_present", False)
    note_source = r.evidence.get("validation_note_source", "none")
    if note_present:
        lines.append(f"| Validation note | yes ({note_source}) |")
    lines.extend(
        [
            "",
            f"**Why:** {_outcome_rationale(r)}",
        ]
    )
    if r.blockers:
        lines.extend(["", "### Blockers", ""])
        for b in r.blockers:
            lines.append(f"- {b}")
    if r.warnings:
        lines.extend(["", "### Warnings", ""])
        for w in r.warnings:
            lines.append(f"- {w}")
    lines.extend(["", "### Summary", ""])
    for x in r.reasons:
        lines.append(f"- {x}")
    lines.extend(["", "### Risks from changed paths", ""])
    if r.risks_triggered:
        for x in r.risks_triggered:
            lines.append(f"- `{x}`")
    else:
        lines.append("- (none)")
    # SCRUM-209 (gap #4): omit the section entirely when there are no
    # validations to show, instead of rendering an empty markdown table.
    if r.validations:
        lines.extend(["", "### Validations", ""])
        lines.append("| Key | Status |")
        lines.append("|-----|--------|")
        for k, status in sorted(r.validations.items()):
            req_marker = " *(required)*" if k in r.validations_required else ""
            lines.append(f"| {k} | {status}{req_marker} |")
    if r.failed_checks:
        lines.extend(["", "### Failed checks", ""])
        for f in r.failed_checks:
            lines.append(f"- `{f}`")
    if r.recommended_actions:
        lines.extend(["", "### Recommended actions", ""])
        for a in r.recommended_actions:
            lines.append(f"- {a}")
    if r.remediation_items:
        lines.extend(["", "### Remediation guidance", ""])
        lines.append("| Check | Severity | Likely cause | Recommended action | Fix type |")
        lines.append("|-------|----------|--------------|--------------------|----------|")
        for item in r.remediation_items:
            sev = item.get("severity", "").upper()
            check = item.get("check", "")
            cause = item.get("likely_cause", "")
            action = item.get("recommended_action", "")
            fix_type = item.get("fix_type", "")
            lines.append(f"| `{check}` | {sev} | {cause} | {action} | {fix_type} |")
    lines.extend(["", "---", "*Deterministic scoring only (no LLM in the decision path).*", ""])
    return "\n".join(lines)
