from __future__ import annotations

from bcm.graph.schema import BioCausalGraph
from bcm.retrieval.causal_traversal import retrieve_failure_context
from bcm.retrieval.context_builder import build_context


def answer_question(graph: BioCausalGraph, question: str) -> str:
    result = retrieve_failure_context(graph, question)
    return build_context(graph, result)
