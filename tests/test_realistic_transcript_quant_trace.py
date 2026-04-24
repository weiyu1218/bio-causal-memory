import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from bcm.cli import app
from bcm.graph.provenance_builder import build_provenance_graph
from bcm.graph.schema import EdgeType, NodeType
from bcm.ingest.bioagent_task_adapter import load_bioagent_task
from bcm.ingest.trace_loader import load_trace
from bcm.ingest.trace_normalizer import normalize_trace
from bcm.retrieval.causal_traversal import retrieve_failure_context
from bcm.retrieval.context_builder import build_context


TRANSCRIPT_QUANT_DIR = "external/bioagent-bench/tasks/transcript-quant"
REALISTIC_TRACE = "data/runs/transcript_quant_bioagent_like_failed.json"


def test_normalize_trace_passthrough_preserves_steps():
    raw = load_trace(REALISTIC_TRACE)
    normalized = normalize_trace(raw)
    assert normalized["task_id"] == "transcript-quant"
    assert len(normalized["steps"]) == 3
    assert normalized["steps"][1]["returncode"] == 1


def test_normalize_trace_converts_shell_step_schema():
    raw = {
        "task_id": "transcript-quant",
        "run_id": "shell_step_example",
        "shell_steps": [
            {
                "index": 1,
                "command": "echo hello",
                "exit_code": 0,
                "stdout": "hello",
                "stderr": "",
            },
            {
                "index": 2,
                "command": "false",
                "exit_code": 1,
                "stdout": "",
                "stderr": "",
            },
        ],
        "grader": {"final_result_reached": False},
    }
    normalized = normalize_trace(raw)
    assert "steps" in normalized
    assert len(normalized["steps"]) == 2
    assert normalized["steps"][0]["step_id"] == 1
    assert normalized["steps"][0]["cmd"] == "echo hello"
    assert normalized["steps"][1]["returncode"] == 1
    assert normalized["steps"][0]["files_before"] == []
    assert normalized["steps"][0]["files_after"] == []


def test_realistic_trace_builds_expected_graph():
    if not Path(TRANSCRIPT_QUANT_DIR).is_dir():
        pytest.skip(f"external task dir not available: {TRANSCRIPT_QUANT_DIR}")

    task = load_bioagent_task(TRANSCRIPT_QUANT_DIR)
    trace = normalize_trace(load_trace(REALISTIC_TRACE))
    graph = build_provenance_graph(task, trace)

    tool_labels = {node.label for node in graph.nodes if node.type == NodeType.TOOL}
    assert "salmon" in tool_labels
    assert "awk" in tool_labels

    command_nodes = [node for node in graph.nodes if node.type == NodeType.COMMAND]
    assert len(command_nodes) == 3

    failed_steps = sorted(
        node.attrs["step_id"]
        for node in command_nodes
        if node.attrs.get("returncode", 0) != 0
    )
    assert failed_steps == [2, 3]

    edge_types = {edge.type for edge in graph.edges}
    assert EdgeType.HAS_LOG in edge_types
    assert EdgeType.FAILED_WITH in edge_types
    assert EdgeType.SUSPECTED_CAUSES in edge_types


def test_realistic_trace_query_identifies_earliest_failure():
    if not Path(TRANSCRIPT_QUANT_DIR).is_dir():
        pytest.skip(f"external task dir not available: {TRANSCRIPT_QUANT_DIR}")

    task = load_bioagent_task(TRANSCRIPT_QUANT_DIR)
    trace = normalize_trace(load_trace(REALISTIC_TRACE))
    graph = build_provenance_graph(task, trace)

    result = retrieve_failure_context(graph, "why did the run fail?")
    context = build_context(graph, result)

    assert "wrong_index" in context
    assert "processing/wrong_index" in context or "wrong_index" in context

    step2_idx = context.find("Step 2 error:")
    step3_idx = context.find("Step 3 error:")
    assert step2_idx != -1
    assert step3_idx != -1
    assert step2_idx < step3_idx, "earliest failing step must appear first"

    assert "final_result_reached=false" in context
    assert "results_match=false" in context


def test_realistic_trace_query_uses_observed_index_artifact_in_repair_hint():
    if not Path(TRANSCRIPT_QUANT_DIR).is_dir():
        pytest.skip(f"external task dir not available: {TRANSCRIPT_QUANT_DIR}")

    task = load_bioagent_task(TRANSCRIPT_QUANT_DIR)
    trace = normalize_trace(load_trace(REALISTIC_TRACE))
    graph = build_provenance_graph(task, trace)

    result = retrieve_failure_context(graph, "why did the run fail?")
    context = build_context(graph, result)

    assert (
        "Replace `-i processing/wrong_index` with `-i processing/index`"
        in context
    )
    assert "salmon_index" not in context


def test_cli_build_graph_accepts_shell_step_trace(tmp_path):
    trace_path = tmp_path / "shell_steps_trace.json"
    out_path = tmp_path / "shell_steps_trace.graph.json"
    trace_path.write_text(
        json.dumps(
            {
                "task_id": "transcript-quant",
                "run_id": "shell_step_cli",
                "shell_steps": [
                    {
                        "index": 1,
                        "command": "salmon index -t transcriptome.fa -i salmon_index",
                        "exit_code": 0,
                        "stdout": "index built",
                        "stderr": "",
                        "files_before": ["transcriptome.fa"],
                        "files_after": ["transcriptome.fa", "salmon_index/"],
                    }
                ],
                "grader": {
                    "final_result_reached": True,
                    "results_match": True,
                },
            }
        ),
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "build-graph",
            "--task",
            "data/fixtures/transcript_quant_task.json",
            "--trace",
            str(trace_path),
            "--out",
            str(out_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert out_path.exists()
