# Changelog

All notable changes to this project will be documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
(see `RELEASE.md` for SHA-pinning until a `1.0` is published).

## [0.2.0] — 2026-04-29

### Added
- `release-readiness-init <target>` scaffold command — emits a starter
  `config.yaml`, validation map, and GitHub Actions workflow.
- Reusable GitHub composite action at
  `.github/actions/release-readiness/action.yml` — adopters reference it
  via `psuthar/release-readiness-core/.github/actions/release-readiness@<sha>`.
- `junit-to-readiness` adapter — converts JUnit XML (Cypress, Jest,
  pytest, Mocha, Karma, Maven Surefire) to the readiness e2e shape.
- `lcov-to-readiness` adapter — converts LCOV `info` coverage to the
  readiness coverage shape.
- Config-schema validation at YAML load time — catches top-level typos
  with "did you mean" suggestions and obvious type errors before the
  engine runs.
- `optional_artifacts: [prod_health, coverage]` config knob (SCRUM-208) —
  declared artifacts no longer warn or deduct when absent.
- Worked second-project example under `examples/second-project/` plus an
  end-to-end regression test (SCRUM-178).
- Four how-to articles: quickstart, map-evidence, tune-scoring, and
  ci-integration (SCRUM-179 through SCRUM-182).

### Changed
- `risk_category_to_required_validation` is now honored by
  `compute_readiness` (SCRUM-207) — the hardcoded TalkBack
  `migrations → migrations_validated` special case is gone; TalkBack
  carries the equivalent mapping in its own config.
- `DEFAULT_EVIDENCE_BOOLEAN_KEYS` is now an empty tuple (SCRUM-209
  gap #6). Adopters opt in via `evidence_boolean_keys` in config.
- Relative artifact paths (`--smoke-results`, `--e2e-results`,
  `--coverage`, `--prod-health`) now resolve under `--repo-root`
  (SCRUM-209 gap #3) instead of the working directory.
- `--empty-diff` help text describes the non-CI use case (gap #7).
- Markdown report omits the "Validations" table when empty (gap #4) and
  the "Validation note" header row when none is present (gap #5).
- Engine messages no longer reference a `pr_risk.md` file the package
  doesn't produce (gap #20).
- `release-readiness-core` Playwright adapter no longer embeds
  TalkBack-specific `VALIDATION_FILE_STEMS`; project-supplied YAML map
  is required (SCRUM-170).

### Documentation
- New `docs/how-to/quickstart.md`, `map-evidence.md`, `tune-scoring.md`,
  `ci-integration.md`.
- New `docs/spikes/SCRUM-178-second-project-validation.md` with the gap
  list driving the 0.2.0 changes; gaps #1, #2, #3, #4, #5, #6, #7, #20
  marked resolved.
- New `RELEASE.md` covering versioning and SHA-pin policy.

## [0.1.0] — 2026-04-28

- Bootstrap project with uv + hatchling packaging.
- Add deterministic engine and CLI skeleton.
- Add baseline test and CI workflow.
