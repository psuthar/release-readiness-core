# Example: Python service with pytest + JUnit XML

Greenfield pytest project showing how to wire `release-readiness-core` into a
Python repo. Uses `pytest --junit-xml` -> `junit-to-readiness` for the e2e
shape.

## Layout

```
.github/workflows/release-readiness.yml   # Tier-1 reusable-workflow drop-in
ops/release-readiness/config.yaml         # validations + scoring + remediation
ops/release-readiness/validation_map.yaml # JUnit classname -> readiness key
```

## Copy into your repo

1. Copy `.github/workflows/release-readiness.yml` into your repo's `.github/workflows/`.
2. Copy `ops/release-readiness/` into your repo.
3. Replace every `<sha>` literal in the workflow with a pinned `release-readiness-core`
   release SHA. (Or scaffold pre-pinned: `release-readiness-init --pin <sha>`.)
4. Adjust `config.yaml` validations to match the guarantees your service needs.
5. Adjust `validation_map.yaml` to map JUnit classnames -> validation keys.
6. Open a PR. The `release-readiness` Check should appear within a few minutes.

## What this example assumes

- You run `pytest` and emit JUnit XML at `test-results.xml`.
- Your tests cover the validations declared in `ops/release-readiness/config.yaml`.
- The `release-readiness-core` package is reachable from your CI runner.

## Where to look next

- `docs/how-to/0-quickstart.md` — broader walkthrough.
- `docs/how-to/1-map-evidence.md` — wiring CI evidence to validation keys.
- `docs/how-to/8-recipe-matrix.md` — drop-in snippets for other stacks.
