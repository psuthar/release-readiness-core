"""``release-readiness init`` — scaffold a starter project layout.

Console script: ``release-readiness-init``.

The init command exists so a new adopter can go from "I want to try
this" to "I have a working config and CI workflow" in one command,
instead of copy-pasting from `docs/how-to/0-quickstart.md`. After running
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
    evidence/smoke.json                            # only if --demo
    evidence/e2e.json                              # only if --demo
    evidence/coverage.json                         # only if --demo

When ``--demo`` is passed, the scaffold also writes synthetic
``evidence/*.json`` files whose shapes match the starter config so the
adopter's first ``release-readiness-evaluate`` run is provably PASS /
score=100. Each demo file carries a ``_comment`` field marking it as
synthetic with a pointer to ``docs/how-to/1-map-evidence.md``.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Iterable, Sequence


CONFIG_TEMPLATE = """\
# release-readiness-core starter config — replace placeholders before shipping.
# Reference docs:
#   - docs/how-to/0-quickstart.md
#   - docs/how-to/1-map-evidence.md
#   - docs/how-to/2-tune-scoring.md
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
# docs/how-to/2-tune-scoring.md for the full list.
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


PR_RISK_CONFIG_TEMPLATE = """\
# release-readiness-core PR-risk config — replace placeholders before shipping.
# Schema: docs/contracts/pr-risk-config-v1.schema.json
# Walkthrough: docs/how-to/7-configure-pr-risk.md
# Examples: see examples/pr-risk/{python-service,node-service}.yaml
#
# Without this file, release-readiness-pr-risk runs with a language-agnostic
# default: every changed path classifies to "other", and only generic gates
# (CI fetch depth, PR review summary, workflow / config validation, add tests
# / evidence, intent alignment, scattered-review plan, test proximity, hotspot
# regression) fire. Add domains and gates here to drive project-specific
# checks.

version: 1

# Domains group changed paths into product areas. First match wins.
# Pattern types: prefix | contains | exact | endswith | any_contains | and.
# domains:
#   - id: api
#     label: api
#     patterns:
#       - { prefix: "src/api/" }
#       - { contains: "/handlers/" }

# Domains whose changes — without test files in the diff — fire the
# `tests_missing` factor (which adds penalty points to the score).
# sensitive_domains:
#   - api

# Gate registry. Each gate fires when its applies_when predicates match.
# Predicate vocabulary (closed set, see docs/reference/pr-risk-config.md):
#   factor_id | not_factor_id | risk_band | not_risk_band | domain_factor |
#   intent_mismatch | concentration_mode | hotspots_present |
#   proximity_distant_with_sensitive
#
# Evidence detector templates (closed set):
#   test_domain | signal_check | migrations | add_tests | validation_note |
#   intent_alignment | intent_strength | intent_aligned_or_weak | proximity | hotspot
#
# gates:
#   - id: my_gate
#     title: "Validate area X before merge"
#     priority: high              # high | medium | supporting
#     fix_type: test              # code | test | config | process | infra | db
#     applies_when:
#       - { risk_band: [high, critical] }
#       - { factor_id: domain_api }
#     applies_when_extra: "API area changed"
#     validation_line: "test: API endpoints exercised (E2E or contract test)"
#     checklist:
#       - "Run E2E for the affected endpoint(s)."
#     evidence:
#       template: test_domain
#       args:
#         domain: api
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

      # uv runs CLIs from PyPI without touching the runner system Python (PEP 668 safe).
      # Bump {pypi_version} when you upgrade: https://pypi.org/project/release-readiness-core/
      # Tier-1 reusable workflow adopters pin package-ref / uses @<sha> — docs/how-to/9-adoption-tiers.md
      - uses: astral-sh/setup-uv@v6

      # ---- collect evidence (project-specific) -------------------
{evidence_steps}
      - name: release-readiness
        run: |
          uvx --from "release-readiness-core=={pypi_version}" release-readiness-evaluate \\
            --repo-root . \\
            --config ops/release-readiness/config.yaml \\
            --base-ref origin/${{{{ github.base_ref }}}} \\
            --enforcement-mode block_only

      - name: Append summary to job page
        if: always()
        run: cat artifacts/release-readiness/report.md >> "$GITHUB_STEP_SUMMARY"
"""


VALID_STACKS = ("playwright", "cypress", "jest", "pytest", "go", "go-coverage")


