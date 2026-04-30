"""PR Risk runtime skeleton (SCRUM-239 / Phase 1 of SCRUM-238).

A ``PRRiskRuntime`` carries the loaded ``PRRiskConfig`` plus lazily-compiled
artifacts that Phases 2-4 will use:

- Phase 2: a compiled ``Classifier`` that turns the config's ``domains`` list
  into ``classify_domain(path)`` / ``classify_area(path)`` lookups.
- Phase 3: a gate registry that loops over ``runtime.gates`` evaluating each
  gate's ``applies_when`` predicates.
- Phase 4: an evidence-detector resolver that compiles each gate's
  ``evidence: { template, args }`` block into a callable.

This module ships only the skeleton: ``from_default()`` returns a runtime
whose config mirrors today's hardcoded behavior; ``from_config(path)`` loads
from a YAML file. The classify / gates / detector accessors are stubs that
Phases 2-4 fill in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from release_readiness_core.pr_risk._config import (
    Gate,
    PRRiskConfig,
    load_pr_risk_config,
)
from release_readiness_core.pr_risk._default_config import default_pr_risk_config


@dataclass
class PRRiskRuntime:
    """Loaded config + lazily-compiled per-runtime artifacts.

    Phase 1 only exposes ``config`` and ``register_detector``. The remaining
    accessors are stubs that raise ``NotImplementedError`` so that any caller
    threading a runtime through before its phase is wired in fails loudly
    rather than silently using stale defaults.
    """

    config: PRRiskConfig
    _custom_detectors: Dict[str, Callable[..., Any]] = field(default_factory=dict)

    @classmethod
    def from_default(cls) -> "PRRiskRuntime":
        """Construct a runtime whose config mirrors today's hardcoded values."""
        return cls(config=default_pr_risk_config())

    @classmethod
    def from_config(cls, path: str | Path) -> "PRRiskRuntime":
        """Construct a runtime from a YAML config file."""
        return cls(config=load_pr_risk_config(path))

    # ------------------------------------------------------------------
    # Phase 2 (classifier).

    @property
    def domains(self) -> List[Any]:
        """Convenience accessor for ``config.domains``."""
        return list(self.config.domains)

    @property
    def sensitive_domains(self) -> List[str]:
        """Convenience accessor for ``config.sensitive_domains``."""
        return list(self.config.sensitive_domains)

    def classify(self, path: str) -> str:  # noqa: ARG002 - Phase 2 fills this in.
        """Return the domain id for a path. Stub until Phase 2 (SCRUM-240)."""
        raise NotImplementedError(
            "PRRiskRuntime.classify is not wired in yet (Phase 2 / SCRUM-240)"
        )

    # ------------------------------------------------------------------
    # Phase 3 (gate registry).

    @property
    def gates(self) -> List[Gate]:
        """Convenience accessor for ``config.gates``."""
        return list(self.config.gates)

    def priority_for(self, action_id: str) -> str:
        """Return the priority string for a gate id from the loaded config.
        Falls back to ``'medium'`` for unknown ids (matches today's behavior
        in ``actions_priority.priority_for_action_id``)."""
        for g in self.config.gates:
            if g.id == action_id:
                return g.priority
        return "medium"

    # ------------------------------------------------------------------
    # Phase 4 (evidence detectors).

    def detector_for(self, action_id: str) -> Callable[..., Any]:  # noqa: ARG002
        """Return the compiled evidence detector callable for a gate id.
        Stub until Phase 4 (SCRUM-242)."""
        raise NotImplementedError(
            "PRRiskRuntime.detector_for is not wired in yet (Phase 4 / SCRUM-242)"
        )

    def register_detector(self, template_name: str, fn: Callable[..., Any]) -> None:
        """Programmatic escape hatch for adopters who need a custom detector
        template that isn't in the closed set. Phase 4 (SCRUM-242) consumes
        the registered callable. Stored on the runtime instance only."""
        if not isinstance(template_name, str) or not template_name:
            raise ValueError("template_name must be a non-empty string")
        if not callable(fn):
            raise TypeError("fn must be callable")
        self._custom_detectors[template_name] = fn
