"""Regression test for the second-project example.

This test runs the ``release-readiness-evaluate`` CLI end-to-end against the
fixture at ``examples/second-project/``. It exists so changes to the engine,
the markdown renderer, or the CLI cannot silently break the documented
quickstart for an unrelated adopter project.

If you intentionally change the second-project fixture or the package's
default behavior, update the assertions below.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = REPO_ROOT / "examples" / "second-project"


def _run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    env_cmd = [sys.executable, "-m", "release_readiness_core.readiness_evaluate", *args]
    return subprocess.run(env_cmd, cwd=str(cwd), capture_output=True, text=True, check=False)


@pytest.fixture()
def clean_artifacts():
    artifacts = EXAMPLE / "artifacts"
    if artifacts.exists():
        shutil.rmtree(artifacts)
    yield artifacts
    if artifacts.exists():
        shutil.rmtree(artifacts)


def test_second_project_example_pass(clean_artifacts: Path):
    proc = _run_cli(
        [
            "--repo-root",
            ".",
            "--config",
            "config.yaml",
            "--smoke-results",
            "evidence/smoke.json",
            "--e2e-results",
            "evidence/e2e.json",
            "--coverage",
            "evidence/coverage.json",
            "--empty-diff",
            "--output-dir",
            "artifacts/release-readiness",
        ],
        cwd=EXAMPLE,
    )
    assert proc.returncode == 0, f"CLI failed:\nstdout={proc.stdout}\nstderr={proc.stderr}"

    report_json = clean_artifacts / "release-readiness" / "report.json"
    assert report_json.exists(), "report.json was not written"
    payload = json.loads(report_json.read_text(encoding="utf-8"))
    assert payload["outcome"] == "PASS"
    assert payload["score"] == 100.0
    assert payload["blockers"] == []
    assert payload["warnings"] == []


def test_second_project_blocks_when_evidence_missing_for_risk(tmp_path: Path):
    """Direct engine call: changes under migrations/** without evidence → BLOCK."""
    import yaml

    from release_readiness_core.readiness_engine import compute_readiness

    config = yaml.safe_load((EXAMPLE / "config.yaml").read_text(encoding="utf-8"))
    res = compute_readiness(
        config=config,
        changed_files=["migrations/0001_init.py"],
        smoke=None,
        e2e=None,
        coverage=None,
        prod_health=None,
        migration_validated_cli=False,
    )
    assert res.outcome == "BLOCK"
    # Risk category and required validation differ now (config maps
    # schema_changes -> db_migrations) — verify the mapping is honored.
    assert "schema_changes" in res.risks_triggered
    assert "db_migrations" in res.validations_required
