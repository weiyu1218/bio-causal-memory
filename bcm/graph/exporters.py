from __future__ import annotations

from bcm.graph.schema import BioCausalGraph


def to_markdown_edges(graph: BioCausalGraph) -> str:
    node_by_id = {node.id: node for node in graph.nodes}
    lines = ["| Source | Edge | Target | Confidence |", "|---|---|---|---:|"]
    for edge in graph.edges:
        source = node_by_id.get(edge.source)
        target = node_by_id.get(edge.target)
        source_label = source.label if source else edge.source
        target_label = target.label if target else edge.target
        lines.append(
            f"| {source_label} | {edge.type.value} | {target_label} | {edge.confidence:.2f} |"
        )
    return "\n".join(lines)
