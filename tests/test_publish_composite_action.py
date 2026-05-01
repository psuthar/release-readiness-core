"""Static tests for the .github/actions/release-readiness-publish composite.

The action's runtime behavior (Check API call + sticky comment) is exercised
in real workflow runs, not in unit tests. These tests assert the action.yml
structure and the forked-PR fallback logic so regressions surface early.
"""

from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTION_PATH = REPO_ROOT / ".github" / "actions" / "release-readiness-publish" / "action.yml"


def _load_action() -> dict:
    return yaml.safe_load(ACTION_PATH.read_text(encoding="utf-8"))


def test_action_file_exists():
    assert ACTION_PATH.is_file()


def test_action_is_composite():
    action = _load_action()
    assert action.get("runs", {}).get("using") == "composite"


def test_action_declares_required_inputs():
    action = _load_action()
    inputs = action.get("inputs", {})
    expected = {
        "gate-payload",
        "report-md",
        "check-name",
        "comment-header",
        "github-token",
        "comment-on-pr",
        "publish-check",
    }
    missing = expected - set(inputs.keys())
    assert not missing, f"missing inputs: {missing}"


def test_github_token_is_required():
    action = _load_action()
    assert action["inputs"]["github-token"].get("required") is True


def test_comment_on_pr_and_publish_check_default_true_strings():
    action = _load_action()
    # action.yml booleans are strings — gh actions interprets the input value as a string.
    assert action["inputs"]["comment-on-pr"]["default"] == "true"
    assert action["inputs"]["publish-check"]["default"] == "true"


def test_action_appends_to_step_summary():
    text = ACTION_PATH.read_text(encoding="utf-8")
    assert "$GITHUB_STEP_SUMMARY" in text
    assert 'if: always()' in text


def test_action_uses_pinned_sticky_comment_action():
    text = ACTION_PATH.read_text(encoding="utf-8")
    assert "marocchino/sticky-pull-request-comment@v2" in text


def test_action_uses_actions_github_script_v8():
    text = ACTION_PATH.read_text(encoding="utf-8")
    assert "actions/github-script@v8" in text


def test_check_publish_step_is_idempotent():
    """The github-script body must look up an existing check by name + head SHA
    and update it rather than creating duplicates."""
    text = ACTION_PATH.read_text(encoding="utf-8")
    assert "checks.listForRef" in text
    assert "checks.update" in text
    assert "checks.create" in text


def test_check_publish_step_handles_forked_pr_token_failure():
    """When checks:write permission is missing (forked PR), the action must
    catch the failure and emit a warning instead of erroring out."""
    text = ACTION_PATH.read_text(encoding="utf-8")
    assert "core.warning" in text
    # The try/catch around the checks API calls.
    assert "try {" in text
    assert "} catch (err)" in text


def test_sticky_comment_step_is_pull_request_only():
    """The sticky comment must only post on pull_request events to avoid
    spurious comments from push / scheduled runs."""
    action = _load_action()
    steps = action.get("runs", {}).get("steps", [])
    sticky = [s for s in steps if "marocchino" in (s.get("uses") or "")]
    assert sticky, "sticky-comment step missing"
    cond = sticky[0].get("if", "")
    assert "pull_request" in cond


def test_sticky_comment_step_continues_on_error():
    """Sticky-comment failures must not fail the action — degraded experience
    on token-restricted PRs is preferable to a red workflow."""
    action = _load_action()
    steps = action.get("runs", {}).get("steps", [])
    sticky = [s for s in steps if "marocchino" in (s.get("uses") or "")]
    assert sticky[0].get("continue-on-error") is True
