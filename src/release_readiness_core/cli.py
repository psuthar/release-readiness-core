"""CLI entrypoint for release-readiness-core."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Sequence

from .engine import ValidationResult, evaluate_release_readiness
from .report import render_markdown_report
from .runtime_config import (
    parse_runtime_config,
    resolve_runtime_defaults,
    summarize_high_priority_hits,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="release-readiness",
        description="Evaluate deterministic PASS/WARN/BLOCK readiness from validation results.",
    )
    parser.add_argument(
        "--input-json",
        default="[]",
        help="JSON array of validation objects with fields: key, status, detail(optional).",
    )
    parser.add_argument(
        "--config-json",
        default="{}",
        help="JSON object with optional fields: report_title, pr_risk.high_priority_evidence_ids.",
    )
    parser.add_argument(
        "--pr-risk-json",
        default="{}",
        help="Optional JSON object for PR-risk payload, including evidence entries.",
    )
    parser.add_argument(
        "--output-format",
        default="json",
        choices=["json", "markdown"],
        help="Output format for report rendering.",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory; falls back to config paths.output_dir_default.",
    )
    parser.add_argument(
        "--base-ref",
        default=None,
        help="Optional base ref; falls back to env var configured in config env.base_ref_env_var.",
    )
    parser.add_argument(
        "--enforcement-mode",
        default=None,
        help="Optional enforcement mode; falls back to env var configured in config env.enforcement_mode_env_var.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    raw_items = json.loads(args.input_json)
    validations = [
        ValidationResult(
            key=item["key"],
            status=item["status"],
            detail=item.get("detail", ""),
        )
        for item in raw_items
    ]
    report = evaluate_release_readiness(validations)
    config = parse_runtime_config(json.loads(args.config_json))
    defaults = resolve_runtime_defaults(config)
    _base_ref = args.base_ref or defaults["base_ref"]
    _enforcement_mode = args.enforcement_mode or defaults["enforcement_mode"]
    _output_dir = args.output_dir or defaults["output_dir"]
    pr_risk_payload = json.loads(args.pr_risk_json)
    high_priority_hits = (
        summarize_high_priority_hits(pr_risk_payload, config.high_priority_evidence_ids)
        if isinstance(pr_risk_payload, dict)
        else {}
    )

    if args.output_format == "markdown":
        print(render_markdown_report(config.report_title, report, high_priority_hits))
    else:
        print(json.dumps(asdict(report), indent=2))
    return 0

