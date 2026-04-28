from release_readiness_core.cli import main


def test_markdown_uses_custom_report_title(capsys):
    code = main(
        [
            "--input-json",
            '[{"key":"release-readiness","status":"PASS"}]',
            "--config-json",
            '{"report_title":"My Custom Readiness Report"}',
            "--output-format",
            "markdown",
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "# My Custom Readiness Report" in captured.out


def test_markdown_uses_custom_high_priority_ids(capsys):
    code = main(
        [
            "--input-json",
            '[{"key":"release-readiness","status":"WARN"}]',
            "--config-json",
            '{"pr_risk":{"high_priority_evidence_ids":["custom_gate"]}}',
            "--pr-risk-json",
            '{"evidence":[{"id":"custom_gate","status":"BLOCK"},{"id":"other","status":"WARN"}]}',
            "--output-format",
            "markdown",
        ]
    )
    assert code == 0
    captured = capsys.readouterr()
    assert "## High-priority PR-risk evidence" in captured.out
    assert "`custom_gate`: BLOCK" in captured.out
    assert "`other`: WARN" not in captured.out
