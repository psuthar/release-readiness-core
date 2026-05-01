"""Tests for the ``release-readiness-init`` scaffold."""

from __future__ import annotations

from pathlib import Path

import pytest

from release_readiness_core.init_scaffold import (
    CONFIG_TEMPLATE,
    GITHUB_WORKFLOW_TEMPLATE,
    main,
    scaffold,
)
from release_readiness_core.readiness_io import load_yaml_config


def test_scaffold_creates_expected_files(tmp_path: Path):
    results = scaffold(tmp_path)
    assert results["ops/release-readiness/config.yaml"] == "created"
    assert results["ops/release-readiness/validation_map.yaml"] == "created"
    assert results[".github/workflows/release-readiness.yml"] == "created"
    assert (tmp_path / "ops/release-readiness/config.yaml").is_file()
    assert (tmp_path / ".github/workflows/release-readiness.yml").is_file()


def test_scaffold_workflow_none_skips_workflow(tmp_path: Path):
    results = scaffold(tmp_path, workflow="none")
    assert ".github/workflows/release-readiness.yml" not in results
    assert not (tmp_path / ".github/workflows/release-readiness.yml").exists()


def test_scaffold_skips_existing_without_force(tmp_path: Path):
    scaffold(tmp_path)
    target_file = tmp_path / "ops/release-readiness/config.yaml"
    target_file.write_text("USER EDITED CONTENT", encoding="utf-8")
    results = scaffold(tmp_path)
    assert results["ops/release-readiness/config.yaml"] == "skipped (exists)"
    assert target_file.read_text(encoding="utf-8") == "USER EDITED CONTENT"


def test_scaffold_force_overwrites(tmp_path: Path):
    scaffold(tmp_path)
    target_file = tmp_path / "ops/release-readiness/config.yaml"
    target_file.write_text("USER EDITED CONTENT", encoding="utf-8")
    results = scaffold(tmp_path, force=True)
    assert results["ops/release-readiness/config.yaml"] == "overwrote"
    assert "USER EDITED CONTENT" not in target_file.read_text(encoding="utf-8")


def test_scaffold_unknown_workflow_raises(tmp_path: Path):
    with pytest.raises(ValueError):
        scaffold(tmp_path, workflow="circleci")


def test_scaffolded_config_loads_against_schema_validation(tmp_path: Path):
    """The scaffolded config must pass our own schema validator — otherwise
    new adopters would hit a ConfigSchemaError on first run."""
    scaffold(tmp_path)
    cfg = load_yaml_config(tmp_path / "ops/release-readiness/config.yaml")
    assert cfg["version"] == 1
    assert "scoring" in cfg
    assert "smoke_passing" in cfg["validations"]


