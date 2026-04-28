from release_readiness_core.cli import main
from release_readiness_core.engine import ValidationResult, evaluate_release_readiness


def test_engine_smoke_pass():
    report = evaluate_release_readiness([ValidationResult(key="go-test", status="PASS")])
    assert report.status == "PASS"
    assert report.passed == 1


def test_cli_smoke(capsys):
    code = main(["--input-json", '[{"key":"release-readiness","status":"WARN"}]'])
    assert code == 0
    captured = capsys.readouterr()
    assert '"status": "WARN"' in captured.out
