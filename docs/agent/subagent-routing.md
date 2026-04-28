# Subagent and Test Routing

Source of truth: This file owns subagent routing policy and test-fixer routing guidance.

## Subagent Routing

- `talkback-architect`
  - multi-file package design and extraction planning
  - API contract changes and backward-compatibility decisions

- `talkback-backend`
  - Python engine, adapters, and CLI logic updates
  - package behavior fixes and test updates

- `talkback-frontend`
  - documentation, examples, and lightweight UX-facing CLI/report output improvements

- `talkback-ux`
  - interaction/usability improvements
  - layout/content hierarchy changes while preserving existing visual language unless requested

- `talkback-reviewer`
  - regression/risk/missing-tests reviews

- `talkback-e2e-fixer`
  - run end-to-end style package/CLI scenario checks
  - diagnose output drift and scenario regressions

- `talkback-smoke-fixer`
  - run smoke/integration tests
  - diagnose/fix deterministic evaluation regressions

## Test Routing

- Use `smoke-tests` skill to create/refine deterministic backend smoke/integration tests.
- Use `talkback-smoke-fixer` for smoke execution/failures/repairs.
- Use `e2e-tests` skill and `talkback-e2e-fixer` for CLI scenario validation when applicable.
- Use `talkback-reviewer` for post-change risk and missing-test reviews.

