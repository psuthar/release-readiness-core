# Changelog

All notable changes to this project will be documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). See `RELEASE.md` for PyPI version pins, git SHA pins, and the release checklist.

## [Unreleased]

### Added
- **`--warn-conclusion` flag on `release-readiness-check-payload`** and a corresponding `warn-conclusion` input on the reusable workflow (`.github/workflows/readiness.yml`) and the `release-readiness-pr-gate` composite action. Choices: `action_required` (default — blocks PR merge but keeps the workflow green; matches existing behavior), `failure` (blocks merge AND turns the workflow red — strict Phase-3 rollout), `neutral` (visible but non-blocking — Phase-1/2 soft rollout). Lets Tier-1/Tier-2 adopters reach strict Phase-3 enforcement without forking. Default preserves current behavior — non-breaking.
- **`docs/contracts/prod-health-input-v1.schema.json`** — versioned schema for the `prod_health` evidence artifact consumed by `--prod-health`. Documents the shape both reference probes produce (`url`, `healthy`, `http_status`, `latency_ms`, `checked_at`, `source`, `body`, optional `error`).
- **§3.5 "Choosing the WARN Check conclusion"** in `docs/how-to/3-ci-integration.md`, with a three-option table (`neutral` / `action_required` / `failure`), Tier 1/2/3 wiring instructions, and a callout for the Tier-3 "two-edit dance" (enforcement-mode flag AND conclusion mapping must change together).
- Phase-3 promotion guidance in `docs/how-to/5-branch-protection.md` §3 explaining the Tier-1 vs Tier-3 mechanics.
- Production-health subsection (§2.1) in `docs/how-to/1-map-evidence.md` with schema reference and pointers to the Go and TypeScript reference probes.
- Cross-references to both sample apps (Go = Phase 2, TypeScript = Phase 3) in `docs/how-to/8-recipe-matrix.md` and `docs/how-to/9-adoption-tiers.md`.

### Changed
- `pr-gate-check-v1.schema.json` — `check_conclusion` enum extended to include `neutral` (was `["success", "action_required", "failure"]`). Description updated to reflect that WARN's conclusion is now configurable.
- `docs/contracts/README.md` — input list now includes `prod-health-input-v1`; status mapping table flags WARN's conclusion as override-able.
- Description on the `release-readiness` composite action clarified: evaluate-only, no Check publication.
- `docs/how-to/3-ci-integration.md` Tier-3 example `conclusionMap` updated from `WARN: 'neutral'` to `WARN: 'action_required'` to match the reusable-workflow default. The previous example was a silent footgun for Tier-3 adopters who later promoted to Phase 3.

## [0.3.4] — 2026-05-01

### Changed
- Scaffold and example workflows prefer **`uvx --from release-readiness-core==…`** against PyPI with a pinned version; quickstart and Python / Node examples updated accordingly.

## [0.3.3] — 2026-05-01

### Added
- **PyPI distribution** — package metadata (`license`, `classifiers`, `project.urls`) and a tag-driven [`.github/workflows/publish-pypi.yml`](.github/workflows/publish-pypi.yml) workflow using Trusted Publishing (OIDC) to upload wheels and sdist. Install without git: `pip install release-readiness-core==0.3.3`.
- **Composite / reusable workflow install mode** — `install-source: git | pypi` and `pypi-version` on `.github/actions/release-readiness`, `.github/actions/release-readiness-pr-gate`, and inputs on `.github/workflows/readiness.yml`. `package-ref` remains the Git ref for `uses: …@ref`; when `install-source` is `pypi`, the Python package is installed from PyPI instead of `git+https://…`.

### Changed
- `release-readiness-init` default workflow documents a PyPI-pinned install line (version read from this repo’s `pyproject.toml` at scaffold time) with a commented git-install alternative.

## [0.3.2] — 2026-04-29

### Changed
- All `*.md` files rewrapped to remove hard-line-break wrapping inside paragraphs. Many markdown previewers (notably IDE preview panes and Confluence-style renderers) treated the internal newlines as soft breaks and produced oddly-shaped paragraphs; GitHub rendered fine but the inconsistency made the docs unpleasant outside GitHub. Structural breaks (headings, lists, tables, code blocks, blockquote paragraph separators) are unchanged. Pure formatting; no engine behavior change.

## [0.3.1] — 2026-04-29

