from release_readiness_core.pr_gate import (
    GateInput,
    combine_gate_inputs,
    format_gate_output,
)


def test_combine_gate_inputs_supports_n_inputs():
    summary = combine_gate_inputs(
        [
            GateInput(source="unit", status="PASS", payload={"count": 10}),
            GateInput(source="e2e", status="WARN", payload={"count": 2}),
            GateInput(source="security", status="PASS", payload={"count": 3}),
        ]
    )
    assert summary.recommendation == "WARN"
    assert len(summary.sources) == 3
    assert [item["source"] for item in summary.sources] == ["unit", "e2e", "security"]


def test_format_gate_output_uses_custom_formatter():
    summary = combine_gate_inputs(
        [
            GateInput(source="risk", status="BLOCK", payload={"score": 88}),
            GateInput(source="readiness", status="PASS", payload={"score": 95}),
        ]
    )

    def formatter(s):
        return {"final_gate": {"status": s.recommendation}, "source_count": len(s.sources)}

    rendered = format_gate_output(summary, formatter=formatter)
    assert rendered == {"final_gate": {"status": "BLOCK"}, "source_count": 2}
