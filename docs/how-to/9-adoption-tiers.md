# Adoption tiers — pick the right surface

`release-readiness-core` exposes three distinct surfaces for CI integration. Pick the one that matches your project's appetite for control vs. config.

| Tier | What you write | Who it's for |
|---|---|---|
| **Tier 1** — Reusable workflow | `uses: …/workflows/readiness.yml@<sha>` + 3 `with:` lines + `secrets: inherit` | Most adopters. The default. |
| **Tier 2** — Composite actions | `uses: …/actions/release-readiness-pr-gate@<sha>` + `…/release-readiness-publish@<sha>` (and/or `…/release-readiness@<sha>`) | Adopters who want to inject custom pre/post steps around the gate. |
| **Tier 3** — Raw CLIs | `uv pip install "release-readiness-core==X.Y.Z"` (or `git+https://…@<sha>`) + invoke the CLIs directly | Non-GitHub CIs (GitLab, Buildkite, Jenkins) and bespoke pipelines. |

The tiers are **opt-in deeper**, not opt-out shallower — Tier 1 is built on the same composite actions a Tier-2 adopter calls directly, which call the same CLIs a Tier-3 adopter shells out to. Picking a tier is a decision about how much YAML you want to own.

> **Third-party default:** if you're adopting from outside this repo and want zero dependency on cross-repo reusable-workflow access, start at **Tier 3** and run CLIs directly. On GitHub Actions stock images, prefer **`uvx --from release-readiness-core ...`** (see [Python install paths](#python-install-paths-pragmatic) below); locally, **`pip install`** into a venv is fine.

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

The `uses: …@<sha>` ref must still point at a commit on `psuthar/release-readiness-core` (that loads this reusable workflow and the local composite actions under `.github/actions/`). By default, **`package-ref` is the git ref** for `pip install git+https://…@…` (same SHA you pass to `with:`). To install the **wheel from PyPI** instead (no git pip dependency), add `install-source: pypi` and `pypi-version: "X.Y.Z"` to `with:`.

**What you get for free:** install + (optional) doctor pre-flight + pr-risk + readiness-evaluate + combine + GitHub Check publish + sticky PR comment + enforcement (fail on BLOCK; also fail on WARN if you set `enforcement-mode: warn_and_block`).

**Working example:** [`examples/python-pytest/.github/workflows/release-readiness.yml`](../../examples/python-pytest/.github/workflows/release-readiness.yml). The reusable workflow itself: [`.github/workflows/readiness.yml`](../../.github/workflows/readiness.yml) (inputs include optional PyPI install mode; 2 outputs).

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
          # install-source: pypi
          # pypi-version: "0.4.0"
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

### Python install paths (pragmatic)

Docs and examples use a **deliberate mix** of installers:

- **`pip install "release-readiness-core==X.Y.Z"`** — the default story for **local machines** and anywhere you control a **venv** (or a non–externally-managed interpreter). This matches PyPI-first adoption in the [quickstart](0-quickstart.md) and [README](../../README.md).
- **`uvx --from "release-readiness-core==X.Y.Z" <cli> ...`** — preferred in **GitHub Actions** snippets when you need a one-liner that runs a CLI **without** writing into the runner’s **system** Python. Stock `ubuntu-latest` images are often **PEP 668** “externally managed”; naive `pip install` to system Python fails there, while `uvx` avoids that class of breakage.
- **`uv pip install --system`** (in some Tier 3 shell examples and in this repo’s own composites) — same pragmatic goal as pip into a dedicated environment, using **uv**’s pip interface where CI already standardizes on uv.

**Pin one version** everywhere you care about (`pip`, `uvx --from`, and `pypi-version` / workflow `@sha`) so local runs, adapters, and CI do not drift.

Nothing GitHub-specific in the *contract* of Tier 3: the four CLIs read JSON, write JSON, and exit non-zero on failure. Wire them into any CI runner that can install Python and execute a shell.

```bash
# Install the package once (PyPI — pin the version).
uv pip install --system "release-readiness-core==0.4.0"

# Or from git (pin a SHA).
# uv pip install --system "git+https://github.com/psuthar/release-readiness-core.git@<sha>"

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

## Tier 3 in GitHub Actions: complete worked example

If you're on GitHub Actions but explicitly want a Tier-3 setup (no cross-repo reusable workflow dependency, all CI logic in your own repo), this section gives you the full workflow YAML. It's stack-agnostic — drop in any evidence-collection block from [`docs/how-to/8-recipe-matrix.md`](8-recipe-matrix.md) and the rest works unchanged.

The blocks below are extracted from a working third-party adopter ([`release-readiness-sample-app`](https://github.com/psuthar/release-readiness-sample-app), Go, **Phase 2** — `enforcement-mode: block_only`). For a Phase-3 adopter that demonstrates `WARN`-blocks-merge with the conclusion-mapping override in place, see the sister sample [`release-readiness-node-js-sample-app`](https://github.com/psuthar/release-readiness-node-js-sample-app) (TypeScript). The two samples together cover both ends of the [phased rollout](5-branch-protection.md#3-phased-rollout-recommended).

### Workflow skeleton

```yaml
name: release-readiness

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
  workflow_dispatch:

env:
  RELEASE_READINESS_CORE_VERSION: "0.4.0"

permissions:
  contents: read
  pull-requests: write
  checks: write

