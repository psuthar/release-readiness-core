"""Filesystem and git helpers for the readiness evaluate CLI."""

from __future__ import annotations

import difflib
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


# top-level keys recognized by the engine. Loading a config with
# any other top-level key raises ConfigSchemaError with a typo suggestion.
# Update this set when adding a new top-level config field.
KNOWN_TOP_LEVEL_CONFIG_KEYS: frozenset[str] = frozenset({
    "version",
    "validations",
    "evidence_boolean_keys",
    "infer_validations_when_pass",
    "risk_category_to_required_validation",
    "risk_from_paths",
    "risky_config_patterns",
    "scoring",
    "remediation",
    "e2e_critical_name_patterns",
    "optional_artifacts",
    # Legacy / extension fields that pass through without engine semantics.
    "report_title",
    "pr_risk",
})


# Minimum type expected for the top-level keys we know about.
_EXPECTED_TYPES: dict[str, type] = {
    "version": int,
    "validations": dict,
    "evidence_boolean_keys": list,
    "infer_validations_when_pass": dict,
    "risk_category_to_required_validation": dict,
    "risk_from_paths": list,
    "risky_config_patterns": list,
    "scoring": dict,
    "remediation": dict,
    "e2e_critical_name_patterns": list,
    "optional_artifacts": list,
}


class ConfigSchemaError(ValueError):
    """Raised when the loaded config has a top-level key the engine doesn't know."""


def _validate_config(data: dict[str, Any], path: Path) -> None:
    """catch top-level typos and obvious type errors at load time.

    The contracts schema under ``docs/contracts/`` is intentionally permissive
    (``additionalProperties: true``) so adopters can extend with their own
    metadata. That means a misspelled engine key like ``infer_validations_when_pas``
    would otherwise be silently ignored. This validator enforces a closed set
    of known top-level keys and surfaces a "did you mean" suggestion when one
    is close.
    """
    unknown = sorted(set(data.keys()) - KNOWN_TOP_LEVEL_CONFIG_KEYS)
    if unknown:
        suggestions: list[str] = []
        for key in unknown:
            close = difflib.get_close_matches(key, KNOWN_TOP_LEVEL_CONFIG_KEYS, n=1, cutoff=0.7)
            if close:
                suggestions.append(f"  - {key!r}  (did you mean {close[0]!r}?)")
            else:
                suggestions.append(f"  - {key!r}")
        raise ConfigSchemaError(
            f"Unknown top-level key(s) in config {path}:\n"
            + "\n".join(suggestions)
            + "\n\nKnown keys: "
            + ", ".join(sorted(KNOWN_TOP_LEVEL_CONFIG_KEYS))
        )

    type_errors: list[str] = []
    for key, expected in _EXPECTED_TYPES.items():
        if key in data and not isinstance(data[key], expected):
            type_errors.append(
                f"  - {key!r}: expected {expected.__name__}, got {type(data[key]).__name__}"
            )
    if type_errors:
        raise ConfigSchemaError(
            f"Type mismatch in config {path}:\n" + "\n".join(type_errors)
        )


def load_yaml_config(path: Path) -> dict[str, Any]:
    import yaml

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Config root must be a mapping: {path}")
    _validate_config(data, path)
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
