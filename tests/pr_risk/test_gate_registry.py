"""Synthetic-config tests for the Phase 3 gate registry.

Each test loads a hand-rolled config with one or two gates whose
``applies_when`` exercises a specific predicate; assertions then check that
the gate fires only when its predicate matches.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent
from typing import List

import pytest

from release_readiness_core.pr_risk._runtime import PRRiskRuntime
from release_readiness_core.pr_risk.actions import compute_required_actions
from release_readiness_core.pr_risk.context.types import (
    ConcentrationInsight,
    ContextInsights,
    HotspotInsight,
    IntentInsight,
    ProximityInsight,
)
from release_readiness_core.pr_risk.types import (
    RequiredAction,
    RiskFactor,
    Signals,
)
from release_readiness_core.pr_risk.validations import compute_required_validations


def _runtime(tmp_path: Path, body: str) -> PRRiskRuntime:
    p = tmp_path / "pr-risk-config.yaml"
    p.write_text(dedent(body).lstrip(), encoding="utf-8")
    return PRRiskRuntime.from_config(p)


def _fac(*ids: str) -> List[RiskFactor]:
    return [RiskFactor(id=i, label=i, points=10.0) for i in ids]


def _action_ids(actions: List[RequiredAction]) -> List[str]:
    return [a.id for a in actions]


# ---------------------------------------------------------------------------
# Predicate coverage — one gate per predicate type.

def test_gate_fires_on_factor_id_string(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_factor
            title: factor gate
            priority: medium
            fix_type: process
            applies_when:
              - { factor_id: my_factor }
            checklist: ["do the thing"]
    """)
    out = compute_required_actions(Signals(), _fac("my_factor"), [], 0, "low", None, runtime=rt)
    assert "g_factor" in _action_ids(out)
    out = compute_required_actions(Signals(), _fac("other"), [], 0, "low", None, runtime=rt)
    assert out == []


def test_gate_fires_on_factor_id_list_any_of(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_any
            title: any-of factor gate
            priority: medium
            fix_type: process
            applies_when:
              - factor_id: [a, b, c]
            checklist: ["x"]
    """)
    for fid in ("a", "b", "c"):
        out = compute_required_actions(Signals(), _fac(fid), [], 0, "low", None, runtime=rt)
        assert "g_any" in _action_ids(out), f"failed for {fid}"
    out = compute_required_actions(Signals(), _fac("d"), [], 0, "low", None, runtime=rt)
    assert out == []


def test_gate_fires_on_not_factor_id(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_not
            title: not-factor gate
            priority: medium
            fix_type: process
            applies_when:
              - { not_factor_id: skip_me }
            checklist: ["x"]
    """)
    # `not_factor_id` matches when the factor is absent → gate fires.
    out = compute_required_actions(Signals(), _fac("other"), [], 0, "low", None, runtime=rt)
    assert "g_not" in _action_ids(out)
    out = compute_required_actions(Signals(), _fac("skip_me"), [], 0, "low", None, runtime=rt)
    assert out == []


def test_gate_fires_on_risk_band(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_band
            title: band gate
            priority: high
            fix_type: test
            applies_when:
              - { risk_band: [high, critical] }
            checklist: ["x"]
    """)
    out = compute_required_actions(Signals(), [], [], 60, "high", None, runtime=rt)
    assert "g_band" in _action_ids(out)
    out = compute_required_actions(Signals(), [], [], 80, "critical", None, runtime=rt)
    assert "g_band" in _action_ids(out)
    out = compute_required_actions(Signals(), [], [], 30, "medium", None, runtime=rt)
    assert out == []


def test_gate_fires_on_not_risk_band(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_nband
            title: not-band gate
            priority: medium
            fix_type: process
            applies_when:
              - { not_risk_band: [high, critical] }
            checklist: ["x"]
    """)
    out = compute_required_actions(Signals(), [], [], 30, "medium", None, runtime=rt)
    assert "g_nband" in _action_ids(out)
    out = compute_required_actions(Signals(), [], [], 60, "high", None, runtime=rt)
    assert out == []


