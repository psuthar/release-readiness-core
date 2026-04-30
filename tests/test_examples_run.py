"""End-to-end: every config under examples/pr-risk/ runs through the CLI on a small
synthetic git repo (Phase 6).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples" / "pr-risk"


def _example_paths() -> list[Path]:
    if not EXAMPLES_DIR.is_dir():
        return []
    return sorted(EXAMPLES_DIR.glob("*.yaml"))


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=True,
    )
    return out.stdout


def _commit(repo: Path, msg: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=t@t.t", "-c", "user.name=t",
         "commit", "-m", msg)


@pytest.fixture
def synth_repo(tmp_path: Path) -> Path:
    """A tiny git repo with one commit on main, then a branch with a small diff."""
    if shutil.which("git") is None:
        pytest.skip("git not available")
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "--initial-branch=main")
    (repo / "README.md").write_text("# repo\n")
    _commit(repo, "init")
    # Make a tiny change.
    (repo / "src").mkdir()
    (repo / "src" / "thing.py").write_text("print('hi')\n")
    _commit(repo, "feat: add thing")
    return repo


@pytest.mark.parametrize("config_path", _example_paths(), ids=lambda p: p.name)
def test_example_runs_against_synth_repo(
    config_path: Path, synth_repo: Path, tmp_path: Path
) -> None:
    """The CLI should accept the example config, score the synth repo's diff,
    and emit pr_risk.json / pr-risk.json without crashing."""
    out_dir = tmp_path / "out"
    base_ref = _git(synth_repo, "rev-parse", "HEAD~1").strip()

    result = subprocess.run(
        [
            "uv", "run", "release-readiness-pr-risk",
            "--repo-root", str(synth_repo),
            "--base-ref", base_ref,
            "--config", str(config_path),
            "--output-dir", str(out_dir),
        ],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"CLI failed for {config_path.name}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )

    pr_risk_json = out_dir / "pr_risk.json"
    semantic_json = out_dir.parent / "pr-risk.json"
    assert pr_risk_json.is_file(), f"missing {pr_risk_json}"
    assert semantic_json.is_file(), f"missing {semantic_json}"

    payload = json.loads(pr_risk_json.read_text())
    # Sanity: the output references the loaded config's domain ids — never
    # the bundled-default project specifics.
    forbidden_default_specifics = {"auth_e2e_gate", "rag_qna_citations_gate"}
    action_ids = {a["id"] for a in payload.get("required_actions", [])}
    # Examples may emit api_e2e_gate, db_migration_gate, etc. but never the
    # legacy project-specific ones.
    assert action_ids.isdisjoint(forbidden_default_specifics), (
        f"{config_path.name}: emitted forbidden actions {action_ids & forbidden_default_specifics}"
    )
