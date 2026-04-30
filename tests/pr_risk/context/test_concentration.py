"""Tests for pr_risk.context.concentration."""

import pytest

from release_readiness_core.pr_risk.context.concentration import (
    analyze_concentration,
    two_segment_prefix,
)
from release_readiness_core.pr_risk.context.input import FileChange, Input


@pytest.mark.parametrize(
    "path,expected",
    [
        ("internal/auth/foo.go", "internal/auth"),
        ("web/src/App.tsx", "web/src"),
        ("README.md", "README.md"),
        ("/leading/slash/x", "leading/slash"),
        ("trailing/slash/", "trailing/slash"),
        ("", "."),
        ("just_root", "just_root"),
    ],
)
def test_two_segment_prefix(path: str, expected: str) -> None:
    assert two_segment_prefix(path) == expected


def test_empty_files_returns_balanced_no_files() -> None:
    out = analyze_concentration(Input(files=[]))
    assert out.mode == "balanced"
    assert out.detail == "no files"


def test_zero_loc_returns_balanced_no_loc_churn() -> None:
    out = analyze_concentration(Input(files=[FileChange(path="x.txt", added=0, deleted=0)]))
    assert out.mode == "balanced"
    assert out.detail == "no LOC churn"
    assert out.unique_dirs == 1


def test_focused_when_top_share_high_and_few_dirs() -> None:
    files = [
        FileChange(path="internal/auth/login.go", added=80, deleted=10),
        FileChange(path="internal/auth/session.go", added=20, deleted=5),
        FileChange(path="web/src/App.tsx", added=2, deleted=1),
    ]
    out = analyze_concentration(Input(files=files))
    assert out.mode == "focused"
    assert out.top_prefix == "internal/auth"
    assert "internal/auth" in out.detail


def test_focused_large_when_total_loc_above_threshold() -> None:
    files = [
        FileChange(path="internal/auth/big.go", added=2500, deleted=0),
        FileChange(path="internal/auth/small.go", added=50, deleted=0),
    ]
    out = analyze_concentration(Input(files=files))
    assert out.mode == "focused_large"
    assert "Large concentrated churn" in out.detail


def test_scattered_when_many_dirs_low_hhi_many_files() -> None:
    # 10 files, 10 distinct two-segment prefixes, even LOC distribution.
    files = [
        FileChange(path=f"area{i}/sub/file.go", added=10, deleted=0) for i in range(10)
    ]
    out = analyze_concentration(Input(files=files))
    assert out.mode == "scattered"
    assert out.unique_dirs == 10


def test_balanced_default() -> None:
    files = [
        FileChange(path="internal/auth/x.go", added=50, deleted=0),
        FileChange(path="internal/api/y.go", added=50, deleted=0),
    ]
    out = analyze_concentration(Input(files=files))
    # Two prefixes, equal LOC → top_share = 0.5 < 0.55 → balanced.
    assert out.mode == "balanced"


def test_hhi_exact_for_single_file() -> None:
    out = analyze_concentration(Input(files=[FileChange(path="a/b/c.go", added=10, deleted=0)]))
    assert out.hhi == 1.0
    assert out.top_share == 1.0
    assert out.unique_dirs == 1


def test_top_prefix_tie_breaks_alphabetically() -> None:
    """When two prefixes have equal LOC, sort places lower lexicographic key first."""
    files = [
        FileChange(path="z/path/a.go", added=10, deleted=0),
        FileChange(path="a/path/b.go", added=10, deleted=0),
    ]
    out = analyze_concentration(Input(files=files))
    assert out.top_prefix == "a/path"
