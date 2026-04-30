"""Intent analyzer (port of internal/prrisk/context/intent.go).

Compares PR title/body keywords to the domains touched in the diff.
"""

from __future__ import annotations

import subprocess
from typing import Dict, List, Optional, Tuple

from release_readiness_core.pr_risk.context.input import Input
from release_readiness_core.pr_risk.context.types import IntentInsight


# (keyword, expected_domains). Order is significant — mirrors Go literal order.
KEYWORD_RULES: List[Tuple[str, Optional[List[str]]]] = [
    ("auth", ["auth"]),
    ("login", ["auth"]),
    ("invite", ["auth"]),
    ("session", ["auth", "api"]),
    ("migration", ["migrations"]),
    ("rag", ["rag"]),
    ("qa", ["rag"]),
    ("ask", ["rag"]),
    ("workflow", ["workflows"]),
    ("github", ["workflows"]),
    ("ci", ["workflows"]),
    ("deploy", ["deploy"]),
    ("docker", ["deploy"]),
    ("render", ["deploy"]),
    ("e2e", ["web"]),
    ("playwright", ["web"]),
    ("test", None),
    ("fix", None),
    ("refactor", None),
]


_GENERIC_TITLES = {
    "wip",
    "fix",
    "update",
    "bump",
    "patch",
    "misc",
    "draft",
    "changes",
    "temp",
    "test",
}


def is_weak_title(title: str) -> bool:
    t = title.strip().lower()
    if t == "":
        return True
    if len(t) <= 4:
        return True
    if t in _GENERIC_TITLES:
        return True
    if " " not in t and len(t) <= 8:
        return True
    return False


def domains_present(hits: Dict[str, int]) -> List[str]:
    if hits is None:
        return []
    keys = [k for k, n in hits.items() if n > 0 and k != "tests"]
    return sorted(keys)


def contains_domain(in_diff: List[str], domain: str) -> bool:
    if domain in in_diff:
        return True
    if domain == "web":
        for d in in_diff:
            if d == "web" or d == "tests":
                return True
    return False


def git_head_message(repo_root: str) -> Tuple[str, str]:
    """Return (subject, body) from `git log -1 --format=%s%n%b`."""
    res = subprocess.run(
        ["git", "-C", repo_root, "log", "-1", "--format=%s%n%b"],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        return "", ""
    parts = res.stdout.split("\n", 1)
    subject = parts[0].strip()
    body = ""
    if len(parts) > 1:
        body = parts[1].strip()
        if len(body) > 800:
            body = body[:800]
    return subject, body


def analyze_intent(in_: Input) -> IntentInsight:
    title = in_.pr_title.strip()
    body = in_.pr_body.strip()
    if title == "" and in_.repo_root != "" and in_.git_error == "":
        title, body = git_head_message(in_.repo_root)

    combined = (title + " " + body).strip().lower()
    weak = is_weak_title(title)

    if combined == "":
        return IntentInsight(
            intent_strength="unknown",
            aligned=True,
            mismatch=False,
            detail="No PR title/body or git subject available; intent alignment skipped.",
        )

    matched: List[str] = []
    expected: List[str] = []
    seen: set = set()
    for kw, domains in KEYWORD_RULES:
        if kw == "":
            continue
        if kw not in combined:
            continue
        if domains is None:
            continue
        matched.append(kw)
        for d in domains:
            if d in seen:
                continue
            seen.add(d)
            expected.append(d)

    if weak:
        strength = "weak"
    else:
        strength = "strong"
    if not expected and not matched:
        strength = "unknown"

    in_diff = domains_present(in_.domain_hits)

    if not expected and weak:
        return IntentInsight(
            title=title,
            intent_strength="weak",
            keywords_matched=matched,
            aligned=False,
            mismatch=False,
            domains_in_diff=in_diff,
            detail=(
                "PR title/body is weak or generic; intent alignment not inferred. "
                "Use a descriptive title (area + change)."
            ),
        )

    if not expected:
        return IntentInsight(
            title=title,
            intent_strength="unknown",
            keywords_matched=matched,
            aligned=True,
            mismatch=False,
            domains_in_diff=in_diff,
            detail="No strong intent keywords matched; alignment not scored.",
        )

    mismatch = False
    for exp in expected:
        if not contains_domain(in_diff, exp):
            mismatch = True
            break

    if mismatch:
        detail = (
            "Title/body suggests certain areas (keywords) but corresponding paths "
            "may be missing from this diff — confirm scope or update the PR description."
        )
    else:
        detail = "Keywords in the title/body align with domains touched in the diff."
    if weak:
        detail += " (Title is still weak; prefer a clearer summary for reviewers.)"

    return IntentInsight(
        title=title,
        intent_strength=strength,
        keywords_matched=matched,
        domains_expected=expected,
        domains_in_diff=in_diff,
        aligned=not mismatch,
        mismatch=mismatch,
        detail=detail,
    )
