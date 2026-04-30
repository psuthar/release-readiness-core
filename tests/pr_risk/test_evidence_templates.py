"""Unit tests for the closed-set evidence templates (SCRUM-242 / Phase 4).

One parametrized class per template, exercising the pass / missing / fail /
not_evaluated / unknown branches each template can return.
"""

from __future__ import annotations

import pytest

from release_readiness_core.pr_risk._evidence_templates import (
    BUILTIN_TEMPLATES,
    template_add_tests,
    template_hotspot,
    template_intent_aligned_or_weak,
    template_intent_alignment,
    template_intent_strength,
    template_migrations,
    template_proximity,
    template_signal_check,
    template_test_domain,
    template_validation_note,
)
from release_readiness_core.pr_risk.context.types import (
    ConcentrationInsight,
    ContextInsights,
    HotspotInsight,
    IntentInsight,
    ProximityInsight,
)
from release_readiness_core.pr_risk.types import (
    EVIDENCE_FAIL,
    EVIDENCE_MISSING,
    EVIDENCE_NOT_EVALUATED,
    EVIDENCE_PASS,
    EVIDENCE_UNKNOWN,
    Result,
    Signals,
)


def _r(*, signals: Signals | None = None, ci: ContextInsights | None = None) -> Result:
    return Result(signals=signals or Signals(), context_insights=ci)


# ---------------------------------------------------------------------------

def test_builtin_templates_registry_lists_all_ten():
    assert set(BUILTIN_TEMPLATES.keys()) == {
        "signal_check",
        "intent_strength",
        "validation_note",
        "test_domain",
        "migrations",
        "add_tests",
        "intent_alignment",
        "intent_aligned_or_weak",
        "proximity",
        "hotspot",
    }


# ---------------------------------------------------------------------------
# signal_check.

class TestSignalCheck:
    def test_pass_when_signal_field_empty(self) -> None:
        ev = template_signal_check(
            "ci_fetch_depth_zero", "L", {"signal_field": "git_error"}, _r()
        )
        assert ev.status == EVIDENCE_PASS
        assert ev.id == "ci_fetch_depth_zero"
        assert ev.label == "L"

    def test_fail_when_signal_field_nonempty(self) -> None:
        ev = template_signal_check(
            "ci_fetch_depth_zero", "L", {"signal_field": "git_error"},
            _r(signals=Signals(git_error="bad ref")),
        )
        assert ev.status == EVIDENCE_FAIL
        assert "bad ref" in ev.rationale


# ---------------------------------------------------------------------------
# intent_strength.

class TestIntentStrength:
    def test_unknown_when_no_insights(self) -> None:
        ev = template_intent_strength("g", "L", {}, _r())
        assert ev.status == EVIDENCE_UNKNOWN

    def test_pass_for_strong(self) -> None:
        ci = ContextInsights(intent=IntentInsight(intent_strength="strong"))
        ev = template_intent_strength("g", "L", {}, _r(ci=ci))
        assert ev.status == EVIDENCE_PASS

    def test_missing_for_weak(self) -> None:
        ci = ContextInsights(intent=IntentInsight(intent_strength="weak", title="tx"))
        ev = template_intent_strength("g", "L", {}, _r(ci=ci))
        assert ev.status == EVIDENCE_MISSING

    def test_missing_for_weak_no_title(self) -> None:
        ci = ContextInsights(intent=IntentInsight(intent_strength="weak", title=""))
        ev = template_intent_strength("g", "L", {}, _r(ci=ci))
        assert ev.status == EVIDENCE_MISSING
        assert "absent" in ev.rationale

    def test_not_evaluated_for_unknown_strength(self) -> None:
        ci = ContextInsights(intent=IntentInsight(intent_strength="unknown"))
        ev = template_intent_strength("g", "L", {}, _r(ci=ci))
        assert ev.status == EVIDENCE_NOT_EVALUATED


# ---------------------------------------------------------------------------
# validation_note.

