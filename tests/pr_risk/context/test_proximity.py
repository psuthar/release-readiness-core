"""Tests for pr_risk.context.proximity."""

from release_readiness_core.pr_risk.context.input import FileChange, Input
from release_readiness_core.pr_risk.context.proximity import (
    analyze_proximity,
    has_nearby_test_in_diff,
    has_sensitive_production_domains,
)


def _input(*paths_with_test: tuple) -> Input:
    """paths_with_test is iterable of (path, is_test, is_untestable). Domain hits empty."""
    files = []
    is_test = []
    is_untestable = []
    for entry in paths_with_test:
        path, t, u = entry
        files.append(FileChange(path=path))
        is_test.append(t)
        is_untestable.append(u)
    return Input(files=files, is_test=is_test, is_untestable=is_untestable)


def test_no_files_returns_n_a() -> None:
    out = analyze_proximity(Input(files=[]))
    assert out.mode == "n_a"
    assert out.behavioral_coverage == "unknown"


def test_only_test_files_returns_n_a_only_tests() -> None:
    inp = _input(("foo_test.go", True, False))
    out = analyze_proximity(inp)
    assert out.mode == "n_a"
    assert "only test files" in out.detail


def test_distant_when_non_test_files_no_test_files() -> None:
    inp = _input(("internal/auth/foo.go", False, False))
    out = analyze_proximity(inp)
    assert out.mode == "distant"
    assert out.non_test_files == 1


def test_n_a_when_all_untestable_and_no_tests() -> None:
    """YAML/shell/markdown-only diff is not flagged as missing-tests."""
    inp = _input(("config.yaml", False, True), ("README.md", False, True))
    out = analyze_proximity(inp)
    assert out.mode == "n_a"
    assert "config/tooling" in out.detail.lower() or "test proximity is not applicable" in out.detail


def test_co_located_when_test_in_same_dir() -> None:
    inp = _input(
        ("internal/auth/login.go", False, False),
        ("internal/auth/login_test.go", True, False),
    )
    out = analyze_proximity(inp)
    assert out.mode == "co_located"
    assert out.with_nearby_test_in_diff == 1
    assert out.ratio == 1.0


def test_partial_when_some_have_nearby_test() -> None:
    inp = _input(
        ("internal/auth/login.go", False, False),
        ("internal/auth/login_test.go", True, False),
        ("internal/db/conn.go", False, False),
    )
    out = analyze_proximity(inp)
    # 1 of 2 non-test files has a nearby test → ratio 0.5 → partial
    assert out.mode == "partial"
    assert out.ratio == 0.5


def test_distant_when_test_unrelated_dir() -> None:
    inp = _input(
        ("internal/auth/login.go", False, False),
        ("internal/auth/session.go", False, False),
        ("internal/auth/account.go", False, False),
        ("web/totally/different/foo.test.tsx", True, False),
    )
    out = analyze_proximity(inp)
    assert out.mode == "distant"


def test_e2e_special_path_matches_web_code() -> None:
    inp = _input(
        ("web/src/components/Login.tsx", False, False),
        ("web/tests/e2e/auth.e2e.ts", True, False),
    )
    out = analyze_proximity(inp)
    assert out.mode == "co_located"  # web/tests/e2e/* matches any web/ code path


def test_has_sensitive_production_domains() -> None:
    assert has_sensitive_production_domains({"auth": 1}) is True
    assert has_sensitive_production_domains({"web": 5}) is False
    assert has_sensitive_production_domains(None) is False
    assert has_sensitive_production_domains({}) is False


def test_has_nearby_test_in_diff_same_dir() -> None:
    assert has_nearby_test_in_diff(
        "internal/auth/login.go", ["internal/auth/login_test.go"]
    ) is True


def test_has_nearby_test_in_diff_parent_relation() -> None:
    assert has_nearby_test_in_diff(
        "internal/auth/sub/handler.go", ["internal/auth/handler_test.go"]
    ) is True


def test_has_nearby_test_in_diff_distant_paths() -> None:
    assert has_nearby_test_in_diff(
        "internal/auth/login.go", ["unrelated/totally/different_test.go"]
    ) is False


def test_behavioral_coverage_adequate_when_no_sensitive_domains() -> None:
    files = [
        FileChange(path="web/src/App.tsx"),
        FileChange(path="web/src/App.test.tsx"),
    ]
    inp = Input(
        files=files,
        is_test=[False, True],
        is_untestable=[False, False],
        domain_hits={"web": 1},
    )
    out = analyze_proximity(inp)
    assert out.behavioral_coverage == "adequate"


def test_behavioral_coverage_shallow_for_unit_only_with_sensitive_domain() -> None:
    files = [
        FileChange(path="internal/auth/login.go"),
        FileChange(path="internal/auth/login_test.go"),
    ]
    inp = Input(
        files=files,
        is_test=[False, True],
        is_untestable=[False, False],
        domain_hits={"auth": 1},
        test_unit_domain_hits={"auth": 1},
        test_e2e_domain_hits={},
    )
    out = analyze_proximity(inp)
    # Co-located + sensitive domain + unit-only evidence → shallow.
    assert out.mode == "co_located"
    assert out.behavioral_coverage == "shallow"


def test_behavioral_coverage_adequate_for_e2e_with_sensitive_domain() -> None:
    """E2E sit alongside web code; with sensitive domain (auth) hit elsewhere,
    overlapping E2E test domain hits make coverage adequate."""
    files = [
        FileChange(path="web/src/Login.tsx"),
        FileChange(path="web/tests/e2e/auth.e2e.ts"),
    ]
    inp = Input(
        files=files,
        is_test=[False, True],
        is_untestable=[False, False],
        domain_hits={"auth": 1, "web": 1},
        test_e2e_domain_hits={"auth": 1},
    )
    out = analyze_proximity(inp)
    # web/tests/e2e/* satisfies "nearby" to any web/ code path → co_located.
    assert out.mode == "co_located"
    # E2E hit on sensitive domain (auth) → adequate.
    assert out.behavioral_coverage == "adequate"
