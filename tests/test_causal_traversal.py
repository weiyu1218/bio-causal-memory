from bcm.graph.provenance_builder import build_provenance_graph
from bcm.ingest.bioagent_loader import load_task_metadata
from bcm.ingest.trace_loader import load_trace
from bcm.retrieval.anchor_finder import infer_intent
from bcm.retrieval.causal_traversal import retrieve_failure_context
from bcm.retrieval.context_builder import build_context


def test_infer_intent():
    assert infer_intent("why did the run fail?") == "WHY_FAILED"


def test_retrieve_failure_context_contains_failure_evidence():
    task = load_task_metadata("data/fixtures/transcript_quant_task.json")
    trace = load_trace("data/runs/transcript_quant_failed_toy.json")
    graph = build_provenance_graph(task, trace)

    result = retrieve_failure_context(graph, "why did the run fail?")
    assert result["intent"] == "WHY_FAILED"
    assert len(result["evidence_nodes"]) > 0
    assert len(result["evidence_edges"]) > 0

    context = build_context(graph, result)
    assert "wrong_index" in context
    assert "salmon_index" in context
