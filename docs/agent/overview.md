# release-readiness-core Agent Policy Overview

Source of truth: This file owns repository context and high-level execution principles for all agents. Workflow-specific rules live in the other `docs/agent/*` files.

## Project Overview

`release-readiness-core` is a project-agnostic Python package for deterministic release-readiness evaluation. It exposes engine, CLI, and adapter capabilities for CI evidence processing and PASS/WARN/BLOCK recommendations.

- Core flow: ingest normalized evidence + optional risk signals, evaluate deterministic rules, emit a machine-readable result and markdown report.
- Scope: reusable package consumed by downstream repositories (including TalkBack during migration).
- Runtime: Python package and CLI (`release-readiness`) with test/build tooling via `uv`.

## Architecture Summary

- Package source: `src/release_readiness_core/`
- Tests: `tests/`
- Automation scripts: `scripts/`
- CI and release policy: `.github/workflows/`

## Product Direction

- Preserve deterministic behavior while extracting from TalkBack into a standalone package.
- Keep contracts stable and explicit for input/output payloads.
- Maintain backward compatibility for existing consumers unless ticket scope explicitly changes behavior.

## Development Workflow Expectations

When working in this repository, agents must:

1. Analyze before editing.
2. Propose a plan before implementing.
3. Implement in small, incremental steps.
4. Prefer backward-compatible changes.
5. Explain touched files after edits.
6. Run focused tests after backend changes.
7. Avoid broad refactors unrelated to ticket scope.

## Karpathy-style Execution Guardrails

These apply to all implementation work:

1. Think before coding: surface assumptions and ambiguity.
2. Prefer minimal solutions: avoid speculative abstractions.
3. Make surgical edits: touch only required files/lines.
4. Tie implementation to verification before completion.
5. Prefer and explain simpler approaches when available.

Tradeoff: these rules bias toward correctness/caution over speed; for trivial tasks, keep execution lightweight while still verifying outcomes.

## Repo-specific Guidance

- Follow existing package patterns before introducing abstractions.
- Keep naming and contract terminology explicit and stable.
- Do not change scoring behavior unless explicitly requested by ticket scope.
- Prefer deterministic, side-effect-light logic and test coverage for all behavior changes.

