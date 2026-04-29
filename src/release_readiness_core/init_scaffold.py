"""``release-readiness init`` — scaffold a starter project layout.

Console script: ``release-readiness-init``.

The init command exists so a new adopter can go from "I want to try
this" to "I have a working config and CI workflow" in one command,
instead of copy-pasting from `docs/how-to/quickstart.md`. After running
init, an adopter customizes the validation keys and risk patterns, then
wires their CI evidence — the package handles the boilerplate.

Usage::

    release-readiness-init <target-dir>            # writes scaffold under <target-dir>
    release-readiness-init . --force               # overwrite if files exist
    release-readiness-init . --workflow github     # default — writes a GitHub Actions workflow
    release-readiness-init . --workflow none       # skip the workflow file (configs only)

Files written under ``<target-dir>``::

    ops/release-readiness/config.yaml              # starter config
    ops/release-readiness/validation_map.yaml      # starter validation map
    .github/workflows/release-readiness.yml        # only if --workflow github
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Sequence


CONFIG_TEMPLATE = """\
# release-readiness-core starter config — replace placeholders before shipping.
# Reference docs:
#   - docs/how-to/quickstart.md
#   - docs/how-to/map-evidence.md
#   - docs/how-to/tune-scoring.md
#   - docs/contracts/validation-config-v1.schema.json

version: 1

validations:
  smoke_passing:
    description: Smoke tests passed in CI.

evidence_boolean_keys:
  - smoke_passing

infer_validations_when_pass:
  smoke:
    - smoke_passing
  e2e: []

# Declare any artifact your project genuinely doesn't have (e.g.
# `prod_health` for a service without a health-monitoring source). Listed
# artifacts neither warn nor deduct when absent.
optional_artifacts:
  - prod_health
  # - coverage  # uncomment if your project doesn't track coverage yet

# Map paths -> risk categories. Categories trigger a required validation.
# risk_from_paths:
#   - categories: [schema_changes]
#     patterns: ["migrations/**", "alembic/**"]

# Map risk categories -> validation keys. Defaults to identity mapping.
# risk_category_to_required_validation:
#   schema_changes: db_migrations

scoring:
  max_score: 100
  pass_threshold: 80
  warn_threshold: 60
  block_score: 0
  penalties:
    missing_smoke_artifact: 25
    missing_e2e_artifact: 15
    missing_coverage_artifact: 5
    missing_prod_health_artifact: 5
    non_critical_e2e_failure: 15
    e2e_retries_or_flaky: 10
    coverage_regression: 12
    risky_config_without_note: 10

# Substring patterns matched (case-insensitive) against E2E failure titles.
# A match promotes the failure to a hard blocker. Be specific — "test"
# would match every failure.
# e2e_critical_name_patterns:
#   - "auth_login"
#   - "checkout"

# Paths that warrant a validation note when changed (e.g. CI configs,
# deploy manifests, IaC). Without a note, the engine warns.
# risky_config_patterns:
#   - ".github/workflows/*.yml"
#   - "Dockerfile"

# Per-failed-check remediation guidance surfaced in the report.
# Keys are the failed-check identifiers emitted by the engine. See
# docs/how-to/tune-scoring.md for the full list.
remediation:
  smoke_artifact:
    severity: warn
    likely_cause: smoke job did not upload results
    recommended_action: Re-run smoke job and upload smoke.json artifact.
    fix_type: ci_config
  e2e_critical:
    severity: block
    likely_cause: critical E2E spec failed
    recommended_action: Fix the failing critical spec or revert the offending change.
    fix_type: code
"""


VALIDATION_MAP_TEMPLATE = """\
# Validation map for the JUnit / Playwright adapters.
# Map each readiness validation key to the test classnames or stems
# whose pass/fail provides evidence for it.
#
# Example for JUnit:
#   auth_login:
#     - LoginFlow
#     - oauth.OAuthCallback
#
# Example for Playwright (use file stems, no extensions):
#   auth_login:
#     - login-flow
#     - oauth-callback

# smoke_passing:
#   - SmokeSuite
"""


GITHUB_WORKFLOW_TEMPLATE = """\
name: release-readiness

on:
  pull_request:
    branches: [main]

