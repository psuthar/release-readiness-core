"""Schema validation tests for the pr-risk config."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


SCHEMA_PATH = Path(__file__).resolve().parents[2] / "docs" / "contracts" / "pr-risk-config-v1.schema.json"


def test_schema_file_exists():
    assert SCHEMA_PATH.is_file(), f"Schema file missing at {SCHEMA_PATH}"


def test_schema_is_valid_json():
    with open(SCHEMA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, dict)
    assert data["$schema"].startswith("https://json-schema.org/")
    assert data["title"]
    assert data["type"] == "object"


def test_schema_top_level_keys_match_loader_closed_set():
    """The schema's top-level keys must match the loader's KNOWN_TOP_LEVEL_KEYS."""
    from release_readiness_core.pr_risk._config import KNOWN_TOP_LEVEL_KEYS

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    schema_keys = set(data.get("properties", {}).keys())
    assert schema_keys == set(KNOWN_TOP_LEVEL_KEYS)


def test_schema_evidence_template_enum_matches_loader():
    """Closed set of evidence template names must match between schema and loader."""
    from release_readiness_core.pr_risk._config import EVIDENCE_TEMPLATE_NAMES

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    schema_templates = set(
        data["$defs"]["gate_evidence"]["properties"]["template"]["enum"]
    )
    assert schema_templates == set(EVIDENCE_TEMPLATE_NAMES)


def test_schema_path_pattern_keys_match_loader():
    """Path-pattern predicate primary keys must match between schema and loader."""
    from release_readiness_core.pr_risk._config import PATH_PATTERN_KEYS

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    pattern_branches = data["$defs"]["path_pattern"]["oneOf"]
    schema_keys = set()
    for branch in pattern_branches:
        # Each branch is `{type: object, required: [<key>], properties: {<key>: ...}}`.
        schema_keys.update(branch.get("required", []))
    assert schema_keys == set(PATH_PATTERN_KEYS)


def test_schema_gate_predicate_keys_match_loader():
    """Gate-predicate primary keys must match between schema and loader."""
    from release_readiness_core.pr_risk._config import GATE_PREDICATE_KEYS

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    branches = data["$defs"]["gate_predicate"]["oneOf"]
    schema_keys = set()
    for branch in branches:
        schema_keys.update(branch.get("required", []))
    assert schema_keys == set(GATE_PREDICATE_KEYS)


def test_schema_gate_priorities_match_loader():
    from release_readiness_core.pr_risk._config import GATE_PRIORITIES

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    schema_priorities = set(
        data["$defs"]["gate"]["properties"]["priority"]["enum"]
    )
    assert schema_priorities == set(GATE_PRIORITIES)


def test_schema_gate_fix_types_match_loader():
    from release_readiness_core.pr_risk._config import GATE_FIX_TYPES

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        data = json.load(f)
    schema_fix_types = set(
        data["$defs"]["gate"]["properties"]["fix_type"]["enum"]
    )
    assert schema_fix_types == set(GATE_FIX_TYPES)


def test_schema_validates_corpus_fixture():
    """The parity-fixture corpus config must validate against the schema."""
    jsonschema = pytest.importorskip("jsonschema")
    yaml = pytest.importorskip("yaml")

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    fixture_path = Path(__file__).parent / "fixtures" / "pr-risk-corpus-config.yaml"
    with open(fixture_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    jsonschema.validate(instance=cfg, schema=schema)
