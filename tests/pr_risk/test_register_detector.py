"""Custom-detector escape hatch tests (Phase 4).

Adopters with detector logic that doesn't fit the closed-set templates use
``PRRiskRuntime.register_detector(template_name, fn)``. The runtime resolves
the registered callable when a gate's ``evidence.template`` references that
name.
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from release_readiness_core.pr_risk._runtime import PRRiskRuntime
from release_readiness_core.pr_risk.evidence import (
    compute_evidence_status,
    evidence_for_action_id,
)
from release_readiness_core.pr_risk.types import (
    EVIDENCE_FAIL,
    EVIDENCE_PASS,
    RequiredAction,
    Result,
    Signals,
    ValidationEvidence,
)


def _runtime(tmp_path: Path, body: str) -> PRRiskRuntime:
    p = tmp_path / "pr-risk-config.yaml"
    p.write_text(dedent(body).lstrip(), encoding="utf-8")
    return PRRiskRuntime.from_config(p)


# ---------------------------------------------------------------------------

def test_register_detector_overrides_builtin(tmp_path: Path) -> None:
    """Registering a callable under an existing template name takes
    precedence over the built-in for that template, on this runtime only."""
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_signal
            title: signal gate
            priority: high
            fix_type: infra
            applies_when:
              - { factor_id: x }
            checklist: ["x"]
            evidence:
              template: signal_check
              args: { signal_field: git_error }
    """)

    def custom(action_id: str, label: str, args, r: Result) -> ValidationEvidence:
        return ValidationEvidence(
            id=action_id, label=label,
            status=EVIDENCE_FAIL, source="custom",
            rationale=f"custom override for {args.get('signal_field')}",
        )

    rt.register_detector("signal_check", custom)
    detector = rt.detector_for("g_signal")
    r = Result(signals=Signals())  # git_error empty → built-in would say PASS
    ev = detector("My Label", r)
    assert ev.status == EVIDENCE_FAIL
    assert ev.source == "custom"
    assert "custom override for git_error" in ev.rationale


def test_register_detector_for_new_template(tmp_path: Path) -> None:
    """Schema's closed-set enum prevents authoring a config with an unknown
    template — register_detector is for adopters who fork the closed set
    in their own runtime, then load a config that uses the new name. We
    simulate this by parsing then mutating the config (loader rejects unknown
    template names by design)."""
    # Load a config with a known template, then swap to a custom template name.
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_x
            title: t
            priority: medium
            fix_type: process
            applies_when:
              - { factor_id: f }
            checklist: ["x"]
            evidence:
              template: hotspot
    """)
    # Replace the in-memory gate's evidence with a custom template name
    # (bypassing the loader's closed-set check, which is what an adopter does
    # in a forked runtime when shipping a new template).
    from dataclasses import replace
    from release_readiness_core.pr_risk._config import GateEvidence

    new_gate = replace(rt.config.gates[0], evidence=GateEvidence(template="my_custom"))
    rt.config.gates[0] = new_gate  # type: ignore[index]

    # Without registration, detector_for raises.
    with pytest.raises(ValueError, match="Unknown evidence template"):
        rt.detector_for("g_x")

    # Register it and now it resolves.
    def custom(action_id, label, args, r):
        return ValidationEvidence(
            id=action_id, label=label, status=EVIDENCE_PASS,
            source="custom", rationale="custom OK",
        )

    rt.register_detector("my_custom", custom)
    detector = rt.detector_for("g_x")
    ev = detector("L", Result(signals=Signals()))
    assert ev.status == EVIDENCE_PASS
    assert ev.source == "custom"


def test_register_detector_arg_validation() -> None:
    rt = PRRiskRuntime.from_default()
    with pytest.raises(ValueError):
        rt.register_detector("", lambda a, l, ar, r: None)
    with pytest.raises(TypeError):
        rt.register_detector("custom", "not-callable")  # type: ignore[arg-type]


def test_compute_evidence_status_uses_custom_detector(tmp_path: Path) -> None:
    """End-to-end: gate fires, custom detector resolves, evidence appears
    in compute_evidence_status output for that gate."""
    rt = _runtime(tmp_path, """
        version: 1
        gates:
          - id: g_custom
            title: custom gate
            priority: high
            fix_type: process
            applies_when:
              - { factor_id: x }
            checklist: ["x"]
            evidence:
              template: signal_check
              args: { signal_field: git_error }
    """)

    def custom(action_id, label, args, r):
        return ValidationEvidence(
            id=action_id, label=label,
            status=EVIDENCE_PASS, source="custom",
            rationale="custom OK",
        )

    rt.register_detector("signal_check", custom)

    r = Result(
        signals=Signals(),
        required_actions=[RequiredAction(id="g_custom", title="custom gate")],
    )
    out, _summary = compute_evidence_status(r, runtime=rt)
    g_custom = next(ev for ev in out if ev.id == "g_custom")
    assert g_custom.source == "custom"
    assert g_custom.status == EVIDENCE_PASS
