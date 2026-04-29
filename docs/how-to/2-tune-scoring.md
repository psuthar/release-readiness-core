# Tune scoring, penalties, and remediation

This guide is for adopters who have a working `release-readiness-core` setup (per `quickstart.md` and `map-evidence.md`) and want to make the deterministic scoring fit their project.

The engine's scoring is opinionated by default but every block is configurable. Knowing what each knob does — and how the knobs interact — is the difference between a useful gate and a noisy one.

> Worked example throughout: `examples/second-project/config.yaml`. All snippets below match that file unless explicitly different.

---

## 1. Mental model

Every readiness run produces three numbers and three lists:

- **`score`** — a float in `[0, max_score]`, starts at `max_score` and decreases as soft penalties fire.
- **`blockers`** — hard failures. Any blocker forces the outcome to BLOCK and floors the score to `block_score`.
- **`warnings`** — soft failures. They subtract from the score and, importantly, **suppress promotion to PASS**.
- **`reasons`**, **`failed_checks`**, **`recommended_actions`** — string arrays for human / agent consumption.

The outcome is a function of `score`, `blockers`, and `warnings`:

| Condition | Outcome |
|---|---|
| any blockers | **BLOCK** |
| no blockers, `score < warn_threshold` | **BLOCK** |
| no blockers, `score >= pass_threshold`, **0 warnings** | **PASS** |
| anything else (no blockers, `score >= warn_threshold`) | **WARN** |

This is implemented in `decide_outcome()` in `readiness_engine.py`.

The order matters: blockers beat thresholds, then thresholds beat warnings, then warnings demote PASS to WARN. There is no path from "score >= pass_threshold + warnings present" to PASS — that's the **warnings-suppress-PASS** rule and it's the single biggest source of "why isn't this PASS-ing?" surprise.

---

## 2. The `scoring` block

```yaml
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

### `max_score`, `pass_threshold`, `warn_threshold`

- `max_score` is the perfect-state ceiling. Penalties subtract from it.
- `pass_threshold` is the floor for a possible PASS. Score must reach it AND there must be 0 warnings.
- `warn_threshold` is the floor below which any run is **BLOCK**, even with no blockers. Treat it as "I lost so much confidence the score alone is a stop."
- `block_score` is the floor the engine clamps to when any blocker fires. Default is 0 — without it, you could see "score 90, outcome BLOCK" because the blocker doesn't carry a penalty by itself.

Tuning rule of thumb:

- Keep `max_score = 100` unless you have a specific reason; almost everything downstream assumes a 0–100 scale.
- `warn_threshold` should be far enough below `pass_threshold` that hitting it represents a serious confidence loss. 20 points is the default gap and it's a reasonable starting point.
- Lowering `pass_threshold` only helps if you also reduce penalty sizes — otherwise you're just papering over noisy gates.

### `penalties` — per-signal soft deductions

Each key here corresponds to a check the engine knows about. The names are stable and listed in `readiness_engine.py`. The defaults:

| Key | Default | When it fires |
|---|---|---|
| `missing_smoke_artifact` | 25 | `--smoke-results` not passed or unreadable. |
| `missing_e2e_artifact` | 15 | `--e2e-results` not passed or unreadable, or status is `skipped`. |
| `missing_coverage_artifact` | 5 | `--coverage` not passed. |
| `missing_prod_health_artifact` | 5 | `--prod-health` not passed. |
| `non_critical_e2e_failure` | 15 | An E2E failure title that doesn't match any `e2e_critical_name_patterns`. |
| `e2e_retries_or_flaky` | 10 | E2E artifact reports `retries > 0` (or `flaky_retried > 0`). |
| `coverage_regression` | 12 | Coverage `line_percent` < `baseline_percent`. |
| `risky_config_without_note` | 10 | A file matching `risky_config_patterns` changed AND no validation note is present. |

Tuning principles:

- **Bigger penalty ≠ stricter gate.** It only matters relative to your thresholds. Bumping `missing_e2e_artifact` from 15 to 25 has no effect if you also drop `pass_threshold` from 80 to 70.
- **Don't zero out penalties to hide noise.** If a missing coverage artifact is genuinely fine, set `penalties.missing_coverage_artifact: 0` AND understand you're losing the soft signal. The matching warning *still* appears (and still suppresses PASS — see §6).
- **The smoke penalty deserves its size.** Smoke is your last-ditch liveness check; making it cheap to skip is a footgun.

---

## 3. `e2e_critical_name_patterns` — promoting failures to blockers

```yaml
e2e_critical_name_patterns:
  - "auth_login"
  - "todo_crud"
```

The engine matches each E2E failure's title against this list (case- insensitive, substring match). Any match promotes that failure to a **critical blocker** — the outcome becomes BLOCK regardless of score. Non-matching failures stay as warnings (with the `non_critical_e2e_failure` penalty applied).

Use this list to encode "if any of these break, ship is unsafe":
- Login / auth flows.
- Anything that touches data the user paid for or that you'd hate to corrupt (CRUD on core entities).
- Anything you'd page someone for at 3am.

Anti-pattern: putting *every* test name in `e2e_critical_name_patterns`. Now nothing is critical, because everything is.

---

## 4. The `remediation` map — actionable failure messages

When a check fails, the engine emits a `failed_checks` entry like `smoke_artifact` or `e2e_critical`. The `remediation` block in your config maps each key to a structured remediation row:

```yaml
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

  risk_without_validation:
    severity: block
    likely_cause: changed area requires evidence that was not provided
    recommended_action: Run the relevant validation in CI and emit a boolean in the evidence JSON.
    fix_type: ci_config
