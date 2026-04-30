"""Required actions — config-driven gate registry (SCRUM-241 / Phase 3 of SCRUM-238).

Loops over ``runtime.gates`` evaluating each gate's ``applies_when`` predicates
against the current factor set, risk band, signals, and context insights. The
five hardcoded gate emit-blocks (auth, rag, processing, orchestration,
migrations) and the generic gates (ci_fetch_depth_zero, pr_review_summary,
workflow_config_validation, add_tests_or_evidence, context_*) all live in the
config now. The only Python branching that remains is the gate evaluator.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from release_readiness_core.pr_risk._internal import factor_ids
from release_readiness_core.pr_risk.actions_priority import sort_required_actions
from release_readiness_core.pr_risk.context.types import ContextInsights
from release_readiness_core.pr_risk.types import (
    RequiredAction,
    RiskFactor,
    RiskReducer,
    Signals,
)

if TYPE_CHECKING:
    from release_readiness_core.pr_risk._config import ChecklistItem, Gate, GateVariant
    from release_readiness_core.pr_risk._runtime import PRRiskRuntime


def compute_required_actions(
    s: Signals,
    factors: List[RiskFactor],
    reducers: List[RiskReducer],
    risk_score: float,
    risk_band: str,
    insights: Optional[ContextInsights],
    *,
    runtime: Optional["PRRiskRuntime"] = None,
) -> List[RequiredAction]:
    """Build the deterministic list of pre-merge required actions, sorted by priority."""
    del reducers, risk_score  # Reserved for future predicates; not used today.

    runtime = runtime or _default_runtime()

    has = factor_ids(factors)
    out: List[RequiredAction] = []
    seen: set = set()

    for gate in runtime.gates:
        if gate.id in seen:
            continue
        if not _evaluate_applies_when(gate.applies_when, has, risk_band, s, insights):
            continue
        action = _materialize_action(gate, s, insights, risk_band)
        seen.add(gate.id)
        out.append(action)

    return sort_required_actions(out)


# ---------------------------------------------------------------------------
# applies_when evaluator (closed predicate set).

def _evaluate_applies_when(
    predicates: List[Dict[str, Any]],
    has: set,
    risk_band: str,
    s: Signals,
    insights: Optional[ContextInsights],
) -> bool:
    """Return True iff ALL predicates in ``predicates`` match (AND semantics).

    Empty predicate list → True (gate always fires; only the dedup ``seen``
    check would prevent emission). Phase 1 / 3 closed set: ``factor_id``
    (str|list), ``not_factor_id`` (str|list), ``risk_band``, ``not_risk_band``,
    ``domain_factor``, ``intent_mismatch``, ``concentration_mode``,
    ``hotspots_present``, ``proximity_distant_with_sensitive``.
    """
    for pred in predicates:
        if not _evaluate_one(pred, has, risk_band, s, insights):
            return False
    return True


def _evaluate_one(
    pred: Dict[str, Any],
    has: set,
    risk_band: str,
    s: Signals,
    insights: Optional[ContextInsights],
) -> bool:
    if "factor_id" in pred:
        return _factor_match(has, pred["factor_id"])
    if "not_factor_id" in pred:
        return not _factor_match(has, pred["not_factor_id"])
    if "risk_band" in pred:
        return risk_band in pred["risk_band"]
    if "not_risk_band" in pred:
        return risk_band not in pred["not_risk_band"]
    if "domain_factor" in pred:
        # Alias: matches when factor `domain_<value>` is present.
        return f"domain_{pred['domain_factor']}" in has
    if "intent_mismatch" in pred:
        want = bool(pred["intent_mismatch"])
        got = bool(insights and insights.intent.mismatch)
        return got is want
    if "concentration_mode" in pred:
        if insights is None:
            return False
        if insights.concentration.mode != pred["concentration_mode"]:
            return False
        min_files = int(pred.get("min_file_count", 0))
        return s.file_count >= min_files
    if "hotspots_present" in pred:
        want = bool(pred["hotspots_present"])
        got = bool(insights and len(insights.hotspots) > 0)
        return got is want
    if "proximity_distant_with_sensitive" in pred:
        want = bool(pred["proximity_distant_with_sensitive"])
        if insights is None:
            return not want
        if insights.proximity.mode != "distant":
            return not want
        min_files = int(pred.get("min_non_test_files", 0))
        if insights.proximity.non_test_files < min_files:
            return not want
        domains = pred.get("domains", []) or []
        if any(s.domain_hits.get(d, 0) > 0 for d in domains):
            return want
        return not want
    # Loader-validated input should never reach here.
    return False


def _factor_match(has: set, val: Any) -> bool:
    if isinstance(val, list):
        return any(f in has for f in val)
    return val in has


# ---------------------------------------------------------------------------
# Variant resolution + checklist materialization.

def _materialize_action(
    gate: "Gate",
    s: Signals,
    insights: Optional[ContextInsights],
    risk_band: str,
) -> RequiredAction:
    variant = _select_variant(gate, risk_band)
    title = variant.title if variant and variant.title is not None else gate.title
    if variant and variant.applies_when_extra is not None:
        applies_when_extra = variant.applies_when_extra
    else:
        applies_when_extra = gate.applies_when_extra
    checklist_items = (
        variant.checklist if variant and variant.checklist is not None else gate.checklist
    )

    domain = _domain_for_gate(gate)
    evidence_level = _evidence_level(s, domain) if domain else "none"

    checklist_strs = [
        _materialize_text(item, s, evidence_level, insights)
        for item in checklist_items
    ]

    return RequiredAction(
        id=gate.id,
        title=title,
        priority=gate.priority,
        fix_type=gate.fix_type,
        applies_when=applies_when_extra,
        checklist=checklist_strs,
    )


def _select_variant(gate: "Gate", risk_band: str) -> Optional["GateVariant"]:
    """Return the first variant whose ``when`` matches the given risk band."""
    for v in gate.variants:
        when = v.when or {}
        if "risk_band" in when and risk_band not in when["risk_band"]:
            continue
        if "not_risk_band" in when and risk_band in when["not_risk_band"]:
            continue
        return v
    return None


def _materialize_text(
    item: "ChecklistItem",
    s: Signals,
    evidence_level: str,
    insights: Optional[ContextInsights],
) -> str:
    text = item.text
    if evidence_level in item.by_evidence_level:
        text = item.by_evidence_level[evidence_level]
    if s.validation_note_found and item.by_validation_note is not None:
        text = item.by_validation_note
    if "{prefix}" in text and insights and insights.hotspots:
        text = text.replace("{prefix}", insights.hotspots[0].prefix)
    return text


def _domain_for_gate(gate: "Gate") -> Optional[str]:
    """Infer the domain a gate is scoped to, for ``_evidence_level`` lookups.

    Order: explicit ``evidence.args.domain`` wins; otherwise look for a
    ``factor_id: domain_<X>`` predicate. Returns ``None`` when the gate isn't
    domain-scoped (generic gates like ``ci_fetch_depth_zero``).
    """
    if gate.evidence and gate.evidence.args:
        d = gate.evidence.args.get("domain")
        if isinstance(d, str) and d:
            return d
    for pred in gate.applies_when:
        fid = pred.get("factor_id")
        if isinstance(fid, str) and fid.startswith("domain_"):
            return fid[len("domain_"):]
    return None


def _evidence_level(s: Signals, domain: str) -> str:
    if s.test_e2e_domain_hits.get(domain, 0) > 0:
        return "e2e"
    if s.test_unit_domain_hits.get(domain, 0) > 0:
        return "unit"
    return "none"


# ---------------------------------------------------------------------------

def _default_runtime():
    """Return a memoized bundled-default ``PRRiskRuntime``.

    Threaded as the default for callers that don't pass an explicit runtime.
    Imported lazily to avoid a circular import with ``classify.py`` /
    ``_runtime.py``.
    """
    from release_readiness_core.pr_risk.classify import _default_runtime as _rt

    return _rt()
