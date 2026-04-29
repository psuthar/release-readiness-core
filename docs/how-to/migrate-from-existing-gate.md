# Migrate from an existing readiness gate

Most teams adopting `release-readiness-core` already have *some* gate
in place — a hand-rolled GitHub Action that checks coverage, a script
that posts a sticky comment when CI fails, an internal "release
readiness" Slack message. This guide walks the migration without
breaking the existing flow on day one.

The strategy: **run both gates in parallel for one to two weeks, tune
the new one against real PRs, then cut over.** This is the same pattern
TalkBack used internally and the one we recommend to every new adopter.

> Prerequisites: the `release-readiness-doctor` command (introduced in
> v0.3.0). If it isn't available on your install, run
> `pip install --upgrade "git+https://github.com/psuthar/release-readiness-core.git@<sha>"`.

---

## 1. Inventory your existing gate

Before mapping anything, list — concretely — what your existing gate
*actually checks*. Be ruthless:

- Smoke pass/fail?
- E2E pass/fail? Per-suite?
- Coverage threshold?
- Coverage regression vs. some baseline?
- Migrations applied / verified?
- Specific files / paths that demand extra review?
- "Is the deploy-config touched without a sign-off note in the commit?"
- Error-rate snapshot from prod?

Write each line in plain English, like an audit checklist. The
`release-readiness-core` config keys map onto these one-to-one — the
hard part of migration is articulating what your old gate did, not the
YAML translation.

---

## 2. Map signals to validation keys

For each item in your inventory, decide:

- Is it **evidence** (something CI emits) or **a rule** (something the
  config asserts)?
- If evidence: what *validation key* does it satisfy? Pick a name that
  describes the *guarantee*, not the *check*. `auth_login_works` is
  better than `cypress_auth_suite_passes`.
- If a rule: does it map to `risk_from_paths` (path-pattern → required
  validation) or `risky_config_patterns` (require a validation note)?

Quick worked example:

| Existing gate signal | Maps to | Notes |
|---|---|---|
| Smoke suite green | `infer_validations_when_pass.smoke: [smoke_passing]` | Inference is fine here. |
| E2E auth suite green | `validations: { auth_login: ... }` + JUnit/Playwright validation map entry | Per-suite explicit booleans. |
| Coverage ≥ 85% | `coverage` evidence + `baseline_percent: 85` from `lcov-to-readiness` | Engine warns on regression. |
| Migrations applied in CI | `--migration-validated` CLI flag in your readiness step | Sets `migrations_validated: true`. |
| Touch `migrations/**` requires evidence | `risk_from_paths` rule with `risk_category_to_required_validation: { schema_changes: db_migrations }` | Risk mapping; see map-evidence.md. |
| Touch `.github/workflows/*.yml` requires sign-off | `risky_config_patterns: [.github/workflows/*.yml]` | Engine warns when no `Validation:` commit-message note. |

If a signal doesn't fit any of these, it probably belongs in a custom
adapter that emits one of the four evidence shapes. Hand-write the
JSON; the format is documented in
`docs/contracts/{smoke,e2e,coverage,pr-risk}-input-v1.schema.json`.

---

## 3. Author the new config and run it locally

Use the scaffold:

```bash
release-readiness-init my-project
```

…or copy `examples/second-project/config.yaml` and adapt. Then run the
doctor against your inventory before touching CI:

```bash
release-readiness-doctor \
  --config ops/release-readiness/config.yaml \
  --smoke-results evidence/smoke.json \
  --e2e-results evidence/e2e.json \
  --coverage evidence/coverage.json
```

Doctor catches the misconfigurations that would otherwise wait until
your first CI run: typos, evidence-shape mismatches, risk categories
without a mapping, and the `failed_count > 0 with empty failures`
inconsistency. Iterate until doctor reports zero errors.

Run a real evaluate against synthetic evidence:

```bash
release-readiness-evaluate \
  --repo-root . \
  --config ops/release-readiness/config.yaml \
  --smoke-results evidence/smoke.json \
  --e2e-results evidence/e2e.json \
  --coverage evidence/coverage.json \
  --empty-diff
```

Confirm the verdict matches what your *existing* gate would have
produced for the same inputs.

---

## 4. Run both gates in parallel

Add the new `release-readiness` workflow as a **non-required** check on
PRs alongside your existing gate. Don't gate merges on it yet.

In GitHub Actions:

```yaml
jobs:
  readiness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with: { fetch-depth: 0 }

      # ... collect evidence ...

      - uses: psuthar/release-readiness-core/.github/actions/release-readiness@<sha>
        with:
          package-ref: <sha>
          config-path: ops/release-readiness/config.yaml
          smoke-results: evidence/smoke.json
          e2e-results: evidence/e2e.json
          coverage: evidence/coverage.json
          enforcement-mode: block_only
```

Watch real PRs for at least one full release cycle (or two weeks,
whichever is longer). Look for:

- **False BLOCKs.** Some signal is too aggressive. Tune via
  `docs/how-to/tune-scoring.md`.
- **False PASSes.** Your old gate caught something this one missed.
  Trace the missing signal back to step 2's mapping.
- **Disagreements.** When the two gates disagree, log it. The discussion
  with reviewers about *why* they disagree is more valuable than the
  config tweak that follows.

---

## 5. Cut over

When the two gates have agreed on at least 10–15 PRs, including
non-trivial WARN/BLOCK cases, cut over:

1. Mark the `release-readiness` check as **required** in branch
   protection (see `docs/how-to/branch-protection.md`).
2. Remove the old gate. Don't leave it running "just in case" — two
   gates checking similar signals creates ambiguity about which one is
   authoritative when they disagree, and the project culture stops
   trusting either.
3. Announce the cut-over: in the PR-template, in the team's release
   doc, anywhere the old gate's verdicts were referenced.

Keep the `enforcement-mode: block_only` for another release cycle.
Promote to `warn_and_block` only when WARN false-positives are rare.

---

## 6. Common migration mistakes

- **Skipping step 1.** "We'll figure it out as we go" doesn't survive
  contact with real PRs. The inventory takes 30 minutes; the alternative
  is weeks of one-off tuning.
- **Mapping check names instead of guarantees.** `cypress_auth_suite_passes`
  becomes a problem the day you switch from Cypress to Playwright.
  `auth_login_works` is durable.
- **Promoting to required too quickly.** A required check that has
  produced even one bad BLOCK loses team trust permanently. Wait.
- **Keeping the old gate around.** See above. Pick one source of truth.

---

## 7. Cross-references

- `docs/how-to/quickstart.md` — the green-field path; review even if you're migrating, since vocabulary matches.
- `docs/how-to/map-evidence.md` — deep dive on validation keys and the two evidence channels.
- `docs/how-to/tune-scoring.md` — when to adjust thresholds vs. remove a noisy warning.
- `docs/how-to/branch-protection.md` — how to actually flip the required-check bit at cut-over.
- `docs/reference/outputs.md` — what every field in the report means; useful when explaining a verdict to skeptical reviewers.
