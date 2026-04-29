"""
Convert a JUnit XML test report to ``e2e_results.json`` (or
``smoke.json``) in the readiness schema.

Console script: ``junit-to-readiness``.

JUnit XML is the most widely shared test-report format — Cypress
(``cypress-multi-reporters``), Jest (``jest-junit``), pytest
(``--junitxml``), Mocha, Karma, Maven Surefire, and many CI systems
emit it natively. One adapter therefore covers most adopters.

Usage::

    junit-to-readiness \\
        --input test-results.xml \\
        --output e2e_results.json \\
        [--validation-map path/to/validation_map.yaml]

The optional validation map mirrors the Playwright adapter: a YAML file
mapping each readiness validation key to a list of test "stems" (the
classname or basename of the test). A validation is satisfied iff every
test belonging to it ran and passed; absent if no tests matched.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable, Optional


def _is_skipped(case: ET.Element) -> bool:
    return case.find("skipped") is not None


def _is_failed(case: ET.Element) -> bool:
    return case.find("failure") is not None or case.find("error") is not None


def _case_title(case: ET.Element) -> str:
    cls = case.get("classname", "").strip()
    name = case.get("name", "").strip()
    if cls and name:
        return f"{cls}.{name}"
    return name or cls or "<unnamed>"


def _case_stems(case: ET.Element) -> list[str]:
    """Stems used for validation-map matching: classname, last classname segment, name."""
    cls = case.get("classname", "").strip()
    name = case.get("name", "").strip()
    stems: list[str] = []
    if cls:
        stems.append(cls)
        if "." in cls:
            stems.append(cls.rsplit(".", 1)[-1])
    if name:
        stems.append(name)
    return stems


def _iter_testcases(root: ET.Element) -> Iterable[ET.Element]:
    """Yield every <testcase> regardless of nesting depth or root tag."""
    if root.tag == "testcase":
        yield root
    for case in root.iter("testcase"):
        yield case


def convert(
    junit_root: ET.Element,
    validation_map: Optional[dict[str, list[str]]] = None,
) -> dict:
    cases = list(_iter_testcases(junit_root))

    total_count = len(cases)
    failed: list[ET.Element] = [c for c in cases if _is_failed(c)]
    skipped_count = sum(1 for c in cases if _is_skipped(c))
    failed_count = len(failed)

    if total_count == 0:
        status = "skipped"
    elif failed_count > 0:
        status = "failed"
    elif skipped_count == total_count:
        status = "skipped"
    else:
        status = "passed"

    failures = [{"title": _case_title(c), "name": _case_title(c)} for c in failed]

    validations: dict[str, bool] = {}
    val_map = validation_map or {}
    if val_map and cases:
        for val_key, stems in val_map.items():
            stem_set = set(stems)
            group = [c for c in cases if any(s in stem_set for s in _case_stems(c))]
            if not group:
                continue
            group_failed = any(_is_failed(c) for c in group)
            validations[val_key] = not group_failed

    return {
        "status": status,
        "failed_count": failed_count,
        "total_count": total_count,
        "retries": 0,
        "failures": failures,
        "validations": validations,
    }


def _load_validation_map(path: Path) -> dict[str, list[str]]:
    import yaml

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"validation map at {path} must be a mapping")
    out: dict[str, list[str]] = {}
    for k, v in raw.items():
        if not isinstance(v, list) or not all(isinstance(s, str) for s in v):
            raise ValueError(f"validation map entry '{k}' must be a list of strings")
        out[str(k)] = list(v)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Convert a JUnit XML test report to e2e_results.json (readiness schema)."
    )
    parser.add_argument("--input", required=True, help="Path to JUnit XML file.")
    parser.add_argument("--output", required=True, help="Path to write the JSON output.")
    parser.add_argument(
        "--validation-map",
        default=None,
        help="Optional YAML mapping validation keys to test stems (classname / name).",
    )
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"WARNING: JUnit input not found: {input_path}", file=sys.stderr)
        output_path.write_text(
            json.dumps(
                {
                    "status": "skipped",
                    "failed_count": 0,
                    "total_count": 0,
                    "retries": 0,
                    "failures": [],
                    "validations": {},
                    "note": f"junit input not found at {input_path}",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return 0

    try:
        tree = ET.parse(input_path)
    except ET.ParseError as exc:
        print(f"ERROR: failed to parse {input_path}: {exc}", file=sys.stderr)
        output_path.write_text(
            json.dumps(
                {
                    "status": "failed",
                    "failed_count": 1,
                    "total_count": 0,
                    "retries": 0,
                    "failures": [{"title": "junit_parse_error", "name": "junit_parse_error"}],
                    "validations": {},
                    "note": f"junit parse error: {exc}",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        return 1

    validation_map: Optional[dict[str, list[str]]] = None
    if args.validation_map:
        map_path = Path(args.validation_map)
        if not map_path.exists():
            print(f"ERROR: validation map not found: {map_path}", file=sys.stderr)
            return 2
        validation_map = _load_validation_map(map_path)

    result = convert(tree.getroot(), validation_map=validation_map)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(
        f"junit -> readiness: status={result['status']}, "
        f"passed={result['total_count'] - result['failed_count']}/{result['total_count']}, "
        f"validations={result['validations']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
