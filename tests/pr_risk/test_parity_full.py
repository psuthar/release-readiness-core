"""Phase 4 corpus parity for the semantic pr-risk.json file.

Same context-injection scaffold as test_parity_score.py: bypass git-dependent
context analysis by feeding captured ContextInsights and reconstructed context
FactorContributions into score(). Then compare the Python-emitted semantic
payload against the captured pr-risk.json byte-for-byte (after JSON canonical
ordering).

The full pr_risk.json deep-equal parity is gated on Phase 5 (real-checkout
end-to-end) because that artifact embeds generated_at timestamps and the
exact string ordering of evidence detail messages — both of which depend on
machinery (timestamps, git_log body) that captured fixtures don't preserve.
This Phase-4 test therefore focuses on what's most observable downstream:
the semantic file used by CI gates.
"""

from __future__ import annotations

import json
import math
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List
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
    return sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir() and (p / "pr-risk.json").is_file())


# corpus_runtime fixture is defined in tests/pr_risk/conftest.py (Phase 5 / SCRUM-243).


# Reuse helpers from test_parity_score (duplicated minimally to keep this file
# independent — the dataclasses are tiny).

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


def _insights_from_dict(d: Dict[str, Any]) -> ContextInsights:
    p = d.get("proximity") or {}
    c = d.get("concentration") or {}
    i = d.get("intent") or {}
    return ContextInsights(
        proximity=ProximityInsight(
            mode=p.get("mode", ""),
            structural_alignment=p.get("structural_alignment", ""),
            behavioral_coverage=p.get("behavioral_coverage", ""),
            non_test_files=p.get("non_test_files", 0),
            with_nearby_test_in_diff=p.get("with_nearby_test_in_diff", 0),
            ratio=p.get("ratio", 0.0),
            detail=p.get("detail", ""),
        ),
        concentration=ConcentrationInsight(
            mode=c.get("mode", ""),
            top_prefix=c.get("top_prefix", ""),
            top_share=c.get("top_share", 0.0),
            hhi=c.get("hhi", 0.0),
            unique_dirs=c.get("unique_prefixes", 0),
            detail=c.get("detail", ""),
        ),
        hotspots=[
            HotspotInsight(
                prefix=h.get("prefix", ""),
                recent_count=h.get("recent_hits", 0),
                detail=h.get("detail", ""),
            )
            for h in (d.get("hotspots") or [])
        ],
        hotspots_skip_reason=d.get("hotspots_skip_reason", ""),
        intent=IntentInsight(
            title=i.get("title", ""),
            intent_strength=i.get("intent_strength", ""),
            keywords_matched=list(i.get("keywords_matched") or []),
            domains_expected=list(i.get("domains_expected") or []),
            domains_in_diff=list(i.get("domains_in_diff") or []),
            aligned=i.get("aligned", False),
            mismatch=i.get("mismatch", False),
            detail=i.get("detail", ""),
        ),
    )


def _ctx_factors(factors_raw: List[Dict[str, Any]]) -> List[FactorContribution]:
    return [
        FactorContribution(
            id=f["id"],
            label=f.get("label", ""),
            points=f.get("points", 0.0),
            detail=f.get("detail", ""),
        )
        for f in factors_raw
        if f.get("id", "").startswith("context_")
    ]


@contextmanager
def _patched_context(insights: ContextInsights, ctx_factors: List[FactorContribution]):
    with mock.patch(
        "release_readiness_core.pr_risk.score.context_analyze_fn",
        return_value=(insights, ctx_factors),
    ):
        yield


def _close_numeric(a: Any, b: Any, rel_tol: float = 1e-9, abs_tol: float = 1e-9) -> bool:
    if isinstance(a, float) or isinstance(b, float):
        try:
            return math.isclose(float(a), float(b), rel_tol=rel_tol, abs_tol=abs_tol)
        except (TypeError, ValueError):
            return False
    return a == b


def _equal_modulo_floats(got: dict, captured: dict) -> bool:
    """Compare two dicts; numeric fields use isclose, others exact."""
    if got.keys() != captured.keys():
        return False
    for k in got:
        a, b = got[k], captured[k]
        if isinstance(a, list) and isinstance(b, list):
            if len(a) != len(b):
                return False
            for xa, xb in zip(a, b):
                if not _close_numeric(xa, xb):
                    return False
        elif not _close_numeric(a, b):
            return False
    return True


@pytest.mark.parametrize("fixture_dir", _discover(), ids=lambda p: p.name)
def test_semantic_payload_parity(fixture_dir: Path, corpus_runtime) -> None:
    """Python's semantic_payload matches captured pr-risk.json structurally."""
    pr_risk = json.loads((fixture_dir / "pr_risk.json").read_text())
    captured_semantic = json.loads((fixture_dir / "pr-risk.json").read_text())

    insights = _insights_from_dict(pr_risk.get("context_insights") or {})
    ctxf = _ctx_factors(pr_risk.get("factors") or [])
    sig = _signals_from_dict(pr_risk["signals"])

    from release_readiness_core.pr_risk.score import score
    from release_readiness_core.pr_risk.semantic_json import semantic_payload_for_test

    with _patched_context(insights, ctxf):
        r = score(sig, default_weights(), runtime=corpus_runtime)

    payload = semantic_payload_for_test(r)
    assert _equal_modulo_floats(payload, captured_semantic), (
        f"{fixture_dir.name}: payload mismatch\n"
        f"  got: {json.dumps(payload, indent=2)}\n"
        f"  want: {json.dumps(captured_semantic, indent=2)}"
    )
