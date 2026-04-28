#!/usr/bin/env bash
# Writes .cursor/mcp.json and .mcp.json with talkback/github/atlassian MCP servers.
# Reads credentials from env and optional .env.mcp file in repo root.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_MCP="$ROOT/.env.mcp"

if [[ -f "$ENV_MCP" ]]; then
  while IFS='=' read -r _k _v || [[ -n "$_k" ]]; do
    [[ "$_k" =~ ^[[:space:]]*# ]] && continue
    [[ -z "${_k// }" ]] && continue
    _k="${_k// /}"
    _v="${_v#"${_v%%[! ]*}"}"
    _v="${_v%"${_v##*[! ]}"}"
    case "$_k" in
      TALKBACK_MCP_AUTH_HEADER|TALKBACK_MCP_ACTING_USER_ID|GITHUB_PERSONAL_ACCESS_TOKEN|GH_PERSONAL_ACCESS_TOKEN|ATLASSIAN_DOMAIN|ATLASSIAN_EMAIL|ATLASSIAN_API_TOKEN)
        [[ -z "${!_k:-}" ]] && export "$_k=$_v"
        ;;
    esac
  done < "$ENV_MCP"
fi

export SETUP_ROOT="$ROOT"
export SETUP_TALKBACK_MCP_AUTH_HEADER="${TALKBACK_MCP_AUTH_HEADER:-}"
export SETUP_TALKBACK_MCP_ACTING_USER_ID="${TALKBACK_MCP_ACTING_USER_ID:-}"
export SETUP_GITHUB_PAT="${GITHUB_PERSONAL_ACCESS_TOKEN:-${GH_PERSONAL_ACCESS_TOKEN:-}}"
export SETUP_ATLASSIAN_DOMAIN="${ATLASSIAN_DOMAIN:-}"
export SETUP_ATLASSIAN_EMAIL="${ATLASSIAN_EMAIL:-}"
export SETUP_ATLASSIAN_API_TOKEN="${ATLASSIAN_API_TOKEN:-}"

python3 <<'PY'
import json
import os
from pathlib import Path

root = Path(os.environ["SETUP_ROOT"])
talkback_auth = os.environ.get("SETUP_TALKBACK_MCP_AUTH_HEADER", "").strip()
talkback_user_id = os.environ.get("SETUP_TALKBACK_MCP_ACTING_USER_ID", "").strip()
github_pat = os.environ.get("SETUP_GITHUB_PAT", "").strip()
atlassian_domain = os.environ.get("SETUP_ATLASSIAN_DOMAIN", "").strip()
atlassian_email = os.environ.get("SETUP_ATLASSIAN_EMAIL", "").strip()
atlassian_token = os.environ.get("SETUP_ATLASSIAN_API_TOKEN", "").strip()

servers = {
    "talkback": {
        "command": "npx",
        "args": [
            "mcp-remote",
            "https://talkback-895n.onrender.com/mcp/",
            "--header",
            "Authorization:${TALKBACK_MCP_AUTH_HEADER}",
            "--header",
            "X-Talkback-Acting-User-Id:${TALKBACK_MCP_ACTING_USER_ID}",
        ],
        "env": {
            "TALKBACK_MCP_AUTH_HEADER": talkback_auth,
            "TALKBACK_MCP_ACTING_USER_ID": talkback_user_id,
        },
    }
}

if github_pat:
    servers["github"] = {
        "command": "docker",
        "args": [
            "run",
            "-i",
            "--rm",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server",
        ],
        "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": github_pat},
    }

if atlassian_domain and atlassian_email and atlassian_token:
    servers["atlassian"] = {
        "command": "npx",
        "args": ["-y", "@xuandev/atlassian-mcp"],
        "env": {
            "ATLASSIAN_DOMAIN": atlassian_domain,
            "ATLASSIAN_EMAIL": atlassian_email,
            "ATLASSIAN_API_TOKEN": atlassian_token,
        },
    }

obj = {"mcpServers": servers}
text = json.dumps(obj, indent=2) + "\n"
(root / ".cursor").mkdir(parents=True, exist_ok=True)
(root / ".cursor" / "mcp.json").write_text(text, encoding="utf-8")
(root / ".mcp.json").write_text(text, encoding="utf-8")

print("Wrote:")
print(f"  {root / '.cursor' / 'mcp.json'}")
print(f"  {root / '.mcp.json'}")
print()
missing = []
if not talkback_auth:
    missing.append("TALKBACK_MCP_AUTH_HEADER")
if not talkback_user_id:
    missing.append("TALKBACK_MCP_ACTING_USER_ID")
if missing:
    print("Talkback server is configured but missing values for:")
    print("  " + ", ".join(missing))
    print()
if not github_pat:
    print("GitHub server omitted: set GITHUB_PERSONAL_ACCESS_TOKEN (or GH_PERSONAL_ACCESS_TOKEN) and rerun.")
if not (atlassian_domain and atlassian_email and atlassian_token):
    print("Atlassian server omitted: set ATLASSIAN_DOMAIN, ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN and rerun.")
PY
