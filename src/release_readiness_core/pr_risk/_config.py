"""PR Risk config dataclass and YAML loader.

Phase 1 ships the schema, dataclass, and loader. No behavior change yet — the
classifier, gate registry, and evidence detectors continue to drive from
hardcoded values until Phases 2-4 wire the runtime in.

Schema: ``docs/contracts/pr-risk-config-v1.schema.json``.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence


# ---------------------------------------------------------------------------
# Closed sets (mirror docs/contracts/pr-risk-config-v1.schema.json).

KNOWN_TOP_LEVEL_KEYS: frozenset[str] = frozenset({
    "version",
    "domains",
    "sensitive_domains",
    "gates",
})

PATH_PATTERN_KEYS: frozenset[str] = frozenset({
    "prefix",
    "contains",
    "exact",
    "endswith",
    "any_contains",
    "and",
})

GATE_PREDICATE_KEYS: frozenset[str] = frozenset({
    "factor_id",
    "not_factor_id",
    "risk_band",
    "not_risk_band",
    "domain_factor",
    "intent_mismatch",
    "concentration_mode",
    "hotspots_present",
    "proximity_distant_with_sensitive",
})

# Optional secondary keys accepted alongside the predicate's primary key.
GATE_PREDICATE_OPTIONAL_KEYS: Mapping[str, frozenset[str]] = {
    "concentration_mode": frozenset({"min_file_count"}),
    "proximity_distant_with_sensitive": frozenset({"min_non_test_files", "domains"}),
}

EVIDENCE_TEMPLATE_NAMES: frozenset[str] = frozenset({
    "test_domain",
    "signal_check",
    "migrations",
    "add_tests",
    "validation_note",
    "intent_alignment",
    "intent_strength",
    "intent_aligned_or_weak",
    "proximity",
    "hotspot",
})

GATE_PRIORITIES: frozenset[str] = frozenset({"high", "medium", "supporting"})
GATE_FIX_TYPES: frozenset[str] = frozenset({"code", "test", "config", "process", "infra", "db"})
RISK_BANDS: frozenset[str] = frozenset({"low", "medium", "high", "critical"})


class PRRiskConfigError(ValueError):
    """Raised when a pr-risk-config.yaml file fails schema validation."""


# ---------------------------------------------------------------------------
# Dataclass shape.

@dataclass(frozen=True)
class ChecklistItem:
    """One checklist line for a gate.

    ``by_evidence_level`` overrides the base text when the gate's primary
    domain has unit / e2e / no test coverage. ``by_validation_note`` overrides
    the base text when the commit message includes a ``Validation:`` note.
    """
    text: str
    by_evidence_level: Dict[str, str] = field(default_factory=dict)
    by_validation_note: Optional[str] = None


@dataclass(frozen=True)
class GateEvidence:
    """Evidence detector binding for a gate. ``template`` selects a closed-set
    detector implementation; ``args`` parametrise it (e.g. ``domain``)."""
    template: str
    args: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GateVariant:
    """Risk-band-conditional override for a gate's title / checklist /
    ``applies_when_extra`` text. Used by ``add_tests_or_evidence`` today."""
    when: Dict[str, Any] = field(default_factory=dict)
    title: Optional[str] = None
    applies_when_extra: Optional[str] = None
    checklist: Optional[List[ChecklistItem]] = None


@dataclass(frozen=True)
class Gate:
    id: str
    title: str
    priority: str
    fix_type: str
    applies_when: List[Dict[str, Any]] = field(default_factory=list)
    applies_when_extra: str = ""
    validation_line: str = ""
    checklist: List[ChecklistItem] = field(default_factory=list)
    evidence: Optional[GateEvidence] = None
    variants: List[GateVariant] = field(default_factory=list)


@dataclass(frozen=True)
class Domain:
    id: str
    label: str
    patterns: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class PRRiskConfig:
    version: int = 1
    domains: List[Domain] = field(default_factory=list)
    sensitive_domains: List[str] = field(default_factory=list)
    gates: List[Gate] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Loader.

def load_pr_risk_config(path: str | Path) -> PRRiskConfig:
    """Load a PR-risk config from a YAML file. Raises ``PRRiskConfigError``
    on any closed-set violation, malformed predicate, or duplicate gate id."""
    import yaml

    p = Path(path)
    with open(p, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise PRRiskConfigError(f"Config root must be a mapping: {p}")
    return parse_pr_risk_config(raw, source=str(p))


def parse_pr_risk_config(data: Mapping[str, Any], source: str = "<dict>") -> PRRiskConfig:
    """Validate and parse a config dict (already loaded from YAML/JSON)."""
    _validate_top_level(data, source)

    version = int(data.get("version", 1))
    if version != 1:
        raise PRRiskConfigError(
            f"Config {source}: unsupported version {version!r} (only v1 is supported)"
        )

    domains = _parse_domains(data.get("domains") or [], source)
    sensitive_domains = _parse_sensitive_domains(data.get("sensitive_domains") or [], source)
    gates = _parse_gates(data.get("gates") or [], source)

    return PRRiskConfig(
        version=version,
        domains=domains,
        sensitive_domains=sensitive_domains,
        gates=gates,
    )


def _validate_top_level(data: Mapping[str, Any], source: str) -> None:
    if "version" not in data:
        raise PRRiskConfigError(f"Config {source}: missing required top-level key 'version'")
    unknown = sorted(set(data.keys()) - KNOWN_TOP_LEVEL_KEYS)
    if unknown:
        suggestions: list[str] = []
        for key in unknown:
            close = difflib.get_close_matches(key, sorted(KNOWN_TOP_LEVEL_KEYS), n=1, cutoff=0.7)
            if close:
                suggestions.append(f"  - {key!r}  (did you mean {close[0]!r}?)")
            else:
                suggestions.append(f"  - {key!r}")
        raise PRRiskConfigError(
            f"Unknown top-level key(s) in pr-risk config {source}:\n"
            + "\n".join(suggestions)
            + "\n\nKnown keys: "
            + ", ".join(sorted(KNOWN_TOP_LEVEL_KEYS))
        )


def _parse_domains(raw: Any, source: str) -> List[Domain]:
    if not isinstance(raw, list):
        raise PRRiskConfigError(f"Config {source}: 'domains' must be a list")
    out: List[Domain] = []
    for i, entry in enumerate(raw):
        loc = f"{source}::domains[{i}]"
        if not isinstance(entry, dict):
            raise PRRiskConfigError(f"{loc}: must be a mapping")
        unknown = sorted(set(entry.keys()) - {"id", "label", "patterns"})
        if unknown:
            raise PRRiskConfigError(f"{loc}: unknown key(s) {unknown}")
        if "id" not in entry or not isinstance(entry["id"], str) or not entry["id"]:
            raise PRRiskConfigError(f"{loc}: 'id' is required and must be a non-empty string")
        domain_id = entry["id"]
        label = entry.get("label", domain_id)
        if not isinstance(label, str):
            raise PRRiskConfigError(f"{loc}: 'label' must be a string")
        patterns_raw = entry.get("patterns", [])
        if not isinstance(patterns_raw, list):
            raise PRRiskConfigError(f"{loc}: 'patterns' must be a list")
        patterns: List[Dict[str, Any]] = []
        for j, pat in enumerate(patterns_raw):
            ploc = f"{loc}::patterns[{j}]"
            patterns.append(_validate_path_pattern(pat, ploc))
        out.append(Domain(id=domain_id, label=label, patterns=patterns))
    return out


def _validate_path_pattern(pat: Any, loc: str) -> Dict[str, Any]:
    if not isinstance(pat, dict):
        raise PRRiskConfigError(f"{loc}: pattern must be a mapping")
    keys = set(pat.keys())
    if not keys:
        raise PRRiskConfigError(f"{loc}: pattern is empty")
    primary = keys & PATH_PATTERN_KEYS
    if len(primary) != 1:
        raise PRRiskConfigError(
            f"{loc}: pattern must contain exactly one of {sorted(PATH_PATTERN_KEYS)}, "
            f"got {sorted(keys)}"
        )
    extras = keys - PATH_PATTERN_KEYS
    if extras:
        raise PRRiskConfigError(f"{loc}: unknown pattern key(s) {sorted(extras)}")
    key = next(iter(primary))
    val = pat[key]
    if key in ("prefix", "contains", "exact", "endswith"):
        if not isinstance(val, str) or not val:
            raise PRRiskConfigError(f"{loc}: '{key}' must be a non-empty string")
    elif key == "any_contains":
        if not isinstance(val, list) or not val:
            raise PRRiskConfigError(f"{loc}: 'any_contains' must be a non-empty list of strings")
        for k, item in enumerate(val):
            if not isinstance(item, str) or not item:
                raise PRRiskConfigError(f"{loc}::any_contains[{k}]: must be a non-empty string")
    elif key == "and":
        if not isinstance(val, list) or len(val) < 2:
            raise PRRiskConfigError(f"{loc}: 'and' must be a list of at least two patterns")
        for k, sub in enumerate(val):
            _validate_path_pattern(sub, f"{loc}::and[{k}]")
    return dict(pat)


def _parse_sensitive_domains(raw: Any, source: str) -> List[str]:
    if not isinstance(raw, list):
        raise PRRiskConfigError(f"Config {source}: 'sensitive_domains' must be a list")
    out: List[str] = []
    for i, item in enumerate(raw):
        if not isinstance(item, str) or not item:
            raise PRRiskConfigError(
                f"Config {source}::sensitive_domains[{i}]: must be a non-empty string"
            )
        out.append(item)
    return out


def _parse_gates(raw: Any, source: str) -> List[Gate]:
    if not isinstance(raw, list):
        raise PRRiskConfigError(f"Config {source}: 'gates' must be a list")
    seen_ids: set[str] = set()
    out: List[Gate] = []
    allowed = {
        "id", "title", "priority", "fix_type",
        "applies_when", "applies_when_extra",
        "validation_line", "checklist", "evidence", "variants",
    }
    for i, entry in enumerate(raw):
        loc = f"{source}::gates[{i}]"
        if not isinstance(entry, dict):
            raise PRRiskConfigError(f"{loc}: must be a mapping")
        unknown = sorted(set(entry.keys()) - allowed)
        if unknown:
            raise PRRiskConfigError(f"{loc}: unknown key(s) {unknown}")
        for required in ("id", "title", "priority", "fix_type"):
            if required not in entry:
                raise PRRiskConfigError(f"{loc}: missing required key '{required}'")
        gate_id = entry["id"]
        if not isinstance(gate_id, str) or not gate_id:
            raise PRRiskConfigError(f"{loc}: 'id' must be a non-empty string")
        if gate_id in seen_ids:
            raise PRRiskConfigError(f"{loc}: duplicate gate id '{gate_id}'")
        seen_ids.add(gate_id)
        priority = entry["priority"]
        if priority not in GATE_PRIORITIES:
            raise PRRiskConfigError(
                f"{loc}: 'priority' must be one of {sorted(GATE_PRIORITIES)}, got {priority!r}"
            )
        fix_type = entry["fix_type"]
        if fix_type not in GATE_FIX_TYPES:
            raise PRRiskConfigError(
                f"{loc}: 'fix_type' must be one of {sorted(GATE_FIX_TYPES)}, got {fix_type!r}"
            )
        applies_when_raw = entry.get("applies_when") or []
        if not isinstance(applies_when_raw, list):
            raise PRRiskConfigError(f"{loc}: 'applies_when' must be a list")
        applies_when = [
            _validate_gate_predicate(p, f"{loc}::applies_when[{j}]")
            for j, p in enumerate(applies_when_raw)
        ]
        checklist = _parse_checklist(entry.get("checklist") or [], f"{loc}::checklist")
        evidence = _parse_evidence(entry.get("evidence"), f"{loc}::evidence")
        variants = _parse_variants(entry.get("variants") or [], f"{loc}::variants")
        out.append(Gate(
            id=gate_id,
            title=str(entry["title"]),
            priority=priority,
            fix_type=fix_type,
            applies_when=applies_when,
            applies_when_extra=str(entry.get("applies_when_extra", "")),
            validation_line=str(entry.get("validation_line", "")),
            checklist=checklist,
            evidence=evidence,
            variants=variants,
        ))
    return out


def _validate_gate_predicate(pred: Any, loc: str) -> Dict[str, Any]:
    if not isinstance(pred, dict):
        raise PRRiskConfigError(f"{loc}: predicate must be a mapping")
    keys = set(pred.keys())
    if not keys:
        raise PRRiskConfigError(f"{loc}: predicate is empty")
    primary = keys & GATE_PREDICATE_KEYS
    if len(primary) != 1:
        raise PRRiskConfigError(
            f"{loc}: predicate must contain exactly one of {sorted(GATE_PREDICATE_KEYS)}, "
            f"got {sorted(keys)}"
        )
    primary_key = next(iter(primary))
    allowed_optional = GATE_PREDICATE_OPTIONAL_KEYS.get(primary_key, frozenset())
    extras = keys - GATE_PREDICATE_KEYS - allowed_optional
    if extras:
        raise PRRiskConfigError(f"{loc}: unknown key(s) {sorted(extras)}")
    val = pred[primary_key]
    if primary_key in ("factor_id", "not_factor_id"):
        if isinstance(val, str):
            if not val:
                raise PRRiskConfigError(f"{loc}: '{primary_key}' must be a non-empty string")
        elif isinstance(val, list):
            if not val:
                raise PRRiskConfigError(
                    f"{loc}: '{primary_key}' list must contain at least one factor id"
                )
            for k, item in enumerate(val):
                if not isinstance(item, str) or not item:
                    raise PRRiskConfigError(
                        f"{loc}::{primary_key}[{k}]: must be a non-empty string"
                    )
        else:
            raise PRRiskConfigError(
                f"{loc}: '{primary_key}' must be a string or non-empty list of strings"
            )
    elif primary_key in ("domain_factor", "concentration_mode"):
        if not isinstance(val, str) or not val:
            raise PRRiskConfigError(f"{loc}: '{primary_key}' must be a non-empty string")
    elif primary_key in ("risk_band", "not_risk_band"):
        if not isinstance(val, list) or not val:
            raise PRRiskConfigError(f"{loc}: '{primary_key}' must be a non-empty list")
        for k, item in enumerate(val):
            if item not in RISK_BANDS:
                raise PRRiskConfigError(
                    f"{loc}::{primary_key}[{k}]: must be one of {sorted(RISK_BANDS)}, got {item!r}"
                )
    elif primary_key in ("intent_mismatch", "hotspots_present", "proximity_distant_with_sensitive"):
        if not isinstance(val, bool):
            raise PRRiskConfigError(f"{loc}: '{primary_key}' must be a boolean")
    if primary_key == "concentration_mode" and "min_file_count" in pred:
        if not isinstance(pred["min_file_count"], int) or pred["min_file_count"] < 0:
            raise PRRiskConfigError(f"{loc}::min_file_count: must be a non-negative integer")
    if primary_key == "proximity_distant_with_sensitive":
        if "min_non_test_files" in pred:
            if not isinstance(pred["min_non_test_files"], int) or pred["min_non_test_files"] < 0:
                raise PRRiskConfigError(
                    f"{loc}::min_non_test_files: must be a non-negative integer"
                )
        if "domains" in pred:
            doms = pred["domains"]
            if not isinstance(doms, list):
                raise PRRiskConfigError(f"{loc}::domains: must be a list of strings")
            for k, d in enumerate(doms):
                if not isinstance(d, str) or not d:
                    raise PRRiskConfigError(f"{loc}::domains[{k}]: must be a non-empty string")
    return dict(pred)


def _parse_checklist(raw: Any, loc: str) -> List[ChecklistItem]:
    if not isinstance(raw, list):
        raise PRRiskConfigError(f"{loc}: must be a list")
    out: List[ChecklistItem] = []
    for i, item in enumerate(raw):
        iloc = f"{loc}[{i}]"
        if isinstance(item, str):
            if not item:
                raise PRRiskConfigError(f"{iloc}: must be a non-empty string")
            out.append(ChecklistItem(text=item))
        elif isinstance(item, dict):
            unknown = sorted(set(item.keys()) - {"text", "by_evidence_level", "by_validation_note"})
            if unknown:
                raise PRRiskConfigError(f"{iloc}: unknown key(s) {unknown}")
            text = item.get("text")
            if not isinstance(text, str) or not text:
                raise PRRiskConfigError(f"{iloc}: 'text' must be a non-empty string")
            by_level_raw = item.get("by_evidence_level") or {}
            if not isinstance(by_level_raw, dict):
                raise PRRiskConfigError(f"{iloc}: 'by_evidence_level' must be a mapping")
            by_level: Dict[str, str] = {}
            for k, v in by_level_raw.items():
                if k not in {"none", "unit", "e2e"}:
                    raise PRRiskConfigError(
                        f"{iloc}::by_evidence_level: unknown level {k!r} "
                        f"(allowed: 'none', 'unit', 'e2e')"
                    )
                if not isinstance(v, str) or not v:
                    raise PRRiskConfigError(
                        f"{iloc}::by_evidence_level[{k!r}]: must be a non-empty string"
                    )
                by_level[k] = v
            by_validation_note = item.get("by_validation_note")
            if by_validation_note is not None and (
                not isinstance(by_validation_note, str) or not by_validation_note
            ):
                raise PRRiskConfigError(
                    f"{iloc}: 'by_validation_note' must be a non-empty string"
                )
            out.append(ChecklistItem(
                text=text,
                by_evidence_level=by_level,
                by_validation_note=by_validation_note,
            ))
        else:
            raise PRRiskConfigError(f"{iloc}: must be a string or mapping")
    return out


def _parse_evidence(raw: Any, loc: str) -> Optional[GateEvidence]:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise PRRiskConfigError(f"{loc}: must be a mapping")
    unknown = sorted(set(raw.keys()) - {"template", "args"})
    if unknown:
        raise PRRiskConfigError(f"{loc}: unknown key(s) {unknown}")
    template = raw.get("template")
    if not isinstance(template, str) or not template:
        raise PRRiskConfigError(f"{loc}: 'template' must be a non-empty string")
    if template not in EVIDENCE_TEMPLATE_NAMES:
        raise PRRiskConfigError(
            f"{loc}: 'template' must be one of {sorted(EVIDENCE_TEMPLATE_NAMES)}, "
            f"got {template!r}"
        )
    args_raw = raw.get("args") or {}
    if not isinstance(args_raw, dict):
        raise PRRiskConfigError(f"{loc}: 'args' must be a mapping")
    return GateEvidence(template=template, args=dict(args_raw))


def _parse_variants(raw: Any, loc: str) -> List[GateVariant]:
    if not isinstance(raw, list):
        raise PRRiskConfigError(f"{loc}: must be a list")
    out: List[GateVariant] = []
    allowed_when_keys = {"risk_band", "not_risk_band"}
    for i, entry in enumerate(raw):
        vloc = f"{loc}[{i}]"
        if not isinstance(entry, dict):
            raise PRRiskConfigError(f"{vloc}: must be a mapping")
        unknown = sorted(set(entry.keys()) - {"when", "title", "applies_when_extra", "checklist"})
        if unknown:
            raise PRRiskConfigError(f"{vloc}: unknown key(s) {unknown}")
        when_raw = entry.get("when") or {}
        if not isinstance(when_raw, dict):
            raise PRRiskConfigError(f"{vloc}::when: must be a mapping")
        when_unknown = sorted(set(when_raw.keys()) - allowed_when_keys)
        if when_unknown:
            raise PRRiskConfigError(f"{vloc}::when: unknown key(s) {when_unknown}")
        when: Dict[str, Any] = {}
        for k in ("risk_band", "not_risk_band"):
            if k in when_raw:
                vals = when_raw[k]
                if not isinstance(vals, list) or not vals:
                    raise PRRiskConfigError(f"{vloc}::when::{k}: must be a non-empty list")
                for j, b in enumerate(vals):
                    if b not in RISK_BANDS:
                        raise PRRiskConfigError(
                            f"{vloc}::when::{k}[{j}]: must be one of {sorted(RISK_BANDS)}"
                        )
                when[k] = list(vals)
        title = entry.get("title")
        if title is not None and not isinstance(title, str):
            raise PRRiskConfigError(f"{vloc}::title: must be a string")
        applies_when_extra = entry.get("applies_when_extra")
        if applies_when_extra is not None and not isinstance(applies_when_extra, str):
            raise PRRiskConfigError(f"{vloc}::applies_when_extra: must be a string")
        checklist = None
        if "checklist" in entry:
            checklist = _parse_checklist(entry["checklist"] or [], f"{vloc}::checklist")
        out.append(GateVariant(
            when=when,
            title=title,
            applies_when_extra=applies_when_extra,
            checklist=checklist,
        ))
    return out


# ---------------------------------------------------------------------------
# Round-trip helper (used by the round-trip test in Phase 1).

def config_to_dict(cfg: PRRiskConfig) -> Dict[str, Any]:
    """Convert a ``PRRiskConfig`` back to a plain dict / list shape suitable
    for ``yaml.safe_dump``. Output is deeply equal to the dict that produced
    the same config via ``parse_pr_risk_config``."""
    out: Dict[str, Any] = {"version": cfg.version}
    if cfg.domains:
        out["domains"] = [_domain_to_dict(d) for d in cfg.domains]
    if cfg.sensitive_domains:
        out["sensitive_domains"] = list(cfg.sensitive_domains)
    if cfg.gates:
        out["gates"] = [_gate_to_dict(g) for g in cfg.gates]
    return out


def _domain_to_dict(d: Domain) -> Dict[str, Any]:
    entry: Dict[str, Any] = {"id": d.id, "label": d.label}
    if d.patterns:
        entry["patterns"] = [dict(p) for p in d.patterns]
    return entry


def _gate_to_dict(g: Gate) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "id": g.id,
        "title": g.title,
        "priority": g.priority,
        "fix_type": g.fix_type,
    }
    if g.applies_when:
        out["applies_when"] = [dict(p) for p in g.applies_when]
    if g.applies_when_extra:
        out["applies_when_extra"] = g.applies_when_extra
    if g.validation_line:
        out["validation_line"] = g.validation_line
    if g.checklist:
        out["checklist"] = [_checklist_to_dict(c) for c in g.checklist]
    if g.evidence is not None:
        ev: Dict[str, Any] = {"template": g.evidence.template}
        if g.evidence.args:
            ev["args"] = dict(g.evidence.args)
        out["evidence"] = ev
    if g.variants:
        out["variants"] = [_variant_to_dict(v) for v in g.variants]
    return out


def _checklist_to_dict(c: ChecklistItem) -> Any:
    if not c.by_evidence_level and c.by_validation_note is None:
        return c.text
    out: Dict[str, Any] = {"text": c.text}
    if c.by_evidence_level:
        out["by_evidence_level"] = dict(c.by_evidence_level)
    if c.by_validation_note is not None:
        out["by_validation_note"] = c.by_validation_note
    return out


def _variant_to_dict(v: GateVariant) -> Dict[str, Any]:
    out: Dict[str, Any] = {"when": dict(v.when)}
    if v.title is not None:
        out["title"] = v.title
    if v.applies_when_extra is not None:
        out["applies_when_extra"] = v.applies_when_extra
    if v.checklist is not None:
        out["checklist"] = [_checklist_to_dict(c) for c in v.checklist]
    return out
