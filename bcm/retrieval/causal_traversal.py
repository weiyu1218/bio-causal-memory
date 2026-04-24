from __future__ import annotations

from collections import deque
from typing import Dict, List, Set

from bcm.graph.schema import BioCausalGraph, EdgeType
from bcm.retrieval.anchor_finder import find_anchors, infer_intent


IMPORTANT_EDGE_TYPES = {
    EdgeType.FAILED_WITH,
    EdgeType.AFFECTED_EVAL,
    EdgeType.SUSPECTED_CAUSES,
    EdgeType.USES,
    EdgeType.USES_REFERENCE,
    EdgeType.USES_TOOL,
    EdgeType.HAS_LOG,
    EdgeType.PRODUCES,
    EdgeType.PRECEDES,
}


def _incident_edges(graph: BioCausalGraph, node_id: str):
    for edge in graph.edges:
        if edge.source == node_id or edge.target == node_id:
            if edge.type in IMPORTANT_EDGE_TYPES:
                yield edge


def retrieve_failure_context(
    graph: BioCausalGraph,
    question: str,
    max_nodes: int = 12,
) -> Dict[str, object]:
    intent = infer_intent(question)
    anchors = find_anchors(graph, question)

    visited_nodes: Set[str] = set()
    visited_edges: Set[str] = set()

    queue = deque(anchors)
    while queue and len(visited_nodes) < max_nodes:
        node_id = queue.popleft()
        if node_id in visited_nodes:
            continue
        visited_nodes.add(node_id)

        for edge in _incident_edges(graph, node_id):
            visited_edges.add(edge.id)
            neighbor = edge.target if edge.source == node_id else edge.source
            if neighbor not in visited_nodes:
                queue.append(neighbor)

    return {
        "intent": intent,
        "anchor_nodes": anchors,
        "evidence_nodes": list(visited_nodes),
        "evidence_edges": list(visited_edges),
        "summary": "",
    }
