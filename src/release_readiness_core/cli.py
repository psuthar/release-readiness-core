"""CLI entrypoint for release-readiness-core."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Sequence

from .engine import ValidationResult, evaluate_release_readiness


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
    print(json.dumps(asdict(report), indent=2))
    return 0

