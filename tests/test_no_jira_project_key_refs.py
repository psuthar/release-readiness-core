"""Regression guard: no `SCRUM-NN` Jira project-key references in package source / docs / tests.

The package brands itself as project-agnostic. Concrete `SCRUM-NN` ticket
identifiers leaking into source code, schema metadata, command-syntax
templates, or test docstrings make the package look tied to one Jira
instance. This test fails if any new such reference is added.

Excluded from the scan (intentionally):
- ``tests/pr_risk/fixtures/``  — captured upstream PR-title data, third party
- ``artifacts/``               — gitignored runtime output
- ``.epic-run/``               — gitignored epic-run state
- ``.claude/agents/``          — agent setup files, owned by the user
- this test file itself.

If you legitimately need to reference a Jira project key (e.g. in a new fixture
that ships captured upstream PR titles), put it under
``tests/pr_risk/fixtures/`` so it stays out of scope.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent

# Files / directories to skip.
SKIP_PREFIXES = (
    "tests/pr_risk/fixtures/",
    "artifacts/",
    ".epic-run/",
    ".claude/agents/",
    ".claude/scheduled_tasks.lock",
    ".git/",
)

SKIP_FILES = {
    "tests/test_no_jira_project_key_refs.py",
}

# Pattern matches a Jira ticket key like SCRUM-123. Bare "SCRUM" without a
# numeric suffix or X/x placeholder is allowed (it can refer to e.g. the
# scrum methodology), but `SCRUM-NN`, `SCRUM-XX`, and `SCRUM-xxx` are not.
PATTERN = re.compile(r"\bSCRUM-(?:\d+|[Xx]+)\b")

# File extensions to scan.
EXTS = ("py", "md", "json", "yaml", "yml", "toml")


def _scanned_files() -> list[Path]:
    out: list[Path] = []
    for ext in EXTS:
        for path in REPO_ROOT.rglob(f"*.{ext}"):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if any(rel.startswith(p) for p in SKIP_PREFIXES):
                continue
            if rel in SKIP_FILES:
                continue
            out.append(path)
    return sorted(set(out))


def test_no_scrum_project_key_references_in_package_source_or_docs():
    """No SCRUM-NN / SCRUM-XX / SCRUM-xxx tokens in package source, docs, or tests."""
    leaks: list[str] = []
    for path in _scanned_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for m in PATTERN.finditer(text):
            line_no = text.count("\n", 0, m.start()) + 1
            rel = path.relative_to(REPO_ROOT).as_posix()
            leaks.append(f"{rel}:{line_no}: {m.group(0)}")
    assert not leaks, (
        f"Found {len(leaks)} Jira project-key reference(s) in package source/docs/tests:\n  "
        + "\n  ".join(leaks)
    )
