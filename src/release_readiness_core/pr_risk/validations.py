"""Required validation lines — config-driven.

The hardcoded ``_VALIDATION_FOR_ACTION`` map is gone; validation lines come
from ``runtime.gates[i].validation_line`` now. This module shrinks to just the
deduplication + ordering logic plus the CI-baseline / validation-note pair.
"""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from release_readiness_core.pr_risk.types import RequiredAction, Signals

if TYPE_CHECKING:
    from release_readiness_core.pr_risk._runtime import PRRiskRuntime


def validation_for_action(action_id: str, *, runtime=None) -> Optional[str]:
    """Return the configured ``validation_line`` for a gate id, or ``None``."""
    runtime = runtime or _default_runtime()
    for g in runtime.gates:
        if g.id == action_id:
            return g.validation_line or None
    return None


def compute_required_validations(
    s: Signals,
    actions: List[RequiredAction],
    *,
    runtime: Optional["PRRiskRuntime"] = None,
) -> List[str]:
    """Build the deterministic ordered list of validation lines."""
    runtime = runtime or _default_runtime()
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

    if s.git_error == "":
        add("ci: required status checks must pass before merge")
    else:
        add("ci: restore reliable git diff before merge (see git error in report)")

    val_map = {g.id: g.validation_line for g in runtime.gates if g.validation_line}
    for a in actions:
        line = val_map.get(a.id)
        if line:
            add(line)

    if s.validation_note_found:
        add("process: validation note present in commit — confirm it matches what was run")

    return out


def _default_runtime():
    from release_readiness_core.pr_risk.classify import _default_runtime as _rt

    return _rt()
