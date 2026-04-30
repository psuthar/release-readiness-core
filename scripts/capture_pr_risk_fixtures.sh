#!/usr/bin/env bash
# capture_pr_risk_fixtures.sh
#
# Capture PR Risk fixtures from any source repository that ships an upstream
# `cmd/prrisk` binary, for parity testing this package's Python implementation
# against that upstream reference.
#
# Reads merged-PR numbers from stdin (one per line) and, for each:
#   1. resolves the merge SHA + parent SHA via gh
#   2. detached-HEAD checkout the merge SHA in the source repo
#   3. runs prrisk into a temp dir OUTSIDE the source repo
#   4. copies pr_risk.{json,md} and pr-risk.json into the fixture dir
#   5. writes meta.json
#
# Restores the source repo's original ref on success, error, or interrupt.
#
# SAFETY GUARANTEES (encoded below):
#   * Pre-flight aborts if the source repo has uncommitted tracked changes.
#   * Only `git fetch`, `git checkout --detach`, `git rev-parse`, `git log`,
#     `git show`, `git symbolic-ref` are run against the source repo.
#   * No `stash`, `reset --hard`, `clean`, `commit`, `push`, `branch -D`,
#     `config`, `gc --prune`.
#   * The source repo's working tree is never written to by the prrisk run
#     (--output-dir always points outside the source).

set -euo pipefail

usage() {
    cat <<EOF
Usage: $(basename "$0") --target <repo> --output <dir> [options] < pr-numbers.txt

Required:
  --target <path>     Source git repo containing cmd/prrisk
  --output <path>     Fixture root (e.g. tests/pr_risk/fixtures)

Optional:
  --prrisk-cmd <cmd>  Command that runs prrisk (default: "go run ./cmd/prrisk")
  --repo-slug <s>     gh -R argument for PR lookups (default: derive from target's origin URL)
  --max <n>           Stop after capturing N new fixtures (default: unlimited)
  --skip-existing     Skip PRs whose pr-N/ directory already has pr-risk.json (default)
  --force             Re-capture even if fixture exists
  -h, --help          Show this help

Reads PR numbers from stdin (one per line; non-numeric lines ignored).

Example:
  ( cd /path/to/source-repo && go build -o /tmp/prrisk-bin ./cmd/prrisk )
  gh -R <owner>/<repo> pr list --state merged --limit 80 --json number --jq '.[].number' \\
    | scripts/capture_pr_risk_fixtures.sh \\
        --target /path/to/source-repo \\
        --output tests/pr_risk/fixtures \\
        --prrisk-cmd /tmp/prrisk-bin
EOF
}

TARGET=""
OUTPUT=""
PRRISK_CMD="go run ./cmd/prrisk"
REPO_SLUG=""
MAX_CAPTURES=0
FORCE=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --target) TARGET="$2"; shift 2 ;;
        --output) OUTPUT="$2"; shift 2 ;;
        --prrisk-cmd) PRRISK_CMD="$2"; shift 2 ;;
        --repo-slug) REPO_SLUG="$2"; shift 2 ;;
        --max) MAX_CAPTURES="$2"; shift 2 ;;
        --skip-existing) FORCE=0; shift ;;
        --force) FORCE=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo "ERROR: unknown arg: $1" >&2; usage; exit 1 ;;
    esac
done

[[ -z "$TARGET" ]] && { echo "ERROR: --target is required" >&2; exit 1; }
[[ -z "$OUTPUT" ]] && { echo "ERROR: --output is required" >&2; exit 1; }
[[ ! -d "$TARGET/.git" ]] && { echo "ERROR: $TARGET is not a git worktree" >&2; exit 1; }

TARGET="$(cd "$TARGET" && pwd)"
mkdir -p "$OUTPUT"
OUTPUT="$(cd "$OUTPUT" && pwd)"

# Derive repo slug if not provided.
if [[ -z "$REPO_SLUG" ]]; then
    ORIGIN_URL=$(git -C "$TARGET" config --get remote.origin.url 2>/dev/null || true)
    # Match git@github.com:owner/repo.git OR https://github.com/owner/repo(.git)?
    if [[ "$ORIGIN_URL" =~ github\.com[:/]([^/]+)/([^/]+)(\.git)?$ ]]; then
        REPO_SLUG="${BASH_REMATCH[1]}/${BASH_REMATCH[2]%.git}"
    else
        echo "ERROR: could not derive --repo-slug from origin URL '$ORIGIN_URL'; pass --repo-slug" >&2
        exit 1
    fi
fi

echo "[capture] target:    $TARGET"
echo "[capture] output:    $OUTPUT"
echo "[capture] repo-slug: $REPO_SLUG"
echo "[capture] prrisk:    $PRRISK_CMD"

# Pre-flight: source repo's tracked tree must be clean.
DIRTY=$(git -C "$TARGET" status --porcelain --untracked-files=no)
if [[ -n "$DIRTY" ]]; then
    echo "ERROR: $TARGET has uncommitted tracked changes:" >&2
    echo "$DIRTY" >&2
    echo "Aborting. Commit or stash before re-running." >&2
    exit 2
fi

# Record original ref to restore on exit.
ORIGINAL_REF=$(git -C "$TARGET" symbolic-ref --short HEAD 2>/dev/null || git -C "$TARGET" rev-parse HEAD)
echo "[capture] original ref: $ORIGINAL_REF"

