from bcm.graph.schema import BioCausalGraph, EdgeType, GraphEdge, GraphNode, NodeType


def test_graph_node_creation():
    node = GraphNode(id="n1", type=NodeType.TASK, label="task")
    assert node.id == "n1"
    assert node.type == NodeType.TASK


def test_graph_edge_creation():
    edge = GraphEdge(id="e1", source="n1", target="n2", type=EdgeType.PRECEDES)
    assert edge.source == "n1"
    assert edge.target == "n2"
    assert edge.confidence == 1.0


def test_bio_causal_graph_dump_load():
    graph = BioCausalGraph(
        task_id="task",
        run_id="run",
        nodes=[GraphNode(id="n1", type=NodeType.TASK, label="task")],
        edges=[],
    )
    dumped = graph.model_dump_json()
    loaded = BioCausalGraph.model_validate_json(dumped)
    assert loaded.task_id == "task"
    assert len(loaded.nodes) == 1
