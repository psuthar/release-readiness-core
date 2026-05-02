"""Build a GitHub Checks API payload from ``pr-gate-summary.json``.

Console script: ``release-readiness-check-payload``.

Reads a ``pr-gate-summary.json`` produced by ``release-readiness-combine`` and
writes a ``pr-gate-check.json`` payload suitable for ``actions/github-script``
to feed to ``github.rest.checks.create`` / ``checks.update``.

Status mapping:

  PASS  → check conclusion ``success``,                  ``workflow_should_fail`` False
  WARN  → check conclusion ``warn_conclusion`` (param),  ``workflow_should_fail`` False
  BLOCK → check conclusion ``failure``,                  ``workflow_should_fail`` True
  error → check conclusion ``failure``,                  ``workflow_should_fail`` True

``warn_conclusion`` defaults to ``action_required``: blocks ``mergeable_state``
(prevents auto-merge and disables the merge button when the check is required)
while keeping the workflow green — semantically "human review needed", not
"build broken". Pass ``failure`` for "block AND turn the workflow red"
(strict Phase-3 rollout) or ``neutral`` for "visible but non-blocking"
(Phase-1/2 soft rollout).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

from release_readiness_core.pr_gate_combine import GATE_FOOTER_MARKDOWN

DEFAULT_CHECK_NAME = "release-readiness"

VALID_STATUSES = frozenset({"PASS", "WARN", "BLOCK"})

VALID_WARN_CONCLUSIONS = ("action_required", "failure", "neutral")
DEFAULT_WARN_CONCLUSION = "action_required"


def _norm_status(raw: Any) -> str:
    s = (str(raw) if raw is not None else "").strip().upper()
    return s if s in VALID_STATUSES else "UNKNOWN"


def conclusion_for_status(
    status: str, warn_conclusion: str = DEFAULT_WARN_CONCLUSION
) -> str:
    if status == "PASS":
        return "success"
    if status == "WARN":
        return warn_conclusion
    return "failure"


def build_title(status: str, check_name: str) -> str:
    if status in VALID_STATUSES:
        return f"{check_name}: {status}"
    return f"{check_name}: error"


def build_summary_block(gate: dict[str, Any], *, run_url: str = "") -> str:
    base = (gate.get("summary") or "").strip()
    lines = [base] if base else []
    if run_url:
        lines.append(f"Workflow run / artifacts: {run_url}")
    return "\n\n".join(lines) if lines else ""


def build_text_detail(data: dict[str, Any], *, run_url: str = "") -> str:
    pr = data.get("pr_risk") or {}
    rr = data.get("release_readiness") or {}
    fg = data.get("final_gate") or {}
    actions = data.get("required_actions") or []

    pr_s = _norm_status(pr.get("status"))
    rr_s = _norm_status(rr.get("status"))
    fg_s = _norm_status(fg.get("status"))

    pr_label = pr.get("label") or pr_s
    rr_score = rr.get("score")
    rr_line = f"{rr_s} ({rr_score}/100)" if rr_score is not None else str(rr_s)

    lines: list[str] = [
        "### Signals",
        "",
        "| Layer | Status |",
        "|-------|--------|",
        f"| PR Risk | {pr_label} |",
        f"| Release Readiness | {rr_line} |",
        f"| **Final Gate** | **{fg_s}** |",
        "",
    ]

    if actions:
        lines.append("### Required actions before merge")
        lines.append("")
        for a in actions:
            lines.append(f"- {a}")
        lines.append("")

    lines.append("### Supporting detail")
    lines.append("")
    score = pr.get("score")
    band = pr.get("band") or "unknown"
    if score is not None:
        lines.append(f"- PR Risk score: **{score}** / 100 ({band})")
    if pr.get("confidence") is not None:
        lines.append(f"- PR Risk test confidence: **{pr['confidence']}** / 100")
    if rr.get("score") is not None:
        lines.append(f"- Release Readiness score: **{rr['score']}** / 100")
    if rr.get("warnings") is not None:
        lines.append(f"- Release Readiness warnings: **{rr['warnings']}**")
    if rr.get("blockers") is not None:
        lines.append(f"- Release Readiness blockers: **{rr['blockers']}**")
    if rr.get("confidence") is not None:
        lines.append(f"- Release Readiness confidence: **{rr['confidence']}** / 100")
    if fg.get("confidence"):
        lines.append(f"- Gate confidence: **{fg['confidence']}**")

    factors = pr.get("top_risk_factors") or []
    if factors:
        lines.append("")
        lines.append("**Top risk signals:**")
        for f in factors[:6]:
            lines.append(f"- {f}")

    lines.append("")
    lines.append("### Drill-down")
    lines.append("")
    lines.append(
        "Full deterministic report: download workflow artifact **release-readiness** — "
        "files **`pr-gate-summary.md`** and **`pr-gate-summary.json`**."
    )
    if run_url:
        lines.append(f"Job summary and logs: {run_url}")
    lines.append("")
    lines.append(GATE_FOOTER_MARKDOWN)
    return "\n".join(lines)


def build_payload_from_dict(
    data: dict[str, Any],
    *,
    run_url: str = "",
    check_name: str = DEFAULT_CHECK_NAME,
    warn_conclusion: str = DEFAULT_WARN_CONCLUSION,
) -> dict[str, Any]:
    fg = data.get("final_gate") or {}
    status = _norm_status(fg.get("status"))

    if status == "UNKNOWN":
        return build_error_payload(
            "final_gate.status missing or invalid in pr-gate-summary.json",
            raw_json=data,
            run_url=run_url,
            check_name=check_name,
        )

    summary = build_summary_block(fg, run_url=run_url)
    text = build_text_detail(data, run_url=run_url)
    wf_fail = bool(fg.get("workflow_should_fail", status == "BLOCK"))

    return {
        "check_name": check_name,
        "check_conclusion": conclusion_for_status(status, warn_conclusion),
        "title": build_title(status, check_name),
        "summary": summary,
        "text": text,
        "workflow_should_fail": wf_fail,
        "details_url": run_url.strip() or None,
        "final_gate_status": status,
    }


def build_error_payload(
    message: str,
    *,
    raw_json: Any = None,
    run_url: str = "",
    check_name: str = DEFAULT_CHECK_NAME,
) -> dict[str, Any]:
    detail = message
    if raw_json is not None and not isinstance(raw_json, dict):
        detail += f"\n\nUnexpected type: {type(raw_json).__name__}"
    snippet = ""
    if isinstance(raw_json, dict):
        try:
            snippet = json.dumps(raw_json, indent=2)[:6000]
        except Exception:
            snippet = repr(raw_json)[:6000]
    text = "### Error\n\n" + detail
    if snippet:
        text += "\n\n```json\n" + snippet + "\n```"
    if run_url:
        text += f"\n\nWorkflow run: {run_url}"
    return {
        "check_name": check_name,
        "check_conclusion": "failure",
        "title": build_title("UNKNOWN", check_name),
        "summary": f"**{check_name} could not be computed.** {message}",
        "text": text,
        "workflow_should_fail": True,
        "details_url": run_url.strip() or None,
        "final_gate_status": "ERROR",
    }


def run(
    gate_json_path: Path,
    output_path: Path,
    *,
    run_url: str = "",
    check_name: str = DEFAULT_CHECK_NAME,
    warn_conclusion: str = DEFAULT_WARN_CONCLUSION,
) -> dict[str, Any]:
    if not gate_json_path.is_file():
        payload = build_error_payload(
            f"File not found: {gate_json_path}",
            run_url=run_url,
            check_name=check_name,
        )
    else:
        try:
            data = json.loads(gate_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            payload = build_error_payload(
                f"Invalid JSON in {gate_json_path}: {exc}",
                run_url=run_url,
                check_name=check_name,
            )
        else:
            if not isinstance(data, dict):
                payload = build_error_payload(
                    f"Expected JSON object in {gate_json_path}",
                    raw_json=data,
                    run_url=run_url,
                    check_name=check_name,
                )
            else:
                payload = build_payload_from_dict(
                    data,
                    run_url=run_url,
                    check_name=check_name,
                    warn_conclusion=warn_conclusion,
                )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a GitHub Checks API payload from pr-gate-summary.json.",
    )
    parser.add_argument(
        "--gate-json", type=Path, default=Path("artifacts/pr-gate-summary.json"),
        help="Input pr-gate-summary.json (default: %(default)s)",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/pr-gate-check.json"),
        help="Output pr-gate-check.json (default: %(default)s)",
    )
    parser.add_argument(
        "--run-url", default="",
        help="Workflow run URL (used for details_url and summary). "
             "Falls back to $GITHUB_RUN_URL.",
    )
    parser.add_argument(
        "--check-name", default=DEFAULT_CHECK_NAME,
        help="Check name to use in the Checks API payload (default: %(default)s)",
    )
    parser.add_argument(
        "--warn-conclusion",
        default=DEFAULT_WARN_CONCLUSION,
        choices=list(VALID_WARN_CONCLUSIONS),
        help=(
            "GitHub Check conclusion to publish for WARN outcomes. "
            "'action_required' (default) blocks PR merge but keeps the workflow green; "
            "'failure' blocks merge AND turns the workflow red (strict Phase 3 rollout); "
            "'neutral' is visible but non-blocking (Phase 1/2 soft rollout)."
        ),
    )
    args = parser.parse_args(argv)

    run_url = (args.run_url or "").strip() or os.environ.get("GITHUB_RUN_URL", "").strip()

    payload = run(
        gate_json_path=args.gate_json,
        output_path=args.output,
        run_url=run_url,
        check_name=args.check_name,
        warn_conclusion=args.warn_conclusion,
    )

    print(payload["title"], "->", payload["check_conclusion"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
