"""Path classification (config-driven).

Determines the primary domain a changed file belongs to via the
``PRRiskRuntime`` classifier and identifies test, config, and migration paths.

Domain mapping is now config-driven: the classifier walks
``runtime.config.domains`` in declared order and returns the first domain whose
patterns match. The ``DOMAIN_*`` string constants live in ``types.py`` for
backward-compat callers but are not the primary registry — adopters configure
domains in ``ops/release-readiness/pr-risk-config.yaml``.

The generic helpers (``is_test_path``, ``is_e2e_path``, ``is_untestable_path``,
``is_config_path``, ``is_migration_path``) stay in code: they are language /
framework detection, not project policy.
"""

from __future__ import annotations

import functools
import os.path
from typing import Optional

from release_readiness_core.pr_risk.types import DOMAIN_OTHER, DOMAIN_TESTS, Signals


@functools.lru_cache(maxsize=1)
def _default_runtime():
    """Return a memoized bundled-default ``PRRiskRuntime``.

    Lazily constructed so that callers who pass an explicit ``runtime=`` never
    pay the construction cost. Importing here (rather than at module top) avoids
    a circular import: ``_runtime.py`` lazy-imports ``is_test_path`` from this
    module for ``classify`` calls.
    """
    from release_readiness_core.pr_risk._runtime import PRRiskRuntime

    return PRRiskRuntime.from_default()


def classify_domain(path: str, *, runtime=None) -> str:
    """Return one primary domain for a repo-relative path.

    ``runtime`` is optional; defaults to the bundled-default ``PRRiskRuntime``
    (mirrors today's hardcoded behavior). Adopters drive a custom config via
    ``runtime=PRRiskRuntime.from_config(...)``.
    """
    if is_test_path(path):
        return DOMAIN_TESTS
    if runtime is None:
        runtime = _default_runtime()
    return runtime.classify_area(path)


def classify_area(path: str, *, runtime=None) -> str:
    """Return the product-area label for a path (ignores test detection)."""
    if runtime is None:
        runtime = _default_runtime()
    return runtime.classify_area(path)


def is_test_path(path: str) -> bool:
    """Return True if the path is test-only or test-heavy."""
    p = path.replace("\\", "/").lower()
    if p == "":
        return False
    if p.endswith("_test.go"):
        return True
    if "/testdata/" in p:
        return True
    if "/e2e/" in p or "playwright" in p:
        return True
    if p.endswith(".spec.ts") or p.endswith(".spec.tsx"):
        return True
    if (
        "__tests__/" in p
        or ".test.ts" in p
        or ".test.tsx" in p
        or ".test.js" in p
        or ".test.jsx" in p
    ):
        return True
    return False


def is_e2e_path(path: str) -> bool:
    """Detect Playwright E2E specs."""
    p = path.replace("\\", "/").lower()
    if "web/tests/e2e/" in p:
        return True
    if "/e2e/" in p and (
        p.endswith(".e2e.ts")
        or p.endswith(".e2e.tsx")
        or p.endswith(".spec.ts")
        or p.endswith(".spec.tsx")
    ):
        return True
    return False


def is_untestable_path(path: str) -> bool:
    """Return True for file types with no conventional co-located tests."""
    p = path.replace("\\", "/").lower()
    _, ext = os.path.splitext(p)
    if ext in {".yml", ".yaml", ".sh", ".bash", ".md", ".lock", ".sum"}:
        return True
    base = os.path.basename(p)
    if base in {
        "makefile",
        "dockerfile",
        ".gitignore",
        ".gitattributes",
        ".dockerignore",
        ".editorconfig",
    }:
        return True
    return False


def is_config_path(path: str) -> bool:
    """Return True for CI / deploy / config paths."""
    p = path.replace("\\", "/").lower()
    if p.startswith(".github/"):
        return True
    if p.startswith("deploy/"):
        return True
    if p == "go.mod" or p == "go.sum":
        return True
    if p.endswith("dockerfile") or p == "dockerfile":
        return True
    if p.endswith("render.yaml"):
        return True
    return False


def is_migration_path(path: str) -> bool:
    """Return True for SQL migration paths."""
    p = path.replace("\\", "/").lower()
    return p.startswith("db/migrations/") or p.startswith("internal/migrations/")


def touches_sensitive_code_without_tests(s: Signals, *, runtime=None) -> bool:
    """Non-test code in risky areas with zero test file changes.

    "Sensitive areas" are defined by ``runtime.sensitive_domains`` (config-driven
    as of Phase 2). Defaults to the bundled set when no runtime is passed.
    """
    if s.test_files > 0:
        return False
    if runtime is None:
        runtime = _default_runtime()
    sensitive = set(runtime.sensitive_domains)
    for f in s.files:
        if is_test_path(f.path):
            continue
        if classify_domain(f.path, runtime=runtime) in sensitive:
            return True
    return False
