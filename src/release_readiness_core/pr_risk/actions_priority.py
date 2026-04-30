"""Action priority lookups + sort.

Priority for a gate id comes from ``runtime.config.gates[i].priority`` now,
not the hardcoded ``_HIGH/_MEDIUM/_SUPPORTING`` sets that previously lived
here. ``sort_required_actions`` keeps its public signature (pure logic, not
data).
"""

from __future__ import annotations

from typing import List, TYPE_CHECKING

from release_readiness_core.pr_risk.types import RequiredAction

if TYPE_CHECKING:
    from release_readiness_core.pr_risk._runtime import PRRiskRuntime


PRIORITY_HIGH = "high"
PRIORITY_MEDIUM = "medium"
PRIORITY_SUPPORTING = "supporting"


def priority_for_action_id(action_id: str, *, runtime=None) -> str:
    """Map action ID to priority tier from the runtime gate registry.

    Falls back to ``"medium"`` for unknown ids (matches the prior hardcoded
    fallback in this module).
    """
    runtime = runtime or _default_runtime()
    return runtime.priority_for(action_id)


_RANK = {PRIORITY_HIGH: 0, PRIORITY_MEDIUM: 1, PRIORITY_SUPPORTING: 2}


def sort_required_actions(
    actions: List[RequiredAction], *, runtime: "PRRiskRuntime | None" = None
) -> List[RequiredAction]:
    """Order actions high → medium → supporting, then by ID. Stable sort."""
    if len(actions) <= 1:
        return list(actions)

    runtime = runtime or _default_runtime()

    def key(a: RequiredAction):
        prio = a.priority or runtime.priority_for(a.id)
        return (_RANK.get(prio, 2), a.id)

    return sorted(actions, key=key)


def _default_runtime():
    from release_readiness_core.pr_risk.classify import _default_runtime as _rt

    return _rt()