def test_gate_fires_on_domain_factor(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_dom
            title: domain factor gate
            priority: high
            fix_type: test
            applies_when:
              - { domain_factor: ml }
            checklist: ["x"]
    """)
    # `domain_factor: ml` matches factor `domain_ml`.
    out = compute_required_actions(Signals(), _fac("domain_ml"), [], 0, "low", None, runtime=rt)
    assert "g_dom" in _action_ids(out)
    out = compute_required_actions(Signals(), _fac("domain_other"), [], 0, "low", None, runtime=rt)
    assert out == []


def test_gate_fires_on_intent_mismatch(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_im
            title: intent mismatch
            priority: medium
            fix_type: process
            applies_when:
              - { intent_mismatch: true }
            checklist: ["x"]
    """)
    insights = ContextInsights(intent=IntentInsight(mismatch=True))
    out = compute_required_actions(Signals(), [], [], 0, "low", insights, runtime=rt)
    assert "g_im" in _action_ids(out)
    insights = ContextInsights(intent=IntentInsight(mismatch=False))
    out = compute_required_actions(Signals(), [], [], 0, "low", insights, runtime=rt)
    assert out == []


def test_gate_fires_on_concentration_mode_with_min_files(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_conc
            title: scattered review
            priority: supporting
            fix_type: process
            applies_when:
              - { concentration_mode: scattered, min_file_count: 10 }
            checklist: ["x"]
    """)
    insights = ContextInsights(concentration=ConcentrationInsight(mode="scattered"))
    s = Signals(file_count=15)
    out = compute_required_actions(s, [], [], 0, "low", insights, runtime=rt)
    assert "g_conc" in _action_ids(out)
    # Below threshold → no fire.
    s = Signals(file_count=5)
    out = compute_required_actions(s, [], [], 0, "low", insights, runtime=rt)
    assert out == []
    # Wrong mode → no fire.
    insights = ContextInsights(concentration=ConcentrationInsight(mode="focused"))
    s = Signals(file_count=15)
    out = compute_required_actions(s, [], [], 0, "low", insights, runtime=rt)
    assert out == []


def test_gate_fires_on_hotspots_present(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_hot
            title: hotspot focus
            priority: supporting
            fix_type: process
            applies_when:
              - { hotspots_present: true }
            checklist: ["look at `{prefix}` carefully"]
    """)
    insights = ContextInsights(hotspots=[HotspotInsight(prefix="src/foo", recent_count=5)])
    out = compute_required_actions(Signals(), [], [], 0, "low", insights, runtime=rt)
    assert "g_hot" in _action_ids(out)
    # Hotspot prefix substituted into checklist.
    g_hot = next(a for a in out if a.id == "g_hot")
    assert "src/foo" in g_hot.checklist[0]
    insights = ContextInsights(hotspots=[])
    out = compute_required_actions(Signals(), [], [], 0, "low", insights, runtime=rt)
    assert out == []


def test_gate_fires_on_proximity_distant_with_sensitive(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_prox
            title: improve proximity
            priority: supporting
            fix_type: test
            applies_when:
              - proximity_distant_with_sensitive: true
                min_non_test_files: 2
                domains: [auth, db]
            checklist: ["x"]
    """)
    insights = ContextInsights(
        proximity=ProximityInsight(mode="distant", non_test_files=3),
    )
    s = Signals(domain_hits={"auth": 1})
    out = compute_required_actions(s, [], [], 0, "low", insights, runtime=rt)
    assert "g_prox" in _action_ids(out)
    # Sensitive-domain hit missing → no fire.
    s = Signals(domain_hits={"web": 1})
    out = compute_required_actions(s, [], [], 0, "low", insights, runtime=rt)
    assert out == []
    # Non-test files below threshold → no fire.
    insights = ContextInsights(
        proximity=ProximityInsight(mode="distant", non_test_files=1),
    )
    s = Signals(domain_hits={"auth": 1})
    out = compute_required_actions(s, [], [], 0, "low", insights, runtime=rt)
    assert out == []
    # Mode != distant → no fire.
    insights = ContextInsights(
        proximity=ProximityInsight(mode="adequate", non_test_files=5),
    )
    s = Signals(domain_hits={"auth": 1})
    out = compute_required_actions(s, [], [], 0, "low", insights, runtime=rt)
    assert out == []


# ---------------------------------------------------------------------------
# Variant resolution.

def test_gate_variant_overrides_title_and_checklist(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_var
            title: base title
            priority: high
            fix_type: test
            applies_when:
              - { factor_id: f }
            checklist: ["base line"]
            variants:
              - when: { risk_band: [high, critical] }
                title: high-band title
                applies_when_extra: high-band extra
                checklist: ["high line 1", "high line 2"]
    """)
    # Medium band → base values.
    out = compute_required_actions(Signals(), _fac("f"), [], 30, "medium", None, runtime=rt)
    assert len(out) == 1
    assert out[0].title == "base title"
    assert out[0].checklist == ["base line"]
    # High band → variant.
    out = compute_required_actions(Signals(), _fac("f"), [], 60, "high", None, runtime=rt)
    assert out[0].title == "high-band title"
    assert out[0].applies_when == "high-band extra"
    assert out[0].checklist == ["high line 1", "high line 2"]


