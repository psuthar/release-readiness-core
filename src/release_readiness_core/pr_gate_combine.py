"""Unified PR gate combiner — reads pr-risk + release-readiness JSON, writes pr-gate-summary.{json,md}.

Console script: ``release-readiness-combine``.

Combines two CI signals into a single deterministic verdict:

  - ``artifacts/pr-risk.json`` (lean semantic summary from ``release-readiness-pr-risk``)
  - ``artifacts/release-readiness.json`` (lean machine summary from ``release-readiness-evaluate``)

Optionally enriches with the full ``release-readiness/report.json`` for blocker /
warning strings used in the rendered required-actions list.

Combining rule (highest severity wins): ``BLOCK > WARN > PASS``.

Exit codes:
  0 — gate computed successfully (PASS, WARN, or BLOCK).
  1 — one or both inputs could not be parsed; gate forced to BLOCK and a partial
      summary is still written.

This is the project-agnostic descendant of TalkBack's ``scripts/pr_gate.py``.
TalkBack-specific phrase rewrites and priority taxonomies are intentionally not
included — adopters get a clean dedupe + grouping; if they want phrase polish,
they can post-process the JSON.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

VERSION = "v1"

REC_DISPLAY: dict[str, str] = {
    "PASS": "PASS (low risk)",
    "WARN": "WARN",
    "BLOCK": "BLOCK",
}
STATUS_EMOJI: dict[str, str] = {
    "PASS": "🟢",
    "WARN": "🟡",
    "BLOCK": "🔴",
}

STANDARD_ACTIONS: list[str] = [
    "CI checks must pass",
    "At least one approving review is required",
]

GATE_FOOTER_MARKDOWN: str = (
    "_This gate is deterministic. "
    "**PASS** does not bypass branch protection or required code review. "
    "**WARN** requires completing validations and review before merging. "
    "**BLOCK** means do not merge until all blockers are resolved._"
)


def gate_decision_summary(gate_status: str, gate_confidence: str) -> str:
    """Confidence-aware decision text. ``gate_confidence`` ∈ {high, moderate, low}."""
    if gate_status == "PASS":
        if gate_confidence == "high":
            return (
                "Low-risk change and readiness checks passed with strong supporting "
                "confidence. Normal merge prerequisites still apply before merge."
            )
        if gate_confidence == "moderate":
            return (
                "Low-risk change and readiness checks passed with moderate supporting "
                "confidence. Normal merge prerequisites still apply before merge."
            )
        return (
            "Low-risk change and readiness checks passed, but supporting confidence "
            "is limited. Normal merge prerequisites still apply before merge."
        )
    if gate_status == "WARN":
        if gate_confidence == "high":
            return (
                "Not blocked, but elevated attention is required due to warnings. "
                "Complete the required validations and review before merging."
            )
        if gate_confidence == "moderate":
            return (
                "Not blocked, but elevated attention is required due to warnings "
                "and only moderate supporting confidence. "
                "Complete the required validations before merging."
            )
        return (
            "Not blocked, but elevated attention is required due to warnings and "
            "low supporting confidence. Complete the required validations and "
            "review before merging."
        )
    return (
        "One or more hard blockers detected. "
        "Do not merge until all blockers are resolved."
    )


@dataclass
class PRRiskInput:
    status: str
    score: float
    band: str
    label: str
    confidence: Optional[int] = None
    required_validations: list[str] = field(default_factory=list)
    top_risk_factors: list[str] = field(default_factory=list)


@dataclass
class ReadinessInput:
    status: str
    score: float
    warnings_count: int
    blockers_count: int
    blocker_messages: list[str] = field(default_factory=list)
    warning_messages: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    critical_failed_titles: list[str] = field(default_factory=list)
    non_critical_failed_titles: list[str] = field(default_factory=list)
    report_enriched: bool = False


def normalize_status(s: Any) -> str:
    s = (str(s) if s is not None else "").strip().upper()
    if s not in ("PASS", "WARN", "BLOCK"):
        raise ValueError(f"Unknown gate status: {s!r}")
    return s


def compute_gate_status(rr_status: str, risk_status: str) -> str:
    if rr_status == "BLOCK" or risk_status == "BLOCK":
        return "BLOCK"
    if rr_status == "WARN" or risk_status == "WARN":
        return "WARN"
    return "PASS"


def derive_rr_confidence(rr: ReadinessInput) -> int:
    base = min(95, int(rr.score))
    if rr.blockers_count > 0:
        base = min(base, 50)
    return base


def classify_gate_confidence(
    risk_conf: Optional[int],
    rr_conf: int,
    gate_status: str,
) -> str:
    if gate_status == "BLOCK":
        return "low"
    rc = risk_conf if risk_conf is not None else 50
    combined = (rc + rr_conf) // 2
    if combined >= 80:
        return "high"
    if combined >= 60:
        return "moderate"
    return "low"


def _action_key(s: str) -> str:
    return s.strip().rstrip(".").lower()


def build_required_actions(risk: PRRiskInput, rr: ReadinessInput) -> list[str]:
    """Deduplicated, ordered required-actions list.

    Order: standard items → PR-risk required validations → RR blockers → RR
    warnings → RR recommended actions. Items are deduped by lowercase /
    trailing-period-stripped key. No phrase rewriting (project-agnostic).
    """
    seen: set[str] = set()
    result: list[str] = []

    def add(item: str) -> None:
        s = (item or "").strip()
        if not s:
            return
        key = _action_key(s)
        if key and key not in seen:
            seen.add(key)
            result.append(s)

    for a in STANDARD_ACTIONS:
        add(a)
    for v in risk.required_validations:
        add(v)
    for b in rr.blocker_messages:
        add(b)
    for w in rr.warning_messages:
        add(w)
    for r in rr.recommended_actions:
        add(r)
    return result


def load_pr_risk(path: Path) -> PRRiskInput:
    data = json.loads(path.read_text(encoding="utf-8"))
    rec = normalize_status(data.get("merge_recommendation", ""))
    raw_conf = data.get("test_confidence")
    confidence = int(raw_conf) if raw_conf is not None else None
    return PRRiskInput(
        status=rec,
        score=float(data.get("score") or 0),
        band=str(data.get("band") or "unknown"),
        label=REC_DISPLAY.get(rec, rec),
        confidence=confidence,
        required_validations=[str(v) for v in (data.get("required_validations") or [])],
        top_risk_factors=[str(f) for f in (data.get("top_risk_factors") or [])],
    )


def load_release_readiness(
    summary_path: Path,
    report_path: Optional[Path] = None,
) -> ReadinessInput:
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    status = normalize_status(summary.get("outcome", ""))

    blocker_msgs: list[str] = []
    warning_msgs: list[str] = []
    recommended: list[str] = []
    critical_failed_titles: list[str] = []
    non_critical_failed_titles: list[str] = []
    report_enriched = False

    if report_path and report_path.exists():
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            blocker_msgs = [str(b) for b in (report.get("blockers") or [])]
            warning_msgs = [str(w) for w in (report.get("warnings") or [])]
            recommended = [str(r) for r in (report.get("recommended_actions") or [])]
            critical_failed_titles = [
                str(t) for t in (report.get("critical_failed_titles") or [])
            ]
            non_critical_failed_titles = [
                str(t) for t in (report.get("non_critical_failed_titles") or [])
            ]
            report_enriched = True
        except Exception as exc:
            print(
                f"Warning: report.json at {report_path} could not be read ({exc})",
                file=sys.stderr,
            )

    return ReadinessInput(
        status=status,
        score=float(summary.get("score") or 0),
        warnings_count=int(summary.get("warnings") or 0),
        blockers_count=int(summary.get("blockers") or 0),
        blocker_messages=blocker_msgs,
        warning_messages=warning_msgs,
        recommended_actions=recommended,
        critical_failed_titles=critical_failed_titles,
        non_critical_failed_titles=non_critical_failed_titles,
        report_enriched=report_enriched,
    )


def build_gate_json(
    risk: PRRiskInput,
    rr: ReadinessInput,
    gate_status: str,
    required_actions: list[str],
) -> dict:
    rr_conf = derive_rr_confidence(rr)
    gate_conf = classify_gate_confidence(risk.confidence, rr_conf, gate_status)
    dec_summary = gate_decision_summary(gate_status, gate_conf)

    pr_risk_section: dict = {
        "status": risk.status,
        "label": risk.label,
        "score": round(risk.score, 1),
        "band": risk.band,
        "top_risk_factors": list(risk.top_risk_factors),
    }
    if risk.confidence is not None:
        pr_risk_section["confidence"] = risk.confidence

    return {
        "version": VERSION,
        "pr_risk": pr_risk_section,
        "release_readiness": {
            "status": rr.status,
            "score": round(rr.score, 1),
            "warnings": rr.warnings_count,
            "blockers": rr.blockers_count,
            "confidence": rr_conf,
            "critical_failed_titles": list(rr.critical_failed_titles),
            "non_critical_failed_titles": list(rr.non_critical_failed_titles),
        },
        "final_gate": {
            "status": gate_status,
            "confidence": gate_conf,
            "summary": dec_summary,
            "workflow_should_fail": gate_status == "BLOCK",
        },
        "required_actions": required_actions,
        "report_enriched": rr.report_enriched,
    }


def build_gate_markdown(
    risk: PRRiskInput,
    rr: ReadinessInput,
    gate_status: str,
    required_actions: list[str],
) -> str:
    ge = STATUS_EMOJI.get(gate_status, "⚪")
    rie = STATUS_EMOJI.get(risk.status, "⚪")
    rre = STATUS_EMOJI.get(rr.status, "⚪")

    rr_label = f"{rr.status} ({rr.score:.0f}/100)"
    if rr.warnings_count or rr.blockers_count:
        rr_label += f" · {rr.warnings_count} warn · {rr.blockers_count} block"

    rr_conf = derive_rr_confidence(rr)
    gate_conf = classify_gate_confidence(risk.confidence, rr_conf, gate_status)

    actions_block = (
        "\n".join(f"- {a}" for a in required_actions)
        if required_actions
        else "_None beyond standard CI and review requirements._"
    )

    lines: list[str] = [
        "# Release Readiness PR Gate",
        "",
        "| Signal | Result |",
        "|--------|--------|",
        f"| PR Risk | {rie} {risk.label} |",
        f"| Release Readiness | {rre} {rr_label} |",
        f"| **Final Gate** | **{ge} {gate_status}** |",
        "",
        "## Decision",
        "",
        gate_decision_summary(gate_status, gate_conf),
        "",
        "## Required actions before merge",
        "",
        actions_block,
        "",
        "## Supporting detail",
        "",
        f"- PR Risk score: {risk.score:.1f} / 100 ({risk.band})",
        f"- Release Readiness score: {rr.score:.1f} / 100",
        f"- Release Readiness warnings: {rr.warnings_count}",
        f"- Release Readiness blockers: {rr.blockers_count}",
    ]
    if risk.confidence is not None:
        lines.append(f"- PR Risk test confidence: {risk.confidence} / 100")
    lines.append(f"- Release Readiness confidence: {rr_conf} / 100")
    lines.append(f"- Gate confidence: {gate_conf}")
    lines += ["", "---", GATE_FOOTER_MARKDOWN, ""]
    return "\n".join(lines)


def _partial_gate_json(
    risk: Optional[PRRiskInput],
    rr: Optional[ReadinessInput],
    errors: list[str],
) -> dict:
    return {
        "version": VERSION,
        "pr_risk": (
            {
                "status": risk.status,
                "label": risk.label,
                "score": round(risk.score, 1),
                "band": risk.band,
                "top_risk_factors": list(risk.top_risk_factors),
            }
            if risk
            else {"status": "UNKNOWN", "error": "Failed to parse PR risk input"}
        ),
        "release_readiness": (
            {
                "status": rr.status,
                "score": round(rr.score, 1),
                "warnings": rr.warnings_count,
                "blockers": rr.blockers_count,
                "confidence": derive_rr_confidence(rr),
            }
            if rr
            else {"status": "UNKNOWN", "error": "Failed to parse release readiness input"}
        ),
        "final_gate": {
            "status": "BLOCK",
            "confidence": "low",
            "summary": "Gate inputs could not be parsed — treated as BLOCK. " + " | ".join(errors),
            "workflow_should_fail": True,
        },
        "required_actions": list(STANDARD_ACTIONS),
        "report_enriched": False,
    }


def _partial_gate_md(errors: list[str]) -> str:
    lines = [
        "# Release Readiness PR Gate",
        "",
        "**🔴 BLOCK — Gate inputs could not be parsed.**",
        "",
        "The following errors occurred while loading gate inputs:",
        "",
    ]
    for e in errors:
        lines.append(f"- {e}")
    lines += [
        "",
        "_Ensure `artifacts/pr-risk.json` and `artifacts/release-readiness.json` were generated._",
        "",
    ]
    return "\n".join(lines)


def _append_step_summary(gate_json: dict) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    gate = gate_json.get("final_gate", {})
    status = gate.get("status", "UNKNOWN")
    emoji = STATUS_EMOJI.get(status, "⚪")
    risk = gate_json.get("pr_risk", {})
    rr = gate_json.get("release_readiness", {})
    rr_emoji = STATUS_EMOJI.get(str(rr.get("status", "")), "⚪")

    lines = [
        "## Release Readiness PR Gate",
        "",
        f"{emoji} **Final gate: {status}** &nbsp;·&nbsp; {gate.get('summary', '')}",
        "",
        "| PR Risk | Release Readiness |",
        "|---------|-------------------|",
        f"| {risk.get('label', '?')} | {rr_emoji} {rr.get('status', '?')} ({rr.get('score', '?')}/100) |",
        "",
        GATE_FOOTER_MARKDOWN,
        "",
    ]
    with open(summary_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def run(
    pr_risk_path: Path,
    readiness_summary_path: Path,
    readiness_report_path: Optional[Path],
    output_dir: Path,
    step_summary: bool = False,
) -> tuple[dict, int]:
    """Compute gate, write pr-gate-summary.{json,md}. Returns (gate_json, exit_code)."""
    errors: list[str] = []
    risk: Optional[PRRiskInput] = None
    rr: Optional[ReadinessInput] = None

    try:
        risk = load_pr_risk(pr_risk_path)
    except Exception as exc:
        errors.append(f"PR risk ({pr_risk_path.name}): {exc}")

    try:
        rr = load_release_readiness(readiness_summary_path, readiness_report_path)
    except Exception as exc:
        errors.append(f"Release readiness ({readiness_summary_path.name}): {exc}")

    output_dir.mkdir(parents=True, exist_ok=True)

    if errors:
        gate_json = _partial_gate_json(risk, rr, errors)
        gate_md = _partial_gate_md(errors)
        (output_dir / "pr-gate-summary.json").write_text(
            json.dumps(gate_json, indent=2, sort_keys=True), encoding="utf-8"
        )
        (output_dir / "pr-gate-summary.md").write_text(gate_md, encoding="utf-8")
        if step_summary:
            _append_step_summary(gate_json)
        return gate_json, 1

    assert risk is not None and rr is not None

    gate_status = compute_gate_status(rr.status, risk.status)
    required_actions = build_required_actions(risk, rr)
    gate_json = build_gate_json(risk, rr, gate_status, required_actions)
    gate_md = build_gate_markdown(risk, rr, gate_status, required_actions)

    (output_dir / "pr-gate-summary.json").write_text(
        json.dumps(gate_json, indent=2, sort_keys=True), encoding="utf-8"
    )
    (output_dir / "pr-gate-summary.md").write_text(gate_md, encoding="utf-8")

    if step_summary:
        _append_step_summary(gate_json)

    return gate_json, 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Combine pr-risk.json + release-readiness.json into a unified PR gate summary.",
    )
    parser.add_argument(
        "--pr-risk-json", default="artifacts/pr-risk.json",
        help="Path to artifacts/pr-risk.json (default: %(default)s)",
    )
    parser.add_argument(
        "--readiness-json", default="artifacts/release-readiness.json",
        help="Path to artifacts/release-readiness.json (default: %(default)s)",
    )
    parser.add_argument(
        "--readiness-report-json",
        default="artifacts/release-readiness/report.json",
        help="Optional full release-readiness report.json — enriches required_actions (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir", default="artifacts",
        help="Directory for pr-gate-summary.json / .md (default: %(default)s)",
    )
    parser.add_argument(
        "--step-summary", action="store_true",
        help="Append a compact gate section to $GITHUB_STEP_SUMMARY",
    )
    args = parser.parse_args(argv)

    gate_json, exit_code = run(
        pr_risk_path=Path(args.pr_risk_json),
        readiness_summary_path=Path(args.readiness_json),
        readiness_report_path=Path(args.readiness_report_json),
        output_dir=Path(args.output_dir),
        step_summary=args.step_summary,
    )

    status = gate_json.get("final_gate", {}).get("status", "UNKNOWN")
    print(f"{STATUS_EMOJI.get(status, '⚪')} PR Gate: {status}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
