"""Tests for pr_risk.classify (port of Go classify_test.go + extras)."""

import pytest

from release_readiness_core.pr_risk.classify import (
    classify_area,
    classify_domain,
    is_config_path,
    is_e2e_path,
    is_migration_path,
    is_test_path,
    is_untestable_path,
    touches_sensitive_code_without_tests,
)
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
    FileChange,
    Signals,
)


# Golden table mirrors classify_test.go::TestClassifyDomain plus extras.
@pytest.mark.parametrize(
    "path,want",
    [
        ("internal/auth/session.go", DOMAIN_AUTH),
        ("internal/handlers/login.go", DOMAIN_AUTH),
        ("internal/handlers/session_invite.go", DOMAIN_AUTH),
        ("internal/handlers/session_participant.go", DOMAIN_AUTH),
        ("internal/handlers/sessions.go", DOMAIN_API),
        ("db/migrations/0001_x.up.sql", DOMAIN_MIGRATIONS),
        ("internal/migrations/0042_init.sql", DOMAIN_MIGRATIONS),
        ("web/src/App.tsx", DOMAIN_WEB),
        ("web/src/modes/CreatorMode.jsx", DOMAIN_ORCHESTRATION),
        ("web/src/foo.test.tsx", DOMAIN_TESTS),
        ("internal/rag/foo.go", DOMAIN_RAG),
        ("internal/handlers/session_ask.go", DOMAIN_RAG),
        ("internal/handlers/session_questions.go", DOMAIN_RAG),
        ("internal/handlers/session_reindex.go", DOMAIN_RAG),
        ("internal/utils/qa.go", DOMAIN_RAG),
        ("internal/orchestration/evaluator.go", DOMAIN_ORCHESTRATION),
        ("internal/handlers/session_orchestration.go", DOMAIN_ORCHESTRATION),
        ("internal/database/orchestration_recommendations.go", DOMAIN_ORCHESTRATION),
        ("internal/database/orchestration_recommendation_audit.go", DOMAIN_ORCHESTRATION),
        ("internal/database/users.go", DOMAIN_DATABASE),
        ("internal/processing/whisper.go", DOMAIN_PROCESSING),
        ("internal/handlers/transcript_jobs.go", DOMAIN_PROCESSING),
        ("internal/handlers/video_url_ingestion.go", DOMAIN_PROCESSING),
        ("internal/handlers/session_materials.go", DOMAIN_PROCESSING),
        ("internal/storage/blob.go", DOMAIN_STORAGE),
        (".github/workflows/ci.yml", DOMAIN_WORKFLOWS),
        ("deploy/render.yaml", DOMAIN_DEPLOY),
        ("Dockerfile", DOMAIN_DEPLOY),
        ("scripts/build.sh", DOMAIN_SCRIPTS),
        ("cmd/myapp/main.go", DOMAIN_API),
        ("internal/foo/bar.go", DOMAIN_API),
        ("go.mod", DOMAIN_OTHER),
        ("README.md", DOMAIN_OTHER),
        ("", DOMAIN_OTHER),
    ],
)
def test_classify_domain_matches_go_table(path: str, want: str, corpus_runtime) -> None:
    """The bundled-default config is now language-agnostic (Phase 5 / SCRUM-243)
    — the project-specific domain mappings live in
    tests/pr_risk/fixtures/pr-risk-corpus-config.yaml. Tests that exercise those
    mappings load it via the ``corpus_runtime`` fixture (in conftest.py)."""
    assert classify_domain(path, runtime=corpus_runtime) == want


@pytest.mark.parametrize(
    "path,expected",
    [
        ("internal/foo/bar_test.go", True),
        ("web/tests/e2e/auth-login.e2e.ts", True),
        ("web/e2e/smoke.spec.ts", True),
        ("web/src/test/VideoStartOverlay.test.jsx", True),
        ("web/src/components/Foo.test.js", True),
        ("internal/handlers/sessions.go", False),
        ("web/src/App.tsx", False),
        ("internal/testdata/sample.json", True),
        ("playwright.config.ts", True),
        ("foo.spec.tsx", True),
        ("__tests__/snapshot.js", True),
    ],
)
def test_is_test_path(path: str, expected: bool) -> None:
    assert is_test_path(path) is expected


@pytest.mark.parametrize(
    "path,expected",
    [
        ("web/tests/e2e/auth-login.e2e.ts", True),
        ("web/tests/e2e/qa-history.e2e.ts", True),
        ("web/src/App.test.tsx", False),
        ("web/foo/e2e/bar.spec.tsx", True),
        ("internal/foo/e2e/bar.e2e.ts", True),
        ("foo/e2e/bar.go", False),
    ],
)
def test_is_e2e_path(path: str, expected: bool) -> None:
    assert is_e2e_path(path) is expected


@pytest.mark.parametrize(
    "path,expected",
    [
        ("ops/release-readiness/config.yaml", True),
        ("scripts/foo.sh", True),
        ("docs/architecture.md", True),
        ("Makefile", True),
        ("Dockerfile", True),
        (".gitignore", True),
        ("internal/foo/bar.go", False),
    ],
)
def test_is_untestable_path(path: str, expected: bool) -> None:
    assert is_untestable_path(path) is expected


@pytest.mark.parametrize(
    "path,expected",
    [
        (".github/workflows/ci.yml", True),
        (".github/dependabot.yml", True),
        ("deploy/render.yaml", True),
        ("go.mod", True),
        ("go.sum", True),
        ("Dockerfile", True),
        ("internal/foo/bar.go", False),
    ],
)
def test_is_config_path(path: str, expected: bool) -> None:
    assert is_config_path(path) is expected


@pytest.mark.parametrize(
    "path,expected",
    [
        ("db/migrations/0001_x.up.sql", True),
        ("internal/migrations/0042_init.sql", True),
        ("internal/foo/bar.go", False),
        ("db/seeds/users.sql", False),
    ],
)
def test_is_migration_path(path: str, expected: bool) -> None:
    assert is_migration_path(path) is expected


def test_classify_area_orders_orchestration_before_database(corpus_runtime) -> None:
    """orchestration_recommendations is in internal/database/ but routes to orchestration.
    Loads the corpus YAML to exercise the project-specific overlap order."""
    assert (
        classify_area("internal/database/orchestration_recommendations.go", runtime=corpus_runtime)
        == DOMAIN_ORCHESTRATION
    )
    assert (
        classify_area("internal/database/users.go", runtime=corpus_runtime)
        == DOMAIN_DATABASE
    )


def test_touches_sensitive_code_without_tests_with_test_file_returns_false(corpus_runtime) -> None:
    s = Signals(test_files=1, files=[FileChange(path="internal/auth/foo.go")])
    assert touches_sensitive_code_without_tests(s, runtime=corpus_runtime) is False


def test_touches_sensitive_code_without_tests_with_only_other_returns_false(corpus_runtime) -> None:
    s = Signals(files=[FileChange(path="README.md")])
    assert touches_sensitive_code_without_tests(s, runtime=corpus_runtime) is False


def test_touches_sensitive_code_without_tests_with_auth_returns_true(corpus_runtime) -> None:
    s = Signals(files=[FileChange(path="internal/auth/foo.go")])
    assert touches_sensitive_code_without_tests(s, runtime=corpus_runtime) is True


def test_touches_sensitive_code_without_tests_skips_test_paths(corpus_runtime) -> None:
    s = Signals(files=[FileChange(path="internal/auth/foo_test.go")])
    # test_files=0 here intentionally; even so, the test path itself is skipped.
    assert touches_sensitive_code_without_tests(s, runtime=corpus_runtime) is False