def test_main_writes_to_target_directory(tmp_path: Path, capsys: pytest.CaptureFixture):
    code = main([str(tmp_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert "Scaffolded" in out
    assert "Next steps" in out


def test_main_workflow_none(tmp_path: Path):
    code = main([str(tmp_path), "--workflow", "none"])
    assert code == 0
    assert not (tmp_path / ".github").exists()


def test_workflow_template_references_pinned_sha_placeholder():
    """The workflow template must remind adopters to pin a SHA — this
    test guards against accidentally shipping an unpinned `@main`."""
    assert "@<sha>" in GITHUB_WORKFLOW_TEMPLATE


def test_config_template_references_optional_artifacts_pattern():
    """scaffolded config demonstrates the optional_artifacts
    opt-out (avoids the second-project gap #2 surprise on first run)."""
    assert "optional_artifacts:" in CONFIG_TEMPLATE
    assert "prod_health" in CONFIG_TEMPLATE


# ---------------------------------------------------------------------------
# --demo flag
# ---------------------------------------------------------------------------


def test_scaffold_without_demo_does_not_write_evidence(tmp_path: Path):
    results = scaffold(tmp_path)
    assert "evidence/smoke.json" not in results
    assert not (tmp_path / "evidence").exists()


def test_scaffold_demo_writes_three_evidence_files(tmp_path: Path):
    results = scaffold(tmp_path, demo=True)
    for rel in ("evidence/smoke.json", "evidence/e2e.json", "evidence/coverage.json"):
        assert results[rel] == "created"
        assert (tmp_path / rel).is_file()


def test_demo_evidence_carries_synthetic_marker(tmp_path: Path):
    import json
    scaffold(tmp_path, demo=True)
    for rel in ("evidence/smoke.json", "evidence/e2e.json", "evidence/coverage.json"):
        data = json.loads((tmp_path / rel).read_text(encoding="utf-8"))
        assert "_comment" in data
        assert "Synthetic" in data["_comment"]
        assert "1-map-evidence.md" in data["_comment"]


def test_demo_evidence_produces_pass_outcome(tmp_path: Path):
    """End-to-end: scaffold with --demo, run release-readiness-evaluate,
    expect PASS / score=100."""
    import subprocess
    import sys
    scaffold(tmp_path, demo=True)
    result = subprocess.run(
        [
            sys.executable, "-m", "release_readiness_core.readiness_evaluate",
            "--repo-root", str(tmp_path),
            "--config", "ops/release-readiness/config.yaml",
            "--smoke-results", "evidence/smoke.json",
            "--e2e-results", "evidence/e2e.json",
            "--coverage", "evidence/coverage.json",
            "--empty-diff",
            "--output-dir", "artifacts/release-readiness",
        ],
        capture_output=True, text=True, cwd=str(tmp_path),
    )
    assert result.returncode == 0, f"evaluate failed: {result.stderr}"
    # Verify PASS in the lean summary.
    import json
    summary = json.loads((tmp_path / "artifacts" / "release-readiness.json").read_text(encoding="utf-8"))
    assert summary["outcome"] == "PASS", f"expected PASS, got {summary['outcome']}; full summary: {summary}"
    assert summary["score"] == 100, f"expected score 100, got {summary['score']}"


def test_main_demo_flag_writes_evidence(tmp_path: Path, capsys: pytest.CaptureFixture):
    code = main([str(tmp_path), "--demo"])
    assert code == 0
    assert (tmp_path / "evidence" / "smoke.json").is_file()
    out = capsys.readouterr().out
    assert "Demo evidence written" in out


def test_scaffold_without_demo_byte_identical_to_legacy(tmp_path: Path):
    """Without --demo, the scaffold output must be byte-identical to the
    pre-D1 behavior (no regressions for adopters who don't opt in)."""
    a = tmp_path / "a"
    b = tmp_path / "b"
    scaffold(a)
    scaffold(b, demo=False)
    for path_a in a.rglob("*"):
        if path_a.is_file():
            rel = path_a.relative_to(a)
            path_b = b / rel
            assert path_b.read_bytes() == path_a.read_bytes(), f"divergence at {rel}"


# ---------------------------------------------------------------------------
# --stack flag
# ---------------------------------------------------------------------------


from release_readiness_core.init_scaffold import VALID_STACKS, render_workflow_template


@pytest.mark.parametrize("stack", VALID_STACKS)
def test_render_workflow_template_for_each_stack(stack: str):
    body = render_workflow_template(stack)
    # Common header (stack-agnostic) preserved.
    assert "name: release-readiness" in body
    assert "uses: actions/checkout@v5" in body
    # Stack-specific marker should be present.
    markers = {
        "playwright": "playwright-to-readiness",
        "cypress": "cypress run",
        "jest": "jest-junit",
        "pytest": "pytest --junit-xml",
        "go": "go test ./...",
        "go-coverage": "lcov-to-readiness",
    }
    assert markers[stack] in body, f"{stack} marker missing in rendered workflow"


def test_render_workflow_template_default_uses_commented_placeholder():
    body = render_workflow_template(None)
    # Commented placeholder marker.
    assert "Replace the placeholders below" in body


def test_scaffold_with_stack_uncomments_runner_block(tmp_path: Path):
    scaffold(tmp_path, stack="playwright")
    workflow = (tmp_path / ".github/workflows/release-readiness.yml").read_text(encoding="utf-8")
    assert "Replace the placeholders below" not in workflow
    assert "Run Playwright" in workflow


def test_scaffold_unknown_stack_raises(tmp_path: Path):
    with pytest.raises(ValueError, match="--stack must be one of"):
        scaffold(tmp_path, stack="circleci")


def test_scaffold_stack_combines_with_demo(tmp_path: Path):
    """--stack and --demo are independent; combining must work."""
    scaffold(tmp_path, stack="pytest", demo=True)
    assert (tmp_path / "evidence" / "smoke.json").is_file()
    workflow = (tmp_path / ".github/workflows/release-readiness.yml").read_text(encoding="utf-8")
    assert "pytest --junit-xml" in workflow


def test_scaffold_without_stack_byte_identical(tmp_path: Path):
    """Without --stack and without --demo, scaffold output must remain
    byte-identical to today's behavior (no regression)."""
    a = tmp_path / "a"
    b = tmp_path / "b"
    scaffold(a)
    scaffold(b, stack=None, demo=False)
    for path_a in a.rglob("*"):
        if path_a.is_file():
            rel = path_a.relative_to(a)
            assert (b / rel).read_bytes() == path_a.read_bytes()


def test_main_unknown_stack_exits_nonzero(tmp_path: Path, capsys: pytest.CaptureFixture):
    """argparse's choices= validation raises SystemExit(2) on invalid input
    and prints valid choices to stderr — that's the clean-error path."""
    with pytest.raises(SystemExit) as exc:
        main([str(tmp_path), "--stack", "circleci"])
    assert exc.value.code != 0
    err = capsys.readouterr().err
    # The error message must enumerate valid choices.
    for stack in VALID_STACKS:
        assert stack in err


@pytest.mark.parametrize("stack", VALID_STACKS)
def test_main_each_stack_succeeds(tmp_path: Path, stack: str):
    sub = tmp_path / stack
    code = main([str(sub), "--stack", stack])
    assert code == 0
    workflow_path = sub / ".github/workflows/release-readiness.yml"
    assert workflow_path.is_file()
    body = workflow_path.read_text(encoding="utf-8")
    # The commented placeholder must be replaced.
    assert "Replace the placeholders below" not in body


# ---------------------------------------------------------------------------
# --pin flag (D2)
# ---------------------------------------------------------------------------


from release_readiness_core.init_scaffold import (
    PIN_REF_ENV_VAR,
    resolve_pin_ref,
)


def test_resolve_pin_ref_arg_wins(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(PIN_REF_ENV_VAR, "from-env")
    assert resolve_pin_ref("from-arg") == "from-arg"


def test_resolve_pin_ref_falls_back_to_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(PIN_REF_ENV_VAR, "abc1234")
    assert resolve_pin_ref(None) == "abc1234"


def test_resolve_pin_ref_falls_back_to_default(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(PIN_REF_ENV_VAR, raising=False)
    # DEFAULT_PIN_REF is empty in dev; resolution returns empty string.
    assert resolve_pin_ref(None) == ""


def test_resolve_pin_ref_treats_whitespace_as_unset(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv(PIN_REF_ENV_VAR, raising=False)
    assert resolve_pin_ref("   ") == ""


def test_scaffold_with_pin_substitutes_sha_in_workflow(tmp_path: Path):
    scaffold(tmp_path, pin_ref="abc1234567")
    body = (tmp_path / ".github/workflows/release-readiness.yml").read_text(encoding="utf-8")
    assert "<sha>" not in body
    assert "abc1234567" in body


def test_scaffold_without_pin_keeps_sha_placeholder(tmp_path: Path):
    scaffold(tmp_path)  # no pin_ref
    body = (tmp_path / ".github/workflows/release-readiness.yml").read_text(encoding="utf-8")
    assert "<sha>" in body


def test_scaffold_pin_byte_identical_to_no_pin_for_other_files(tmp_path: Path):
    """--pin only affects the workflow file; other scaffold files are
    byte-identical to the no-pin output."""
    a = tmp_path / "a"
    b = tmp_path / "b"
    scaffold(a)
    scaffold(b, pin_ref="deadbeef")
    for path_a in a.rglob("*"):
        if path_a.is_file() and path_a.relative_to(a).as_posix() != ".github/workflows/release-readiness.yml":
            assert (b / path_a.relative_to(a)).read_bytes() == path_a.read_bytes()


def test_main_pin_arg_substitutes(tmp_path: Path, capsys: pytest.CaptureFixture):
    code = main([str(tmp_path), "--pin", "v0.4.0"])
    assert code == 0
    body = (tmp_path / ".github/workflows/release-readiness.yml").read_text(encoding="utf-8")
    assert "<sha>" not in body
    assert "v0.4.0" in body
    out = capsys.readouterr().out
    assert "Workflow pinned to v0.4.0" in out


def test_main_pin_env_substitutes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture):
    monkeypatch.setenv(PIN_REF_ENV_VAR, "abc1234")
    code = main([str(tmp_path)])
    assert code == 0
    body = (tmp_path / ".github/workflows/release-readiness.yml").read_text(encoding="utf-8")
    assert "abc1234" in body


def test_main_no_pin_source_prints_replace_hint(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture):
    monkeypatch.delenv(PIN_REF_ENV_VAR, raising=False)
    code = main([str(tmp_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert "Replace <sha>" in out
    assert "RR_PIN_REF" in out
