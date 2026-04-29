"""Filesystem and git helpers for the readiness evaluate CLI."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Optional


def read_json(path: Path) -> Optional[dict[str, Any]]:
    """Return parsed JSON or ``{\"_parse_error\": ...}`` / ``None`` when missing."""
    if not path or not path.is_file():
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {"_parse_error": "root must be an object"}
    except (json.JSONDecodeError, OSError) as e:
        return {"_parse_error": str(e)}


def load_yaml_config(path: Path) -> dict[str, Any]:
    import yaml

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {path}")
    return data


def git_commit_messages(repo_root: Path, base_ref: str) -> list[str]:
    """Return all lines from commit messages in ``base_ref...HEAD``."""
    try:
        r = subprocess.run(
            ["git", "-C", str(repo_root), "log", "--format=%B", f"{base_ref}...HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode != 0:
            return []
        return r.stdout.splitlines()
    except OSError:
        return []


def detect_validation_note(lines: list[str]) -> tuple[bool, str]:
    """Return ``(found, snippet)`` for the first ``Validation:`` / ``Validate:`` line."""
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if lower.startswith("validation:") or lower.startswith("validate:"):
            return True, stripped[:120]
    return False, ""


def git_changed_files(repo_root: Path, base_ref: str) -> list[str]:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo_root), "diff", "--name-only", f"{base_ref}...HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if r.returncode != 0:
            r = subprocess.run(
                ["git", "-C", str(repo_root), "diff", "--name-only", base_ref],
                capture_output=True,
                text=True,
                check=False,
            )
        if r.returncode != 0:
            return []
        return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    except OSError:
        return []
