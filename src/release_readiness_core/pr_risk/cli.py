"""release-readiness-pr-risk CLI entry point.

This is a Phase 0 stub (SCRUM-232). The full implementation lands across
SCRUM-233..236. Until then the CLI exits 2 with an explanatory message,
preserving the registered entry-point name for downstream wiring.
"""

import argparse
import sys
from typing import Optional, Sequence

from release_readiness_core.pr_risk.version import report_version_string


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
    parser.parse_args(argv)
    sys.stderr.write(
        "release-readiness-pr-risk is not yet implemented. "
        "Phase 0 (SCRUM-232) registered the entry-point; the scoring engine "
        "lands incrementally across SCRUM-233..236.\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