class TestValidationNote:
    def test_pass_when_note_present(self) -> None:
        s = Signals(validation_note_found=True, validation_note_snippet="Validation: ran X")
        ev = template_validation_note("g", "L", {}, _r(signals=s))
        assert ev.status == EVIDENCE_PASS
        assert "Validation: ran X" in ev.rationale

    def test_not_evaluated_otherwise(self) -> None:
        ev = template_validation_note("g", "L", {}, _r())
        assert ev.status == EVIDENCE_NOT_EVALUATED


# ---------------------------------------------------------------------------
# test_domain.

class TestTestDomain:
    def test_pass_for_e2e_hits(self) -> None:
        s = Signals(test_e2e_domain_hits={"auth": 2})
        ev = template_test_domain("g", "L", {"domain": "auth"}, _r(signals=s))
        assert ev.status == EVIDENCE_PASS
        assert "E2E test files" in ev.rationale

    def test_not_evaluated_for_unit_only(self) -> None:
        s = Signals(test_unit_domain_hits={"auth": 1})
        ev = template_test_domain("g", "L", {"domain": "auth"}, _r(signals=s))
        assert ev.status == EVIDENCE_NOT_EVALUATED

    def test_missing_when_no_test_hits(self) -> None:
        ev = template_test_domain("g", "L", {"domain": "auth"}, _r())
        assert ev.status == EVIDENCE_MISSING


# ---------------------------------------------------------------------------
# migrations.

class TestMigrations:
    def test_pass_for_e2e_hits(self) -> None:
        s = Signals(test_e2e_domain_hits={"migrations": 1})
        ev = template_migrations("g", "L", {}, _r(signals=s))
        assert ev.status == EVIDENCE_PASS

    def test_pass_for_validation_note_with_migration_files(self) -> None:
        s = Signals(validation_note_found=True, validation_note_snippet="x", migration_files=2)
        ev = template_migrations("g", "L", {}, _r(signals=s))
        assert ev.status == EVIDENCE_PASS
        assert "Validation note present" in ev.rationale

    def test_missing_when_migration_files_no_evidence(self) -> None:
        s = Signals(migration_files=1)
        ev = template_migrations("g", "L", {}, _r(signals=s))
        assert ev.status == EVIDENCE_MISSING

    def test_unknown_when_no_migration_files(self) -> None:
        ev = template_migrations("g", "L", {}, _r())
        assert ev.status == EVIDENCE_UNKNOWN


# ---------------------------------------------------------------------------
# add_tests.

class TestAddTests:
    def test_pass_for_style_only(self) -> None:
        s = Signals(style_only_note_found=True)
        ev = template_add_tests("g", "L", {}, _r(signals=s))
        assert ev.status == EVIDENCE_PASS
        assert "Style-only" in ev.rationale

    def test_pass_for_adequate_proximity(self) -> None:
        ci = ContextInsights(proximity=ProximityInsight(behavioral_coverage="adequate"))
        ev = template_add_tests("g", "L", {}, _r(ci=ci))
        assert ev.status == EVIDENCE_PASS

    def test_pass_for_high_test_loc_ratio(self) -> None:
        s = Signals(test_loc_ratio=0.5, test_files=3)
        ev = template_add_tests("g", "L", {}, _r(signals=s))
        assert ev.status == EVIDENCE_PASS

    def test_missing_when_no_test_files(self) -> None:
        ev = template_add_tests("g", "L", {}, _r())
        assert ev.status == EVIDENCE_MISSING

    def test_not_evaluated_for_shallow_proximity(self) -> None:
        s = Signals(test_files=1, test_loc_ratio=0.1)
        ci = ContextInsights(proximity=ProximityInsight(behavioral_coverage="shallow"))
        ev = template_add_tests("g", "L", {}, _r(signals=s, ci=ci))
        assert ev.status == EVIDENCE_NOT_EVALUATED

    def test_not_evaluated_when_few_tests_no_ci(self) -> None:
        s = Signals(test_files=1, test_loc_ratio=0.1)
        ev = template_add_tests("g", "L", {}, _r(signals=s))
        assert ev.status == EVIDENCE_NOT_EVALUATED


