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
