"""release-readiness-pr-risk CLI entry point (port of cmd/prrisk/main.go)."""

from __future__ import annotations

import argparse
import os
import os.path
import sys
from typing import Optional, Sequence

from release_readiness_core.pr_risk.gitdiff import extract_signals
from release_readiness_core.pr_risk.integrations import ENV_JIRA_ISSUE_KEY
from release_readiness_core.pr_risk.report import write_json, write_markdown
from release_readiness_core.pr_risk.score import score
from release_readiness_core.pr_risk.semantic_json import write_semantic_pr_risk_json
from release_readiness_core.pr_risk.types import default_weights
from release_readiness_core.pr_risk.version import (
    VERSION,
    VERSION_MINOR,
    report_version_string,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="release-readiness-pr-risk",
        description=(
            "Compute PR risk score and required actions from a git diff. "
            f"Schema/report version {report_version_string()}."
        ),
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the git worktree root (default: current directory).",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Base ref to diff against (default: origin/main).",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/release-readiness",
        help="Directory for pr_risk.json and pr_risk.md (default: artifacts/release-readiness).",
    )
    parser.add_argument(
        "--jira-key",
        default=None,
        help="Optional Jira issue key embedded in integrations output.",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    jira_key = (args.jira_key or "").strip()
    if not jira_key:
        jira_key = os.environ.get(ENV_JIRA_ISSUE_KEY, "").strip()

    signals = extract_signals(args.repo_root, args.base_ref)
    res = score(signals, default_weights(), jira_key)

    out = os.path.normpath(args.output_dir)
    os.makedirs(out, exist_ok=True)

    json_out = os.path.join(out, "pr_risk.json")
    md_out = os.path.join(out, "pr_risk.md")
    semantic_out = os.path.normpath(os.path.join(out, "..", "pr-risk.json"))

    try:
        write_json(json_out, res)
        write_markdown(md_out, res)
        write_semantic_pr_risk_json(semantic_out, res)
    except OSError as e:
        sys.stderr.write(f"prrisk: write failed: {e}\n")
        return 1

    print(
        f"PR risk v{VERSION}.{VERSION_MINOR}: score={res.risk_score:.1f} "
        f"({res.risk_band}) — wrote "
        f"{os.path.basename(json_out)}/{os.path.basename(md_out)} "
        f"+ {os.path.basename(semantic_out)}"
    )
    if signals.git_error:
        sys.stderr.write(f"warning: git diff issue: {signals.git_error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