# Baked-in pin reference. Updated at release time by maintenance tooling so
# `release-readiness-init --pin` can resolve to the latest release SHA without
# requiring the adopter to look one up. Empty in development.
DEFAULT_PIN_REF = ""

# Environment variable consulted when --pin is not passed and DEFAULT_PIN_REF
# is empty. Lets adopters set a pin once via env without typing it on every
# scaffold invocation.
PIN_REF_ENV_VAR = "RR_PIN_REF"


def resolve_pin_ref(cli_pin: str | None = None) -> str:
    """Source precedence: --pin arg → RR_PIN_REF env → DEFAULT_PIN_REF.

    Returns the resolved ref or the empty string when no source is set.
    Whitespace-only values are treated as unset.
    """
    if cli_pin and cli_pin.strip():
        return cli_pin.strip()
    env_value = os.environ.get(PIN_REF_ENV_VAR, "")
    if env_value.strip():
        return env_value.strip()
    return DEFAULT_PIN_REF.strip()


# Evidence-collection step blocks per stack. Each block is the YAML body that
# substitutes into GITHUB_WORKFLOW_TEMPLATE's {evidence_steps} placeholder.
# Bodies are indented to match the surrounding workflow's `steps:` indent (6 sp).
_DEFAULT_EVIDENCE_STEPS = """\
      # Replace the placeholders below with your actual smoke / e2e /
      # coverage steps. Each must produce the JSON shapes documented in
      # docs/contracts/. See docs/how-to/1-map-evidence.md.
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
"""


_PLAYWRIGHT_EVIDENCE_STEPS = """\
      - uses: actions/setup-node@v5
        with:
          node-version: "22"

      - name: Install Node deps
        run: npm ci

      - name: Run Playwright (--reporter=json)
        run: npx playwright test --reporter=json > playwright-results.json

      - uses: astral-sh/setup-uv@v6

      - name: Convert Playwright -> readiness e2e shape
        run: |
          mkdir -p evidence
          uvx --from "release-readiness-core=={pypi_version}" playwright-to-readiness \\
            --input playwright-results.json \\
            --output evidence/e2e.json \\
            --validation-map ops/release-readiness/validation_map.yaml
"""


_CYPRESS_EVIDENCE_STEPS = """\
      - uses: actions/setup-node@v5
        with:
          node-version: "22"

      - name: Install Node deps
        run: npm ci

      - name: Run Cypress with JUnit reporter
        run: |
          npx cypress run \\
            --reporter junit \\
            --reporter-options "mochaFile=test-results.xml,toConsole=true"

      - uses: astral-sh/setup-uv@v6

      - name: Convert JUnit -> readiness e2e shape
        run: |
          mkdir -p evidence
          uvx --from "release-readiness-core=={pypi_version}" junit-to-readiness \\
            --input test-results.xml \\
            --output evidence/e2e.json \\
            --validation-map ops/release-readiness/validation_map.yaml
"""


_JEST_EVIDENCE_STEPS = """\
      - uses: actions/setup-node@v5
        with:
          node-version: "22"

      - name: Install Node deps
        run: npm ci

      - name: Run Jest with jest-junit reporter
        env:
          JEST_JUNIT_OUTPUT_FILE: test-results.xml
        run: npx jest --reporters=default --reporters=jest-junit

      - uses: astral-sh/setup-uv@v6

      - name: Convert JUnit -> readiness e2e shape
        run: |
          mkdir -p evidence
          uvx --from "release-readiness-core=={pypi_version}" junit-to-readiness \\
            --input test-results.xml \\
            --output evidence/e2e.json \\
            --validation-map ops/release-readiness/validation_map.yaml
"""


_PYTEST_EVIDENCE_STEPS = """\
      - name: Install pytest deps
        run: pip install -e ".[test]" || pip install pytest

      - name: Run pytest with JUnit XML
        run: pytest --junit-xml=test-results.xml

      - uses: astral-sh/setup-uv@v6

      - name: Convert JUnit -> readiness e2e shape
        run: |
          mkdir -p evidence
          uvx --from "release-readiness-core=={pypi_version}" junit-to-readiness \\
            --input test-results.xml \\
            --output evidence/e2e.json \\
            --validation-map ops/release-readiness/validation_map.yaml
"""


