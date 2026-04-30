"""Tiny private helpers shared by floors, score, etc.

These mirror small Go-side helpers from internal/prrisk that need to be
available to multiple ports. Kept private (leading underscore) — public API
exposes them through their parent module's domain (e.g. score.clamp_100
will be re-exported when Phase 3 lands).
"""

from __future__ import annotations

from typing import Iterable, Mapping


def clamp_100(x: float) -> float:
    """Clamp x to [0, 100]. Mirrors Go score.go::clamp100."""
    if x < 0:
        return 0.0
    if x > 100:
        return 100.0
    return float(x)


def factor_ids(factors: Iterable) -> set:
    """Return a set of factor IDs. Mirrors Go reducers.go::factorIDs."""
    return {f.id for f in factors}


def ok_bool(has: Mapping | set, key: str) -> bool:
    """Return whether key is present. Mirrors Go reducers.go::okBool."""
    return key in has


def max_float(a: float, b: float) -> float:
    """Mirrors Go floors.go::maxFloat."""
    return a if a > b else b
