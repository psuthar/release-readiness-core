# Outputs reference — what every report field means

This is the field-by-field reference for everything
`release-readiness-core` writes to disk. When a reviewer or an adopter
asks "what does *this* mean?" — point them here.

The package writes three files:

| File | Audience | Format |
|---|---|---|
| `report.md` | Humans (PR comments, CI step summary) | Markdown |
| `report.json` | Programmatic consumers (downstream automation, dashboards) | JSON |
| `release-readiness.json` | The gate / branch protection | JSON, lean |

`report.md` and `report.json` cover the same content; `report.json` is
the source of truth for fields, and `report.md` is its rendering.
`release-readiness.json` is a separate, intentionally-minimal summary.

---

## 1. `release-readiness.json` — the gate

The lean machine summary. Designed to be tiny and stable so CI gates
and other tooling can `jq -r .outcome` without parsing the full
report.

```json
{
  "outcome": "PASS | WARN | BLOCK",
  "score": 95.0,
  "warnings": 1,
  "blockers": 0
}
```

| Field | Type | Notes |
|---|---|---|
| `outcome` | string | One of `PASS`, `WARN`, `BLOCK`. The gate-defining field. Branch-protection wrappers usually map this to `success` / `neutral` / `failure`. |
| `score` | float | 0..100. Rounded to one decimal. Use for trend dashboards; do not use for gating (the engine already did that work). |
| `warnings` | int | Count of warning strings in `report.json.warnings`. |
| `blockers` | int | Count of blocker strings in `report.json.blockers`. |

If `compute_readiness` itself crashes — for example, the config fails
to load — this file is still written, with `execution_failed: true`
and `error: "<truncated message>"` added. Treat that as `outcome:
BLOCK` for gating purposes.

---

## 2. `report.json` — the full payload

Top-level structure:

```json
{
  "outcome": "WARN",
  "score": 85.0,
  "max_score": 100.0,
  "pass_threshold": 80.0,
  "warn_threshold": 60.0,
  "reasons": [...],
  "warnings": [...],
  "blockers": [...],
  "failed_checks": [...],
  "changed_files": [...],
  "risks_triggered": [...],
  "validations": {...},
  "validations_required": [...],
  "evidence": {...},
  "recommended_actions": [...],
  "remediation_items": [...],
  "outcome_overrides": [...],
  "critical_failed_titles": [...],
  "non_critical_failed_titles": [...],
  "timestamp_utc": "...",
  "config_path": "...",
  "base_ref": "origin/main",
  "deterministic_summary": "WARN: score=85.0, blockers=0, warnings=1",
  "pr_risk": {...?}
}
```

### Outcome and score

| Field | Type | Meaning |
|---|---|---|
| `outcome` | string | Final verdict: PASS, WARN, BLOCK. See `decide_outcome` in the engine source. |
| `score` | float | Same as `release-readiness.json.score`. |
| `max_score` | float | Configured ceiling (default 100). |
| `pass_threshold` | float | Score floor for PASS (default 80). PASS also requires zero warnings. |
| `warn_threshold` | float | Score floor for WARN (default 60). Below this, outcome is BLOCK regardless of blockers. |

### Why the outcome is what it is

| Field | Type | Meaning |
|---|---|---|
| `reasons` | string[] | Human-readable explanations of the score and risk path (e.g. "Score=85.0/100 (PASS: score>=80…)"). |
| `warnings` | string[] | Soft-failure messages that demoted the run (or were demoted *to* by hard rules). PASS is impossible while this is non-empty. |
| `blockers` | string[] | Hard-failure messages. Any non-empty list forces BLOCK. |
| `failed_checks` | string[] | Short keys for each warning/blocker — the join key for `remediation` in `config.yaml`. Examples: `smoke_artifact`, `e2e_critical`, `coverage_regression`. See `docs/how-to/tune-scoring.md` §4 for the full list. |
| `outcome_overrides` | string[] | Non-empty when the final outcome differs from what `score` alone would produce. The most common case: `warnings_suppress_pass` (score in PASS range but warnings demoted to WARN). |

### What changed and what risks fired

| Field | Type | Meaning |
|---|---|---|
| `changed_files` | string[] | Files in `git diff <base-ref>...HEAD`. Empty when `--empty-diff` was passed. |
| `risks_triggered` | string[] | Risk-category names from `risk_from_paths` that matched at least one changed file. |
| `validations_required` | string[] | Validation keys that *must* be satisfied because of triggered risks. Resolved via `risk_category_to_required_validation` (with identity fallback). |

### Validations

```json
"validations": {
  "auth_login":   "satisfied",
  "db_migrations": "missing",
  "search":        "not_required"
}
```

| Status | Meaning |
|---|---|
| `satisfied` | Required by a risk and evidenced by smoke/E2E. Good. |
| `missing` | Required by a risk but no evidence satisfied it. The engine adds `risk_without_validation` to `failed_checks` and a blocker line. |
| `not_required` | Evidenced (true) but not required by any risk this run. Informational. |
| `not_evaluated` | Required, but neither smoke nor E2E artifacts were provided — the package can't disprove or prove it. |