_GO_EVIDENCE_STEPS = """\
      - uses: actions/setup-go@v6
        with:
          go-version-file: go.mod

      - name: Run Go tests
        id: gotest
        continue-on-error: true
        run: go test ./... -count=1

      - name: Write smoke evidence
        run: |
          mkdir -p evidence
          if [ "${{ steps.gotest.outcome }}" = "success" ]; then
            echo '{"status":"passed","passed":true,"smoke_passing":true}' > evidence/smoke.json
          else
            echo '{"status":"failed","passed":false,"failed_count":1,"total_count":1,"failures":[{"title":"go test failed"}]}' > evidence/smoke.json
          fi
"""


_GO_COVERAGE_EVIDENCE_STEPS = """\
      - uses: actions/setup-go@v6
        with:
          go-version-file: go.mod

      - name: Run Go tests with coverage
        run: go test ./... -count=1 -coverprofile=coverage.out

      - name: Convert Go coverage -> LCOV
        run: |
          go install github.com/jandelgado/gcov2lcov@latest
          mkdir -p coverage
          gcov2lcov -infile=coverage.out -outfile=coverage/lcov.info

      - uses: astral-sh/setup-uv@v6

      - name: Convert LCOV -> readiness coverage shape
        run: |
          mkdir -p evidence
          uvx --from "release-readiness-core=={pypi_version}" lcov-to-readiness \\
            --input coverage/lcov.info \\
            --output evidence/coverage.json \\
            --baseline-percent 85
"""


def _read_project_version() -> str:
    """Version from repo-root ``pyproject.toml`` (for scaffolded PyPI pin)."""
    pyproject = Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError:
        return "0.0.0"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("version = "):
            _, _, rhs = stripped.partition("=")
            return rhs.strip().strip('"').strip("'")
    return "0.0.0"


_EVIDENCE_BLOCKS = {
    "playwright": _PLAYWRIGHT_EVIDENCE_STEPS,
    "cypress": _CYPRESS_EVIDENCE_STEPS,
    "jest": _JEST_EVIDENCE_STEPS,
    "pytest": _PYTEST_EVIDENCE_STEPS,
    "go": _GO_EVIDENCE_STEPS,
    "go-coverage": _GO_COVERAGE_EVIDENCE_STEPS,
}


def render_workflow_template(stack: str | None = None, pin_ref: str = "") -> str:
    """Return the GitHub Actions workflow body.

    With ``stack``, substitute the matching evidence-collection block.
    With ``pin_ref`` non-empty, substitute every ``<sha>`` literal (e.g. in the
    commented git-install alternative) so the scaffold can show a concrete ref.
    The active install line uses the current ``version`` from ``pyproject.toml``.
    """
    block = _DEFAULT_EVIDENCE_STEPS if stack is None else _EVIDENCE_BLOCKS[stack]
    pypi_version = _read_project_version()
    block = block.replace("{pypi_version}", pypi_version)
    body = GITHUB_WORKFLOW_TEMPLATE.format(
        evidence_steps=block,
        pypi_version=pypi_version,
    )
    if pin_ref:
        body = body.replace("<sha>", pin_ref)
    return body


DEMO_SYNTHETIC_HEADER = (
    "Synthetic — replace before relying on this gate. "
    "See docs/how-to/1-map-evidence.md for the real evidence shapes."
)

DEMO_SMOKE_JSON = """\
{
  "_comment": "%s",
  "status": "passed",
  "passed": true,
  "smoke_passing": true
}
""" % DEMO_SYNTHETIC_HEADER

DEMO_E2E_JSON = """\
{
  "_comment": "%s",
  "status": "passed",
  "failed_count": 0,
  "total_count": 0,
  "retries": 0,
  "failures": [],
  "validations": {}
}
""" % DEMO_SYNTHETIC_HEADER

DEMO_COVERAGE_JSON = """\
{
  "_comment": "%s",
  "line_percent": 92.0,
  "baseline_percent": 85.0
}
""" % DEMO_SYNTHETIC_HEADER


