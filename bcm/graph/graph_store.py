from __future__ import annotations

from pathlib import Path

from bcm.graph.schema import BioCausalGraph


def save_graph(graph: BioCausalGraph, path: str) -> None:
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(graph.model_dump_json(indent=2), encoding="utf-8")


def load_graph(path: str) -> BioCausalGraph:
    graph_path = Path(path)
    if not graph_path.exists():
        raise FileNotFoundError(f"Graph file not found: {graph_path}")
    return BioCausalGraph.model_validate_json(graph_path.read_text(encoding="utf-8"))
