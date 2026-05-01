# Adoption tiers — pick the right surface

`release-readiness-core` exposes three distinct surfaces for CI integration. Pick the one that matches your project's appetite for control vs. config.

| Tier | What you write | Who it's for |
|---|---|---|
| **Tier 1** — Reusable workflow | `uses: …/workflows/readiness.yml@<sha>` + 3 `with:` lines + `secrets: inherit` | Most adopters. The default. |
| **Tier 2** — Composite actions | `uses: …/actions/release-readiness-pr-gate@<sha>` + `…/release-readiness-publish@<sha>` (and/or `…/release-readiness@<sha>`) | Adopters who want to inject custom pre/post steps around the gate. |
| **Tier 3** — Raw CLIs | `uv pip install …` + invoke `release-readiness-evaluate` / `release-readiness-pr-risk` / `release-readiness-combine` / `release-readiness-check-payload` directly | Non-GitHub CIs (GitLab, Buildkite, Jenkins) and bespoke pipelines. |

The tiers are **opt-in deeper**, not opt-out shallower — Tier 1 is built on the same composite actions a Tier-2 adopter calls directly, which call the same CLIs a Tier-3 adopter shells out to. Picking a tier is a decision about how much YAML you want to own.

---

## Tier 1 — reusable workflow (recommended)

```yaml
# .github/workflows/release-readiness.yml in your repo
name: release-readiness

on:
  pull_request:
    branches: [main]

jobs:
  readiness:
    uses: psuthar/release-readiness-core/.github/workflows/readiness.yml@<sha>
    with:
      package-ref: <sha>
      smoke-results: evidence/smoke.json
      e2e-results: evidence/e2e.json
    secrets: inherit
```

**What you get for free:** install + (optional) doctor pre-flight + pr-risk + readiness-evaluate + combine + GitHub Check publish + sticky PR comment + enforcement (fail on BLOCK; also fail on WARN if you set `enforcement-mode: warn_and_block`).

**Working example:** [`examples/python-pytest/.github/workflows/release-readiness.yml`](../../examples/python-pytest/.github/workflows/release-readiness.yml). The reusable workflow itself: [`.github/workflows/readiness.yml`](../../.github/workflows/readiness.yml) (15 inputs, 2 outputs).

**Who it's for:** any GitHub-Actions adopter without an explicit reason to fork. Picks up improvements to the reusable workflow on your next pin bump.

---

## Tier 2 — piecewise composite actions

You write the workflow YAML; the package gives you composables that handle install + the four CLIs + Check + sticky comment + step summary. Useful when you need:

- Custom pre-steps (e.g., spin up Docker services, prep test fixtures, run code generation).
- Custom post-steps (e.g., upload a non-readiness artifact, notify Slack, gate on a different signal).
- A different ordering than Tier 1's chain.
- Multi-job pipelines where evidence is collected in N parallel jobs and combined in one readiness job.

```yaml
jobs:
  collect-evidence:
    runs-on: ubuntu-latest
    steps:
      # ... your pre-steps ...
      - run: ./ci/run-smoke.sh   # writes evidence/smoke.json
      - run: ./ci/run-e2e.sh     # writes evidence/e2e.json
      - run: ./ci/coverage.sh    # writes evidence/coverage.json

  readiness:
    needs: collect-evidence
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      checks: write
    steps:
      - uses: actions/checkout@v5
        with: { fetch-depth: 0 }

      # ... any custom pre-readiness steps ...

      - uses: psuthar/release-readiness-core/.github/actions/release-readiness-pr-gate@<sha>
        with:
          package-ref: <sha>
          smoke-results: evidence/smoke.json
          e2e-results: evidence/e2e.json
          coverage: evidence/coverage.json

      - uses: psuthar/release-readiness-core/.github/actions/release-readiness-publish@<sha>
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}

      # ... any custom post-readiness steps ...

      - name: Enforce gate
        if: always()
        env:
          STATUS: ${{ steps.pr-gate.outputs.gate-status }}
        run: |
          if [ "$STATUS" = "BLOCK" ]; then exit 1; fi
```

**Composite actions in this package:**

