"""Tests for pr_risk.context.hotspots."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from release_readiness_core.pr_risk.context.hotspots import (
    analyze_hotspots,
    is_git_object_id,
    prefix_commits_from_name_only_log,
)
from release_readiness_core.pr_risk.context.input import FileChange, Input


def test_is_git_object_id_accepts_sha1() -> None:
    assert is_git_object_id("a" * 40) is True
    assert is_git_object_id("0123456789abcdef0123456789abcdef01234567") is True


def test_is_git_object_id_accepts_sha256() -> None:
    assert is_git_object_id("a" * 64) is True


def test_is_git_object_id_rejects_short_long() -> None:
    assert is_git_object_id("abc") is False
    assert is_git_object_id("a" * 39) is False
    assert is_git_object_id("a" * 41) is False


def test_is_git_object_id_rejects_non_hex() -> None:
    assert is_git_object_id("z" * 40) is False


def test_prefix_commits_from_name_only_log_basic() -> None:
    log = (
        "abcdef0123456789abcdef0123456789abcdef01\n"
        "internal/auth/login.go\n"
        "internal/auth/session.go\n"
        "\n"
        "0123456789abcdef0123456789abcdef01234567\n"
        "web/src/App.tsx\n"
    )
    out = prefix_commits_from_name_only_log(log)
    assert out["internal/auth"] == 1
    assert out["web/src"] == 1


def test_prefix_commits_counts_distinct_commits_not_lines() -> None:
    log = (
        "abcdef0123456789abcdef0123456789abcdef01\n"
        "internal/auth/login.go\n"
        "internal/auth/session.go\n"
        "internal/auth/account.go\n"  # 3 lines, same prefix, 1 commit
        "0123456789abcdef0123456789abcdef01234567\n"
        "internal/auth/another.go\n"  # different commit, same prefix
    )
    out = prefix_commits_from_name_only_log(log)
    assert out["internal/auth"] == 2  # not 4


def test_prefix_commits_handles_empty_log() -> None:
    assert prefix_commits_from_name_only_log("") == {}


def test_analyze_hotspots_no_repo_returns_empty_no_skip() -> None:
    inp = Input(repo_root="", files=[])
    hotspots, skip = analyze_hotspots(inp)
    assert hotspots == []
    assert skip == ""


def test_analyze_hotspots_git_error_returns_empty_no_skip() -> None:
    inp = Input(repo_root="/tmp", git_error="git failed", files=[])
    hotspots, skip = analyze_hotspots(inp)
    assert hotspots == []
    assert skip == ""


def _git(repo: Path, *args: str) -> str:
    res = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return res.stdout


def _commit(repo: Path, msg: str, files: dict) -> None:
    for path, content in files.items():
        full = repo / path
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", msg)


@pytest.fixture
def hot_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "hot"
    repo.mkdir()
    _git(repo, "init", "--initial-branch=main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")
    # Seed >= 5 distinct commits touching internal/auth/
    for i in range(6):
        _commit(repo, f"auth touch {i}", {f"internal/auth/file_{i}.go": f"// {i}\n"})
    # Seed 2 commits touching internal/db/ (below the 5-commit threshold)
    for i in range(2):
        _commit(repo, f"db touch {i}", {f"internal/db/q_{i}.go": f"// {i}\n"})
    return repo


def test_analyze_hotspots_finds_overlap(hot_repo: Path) -> None:
    inp = Input(
        repo_root=str(hot_repo),
        files=[FileChange(path="internal/auth/file_0.go", added=10, deleted=0)],
    )
    hotspots, skip = analyze_hotspots(inp)
    assert skip == ""
    assert len(hotspots) == 1
    assert hotspots[0].prefix == "internal/auth"
    assert hotspots[0].recent_count >= 5


def test_analyze_hotspots_below_threshold_excluded(hot_repo: Path) -> None:
    """internal/db/ has only 2 commits in the seeded log, below the 5-commit floor."""
    inp = Input(
        repo_root=str(hot_repo),
        files=[FileChange(path="internal/db/q_0.go", added=10, deleted=0)],
    )
    hotspots, _ = analyze_hotspots(inp)
    assert all(h.prefix != "internal/db" for h in hotspots)


def test_analyze_hotspots_no_overlap_returns_empty(hot_repo: Path) -> None:
    """Hot prefix is internal/auth, but the diff doesn't touch it."""
    inp = Input(
        repo_root=str(hot_repo),
        files=[FileChange(path="other/area/x.go", added=1, deleted=0)],
    )
    hotspots, _ = analyze_hotspots(inp)
    assert hotspots == []
