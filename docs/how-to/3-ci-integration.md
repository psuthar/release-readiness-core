# Wire `release-readiness-core` into CI

This guide shows how to run the readiness CLI inside CI and surface its PASS/WARN/BLOCK verdict to humans (in PR descriptions or as a status check) and to merge automation (as a gate). It covers the GitHub happy-path in detail, then explains the generic formatter pattern so you aren't trapped on GitHub.

> Prerequisites: a working local setup (`docs/how-to/0-quickstart.md`) and a `config.yaml` that produces the verdict you expect when run against representative evidence.

---

## 0. Choose your integration mode first

Two valid GitHub approaches:

- **Consumer-owned (third-party-safe, recommended):** run `release-readiness-*` CLIs directly in your own workflow via `uvx --from release-readiness-core==X.Y.Z ...` (pin the version).
- **Source-owned reusable workflow:** call `psuthar/release-readiness-core/.github/workflows/readiness.yml@<sha>`.

Use consumer-owned mode when you cannot or do not want to depend on cross-repo reusable workflow access. For private repos, this avoids failures caused by reusable-workflow access policy mismatches.

**Reusable workflow + PyPI wheel:** the `uses: …/readiness.yml@<sha>` line pins the **workflow YAML** to a commit on this repo. You can still install the **Python package** from PyPI (no `git+https` pip install) by passing `install-source: pypi` and `pypi-version: X.Y.Z` — see `docs/how-to/9-adoption-tiers.md`.

---

## 1. What the CLI emits

`release-readiness-evaluate` writes three artifacts under `--output-dir` (default `artifacts/release-readiness/`):

| File | Content | Best consumer |
|---|---|---|
| `report.md` | Human-readable markdown summary. | PR comment / PR body / step summary. |
| `report.json` | Full structured payload (`outcome`, `score`, `blockers`, `warnings`, `failed_checks`, `validations`, `remediation_items`, …). | Programmatic gate logic; downstream tooling. |
| `<repo>/artifacts/release-readiness.json` | Lean machine summary: `{outcome, score, warnings, blockers}`. | CI status checks / merge gate. Designed to be tiny and stable. |

Exit code:

- **0** — outcome is PASS or WARN (and `--enforcement-mode block_only`, the default).
- **1** — outcome is BLOCK, OR outcome is WARN with `--enforcement-mode warn_and_block`.

Make `--enforcement-mode` your gating dial: most teams start in `block_only` and tighten to `warn_and_block` once their config is calibrated.

---

## 1a. Two-line GitHub Actions adoption (reusable composite action)

For the impatient: `release-readiness-core` ships a reusable composite action at `.github/actions/release-readiness/`. Reference it from your own workflow:

```yaml
# .github/workflows/release-readiness.yml
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

      # ---- collect evidence (project-specific steps go here) -----
      # ...

      - uses: psuthar/release-readiness-core/.github/actions/release-readiness@<sha>
        with:
          package-ref: <sha>          # same SHA — pins @ref and (by default) the git-based pip install
          # install-source: pypi     # optional — pip from PyPI instead of git
          # pypi-version: "0.3.3"    # required with install-source: pypi
          config-path: ops/release-readiness/config.yaml
          smoke-results: evidence/smoke.json
          e2e-results: evidence/e2e.json
          coverage: evidence/coverage.json
          enforcement-mode: block_only
```

The composite action installs the package, runs `release-readiness-evaluate`, and appends the report to `$GITHUB_STEP_SUMMARY`. For PR-comment / Check-run publishing, fall through to §2 below.

**Even faster:** `release-readiness-init <target>` writes a starter config + workflow into your project. Edit the placeholders and you're running.

## 2. GitHub Actions — full workflow with PR comment + Check run

A minimal workflow that runs readiness and publishes a Check + PR comment:

