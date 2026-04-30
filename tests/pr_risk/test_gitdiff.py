"""Tests for pr_risk.gitdiff against synthetic git repos."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from release_readiness_core.pr_risk.gitdiff import (
    detect_style_only_note,
    detect_validation_note,
    diff_numstat,
    extract_signals,
    head_ref,
)


def _git(repo: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "--initial-branch=main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")


def _commit(repo: Path, msg: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", msg, "--allow-empty")
    return _git(repo, "rev-parse", "HEAD").strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    _init_repo(r)
    (r / "README.md").write_text("hello\n")
    _commit(r, "initial")
    return r


def test_head_ref_returns_main(repo: Path) -> None:
    assert head_ref(str(repo)) in {"refs/heads/main", "HEAD"}


def test_head_ref_handles_missing_repo(tmp_path: Path) -> None:
    # Pointing at a non-git dir should fall back to "HEAD" rather than raise.
    assert head_ref(str(tmp_path / "nope")) == "HEAD"


def test_diff_numstat_empty_when_no_changes(repo: Path) -> None:
    files, err = diff_numstat(str(repo), "HEAD")
    assert files == []
    assert err == ""


def test_diff_numstat_picks_up_added_file(repo: Path) -> None:
    base = _git(repo, "rev-parse", "HEAD").strip()
    (repo / "internal" / "foo").mkdir(parents=True)
    (repo / "internal" / "foo" / "bar.go").write_text("package foo\n\nfunc Bar() {}\n")
    _commit(repo, "add bar")
    files, err = diff_numstat(str(repo), base)
    assert err == ""
    assert len(files) == 1
    assert files[0].path == "internal/foo/bar.go"
    assert files[0].added == 3
    assert files[0].deleted == 0


def test_diff_numstat_handles_added_and_deleted_lines(repo: Path) -> None:
    (repo / "x.txt").write_text("line1\nline2\n")
    base = _commit(repo, "add x")
    (repo / "x.txt").write_text("line1\nNEW\nline3\n")
    _commit(repo, "edit x")
    files, err = diff_numstat(str(repo), base)
    assert err == ""
    assert len(files) == 1
    assert files[0].added == 2
    assert files[0].deleted == 1


def test_diff_numstat_returns_error_on_invalid_ref(repo: Path) -> None:
    files, err = diff_numstat(str(repo), "notarealref")
    assert files == []
    assert err != ""


def test_detect_validation_note_finds_prefix(repo: Path) -> None:
    base = _git(repo, "rev-parse", "HEAD").strip()
    (repo / "x.txt").write_text("x\n")
    _commit(repo, "feat: add x\n\nValidation: ran go test ./internal/foo")
    found, snippet = detect_validation_note(str(repo), base)
    assert found is True
    assert snippet.lower().startswith("validation:")


def test_detect_validation_note_truncates_long_lines(repo: Path) -> None:
    base = _git(repo, "rev-parse", "HEAD").strip()
    long_msg = "Validation: " + ("X" * 200)
    (repo / "y.txt").write_text("y\n")
    _commit(repo, f"feat: y\n\n{long_msg}")
    found, snippet = detect_validation_note(str(repo), base)
    assert found is True
    assert len(snippet) == 120


def test_detect_validation_note_absent(repo: Path) -> None:
    base = _git(repo, "rev-parse", "HEAD").strip()
    (repo / "z.txt").write_text("z\n")
    _commit(repo, "feat: z (no note)")
    found, snippet = detect_validation_note(str(repo), base)
    assert found is False
    assert snippet == ""


def test_detect_style_only_note_finds_both_variants(repo: Path) -> None:
    base = _git(repo, "rev-parse", "HEAD").strip()
    (repo / "a.css").write_text(".x { color: red; }\n")
    _commit(repo, "Style-only: red color\n")
    found, snippet = detect_style_only_note(str(repo), base)
    assert found is True
    assert "style-only" in snippet.lower()


def test_extract_signals_populates_domain_hits(repo: Path, corpus_runtime) -> None:
    base = _git(repo, "rev-parse", "HEAD").strip()
    (repo / "internal" / "auth").mkdir(parents=True)
    (repo / "internal" / "auth" / "login.go").write_text("package auth\n")
    (repo / ".github" / "workflows").mkdir(parents=True)
    (repo / ".github" / "workflows" / "ci.yml").write_text("name: CI\n")
    _commit(repo, "feat: add auth + ci")
    s = extract_signals(str(repo), base, runtime=corpus_runtime)
    assert s.file_count == 2
    assert s.git_error == ""
    assert s.domain_hits.get("auth") == 1
    assert s.domain_hits.get("workflows") == 1
    assert s.config_files == 1


def test_extract_signals_test_loc_ratio(repo: Path) -> None:
    base = _git(repo, "rev-parse", "HEAD").strip()
    (repo / "internal" / "foo").mkdir(parents=True)
    (repo / "internal" / "foo" / "bar.go").write_text("package foo\nfunc Bar() {}\n")
    (repo / "internal" / "foo" / "bar_test.go").write_text(
        "package foo\nimport \"testing\"\nfunc TestBar(t *testing.T) {}\n"
    )
    _commit(repo, "feat: add bar + test")
    s = extract_signals(str(repo), base)
    assert s.test_files == 1
    assert s.unit_test_files == 1
    assert s.test_loc_ratio > 0.0
    assert s.total_loc > 0