- [`release-readiness-pr-gate`](../../.github/actions/release-readiness-pr-gate/action.yml) — chains pr-risk + evaluate + combine + check-payload, emits `pr-gate-check.json`.
- [`release-readiness-publish`](../../.github/actions/release-readiness-publish/action.yml) — Check + sticky comment + step summary.
- [`release-readiness`](../../.github/actions/release-readiness/action.yml) — install + evaluate-only (no PR risk, no combine).

**Who it's for:** adopters who want to keep the readiness step but need it embedded in a workflow whose shape they own.

---

## Tier 3 — raw CLIs

Nothing GitHub-specific. The four CLIs read JSON, write JSON, and exit non-zero on failure. Wire them into any CI runner that can install Python and execute a shell.

```bash
# Install the package once.
uv pip install --system "git+https://github.com/psuthar/release-readiness-core.git@<sha>"

# Per-PR run:
release-readiness-pr-risk --base-ref origin/main --output-dir artifacts/release-readiness
release-readiness-evaluate \
  --repo-root . \
  --config ops/release-readiness/config.yaml \
  --base-ref origin/main \
  --smoke-results evidence/smoke.json \
  --e2e-results evidence/e2e.json \
  --coverage evidence/coverage.json \
  --output-dir artifacts/release-readiness
release-readiness-combine \
  --pr-risk-json artifacts/pr-risk.json \
  --readiness-json artifacts/release-readiness.json \
  --readiness-report-json artifacts/release-readiness/report.json \
  --output-dir artifacts
release-readiness-check-payload \
  --gate-json artifacts/pr-gate-summary.json \
  --output artifacts/pr-gate-check.json

# Read the verdict programmatically:
jq -r .final_gate.status artifacts/pr-gate-summary.json
jq -r .workflow_should_fail artifacts/pr-gate-check.json
```

**CLIs in this package:**

- [`release-readiness-pr-risk`](../../src/release_readiness_core/pr_risk/cli.py) — score the diff.
- [`release-readiness-evaluate`](../../src/release_readiness_core/readiness_evaluate.py) — compute readiness verdict from evidence.
- [`release-readiness-combine`](../../src/release_readiness_core/pr_gate_combine.py) — merge pr-risk + readiness into a single gate.
- [`release-readiness-check-payload`](../../src/release_readiness_core/pr_gate_check.py) — build the GitHub Checks API payload (or any other Check-style payload via `--check-name`).

Plus auxiliary adapters: `playwright-to-readiness`, `junit-to-readiness`, `lcov-to-readiness`, `pr-risk-semantic`, and pre-flight tools `release-readiness-doctor` and `release-readiness-init`.

The output JSON shapes are documented under [`docs/contracts/`](../contracts/) — read those before writing your CI's adapter.

**Who it's for:** non-GitHub CIs (GitLab, Buildkite, Jenkins, CircleCI) and pipelines that need to compose readiness with signals the package doesn't model (custom security scans, compliance checks, etc.). Also useful when you want to drive readiness from a service rather than a workflow.

---

## Migrating between tiers

You can move from Tier 1 → Tier 2 by replacing the reusable-workflow `uses:` line with the two composite-action `uses:` lines from the Tier-2 example above (plus your own enforce step). The configs and evidence formats are identical.

You can move from Tier 2 → Tier 3 by replacing the composite actions with the equivalent shell invocations of the four CLIs. Same artifacts in the same locations.

There is no migration path going **shallower** that loses functionality — Tier 1 has every input Tier 2 has, and Tier 2 has every CLI Tier 3 has. The deeper you go, the more YAML you write; you don't lose features.

---

## Cross-references

- [`docs/how-to/0-quickstart.md`](0-quickstart.md) — the four-command Tier-1 path.
- [`docs/how-to/3-ci-integration.md`](3-ci-integration.md) — Tier-3 wiring details for non-GitHub CIs.
- [`docs/how-to/8-recipe-matrix.md`](8-recipe-matrix.md) — per-stack adapter snippets.
- [`docs/contracts/`](../contracts/) — JSON schemas for every artifact in the chain.