```yaml
# .github/workflows/release-readiness.yml
name: release-readiness

on:
  pull_request:
    branches: [main]

permissions:
  contents: read
  pull-requests: write   # for posting PR comments
  checks: write          # for publishing the Check run

jobs:
  readiness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with:
          fetch-depth: 0   # readiness needs git history for diff

      - uses: astral-sh/setup-uv@v6

      # ---- collect evidence (project-specific) -------------------
      - name: Run smoke
        run: ./ci/run-smoke.sh   # writes evidence/smoke.json

      - name: Run E2E
        run: ./ci/run-e2e.sh     # writes playwright-results.json

      - name: Convert Playwright -> readiness
        run: |
          uvx --from release-readiness-core playwright-to-readiness \
            --input playwright-results.json \
            --output evidence/e2e.json \
            --validation-map ops/release-readiness/e2e_validation_map.yaml

      - name: Coverage summary
        run: ./ci/coverage-summary.sh   # writes evidence/coverage.json

      # ---- evaluate ----------------------------------------------
      - name: release-readiness
        id: readiness
        run: |
          uvx --from release-readiness-core release-readiness-evaluate \
            --repo-root . \
            --config ops/release-readiness/config.yaml \
            --base-ref origin/${{ github.base_ref }} \
            --smoke-results evidence/smoke.json \
            --e2e-results evidence/e2e.json \
            --coverage evidence/coverage.json \
            --enforcement-mode block_only

      # ---- publish ----------------------------------------------
      - name: Append summary to job page
        if: always()
        run: cat artifacts/release-readiness/report.md >> "$GITHUB_STEP_SUMMARY"

      - name: Comment on PR
        if: github.event_name == 'pull_request' && always()
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
            const summary = fs.readFileSync('artifacts/release-readiness/release-readiness.json', 'utf8');
            const data = JSON.parse(summary);
            const conclusionMap = { PASS: 'success', WARN: 'neutral', BLOCK: 'failure' };
            await github.rest.checks.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              name: 'release-readiness',
              head_sha: context.payload.pull_request?.head.sha ?? context.sha,
              status: 'completed',
              conclusion: conclusionMap[data.outcome] ?? 'neutral',
              output: {
                title: `release-readiness: ${data.outcome} (score ${data.score})`,
                summary: fs.readFileSync('artifacts/release-readiness/report.md', 'utf8'),
              },
            });
```

Notes:

- `actions/checkout@v5` with `fetch-depth: 0` is required because the CLI shells out to `git diff <base-ref>` to compute changed files. If you want to skip that, pass `--empty-diff` and don't set fetch-depth.
- The `if: always()` on publish steps ensures the report still posts even when the readiness step exits non-zero on BLOCK. Without that, a BLOCK leaves no PR comment.
- `marocchino/sticky-pull-request-comment` keeps a single PR comment updated across pushes; `actions/github-script` is just one of many ways to publish the Check.
- `uvx --from release-readiness-core ...` avoids system Python writes (`pip --system`) and works on externally managed GitHub runners.

### Reusable workflow caveat for private repos

If you use `uses: psuthar/release-readiness-core/.github/workflows/readiness.yml@<sha>`, verify reusable-workflow access is enabled on the source repo. A disabled policy can surface as a confusing "workflow was not found" error even when the file exists.

### Gating merges

Two flavors:

- **Soft gate** (recommended at first): `release-readiness` is a non-required check. Reviewers see the WARN/BLOCK verdict but can still merge.
- **Hard gate**: mark the `release-readiness` check as required in the branch protection rules. With `--enforcement-mode block_only` (default), the workflow fails on BLOCK only. With `warn_and_block`, it also fails on WARN.

Tighten gradually: start with a soft gate, watch for false positives, adjust thresholds and penalties (see `docs/how-to/2-tune-scoring.md`), then make it required.

---

## 3. Surfacing the verdict in PR descriptions vs. checks

Two different consumers, two different outputs:

| Consumer | Best surface | Why |
|---|---|---|
| Reviewer reading the PR | PR comment or PR body excerpt | Inline, no extra clicks. Markdown rendering. |
| Merge automation / branch protection | Check run with `conclusion` | Programmatic; integrates with required-check rules. |
| Logs for postmortem | Step summary (`GITHUB_STEP_SUMMARY`) | Persists with the workflow run; easy to link from Slack. |

You typically want all three: comment for humans, check for automation, step summary for retro. The workflow above does all three.

The PR-body update pattern (less common, but useful if you want a stable section that PRs can edit around):

```bash
gh pr edit "$PR_NUMBER" --body "$(printf '%s\n\n---\n\n%s' \
  "$ORIGINAL_BODY" \
  "$(cat artifacts/release-readiness/report.md)")"
```

---

## 4. The generic formatter pattern (non-GitHub CIs)

`release-readiness-core` doesn't ship CI integrations *as integrations* — it ships **JSON output** with a stable schema, and a tiny Python API for combining it with other gates. The integration is your CI's job.

### Stable contract

The shape that travels between the engine and any CI is the `release-readiness.json` summary plus the `report.md` body. That's the input contract for any adapter. As long as the adapter reads those two files, it can target any CI.

### The `combine_gate_inputs` helper (multi-gate composition)

If your release decision combines readiness with other gates (PR-risk, security scan, custom checks), use the package's combiner:

```python
from release_readiness_core.pr_gate import (
    GateInput,
    combine_gate_inputs,
    format_gate_output,
)

inputs = [
    GateInput(source="release-readiness", status="WARN", payload={"score": 88}),
    GateInput(source="pr-risk", status="PASS", payload={"band": "low"}),
    GateInput(source="security-scan", status="PASS", payload={}),
]
summary = combine_gate_inputs(inputs)        # BLOCK > WARN > PASS precedence
print(format_gate_output(summary))
# {'recommendation': 'WARN', 'sources': [...]}
```

