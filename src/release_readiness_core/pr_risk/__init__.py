"""Deterministic PR risk scorer driven by git diff signals.

Computes a 0-100 risk score, a band (low / medium / high / critical), a
merge recommendation (pass / warn / block), and an explainable factor /
reducer / required-action breakdown. The CLI ``release-readiness-pr-risk``
emits ``pr_risk.json`` (full result), ``pr-risk.json`` (lean semantic
summary for CI gates), and ``pr_risk.md`` (human-readable report).

Schema/report version is exposed via ``report_version_string()``.
"""

from release_readiness_core.pr_risk.version import (
    VERSION,
    VERSION_MINOR,
    report_version_string,
)

__all__ = ["VERSION", "VERSION_MINOR", "report_version_string"]
