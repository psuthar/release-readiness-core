"""Proximity analyzer (port of internal/prrisk/context/proximity.go).

Scores whether tests in the diff sit near the production code they exercise,
and classifies behavioral-coverage depth vs sensitive domains.
"""

from __future__ import annotations

import os.path
from typing import Dict, List

from release_readiness_core.pr_risk.context.input import Input
from release_readiness_core.pr_risk.context.types import ProximityInsight


_SENSITIVE_DOMAINS = ("auth", "rag", "processing", "migrations", "api", "database")


def _to_slash(p: str) -> str:
    return p.replace("\\", "/").strip()


def has_sensitive_production_domains(h: Dict[str, int]) -> bool:
    if h is None:
        return False
    return any(h.get(k, 0) > 0 for k in _SENSITIVE_DOMAINS)


def overlaps_sensitive_test_domains(
    test_hits: Dict[str, int], domain_hits: Dict[str, int]
) -> bool:
    if test_hits is None or domain_hits is None:
        return False
    return any(
        domain_hits.get(k, 0) > 0 and test_hits.get(k, 0) > 0
        for k in _SENSITIVE_DOMAINS
    )


def has_nearby_test_in_diff(code_path: str, test_paths: List[str]) -> bool:
    code_path = _to_slash(code_path)
    code_dir = os.path.dirname(code_path).replace("\\", "/")

    for t in test_paths:
        t = _to_slash(t)
        if t == "":
            continue
        test_dir = os.path.dirname(t).replace("\\", "/")
        if test_dir == code_dir:
            return True
        parent_of_dir = os.path.dirname(code_dir).replace("\\", "/")
        parent_of_test_dir = os.path.dirname(test_dir).replace("\\", "/")
        if test_dir == parent_of_dir or code_dir == parent_of_test_dir:
            return True
        if "web/tests/e2e/" in t and code_path.startswith("web/"):
            return True
    return False


def behavioral_coverage_note(depth: str) -> str:
    if depth == "adequate":
        return (
            "Behavioral depth: adequate for this diff’s risk class "
            "(E2E/domain overlap with sensitive areas, or non-sensitive production changes)."
        )
    if depth == "shallow":
        return (
            "Behavioral depth: unit-level overlap with sensitive domains but no matching "
            "E2E evidence in this diff — consider deeper tests where applicable."
        )
    return ""


def compute_behavioral_coverage(in_: Input, structural_mode: str) -> str:
    if structural_mode == "n_a" or structural_mode == "distant":
        return "unknown"
    if not has_sensitive_production_domains(in_.domain_hits):
        return "adequate"
    if overlaps_sensitive_test_domains(in_.test_e2e_domain_hits, in_.domain_hits):
        return "adequate"
    if overlaps_sensitive_test_domains(in_.test_unit_domain_hits, in_.domain_hits):
        if structural_mode == "co_located":
            return "shallow"
        return "unknown"
    return "unknown"


def analyze_proximity(in_: Input) -> ProximityInsight:
    if not in_.files or len(in_.is_test) != len(in_.files):
        return ProximityInsight(
            mode="n_a",
            structural_alignment="n_a",
            behavioral_coverage="unknown",
            detail="no files to analyze",
        )

    non_test_paths: List[str] = []
    test_paths: List[str] = []
    for i, f in enumerate(in_.files):
        if i >= len(in_.is_test):
            break
        if in_.is_test[i]:
            test_paths.append(f.path)
        else:
            non_test_paths.append(f.path)

    if not non_test_paths:
        return ProximityInsight(
            mode="n_a",
            structural_alignment="n_a",
            behavioral_coverage="unknown",
            detail="only test files in diff",
        )

    if not test_paths:
        all_untestable = len(in_.is_untestable) == len(in_.files)
        if all_untestable:
            for i in range(len(in_.files)):
                if not in_.is_test[i] and not in_.is_untestable[i]:
                    all_untestable = False
                    break
        if all_untestable:
            return ProximityInsight(
                mode="n_a",
                structural_alignment="n_a",
                behavioral_coverage="unknown",
                detail=(
                    "Diff contains only config/tooling files (YAML, shell, docs…); "
                    "test proximity is not applicable."
                ),
            )
        return ProximityInsight(
            mode="distant",
            structural_alignment="distant",
            behavioral_coverage="unknown",
            non_test_files=len(non_test_paths),
            with_nearby_test_in_diff=0,
            ratio=0.0,
            detail=(
                "No test files in diff; proximity of tests to changed code "
                "cannot be established from this diff alone."
            ),
        )

    with_nearby = 0
    for p in non_test_paths:
        if has_nearby_test_in_diff(p, test_paths):
            with_nearby += 1

    ratio = with_nearby / len(non_test_paths)
    if ratio >= 0.75:
        mode = "co_located"
    elif ratio >= 0.35:
        mode = "partial"
    else:
        mode = "distant"

    if mode == "co_located":
        detail = (
            "Tests in this diff are mostly next to or under the same directories "
            "as changed production files."
        )
    elif mode == "partial":
        detail = (
            "Some production changes lack adjacent tests in the same diff; "
            "spot-check coverage."
        )
    else:  # distant
        detail = (
            "Many changed production files have no test file in the same directory "
            "or an obvious sibling path in this diff."
        )

    behavioral = compute_behavioral_coverage(in_, mode)
    if behavioral != "" and behavioral != "unknown":
        detail += " " + behavioral_coverage_note(behavioral)

    return ProximityInsight(
        mode=mode,
        structural_alignment=mode,
        behavioral_coverage=behavioral,
        non_test_files=len(non_test_paths),
        with_nearby_test_in_diff=with_nearby,
        ratio=ratio,
        detail=detail,
    )
