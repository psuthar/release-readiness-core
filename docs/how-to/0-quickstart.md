# Quickstart: foolproof drop-in for `release-readiness-core`

The fastest path from "I want to try this" to a green `release-readiness` Check on your first PR is **four shell commands**. Pick a stack, scaffold pre-pinned + pre-greened, and push.

> If you want the deep dive on validation keys, scoring, and adapter mechanics, jump to the [Under the hood](#under-the-hood) appendix or the dedicated guides linked from the [README](../../README.md).

---

## TL;DR — four commands

Install the package as a third-party dependency, then scaffold:

```bash
pip install release-readiness-core
release-readiness-init my-project --demo --stack pytest
cd my-project && git init && git add . && git commit -m "release-readiness scaffold"

# Push to your repo and open a PR — the release-readiness Check will appear
```

That's the whole thing. The scaffold ships with synthetic green evidence (`evidence/*.json`), a stack-specific evidence-collection block, and a workflow pinned to the SHA you chose. First CI run is a deterministic PASS.

Replace `--stack pytest` with whichever runner matches your project — `playwright`, `cypress`, `jest`, `pytest`, `go`, or `go-coverage`. See [`docs/how-to/8-recipe-matrix.md`](8-recipe-matrix.md) for the full list and per-stack snippets.

---

## What just got scaffolded

```
my-project/
├── ops/release-readiness/
│   ├── config.yaml              # validations + scoring + remediation
│   ├── validation_map.yaml      # JUnit / Playwright stem -> validation key
│   └── pr-risk-config.yaml      # PR-risk scoring config (optional)
├── .github/workflows/
│   └── release-readiness.yml    # uses Tier-1 reusable workflow @ pinned SHA
└── evidence/                    # only with --demo
    ├── smoke.json               # synthetic — replace before relying on the gate
    ├── e2e.json
    └── coverage.json
```

The scaffold defaults to Tier-1 reusable workflow integration (`uses: psuthar/release-readiness-core/.../readiness.yml@<sha>`). This is the shortest setup when your repo has access to reusable workflows from `release-readiness-core`.

### Third-party-safe path (no source-workflow coupling)

If you are adopting as an external consumer and do **not** want to rely on cross-repo reusable workflow access, keep the scaffolded config/evidence files but run the CLIs directly in your own workflow (Tier 3):

```yaml
- uses: astral-sh/setup-uv@v6
- run: uvx --from release-readiness-core release-readiness-doctor --config ops/release-readiness/config.yaml --smoke-results evidence/smoke.json --e2e-results evidence/e2e.json --coverage evidence/coverage.json
- run: uvx --from release-readiness-core release-readiness-evaluate --repo-root . --config ops/release-readiness/config.yaml --smoke-results evidence/smoke.json --e2e-results evidence/e2e.json --coverage evidence/coverage.json --enforcement-mode block_only
```

Use this mode when:
- your org policy blocks cross-repo reusable workflows,
- the source repo is private, or
- you want all CI logic to live in the consumer repo.

---

## Three adoption tiers

The package supports three usage patterns. The quickstart above uses **Tier 1** (recommended for most adopters).

| Tier | Surface | Use when |
|---|---|---|
| **Tier 1** | Reusable workflow `uses: …/workflows/readiness.yml@<sha>` | Default. Most adopters. Two lines + `secrets: inherit`. |
| **Tier 2** | Composite actions (`release-readiness-pr-gate`, `release-readiness-publish`, `release-readiness`) | You want to swap in custom pre/post steps. |
| **Tier 3** | Raw CLIs (`release-readiness-evaluate`, `release-readiness-pr-risk`, `release-readiness-combine`, `release-readiness-check-payload`) | Non-GitHub CIs (GitLab, Buildkite, Jenkins) and bespoke pipelines. |

Full breakdown with canonical snippets per tier: [`docs/how-to/9-adoption-tiers.md`](9-adoption-tiers.md).

---

## When the first PR shows BLOCK

Open the PR and check the `release-readiness` Check's "Details" tab. The sticky comment also surfaces the verdict. The most common first-PR surprises:

| Symptom | Likely cause | Fix |
|---|---|---|
| `BLOCK` immediately, "missing smoke artifact" | You scaffolded without `--demo` and CI hasn't emitted real evidence yet | Re-run with `--demo`, or wire the per-stack evidence step from [`docs/how-to/8-recipe-matrix.md`](8-recipe-matrix.md) |
| `BLOCK` with "smoke parse error" | Your test runner emitted JSON in a different shape | Compare against `docs/contracts/smoke-input-v1.schema.json` and adjust your adapter step |
| `WARN` at score 100 | Optional artifact (e.g. `prod_health`) missing — warning suppresses PASS | Either provide the artifact or add it to `optional_artifacts:` in `config.yaml` |
| Workflow itself failed (red dot, no Check) | `<sha>` literal still in `.github/workflows/release-readiness.yml` | Re-run `release-readiness-init . --pin <sha> --force` |

For unexpected validation states (`missing` / `not_evaluated`), see [`docs/how-to/1-map-evidence.md`](1-map-evidence.md) §7.

---

## Verify locally before pushing

```bash
release-readiness-doctor \
  --config ops/release-readiness/config.yaml \
  --smoke-results evidence/smoke.json \
  --e2e-results evidence/e2e.json \
  --coverage evidence/coverage.json
```

Doctor catches typos, evidence-shape mismatches, and common inconsistencies (e.g. `failed_count > 0` with `failures: []`) before they hit a real CI run. Exits non-zero on any error.

If you scaffolded with `--demo`, you can also run the evaluator against the synthetic evidence to confirm green locally:

```bash
release-readiness-evaluate \
  --repo-root . \
  --config ops/release-readiness/config.yaml \
  --smoke-results evidence/smoke.json \
  --e2e-results evidence/e2e.json \
  --coverage evidence/coverage.json \
  --empty-diff
# Expected: Result: PASS, score=100
```

---

## Next steps

- **Replace synthetic evidence with real CI:** wire your test runner's output through the matching adapter — see [`docs/how-to/8-recipe-matrix.md`](8-recipe-matrix.md) for the per-stack snippet and [`docs/how-to/1-map-evidence.md`](1-map-evidence.md) for the mechanics of validation keys and evidence channels.
- **Tune the gate:** [`docs/how-to/2-tune-scoring.md`](2-tune-scoring.md) walks through penalties, thresholds, and the warnings-suppress-PASS rule.
- **Wire CI integrations:** if you outgrow Tier 1, [`docs/how-to/3-ci-integration.md`](3-ci-integration.md) covers GitHub Checks + the generic adapter pattern for non-GitHub CIs.
- **Make the check required:** once the gate has stabilized, [`docs/how-to/5-branch-protection.md`](5-branch-protection.md) shows the phased rollout to a required check.

---

## Under the hood

Want to know what each scaffolded file does? Or you want to author a config from scratch instead of using `release-readiness-init`? This appendix is the legacy walkthrough — it explains the moving parts but takes longer than the four-command path above.

### Minimum viable `config.yaml`

The smallest config that runs without errors:

```yaml
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
```

Each block:

- **`version`** — schema version, currently `1`.
- **`validations`** — registry of validation keys. Required keys appear here with a human description.
- **`evidence_boolean_keys`** — top-level keys in your smoke / e2e JSON that mark a validation as satisfied when set to `true`. Without this, the engine falls back to TalkBack-flavored defaults.
- **`infer_validations_when_pass`** — when the smoke or e2e suite passes overall, mark these validation keys as satisfied even without explicit booleans.
- **`scoring`** — thresholds and per-signal penalties. Tune per [`docs/how-to/2-tune-scoring.md`](2-tune-scoring.md).

### Synthetic evidence shapes (the same files `--demo` writes)

`evidence/smoke.json`:

```json
{ "status": "passed", "passed": true, "smoke_passing": true }
```

`evidence/e2e.json`:

```json
{
  "status": "passed",
  "failed_count": 0,
  "total_count": 0,
  "retries": 0,
  "failures": [],
  "validations": {}
}
```

`evidence/coverage.json`:

```json
{ "line_percent": 92.0, "baseline_percent": 85.0 }
```

### Outputs after `release-readiness-evaluate`

```
artifacts/release-readiness/report.json   # full structured payload
artifacts/release-readiness/report.md     # human-readable markdown
artifacts/release-readiness.json          # short summary the CI gate reads
```

### Where to look first when the report says BLOCK or WARN

1. **`### Outcome determination` table** — score, blockers, warnings, and any outcome override.
2. **`### Warnings` / `### Blockers` lists** — human-readable signals that drove the result.
3. **`### Failed checks`** — short keys (`smoke_artifact`, `e2e_critical`, …) for each signal. These are the join keys for `remediation` in `config.yaml`.
4. **`### Remediation guidance` table** — recommended action for each failed check, populated from your `remediation` config.

For programmatic use, `report.json` carries everything the markdown shows, plus `critical_failed_titles` and `non_critical_failed_titles` arrays so a CI gate doesn't have to re-parse raw test output.

---

If the four-command path didn't behave as advertised, please open an issue against `release-readiness-core`.
