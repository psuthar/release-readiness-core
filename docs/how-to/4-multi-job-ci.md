# Multi-job CI — when smoke, E2E, and coverage live in separate jobs

The walkthrough in `ci-integration.md` runs everything in one job for
clarity. Real CIs almost never look like that — smoke runs on one
matrix, E2E runs on another (often parallelized across browsers),
coverage is a separate job, and the readiness step at the end gathers
the artifacts.

This guide shows the artifact-sharing pattern in GitHub Actions and
the equivalent shape in non-GitHub CIs.

> Prerequisites: a working single-job pipeline first
> (`docs/how-to/0-quickstart.md` and `docs/how-to/3-ci-integration.md`).
> Don't split until the simple version passes locally and against
> `release-readiness-doctor`.

---

## 1. Pattern: one readiness job depending on N evidence jobs

In GitHub Actions, each evidence-emitting job uploads its JSON via
`actions/upload-artifact`, and the readiness job downloads them all
before invoking the evaluator.

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
  smoke:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - run: ./ci/run-smoke.sh   # writes evidence/smoke.json
      - uses: actions/upload-artifact@v4
        with:
          name: readiness-evidence-smoke
          path: evidence/smoke.json
          if-no-files-found: error

  e2e:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        browser: [chromium, firefox]
    steps:
      - uses: actions/checkout@v5
      - run: npx playwright test --project=${{ matrix.browser }} --reporter=json > playwright.json
      - run: |
          playwright-to-readiness \
            --input playwright.json \
            --output evidence/e2e-${{ matrix.browser }}.json \
            --validation-map ops/release-readiness/validation_map.yaml
      - uses: actions/upload-artifact@v4
        with:
          name: readiness-evidence-e2e-${{ matrix.browser }}
          path: evidence/e2e-${{ matrix.browser }}.json

  coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - run: ./ci/run-coverage.sh   # writes coverage/lcov.info
      - run: |
          lcov-to-readiness \
            --input coverage/lcov.info \
            --output evidence/coverage.json \
            --baseline-percent 85
      - uses: actions/upload-artifact@v4
        with:
          name: readiness-evidence-coverage
          path: evidence/coverage.json

  readiness:
    needs: [smoke, e2e, coverage]
    if: always()                      # run even if a dependency failed
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
        with: { fetch-depth: 0 }

      - uses: actions/download-artifact@v4
        with:
          path: evidence-raw
          pattern: readiness-evidence-*
          merge-multiple: true

      # Reorganize artifacts to the structure the CLI expects.
      # `merge-multiple: true` flattens artifact dirs into one folder.
      - name: Stage evidence
        run: |
          mkdir -p evidence
          cp evidence-raw/smoke.json evidence/smoke.json
          cp evidence-raw/coverage.json evidence/coverage.json
          # Pick the worst e2e result across browsers (project-specific):
          jq -s 'sort_by(.failed_count) | reverse | .[0]' \
            evidence-raw/e2e-*.json > evidence/e2e.json

      - uses: psuthar/release-readiness-core/.github/actions/release-readiness@<sha>
        with:
          package-ref: <sha>
          config-path: ops/release-readiness/config.yaml
          smoke-results: evidence/smoke.json
          e2e-results: evidence/e2e.json
          coverage: evidence/coverage.json
          enforcement-mode: block_only
```

Two things to call out:

- **`if: always()`** on the readiness job ensures it runs even when a
  dependency fails. Without this, a failing smoke job skips readiness
  entirely — and reviewers see no readiness verdict on a PR that most
  needs one.
- **The "stage evidence" step** is the project-specific glue. The
  example combines two browsers' E2E results into one by picking the
  worst — your project might want to merge them, run readiness twice,
  or fail if browsers disagreed. Don't optimize this prematurely;
  start with "pick the worst" and iterate.

---

## 2. Splitting evidence across more than three jobs

The pattern generalizes. For each independent evidence source:

1. Run it in its own job, emitting its readiness-shape JSON.
2. Upload the JSON as `readiness-evidence-<name>`.
3. The readiness job downloads all artifacts matching
   `pattern: readiness-evidence-*` and stages them into one
   `evidence/` directory.
4. The CLI is invoked once with `--smoke-results`, `--e2e-results`,
   `--coverage`, and (if configured) `--prod-health` pointing at the
   staged files.

If you have a fifth evidence source (e.g. a custom security scan),
either:

- Map it onto an existing slot (e.g. fold security-scan results into
  the smoke JSON via `validations: {security_scan: true}`), or
- Treat it as a separate gate input and combine via
  `release_readiness_core.pr_gate.combine_gate_inputs` — see
  `ci-integration.md` §4 (generic formatter pattern).

---

## 3. Non-GitHub CIs

The shape transfers directly. In every CI you need three primitives:

1. **Per-job artifacts:** the equivalent of `upload-artifact`. GitLab
   has `artifacts:`, Buildkite has `buildkite-agent artifact upload`,
   CircleCI has `store_artifacts`, Jenkins has `archiveArtifacts`.
2. **Cross-job artifact retrieval:** the equivalent of
   `download-artifact`. Same vendors expose either an explicit fetch
   step or a `dependencies:` declaration that auto-fetches.
3. **Conditional execution:** the equivalent of `if: always()`. GitLab
   has `when: always`, Buildkite has `soft_fail`, CircleCI has
   `when: always`.

Once those three primitives are wired, the readiness step is identical
to the single-job case: collect the staged JSON, invoke
`release-readiness-evaluate`.

---

## 4. Common pitfalls

### "Readiness ran but didn't see my evidence"

90% of the time this is `merge-multiple: true` flattening artifact
directories in unexpected ways. Verify by listing the staged dir
before invoking readiness:

```yaml
- run: ls -la evidence-raw/ && find evidence/ -type f
```

If a file isn't there, the upload step probably named it differently
than the read step expects.

### "Readiness reports BLOCK but every dependency was green"

The dependency jobs probably exited 0 even though their evidence said
failed. Check each evidence JSON manually — `failed_count > 0` with
`status == "passed"` is a common bug in custom emitters.

`release-readiness-doctor` catches this if you wire it as a separate
job:

```yaml
  doctor:
    needs: [smoke, e2e, coverage]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/download-artifact@v4
        with: { path: evidence, pattern: readiness-evidence-*, merge-multiple: true }
      - run: pip install "git+https://github.com/psuthar/release-readiness-core.git@<sha>"
      - run: |
          release-readiness-doctor \
            --config ops/release-readiness/config.yaml \
            --smoke-results evidence/smoke.json \
            --e2e-results evidence/e2e.json \
            --coverage evidence/coverage.json
```

A doctor failure is cheap and catches most "evidence emitter is
buggy" cases before they hit the real gate.

### "Coverage shows up as missing, but my coverage job uploaded the file"

Either the artifact name didn't match the download pattern, or the
coverage job uploaded `lcov.info` instead of running
`lcov-to-readiness`. The CLI consumes the readiness shape, not raw
lcov.

---

## 5. Cross-references

- `docs/how-to/3-ci-integration.md` — the single-job version; this guide
  builds on it.
- `docs/how-to/5-branch-protection.md` — once the multi-job workflow is
  green, this is how you make it required.
- `release-readiness-doctor --help` — pre-flight verifier; ideal for
  catching emitter bugs before they reach the gate.