permissions:
  contents: read
  pull-requests: write
  checks: write

jobs:
  readiness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - uses: astral-sh/setup-uv@v6
      - run: uv python install

      # Pin to a specific SHA in production. Replace <sha> below.
      - name: Install release-readiness-core
        run: |
          uv pip install --system \\
            "git+https://github.com/psuthar/release-readiness-core.git@<sha>"

      # ---- collect evidence (project-specific) -------------------
      # Replace the placeholders below with your actual smoke / e2e /
      # coverage steps. Each must produce the JSON shapes documented
      # in docs/contracts/.
      #
      # - name: Run smoke
      #   run: ./ci/run-smoke.sh   # writes evidence/smoke.json
      #
      # - name: Run E2E (Playwright example)
      #   run: npx playwright test --reporter=json > playwright-results.json
      #
      # - name: Convert Playwright -> readiness
      #   run: |
      #     playwright-to-readiness \\
      #       --input playwright-results.json \\
      #       --output evidence/e2e.json \\
      #       --validation-map ops/release-readiness/validation_map.yaml
      #
      # - name: Convert JUnit -> readiness (Cypress / Jest / pytest)
      #   run: |
      #     junit-to-readiness \\
      #       --input test-results.xml \\
      #       --output evidence/e2e.json \\
      #       --validation-map ops/release-readiness/validation_map.yaml
      #
      # - name: Coverage summary (LCOV)
      #   run: |
      #     lcov-to-readiness \\
      #       --input coverage/lcov.info \\
      #       --output evidence/coverage.json \\
      #       --baseline-percent 85

      - name: release-readiness
        run: |
          release-readiness-evaluate \\
            --repo-root . \\
            --config ops/release-readiness/config.yaml \\
            --base-ref origin/${{ github.base_ref }} \\
            --enforcement-mode block_only

      - name: Append summary to job page
        if: always()
        run: cat artifacts/release-readiness/report.md >> "$GITHUB_STEP_SUMMARY"
"""


def _write_file(path: Path, content: str, force: bool) -> str:
    """Return one of: ``'created'``, ``'overwrote'``, ``'skipped (exists)'``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return "skipped (exists)"
    state = "overwrote" if path.exists() else "created"
    path.write_text(content, encoding="utf-8")
    return state


def scaffold(target: Path, *, workflow: str = "github", force: bool = False) -> dict[str, str]:
    """Write scaffold files under ``target``. Returns ``{relpath: status}``."""
    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)

    plan: list[tuple[Path, str]] = [
        (target / "ops" / "release-readiness" / "config.yaml", CONFIG_TEMPLATE),
        (target / "ops" / "release-readiness" / "validation_map.yaml", VALIDATION_MAP_TEMPLATE),
    ]
    if workflow == "github":
        plan.append(
            (target / ".github" / "workflows" / "release-readiness.yml", GITHUB_WORKFLOW_TEMPLATE)
        )
    elif workflow != "none":
        raise ValueError(f"--workflow must be 'github' or 'none', got {workflow!r}")

    results: dict[str, str] = {}
    for path, content in plan:
        rel = path.relative_to(target).as_posix()
        results[rel] = _write_file(path, content, force=force)
    return results


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold a starter release-readiness-core config and CI workflow."
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Directory to scaffold into (default: current directory).",
    )
    parser.add_argument(
        "--workflow",
        choices=["github", "none"],
        default="github",
        help="Which CI workflow to emit (default: github).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files instead of skipping them.",
    )
    args = parser.parse_args(argv)

    target = Path(args.target)
    try:
        results = scaffold(target, workflow=args.workflow, force=args.force)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Scaffolded under {target.resolve()}:")
    for rel, status in results.items():
        print(f"  {status:>20}  {rel}")
    print()
    print("Next steps:")
    print("  1. Edit ops/release-readiness/config.yaml — declare your validation keys.")
    print("  2. Edit ops/release-readiness/validation_map.yaml — map keys to test stems.")
    if args.workflow == "github":
        print("  3. Replace <sha> in .github/workflows/release-readiness.yml with a pinned SHA.")
        print("  4. Wire the evidence-collection steps to your CI's smoke / E2E / coverage jobs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
