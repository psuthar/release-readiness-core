"""Routing hints (port of routing.go)."""

from __future__ import annotations

from typing import List, Optional

from release_readiness_core.pr_risk._internal import factor_ids, ok_bool
from release_readiness_core.pr_risk.context.types import ContextInsights
from release_readiness_core.pr_risk.types import (
    DOMAIN_AUTH,
    DOMAIN_DEPLOY,
    DOMAIN_MIGRATIONS,
    DOMAIN_ORCHESTRATION,
    DOMAIN_PROCESSING,
    DOMAIN_RAG,
    DOMAIN_WEB,
    DOMAIN_WORKFLOWS,
    RiskFactor,
    Signals,
)


def join_comma_sorted(xs: List[str]) -> str:
    if not xs:
        return ""
    return ", ".join(sorted(xs))


def compute_routing_hints(
    s: Signals,
    factors: List[RiskFactor],
    insights: Optional[ContextInsights],
) -> List[str]:
    """Return deterministic reviewer-routing hints."""
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

    has = factor_ids(factors)

    if s.domain_hits.get(DOMAIN_AUTH, 0) > 0:
        add("Include a reviewer familiar with auth, sessions, and invitations.")
    if s.domain_hits.get(DOMAIN_RAG, 0) > 0 or s.domain_hits.get(DOMAIN_PROCESSING, 0) > 0:
        add("Route processing/RAG changes to someone who owns ingestion, jobs, and Q&A quality.")
    if s.domain_hits.get(DOMAIN_ORCHESTRATION, 0) > 0:
        add(
            "Include reviewer familiar with creator orchestration recommendations and "
            "draft-approval flows."
        )
    if s.domain_hits.get(DOMAIN_WEB, 0) > 0 or ok_bool(has, "web_large"):
        add("Include frontend review for web/ UI and client behavior.")
    if s.migration_files > 0 or s.domain_hits.get(DOMAIN_MIGRATIONS, 0) > 0:
        add("Include database/migrations review before merge.")
    if s.domain_hits.get(DOMAIN_WORKFLOWS, 0) > 0 or s.domain_hits.get(DOMAIN_DEPLOY, 0) > 0:
        add("Include CI/infra review for workflow or deploy config changes.")

    if insights is not None:
        conc = insights.concentration
        if conc.mode in ("focused", "focused_large") and conc.top_prefix != "":
            add(f"Focus primary review on `{conc.top_prefix}` (majority of churn).")
        if conc.mode == "focused_large" and conc.top_prefix != "":
            add(
                f"Large single-area churn — run targeted regression and integration "
                f"checks around `{conc.top_prefix}`."
            )
        if conc.mode == "scattered" and s.file_count >= 10:
            add(
                "Split review by subsystem or commit; avoid single-threaded review of "
                "unrelated areas."
            )
        if len(insights.hotspots) > 0:
            p = insights.hotspots[0].prefix
            add(f"Extra reviewer attention on `{p}` (several recent commits touched this area).")
        if insights.intent.mismatch and len(insights.intent.domains_expected) > 0:
            add(
                "Confirm scope with author: PR text implies domains "
                f"{join_comma_sorted(insights.intent.domains_expected)} but diff may differ."
            )

    if not out and s.file_count > 0 and s.git_error == "":
        add("Assign reviewers using changed paths and domain hits; use CODEOWNERS if configured.")

    return out