def _write_file(path: Path, content: str, force: bool) -> str:
    """Return one of: ``'created'``, ``'overwrote'``, ``'skipped (exists)'``."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return "skipped (exists)"
    state = "overwrote" if path.exists() else "created"
    path.write_text(content, encoding="utf-8")
    return state


def scaffold(
    target: Path,
    *,
    workflow: str = "github",
    force: bool = False,
    demo: bool = False,
    stack: str | None = None,
    pin_ref: str = "",
) -> dict[str, str]:
    """Write scaffold files under ``target``. Returns ``{relpath: status}``.

    When ``demo`` is True, also writes synthetic ``evidence/{smoke,e2e,coverage}.json``
    so the adopter's first ``release-readiness-evaluate`` run is provably PASS.

    When ``stack`` is one of ``VALID_STACKS``, the emitted GitHub Actions
    workflow has the matching test-runner + adapter-conversion steps
    uncommented and parameterized (instead of the commented placeholder).

    When ``pin_ref`` is non-empty, every ``<sha>`` literal in the emitted
    workflow is substituted so the scaffold ships pre-pinned. Use
    ``resolve_pin_ref`` to honor the --pin / RR_PIN_REF / DEFAULT_PIN_REF
    precedence chain.

    Without any of these flags, scaffold output is byte-identical to the
    pre-D1 / D3 / D2 behavior.
    """
    if stack is not None and stack not in VALID_STACKS:
        raise ValueError(
            f"--stack must be one of {sorted(VALID_STACKS)}, got {stack!r}"
        )

    target = target.resolve()
    target.mkdir(parents=True, exist_ok=True)

    plan: list[tuple[Path, str]] = [
        (target / "ops" / "release-readiness" / "config.yaml", CONFIG_TEMPLATE),
        (target / "ops" / "release-readiness" / "validation_map.yaml", VALIDATION_MAP_TEMPLATE),
        (target / "ops" / "release-readiness" / "pr-risk-config.yaml", PR_RISK_CONFIG_TEMPLATE),
    ]
    if workflow == "github":
        plan.append(
            (
                target / ".github" / "workflows" / "release-readiness.yml",
                render_workflow_template(stack, pin_ref=pin_ref),
            )
        )
    elif workflow != "none":
        raise ValueError(f"--workflow must be 'github' or 'none', got {workflow!r}")

    if demo:
        plan.extend([
            (target / "evidence" / "smoke.json", DEMO_SMOKE_JSON),
            (target / "evidence" / "e2e.json", DEMO_E2E_JSON),
            (target / "evidence" / "coverage.json", DEMO_COVERAGE_JSON),
        ])

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
    parser.add_argument(
        "--demo",
        action="store_true",
        help=(
            "Also write synthetic evidence/{smoke,e2e,coverage}.json that match "
            "the starter config so the first release-readiness-evaluate run is "
            "provably PASS (score 100). Replace before relying on the gate."
        ),
    )
    parser.add_argument(
        "--stack",
        choices=list(VALID_STACKS),
        default=None,
        help=(
            "Pre-fill the emitted release-readiness.yml with stack-specific "
            "test-runner + adapter-conversion steps. Without --stack, the "
            "workflow ships with a commented placeholder block."
        ),
    )
    parser.add_argument(
        "--pin",
        default=None,
        help=(
            "git ref (SHA or tag) substituted for every <sha> literal in the "
            "emitted workflow. Source precedence: --pin arg -> RR_PIN_REF env "
            "-> DEFAULT_PIN_REF (release-time constant, empty in dev). When no "
            "source is set, the workflow ships with the literal <sha> placeholder."
        ),
    )
    args = parser.parse_args(argv)

    pin_ref = resolve_pin_ref(args.pin)

    target = Path(args.target)
    try:
        results = scaffold(
            target,
            workflow=args.workflow,
            force=args.force,
            demo=args.demo,
            stack=args.stack,
            pin_ref=pin_ref,
        )
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
        if pin_ref:
            print(f"  3. Git-install comment in the workflow can use pin {pin_ref} (--pin / RR_PIN_REF).")
        else:
            print(
                "  3. The workflow installs from PyPI at "
                f"{_read_project_version()} — bump that version when you upgrade; "
                "optional git-install lines use <sha> (re-run with --pin / set RR_PIN_REF)."
            )
        print("  4. Wire the evidence-collection steps to your CI's smoke / E2E / coverage jobs.")
    if args.demo:
        print()
        print("Demo evidence written. Verify a green PASS with:")
        print("  release-readiness-evaluate --repo-root . \\")
        print("    --config ops/release-readiness/config.yaml \\")
        print("    --smoke-results evidence/smoke.json \\")
        print("    --e2e-results evidence/e2e.json \\")
        print("    --coverage evidence/coverage.json --empty-diff")
        print("Replace evidence/*.json with real CI outputs before relying on the gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
