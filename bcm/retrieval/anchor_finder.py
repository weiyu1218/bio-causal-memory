from __future__ import annotations

from typing import List

from bcm.graph.schema import BioCausalGraph, NodeType


WHY_FAILED = "WHY_FAILED"
WHERE_FAILED = "WHERE_FAILED"
HOW_REPAIR = "HOW_REPAIR"


def infer_intent(question: str) -> str:
    q = question.lower()

    if any(token in q for token in ["repair", "fix", "修复", "改正", "解决"]):
        return HOW_REPAIR

    if any(token in q for token in ["where", "step", "哪一步", "哪里", "哪个步骤"]):
        return WHERE_FAILED

    if any(token in q for token in ["why", "failed", "fail", "为什么", "失败", "原因"]):
        return WHY_FAILED

    return WHY_FAILED


def find_anchors(graph: BioCausalGraph, question: str) -> List[str]:
    intent = infer_intent(question)

    error_nodes = [node.id for node in graph.nodes if node.type == NodeType.ERROR]
    eval_nodes = [node.id for node in graph.nodes if node.type == NodeType.EVAL]
    failed_commands = [
        node.id
        for node in graph.nodes
        if node.type == NodeType.COMMAND and node.attrs.get("returncode", 0) != 0
    ]

    if intent in {WHY_FAILED, WHERE_FAILED, HOW_REPAIR}:
        if error_nodes:
            return error_nodes
        if failed_commands:
            return failed_commands
        if eval_nodes:
            return eval_nodes

    return eval_nodes
