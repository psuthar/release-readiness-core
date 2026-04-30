"""Concentration analyzer (port of internal/prrisk/context/concentration.go).

Measures whether churn is focused in a few areas or scattered using the
Herfindahl Index over two-segment-prefix LOC shares.
"""

from __future__ import annotations

from release_readiness_core.pr_risk.context.input import Input
from release_readiness_core.pr_risk.context.types import ConcentrationInsight


_FOCUSED_LARGE_LOC = 2000  # aligns with very-large diff scale


def two_segment_prefix(p: str) -> str:
    """Return the first two segments of a path, joined by '/'.

    Mirrors Go context/concentration.go::twoSegmentPrefix exactly.
    """
    p = p.strip("/").replace("\\", "/")
    parts = p.split("/")
    if len(parts) == 0 or (len(parts) == 1 and parts[0] == ""):
        return "."
    if len(parts) == 1:
        return parts[0]
    return parts[0] + "/" + parts[1]


def _fmt_pct(x: float) -> str:
    """Format like Go fmt.Sprintf("%.0f", x) (half-away-from-zero, no decimals)."""
    from release_readiness_core.pr_risk._round import round_half_away

    return str(int(round_half_away(x)))


def _fmt_2(x: float) -> str:
    """Format like Go fmt.Sprintf("%.2f", x)."""
    return f"{x:.2f}"


def analyze_concentration(in_: Input) -> ConcentrationInsight:
    if not in_.files:
        return ConcentrationInsight(mode="balanced", detail="no files")

    loc_by_prefix: dict = {}
    for f in in_.files:
        p = f.path.replace("\\", "/").strip()
        prefix = two_segment_prefix(p)
        loc = f.added + f.deleted
        loc_by_prefix[prefix] = loc_by_prefix.get(prefix, 0) + loc

    total = sum(loc_by_prefix.values())
    if total == 0:
        return ConcentrationInsight(
            mode="balanced", unique_dirs=len(loc_by_prefix), detail="no LOC churn"
        )

    # Sort prefixes by LOC desc. Go used sort.Slice which is unstable, but for
    # parity we add a deterministic secondary key (prefix asc).
    prefs = sorted(loc_by_prefix.keys(), key=lambda k: (-loc_by_prefix[k], k))
    top = prefs[0]
    top_share = loc_by_prefix[top] / total

    # Herfindahl index on LOC shares.
    hhi = 0.0
    for v in loc_by_prefix.values():
        s = v / total
        hhi += s * s

    mode = "balanced"
    detail = "Churn is spread across several areas in a typical way."
    if len(loc_by_prefix) >= 6 and hhi < 0.18 and len(in_.files) >= 10:
        mode = "scattered"
        detail = (
            f"Churn is spread across {len(loc_by_prefix)} top-level areas "
            f"(HHI={_fmt_2(hhi)}); review may be harder to scope."
        )
    elif top_share >= 0.55 and len(loc_by_prefix) <= 4:
        mode = "focused"
        detail = f"Most churn (~{_fmt_pct(top_share * 100)}%) sits under `{top}`."
        if total >= _FOCUSED_LARGE_LOC:
            mode = "focused_large"
            detail = (
                f"Large concentrated churn (~{total} LOC); "
                f"~{_fmt_pct(top_share * 100)}% sits under `{top}` — "
                f"prioritize regression around this area."
            )

    return ConcentrationInsight(
        mode=mode,
        top_prefix=top,
        top_share=top_share,
        hhi=hhi,
        unique_dirs=len(loc_by_prefix),
        detail=detail,
    )
