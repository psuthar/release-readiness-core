## release-readiness-core

Project-agnostic deterministic release-readiness engine and adapters.

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

```bash
uv sync
uv run release-readiness --input-json '[{"key":"go-test","status":"PASS"}]'
```

Evaluate from a YAML config and optional JSON artifacts (writes `report.json`, `report.md`, and `artifacts/release-readiness.json` under the repo root):

```bash
uv run release-readiness-evaluate --repo-root . --config path/to/config.yaml \
  --empty-diff --output-dir artifacts/release-readiness
```

Adapter CLIs (ported from TalkBack scripts):

```bash
uv run playwright-to-readiness --input playwright-results.json --output e2e_results.json \
  --validation-map ops/release-readiness/e2e_validation_map.yaml
uv run pr-risk-semantic --pr-risk-json artifacts/pr-risk.json --generator-outcome success
```

`--validation-map` is optional; without it, the converter emits an empty `validations`
object (counts and failures still reported). Spec extensions stripped when computing
file stems can be overridden with `--spec-extensions ts,js,mjs,e2e`.

The N-input PR gate combiner lives in `release_readiness_core.pr_gate` (`combine_gate_inputs`).

### Install from Git (SHA-pinned)

```bash
pip install "git+https://github.com/psuthar/release-readiness-core.git@<sha>"
```

### Development

```bash
uv run pytest
uv build
```

### How-to guides

- Quickstart — adopt the package in a new project: `docs/how-to/quickstart.md`
- Map evidence — wire CI artifacts to validation keys: `docs/how-to/map-evidence.md`
- Tune scoring — penalties, thresholds, remediation: `docs/how-to/tune-scoring.md`
- CI integration — GitHub Checks and the generic adapter pattern: `docs/how-to/ci-integration.md`

### Contracts and Spike Notes

- SCRUM-166 spike notes: `docs/spikes/SCRUM-166-package-boundary-api-contract.md`
- SCRUM-167 prep (validation keys → config): `docs/prep/SCRUM-167-validation-key-handling.md`
- PR risk input schema: `docs/contracts/pr-risk-input-v1.schema.json`
- Readiness output schema: `docs/contracts/release-readiness-output-v1.schema.json`
- Validation config draft schema (SCRUM-167): `docs/contracts/validation-config-v1.schema.json`
- Contract reference guide: `docs/contracts/README.md`

### MCP Setup (Cursor + Claude)

This repo mirrors the same MCP server set used in TalkBack:
- `talkback`
- `github`
- `atlassian`

Create `.env.mcp` in the repo root (or export these vars in your shell):

```bash
TALKBACK_MCP_AUTH_HEADER="Bearer <talkback-api-key>"
TALKBACK_MCP_ACTING_USER_ID="<talkback-user-uuid>"
GITHUB_PERSONAL_ACCESS_TOKEN="<github-pat>"
ATLASSIAN_DOMAIN="<your-domain>.atlassian.net"
ATLASSIAN_EMAIL="<your-email>"
ATLASSIAN_API_TOKEN="<atlassian-api-token>"
```

Then generate local MCP config for both tools:

```bash
./scripts/setup-mcp-config.sh
```

This writes:
- `.cursor/mcp.json` (Cursor)
- `.mcp.json` (Claude Code project scope)

Both files are gitignored.

### Agent Command Workflows

This repository supports the same Jira automation command patterns as TalkBack.

- `implement SCRUM-xxx`  
  Standard ticket workflow: code + tests + PR + Jira transition to In Review.
- `implement SCRUM-xxx FULL_AUTO`  
  Includes standard workflow plus post-PR gate polling, merge, and Jira Done transition.
- `run epic SCRUM-xxx` / `continue epic SCRUM-xxx`  
  Epic automation mode that runs each child ticket as FULL_AUTO and drains remaining work.

Policy ownership:
- Entry point: `CLAUDE.md`
- Jira workflow: `docs/agent/workflow-jira.md`
- FULL_AUTO merge rules: `docs/agent/workflow-full-auto.md`
- Epic run rules: `docs/agent/workflow-epic-run.md`
- Testing policy: `docs/agent/testing-validation.md`
- Rule map: `docs/agent/rule-ownership.md`

Epic mode uses the same merge gate as FULL_AUTO in this repo: PR Gate `success` plus `mergeable_state: clean`.

