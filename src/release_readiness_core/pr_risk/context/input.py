"""Context Input dataclasses (port of internal/prrisk/context/input.go).

Mirrors the Go package boundary: FileChange and Input are minimal types,
intentionally not importing from the parent package to avoid cycles.
Callers (e.g. _context_bridge in pr_risk root) construct Input from
prrisk.Signals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class FileChange:
    path: str = ""
    added: int = 0
    deleted: int = 0


@dataclass
class Input:
    repo_root: str = ""
    git_error: str = ""
    files: List[FileChange] = field(default_factory=list)
    is_test: List[bool] = field(default_factory=list)
    is_untestable: List[bool] = field(default_factory=list)
    domain_hits: Dict[str, int] = field(default_factory=dict)
    test_unit_domain_hits: Dict[str, int] = field(default_factory=dict)
    test_e2e_domain_hits: Dict[str, int] = field(default_factory=dict)
    pr_title: str = ""
    pr_body: str = ""
