"""Static guard tests for the per-stack example workflows under examples/.

These workflows are documentation, not exercised in CI directly. Tests assert
they reference the Tier-1 reusable workflow at the canonical path, are
yamllint-loadable, and use the documented adapter for their stack.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"

EXAMPLE_DIRS = (
    "second-project",
    "python-pytest",
    "node-playwright",
)


def _workflow_for(example: str) -> Path:
    return EXAMPLES_DIR / example / ".github" / "workflows" / "release-readiness.yml"


def _readme_for(example: str) -> Path:
    return EXAMPLES_DIR / example / "README.md"


def _config_for(example: str) -> Path:
    return EXAMPLES_DIR / example / "ops" / "release-readiness" / "config.yaml"


@pytest.mark.parametrize("example", EXAMPLE_DIRS)
def test_example_workflow_exists(example: str):
    assert _workflow_for(example).is_file(), f"missing workflow for {example}"


@pytest.mark.parametrize("example", EXAMPLE_DIRS)
def test_example_workflow_loads_as_yaml(example: str):
    yaml.safe_load(_workflow_for(example).read_text(encoding="utf-8"))


@pytest.mark.parametrize("example", EXAMPLE_DIRS)
def test_example_workflow_calls_reusable_workflow(example: str):
    text = _workflow_for(example).read_text(encoding="utf-8")
    assert "psuthar/release-readiness-core/.github/workflows/readiness.yml@" in text, (
        f"{example} does not call Tier-1 reusable workflow"
    )


@pytest.mark.parametrize("example", EXAMPLE_DIRS)
def test_example_readme_exists(example: str):
    assert _readme_for(example).is_file(), f"missing README for {example}"


@pytest.mark.parametrize("example", ("python-pytest", "node-playwright"))
def test_greenfield_examples_have_config_yaml(example: str):
    """The two greenfield examples must ship a runnable starter config."""
    cfg = _config_for(example)
    assert cfg.is_file()
    data = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert "validations" in data
    assert "scoring" in data


def test_second_project_workflow_references_existing_evidence():
    text = _workflow_for("second-project").read_text(encoding="utf-8")
    # The fixture's evidence files already exist in the repo.
    for rel in (
        "examples/second-project/evidence/smoke.json",
        "examples/second-project/evidence/e2e.json",
        "examples/second-project/evidence/coverage.json",
    ):
        assert (REPO_ROOT / rel).is_file(), f"second-project workflow expects {rel}"
        assert rel in text


def test_python_pytest_workflow_uses_junit_to_readiness():
    text = _workflow_for("python-pytest").read_text(encoding="utf-8")
    assert "junit-to-readiness" in text
    assert "pytest --junit-xml" in text


def test_node_playwright_workflow_uses_playwright_to_readiness():
    text = _workflow_for("node-playwright").read_text(encoding="utf-8")
    assert "playwright-to-readiness" in text
    assert "playwright test --reporter=json" in text
