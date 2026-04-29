# Quickstart: adopting `release-readiness-core` in a new project

This walkthrough takes you from zero to a green PASS report in under 30 minutes. By the end you will have:

1. Installed `release-readiness-core` into a Python project.
2. Authored a minimal `config.yaml`.
3. Run the evaluator against synthetic evidence and read the report.

It assumes you have Python 3.9+ and either `pip` or `uv` available.

> Worked example: a fully runnable version of every step lives at `examples/second-project/` in this repo. If you get stuck, diff your setup against that fixture.

---

## 0. Scaffold (optional, recommended)

Skip §§1–2 by using the scaffold command:

```bash
pip install "git+https://github.com/psuthar/release-readiness-core.git@<sha>"
release-readiness-init my-project
```

This writes `ops/release-readiness/config.yaml`, `ops/release-readiness/validation_map.yaml`, and a starter `.github/workflows/release-readiness.yml` under `my-project/`. Skim the placeholders, swap in your validation keys, and you have a working baseline. The rest of this guide explains what the scaffold emits.

After editing the config and gathering some evidence files, verify your setup with the doctor before pushing:

```bash
release-readiness-doctor \
  --config ops/release-readiness/config.yaml \
  --smoke-results evidence/smoke.json \
  --e2e-results evidence/e2e.json \
  --coverage evidence/coverage.json
```

Doctor catches typos, missing fields, and common inconsistencies (e.g. `failed_count > 0` with `failures: []`) before they hit a real CI run. Exits non-zero on any error.

## 1. Install

The package is published from this Git repository. Pin a SHA in production:

```bash
pip install "git+https://github.com/psuthar/release-readiness-core.git@<sha>"
```

For local exploration, install the latest `main`:

```bash
pip install "git+https://github.com/psuthar/release-readiness-core.git"
```

The install puts four CLIs on your `PATH`:

| Command | What it does |
|---|---|
| `release-readiness-evaluate` | Full PASS/WARN/BLOCK evaluator. **The one you want for CI.** |
| `release-readiness` | Lightweight summary of validation booleans (no scoring). |
| `playwright-to-readiness` | Convert a Playwright JSON report to readiness E2E shape. |
| `pr-risk-semantic` | Combine PR-risk JSON with a check generator outcome. |

Verify the install:

```bash
release-readiness-evaluate --help
```

---

## 2. Minimum viable `config.yaml`

Drop a `config.yaml` at the root of the project (or wherever you want; you'll point the CLI at it with `--config`). The smallest config that runs without errors:

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

What each block does:

- **`version`** — schema version, currently `1`.
- **`validations`** — registry of the validation keys your project knows about. Required keys appear here with a human description.
- **`evidence_boolean_keys`** — top-level keys in your smoke / e2e JSON that mark a validation as satisfied when set to `true`. Without this, the engine falls back to TalkBack-flavored defaults (see `docs/how-to/1-map-evidence.md` for why you almost always want to set this explicitly).
- **`infer_validations_when_pass`** — optional inference: when smoke or e2e passes overall, mark these validation keys as satisfied even without explicit booleans.
- **`scoring`** — thresholds and per-signal penalties. Defaults below preserve the deterministic engine's behavior. Tune per `docs/how-to/2-tune-scoring.md`.

Everything else (`risk_from_paths`, `risky_config_patterns`, `remediation`, `e2e_critical_name_patterns`, etc.) is optional — start without it and add as you need it.

---

## 3. First run — no evidence

Run the evaluator from the project root with no artifacts attached:

```bash
release-readiness-evaluate \
  --repo-root . \
  --config config.yaml \
  --empty-diff \
  --output-dir artifacts/release-readiness
```

`--empty-diff` skips the `git diff` step. Use it for local runs and non-CI invocations. In CI, drop it and the package will compute changed files via `git diff origin/main…HEAD`.

Expected output (excerpt):

```
## Result: **BLOCK** (score 50.0)

### Warnings
- Smoke results artifact missing or unreadable
- E2E test results artifact missing or unreadable
- Coverage summary not provided (confidence reduced)
- Production health snapshot not provided (optional)
```

This is the package telling you the truth: no evidence, no confidence, no PASS. It's also a healthy first signal that your install works.

Outputs land in:

```
artifacts/release-readiness/report.json   # full structured payload
artifacts/release-readiness/report.md     # human-readable markdown
artifacts/release-readiness.json          # short summary the CI gate reads
```

---

## 4. Second run — with synthetic evidence

Create three synthetic artifact files. These mimic what your real CI will emit later.

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
{ "line_percent": 88.0, "baseline_percent": 85.0 }
```

(Optional — add `evidence/prod_health.json` if your project has a production-health source. If your project doesn't have one, declare `optional_artifacts: [prod_health]` in your `config.yaml` and the warning won't fire — see `tune-scoring.md` for the full opt-out list.)

Re-run, this time pointing at the artifacts:

```bash
release-readiness-evaluate \
  --repo-root . \
  --config config.yaml \
  --smoke-results evidence/smoke.json \
  --e2e-results evidence/e2e.json \
  --coverage evidence/coverage.json \
  --empty-diff \
  --output-dir artifacts/release-readiness
```

Expected:

```
## Result: **WARN** (score 95.0)
### Warnings
- Production health snapshot not provided (optional)
```

The score is 95/100 (one optional warning) but PASS requires score ≥ 80 **and** zero warnings, so the outcome demotes to WARN. Two ways to clear it:

- **Provide a stub `prod_health.json`** (e.g. `{ "status": "healthy" }`) and re-run with `--prod-health evidence/prod_health.json`. Use this when your project genuinely has a production-health source you want to start tracking.
- **Declare it optional in `config.yaml`** when your project has no production-health monitoring at all:

  ```yaml
  optional_artifacts:
    - prod_health
  ```

  The warning is suppressed and so is the score penalty. Coverage can be opted out the same way.

Either gets you to:

```
## Result: **PASS** (score 100.0)
```

That's the green path. From here, every CI run that emits the same artifact shapes will produce a deterministic, reviewable readiness report.

---

## 5. Where to look first

When the report says BLOCK or WARN, read in this order:

1. **`### Outcome determination` table** — score, blockers, warnings, and any outcome override.
2. **`### Warnings` / `### Blockers` lists** — the human-readable signals that drove the result.
3. **`### Failed checks`** — short keys (`smoke_artifact`, `e2e_critical`, …) for each signal. These are the join keys for `remediation` in `config.yaml`.
4. **`### Remediation guidance` table** — the recommended action for each failed check, populated from your `remediation` config.

For programmatic use, `report.json` carries everything the markdown shows, plus `critical_failed_titles` and `non_critical_failed_titles` arrays so a CI gate doesn't have to re-parse `playwright-results.json`.

---

## 6. Next steps

- **Wire your real evidence:** `docs/how-to/1-map-evidence.md` covers smoke / e2e schemas, the Playwright adapter, and how `infer_validations_when_pass` interacts with explicit JSON validations.
- **Tune the scoring:** `docs/how-to/2-tune-scoring.md` walks through penalties, thresholds, and avoiding the common "warning suppresses PASS at 100" anti-pattern.
- **Plug into CI:** `docs/how-to/3-ci-integration.md` shows the GitHub Checks pattern and a generic adapter pattern for non-GitHub CI.
- **Reference docs:** `docs/contracts/README.md` has the JSON schemas for inputs and outputs.

If something in this quickstart didn't behave as advertised, please open an issue against `release-readiness-core`.