### Changed
- How-to filenames under `docs/how-to/` now carry a numeric prefix matching their intended reading order (`0-quickstart.md`, `1-map-evidence.md`, `2-tune-scoring.md`, `3-ci-integration.md`, `4-multi-job-ci.md`, `5-branch-protection.md`, `6-migrate-from-existing-gate.md`). Adopters who hard-coded the old paths in their own docs need to update; nothing in the package's runtime behavior changed.

## [0.3.0] — 2026-04-29

### Added
- **`release-readiness-doctor`** — pre-flight verifier that catches install, config, and evidence-shape problems before a real run. Validates config against the closed-set schema, validates each evidence file, and surfaces common pitfalls (e.g. `failed_count > 0` with empty `failures`). Exits non-zero on any ERROR.
- Three evidence-shape JSON schemas under `docs/contracts/`: `smoke-input-v1.schema.json`, `e2e-input-v1.schema.json`, `coverage-input-v1.schema.json`. Doctor uses them; adopters can validate their own evidence-emission tooling against them too.
- `docs/how-to/6-migrate-from-existing-gate.md` — step-by-step migration for teams replacing a hand-rolled readiness gate. Covers inventory → mapping → parallel-run → cut-over.
- `docs/how-to/4-multi-job-ci.md` — `actions/upload-artifact` / `download-artifact` pattern for projects whose smoke / e2e / coverage live in separate jobs.
- `docs/how-to/5-branch-protection.md` — concrete UI and `gh api` steps for making the readiness check required.
- `docs/reference/outputs.md` — exhaustive field-by-field glossary for `release-readiness.json` and `report.json`.

### Changed
- README "How-to guides" gains the three new how-tos plus a "Reference" section and an explicit note about the two CLIs (`release-readiness-evaluate` vs. lightweight `release-readiness`).

## [0.2.0] — 2026-04-29

### Added
- `release-readiness-init <target>` scaffold command — emits a starter `config.yaml`, validation map, and GitHub Actions workflow.
- Reusable GitHub composite action at `.github/actions/release-readiness/action.yml` — adopters reference it via `psuthar/release-readiness-core/.github/actions/release-readiness@<sha>`.
- `junit-to-readiness` adapter — converts JUnit XML (Cypress, Jest, pytest, Mocha, Karma, Maven Surefire) to the readiness e2e shape.
- `lcov-to-readiness` adapter — converts LCOV `info` coverage to the readiness coverage shape.
- Config-schema validation at YAML load time — catches top-level typos with "did you mean" suggestions and obvious type errors before the engine runs.
- `optional_artifacts: [prod_health, coverage]` config knob — declared artifacts no longer warn or deduct when absent.
- Worked second-project example under `examples/second-project/` plus an end-to-end regression test.
- Four how-to articles: quickstart, map-evidence, tune-scoring, and ci-integration.

### Changed
- `risk_category_to_required_validation` is now honored by `compute_readiness` — the hardcoded TalkBack `migrations → migrations_validated` special case is gone; TalkBack carries the equivalent mapping in its own config.
- `DEFAULT_EVIDENCE_BOOLEAN_KEYS` is now an empty tuple (gap #6). Adopters opt in via `evidence_boolean_keys` in config.
- Relative artifact paths (`--smoke-results`, `--e2e-results`, `--coverage`, `--prod-health`) now resolve under `--repo-root` (gap #3) instead of the working directory.
- `--empty-diff` help text describes the non-CI use case (gap #7).
- Markdown report omits the "Validations" table when empty (gap #4) and the "Validation note" header row when none is present (gap #5).
- Engine messages no longer reference a `pr_risk.md` file the package doesn't produce (gap #20).
- `release-readiness-core` Playwright adapter no longer embeds TalkBack-specific `VALIDATION_FILE_STEMS`; project-supplied YAML map is required.

### Documentation
- New `docs/how-to/0-quickstart.md`, `1-map-evidence.md`, `2-tune-scoring.md`, `3-ci-integration.md`.
- New `docs/spikes/second-project-validation.md` with the gap list driving the 0.2.0 changes; gaps #1, #2, #3, #4, #5, #6, #7, #20 marked resolved.
- New `RELEASE.md` covering versioning and SHA-pin policy.

## [0.1.0] — 2026-04-28

- Bootstrap project with uv + hatchling packaging.
- Add deterministic engine and CLI skeleton.
- Add baseline test and CI workflow.