# ---------------------------------------------------------------------------
# intent_alignment.

class TestIntentAlignment:
    def test_unknown_when_no_insights(self) -> None:
        ev = template_intent_alignment("g", "L", {}, _r())
        assert ev.status == EVIDENCE_UNKNOWN

    def test_fail_for_mismatch(self) -> None:
        ci = ContextInsights(intent=IntentInsight(mismatch=True, detail="auth"))
        ev = template_intent_alignment("g", "L", {}, _r(ci=ci))
        assert ev.status == EVIDENCE_FAIL

    def test_pass_for_aligned(self) -> None:
        ci = ContextInsights(intent=IntentInsight(aligned=True))
        ev = template_intent_alignment("g", "L", {}, _r(ci=ci))
        assert ev.status == EVIDENCE_PASS

    def test_not_evaluated_otherwise(self) -> None:
        ci = ContextInsights(intent=IntentInsight())
        ev = template_intent_alignment("g", "L", {}, _r(ci=ci))
        assert ev.status == EVIDENCE_NOT_EVALUATED


# ---------------------------------------------------------------------------
# intent_aligned_or_weak.

class TestIntentAlignedOrWeak:
    def test_unknown_when_no_insights(self) -> None:
        ev = template_intent_aligned_or_weak("g", "L", {}, _r())
        assert ev.status == EVIDENCE_UNKNOWN

    def test_pass_for_strong_aligned(self) -> None:
        ci = ContextInsights(intent=IntentInsight(intent_strength="strong", aligned=True))
        ev = template_intent_aligned_or_weak("g", "L", {}, _r(ci=ci))
        assert ev.status == EVIDENCE_PASS

    def test_missing_for_weak(self) -> None:
        ci = ContextInsights(intent=IntentInsight(intent_strength="weak"))
        ev = template_intent_aligned_or_weak("g", "L", {}, _r(ci=ci))
        assert ev.status == EVIDENCE_MISSING

    def test_not_evaluated_otherwise(self) -> None:
        ci = ContextInsights(intent=IntentInsight(intent_strength="unknown"))
        ev = template_intent_aligned_or_weak("g", "L", {}, _r(ci=ci))
        assert ev.status == EVIDENCE_NOT_EVALUATED


# ---------------------------------------------------------------------------
# proximity.

class TestProximity:
    def test_unknown_when_no_insights(self) -> None:
        ev = template_proximity("g", "L", {}, _r())
        assert ev.status == EVIDENCE_UNKNOWN

    def test_pass_for_adequate(self) -> None:
        ci = ContextInsights(proximity=ProximityInsight(behavioral_coverage="adequate"))
        ev = template_proximity("g", "L", {}, _r(ci=ci))
        assert ev.status == EVIDENCE_PASS

    def test_missing_for_distant_unknown(self) -> None:
        ci = ContextInsights(
            proximity=ProximityInsight(mode="distant", behavioral_coverage="unknown"),
        )
        ev = template_proximity("g", "L", {}, _r(ci=ci))
        assert ev.status == EVIDENCE_MISSING

    def test_not_evaluated_otherwise(self) -> None:
        ci = ContextInsights(
            proximity=ProximityInsight(mode="adequate", behavioral_coverage="shallow"),
        )
        ev = template_proximity("g", "L", {}, _r(ci=ci))
        assert ev.status == EVIDENCE_NOT_EVALUATED


# ---------------------------------------------------------------------------
# hotspot.

class TestHotspot:
    def test_pass_when_validation_note(self) -> None:
        s = Signals(validation_note_found=True, validation_note_snippet="x")
        ev = template_hotspot("g", "L", {}, _r(signals=s))
        assert ev.status == EVIDENCE_PASS

    def test_not_evaluated_otherwise(self) -> None:
        ev = template_hotspot("g", "L", {}, _r())
        assert ev.status == EVIDENCE_NOT_EVALUATED
