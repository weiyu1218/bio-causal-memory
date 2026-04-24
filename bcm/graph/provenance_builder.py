from __future__ import annotations

import hashlib
import shlex
from typing import Any, Dict, Iterable, List, Optional, Set

from bcm.graph.schema import (
    BioCausalGraph,
    EdgeType,
    GraphEdge,
    GraphNode,
    NodeType,
)


def _stable_id(*parts: object) -> str:
    raw = "::".join(str(p) for p in parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]
    return digest


def _node_id(node_type: NodeType, *parts: object) -> str:
    return f"{node_type.value.lower()}_{_stable_id(node_type.value, *parts)}"


def _edge_id(edge_type: EdgeType, source: str, target: str, *parts: object) -> str:
    return f"{edge_type.value.lower()}_{_stable_id(edge_type.value, source, target, *parts)}"


def _tool_from_cmd(cmd: str) -> str:
    try:
        tokens = shlex.split(cmd)
    except ValueError:
        tokens = cmd.split()
    if not tokens:
        return "unknown"
    return tokens[0]


def _add_node_once(nodes_by_id: Dict[str, GraphNode], node: GraphNode) -> None:
    if node.id not in nodes_by_id:
        nodes_by_id[node.id] = node


def _add_edge_once(edges_by_id: Dict[str, GraphEdge], edge: GraphEdge) -> None:
    if edge.id not in edges_by_id:
        edges_by_id[edge.id] = edge


def _cmd_mentions(cmd: str, name: str) -> bool:
    return name in cmd


def _new_files(files_before: Iterable[str], files_after: Iterable[str]) -> Set[str]:
    return set(files_after) - set(files_before)