jobs:
  collect-evidence:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0   # required so --base-ref can diff against the target branch

      # --- stack-specific test + adapter steps go here ---
      # See docs/how-to/8-recipe-matrix.md for per-stack snippets.
      # Each step writes evidence/{smoke,e2e,coverage}.json.

      - uses: actions/upload-artifact@v4
        with:
          name: readiness-evidence
          path: evidence/

  readiness:
    needs: collect-evidence
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - uses: actions/download-artifact@v4
        with:
          name: readiness-evidence
          path: evidence/

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install release-readiness-core
        run: |
          python -m venv .venv
          .venv/bin/python -m pip install -U pip
          .venv/bin/pip install "release-readiness-core==${{ env.RELEASE_READINESS_CORE_VERSION }}"

      - name: Evaluate release readiness
        id: evaluate
        continue-on-error: true
        run: |
          # PR: diff vs target branch. Push to main: diff vs parent commit.
          if [ "${{ github.event_name }}" = "pull_request" ]; then
            BASE_REF="origin/${{ github.base_ref }}"
          elif [ "${{ github.event.before }}" != "0000000000000000000000000000000000000000" ]; then
            BASE_REF="${{ github.event.before }}"
          else
            BASE_REF="HEAD~1"
          fi
          .venv/bin/release-readiness-evaluate \
            --repo-root . \
            --config ops/release-readiness/config.yaml \
            --base-ref "$BASE_REF" \
            --smoke-results evidence/smoke.json \
            --e2e-results evidence/e2e.json \
            --coverage evidence/coverage.json \
            --enforcement-mode block_only

      - name: Append report to run summary
        if: always()
        run: |
          if [ -f artifacts/release-readiness/report.md ]; then
            cat artifacts/release-readiness/report.md >> "$GITHUB_STEP_SUMMARY"
          fi

      - name: Comment on PR
        if: github.event_name == 'pull_request' && always() && hashFiles('artifacts/release-readiness/report.md') != ''
        uses: marocchino/sticky-pull-request-comment@v2
        with:
          path: artifacts/release-readiness/report.md
          header: release-readiness

      - name: Publish Check run
        if: always()
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const summaryPath = 'artifacts/release-readiness.json';
            const reportPath = 'artifacts/release-readiness/report.md';
            const fallback = { outcome: 'BLOCK', score: 0 };
            const data = fs.existsSync(summaryPath) ? JSON.parse(fs.readFileSync(summaryPath, 'utf8')) : fallback;
            const conclusionMap = { PASS: 'success', WARN: 'neutral', BLOCK: 'failure' };
            try {
              await github.rest.checks.create({
                owner: context.repo.owner,
                repo: context.repo.repo,
                name: 'release-readiness',
                head_sha: context.payload.pull_request?.head.sha ?? context.sha,
                status: 'completed',
                conclusion: conclusionMap[data.outcome] ?? 'failure',
                output: {
                  title: `release-readiness: ${data.outcome} (score ${data.score})`,
                  summary: fs.existsSync(reportPath)
                    ? fs.readFileSync(reportPath, 'utf8')
                    : 'release-readiness report was not generated.',
                },
              });
            } catch (e) {
              console.warn(`Could not publish Check run: ${e}`);
            }

      - name: Enforce BLOCK outcome
        if: always()
        run: |
          if [ ! -f artifacts/release-readiness.json ]; then
            echo "Missing artifacts/release-readiness.json"; exit 1
          fi
          outcome="$(jq -r '.outcome // "BLOCK"' artifacts/release-readiness.json)"
          echo "release-readiness outcome: ${outcome}"
          if [ "${outcome}" = "BLOCK" ]; then exit 1; fi
```

### Why each block matters

- **`fetch-depth: 0`** — `--base-ref` needs full history to compute the diff. Shallow clones silently produce empty diffs (PR-risk and coverage-regression signals no-op).
- **`env.RELEASE_READINESS_CORE_VERSION`** — single source of truth for the package version. Bump it in one place; both jobs pick it up.
- **Two-job split (`collect-evidence` → `readiness`)** — keeps test execution and verdict computation in separate runners. Evidence flows through `upload-artifact`/`download-artifact`. Lets you parallelize evidence collection across N jobs later.
- **`continue-on-error: true` on `evaluate`** — readiness runs even when verdict is BLOCK so the publish/comment/enforce steps can render the diagnostics. The `Enforce BLOCK outcome` step at the end is what actually fails the workflow.
- **PR-vs-push `BASE_REF` switch** — without this, push-to-main runs evaluate against the wrong base (or empty diff), and PR-risk / coverage-regression signals don't fire. The three branches cover: PR (diff vs target), normal push (diff vs parent commit), and first-push edge case.
- **Check + sticky comment + step summary** — these are what an adopter gets "for free" from Tier 1's reusable workflow. In Tier 3 you write them yourself; the YAML above is the canonical implementation.
- **`Enforce BLOCK outcome`** — Tier 1's hidden enforce step. Reads `artifacts/release-readiness.json`, fails the workflow on BLOCK only (matching `--enforcement-mode block_only`). Switch to `warn_and_block` mode when warnings are trustworthy.

### Output paths the workflow assumes

`release-readiness-evaluate` writes to fixed paths the publish steps read from:

```
artifacts/release-readiness.json          # short summary the gate reads
artifacts/release-readiness/report.json   # full structured payload
artifacts/release-readiness/report.md     # markdown for sticky comment + step summary
```

These paths are stable contracts — don't override `--output-dir` unless you also update the publish steps.

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
