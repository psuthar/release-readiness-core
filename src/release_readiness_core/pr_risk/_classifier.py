"""Config-driven path classifier.

Compiles a ``PRRiskConfig`` into a path-to-domain lookup. Replaces the hardcoded
switch in the previous ``classify.classify_area`` implementation. The first
``Domain`` (in declared order) whose patterns match wins; falls back to
``"other"`` when no domain matches.

Pattern compilation supports the closed set ``prefix``, ``contains``, ``exact``,
``endswith``, ``any_contains``, and ``and`` (recursive). Iteration follows
declared order to mirror today's switch order.

Test detection (``is_test_path``) is a language/framework heuristic that lives
in ``classify.py`` and stays in code; Phase 2 only moves the project-policy
domain mapping into config.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

from release_readiness_core.pr_risk._config import (
    Domain,
    PATH_PATTERN_KEYS,
    PRRiskConfig,
)


def _to_slash(path: str) -> str:
    """Mirror filepath.ToSlash: convert backslash separators to forward slashes."""
    return path.replace("\\", "/")


class Classifier:
    """Compiled domain classifier built once per ``PRRiskConfig``."""

    __slots__ = ("_config", "_domains")

    def __init__(self, config: PRRiskConfig):
        self._config = config
        # Materialize once; patterns are stored as plain dicts in the dataclass
        # so no further compilation is required.
        self._domains: List[Domain] = list(config.domains)

    @property
    def config(self) -> PRRiskConfig:
        return self._config

    def classify_area(self, path: str) -> str:
        """Return the product-area domain id for ``path`` (ignores test detection)."""
        p = _to_slash(path.strip()).lower()
        if p == "":
            return "other"
        for domain in self._domains:
            if self._match_patterns(domain.patterns, p):
                return domain.id
        return "other"

    # ------------------------------------------------------------------
    # Pattern matching (recursive for ``and``).

    def _match_patterns(self, patterns: Iterable[Dict[str, Any]], p: str) -> bool:
        for pat in patterns:
            if self._match_one(pat, p):
                return True
        return False

    def _match_one(self, pat: Dict[str, Any], p: str) -> bool:
        # The loader already validated that exactly one primary key is present;
        # check each in order so the first match short-circuits.
        if "prefix" in pat:
            return p.startswith(pat["prefix"])
        if "contains" in pat:
            return pat["contains"] in p
        if "exact" in pat:
            return p == pat["exact"]
        if "endswith" in pat:
            return p.endswith(pat["endswith"])
        if "any_contains" in pat:
            return any(s in p for s in pat["any_contains"])
        if "and" in pat:
            for sub in pat["and"]:
                if not self._match_one(sub, p):
                    return False
            return True
        # Loader-validated input should never reach here.
        return False
