from bcm.graph.provenance_builder import build_provenance_graph
from bcm.ingest.bioagent_loader import load_task_metadata
from bcm.ingest.trace_loader import load_trace
from bcm.retrieval.causal_traversal import retrieve_failure_context
from bcm.retrieval.context_builder import build_context


def test_failed_commands_and_errors_sorted_by_step_id_ascending():
    task = load_task_metadata("data/fixtures/transcript_quant_task.json")
    trace = load_trace("data/runs/transcript_quant_failed_toy.json")
    graph = build_provenance_graph(task, trace)

    result = retrieve_failure_context(graph, "why did the run fail?")
    context = build_context(graph, result)

    step2_error_idx = context.find("Step 2 error:")
    step3_error_idx = context.find("Step 3 error:")

    assert step2_error_idx != -1, "Step 2 error must appear in context"
    assert step3_error_idx != -1, "Step 3 error must appear in context"
    assert step2_error_idx < step3_error_idx, (
        "Step 2 error must appear before Step 3 error (ascending step_id order)"
    )


def test_likely_failure_cause_uses_earliest_failed_step():
    task = load_task_metadata("data/fixtures/transcript_quant_task.json")
    trace = load_trace("data/runs/transcript_quant_failed_toy.json")
    graph = build_provenance_graph(task, trace)

    result = retrieve_failure_context(graph, "why did the run fail?")
    context = build_context(graph, result)

    cause_section = context.split("Evidence path:")[0]
    assert "wrong_index" in cause_section, (
        "Likely failure cause must reference the earliest failed command (step 2 wrong_index)"
    )
    assert "FileNotFoundError" not in cause_section, (
        "Likely failure cause must not be taken from step 3 (later failure)"
    )
