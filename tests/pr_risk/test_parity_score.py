"""Phase 3 corpus parity for the score / categories / policy layer.

This bypasses the git-dependent context analyzer (hotspots needs the
captured-time git state; full intent needs the merge-commit body that the
capture script didn't preserve). For each fixture we instead **inject** the
captured ContextInsights and rebuild the context FactorContribution list
from the captured factors[]. That way every fixture's score / categories /
merge_recommendation is computed by Python's score, categories, and policy
modules using the exact same context inputs Go used.

Phase 4 (SCRUM-236) will replace this scaffold with a true end-to-end
parity test that runs the full CLI against a real repo checkout.
"""

from __future__ import annotations

import json
import math
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Tuple
from unittest import mock

import pytest

from release_readiness_core.pr_risk.context.types import (
    ConcentrationInsight,
    ContextInsights,
    FactorContribution,
    HotspotInsight,
    IntentInsight,
    ProximityInsight,
)
from release_readiness_core.pr_risk.types import FileChange, Signals, default_weights


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _discover() -> List[Path]:
    if not FIXTURES_DIR.exists():
        return []
    return sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir() and (p / "pr_risk.json").is_file())


# ---------------------------------------------------------------------------
# Reconstruction helpers.

def _signals_from_dict(d: Dict[str, Any]) -> Signals:
    files_raw = d.get("files") or []
    files = [
        FileChange(path=f["path"], added=f.get("added", 0), deleted=f.get("deleted", 0))
        for f in files_raw
    ]
    return Signals(
        base_ref=d.get("base_ref", ""),
        head_ref=d.get("head_ref", ""),
        file_count=d.get("file_count", 0),
        total_added=d.get("total_added", 0),
        total_deleted=d.get("total_deleted", 0),
        total_loc=d.get("total_loc", 0),
        test_loc_ratio=d.get("test_loc_ratio", 0.0),
        files=files,
        domain_hits=dict(d.get("domain_hits") or {}),
        test_domain_hits=dict(d.get("test_domain_hits") or {}),
        test_unit_domain_hits=dict(d.get("test_unit_domain_hits") or {}),
        test_e2e_domain_hits=dict(d.get("test_e2e_domain_hits") or {}),
        test_files=d.get("test_files", 0),
        unit_test_files=d.get("unit_test_files", 0),
        e2e_test_files=d.get("e2e_test_files", 0),
        config_files=d.get("config_files", 0),
        migration_files=d.get("migration_files", 0),
        git_error=d.get("git_error", ""),
        validation_note_found=d.get("validation_note_found", False),
        validation_note_snippet=d.get("validation_note_snippet", ""),
        style_only_note_found=d.get("style_only_note_found", False),
        style_only_note_snippet=d.get("style_only_note_snippet", ""),
        repo_root=d.get("repo_root", ""),
    )


def _proximity_from_dict(d: Dict[str, Any]) -> ProximityInsight:
    return ProximityInsight(
        mode=d.get("mode", ""),
        structural_alignment=d.get("structural_alignment", ""),
        behavioral_coverage=d.get("behavioral_coverage", ""),
        non_test_files=d.get("non_test_files", 0),
        with_nearby_test_in_diff=d.get("with_nearby_test_in_diff", 0),
        ratio=d.get("ratio", 0.0),
        detail=d.get("detail", ""),
    )


def _concentration_from_dict(d: Dict[str, Any]) -> ConcentrationInsight:
    return ConcentrationInsight(
        mode=d.get("mode", ""),
        top_prefix=d.get("top_prefix", ""),
        top_share=d.get("top_share", 0.0),
        hhi=d.get("hhi", 0.0),
        unique_dirs=d.get("unique_prefixes", 0),  # JSON tag rename
        detail=d.get("detail", ""),
    )


def _hotspot_from_dict(d: Dict[str, Any]) -> HotspotInsight:
    return HotspotInsight(
        prefix=d.get("prefix", ""),
        recent_count=d.get("recent_hits", 0),  # JSON tag rename
        detail=d.get("detail", ""),
    )


def _intent_from_dict(d: Dict[str, Any]) -> IntentInsight:
    return IntentInsight(
        title=d.get("title", ""),
        intent_strength=d.get("intent_strength", ""),
        keywords_matched=list(d.get("keywords_matched") or []),
        domains_expected=list(d.get("domains_expected") or []),
        domains_in_diff=list(d.get("domains_in_diff") or []),
        aligned=d.get("aligned", False),
        mismatch=d.get("mismatch", False),
        detail=d.get("detail", ""),
    )


def _insights_from_dict(d: Dict[str, Any]) -> ContextInsights:
    return ContextInsights(
        proximity=_proximity_from_dict(d.get("proximity") or {}),
        concentration=_concentration_from_dict(d.get("concentration") or {}),
        hotspots=[_hotspot_from_dict(h) for h in (d.get("hotspots") or [])],
        hotspots_skip_reason=d.get("hotspots_skip_reason", ""),
        intent=_intent_from_dict(d.get("intent") or {}),
    )


