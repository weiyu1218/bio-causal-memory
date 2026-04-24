from bcm.graph.provenance_builder import build_provenance_graph
from bcm.graph.schema import EdgeType, NodeType
from bcm.ingest.bioagent_loader import load_task_metadata
from bcm.ingest.trace_loader import load_trace
from bcm.retrieval.causal_traversal import retrieve_failure_context


def test_has_log_edge_type_exists():
    assert EdgeType.HAS_LOG.value == "HAS_LOG"


def test_command_to_log_edges_created_for_each_step():
    task = load_task_metadata("data/fixtures/transcript_quant_task.json")
    trace = load_trace("data/runs/transcript_quant_failed_toy.json")
    graph = build_provenance_graph(task, trace)

    node_by_id = {node.id: node for node in graph.nodes}

    has_log_edges = [edge for edge in graph.edges if edge.type == EdgeType.HAS_LOG]
    command_nodes = [node for node in graph.nodes if node.type == NodeType.COMMAND]
    log_nodes = [node for node in graph.nodes if node.type == NodeType.LOG]

    assert len(has_log_edges) == len(trace["steps"]), (
        "One HAS_LOG edge per step expected"
    )
    assert len(log_nodes) == len(trace["steps"]), "One LOG node per step expected"

    for edge in has_log_edges:
        source_node = node_by_id[edge.source]
        target_node = node_by_id[edge.target]
        assert source_node.type == NodeType.COMMAND
        assert target_node.type == NodeType.LOG
        assert source_node.attrs.get("step_id") == target_node.attrs.get("step_id")

    log_targets = {edge.target for edge in has_log_edges}
    for log_node in log_nodes:
        assert log_node.id in log_targets, (
            f"LOG node {log_node.id} must be reached via HAS_LOG edge"
        )


def test_failure_context_retrieval_includes_log_nodes():
    task = load_task_metadata("data/fixtures/transcript_quant_task.json")
    trace = load_trace("data/runs/transcript_quant_failed_toy.json")
    graph = build_provenance_graph(task, trace)

    result = retrieve_failure_context(graph, "why did the run fail?")
    node_by_id = {node.id: node for node in graph.nodes}
    evidence_types = {
        node_by_id[node_id].type
        for node_id in result["evidence_nodes"]
        if node_id in node_by_id
    }

    assert NodeType.LOG in evidence_types
