from __future__ import annotations

from typing import Dict, List

from bcm.graph.schema import BioCausalGraph, EdgeType, NodeType


def _shorten(text: str, limit: int = 240) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def build_context(graph: BioCausalGraph, retrieval_result: Dict[str, object]) -> str:
    node_by_id = {node.id: node for node in graph.nodes}
    edge_by_id = {edge.id: edge for edge in graph.edges}

    evidence_node_ids = set(retrieval_result.get("evidence_nodes", []))
    evidence_edge_ids = set(retrieval_result.get("evidence_edges", []))

    evidence_nodes = [node_by_id[nid] for nid in evidence_node_ids if nid in node_by_id]
    evidence_edges = [edge_by_id[eid] for eid in evidence_edge_ids if eid in edge_by_id]

    failed_commands = [
        node
        for node in evidence_nodes
        if node.type == NodeType.COMMAND and node.attrs.get("returncode", 0) != 0
    ]
    errors = [node for node in evidence_nodes if node.type == NodeType.ERROR]
    evals = [node for node in evidence_nodes if node.type == NodeType.EVAL]
    produced_artifacts = [
        node for node in evidence_nodes if node.type == NodeType.ARTIFACT
    ]

    lines: List[str] = []

    lines.append("Likely failure cause:")

    if failed_commands:
        cmd = failed_commands[0].attrs.get("cmd", failed_commands[0].label)
        stderr = ""
        if errors:
            stderr = errors[0].attrs.get("stderr", "")
        if "wrong_index" in cmd or "wrong_index" in stderr:
            lines.append(
                "The run likely failed because a quantification command used `wrong_index`, while the available index artifact was `salmon_index/`."
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

    for eval_node in evals:
        final_result = eval_node.attrs.get("final_result_reached")
        results_match = eval_node.attrs.get("results_match")
        notes = eval_node.attrs.get("notes", "")
        lines.append(
            f"- Grader result: final_result_reached={final_result}, results_match={results_match}."
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

    text_blob = "\n".join(lines)
    if "wrong_index" in text_blob and "salmon_index" in text_blob:
        lines.append("Replace `-i wrong_index` with `-i salmon_index` in the `salmon quant` command.")
    elif errors:
        lines.append("Inspect the first non-zero-returncode command and rerun from that step after fixing the stderr-reported issue.")
    else:
        lines.append("Inspect the earliest failed command and verify that all required input artifacts exist.")

    return "\n".join(lines)
