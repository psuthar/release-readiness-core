"""Dataclasses for context insights (port of internal/prrisk/context/types.go)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ProximityInsight:
    mode: str = ""                       # co_located | partial | distant | n_a
    structural_alignment: str = ""        # mirrors mode
    behavioral_coverage: str = ""         # unknown | shallow | adequate
    non_test_files: int = 0
    with_nearby_test_in_diff: int = 0
    ratio: float = 0.0
    detail: str = ""


@dataclass
class ConcentrationInsight:
    mode: str = ""                       # focused | focused_large | balanced | scattered
    top_prefix: str = ""
    top_share: float = 0.0
    hhi: float = 0.0
    unique_dirs: int = 0                  # JSON key: unique_prefixes (preserved on serialize)
    detail: str = ""


@dataclass
class HotspotInsight:
    prefix: str = ""
    recent_count: int = 0                 # JSON key: recent_hits
    detail: str = ""


@dataclass
class IntentInsight:
    title: str = ""
    intent_strength: str = ""             # strong | weak | unknown
    keywords_matched: List[str] = field(default_factory=list)
    domains_expected: List[str] = field(default_factory=list)
    domains_in_diff: List[str] = field(default_factory=list)
    aligned: bool = False
    mismatch: bool = False
    detail: str = ""


@dataclass
class ContextInsights:
    proximity: ProximityInsight = field(default_factory=ProximityInsight)
    concentration: ConcentrationInsight = field(default_factory=ConcentrationInsight)
    hotspots: List[HotspotInsight] = field(default_factory=list)
    hotspots_skip_reason: str = ""
    intent: IntentInsight = field(default_factory=IntentInsight)


@dataclass
class FactorContribution:
    id: str = ""
    label: str = ""
    points: float = 0.0
    detail: str = ""


@dataclass
class Weights:
    proximity_low_points: float = 0.0
    scattered_points: float = 0.0
    hotspot_points: float = 0.0
    intent_mismatch_points: float = 0.0
