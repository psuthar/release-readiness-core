"""Path classification (port of internal/prrisk/classify.go).

Determines the primary domain a changed file belongs to (auth, rag,
processing, etc.) and identifies test, config, and migration paths.
The match order in classify_area is significant — it mirrors the Go
switch order exactly for parity.
"""

from __future__ import annotations

import os.path
from typing import Iterable

from release_readiness_core.pr_risk.types import (
    DOMAIN_API,
    DOMAIN_AUTH,
    DOMAIN_DATABASE,
    DOMAIN_DEPLOY,
    DOMAIN_MIGRATIONS,
    DOMAIN_ORCHESTRATION,
    DOMAIN_OTHER,
    DOMAIN_PROCESSING,
    DOMAIN_RAG,
    DOMAIN_SCRIPTS,
    DOMAIN_STORAGE,
    DOMAIN_TESTS,
    DOMAIN_WEB,
    DOMAIN_WORKFLOWS,
    Signals,
)


def _to_slash(path: str) -> str:
    """Mirror filepath.ToSlash: convert backslash separators to forward slashes."""
    return path.replace("\\", "/")


def classify_domain(path: str) -> str:
    """Return one primary domain for a repo-relative path."""
    if is_test_path(path):
        return DOMAIN_TESTS
    return classify_area(path)


def classify_area(path: str) -> str:
    """Return the product-area label for a path (ignores test detection)."""
    p = _to_slash(path.strip()).lower()
    if p == "":
        return DOMAIN_OTHER

    # Migrations.
    if p.startswith("db/migrations/") or p.startswith("internal/migrations/"):
        return DOMAIN_MIGRATIONS

    # Auth/session and invite flows.
    if p.startswith("internal/auth/"):
        return DOMAIN_AUTH
    if p.startswith("internal/invitations/"):
        return DOMAIN_AUTH
    if "internal/handlers/" in p and (
        "login" in p
        or "session_invite" in p
        or "invitations" in p
        or "session_participant" in p
        or "zoom_auth" in p
        or "teams_auth" in p
        or "auth" in p
        or "invite" in p
    ):
        return DOMAIN_AUTH

    # Decision-grade Q&A / RAG.
    if p.startswith("internal/rag/"):
        return DOMAIN_RAG
    if "internal/utils/qa.go" in p:
        return DOMAIN_RAG
    if (
        "internal/handlers/session_ask" in p
        or "internal/handlers/session_questions" in p
        or "internal/handlers/session_reindex" in p
    ):
        return DOMAIN_RAG

    # Material processing / transcription pipeline.
    if p.startswith("internal/processing/"):
        return DOMAIN_PROCESSING
    if (
        "internal/handlers/transcript_" in p
        or "internal/handlers/transcript" in p
        or "internal/handlers/video_url_ingestion" in p
        or "internal/handlers/video_upload" in p
        or "internal/handlers/session_materials" in p
        or "internal/handlers/transcript_job_status" in p
        or "internal/handlers/transcript_jobs" in p
    ):
        return DOMAIN_PROCESSING

    # Storage and remaining internal areas.
    if p.startswith("internal/storage/"):
        return DOMAIN_STORAGE
    if p.startswith("internal/orchestration/"):
        return DOMAIN_ORCHESTRATION
    if "internal/handlers/session_orchestration" in p:
        return DOMAIN_ORCHESTRATION
    if "internal/database/orchestration_recommendations" in p:
        return DOMAIN_ORCHESTRATION
    if "internal/database/orchestration_recommendation_audit" in p:
        return DOMAIN_ORCHESTRATION
    if p.startswith("internal/database/"):
        return DOMAIN_DATABASE
    if p.startswith("internal/handlers/"):
        return DOMAIN_API

    # Frontend.
    if "web/src/modes/creatormode" in p:
        return DOMAIN_ORCHESTRATION
    if p.startswith("web/"):
        return DOMAIN_WEB

    # CI / deploy / infra config.
    if p.startswith(".github/workflows/"):
        return DOMAIN_WORKFLOWS
    if p.startswith("deploy/") or p == "dockerfile" or p.endswith("/dockerfile"):
        return DOMAIN_DEPLOY
    if p.endswith("render.yaml") or "/render.yaml" in p:
        return DOMAIN_DEPLOY

    # Misc.
    if p.startswith("cmd/"):
        return DOMAIN_API
    if p.startswith("scripts/"):
        return DOMAIN_SCRIPTS

    if p.startswith("internal/"):
        return DOMAIN_API
    return DOMAIN_OTHER


def is_test_path(path: str) -> bool:
    """Return True if the path is test-only or test-heavy."""
    p = _to_slash(path).lower()
    if p == "":
        return False
    if p.endswith("_test.go"):
        return True
    if "/testdata/" in p:
        return True
    if "/e2e/" in p or "playwright" in p:
        return True
    if p.endswith(".spec.ts") or p.endswith(".spec.tsx"):
        return True
    if (
        "__tests__/" in p
        or ".test.ts" in p
        or ".test.tsx" in p
        or ".test.js" in p
        or ".test.jsx" in p
    ):
        return True
    return False


def is_e2e_path(path: str) -> bool:
    """Detect Playwright E2E specs."""
    p = _to_slash(path).lower()
    if "web/tests/e2e/" in p:
        return True
    if "/e2e/" in p and (
        p.endswith(".e2e.ts")
        or p.endswith(".e2e.tsx")
        or p.endswith(".spec.ts")
        or p.endswith(".spec.tsx")
    ):
        return True
    return False


def is_untestable_path(path: str) -> bool:
    """Return True for file types with no conventional co-located tests."""
    p = _to_slash(path).lower()
    _, ext = os.path.splitext(p)
    if ext in {".yml", ".yaml", ".sh", ".bash", ".md", ".lock", ".sum"}:
        return True
    base = os.path.basename(p)
    if base in {
        "makefile",
        "dockerfile",
        ".gitignore",
        ".gitattributes",
        ".dockerignore",
        ".editorconfig",
    }:
        return True
    return False


def is_config_path(path: str) -> bool:
    """Return True for CI / deploy / config paths."""
    p = _to_slash(path).lower()
    if p.startswith(".github/"):
        return True
    if p.startswith("deploy/"):
        return True
    if p == "go.mod" or p == "go.sum":
        return True
    if p.endswith("dockerfile") or p == "dockerfile":
        return True
    if p.endswith("render.yaml"):
        return True
    return False


def is_migration_path(path: str) -> bool:
    """Return True for SQL migration paths."""
    p = _to_slash(path).lower()
    return p.startswith("db/migrations/") or p.startswith("internal/migrations/")


def touches_sensitive_code_without_tests(s: Signals) -> bool:
    """Non-test code in risky areas with zero test file changes."""
    if s.test_files > 0:
        return False
    sensitive = {
        DOMAIN_AUTH,
        DOMAIN_API,
        DOMAIN_DATABASE,
        DOMAIN_RAG,
        DOMAIN_PROCESSING,
        DOMAIN_ORCHESTRATION,
        DOMAIN_WEB,
        DOMAIN_MIGRATIONS,
    }
    for f in s.files:
        if is_test_path(f.path):
            continue
        if classify_domain(f.path) in sensitive:
            return True
    return False
