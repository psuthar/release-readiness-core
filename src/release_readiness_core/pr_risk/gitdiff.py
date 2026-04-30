"""Git diff parsing (port of internal/prrisk/gitdiff.go).

Shells out to git via subprocess. The four git invocations mirror Go exactly:
  git -C <root> rev-parse --symbolic-full-name HEAD
  git -C <root> diff --numstat <base>...HEAD
  git -C <root> diff --numstat <base>            (fallback)
  git -C <root> log  --format=%B <base>...HEAD   (commit-message scan)
"""

from __future__ import annotations

import os.path
import subprocess
from typing import List, Tuple

from release_readiness_core.pr_risk.classify import (
    classify_area,
    classify_domain,
    is_config_path,
    is_e2e_path,
    is_migration_path,
    is_test_path,
)
from release_readiness_core.pr_risk.types import FileChange, Signals


def _run(args: List[str]) -> Tuple[str, str, int]:
    """Run a git command, return (stdout, stderr, returncode). Never raises."""
    res = subprocess.run(
        args,
        capture_output=True,
        text=True,
        check=False,
    )
    return res.stdout, res.stderr, res.returncode


def head_ref(repo_root: str) -> str:
    """Return symbolic HEAD or 'HEAD' on error."""
    out, _err, rc = _run(["git", "-C", repo_root, "rev-parse", "--symbolic-full-name", "HEAD"])
    if rc != 0:
        return "HEAD"
    s = out.strip()
    return s if s else "HEAD"


def diff_numstat(repo_root: str, base_ref: str) -> Tuple[List[FileChange], str]:
    """Return (files, error_message). Mirrors Go DiffNumstat exactly."""
    out, err, rc = _run(["git", "-C", repo_root, "diff", "--numstat", f"{base_ref}...HEAD"])
    if rc != 0:
        out, err, rc = _run(["git", "-C", repo_root, "diff", "--numstat", base_ref])
        if rc != 0:
            msg = err.strip()
            if msg == "":
                msg = f"git diff failed (rc={rc})"
            return [], msg

    files: List[FileChange] = []
    for line in out.strip().split("\n"):
        if line == "":
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        added = 0
        deleted = 0
        if parts[0] != "-":
            try:
                added = int(parts[0])
            except ValueError:
                added = 0
        if parts[1] != "-":
            try:
                deleted = int(parts[1])
            except ValueError:
                deleted = 0
        path = parts[2].strip()
        # Handle rename "path => newpath".
        idx = path.rfind("\t")
        if idx >= 0:
            path = path[idx + 1 :].strip()
        path = path.replace("\\", "/")
        files.append(FileChange(path=path, added=added, deleted=deleted))
    return files, ""


def detect_validation_note(repo_root: str, base_ref: str) -> Tuple[bool, str]:
    """Scan commit messages for a 'Validation:' or 'Validate:' prefix line."""
    return _detect_commit_prefix(
        repo_root, base_ref, ("validation:", "validate:")
    )


def detect_style_only_note(repo_root: str, base_ref: str) -> Tuple[bool, str]:
    """Scan commit messages for a 'Style-only:' or 'Style only:' prefix line."""
    return _detect_commit_prefix(
        repo_root, base_ref, ("style-only:", "style only:")
    )


def _detect_commit_prefix(
    repo_root: str, base_ref: str, prefixes: Tuple[str, ...]
) -> Tuple[bool, str]:
    out, _err, rc = _run(
        ["git", "-C", repo_root, "log", "--format=%B", f"{base_ref}...HEAD"]
    )
    if rc != 0:
        return False, ""
    for line in out.split("\n"):
        stripped = line.strip()
        if stripped == "":
            continue
        lower = stripped.lower()
        for prefix in prefixes:
            if lower.startswith(prefix):
                if len(stripped) > 120:
                    return True, stripped[:120]
                return True, stripped
    return False, ""


def extract_signals(repo_root: str, base_ref: str) -> Signals:
    """Build Signals from git diff. Mirrors Go ExtractSignals."""
    repo_root = os.path.normpath(repo_root)
    files, git_err = diff_numstat(repo_root, base_ref)

    val_found, val_snippet = detect_validation_note(repo_root, base_ref)
    style_only, style_snippet = detect_style_only_note(repo_root, base_ref)

    s = Signals(
        repo_root=repo_root,
        base_ref=base_ref,
        head_ref=head_ref(repo_root),
        files=files,
        git_error=git_err,
        validation_note_found=val_found,
        validation_note_snippet=val_snippet,
        style_only_note_found=style_only,
        style_only_note_snippet=style_snippet,
    )

    for f in files:
        s.file_count += 1
        s.total_added += f.added
        s.total_deleted += f.deleted
        d = classify_domain(f.path)
        s.domain_hits[d] = s.domain_hits.get(d, 0) + 1
        if is_test_path(f.path):
            s.test_files += 1
            td = classify_area(f.path)
            s.test_domain_hits[td] = s.test_domain_hits.get(td, 0) + 1
            if is_e2e_path(f.path):
                s.e2e_test_files += 1
                s.test_e2e_domain_hits[td] = s.test_e2e_domain_hits.get(td, 0) + 1
            else:
                s.unit_test_files += 1
                s.test_unit_domain_hits[td] = s.test_unit_domain_hits.get(td, 0) + 1
        if is_config_path(f.path):
            s.config_files += 1
        if is_migration_path(f.path):
            s.migration_files += 1

    s.total_loc = s.total_added + s.total_deleted
    if s.total_loc > 0 and s.test_files > 0:
        test_loc = sum(f.added + f.deleted for f in files if is_test_path(f.path))
        s.test_loc_ratio = test_loc / s.total_loc
    return s
