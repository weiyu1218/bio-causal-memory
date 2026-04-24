from bcm.graph.provenance_builder import build_provenance_graph
from bcm.graph.schema import EdgeType, NodeType
from bcm.ingest.bioagent_loader import load_task_metadata
from bcm.ingest.trace_loader import load_trace


def test_build_provenance_graph():
    task = load_task_metadata("data/fixtures/transcript_quant_task.json")
    trace = load_trace("data/runs/transcript_quant_failed_toy.json")
    graph = build_provenance_graph(task, trace)

    node_types = [node.type for node in graph.nodes]
    edge_types = [edge.type for edge in graph.edges]

    assert NodeType.TASK in node_types
    assert len([node for node in graph.nodes if node.type == NodeType.COMMAND]) == 3
    assert any(node.type == NodeType.TOOL and node.label == "salmon" for node in graph.nodes)
    assert any(node.type == NodeType.ARTIFACT and node.label == "salmon_index/" for node in graph.nodes)
    assert NodeType.ERROR in node_types
    assert NodeType.EVAL in node_types

    assert EdgeType.FAILED_WITH in edge_types
    assert EdgeType.SUSPECTED_CAUSES in edge_types