```

Each `remediation` entry surfaces in the markdown report's "Remediation guidance" table and in `report.json` as `remediation_items[]`. CI gates and reviewer agents read these to suggest concrete next steps without having to know the engine's internals.

The full set of `failed_checks` keys produced by the engine:

`smoke_artifact`, `smoke_parse_error`, `smoke_failed`, `e2e_artifact`, `e2e_skipped`, `e2e_critical`, `e2e_non_critical`, `e2e_retries`, `coverage_regression`, `risky_config_without_note`, `pr_risk_block`, `pr_risk_warn`, `risk_without_validation`.

Cover at least these in `remediation` for any production-bound config; the engine will emit a "Investigate check: <name>" placeholder for any key you skip, which is fine for triage but not great for adopters.

---

## 5. Worked example: tuning a PASS into WARN

Start with `examples/second-project/config.yaml`. The fixture's synthetic evidence produces `PASS, score=100`.

Now imagine you want to tighten the gate so a coverage shortfall fails the build.

**Change 1** — add a stricter coverage baseline:

```diff
- "line_percent": 88.2,
- "baseline_percent": 85.0
+ "line_percent": 84.5,
+ "baseline_percent": 85.0
```

Now `coverage_regression` fires, the warning lands, and the score drops by 12 (the `coverage_regression` penalty).

Re-run:

```
## Result: **WARN** (score 88.0)
### Warnings
- Coverage regression: 84.5% vs baseline 85.0%
```

Why WARN, not PASS? Score 88 is above `pass_threshold` (80), but the new warning suppresses promotion. **The penalty alone wouldn't have demoted the run** — the warning did.

**Change 2** — make coverage regression a blocker by raising its penalty above the warn threshold:

```yaml
scoring:
  ...
  penalties:
    coverage_regression: 30   # was 12
```

Re-run: score drops by 30 (from 100 to 70). 70 ≥ 60 (warn threshold), so still WARN, not BLOCK. To force BLOCK on coverage shortfall you'd raise the penalty above 40 (so score lands < 60), or — cleaner — use `risk_from_paths` to require an explicit "coverage_acceptable" validation that you only emit when the regression is acceptable.

The lesson: **soft penalties alone can't cause BLOCK** unless they push score below `warn_threshold`. Real BLOCK conditions belong in the blocker path: smoke fail, critical E2E, missing required validation, or a `pr_risk` enforcement of `BLOCK`.

---

## 6. Anti-patterns

### "PASS at score 100 still demoted to WARN"

This is the `outcome_overrides` exit you'll see most often. It happens because a warning fired but its penalty was 0 or trivially small. The warning text *itself* is the cause, not the score.

Two valid responses:

- If the warning is genuinely noise: gate it behind a config knob (e.g. supply a stub `prod_health.json`), or don't pass the relevant CLI flag at all so the corresponding warning never fires.
- If the warning reflects something real: leave it. PASS is not the goal; "deploy is safe" is the goal.

The anti-pattern is **lowering `pass_threshold` so that warnings fit under the bar**. That doesn't suppress the warning — it's still a warning, still demotes to WARN. It just degrades the signal.

### Penalties bigger than `(max_score - warn_threshold)`

A single 50-point penalty against a 100-point ceiling and a 60 warn threshold means one failure → BLOCK no matter what. That's fine if you mean it, but you should mean it. Otherwise you're using a soft penalty to do a blocker's job — express it as a blocker instead (via `risk_from_paths` requiring a validation, or a critical E2E pattern).

### Disabling a check by zeroing its penalty

`penalties.missing_e2e_artifact: 0` doesn't disable the missing-E2E warning; it just removes the score penalty. The warning still appears and still suppresses PASS. To genuinely opt out of a check, don't pass the relevant CLI flag — but then any required-validation logic that depends on E2E evidence will report `not_evaluated`, which is its own form of demotion.

For artifacts that are *legitimately* optional in your project (e.g. no production-health monitoring source, no coverage tracking), use `optional_artifacts` to suppress the warning and the penalty together:

```yaml
optional_artifacts:
  - prod_health
  - coverage
```

When an artifact is in this list and absent at run time, the engine neither warns nor deducts. Use sparingly — the artifacts are only "optional" for projects that genuinely don't have them; suppressing them in a project that does is just hiding signal.

### Blanket-critical E2E patterns

`e2e_critical_name_patterns: ["test"]` matches every E2E failure as critical. Now you can't tell which failure actually mattered. Be specific: name the flows, not the substrings.

---

## 7. Cross-references

- `docs/how-to/0-quickstart.md` — bootstrap a fresh project before tuning.
- `docs/how-to/1-map-evidence.md` — wire validation evidence; `risk_from_paths` and `risk_category_to_required_validation` are the source of *required* validations that interact with this scoring layer.
- `docs/how-to/3-ci-integration.md` — surface PASS/WARN/BLOCK in GitHub Checks and other CIs.
- `docs/contracts/validation-config-v1.schema.json` — every field referenced here, machine-readable.
