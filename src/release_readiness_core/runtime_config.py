"""Runtime configuration models for CLI/report behavior."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from typing import Any, Dict, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class RuntimeConfig:
    """Config-driven values used by CLI report rendering."""

    report_title: str = "Release readiness report"
    high_priority_evidence_ids: Sequence[str] = field(default_factory=tuple)
    input_json_default_path: str = ""
    output_dir_default: str = "artifacts/release-readiness"
    base_ref_env_var: str = "RELEASE_READINESS_BASE_REF"
    enforcement_mode_env_var: str = "READINESS_ENFORCEMENT_MODE"


def parse_runtime_config(raw: Mapping[str, Any]) -> RuntimeConfig:
    """Parse runtime config payload into strongly typed values."""
    report_title = str(raw.get("report_title", "Release readiness report"))
    pr_risk = raw.get("pr_risk", {})
    high_priority: Iterable[str] = ()
    if isinstance(pr_risk, dict):
        ids = pr_risk.get("high_priority_evidence_ids", ())
        if isinstance(ids, list):
            high_priority = [str(v) for v in ids]
    paths = raw.get("paths", {})
    env_cfg = raw.get("env", {})

    input_json_default_path = ""
    output_dir_default = "artifacts/release-readiness"
    if isinstance(paths, dict):
        if isinstance(paths.get("input_json_default_path"), str):
            input_json_default_path = paths["input_json_default_path"]
        if isinstance(paths.get("output_dir_default"), str):
            output_dir_default = paths["output_dir_default"]

    base_ref_env_var = "RELEASE_READINESS_BASE_REF"
    enforcement_mode_env_var = "READINESS_ENFORCEMENT_MODE"
    if isinstance(env_cfg, dict):
        if isinstance(env_cfg.get("base_ref_env_var"), str):
            base_ref_env_var = env_cfg["base_ref_env_var"]
        if isinstance(env_cfg.get("enforcement_mode_env_var"), str):
            enforcement_mode_env_var = env_cfg["enforcement_mode_env_var"]

    return RuntimeConfig(
        report_title=report_title,
        high_priority_evidence_ids=tuple(high_priority),
        input_json_default_path=input_json_default_path,
        output_dir_default=output_dir_default,
        base_ref_env_var=base_ref_env_var,
        enforcement_mode_env_var=enforcement_mode_env_var,
    )


def resolve_runtime_defaults(config: RuntimeConfig) -> Dict[str, str]:
    """Resolve default runtime values using config-defined env var names."""
    return {
        "base_ref": os.getenv(config.base_ref_env_var, "origin/main"),
        "enforcement_mode": os.getenv(config.enforcement_mode_env_var, "warn"),
        "output_dir": config.output_dir_default,
        "input_json_default_path": config.input_json_default_path,
    }


def summarize_high_priority_hits(
    pr_risk_payload: Mapping[str, Any],
    high_priority_ids: Sequence[str],
) -> Dict[str, str]:
    """Return matching high-priority evidence id -> status from pr_risk payload."""
    id_set = set(high_priority_ids)
    hits: Dict[str, str] = {}
    evidence = pr_risk_payload.get("evidence", [])
    if not isinstance(evidence, list):
        return hits
    for item in evidence:
        if not isinstance(item, dict):
            continue
        evidence_id = item.get("id")
        status = item.get("status")
        if isinstance(evidence_id, str) and evidence_id in id_set and isinstance(status, str):
            hits[evidence_id] = status
    return hits