# ---------------------------------------------------------------------------
# Checklist text overrides.

def test_checklist_by_evidence_level(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_ev
            title: evidence-conditioned
            priority: high
            fix_type: test
            applies_when:
              - { factor_id: domain_widget }
            checklist:
              - text: "default text"
                by_evidence_level:
                  none: "no test text"
                  unit: "unit-only text"
            evidence:
              template: test_domain
              args: { domain: widget }
    """)
    # No tests for "widget" → "none" override.
    out = compute_required_actions(
        Signals(), _fac("domain_widget"), [], 0, "low", None, runtime=rt
    )
    assert out[0].checklist == ["no test text"]
    # Unit tests for "widget" → "unit" override.
    s = Signals(test_unit_domain_hits={"widget": 1})
    out = compute_required_actions(s, _fac("domain_widget"), [], 0, "low", None, runtime=rt)
    assert out[0].checklist == ["unit-only text"]
    # E2E tests for "widget" → falls through to default text (no "e2e" override here).
    s = Signals(test_e2e_domain_hits={"widget": 1})
    out = compute_required_actions(s, _fac("domain_widget"), [], 0, "low", None, runtime=rt)
    assert out[0].checklist == ["default text"]


def test_checklist_by_validation_note(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_vn
            title: validation-note conditioned
            priority: medium
            fix_type: config
            applies_when:
              - { factor_id: ci_workflows }
            checklist:
              - text: "Confirm checks pass."
                by_validation_note: "Validation note present; confirm checks pass."
              - "Static second line."
    """)
    out = compute_required_actions(
        Signals(), _fac("ci_workflows"), [], 0, "low", None, runtime=rt
    )
    assert out[0].checklist[0] == "Confirm checks pass."
    s = Signals(validation_note_found=True)
    out = compute_required_actions(s, _fac("ci_workflows"), [], 0, "low", None, runtime=rt)
    assert out[0].checklist[0] == "Validation note present; confirm checks pass."
    assert out[0].checklist[1] == "Static second line."


# ---------------------------------------------------------------------------
# Validation lines come from the runtime gate registry.

def test_required_validations_pulls_from_runtime_gates(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_val
            title: t
            priority: high
            fix_type: test
            applies_when:
              - { factor_id: f }
            validation_line: "test: my_custom_validation"
            checklist: ["x"]
    """)
    # Build a RequiredAction from compute_required_actions (it'll have id g_val).
    actions = compute_required_actions(Signals(), _fac("f"), [], 0, "low", None, runtime=rt)
    out = compute_required_validations(Signals(), actions, runtime=rt)
    # CI baseline + my_custom_validation.
    assert any("my_custom_validation" in line for line in out)
    # Non-runtime-known action → no validation line for it.
    actions = [RequiredAction(id="unknown_action", title="x")]
    out = compute_required_validations(Signals(), actions, runtime=rt)
    assert not any("unknown_action" in line for line in out)
    assert not any("my_custom_validation" in line for line in out)


# ---------------------------------------------------------------------------
# Priority comes from the runtime gate registry, not a hardcoded set.

def test_priority_comes_from_runtime(tmp_path: Path) -> None:
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_high
            title: t
            priority: high
            fix_type: test
            applies_when:
              - { factor_id: a }
          - id: g_supp
            title: t
            priority: supporting
            fix_type: process
            applies_when:
              - { factor_id: b }
    """)
    out = compute_required_actions(
        Signals(), _fac("a", "b"), [], 0, "low", None, runtime=rt,
    )
    # Sorted high → supporting.
    assert [a.id for a in out] == ["g_high", "g_supp"]
    assert out[0].priority == "high"
    assert out[1].priority == "supporting"
