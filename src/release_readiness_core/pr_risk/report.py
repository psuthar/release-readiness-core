"""JSON + markdown writers for the PR Risk report (port of report.go).

write_json emits the full Result; write_markdown emits the human-readable
report. JSON parity is byte-stable except for the ``generated_at`` timestamp
(differs between runs by definition); markdown parity is whitespace-tolerant
per the SCRUM-231 decisions doc.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, is_dataclass
from datetime import datetime
from io import StringIO
from typing import Any, List

from release_readiness_core.pr_risk.evidence import evidence_status_icon
from release_readiness_core.pr_risk.types import (
    CATEGORY_TEST_CONFIDENCE,
    EVIDENCE_NOT_EVALUATED,
    EVIDENCE_UNKNOWN,
    Result,
)
from release_readiness_core.pr_risk.version import report_version_string


def _result_to_json_dict(r: Result) -> dict:
    """Convert Result to a JSON-serializable dict matching Go's struct tags.

    Python dataclasses with snake_case names already match Go's JSON output
    (Go uses snake_case in struct tags). Two known renames live in the context
    subpackage: concentration.unique_dirs -> 'unique_prefixes', and
    hotspot.recent_count -> 'recent_hits'.
    """
    d = asdict(r)
    # Apply field renames inside context_insights, if present.
    ci = d.get("context_insights") or None
    if ci is not None:
        conc = ci.get("concentration")
        if conc is not None and "unique_dirs" in conc:
            conc["unique_prefixes"] = conc.pop("unique_dirs")
        for h in ci.get("hotspots") or []:
            if "recent_count" in h:
                h["recent_hits"] = h.pop("recent_count")
    # generated_at is a datetime; serialize as RFC3339 UTC.
    if isinstance(d.get("generated_at"), datetime):
        d["generated_at"] = d["generated_at"].strftime("%Y-%m-%dT%H:%M:%SZ")
    return d


def write_json(path: str, r: Result) -> None:
    """Write Result to a JSON file with 2-space indent (matches Go MarshalIndent)."""
    os.makedirs(os.path.dirname(path), exist_ok=True) if os.path.dirname(path) else None
    payload = _result_to_json_dict(r)
    with open(path, "w") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False, default=str)


def _display_rec(rec: str) -> str:
    if rec == "pass":
        return "PASS (low risk)"
    if rec == "warn":
        return "WARN"
    if rec == "block":
        return "BLOCK"
    return rec.upper()


def write_markdown(path: str, r: Result) -> None:
    """Write the human-readable markdown report.

    Whitespace-tolerant per the SCRUM-231 decisions doc; the PR comment in
    integrations.py is the byte-stable surface that reviewers/CI consume.
    """
    sb = StringIO()
    sb.write(f"# PR Risk Report ({report_version_string()})\n\n")
    if r.generated_at is not None:
        sb.write(f"**Generated:** {r.generated_at.strftime('%Y-%m-%dT%H:%M:%SZ')}  \n")
    sb.write(f"**Base ref:** `{r.base_ref}`  \n\n")
    if r.interpretation:
        sb.write(f"> {r.interpretation}\n\n")

    sb.write("## Summary\n\n")
    sb.write("| Metric | Value |\n|--------|-------|\n")
    sb.write(f"| Risk score | **{r.risk_score:.1f}** / 100 |\n")
    sb.write(f"| Band | **{r.risk_band}** |\n")
    sb.write(f"| Report version | **{r.report_version}** |\n")
    for c in r.categories:
        if c.key == CATEGORY_TEST_CONFIDENCE:
            sb.write(f"| Test confidence | **{c.confidence:.0f}** / 100 |\n")
            break
    sb.write(f"| Files changed | {r.signals.file_count} |\n")
    sb.write(f"| LOC churn (add+del) | {r.signals.total_loc} |\n")
    sb.write(f"| Test files in diff | {r.signals.test_files} |\n")
    sb.write(f"| Config-ish files (CI/deploy/mod) | {r.signals.config_files} |\n")

    enf = r.enforcement
    sb.write("\n## PR risk assessment\n\n")
    sb.write(f"**{_display_rec(enf.merge_recommendation)}** — {enf.rationale}\n\n")

    if enf.required_validations:
        sb.write("### Required validations\n\n")
        for v in enf.required_validations:
            sb.write(f"- {v}\n")
        sb.write("\n")

    sb.write("\n## Score math\n\n")
    sm = r.score_math
    sb.write(f"- Factors subtotal: **{sm.factors_subtotal:.1f}**\n")
    sb.write(f"- Reducers subtotal: **{sm.reducers_subtotal:.1f}**\n")
    sb.write(f"- Net before floor: **{sm.net_before_floor:.1f}**\n")
    sb.write(f"- Final score: **{sm.final_score:.1f}**\n")
    sb.write(f"- Final band: **{sm.final_band}**\n")
    if sm.floor_applied:
        sb.write(f"- Floor applied at **{sm.floor_min_score:.0f}**\n")

    if r.factors:
        sb.write("\n## Risk factors\n\n")
        for f in r.factors:
            sb.write(f"- **{f.label}** (`{f.id}`, {f.points:.1f} pts)")
            if f.detail:
                sb.write(f": {f.detail}")
            sb.write("\n")

    if r.required_actions:
        sb.write("\n## Required actions\n\n")
        for a in r.required_actions:
            sb.write(f"- **[{a.priority or 'medium'}]** {a.title}\n")

    if enf.evidence_status:
        sb.write("\n## Evidence status\n\n")
        for ev in enf.evidence_status:
            if ev.status == EVIDENCE_UNKNOWN:
                continue
            icon = evidence_status_icon(ev.status)
            sb.write(f"- {icon} `{ev.id}` ({ev.status}): {ev.rationale}\n")

    sb.write("\n## Suggested PR comment\n\n```markdown\n")
    sb.write(r.integrations.pr_comment_markdown)
    sb.write("\n```\n")

    if os.path.dirname(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(sb.getvalue())
