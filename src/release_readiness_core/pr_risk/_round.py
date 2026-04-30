"""Half-away-from-zero rounding, matching Go's math.Round.

Python's built-in round() uses banker's rounding (round-half-to-even).
Go's math.Round rounds half away from zero. The PR Risk scorer relies
on math.Round at several score-computation sites (see score.go); to
preserve byte-for-byte parity we must use the Go semantics.
"""

import math


def round_half_away(x: float) -> float:
    """Round x to the nearest integer, with halves rounded away from zero.

    Matches Go's math.Round:
      math.Round(0.5)  ==  1
      math.Round(-0.5) == -1
      math.Round(2.5)  ==  3   (Python's round(2.5) returns 2)
      math.Round(-2.5) == -3
    """
    if math.isnan(x) or math.isinf(x):
        return x
    if x >= 0:
        return math.floor(x + 0.5)
    return math.ceil(x - 0.5)
