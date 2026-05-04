# Contributing to release-readiness-core

Thanks for considering a contribution. The package aims to stay small, deterministic, and project-agnostic — please keep changes scoped accordingly.

## Development setup

```bash
uv sync
uv run pytest
uv build
```

Tests are the canonical contract. Every behavior change should land with at least one regression test, and `uv run pytest` is the same suite run as the required `test` Check on PRs.

## Submitting changes

1. Fork the repo and create a feature branch off `main`.
2. Make your change with tests.
3. Run `uv run pytest` locally and confirm green.
4. Open a PR against `main`. CODEOWNERS review is required; the `test` status check must pass.

Commit messages follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `release:`). Single-line title, body explaining *why* over *what*.

## Adding an adapter for a new test runner

The recipe matrix ([`docs/how-to/8-recipe-matrix.md`](docs/how-to/8-recipe-matrix.md)) lists the stacks already covered. To add a new one:

1. Add a CLI in `src/release_readiness_core/adapters/` that reads your runner's output and emits a smoke / e2e / coverage JSON shape matching the relevant contract under `docs/contracts/`.
2. Add tests with golden fixtures (see existing adapters for examples).
3. Add a wire-up snippet to `docs/how-to/8-recipe-matrix.md` so adopters can find it.
4. Optionally extend `release-readiness-init` (`src/release_readiness_core/init/`) with a `--stack <X>` template that generates the evidence-collection block automatically.

## Reporting issues

When the verdict surprises you, the report is the source of truth. Open an issue with:

- The PR or commit URL where the verdict appeared.
- The `report.md` (or relevant excerpt).
- What you expected vs. what you got.

"WARN at score 100 with no obvious cause" is a particularly useful failure mode to report — the docs or the report explanation are wrong, and we want to fix it.

---

## Maintainer-only tooling

> The sections below are for repository maintainers. External contributors can skip them — none of this is required to submit a PR. The MCP endpoints and Jira project referenced here are not publicly reachable.

### MCP servers

The maintainer's local agent setup uses three MCP servers:

- `talkback` (internal — not publicly reachable)
- `github`
- `atlassian`

Configure via `.env.mcp` in the repo root (or export the variables in your shell):

```bash
TALKBACK_MCP_AUTH_HEADER="Bearer <api-key>"
TALKBACK_MCP_ACTING_USER_ID="<user-uuid>"
GITHUB_PERSONAL_ACCESS_TOKEN="<github-pat>"
ATLASSIAN_DOMAIN="<your-domain>.atlassian.net"
ATLASSIAN_EMAIL="<your-email>"
ATLASSIAN_API_TOKEN="<atlassian-api-token>"
```

Then generate local MCP config:

```bash
./scripts/setup-mcp-config.sh
```

This writes:
- `.cursor/mcp.json` (Cursor)
- `.mcp.json` (Claude Code project scope)

Both files are gitignored.

### Jira automation commands

Internal Jira-driven workflow patterns:

- `implement <TICKET-KEY>` — code + tests + PR + Jira transition to In Review.
- `implement <TICKET-KEY> FULL_AUTO` — above plus post-PR gate polling, merge, and Jira Done transition.
- `run epic <TICKET-KEY>` / `continue epic <TICKET-KEY>` — runs each child ticket as FULL_AUTO and drains remaining work.

Policy ownership:

- Entry point: `CLAUDE.md`
- Jira workflow: `docs/agent/workflow-jira.md`
- FULL_AUTO merge rules: `docs/agent/workflow-full-auto.md`
- Epic run rules: `docs/agent/workflow-epic-run.md`
- Testing policy: `docs/agent/testing-validation.md`
- Rule map: `docs/agent/rule-ownership.md`

Epic-mode merge gate: PR Gate `success` plus `mergeable_state: clean`.