restore() {
    echo "[capture] restoring $TARGET to $ORIGINAL_REF"
    git -C "$TARGET" checkout --quiet "$ORIGINAL_REF" >/dev/null 2>&1 || true
}
trap restore EXIT INT TERM

# Fetch latest history (read-only-ish: updates origin/* refs only, no working-tree changes).
git -C "$TARGET" fetch --quiet origin || true

CAPTURED=0
SKIPPED=0
FAILED=0

while IFS= read -r RAW_PR; do
    PR_NUMBER="${RAW_PR//[!0-9]/}"
    [[ -z "$PR_NUMBER" ]] && continue

    if [[ "$MAX_CAPTURES" -gt 0 && "$CAPTURED" -ge "$MAX_CAPTURES" ]]; then
        echo "[capture] reached --max=$MAX_CAPTURES, stopping"
        break
    fi

    FIXTURE_DIR="$OUTPUT/pr-$PR_NUMBER"
    if [[ "$FORCE" -eq 0 && -f "$FIXTURE_DIR/pr-risk.json" ]]; then
        SKIPPED=$((SKIPPED + 1))
        continue
    fi

    MERGE_INFO=$(gh -R "$REPO_SLUG" pr view "$PR_NUMBER" \
        --json mergeCommit,baseRefName,headRefName,title,state \
        2>/dev/null || true)
    if [[ -z "$MERGE_INFO" ]]; then
        echo "[capture] PR #$PR_NUMBER: gh lookup failed, skipping"
        FAILED=$((FAILED + 1))
        continue
    fi

    MERGE_SHA=$(echo "$MERGE_INFO" | jq -r '.mergeCommit.oid // empty')
    BASE_REF=$(echo "$MERGE_INFO" | jq -r '.baseRefName // "main"')
    PR_TITLE=$(echo "$MERGE_INFO" | jq -r '.title // ""')
    PR_STATE=$(echo "$MERGE_INFO" | jq -r '.state // ""')

    if [[ -z "$MERGE_SHA" ]]; then
        echo "[capture] PR #$PR_NUMBER: no merge commit (state=$PR_STATE), skipping"
        FAILED=$((FAILED + 1))
        continue
    fi

    # Resolve parent SHA on the base branch.
    if ! git -C "$TARGET" cat-file -e "${MERGE_SHA}^{commit}" 2>/dev/null; then
        echo "[capture] PR #$PR_NUMBER: merge SHA $MERGE_SHA not in target repo, skipping"
        FAILED=$((FAILED + 1))
        continue
    fi
    PARENT_SHA=$(git -C "$TARGET" rev-parse "${MERGE_SHA}^1" 2>/dev/null || echo "")
    if [[ -z "$PARENT_SHA" ]]; then
        echo "[capture] PR #$PR_NUMBER: parent SHA unavailable, skipping"
        FAILED=$((FAILED + 1))
        continue
    fi

    echo "[capture] PR #$PR_NUMBER: merge=${MERGE_SHA:0:10} parent=${PARENT_SHA:0:10}"

    git -C "$TARGET" checkout --quiet --detach "$MERGE_SHA"

    mkdir -p "$FIXTURE_DIR"
    TMP_OUT=$(mktemp -d -t prrisk-XXXXXX)

    set +e
    (
        cd "$TARGET" && \
        PRRISK_PR_TITLE="$PR_TITLE" $PRRISK_CMD \
            --repo-root . \
            --base-ref "$PARENT_SHA" \
            --output-dir "$TMP_OUT/release-readiness" \
            > "$FIXTURE_DIR/capture.log" 2>&1
    )
    PRRISK_RC=$?
    set -e

    if [[ "$PRRISK_RC" -ne 0 ]]; then
        echo "[capture]   prrisk exit=$PRRISK_RC; see $FIXTURE_DIR/capture.log"
        FAILED=$((FAILED + 1))
        rm -rf "$TMP_OUT"
        continue
    fi

    [[ -f "$TMP_OUT/release-readiness/pr_risk.json" ]] && cp "$TMP_OUT/release-readiness/pr_risk.json" "$FIXTURE_DIR/" || true
    [[ -f "$TMP_OUT/release-readiness/pr_risk.md"   ]] && cp "$TMP_OUT/release-readiness/pr_risk.md"   "$FIXTURE_DIR/" || true
    [[ -f "$TMP_OUT/pr-risk.json" ]] && cp "$TMP_OUT/pr-risk.json" "$FIXTURE_DIR/" || true

    if [[ ! -f "$FIXTURE_DIR/pr-risk.json" ]]; then
        echo "[capture]   prrisk exit=0 but pr-risk.json missing; see $FIXTURE_DIR/capture.log"
        FAILED=$((FAILED + 1))
        rm -rf "$TMP_OUT"
        continue
    fi

    jq -n \
        --argjson pr "$PR_NUMBER" \
        --arg merge "$MERGE_SHA" \
        --arg parent "$PARENT_SHA" \
        --arg base "$BASE_REF" \
        --arg title "$PR_TITLE" \
        --arg slug "$REPO_SLUG" \
        '{
            pr_number: $pr,
            merge_sha: $merge,
            parent_sha: $parent,
            base_ref: $base,
            pr_title: $title,
            repo_slug: $slug,
            schema_version: "1.0"
         }' > "$FIXTURE_DIR/meta.json"

    rm -rf "$TMP_OUT"
    CAPTURED=$((CAPTURED + 1))
done

echo "[capture] done: captured=$CAPTURED skipped(existing)=$SKIPPED failed=$FAILED"
