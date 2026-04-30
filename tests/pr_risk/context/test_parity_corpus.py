"""Corpus parity test for context analyzers (proximity + concentration only).

Hotspots and intent require the same git state and same git_head_message body
that Go saw at capture time. The capture script preserved PR title via env,
but the merge-commit body wasn't recorded — so intent's `keywords_matched`
can legitimately diverge for fixtures whose PR body contained domain keywords.

This file therefore parity-tests proximity + concentration. Hotspots and full
intent parity arrive in Phase 4 (SCRUM-236) where the CLI runs end-to-end
against a real checkout.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List

import pytest

from release_readiness_core.pr_risk.classify import is_test_path, is_untestable_path
from release_readiness_core.pr_risk.context.analyze import analyze, default_weights
from release_readiness_core.pr_risk.context.input import FileChange, Input

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


def _discover() -> List[Path]:
    if not FIXTURES_DIR.exists():
        return []
    return sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir() and (p / "pr_risk.json").is_file())


def _input_from_signals(sig: Dict[str, Any], pr_title: str) -> Input:
    files_raw = sig.get("files") or []
    files = [
        FileChange(path=f["path"], added=f.get("added", 0), deleted=f.get("deleted", 0))
        for f in files_raw
    ]
    is_test = [is_test_path(f.path) for f in files]
    is_untestable = [is_untestable_path(f.path) for f in files]
    return Input(
        # Empty repo_root + git_error="" suppresses git-dependent paths
        # (hotspots returns []; intent skips git_head_message body).
        repo_root="",
        git_error="",
        files=files,
        is_test=is_test,
        is_untestable=is_untestable,
        domain_hits=sig.get("domain_hits") or {},
        test_unit_domain_hits=sig.get("test_unit_domain_hits") or {},
        test_e2e_domain_hits=sig.get("test_e2e_domain_hits") or {},
        pr_title=pr_title,
        pr_body="",
    )


def _proximity_to_dict(p) -> Dict[str, Any]:
    return {
        "mode": p.mode,
        "structural_alignment": p.structural_alignment,
        "behavioral_coverage": p.behavioral_coverage,
        "non_test_files": p.non_test_files,
        "with_nearby_test_in_diff": p.with_nearby_test_in_diff,
        "ratio": p.ratio,
        "detail": p.detail,
    }


def _concentration_to_dict(c) -> Dict[str, Any]:
    """Note Go JSON tag rename: unique_dirs -> unique_prefixes."""
    return {
        "mode": c.mode,
        "top_prefix": c.top_prefix,
        "top_share": c.top_share,
        "hhi": c.hhi,
        "unique_prefixes": c.unique_dirs,
        "detail": c.detail,
    }


def _dicts_close(got: Dict[str, Any], captured: Dict[str, Any]) -> bool:
    """Equal up to float ULP drift on numeric fields.

    Go map iteration is non-deterministic, so summed floats (HHI, top_share)
    can differ from any reproducer by a handful of ULPs. We accept relative
    tolerance 1e-12 for floats, exact for everything else.
    """
    if got.keys() != captured.keys():
        return False
    for k in got:
        a, b = got[k], captured[k]
        if isinstance(a, float) and isinstance(b, (int, float)):
            if not math.isclose(a, float(b), rel_tol=1e-12, abs_tol=1e-12):
                return False
        else:
            if a != b:
                return False
    return True


def _filter_optional(d: Dict[str, Any]) -> Dict[str, Any]:
    """Mirror Go json:"...,omitempty" — drop zero-valued optional fields for fair compare.

    Go's `omitempty` removes zero numbers and empty strings from the JSON. We
    filter both sides identically before comparing.
    """
    OMIT_IF_ZERO = {"top_share", "hhi", "non_test_files", "with_nearby_test_in_diff", "ratio"}
    OMIT_IF_EMPTY = {"top_prefix", "detail"}
    out = {}
    for k, v in d.items():
        if k in OMIT_IF_ZERO and v == 0:
            continue
        if k in OMIT_IF_EMPTY and v == "":
            continue
        out[k] = v
    return out


@pytest.mark.parametrize("fixture_dir", _discover(), ids=lambda p: p.name)
def test_proximity_parity(fixture_dir: Path) -> None:
    pr_risk = json.loads((fixture_dir / "pr_risk.json").read_text())
    meta = json.loads((fixture_dir / "meta.json").read_text())
    captured = pr_risk.get("context_insights", {}).get("proximity")
    if captured is None:
        pytest.skip("no proximity in captured fixture")
    inp = _input_from_signals(pr_risk["signals"], meta.get("pr_title", ""))
    insights, _ = analyze(inp, default_weights())
    got = _proximity_to_dict(insights.proximity)
    assert _dicts_close(_filter_optional(got), _filter_optional(captured)), fixture_dir.name


@pytest.mark.parametrize("fixture_dir", _discover(), ids=lambda p: p.name)
def test_concentration_parity(fixture_dir: Path) -> None:
    pr_risk = json.loads((fixture_dir / "pr_risk.json").read_text())
    meta = json.loads((fixture_dir / "meta.json").read_text())
    captured = pr_risk.get("context_insights", {}).get("concentration")
    if captured is None:
        pytest.skip("no concentration in captured fixture")
    inp = _input_from_signals(pr_risk["signals"], meta.get("pr_title", ""))
    insights, _ = analyze(inp, default_weights())
    got = _concentration_to_dict(insights.concentration)
    assert _dicts_close(_filter_optional(got), _filter_optional(captured)), fixture_dir.name
