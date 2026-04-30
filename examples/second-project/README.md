# Second-project example: `todo-api`

A fictional small Flask REST API used as the **second consumer** in the package generalization spike. Nothing in this directory is wired into the package — it exists so a) anyone can see what an unrelated `config.yaml` looks like, and b) the regression test in `tests/test_second_project_example.py` keeps the package working against it as the API evolves.

## Running

From the repo root:

```bash
uv run release-readiness-evaluate \
  --repo-root examples/second-project \
  --config config.yaml \
  --smoke-results evidence/smoke.json \
  --e2e-results evidence/e2e.json \
  --coverage evidence/coverage.json \
  --empty-diff \
  --output-dir artifacts/release-readiness
```

`--empty-diff` skips the `git diff` step (this directory is not a real project, so there is no diff to take). Outputs land in `examples/second-project/artifacts/release-readiness/report.{json,md}` and `examples/second-project/artifacts/release-readiness.json`.

Note: there is no `--prod-health` flag here — the fixture's `config.yaml` declares `optional_artifacts: [prod_health]` because todo-api has no production-health monitoring source. The package treats the missing artifact as silent rather than emitting a PASS-suppressing warning.

## Why this project

- Vocabulary is intentionally unlike TalkBack: validations are `api_health`, `db_migrations`, `auth_login`, `todo_crud`, `search_filtering`. None of TalkBack's validation keys appear.
- Layout is a Python web service, not a frontend app.
- Risk patterns target `migrations/**`, `src/todo_api/auth/**`, etc.