def _ctx_factors_from_captured(factors_raw: List[Dict[str, Any]]) -> List[FactorContribution]:
    """Pull the context_* factors from captured factors[] in their captured order."""
    out: List[FactorContribution] = []
    for f in factors_raw:
        if f.get("id", "").startswith("context_"):
            out.append(
                FactorContribution(
                    id=f["id"],
                    label=f.get("label", ""),
                    points=f.get("points", 0.0),
                    detail=f.get("detail", ""),
                )
            )
    return out


@contextmanager
def _patched_context(insights: ContextInsights, ctx_factors: List[FactorContribution]):
    """Replace score's context_analyze_fn with a constant function for one call."""
    with mock.patch(
        "release_readiness_core.pr_risk.score.context_analyze_fn",
        return_value=(insights, ctx_factors),
    ):
        yield


# ---------------------------------------------------------------------------
# Comparison helpers.

def _close(a: Any, b: Any, rel_tol: float = 1e-9, abs_tol: float = 1e-9) -> bool:
    if isinstance(a, float) or isinstance(b, float):
        try:
            return math.isclose(float(a), float(b), rel_tol=rel_tol, abs_tol=abs_tol)
        except (TypeError, ValueError):
            return False
    return a == b


# ---------------------------------------------------------------------------
# Tests.

@pytest.mark.parametrize("fixture_dir", _discover(), ids=lambda p: p.name)
def test_score_band_math_parity(fixture_dir: Path) -> None:
    """final_score, final_band, score_math fields match captured Go output."""
    pr_risk = json.loads((fixture_dir / "pr_risk.json").read_text())
    insights = _insights_from_dict(pr_risk.get("context_insights") or {})
    ctx_factors = _ctx_factors_from_captured(pr_risk.get("factors") or [])
    sig = _signals_from_dict(pr_risk["signals"])

    from release_readiness_core.pr_risk.score import score

    with _patched_context(insights, ctx_factors):
        r = score(sig, default_weights())

    assert r.risk_band == pr_risk["risk_band"], fixture_dir.name
    assert _close(r.risk_score, pr_risk["risk_score"]), fixture_dir.name

    sm = pr_risk["score_math"]
    assert _close(r.score_math.factors_subtotal, sm["factors_subtotal"])
    assert _close(r.score_math.reducers_subtotal, sm["reducers_subtotal"])
    assert _close(r.score_math.net_before_floor, sm["net_before_floor"])
    assert _close(r.score_math.floor_min_score, sm["floor_min_score"])
    assert r.score_math.floor_applied == sm["floor_applied"]
    assert _close(r.score_math.final_score, sm["final_score"])
    assert r.score_math.final_band == sm["final_band"]


@pytest.mark.parametrize("fixture_dir", _discover(), ids=lambda p: p.name)
def test_categories_parity(fixture_dir: Path) -> None:
    """Per-lane category risk_score and factor/reducer membership match Go."""
    pr_risk = json.loads((fixture_dir / "pr_risk.json").read_text())
    insights = _insights_from_dict(pr_risk.get("context_insights") or {})
    ctx_factors = _ctx_factors_from_captured(pr_risk.get("factors") or [])
    sig = _signals_from_dict(pr_risk["signals"])

    from release_readiness_core.pr_risk.score import score

    with _patched_context(insights, ctx_factors):
        r = score(sig, default_weights())

    captured_cats = pr_risk.get("categories") or []
    by_key = {c["key"]: c for c in captured_cats}

    for cat in r.categories:
        cap = by_key.get(cat.key)
        if cap is None:
            pytest.fail(f"category {cat.key!r} missing from captured fixture {fixture_dir.name}")
        assert _close(cat.risk_score, cap["risk_score"]), f"{fixture_dir.name}/{cat.key}"
        if "confidence" in cap:
            assert _close(cat.confidence, cap["confidence"])
        # Factor/reducer membership: order matters for parity (Go preserves emit order).
        assert list(cat.factors) == list(cap.get("factors") or []), f"{fixture_dir.name}/{cat.key}/factors"
        assert list(cat.reducers) == list(cap.get("reducers") or []), f"{fixture_dir.name}/{cat.key}/reducers"


@pytest.mark.parametrize("fixture_dir", _discover(), ids=lambda p: p.name)
def test_merge_recommendation_parity(fixture_dir: Path) -> None:
    pr_risk = json.loads((fixture_dir / "pr_risk.json").read_text())
    insights = _insights_from_dict(pr_risk.get("context_insights") or {})
    ctx_factors = _ctx_factors_from_captured(pr_risk.get("factors") or [])
    sig = _signals_from_dict(pr_risk["signals"])

    from release_readiness_core.pr_risk.score import score

    with _patched_context(insights, ctx_factors):
        r = score(sig, default_weights())

    captured_rec = (pr_risk.get("enforcement") or {}).get("merge_recommendation", "")
    # Note: Go's mergeRecommendation returns the lowercase short form (pass/warn/block).
    # Phase 4 will add the evidence-aware upgrade that may change this; for Phase 3
    # we only validate the base recommendation logic.
    assert r.enforcement.merge_recommendation == captured_rec, fixture_dir.name
