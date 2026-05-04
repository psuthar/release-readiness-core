## release-readiness-core

A deterministic release-readiness engine: same evidence in, same PASS / WARN / BLOCK out. Project-agnostic, configured in YAML, with adapters for Playwright, JUnit, and LCOV — and a four-command quickstart that lands a green Check on your first PR.

### Sample apps

End-to-end working examples — the fastest way to see the gate in motion on real PRs:

- [`release-readiness-sample-app`](https://github.com/psuthar/release-readiness-sample-app) (Go) — Phase-2 rollout: `--enforcement-mode block_only` paired with `WARN → neutral` Check mapping. WARN visible on PRs but doesn't block merge.
- [`release-readiness-node-js-sample-app`](https://github.com/psuthar/release-readiness-node-js-sample-app) (TypeScript) — Phase-3 rollout: `--enforcement-mode warn_and_block` paired with `WARN → failure` Check mapping. WARN PRs are blocked from merging.

Reading the two side by side shows the full phased adoption path.

### Package layout

| Path | Role |
|------|------|
| `release_readiness_core.engine` | Core validation merge types and deterministic summary |
| `release_readiness_core.pr_gate` | Generic N-input PR gate combiner |
| `release_readiness_core.readiness_engine` | Full artifact-based PASS/WARN/BLOCK evaluation |
| `release_readiness_core.cli` | CLI entries `release-readiness` (validation summary) and `release-readiness-evaluate` (YAML + artifacts) |
| `release_readiness_core.readiness_io` | JSON/YAML/git helpers for evaluate |
| `release_readiness_core.adapters` | Optional helpers (Playwright → schema, GitHub check payloads) |

### Quickstart

The shortest path to a green `release-readiness` Check on your first PR is **four commands**:

```bash
pip install "release-readiness-core==0.4.0"
release-readiness-init my-project --demo --stack <go|pytest|jest|playwright|cypress|vitest|go-coverage>
cd my-project && git init && git add . && git commit -m "release-readiness scaffold"
# push, open a PR — the release-readiness Check appears
```

`--demo` ships synthetic green evidence so the first PR proves your CI plumbing before you've changed any product code. Full walkthrough including the seven-stage path from synthetic green to a required gate on `main`: [`docs/how-to/0-quickstart.md`](docs/how-to/0-quickstart.md).

**Toolchain:** docs standardize on **`pip install`** for local / PyPI adoption; some **GitHub Actions** examples use **`uvx --from …`** so CLIs work on PEP 668–managed runners without a venv dance. Why both appear: [`docs/how-to/9-adoption-tiers.md`](docs/how-to/9-adoption-tiers.md#python-install-paths-pragmatic).

### Direct CLI usage

If you'd rather skip the scaffold and call the engine directly:

```bash
uv run release-readiness --input-json '[{"key":"go-test","status":"PASS"}]'
```

Evaluate from a YAML config and JSON evidence (writes `report.json`, `report.md`, `release-readiness.json`):

```bash
uv run release-readiness-evaluate --repo-root . --config path/to/config.yaml \
  --empty-diff --output-dir artifacts/release-readiness
```

### Adapter CLIs

```bash
# Playwright JSON reporter -> readiness e2e shape
uv run playwright-to-readiness --input playwright-results.json --output e2e_results.json \
  --validation-map ops/release-readiness/validation_map.yaml

# JUnit XML (Cypress / Jest / pytest / Mocha / etc.) -> readiness e2e shape
uv run junit-to-readiness --input test-results.xml --output e2e_results.json \
  --validation-map ops/release-readiness/validation_map.yaml

# LCOV info -> readiness coverage shape
uv run lcov-to-readiness --input coverage/lcov.info --output coverage.json \
  --baseline-percent 85

# PR-risk semantic combiner (consumes existing pr-risk.json)
uv run pr-risk-semantic --pr-risk-json artifacts/pr-risk.json --generator-outcome success
```

`--validation-map` is optional on Playwright and JUnit; without it the converter emits an empty `validations` object (counts and failures still reported). For Playwright, override default spec extensions with `--spec-extensions ts,js,mjs,e2e`.

The N-input PR gate combiner lives in `release_readiness_core.pr_gate` (`combine_gate_inputs`).

### Install from PyPI (version-pinned)

```bash
pip install "release-readiness-core==0.4.0"
```

### Install from Git (SHA-pinned)

```bash
pip install "git+https://github.com/psuthar/release-readiness-core.git@<sha>"
```

Use this when you need an unreleased commit or a fork. Release policy and versioning: [`RELEASE.md`](RELEASE.md).

### Development

```bash
uv run pytest
uv build
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for branch/PR conventions and how to add an adapter.

### Configuring PR Risk for your project

`release-readiness-pr-risk` ships a generic, language-agnostic baseline by default — domains classify everything to `other`, only generic gates (CI fetch depth, PR review summary, workflow / config validation, add tests / evidence, intent alignment, scattered review plan, test proximity, hotspot regression) fire. To make it project-specific (auth E2E gate when `src/auth/` changes, migration validation when SQL files change, etc.), author a `pr-risk-config.yaml`:

- Walkthrough: [`docs/how-to/7-configure-pr-risk.md`](docs/how-to/7-configure-pr-risk.md)
- Predicate vocabulary + detector template reference: [`docs/reference/pr-risk-config.md`](docs/reference/pr-risk-config.md)
- Examples: [`examples/pr-risk/python-service.yaml`](examples/pr-risk/python-service.yaml), [`examples/pr-risk/node-service.yaml`](examples/pr-risk/node-service.yaml)
- Schema: [`docs/contracts/pr-risk-config-v1.schema.json`](docs/contracts/pr-risk-config-v1.schema.json)

`release-readiness-init` writes a commented starter at `ops/release-readiness/pr-risk-config.yaml`; `release-readiness-doctor --pr-risk-config <path>` validates it (typos, malformed predicates, references to undeclared domains, unknown evidence templates).

### How-to guides

- Quickstart — adopt the package in a new project: `docs/how-to/0-quickstart.md`
- Map evidence — wire CI artifacts to validation keys: `docs/how-to/1-map-evidence.md`
- Tune scoring — penalties, thresholds, remediation: `docs/how-to/2-tune-scoring.md`
- CI integration — GitHub Checks and the generic adapter pattern: `docs/how-to/3-ci-integration.md`
- Multi-job CI — split smoke / e2e / coverage across jobs: `docs/how-to/4-multi-job-ci.md`
- Branch protection — make the readiness check required: `docs/how-to/5-branch-protection.md`
- Migrating from an existing gate: `docs/how-to/6-migrate-from-existing-gate.md`
- Configure PR Risk for your project: `docs/how-to/7-configure-pr-risk.md`
- Recipe matrix — adapter snippets per stack (Playwright / pytest / Cypress / Jest / Vitest / Go): `docs/how-to/8-recipe-matrix.md`
- Adoption tiers — pick reusable workflow vs. composables vs. raw CLIs: `docs/how-to/9-adoption-tiers.md`

### Reference

- Outputs glossary — every field in `report.json` / `release-readiness.json` explained: `docs/reference/outputs.md`
- JSON contracts: `docs/contracts/`
- Release process and SHA-pin policy: `RELEASE.md`
- Changelog: `CHANGELOG.md`

### Pre-flight

Before wiring CI, run the doctor against your scaffolded config:

```bash
release-readiness-doctor --config ops/release-readiness/config.yaml \
  --smoke-results evidence/smoke.json \
  --e2e-results evidence/e2e.json \
  --coverage evidence/coverage.json
```

Doctor catches config typos, evidence-shape mismatches, and common inconsistencies (e.g. `failed_count > 0` but `failures: []`) before they reach a real run. Exits non-zero on any error.

### Two CLIs — when to use which

- `release-readiness-evaluate` — the **full evaluator**. Loads `config.yaml`, reads evidence files, computes PASS/WARN/BLOCK, writes `report.json` / `report.md` / `release-readiness.json`. **Use this in CI.**
- `release-readiness` — a **lightweight summary** of validation booleans given inline JSON. No scoring, no thresholds, no artifacts on disk. Useful for quick sanity checks (`release-readiness --input-json '[{"key":"x","status":"PASS"}]'`) or as a debugging probe in scripts. **Not a substitute for the evaluator in production CI.**

### Contracts

- PR risk input schema: `docs/contracts/pr-risk-input-v1.schema.json`
- Readiness output schema: `docs/contracts/release-readiness-output-v1.schema.json`
- Validation config schema: `docs/contracts/validation-config-v1.schema.json`
- Contract reference guide: `docs/contracts/README.md`

### Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for development setup, PR conventions, and how to add an adapter for a new test runner. Maintainer-specific tooling (MCP servers, Jira automation) lives there too.