A key absent from this map either wasn't required *and* wasn't
evidenced, or wasn't declared in `validations:` and didn't appear in
any evidence — pure noise either way.

### Evidence summary

```json
"evidence": {
  "smoke_present": true,
  "e2e_present":   true,
  "coverage_present": false,
  "prod_health_present": false,
  "validation_note_present": true,
  "validation_note_source": "commit_message",
  "validation_note_snippet": "Validation: schema migration verified in CI"
}
```

`*_present` booleans answer "did the engine see this artifact?".
`validation_note_*` covers the `Validation:` / `Validate:` commit
message convention; see `docs/how-to/map-evidence.md` §5.

### Remediation

```json
"remediation_items": [
  {
    "check":              "smoke_artifact",
    "severity":           "warn",
    "likely_cause":       "smoke job did not upload results",
    "recommended_action": "Re-run smoke job and upload smoke.json artifact.",
    "fix_type":           "ci_config"
  }
]
```

One entry per `failed_checks` key, populated from `remediation` in
`config.yaml`. Unmapped keys get a placeholder
`"Investigate check: <key>"` so reviewers always have *something* to
go on. Tune via `docs/how-to/tune-scoring.md` §4.

### E2E failure detail

```json
"critical_failed_titles":     ["LoginFlow.fails_for_unknown_user"],
"non_critical_failed_titles": ["DiagnosticsTab.shows_extra_info"]
```

The full list of E2E failure titles, classified by whether they
matched any pattern in `e2e_critical_name_patterns`. Use these instead
of re-parsing `playwright-results.json` / JUnit XML — they're the
post-classification view the engine itself used.

### Other

| Field | Type | Meaning |
|---|---|---|
| `timestamp_utc` | string | When the run produced the report. ISO 8601. |
| `config_path` | string | The exact `config.yaml` path that was loaded. |
| `base_ref` | string | The `--base-ref` used for the diff. |
| `deterministic_summary` | string | Compact human-readable verdict, intentionally stable for log scraping. |
| `pr_risk` | object? | Mirror of the consumed `pr_risk.json` *if present*. Absent when no PR-risk source. |

---

## 3. `report.md` — the rendered version

`report.md` is `report.json` rendered through
`render_readiness_result_markdown`. Sections appear in this order:

1. **Heading** — `# Release readiness report` (or the configured `--report-title`).
2. **Result** — `## Result: **PASS** (score N.N)`.
3. **Outcome determination** — table with score, score band, blockers count, warnings count, override (when any), and the `Why:` line.
4. **Blockers** — bulleted list, only when non-empty.
5. **Warnings** — bulleted list, only when non-empty.
6. **Summary** — the `reasons` array.
7. **Risks from changed paths** — bulleted list, with `(none)` when empty.
8. **Validations** — table, **omitted entirely when no validations are present** (post-SCRUM-209 fix).
9. **Failed checks** — bulleted list, only when non-empty.
10. **Recommended actions** — high-level next steps.
11. **Remediation guidance** — table from `remediation_items`.
12. **Footer** — "Deterministic scoring only (no LLM in the decision path)."

If you're tempted to parse `report.md` programmatically, parse
`report.json` instead — the markdown is for humans and its layout
will continue to evolve.

---

## 4. Where each field comes from

A reverse map for the "where does this come from?" question:

| Field | Engine source |
|---|---|
| `outcome`, `score`, `max_score`, `*_threshold` | `decide_outcome` + score arithmetic |
| `blockers`, `warnings` | Hard rules (smoke fail, critical E2E, missing required validation, PR-risk BLOCK) for blockers; soft penalties (missing artifacts, retries, coverage regression, PR-risk WARN, risky-config-without-note) for warnings. |
| `failed_checks` | Each warning/blocker appends a key. Used as the join into `remediation`. |
| `validations` | `merge_validations` (explicit booleans + inference) plus the `--migration-validated` CLI flag. |
| `risks_triggered`, `validations_required` | `risks_for_files` over `risk_from_paths`, then `risk_category_to_required_validation`. |
| `evidence.validation_note_*` | `git log` commit messages between `--base-ref` and HEAD, scanned for `Validation:` / `Validate:` lines. |
| `pr_risk` | The optional `pr_risk.json` artifact at `<output-dir>/pr_risk.json`. Absent → field absent. |

Find the engine code itself in
`src/release_readiness_core/readiness_engine.py` if you need to trace a
specific value back to its rule.

---

## 5. Cross-references

- `docs/how-to/quickstart.md` — first-time read.
- `docs/how-to/map-evidence.md` — how validations get satisfied.
- `docs/how-to/tune-scoring.md` — penalties, thresholds, and the full `failed_checks` key list.
- `docs/contracts/release-readiness-output-v1.schema.json` — machine-readable schema for `release-readiness.json`.
