"""Tests for pr_risk.context.intent."""

import os

import pytest

from release_readiness_core.pr_risk.context.input import FileChange, Input
from release_readiness_core.pr_risk.context.intent import (
    KEYWORD_RULES,
    analyze_intent,
    contains_domain,
    domains_present,
    is_weak_title,
)


@pytest.mark.parametrize(
    "title,expected",
    [
        ("", True),
        ("wip", True),
        ("fix", True),
        ("Update", True),
        ("a", True),  # <= 4 chars
        ("misc", True),
        ("cleanup", True),  # 7 chars, single token
        ("auth: refactor login flow", False),
        ("Fix auth login", False),  # has space
    ],
)
def test_is_weak_title(title: str, expected: bool) -> None:
    assert is_weak_title(title) is expected


def test_domains_present_excludes_tests_and_zero_counts() -> None:
    out = domains_present({"auth": 1, "tests": 5, "web": 0, "rag": 2})
    assert out == ["auth", "rag"]


def test_domains_present_handles_none_and_empty() -> None:
    assert domains_present(None) == []
    assert domains_present({}) == []


def test_contains_domain_direct_match() -> None:
    assert contains_domain(["auth", "rag"], "auth") is True
    assert contains_domain(["auth"], "rag") is False


def test_contains_domain_web_special_matches_tests() -> None:
    """When asking for 'web', any 'tests' presence also satisfies it."""
    assert contains_domain(["tests"], "web") is True
    assert contains_domain(["web"], "web") is True


def test_keyword_rules_first_entries() -> None:
    """Order in KEYWORD_RULES is significant — sanity-check the first two."""
    assert KEYWORD_RULES[0] == ("auth", ["auth"])
    assert KEYWORD_RULES[1] == ("login", ["auth"])


def test_empty_title_and_body_returns_skipped() -> None:
    inp = Input(pr_title="", pr_body="", repo_root="", git_error="set so no fallback")
    out = analyze_intent(inp)
    assert out.intent_strength == "unknown"
    assert out.aligned is True
    assert out.mismatch is False
    assert "alignment skipped" in out.detail


def test_aligned_when_keywords_match_diff_domains() -> None:
    inp = Input(
        pr_title="auth: tighten login flow",
        domain_hits={"auth": 1},
    )
    out = analyze_intent(inp)
    assert out.intent_strength == "strong"
    assert "auth" in out.keywords_matched
    assert out.aligned is True
    assert out.mismatch is False


def test_mismatch_when_keyword_domains_absent_from_diff() -> None:
    inp = Input(
        pr_title="auth: refactor login",
        domain_hits={"web": 1},
    )
    out = analyze_intent(inp)
    assert out.mismatch is True
    assert out.aligned is False


def test_weak_title_returns_weak_with_no_alignment() -> None:
    inp = Input(pr_title="wip", pr_body="", domain_hits={"auth": 1})
    out = analyze_intent(inp)
    assert out.intent_strength == "weak"
    assert out.aligned is False
    assert out.mismatch is False
    assert "weak or generic" in out.detail


def test_no_keyword_match_returns_unknown_aligned() -> None:
    inp = Input(
        pr_title="A descriptive title with no keywords",
        domain_hits={"auth": 1},
    )
    out = analyze_intent(inp)
    assert out.intent_strength == "unknown"
    assert out.aligned is True
    assert out.mismatch is False


def test_session_keyword_expects_auth_or_api() -> None:
    """'session' maps to ['auth', 'api'] — only one of the two needs to be missing for mismatch."""
    inp = Input(
        pr_title="session refactor for performance",
        domain_hits={"web": 1},  # neither auth nor api in diff
    )
    out = analyze_intent(inp)
    assert out.mismatch is True


def test_keyword_matching_is_case_insensitive_substring() -> None:
    inp = Input(
        pr_title="MIGRATION: backfill anonymous rows",
        domain_hits={"migrations": 1},
    )
    out = analyze_intent(inp)
    assert "migration" in out.keywords_matched
    assert out.aligned is True
