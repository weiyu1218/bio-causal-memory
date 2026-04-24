from __future__ import annotations

import typer
from rich.console import Console

from bcm.graph.graph_store import load_graph, save_graph
from bcm.graph.provenance_builder import build_provenance_graph
from bcm.ingest.bioagent_loader import load_task_metadata
from bcm.ingest.trace_loader import load_trace
from bcm.retrieval.router import answer_question

app = typer.Typer(help="bio-causal-memory CLI")
console = Console()


@app.command("build-graph")
def build_graph(
    task: str = typer.Option(..., "--task", help="Path to task metadata JSON"),
    trace: str = typer.Option(..., "--trace", help="Path to run trace JSON"),
    out: str = typer.Option(..., "--out", help="Output graph JSON path"),
) -> None:
    task_metadata = load_task_metadata(task)
    run_trace = load_trace(trace)
    graph = build_provenance_graph(task_metadata, run_trace)
    save_graph(graph, out)
    console.print(f"[green]Saved graph[/green]: {out}")
    console.print(f"Nodes: {len(graph.nodes)}")
    console.print(f"Edges: {len(graph.edges)}")


@app.command("query")
def query_graph(
    graph: str = typer.Option(..., "--graph", help="Path to graph JSON"),
    question: str = typer.Option(..., "--question", help="Question to ask"),
) -> None:
    loaded_graph = load_graph(graph)
    answer = answer_question(loaded_graph, question)
    console.print(answer)


if __name__ == "__main__":
    app()