def build_provenance_graph(task: Dict[str, Any], trace: Dict[str, Any]) -> BioCausalGraph:
    task_id = trace["task_id"]
    run_id = trace["run_id"]

    nodes_by_id: Dict[str, GraphNode] = {}
    edges_by_id: Dict[str, GraphEdge] = {}

    task_node_id = _node_id(NodeType.TASK, task_id)
    task_node = GraphNode(
        id=task_node_id,
        type=NodeType.TASK,
        label=task.get("name", task_id),
        attrs={
            "task_id": task_id,
            "goal": task.get("goal", ""),
            "expected_outputs": task.get("expected_outputs", []),
        },
    )
    _add_node_once(nodes_by_id, task_node)

    input_nodes: Dict[str, str] = {}
    for filename in task.get("input_data", []):
        node_id = _node_id(NodeType.INPUT_DATA, task_id, filename)
        input_nodes[filename] = node_id
        _add_node_once(
            nodes_by_id,
            GraphNode(
                id=node_id,
                type=NodeType.INPUT_DATA,
                label=filename,
                attrs={"path": filename},
            ),
        )

    reference_nodes: Dict[str, str] = {}
    for filename in task.get("reference_data", []):
        node_id = _node_id(NodeType.REFERENCE_DATA, task_id, filename)
        reference_nodes[filename] = node_id
        _add_node_once(
            nodes_by_id,
            GraphNode(
                id=node_id,
                type=NodeType.REFERENCE_DATA,
                label=filename,
                attrs={"path": filename},
            ),
        )

    eval_node_id = _node_id(NodeType.EVAL, task_id, run_id, "grader")
    grader = trace.get("grader", {})
    _add_node_once(
        nodes_by_id,
        GraphNode(
            id=eval_node_id,
            type=NodeType.EVAL,
            label=f"grader:{run_id}",
            attrs=grader,
        ),
    )

    command_node_ids: List[str] = []
    failed_command_ids: List[str] = []
    error_node_ids: List[str] = []

    known_artifact_nodes: Dict[str, str] = {}

    steps = trace.get("steps", [])
    for step in steps:
        step_id = step["step_id"]
        cmd = step["cmd"]
        returncode = step["returncode"]
        stdout = step.get("stdout", "")
        stderr = step.get("stderr", "")

        command_node_id = _node_id(NodeType.COMMAND, task_id, run_id, step_id, cmd)
        command_node_ids.append(command_node_id)

        _add_node_once(
            nodes_by_id,
            GraphNode(
                id=command_node_id,
                type=NodeType.COMMAND,
                label=f"step {step_id}: {cmd}",
                attrs={
                    "step_id": step_id,
                    "cmd": cmd,
                    "cwd": step.get("cwd", ""),
                    "returncode": returncode,
                    "start_time": step.get("start_time", ""),
                    "end_time": step.get("end_time", ""),
                },
            ),
        )

        tool_name = _tool_from_cmd(cmd)
        tool_node_id = _node_id(NodeType.TOOL, tool_name)
        _add_node_once(
            nodes_by_id,
            GraphNode(
                id=tool_node_id,
                type=NodeType.TOOL,
                label=tool_name,
                attrs={"tool_name": tool_name},
            ),
        )

        _add_edge_once(
            edges_by_id,
            GraphEdge(
                id=_edge_id(EdgeType.USES_TOOL, command_node_id, tool_node_id),
                source=command_node_id,
                target=tool_node_id,
                type=EdgeType.USES_TOOL,
                confidence=1.0,
                evidence=[cmd],
            ),
        )

        for filename, input_node_id in input_nodes.items():
            if _cmd_mentions(cmd, filename):
                _add_edge_once(
                    edges_by_id,
                    GraphEdge(
                        id=_edge_id(EdgeType.USES, command_node_id, input_node_id),
                        source=command_node_id,
                        target=input_node_id,
                        type=EdgeType.USES,
                        confidence=1.0,
                        evidence=[cmd],
                    ),
                )

        for filename, reference_node_id in reference_nodes.items():
            if _cmd_mentions(cmd, filename):
                _add_edge_once(
                    edges_by_id,
                    GraphEdge(
                        id=_edge_id(
                            EdgeType.USES_REFERENCE,
                            command_node_id,
                            reference_node_id,
                        ),
                        source=command_node_id,
                        target=reference_node_id,
                        type=EdgeType.USES_REFERENCE,
                        confidence=1.0,
                        evidence=[cmd],
                    ),
                )

        created_files = _new_files(step.get("files_before", []), step.get("files_after", []))
        for artifact_path in sorted(created_files):
            artifact_node_id = _node_id(NodeType.ARTIFACT, task_id, run_id, artifact_path)
            known_artifact_nodes[artifact_path] = artifact_node_id
            _add_node_once(
                nodes_by_id,
                GraphNode(
                    id=artifact_node_id,
                    type=NodeType.ARTIFACT,
                    label=artifact_path,
                    attrs={"path": artifact_path, "created_by_step": step_id},
                ),
            )
            _add_edge_once(
                edges_by_id,
                GraphEdge(
                    id=_edge_id(EdgeType.PRODUCES, command_node_id, artifact_node_id),
                    source=command_node_id,
                    target=artifact_node_id,
                    type=EdgeType.PRODUCES,
                    confidence=1.0,
                    evidence=[cmd],
                ),
            )

        log_text = "\n".join(
            part for part in [f"STDOUT:\n{stdout}", f"STDERR:\n{stderr}"] if part
        )
        log_node_id = _node_id(NodeType.LOG, task_id, run_id, step_id, "log")
        _add_node_once(
            nodes_by_id,
            GraphNode(
                id=log_node_id,
                type=NodeType.LOG,
                label=f"step {step_id} log",
                attrs={
                    "step_id": step_id,
                    "stdout": stdout,
                    "stderr": stderr,
                },
            ),
        )

        _add_edge_once(
            edges_by_id,
            GraphEdge(
                id=_edge_id(EdgeType.HAS_LOG, command_node_id, log_node_id),
                source=command_node_id,
                target=log_node_id,
                type=EdgeType.HAS_LOG,
                confidence=1.0,
                evidence=[log_text] if log_text else [],
            ),
        )

        if returncode != 0:
            failed_command_ids.append(command_node_id)
            error_node_id = _node_id(NodeType.ERROR, task_id, run_id, step_id, stderr)
            error_node_ids.append(error_node_id)
            _add_node_once(
                nodes_by_id,
                GraphNode(
                    id=error_node_id,
                    type=NodeType.ERROR,
                    label=f"step {step_id} error",
                    attrs={
                        "step_id": step_id,
                        "returncode": returncode,
                        "stderr": stderr,
                    },
                ),
            )

            _add_edge_once(
                edges_by_id,
                GraphEdge(
                    id=_edge_id(EdgeType.FAILED_WITH, command_node_id, error_node_id),
                    source=command_node_id,
                    target=error_node_id,
                    type=EdgeType.FAILED_WITH,
                    confidence=1.0,
                    evidence=[stderr or f"returncode={returncode}"],
                ),
            )

            _add_edge_once(
                edges_by_id,
                GraphEdge(
                    id=_edge_id(EdgeType.AFFECTED_EVAL, error_node_id, eval_node_id),
                    source=error_node_id,
                    target=eval_node_id,
                    type=EdgeType.AFFECTED_EVAL,
                    confidence=1.0,
                    evidence=[
                        stderr or f"returncode={returncode}",
                        grader.get("notes", ""),
                    ],
                ),
            )

    for prev_id, next_id in zip(command_node_ids, command_node_ids[1:]):
        _add_edge_once(
            edges_by_id,
            GraphEdge(
                id=_edge_id(EdgeType.PRECEDES, prev_id, next_id),
                source=prev_id,
                target=next_id,
                type=EdgeType.PRECEDES,
                confidence=1.0,
                evidence=["step order"],
            ),
        )

    if failed_command_ids:
        first_failed_command_id = failed_command_ids[0]
        first_error_node_id = error_node_ids[0] if error_node_ids else None
        evidence = [grader.get("notes", "")]
        if first_error_node_id:
            evidence.append(nodes_by_id[first_error_node_id].attrs.get("stderr", ""))

        _add_edge_once(
            edges_by_id,
            GraphEdge(
                id=_edge_id(
                    EdgeType.SUSPECTED_CAUSES,
                    first_failed_command_id,
                    eval_node_id,
                    "first_failed_command",
                ),
                source=first_failed_command_id,
                target=eval_node_id,
                type=EdgeType.SUSPECTED_CAUSES,
                confidence=0.7,
                evidence=[e for e in evidence if e],
                attrs={"reason": "first non-zero returncode command"},
            ),
        )

    return BioCausalGraph(
        task_id=task_id,
        run_id=run_id,
        nodes=list(nodes_by_id.values()),
        edges=list(edges_by_id.values()),
        metadata={
            "builder": "deterministic_provenance_v0",
            "num_steps": len(steps),
        },
    )
