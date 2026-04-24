from bcm.ingest.trace_loader import load_trace


def test_load_trace_fixture():
    trace = load_trace("data/runs/transcript_quant_failed_toy.json")
    assert trace["task_id"] == "transcript-quant"
    assert trace["run_id"] == "transcript_quant_failed_toy"
    assert len(trace["steps"]) == 3
    assert trace["steps"][1]["returncode"] == 1
    assert "grader" in trace
