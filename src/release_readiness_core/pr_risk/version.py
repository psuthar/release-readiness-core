"""Schema/report version, mirrored from internal/prrisk/version.go."""

VERSION = 2
VERSION_MINOR = 8


def report_version_string() -> str:
    return f"v{VERSION}.{VERSION_MINOR}"
