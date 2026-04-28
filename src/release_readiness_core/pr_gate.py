"""Generic PR gate combiner supporting N inputs and pluggable formatting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Mapping, Sequence


Status = str


@dataclass(frozen=True)
class GateInput:
    """Single gate input normalized for aggregation."""

    source: str
    status: Status
    payload: Mapping[str, Any]


@dataclass(frozen=True)
class GateSummary:
    """Combined recommendation and normalized per-source statuses."""

    recommendation: Status
    sources: Sequence[Dict[str, Any]]


def _normalize_status(value: str) -> Status:
    status = value.upper()
    if status not in {"PASS", "WARN", "BLOCK"}:
        raise ValueError(f"Unsupported gate status: {value}")
    return status


def combine_gate_inputs(inputs: Iterable[GateInput]) -> GateSummary:
    """Combine N gate inputs using BLOCK > WARN > PASS precedence."""
    normalized: List[GateInput] = []
    for item in inputs:
        normalized.append(
            GateInput(source=item.source, status=_normalize_status(item.status), payload=item.payload)
        )
    recommendation = "PASS"
    if any(item.status == "BLOCK" for item in normalized):
        recommendation = "BLOCK"
    elif any(item.status == "WARN" for item in normalized):
        recommendation = "WARN"

    return GateSummary(
        recommendation=recommendation,
        sources=[
            {"source": item.source, "status": item.status, "payload": dict(item.payload)}
            for item in normalized
        ],
    )


def to_payload(summary: GateSummary) -> Dict[str, Any]:
    """Default payload formatter."""
    return {"recommendation": summary.recommendation, "sources": list(summary.sources)}


def format_gate_output(
    summary: GateSummary,
    formatter: Callable[[GateSummary], Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """Format gate output with default or custom formatter."""
    return formatter(summary) if formatter is not None else to_payload(summary)
