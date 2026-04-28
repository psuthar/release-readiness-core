"""Report rendering helpers."""

from __future__ import annotations

from .engine import ReadinessReport


def render_markdown_report(
    title: str,
    report: ReadinessReport,
    high_priority_hits: dict[str, str],
) -> str:
    """Render a markdown report with optional high-priority evidence section."""
    lines = [
        f"# {title}",
        "",
        f"- Overall status: **{report.status}**",
        f"- Passed: {report.passed}",
        f"- Warnings: {report.warnings}",
        f"- Blocked: {report.blocked}",
        "",
        "## Validations",
    ]
    for v in report.validations:
        detail_suffix = f" - {v.detail}" if v.detail else ""
        lines.append(f"- `{v.key}`: {v.status}{detail_suffix}")
    if high_priority_hits:
        lines.extend(["", "## High-priority PR-risk evidence"])
        for evidence_id in sorted(high_priority_hits):
            lines.append(f"- `{evidence_id}`: {high_priority_hits[evidence_id]}")
    return "\n".join(lines) + "\n"
