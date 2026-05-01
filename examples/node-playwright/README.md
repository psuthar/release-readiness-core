# Example: Node service with Playwright E2E

Greenfield Playwright project showing how to wire `release-readiness-core` into
a Node repo. Uses Playwright JSON reporter -> `playwright-to-readiness` for the
e2e shape.

## Layout

```
.github/workflows/release-readiness.yml   # Tier-1 reusable-workflow drop-in
ops/release-readiness/config.yaml         # validations + scoring + remediation
ops/release-readiness/validation_map.yaml # Playwright file stem -> readiness key
```

## Copy into your repo

1. Copy `.github/workflows/release-readiness.yml` into your repo's `.github/workflows/`.
2. Copy `ops/release-readiness/` into your repo.
3. Replace every `<sha>` literal in the workflow with a pinned `release-readiness-core`
   release SHA. (Or scaffold pre-pinned: `release-readiness-init --pin <sha>`.)
4. Adjust `validation_map.yaml` to map Playwright file stems -> validation keys.
5. Open a PR. The `release-readiness` Check should appear within a few minutes.

## What this example assumes

- Playwright is installed and runnable (`npx playwright test`).
- Tests live under `tests/` (or wherever your `playwright.config` points).
- The Playwright JSON reporter is enabled (or the workflow passes `--reporter=json`).

## Where to look next

- `docs/how-to/0-quickstart.md`
- `docs/how-to/1-map-evidence.md`
- `docs/how-to/8-recipe-matrix.md`
