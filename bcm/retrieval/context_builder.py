from __future__ import annotations

import re
import shlex
from typing import Any, Dict, List

from bcm.graph.schema import BioCausalGraph, EdgeType, NodeType


def _shorten(text: str, limit: int = 240) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _format_value(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _command_tokens(cmd: str) -> List[str]:
    try:
        return shlex.split(cmd)
    except ValueError:
        return cmd.split()


def _extract_index_arg(cmd: str) -> str:
    tokens = _command_tokens(cmd)
    for idx, token in enumerate(tokens[:-1]):
        if token == "-i":
            return tokens[idx + 1]
    return ""


def _clean_path(path: str) -> str:
    return path.strip().strip("`'\".,;:").rstrip("/")


def _candidate_index_artifacts(
    evidence_nodes: List[Any],
    failed_step_id: int,
) -> List[str]:
    candidates = []
    for node in evidence_nodes:
        if node.type != NodeType.ARTIFACT:
            continue
        path = _clean_path(node.attrs.get("path", node.label))
        if "index" not in path.lower():
            continue
        created_by_step = node.attrs.get("created_by_step")
        if created_by_step is not None and created_by_step >= failed_step_id:
            continue
        candidates.append((created_by_step if created_by_step is not None else -1, path))

    candidates.sort(reverse=True)
    return [path for _step_id, path in candidates]


def _index_from_grader_notes(evals: List[Any]) -> str:
    for eval_node in evals:
        notes = eval_node.attrs.get("notes", "")
        match = re.search(r"instead of\s+([A-Za-z0-9_./-]+)", notes)
        if match:
            return _clean_path(match.group(1))
    return ""


def _replacement_index_hint(
    failed_commands: List[Any],
    evidence_nodes: List[Any],
    evals: List[Any],
) -> tuple[str, str]:
    if not failed_commands:
        return "", ""

    failed_command = failed_commands[0]
    cmd = failed_command.attrs.get("cmd", failed_command.label)
    bad_index = _clean_path(_extract_index_arg(cmd))
    if not bad_index:
        return "", ""

    failed_step_id = failed_command.attrs.get("step_id", 0)
    artifact_candidates = _candidate_index_artifacts(evidence_nodes, failed_step_id)
    if artifact_candidates:
        return bad_index, artifact_candidates[0]

    noted_index = _index_from_grader_notes(evals)
    if noted_index:
        return bad_index, noted_index

    if bad_index.endswith("wrong_index"):
        return bad_index, _clean_path(bad_index[: -len("wrong_index")] + "index")

    return bad_index, ""


def build_context(graph: BioCausalGraph, retrieval_result: Dict[str, object]) -> str:
    node_by_id = {node.id: node for node in graph.nodes}
    edge_by_id = {edge.id: edge for edge in graph.edges}

    evidence_node_ids = set(retrieval_result.get("evidence_nodes", []))
    evidence_edge_ids = set(retrieval_result.get("evidence_edges", []))

    evidence_nodes = [node_by_id[nid] for nid in evidence_node_ids if nid in node_by_id]
    evidence_edges = [edge_by_id[eid] for eid in evidence_edge_ids if eid in edge_by_id]

    failed_commands = sorted(
        [
            node
            for node in evidence_nodes
            if node.type == NodeType.COMMAND and node.attrs.get("returncode", 0) != 0
        ],
        key=lambda n: n.attrs.get("step_id", 0),
    )
    errors = sorted(
        [node for node in evidence_nodes if node.type == NodeType.ERROR],
        key=lambda n: n.attrs.get("step_id", 0),
    )
    evals = [node for node in evidence_nodes if node.type == NodeType.EVAL]
    produced_artifacts = [
        node for node in evidence_nodes if node.type == NodeType.ARTIFACT
    ]
    logs = sorted(
        [node for node in evidence_nodes if node.type == NodeType.LOG],
        key=lambda n: n.attrs.get("step_id", 0),
    )
    failed_step_ids = {node.attrs.get("step_id") for node in failed_commands}
    bad_index, replacement_index = _replacement_index_hint(
        failed_commands,
        evidence_nodes,
        evals,
    )

    lines: List[str] = []

    lines.append("Likely failure cause:")

    if failed_commands:
        cmd = failed_commands[0].attrs.get("cmd", failed_commands[0].label)
        stderr = ""
        if errors:
            stderr = errors[0].attrs.get("stderr", "")
        if bad_index and replacement_index:
            lines.append(
                f"The run likely failed because a quantification command used `{bad_index}`, while the available index artifact was `{replacement_index}`."
            )
        elif bad_index or "wrong_index" in cmd or "wrong_index" in stderr:
            lines.append(
                f"The run likely failed because a quantification command used `{bad_index or 'wrong_index'}`."
            )
        else:
            lines.append(
                f"The run likely failed at command: `{cmd}`."
            )
    elif errors:
        stderr = errors[0].attrs.get("stderr", errors[0].label)
        lines.append(f"The run likely failed due to error: `{_shorten(stderr)}`.")
    else:
        lines.append("The failure cause is unclear from the available graph evidence.")

    lines.append("")
    lines.append("Evidence path:")

    ordered_commands = sorted(
        [node for node in evidence_nodes if node.type == NodeType.COMMAND],
        key=lambda n: n.attrs.get("step_id", 0),
    )
    for node in ordered_commands:
        step_id = node.attrs.get("step_id", "?")
        cmd = node.attrs.get("cmd", node.label)
        returncode = node.attrs.get("returncode", 0)
        lines.append(f"- Step {step_id} command: `{cmd}`; returncode={returncode}.")

    for artifact in produced_artifacts:
        lines.append(f"- Produced artifact: `{artifact.label}`.")

    for error in errors:
        step_id = error.attrs.get("step_id", "?")
        stderr = error.attrs.get("stderr", "")
        lines.append(f"- Step {step_id} error: `{_shorten(stderr)}`.")

    for log in logs:
        step_id = log.attrs.get("step_id", "?")
        if step_id not in failed_step_ids:
            continue
        stdout = log.attrs.get("stdout", "")
        stderr = log.attrs.get("stderr", "")
        if stderr:
            lines.append(f"- Step {step_id} log stderr: `{_shorten(stderr)}`.")
        elif stdout:
            lines.append(f"- Step {step_id} log stdout: `{_shorten(stdout)}`.")

    for eval_node in evals:
        final_result = eval_node.attrs.get("final_result_reached")
        results_match = eval_node.attrs.get("results_match")
        notes = eval_node.attrs.get("notes", "")
        lines.append(
            f"- Grader result: final_result_reached={_format_value(final_result)}, results_match={_format_value(results_match)}."
        )
        if notes:
            lines.append(f"- Grader notes: {_shorten(notes)}")

    suspected_edges = [edge for edge in evidence_edges if edge.type == EdgeType.SUSPECTED_CAUSES]
    for edge in suspected_edges:
        for ev in edge.evidence:
            if ev:
                lines.append(f"- Suspected cause evidence: {_shorten(ev)}")

    lines.append("")
    lines.append("Minimal repair suggestion:")

    if bad_index and replacement_index:
        lines.append(
            f"Replace `-i {bad_index}` with `-i {replacement_index}` in the `salmon quant` command."
        )
    elif errors:
        lines.append("Inspect the first non-zero-returncode command and rerun from that step after fixing the stderr-reported issue.")
    else:
        lines.append("Inspect the earliest failed command and verify that all required input artifacts exist.")

    return "\n".join(lines)