### Custom formatter — minimal example

```python
import json
from release_readiness_core.pr_gate import format_gate_output

def gitlab_job_artifact(summary):
    """GitLab CI consumes JSON via 'reports' artifacts. This adapter
    emits a shape that fits a custom 'metrics' report."""
    return {
        "metrics": [
            {"name": "release_readiness_recommendation", "value": summary.recommendation},
            {"name": "release_readiness_block_count",
             "value": sum(1 for s in summary.sources if s["status"] == "BLOCK")},
        ],
    }

payload = format_gate_output(summary, formatter=gitlab_job_artifact)
print(json.dumps(payload))
```

The formatter is a `Callable[[GateSummary], Dict[str, Any]]`. Anything JSON-serializable goes; the engine is intentionally agnostic.

---

## 5. A non-GitHub example — GitLab CI

```yaml
# .gitlab-ci.yml
release-readiness:
  image: python:3.11
  script:
    - pip install "release-readiness-core==0.3.3"
    # Or: pip install "git+https://github.com/psuthar/release-readiness-core.git@<sha>"
    - ./ci/collect-evidence.sh    # writes evidence/*.json
    - release-readiness-evaluate
        --repo-root .
        --config ops/release-readiness/config.yaml
        --smoke-results evidence/smoke.json
        --e2e-results evidence/e2e.json
        --coverage evidence/coverage.json
        --enforcement-mode block_only
  artifacts:
    when: always
    paths:
      - artifacts/release-readiness/
    reports:
      # Surface report.md as a job-level artifact reviewers can browse.
      junit: artifacts/release-readiness/report.md   # placeholder; GitLab needs JUnit XML for the inline UI
  allow_failure: false        # fail the pipeline on BLOCK
```

Two things to note for non-GitHub CIs:

1. There's no native "Check Run" concept. The closest analog is a pipeline step with a JSON artifact, plus whatever native commenting integration your platform offers (e.g. GitLab's `gitlab-comment-on-mr` snippets or Buildkite's `buildkite-agent annotate`).
2. To gate merges, you typically wire pipeline status into the merge request's "must pass" checks rather than a per-test Check Run.

---

## 5a. Adopting without PR-risk

`compute_readiness` honors a `pr_risk.json` artifact when one is present at `<output-dir>/pr_risk.json`. This is the integration point TalkBack uses to combine its Go-binary risk scoring with the readiness gate.

If your project has no PR-risk source:

- **Just don't write `pr_risk.json`.** The engine skips the entire `pr_risk` block when the file is absent or unreadable. No warning, no penalty, no behavior change.
- **No config change needed.** `pr_risk` is opt-in by convention (presence of the file), not by config flag.
- **The relevant `failed_checks` keys** (`pr_risk_block`, `pr_risk_warn`) simply never fire; you don't need entries for them in `remediation`.

If you later decide to add a PR-risk source: emit a JSON file matching `docs/contracts/pr-risk-input-v1.schema.json` at `<output-dir>/pr_risk.json` before invoking `release-readiness-evaluate`. The engine picks it up automatically.

## 6. Recipes

### Recipe — fail PR on BLOCK only, comment on every result

```bash
release-readiness-evaluate ... --enforcement-mode block_only
# always post comment (using `if: always()` in GitHub Actions terms)
```

### Recipe — fail PR on WARN too

```bash
release-readiness-evaluate ... --enforcement-mode warn_and_block
```

### Recipe — read just the verdict in shell

```bash
jq -r .outcome artifacts/release-readiness.json
# PASS | WARN | BLOCK
```

Useful for downstream "release-train" automation that wants the verdict without re-parsing the full report.

### Recipe — combine readiness with a separate PR-risk gate

```python
import json, pathlib
from release_readiness_core.pr_gate import GateInput, combine_gate_inputs, to_payload

readiness = json.loads(pathlib.Path("artifacts/release-readiness.json").read_text())
pr_risk = json.loads(pathlib.Path("artifacts/pr-risk.json").read_text())

summary = combine_gate_inputs([
    GateInput("release-readiness", readiness["outcome"], readiness),
    GateInput("pr-risk", pr_risk.get("merge_recommendation", "PASS"), pr_risk),
])
print(json.dumps(to_payload(summary), indent=2))
```

The combiner uses `BLOCK > WARN > PASS` precedence. Any input contributing BLOCK forces an overall BLOCK.

---

## 7. Cross-references

- `docs/how-to/0-quickstart.md` — fundamentals; the CLI surface this guide assumes.
- `docs/how-to/1-map-evidence.md` — wiring CI evidence into the engine.
- `docs/how-to/2-tune-scoring.md` — turning a noisy gate into a useful one before you require it.
- `docs/contracts/pr-risk-input-v1.schema.json`, `release-readiness-output-v1.schema.json` — the JSON shapes referenced above, machine-readable.
