from __future__ import annotations

from typing import Optional

from bcm.graph.schema import BioCausalGraph, NodeType


def first_failed_step(graph: BioCausalGraph) -> Optional[int]:
    failed = [
        node.attrs.get("step_id")
        for node in graph.nodes
        if node.type == NodeType.COMMAND and node.attrs.get("returncode", 0) != 0
    ]
    failed = [x for x in failed if x is not None]
    return min(failed) if failed else None
