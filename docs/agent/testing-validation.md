# release-readiness-core Testing and Validation Policy

Source of truth: This file owns test planning, required test coverage rules, and validation gates.

## Test Planning (Before Implementation)

Before writing implementation code:

1. Determine whether the ticket changes executable behavior or is docs/config only.
2. For product-code changes, identify:
   - new behavior that needs tests,
   - existing tests that must be updated,
   - security/correctness-sensitive paths,
   - appropriate test type matching existing repository patterns.
3. Record a brief test plan and treat it as acceptance criteria for done.

## Required Test Type Matrix

| Changed area | Required test type |
|---|---|
| Core package logic under `src/release_readiness_core/` | Add/update Python unit tests in `tests/` |
| CLI behavior changes | Add/update CLI-focused tests and output assertions |
| Contract or serializer changes | Golden/fixture regression test for payload compatibility |
| Adapter behavior changes | Adapter-focused tests plus failure-path checks |
| Docs/config only, no executable behavior | No test required |

## Hard Stops Before Commit

- If executable code changed under `src/release_readiness_core/`, at least one relevant test file must be added/updated.
- If contract behavior changed, include a golden regression fixture update in the same PR.

## Validation Before Completion

- Run relevant validation before completion:
  - `uv run pytest`
  - targeted CLI or adapter checks as applicable
- Do not proceed when validation fails.

