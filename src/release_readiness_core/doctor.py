"""``release-readiness-doctor`` — pre-flight verifier.

Console script: ``release-readiness-doctor``.

Doctor exists so adopters catch misconfiguration **before** they wire
release-readiness into a CI gate that fails for the wrong reasons.
A typical first-time adoption hits one of these mistakes:

- A typo in ``config.yaml`` that the engine silently ignores
  (mostly addressed by SCRUM-209 schema validation, but doctor surfaces
  it explicitly with line-style output).
- An evidence JSON whose shape doesn't match what the engine expects.
- ``failed_count > 0`` but ``failures: []`` — engine treats that as a
  critical failure with no titles, leaving reviewers guessing.
- Risk categories declared in ``risk_from_paths`` that map to a
  validation key no project artifact ever satisfies.

Doctor runs every check that doesn't require a real CI run, prints a
report, and exits non-zero on any ERROR.

Usage::

    release-readiness-doctor                                   # run from project root
    release-readiness-doctor --config ops/release-readiness/config.yaml
    release-readiness-doctor --config <path> \\
        --smoke-results evidence/smoke.json \\
        --e2e-results evidence/e2e.json \\
        --coverage evidence/coverage.json \\
        --prod-health evidence/prod_health.json
"""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional


SEVERITY_ORDER = ("INFO", "OK", "WARN", "ERROR")


@dataclass
class Finding:
    severity: str  # OK | INFO | WARN | ERROR
    message: str

    def render(self) -> str:
        return f"[{self.severity:<5}] {self.message}"


def _check_install() -> list[Finding]:
    out: list[Finding] = []
    try:
        importlib.import_module("release_readiness_core.readiness_engine")
        importlib.import_module("release_readiness_core.readiness_evaluate")
    except ImportError as exc:
        out.append(Finding("ERROR", f"release-readiness-core import failed: {exc}"))
        return out
    out.append(Finding("OK", "release-readiness-core importable"))

    if shutil.which("git"):
        out.append(Finding("OK", "git available (required for change-detection)"))
    else:
        out.append(
            Finding(
                "WARN",
                "git not found on PATH — you'll need --empty-diff for every run",
            )
        )
    return out


def _check_config(config_path: Optional[Path]) -> tuple[list[Finding], Optional[dict[str, Any]]]:
    """Validate the config and return (findings, loaded_config_or_None)."""
    out: list[Finding] = []
    if config_path is None:
        out.append(Finding("INFO", "no --config supplied; skipping config checks"))
        return out, None
    if not config_path.exists():
        out.append(Finding("ERROR", f"config not found: {config_path}"))
        return out, None

    from .readiness_io import ConfigSchemaError, load_yaml_config

    try:
        cfg = load_yaml_config(config_path)
    except ConfigSchemaError as exc:
        out.append(Finding("ERROR", f"config schema error in {config_path}:\n  {exc}"))
        return out, None
    except (ValueError, OSError) as exc:
        out.append(Finding("ERROR", f"config could not be loaded: {exc}"))
        return out, None

    out.append(Finding("OK", f"config loaded and validated: {config_path}"))

    declared = (cfg.get("validations") or {})
    if declared:
        out.append(Finding("OK", f"config declares {len(declared)} validation key(s)"))
    else:
        out.append(
            Finding(
                "WARN",
                "config has no `validations:` registry — risk-driven required validations "
                "will only show as raw keys in the report",
            )
        )

    rfp = cfg.get("risk_from_paths") or []
    rcv = cfg.get("risk_category_to_required_validation") or {}
    declared_categories: set[str] = set()
    for rule in rfp:
        if isinstance(rule, dict):
            for c in rule.get("categories", []) or []:
                declared_categories.add(c)
    if declared_categories:
        unmapped = [c for c in sorted(declared_categories) if c not in rcv and c not in declared]
        if unmapped:
            out.append(
                Finding(
                    "WARN",
                    "risk categories without an explicit mapping or matching validation key "
                    "(identity fallback applies): " + ", ".join(unmapped),
                )
            )

    return out, cfg


# ---- evidence shape checks --------------------------------------------------


def _check_smoke(smoke_path: Optional[Path]) -> list[Finding]:
    out: list[Finding] = []
    if smoke_path is None:
        out.append(Finding("INFO", "no --smoke-results supplied; engine will warn at run time"))
        return out
    return _check_file_shape(
        smoke_path,
        kind="smoke",
        required_top_level={"status"},
        warn_top_level=set(),
        check_consistency=_smoke_consistency,
    )


def _check_e2e(e2e_path: Optional[Path]) -> list[Finding]:
    out: list[Finding] = []
    if e2e_path is None:
        out.append(Finding("INFO", "no --e2e-results supplied; engine will warn at run time"))
        return out
    return _check_file_shape(
        e2e_path,
        kind="e2e",
        required_top_level={"status"},
        warn_top_level=set(),
        check_consistency=_e2e_consistency,
    )


def _check_coverage(coverage_path: Optional[Path]) -> list[Finding]:
    out: list[Finding] = []
    if coverage_path is None:
        out.append(Finding("INFO", "no --coverage supplied; engine will warn at run time"))
        return out
    return _check_file_shape(
        coverage_path,
        kind="coverage",
        required_top_level=set(),  # line_percent is documented but not strictly required
        warn_top_level=set(),
        check_consistency=_coverage_consistency,
    )


def _check_prod_health(prod_health_path: Optional[Path], cfg: Optional[dict[str, Any]]) -> list[Finding]:
    out: list[Finding] = []
    if prod_health_path is None:
        if cfg and "prod_health" in (cfg.get("optional_artifacts") or []):
            out.append(
                Finding(
                    "INFO",
                    "no --prod-health supplied, but `optional_artifacts: [prod_health]` is set — fine",
                )
            )
        else:
            out.append(
                Finding(
                    "INFO",
                    "no --prod-health supplied; engine will warn (declare in optional_artifacts to silence)",
                )
            )
        return out
    return _check_file_shape(
        prod_health_path,
        kind="prod_health",
        required_top_level=set(),
        warn_top_level=set(),
        check_consistency=lambda data: [],
    )


