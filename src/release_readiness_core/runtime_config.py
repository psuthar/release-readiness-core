"""Runtime configuration models for CLI/report behavior."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class RuntimeConfig:
    """Config-driven values used by CLI report rendering."""

    report_title: str = "Release readiness report"
    high_priority_evidence_ids: Sequence[str] = field(default_factory=tuple)


def parse_runtime_config(raw: Mapping[str, Any]) -> RuntimeConfig:
    """Parse runtime config payload into strongly typed values."""
    report_title = str(raw.get("report_title", "Release readiness report"))
    pr_risk = raw.get("pr_risk", {})
    high_priority: Iterable[str] = ()
    if isinstance(pr_risk, dict):
        ids = pr_risk.get("high_priority_evidence_ids", ())
        if isinstance(ids, list):
            high_priority = [str(v) for v in ids]
    return RuntimeConfig(
        report_title=report_title,
        high_priority_evidence_ids=tuple(high_priority),
    )


def summarize_high_priority_hits(
    pr_risk_payload: Mapping[str, Any],
    high_priority_ids: Sequence[str],
) -> Dict[str, str]:
    """Return matching high-priority evidence id -> status from pr_risk payload."""
    id_set = set(high_priority_ids)
    hits: Dict[str, str] = {}
    evidence = pr_risk_payload.get("evidence", [])
    if not isinstance(evidence, list):
        return hits
    for item in evidence:
        if not isinstance(item, dict):
            continue
        evidence_id = item.get("id")
        status = item.get("status")
        if isinstance(evidence_id, str) and evidence_id in id_set and isinstance(status, str):
            hits[evidence_id] = status
    return hits
