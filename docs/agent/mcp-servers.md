# release-readiness-core MCP and Command Reference

Source of truth: This file owns repository command references and MCP server/tooling details.

## Repository Development Commands

- Setup environment: `uv sync`
- Run tests: `uv run pytest`
- Build package: `uv build`
- Smoke CLI: `uv run release-readiness --input-json '[{"key":"go-test","status":"PASS"}]'`
- Configure MCP clients: `./scripts/setup-mcp-config.sh`

## MCP Servers

Three MCP servers are configured in `.cursor/mcp.json` and `.mcp.json`. Regenerate both with `./scripts/setup-mcp-config.sh`.

### `talkback` server

- Command (remote bridge): `npx mcp-remote https://talkback-895n.onrender.com/mcp/ ...`
- Primary use in this repo: cross-repo references during migration and verification.

Important env vars:

- `TALKBACK_MCP_AUTH_HEADER`
- `TALKBACK_MCP_ACTING_USER_ID`

`talkback` MCP is optional for local package development; keep enabled when tasks require cross-repo checks.

### `github` server

- Command: `docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN ghcr.io/github/github-mcp-server`
- PAT requirement: classic token with `repo` scope.
- FULL_AUTO relies on `pull_request_read` with `method: get` and `mergeable_state`.
- If `mergeable_state` is absent, FULL_AUTO is unavailable and must hard-stop.

### `atlassian` server

- Package: `@xuandev/atlassian-mcp` via `npx -y`
- Tools: `jira_*` and `confluence_*`
- Required env vars: `ATLASSIAN_DOMAIN`, `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN`
- `jira_add_comment` requires `body` (not `comment`)

