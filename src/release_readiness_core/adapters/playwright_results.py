"""
Convert Playwright JSON reporter output to ``e2e_results.json`` in the
release-readiness schema.

Console script: ``playwright-to-readiness``.

Usage:
    playwright-to-readiness --input playwright-results.json --output e2e_results.json \
        [--validation-map path/to/validation_map.yaml] \
        [--spec-extensions .ts,.js,.mjs,.e2e]

Schema produced (all extra fields in the input are ignored by the engine):
    {
      "status": "passed|failed|skipped",
      "failed_count": <int>,
      "total_count": <int>,
      "retries": <int>,
      "failures": [{"title": "...", "name": "..."}],
      "validations": {
        "<validation_key>": true|false,
        ...
      }
    }

Validation map (project-supplied, optional):
    A YAML file mapping each readiness validation key to a list of Playwright
    test file stems that provide evidence for it. Stems are filenames with
    spec extensions stripped.

    Example::

        auth_session:
          - login-flow
          - signup-flow
        checkout:
          - cart-checkout

    A validation is True iff ALL tests in the group ran and ALL passed.
    A validation key is omitted when no tests from its group ran.

    When no validation map is supplied, ``validations`` is emitted as an
    empty object — counts and failures are still reported.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable, Optional

DEFAULT_SPEC_EXTENSIONS: tuple[str, ...] = (".ts", ".js", ".mjs", ".e2e")


def _stem_for_spec(file_path: str, extensions: Iterable[str]) -> str:
    """Return the bare file stem from a path, stripping configured extensions.

    Extensions are stripped iteratively so chained suffixes like ``.e2e.ts``
    collapse to ``foo`` when both ``.ts`` and ``.e2e`` are configured.
    """
    p = Path(file_path.replace("\\", "/"))
    name = p.name
    changed = True
    while changed:
        changed = False
        for ext in extensions:
            if ext and name.endswith(ext):
                name = name[: -len(ext)]
                changed = True
    return name


def _file_belongs_to_group(file_path: str, stems: list[str], extensions: Iterable[str]) -> bool:
    return _stem_for_spec(file_path, extensions) in stems


def _collect_specs(suite_node: dict) -> list[dict]:
    """Recursively walk the Playwright JSON suite tree and collect leaf spec nodes."""
    specs: list[dict] = []
    for spec in suite_node.get("specs", []):
        if "file" not in spec:
            spec = dict(spec)
            spec["file"] = suite_node.get("file", "")
        specs.append(spec)

    for child_suite in suite_node.get("suites", []):
        if "file" not in child_suite and "file" in suite_node:
            child_suite = dict(child_suite)
            child_suite["file"] = suite_node["file"]
        specs.extend(_collect_specs(child_suite))

    return specs


def convert(
    playwright_data: dict,
    validation_map: Optional[dict[str, list[str]]] = None,
    spec_extensions: Optional[Iterable[str]] = None,
) -> dict:
    """Convert a Playwright JSON reporter payload to the readiness schema.

    Args:
        playwright_data: Parsed JSON from ``playwright test --reporter=json``.
        validation_map: Optional mapping of validation key → list of test
            file stems. When omitted, ``validations`` is an empty object.
        spec_extensions: Optional iterable of spec extensions stripped when
            computing test file stems. Defaults to ``(".ts", ".js", ".mjs",
            ".e2e")``.
    """

    extensions: tuple[str, ...] = (
        tuple(spec_extensions) if spec_extensions is not None else DEFAULT_SPEC_EXTENSIONS
    )
    val_map: dict[str, list[str]] = validation_map or {}

    stats: dict = playwright_data.get("stats", {})
    top_suites: list[dict] = playwright_data.get("suites", [])

    total_expected = int(stats.get("expected", 0))
    total_unexpected = int(stats.get("unexpected", 0))
    total_skipped = int(stats.get("skipped", 0))
    total_flaky = int(stats.get("flaky", 0))
    total_count = total_expected + total_unexpected + total_skipped + total_flaky

    all_specs: list[dict] = []
    for suite in top_suites:
        all_specs.extend(_collect_specs(suite))

    # Deduplicate retried specs: keep failing variant if any.
    seen: dict[tuple[str, str], dict] = {}
    for spec in all_specs:
        file_path = spec.get("file", "")
        title = spec.get("title", "")
        key = (file_path, title)
        if key not in seen:
            seen[key] = spec
        else:
            if not spec.get("ok", True):
                seen[key] = spec

    unique_specs = list(seen.values())

    retry_count = 0
    for spec in unique_specs:
        for t in spec.get("tests", []):
            if len(t.get("results", [])) > 1:
                retry_count += 1

    if total_count == 0 and unique_specs:
        total_count = len(unique_specs)

    failures: list[dict] = []
    for spec in unique_specs:
        if not spec.get("ok", True):
            title = spec.get("title", "")
            failures.append({"title": title, "name": title})

    failed_count = len(failures)
    if failed_count == 0 and total_unexpected > 0:
        failed_count = total_unexpected

    if total_count == 0 and not unique_specs:
        status = "skipped"
    elif failed_count > 0:
        status = "failed"
    else:
        status = "passed"

    validations: dict[str, bool] = {}
    for val_key, stems in val_map.items():
        group_specs = [
            s for s in unique_specs if _file_belongs_to_group(s.get("file", ""), stems, extensions)
        ]
        if not group_specs:
            continue
        group_failed = any(not s.get("ok", True) for s in group_specs)
        validations[val_key] = not group_failed

    return {
        "status": status,
        "failed_count": failed_count,
        "total_count": total_count,
        "retries": retry_count,
        "failures": failures,
        "validations": validations,
    }


def _load_validation_map(path: Path) -> dict[str, list[str]]:
    import yaml  # local import keeps yaml optional at convert() call sites

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(
            f"validation map at {path} must be a mapping of validation key → list of stems"
        )
    result: dict[str, list[str]] = {}
    for key, stems in raw.items():
        if not isinstance(stems, list) or not all(isinstance(s, str) for s in stems):
            raise ValueError(
                f"validation map entry '{key}' must be a list of strings (file stems)"
            )
        result[str(key)] = list(stems)
    return result


def _parse_spec_extensions(value: str) -> tuple[str, ...]:
    parts = [p.strip() for p in value.split(",") if p.strip()]
    return tuple(p if p.startswith(".") else f".{p}" for p in parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Playwright JSON reporter output to e2e_results.json (readiness schema)."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to playwright-results.json (Playwright --reporter=json output).",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write e2e_results.json.",
    )
    parser.add_argument(
        "--validation-map",
        default=None,
        help=(
            "Optional path to a YAML file mapping validation keys to lists of "
            "Playwright test file stems. Without it, the 'validations' object "
            "in the output is empty."
        ),
    )
    parser.add_argument(
        "--spec-extensions",
        default=None,
        help=(
            "Comma-separated list of spec extensions stripped when computing file "
            f"stems (default: {','.join(DEFAULT_SPEC_EXTENSIONS)})."
        ),
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    validation_map: Optional[dict[str, list[str]]] = None
    if args.validation_map:
        map_path = Path(args.validation_map)
        if not map_path.exists():
            print(f"ERROR: validation map not found: {map_path}", file=sys.stderr)
            sys.exit(2)
        validation_map = _load_validation_map(map_path)

    spec_extensions: Optional[tuple[str, ...]] = None
    if args.spec_extensions is not None:
        spec_extensions = _parse_spec_extensions(args.spec_extensions)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                {
                    "status": "skipped",
                    "failed_count": 0,
                    "total_count": 0,
                    "retries": 0,
                    "failures": [],
                    "validations": {},
                    "note": f"playwright-results.json not found at {input_path}",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        sys.exit(0)

    raw = input_path.read_text(encoding="utf-8")
    if not raw.strip():
        print(f"WARNING: {input_path} is empty — treating as no tests ran", file=sys.stderr)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                {
                    "status": "skipped",
                    "failed_count": 0,
                    "total_count": 0,
                    "retries": 0,
                    "failures": [],
                    "validations": {},
                    "note": "playwright-results.json was empty; no E2E tests ran",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        sys.exit(0)

    try:
        playwright_data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: failed to parse {input_path}: {exc}", file=sys.stderr)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                {
                    "status": "failed",
                    "failed_count": 1,
                    "total_count": 0,
                    "retries": 0,
                    "failures": [
                        {"title": "playwright_json_parse_error", "name": "playwright_json_parse_error"}
                    ],
                    "validations": {},
                    "note": f"JSON parse error: {exc}",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        sys.exit(1)

    result = convert(
        playwright_data,
        validation_map=validation_map,
        spec_extensions=spec_extensions,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(
        f"e2e_results.json written: status={result['status']}, "
        f"passed={result['total_count'] - result['failed_count']}/{result['total_count']}, "
        f"retries={result['retries']}, "
        f"validations={result['validations']}"
    )


if __name__ == "__main__":
    main()
