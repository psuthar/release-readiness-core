"""CLI: load YAML config + JSON artifacts and run :func:`~release_readiness_core.readiness_engine.compute_readiness`."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .readiness_engine import ReadinessResult, compute_readiness
from .readiness_io import (
    detect_validation_note,
    git_changed_files,
    git_commit_messages,
    load_yaml_config,
    read_json,
)
from .readiness_markdown import render_readiness_result_markdown


def evaluate(
    repo_root: Path,
    config: dict[str, Any],
    base_ref: str,
    smoke: Optional[dict[str, Any]],
    e2e: Optional[dict[str, Any]],
    coverage: Optional[dict[str, Any]],
    prod_health: Optional[dict[str, Any]],
    migration_validated_cli: bool,
    empty_diff: bool = False,
    commit_validation_note: bool = False,
    commit_validation_snippet: str = "",
    pr_risk: Optional[dict[str, Any]] = None,
) -> ReadinessResult:
    changed: list[str] = [] if empty_diff else git_changed_files(repo_root, base_ref)
    return compute_readiness(
        config=config,
        changed_files=changed,
        smoke=smoke,
        e2e=e2e,
        coverage=coverage,
        prod_health=prod_health,
        migration_validated_cli=migration_validated_cli,
        commit_validation_note=commit_validation_note,
        commit_validation_snippet=commit_validation_snippet,
        pr_risk=pr_risk,
    )


def write_machine_readiness_summary(
    repo_root: Path,
    result: ReadinessResult,
    extra: Optional[dict[str, Any]] = None,
) -> Path:
    path = repo_root / "artifacts" / "release-readiness.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "outcome": result.outcome,
        "score": round(float(result.score), 1),
        "warnings": len(result.warnings),
        "blockers": len(result.blockers),
    }
    if extra:
        data.update(extra)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def write_machine_readiness_failure(repo_root: Path, message: str) -> Path:
    path = repo_root / "artifacts" / "release-readiness.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data: dict[str, Any] = {
        "outcome": "BLOCK",
        "score": 0.0,
        "warnings": 0,
        "blockers": 1,
        "execution_failed": True,
        "error": message[:500],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Release readiness evaluate (deterministic)")
    ap.add_argument("--repo-root", type=Path, default=Path("."))
    ap.add_argument("--config", type=Path, default=Path("config.yaml"))
    ap.add_argument("--base-ref", default=os.environ.get("RELEASE_READINESS_BASE_REF", "origin/main"))
    ap.add_argument("--smoke-results", type=Path, help="JSON smoke summary (relative paths resolved under --repo-root)")
    ap.add_argument("--e2e-results", type=Path, help="JSON E2E summary (relative paths resolved under --repo-root)")
    ap.add_argument("--coverage", type=Path, help="JSON coverage summary (relative paths resolved under --repo-root)")
    ap.add_argument("--prod-health", type=Path, help="JSON prod health snapshot (relative paths resolved under --repo-root)")
    ap.add_argument("--migration-validated", action="store_true", help="CI validated migrations")
    ap.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/release-readiness"),
        help="Directory for report.json, report.md (and reads pr_risk.json when present)",
    )
    ap.add_argument(
        "--report-title",
        default=None,
        help="Optional markdown title override (default: Release readiness report)",
    )
    ap.add_argument(
        "--empty-diff",
        action="store_true",
        help=(
            "Treat changed-files list as empty (skip git diff). Use this for local "
            "or non-CI invocations and against fixtures that aren't a git checkout."
        ),
    )
    ap.add_argument(
        "--enforcement-mode",
        default=os.environ.get("READINESS_ENFORCEMENT_MODE", "block_only"),
        choices=["block_only", "warn_and_block"],
        help="Exit non-zero on WARN when set to warn_and_block.",
    )
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()

    try:
        return _main_inner(args, repo_root)
    except Exception as e:
        write_machine_readiness_failure(repo_root, str(e))
        print(f"ERROR: release readiness failed: {e}", file=sys.stderr)
        return 1


def _resolve_under_repo_root(p: Optional[Path], repo_root: Path) -> Optional[Path]:
    """SCRUM-209: relative artifact paths are interpreted under --repo-root.

    Without this, a CLI invocation from outside the project tree (e.g. with
    ``--repo-root subdir/ --smoke-results evidence/smoke.json``) silently
    failed because read_json was called with the literal path resolved from
    cwd. Now relative paths join under repo_root; absolute paths are
    untouched.
    """
    if p is None:
        return None
    return p if p.is_absolute() else repo_root / p


def _main_inner(args: argparse.Namespace, repo_root: Path) -> int:
    config_path = args.config if args.config.is_absolute() else repo_root / args.config
    config = load_yaml_config(config_path)

    smoke = read_json(_resolve_under_repo_root(args.smoke_results, repo_root)) if args.smoke_results else None
    e2e = read_json(_resolve_under_repo_root(args.e2e_results, repo_root)) if args.e2e_results else None
    coverage = read_json(_resolve_under_repo_root(args.coverage, repo_root)) if args.coverage else None
    prod_health = read_json(_resolve_under_repo_root(args.prod_health, repo_root)) if args.prod_health else None

    commit_msgs = git_commit_messages(repo_root, args.base_ref)
    commit_note_found, commit_note_snippet = detect_validation_note(commit_msgs)

    out_dir = args.output_dir if args.output_dir.is_absolute() else repo_root / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    pr_risk_path = out_dir / "pr_risk.json"
    pr_risk_data = read_json(pr_risk_path)

    result = evaluate(
        repo_root,
        config,
        args.base_ref,
        smoke,
        e2e,
        coverage,
        prod_health,
        args.migration_validated,
        empty_diff=args.empty_diff,
        commit_validation_note=commit_note_found,
        commit_validation_snippet=commit_note_snippet,
        pr_risk=pr_risk_data,
    )

    payload = asdict(result)
    payload["config_path"] = str(config_path)
    payload["base_ref"] = args.base_ref
    payload["timestamp_utc"] = datetime.now(timezone.utc).isoformat()

    pr_risk = pr_risk_data
    if pr_risk and isinstance(pr_risk, dict) and "_parse_error" not in pr_risk:
        enforcement = pr_risk.get("enforcement") or {}
        evidence_summary = enforcement.get("evidence_summary") or {}
        payload["pr_risk"] = {
            "version": pr_risk.get("version"),
            "version_minor": pr_risk.get("version_minor"),
            "report_version": pr_risk.get("report_version"),
            "risk_score": pr_risk.get("risk_score"),
            "risk_band": pr_risk.get("risk_band"),
            "enforcement": enforcement,
            "evidence_summary": evidence_summary,
        }

    override_note = f", overrides={len(result.outcome_overrides)}" if result.outcome_overrides else ""
    payload["deterministic_summary"] = (
        f"{result.outcome}: score={result.score:.1f}, "
        f"blockers={len(result.blockers)}, warnings={len(result.warnings)}{override_note}"
    )

    report_json = out_dir / "report.json"
    with open(report_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    summary_path = write_machine_readiness_summary(repo_root, result)
    print(f"Wrote {summary_path}", file=sys.stderr)

    md = render_readiness_result_markdown(
        result,
        config.get("version"),
        title=args.report_title,
    )
    report_md = out_dir / "report.md"
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(md)

    print(md)
    print(f"\nWrote {report_json}, {summary_path} and {report_md}", file=sys.stderr)
    print(f"Enforcement mode: {args.enforcement_mode}", file=sys.stderr)

    if result.outcome == "BLOCK":
        print("Outcome BLOCK — failing.", file=sys.stderr)
        return 1
    if result.outcome == "WARN" and args.enforcement_mode == "warn_and_block":
        print("Outcome WARN — failing (enforcement_mode=warn_and_block).", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