def _check_file_shape(
    path: Path,
    *,
    kind: str,
    required_top_level: set[str],
    warn_top_level: set[str],
    check_consistency,
) -> list[Finding]:
    out: list[Finding] = []
    if not path.exists():
        out.append(Finding("ERROR", f"{kind}: file not found at {path}"))
        return out
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        out.append(Finding("ERROR", f"{kind}: {path} is not valid JSON: {exc}"))
        return out
    if not isinstance(data, dict):
        out.append(Finding("ERROR", f"{kind}: {path} root must be an object, got {type(data).__name__}"))
        return out

    missing = sorted(required_top_level - set(data.keys()))
    if missing:
        out.append(Finding("ERROR", f"{kind}: {path} missing required field(s): {', '.join(missing)}"))
        return out

    out.append(Finding("OK", f"{kind}: {path} parses and has required top-level fields"))
    out.extend(check_consistency(data))
    return out


def _smoke_consistency(data: dict[str, Any]) -> list[Finding]:
    out: list[Finding] = []
    status = str(data.get("status", "")).lower()
    failed_count = int(data.get("failed_count", 0) or 0)
    if status in ("passed", "pass", "success") and failed_count > 0:
        out.append(
            Finding(
                "WARN",
                f"smoke: status='{status}' but failed_count={failed_count} — engine will block on smoke_failed",
            )
        )
    if "validations" in data and not isinstance(data["validations"], dict):
        out.append(Finding("ERROR", "smoke: 'validations' must be an object of {key: bool}"))
    return out


def _e2e_consistency(data: dict[str, Any]) -> list[Finding]:
    out: list[Finding] = []
    status = str(data.get("status", "")).lower()
    failed_count = int(data.get("failed_count", 0) or 0)
    failures = data.get("failures", [])

    if status == "skipped":
        out.append(
            Finding(
                "WARN",
                "e2e: status='skipped' — engine will warn 'E2E was skipped in CI (no inference from E2E)'",
            )
        )
    if failed_count > 0 and (not isinstance(failures, list) or len(failures) == 0):
        out.append(
            Finding(
                "WARN",
                f"e2e: failed_count={failed_count} but 'failures' is empty — "
                "engine emits 'e2e_unlisted_failures' as a critical blocker with no spec titles",
            )
        )
    if "validations" in data and not isinstance(data["validations"], dict):
        out.append(Finding("ERROR", "e2e: 'validations' must be an object of {key: bool}"))
    return out


def _coverage_consistency(data: dict[str, Any]) -> list[Finding]:
    out: list[Finding] = []
    line = data.get("line_percent")
    base = data.get("baseline_percent")
    if line is None:
        out.append(Finding("WARN", "coverage: missing 'line_percent' — coverage section will be inert"))
    else:
        try:
            line_f = float(line)
            if line_f < 0 or line_f > 100:
                out.append(
                    Finding("WARN", f"coverage: line_percent={line_f} is outside 0..100 — likely a unit error")
                )
        except (TypeError, ValueError):
            out.append(Finding("ERROR", f"coverage: line_percent must be a number, got {type(line).__name__}"))
    if base is not None and line is not None:
        try:
            if float(line) < float(base):
                out.append(
                    Finding(
                        "INFO",
                        f"coverage: line_percent({line}) < baseline_percent({base}) — engine will warn coverage_regression",
                    )
                )
        except (TypeError, ValueError):
            out.append(Finding("ERROR", "coverage: baseline_percent must be a number or null"))
    return out


# ---- runner / main ----------------------------------------------------------


def run(
    *,
    config_path: Optional[Path] = None,
    smoke_path: Optional[Path] = None,
    e2e_path: Optional[Path] = None,
    coverage_path: Optional[Path] = None,
    prod_health_path: Optional[Path] = None,
) -> list[Finding]:
    findings: list[Finding] = []
    findings.extend(_check_install())
    cfg_findings, cfg = _check_config(config_path)
    findings.extend(cfg_findings)
    findings.extend(_check_smoke(smoke_path))
    findings.extend(_check_e2e(e2e_path))
    findings.extend(_check_coverage(coverage_path))
    findings.extend(_check_prod_health(prod_health_path, cfg))
    return findings


def _summarize(findings: Iterable[Finding]) -> dict[str, int]:
    counts = {sev: 0 for sev in SEVERITY_ORDER}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    return counts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pre-flight verifier for release-readiness-core. "
        "Checks install, config, and evidence shapes before a real run.",
    )
    parser.add_argument("--config", type=Path, default=None, help="Path to config.yaml.")
    parser.add_argument("--smoke-results", type=Path, default=None)
    parser.add_argument("--e2e-results", type=Path, default=None)
    parser.add_argument("--coverage", type=Path, default=None)
    parser.add_argument("--prod-health", type=Path, default=None)
    args = parser.parse_args(argv)

    findings = run(
        config_path=args.config,
        smoke_path=args.smoke_results,
        e2e_path=args.e2e_results,
        coverage_path=args.coverage,
        prod_health_path=args.prod_health,
    )

    print("release-readiness-doctor")
    print("=" * 60)
    for f in findings:
        print(f.render())

    counts = _summarize(findings)
    print()
    print(
        f"Summary: {counts['OK']} ok, {counts['INFO']} info, "
        f"{counts['WARN']} warn, {counts['ERROR']} error"
    )

    return 1 if counts["ERROR"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
