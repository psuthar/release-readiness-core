"""Bridge between prrisk.Signals and the context subpackage's Input.

Mirrors internal/prrisk/context_bridge.go. Reads PRRISK_PR_TITLE and
PRRISK_PR_BODY env vars exactly like Go.
"""

from __future__ import annotations

import os

from release_readiness_core.pr_risk.classify import is_test_path, is_untestable_path
from release_readiness_core.pr_risk.context.input import FileChange as CtxFile, Input
from release_readiness_core.pr_risk.context.types import Weights as CtxWeights
from release_readiness_core.pr_risk.types import ScoreWeights, Signals


def context_input_from_signals(s: Signals, *, runtime=None) -> Input:
    """Build a context-analysis ``Input`` from prrisk Signals.

    ``runtime`` is accepted for forward-compat: ``is_test_path`` and
    ``is_untestable_path`` are language heuristics that don't need it today,
    but later phases may thread it for adopter-specific overrides.
    """
    del runtime  # Phase 2 / language heuristics — no runtime needed.
    files = [CtxFile(path=f.path, added=f.added, deleted=f.deleted) for f in s.files]
    is_test = [is_test_path(f.path) for f in s.files]
    is_untestable = [is_untestable_path(f.path) for f in s.files]
    title = os.environ.get("PRRISK_PR_TITLE", "")
    body = os.environ.get("PRRISK_PR_BODY", "")
    return Input(
        repo_root=s.repo_root,
        git_error=s.git_error,
        files=files,
        is_test=is_test,
        is_untestable=is_untestable,
        domain_hits=dict(s.domain_hits),
        test_unit_domain_hits=dict(s.test_unit_domain_hits),
        test_e2e_domain_hits=dict(s.test_e2e_domain_hits),
        pr_title=title,
        pr_body=body,
    )


def risk_context_weights(w: ScoreWeights) -> CtxWeights:
    return CtxWeights(
        proximity_low_points=w.context_proximity_low_points,
        scattered_points=w.context_scattered_points,
        hotspot_points=w.context_hotspot_points,
        intent_mismatch_points=w.context_intent_mismatch_points,
    )
