"""PR Risk scorer (Python port of TalkBack's Go cmd/prrisk + internal/prrisk).

Schema/report version remains v2.8 during the Go→Python port (SCRUM-231).
The public API surfaces incrementally across SCRUM-232..236; until then,
the CLI exits non-zero with a "not implemented" message.
"""

from release_readiness_core.pr_risk.version import (
    VERSION,
    VERSION_MINOR,
    report_version_string,
)

__all__ = ["VERSION", "VERSION_MINOR", "report_version_string"]
