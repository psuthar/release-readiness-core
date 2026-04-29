"""
Convert an LCOV ``info`` coverage report to ``coverage.json`` in the
readiness schema.

Console script: ``lcov-to-readiness``.

LCOV info is emitted by ``c8``, ``istanbul``, ``coverage.py --lcov``,
``gocover --lcov``, and most JS / Python / Go coverage tooling — a
single adapter covers the long tail.

Output shape::

    {
      "line_percent": <float, 0..100>,
      "baseline_percent": <float | null>
    }

Usage::

    lcov-to-readiness \\
        --input coverage/lcov.info \\
        --output coverage.json \\
        [--baseline-percent 85.0]

LCOV format primer (only the lines this adapter cares about)::

    SF:<source file>
    LF:<lines found>
    LH:<lines hit>
    end_of_record

Multiple source files appear as repeated SF/LF/LH/end_of_record blocks;
we sum LF and LH across the entire report and compute the percentage.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional


def parse_lcov(text: str) -> tuple[int, int]:
    """Return (lines_found, lines_hit) summed across all source files."""
    lines_found = 0
    lines_hit = 0
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("LF:"):
            try:
                lines_found += int(line[3:].strip())
            except ValueError:
                continue
        elif line.startswith("LH:"):
            try:
                lines_hit += int(line[3:].strip())
            except ValueError:
                continue
    return lines_found, lines_hit


def line_percent(text: str) -> float:
    """Compute line coverage percent (0..100, two decimals).

    Returns 0.0 when LCOV reports zero lines (empty / malformed).
    """
    lines_found, lines_hit = parse_lcov(text)
    if lines_found == 0:
        return 0.0
    return round((lines_hit / lines_found) * 100.0, 2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert LCOV info coverage to coverage.json (readiness schema)."
    )
    parser.add_argument("--input", required=True, help="Path to lcov.info file.")
    parser.add_argument("--output", required=True, help="Path to write coverage.json.")
    parser.add_argument(
        "--baseline-percent",
        type=float,
        default=None,
        help=(
            "Optional baseline coverage percent. The engine treats line_percent "
            "below baseline_percent as a coverage regression warning."
        ),
    )
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"WARNING: lcov input not found: {input_path}", file=sys.stderr)
        output_path.write_text(
            json.dumps(
                {
                    "line_percent": 0.0,
                    "baseline_percent": args.baseline_percent,
                    "note": f"lcov input not found at {input_path}",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return 0

    text = input_path.read_text(encoding="utf-8", errors="replace")
    pct = line_percent(text)

    payload: dict = {"line_percent": pct, "baseline_percent": args.baseline_percent}
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(
        f"lcov -> coverage: line_percent={pct} baseline_percent={args.baseline_percent}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
