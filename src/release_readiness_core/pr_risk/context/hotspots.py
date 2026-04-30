"""Hotspots analyzer (port of internal/prrisk/context/hotspots.go).

Identifies path prefixes that appear in several recent commits and overlap
the current diff. Shells out to git log; if git is unavailable (GitError set
or empty repo_root), returns an empty list with a non-empty skip reason.
"""

from __future__ import annotations

import subprocess
from typing import Dict, List, Tuple

from release_readiness_core.pr_risk.context.concentration import two_segment_prefix
from release_readiness_core.pr_risk.context.input import Input
from release_readiness_core.pr_risk.context.types import HotspotInsight


_HOTSPOT_SAMPLE_COMMITS = 50
# Distinct commits required for a prefix to count as a hotspot — counting commits
# (not lines) prevents one large commit from inflating the score.
_HOTSPOT_MIN_COMMITS = 5


def is_git_object_id(s: str) -> bool:
    """Return True if s looks like a SHA-1 (40) or SHA-256 (64) git object hash."""
    if len(s) not in (40, 64):
        return False
    for c in s:
        if "0" <= c <= "9":
            continue
        if "a" <= c <= "f":
            continue
        if "A" <= c <= "F":
            continue
        return False
    return True


def prefix_commits_from_name_only_log(stdout: str) -> Dict[str, int]:
    """Parse `git log -n N --name-only --pretty=format:%H` into {prefix: distinct_commits}."""
    prefix_commits: Dict[str, set] = {}
    cur_hash = ""
    seen_prefix_in_commit: set = set()

    def flush() -> None:
        if not cur_hash:
            return
        for p in seen_prefix_in_commit:
            prefix_commits.setdefault(p, set()).add(cur_hash)

    for raw in stdout.split("\n"):
        line = raw.strip()
        if line == "":
            continue
        if is_git_object_id(line):
            flush()
            cur_hash = line
            seen_prefix_in_commit = set()
            continue
        if cur_hash == "":
            continue
        line = line.replace("\\", "/")
        seen_prefix_in_commit.add(two_segment_prefix(line))
    flush()

    return {p: len(commits) for p, commits in prefix_commits.items()}


def analyze_hotspots(in_: Input) -> Tuple[List[HotspotInsight], str]:
    """Return (hotspots, skip_reason). Empty list with skip_reason="" is the no-git case."""
    if in_.git_error != "" or in_.repo_root == "":
        return [], ""

    res = subprocess.run(
        [
            "git",
            "-C",
            in_.repo_root,
            "log",
            "-n",
            str(_HOTSPOT_SAMPLE_COMMITS),
            "--name-only",
            "--pretty=format:%H",
            "HEAD",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        return [], res.stderr.strip()

    commit_count_by_prefix = prefix_commits_from_name_only_log(res.stdout)

    diff_pref: set = set()
    for f in in_.files:
        diff_pref.add(two_segment_prefix(f.path.replace("\\", "/").strip()))

    # Build the qualifying list and sort by (count desc, prefix asc) for parity.
    qualifying = [
        (k, v)
        for k, v in commit_count_by_prefix.items()
        if v >= _HOTSPOT_MIN_COMMITS
    ]
    qualifying.sort(key=lambda kv: (-kv[1], kv[0]))

    out: List[HotspotInsight] = []
    for k, v in qualifying:
        if k in diff_pref:
            out.append(
                HotspotInsight(
                    prefix=k,
                    recent_count=v,
                    detail=(
                        f"Prefix touched in {v} of the last {_HOTSPOT_SAMPLE_COMMITS} "
                        f"sampled commits — sustained activity; extra regression care."
                    ),
                )
            )
    if len(out) > 5:
        out = out[:5]
    return out, ""
