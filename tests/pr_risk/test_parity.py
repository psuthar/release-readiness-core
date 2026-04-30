"""End-to-end parity harness: runs the Python pr_risk CLI against captured
Go-emitted goldens and diffs each expected output file.

This file is the framework only; the Python pipeline that satisfies parity
is built incrementally across SCRUM-233..236. Until then every fixture is
SKIPPED with a clear reason. Once a phase lands, the relevant assertions
become live (see ``ParityScope``).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def discover_fixtures() -> list[Path]:
    if not FIXTURES_DIR.exists():
        return []
    return sorted(p for p in FIXTURES_DIR.iterdir() if p.is_dir() and (p / "meta.json").is_file())


def fixture_id(path: Path) -> str:
    return path.name


@dataclass(frozen=True)
class Fixture:
    path: Path
    meta: dict
    pr_risk_json: Optional[dict]
    semantic_pr_risk: Optional[dict]
    pr_risk_md: Optional[str]

    @classmethod
    def load(cls, path: Path) -> "Fixture":
        meta = json.loads((path / "meta.json").read_text())
        pr_full = path / "pr_risk.json"
        sem = path / "pr-risk.json"
        md = path / "pr_risk.md"
        return cls(
            path=path,
            meta=meta,
            pr_risk_json=json.loads(pr_full.read_text()) if pr_full.is_file() else None,
            semantic_pr_risk=json.loads(sem.read_text()) if sem.is_file() else None,
            pr_risk_md=md.read_text() if md.is_file() else None,
        )


# Parity scope flag — flipped on per phase as ports land.
# Phase 0: PARITY_SCOPE = "none"
# Phase 2 (context only): PARITY_SCOPE = "context"
# Phase 3 (score-level): PARITY_SCOPE = "score"
# Phase 4 (full): PARITY_SCOPE = "full"
PARITY_SCOPE = os.environ.get("PR_RISK_PARITY_SCOPE", "none")


_DISCOVERED = discover_fixtures()


@pytest.fixture(scope="session")
def fixtures() -> list[Fixture]:
    return [Fixture.load(p) for p in _DISCOVERED]


def _skip_until_implemented(reason: str) -> None:
    pytest.skip(f"PR Risk Python pipeline not implemented yet: {reason}")


@pytest.mark.parametrize("fixture_path", _DISCOVERED, ids=fixture_id)
def test_corpus_loads(fixture_path: Path) -> None:
    """Every captured fixture must have a parseable meta.json + at least one Go output."""
    fx = Fixture.load(fixture_path)
    assert fx.meta.get("schema_version") == "1.0", f"unexpected schema_version in {fixture_path}"
    assert fx.meta.get("merge_sha"), f"missing merge_sha in {fixture_path}/meta.json"
    assert fx.meta.get("parent_sha"), f"missing parent_sha in {fixture_path}/meta.json"
    assert fx.semantic_pr_risk is not None, f"missing pr-risk.json in {fixture_path}"


@pytest.mark.parametrize("fixture_path", _DISCOVERED, ids=fixture_id)
def test_semantic_pr_risk_parity(fixture_path: Path) -> None:
    """Byte-identical pr-risk.json (the "semantic" file). Closes in Phase 4 (SCRUM-236)."""
    if PARITY_SCOPE != "full":
        _skip_until_implemented("semantic pr-risk.json parity is gated until Phase 4 (SCRUM-236)")
    # When Phase 4 lands, this branch will:
    #   1. invoke release-readiness-pr-risk against a checked-out fixture
    #   2. compare its pr-risk.json to fx.semantic_pr_risk via canonical jq -S
    raise AssertionError("unreachable until Phase 4 wiring lands")


@pytest.mark.parametrize("fixture_path", _DISCOVERED, ids=fixture_id)
def test_pr_risk_full_parity(fixture_path: Path) -> None:
    """Deep-equal pr_risk.json. Closes in Phase 4 (SCRUM-236)."""
    if PARITY_SCOPE != "full":
        _skip_until_implemented("pr_risk.json parity is gated until Phase 4 (SCRUM-236)")
    raise AssertionError("unreachable until Phase 4 wiring lands")


@pytest.mark.parametrize("fixture_path", _DISCOVERED, ids=fixture_id)
def test_score_level_parity(fixture_path: Path) -> None:
    """Score, band, score_math, categories, merge_recommendation. Closes in Phase 3 (SCRUM-235)."""
    if PARITY_SCOPE not in {"score", "full"}:
        _skip_until_implemented("score-level parity is gated until Phase 3 (SCRUM-235)")
    raise AssertionError("unreachable until Phase 3 wiring lands")


@pytest.mark.parametrize("fixture_path", _DISCOVERED, ids=fixture_id)
def test_context_insights_parity(fixture_path: Path) -> None:
    """ContextInsights subtree of pr_risk.json. Closes in Phase 2 (SCRUM-234)."""
    if PARITY_SCOPE not in {"context", "score", "full"}:
        _skip_until_implemented("context parity is gated until Phase 2 (SCRUM-234)")
    raise AssertionError("unreachable until Phase 2 wiring lands")


def test_cli_help_works() -> None:
    """The Phase 0 stub CLI must at least respond to --help cleanly."""
    res = subprocess.run(
        [sys.executable, "-m", "release_readiness_core.pr_risk.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stderr
    assert "release-readiness-pr-risk" in res.stdout


def test_cli_runs_against_a_repo(tmp_path: Path) -> None:
    """Phase 4 CLI should run end-to-end against a synthetic repo and produce the three artifacts."""
    import subprocess as _sp
    repo = tmp_path / "repo"
    repo.mkdir()
    _sp.run(["git", "-C", str(repo), "init", "--initial-branch=main"], check=True, capture_output=True)
    _sp.run(["git", "-C", str(repo), "config", "user.email", "t@t.test"], check=True, capture_output=True)
    _sp.run(["git", "-C", str(repo), "config", "user.name", "T"], check=True, capture_output=True)
    _sp.run(["git", "-C", str(repo), "config", "commit.gpgsign", "false"], check=True, capture_output=True)
    (repo / "README.md").write_text("a\n")
    _sp.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    _sp.run(["git", "-C", str(repo), "commit", "-m", "init"], check=True, capture_output=True)
    base = _sp.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    (repo / "internal" / "auth").mkdir(parents=True)
    (repo / "internal" / "auth" / "login.go").write_text("package auth\n")
    _sp.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    _sp.run(["git", "-C", str(repo), "commit", "-m", "feat: auth"], check=True, capture_output=True)
    out_dir = tmp_path / "artifacts" / "release-readiness"

    res = subprocess.run(
        [
            sys.executable,
            "-m",
            "release_readiness_core.pr_risk.cli",
            "--repo-root",
            str(repo),
            "--base-ref",
            base,
            "--output-dir",
            str(out_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0, res.stderr
    assert (out_dir / "pr_risk.json").is_file()
    assert (out_dir / "pr_risk.md").is_file()
    assert (out_dir.parent / "pr-risk.json").is_file()
