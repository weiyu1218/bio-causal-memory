# bio-causal-memory

Workflow-level causal provenance memory for bioinformatics agents.

The project builds typed provenance graphs from bioinformatics agent execution traces and retrieves minimal evidence paths for failure analysis and repair. It models workflow execution provenance, not biological causality.

## Scope

This project does not build biological causal graphs, gene regulatory networks, expression-matrix causal discovery systems, LLM causal labelers, graph databases, or web UI surfaces.

It represents workflow-level evidence over:

- task
- input data
- reference data
- tool
- command
- artifact
- log
- error
- grader result

## Current Architecture

The CLI entrypoint is `bcm.cli`.

`build-graph` loads task metadata and a run trace, normalizes the trace schema, builds a deterministic provenance graph, and stores the graph as JSON.

`query` loads a stored graph, retrieves local failure evidence, and renders a concise answer with the likely failure cause, evidence path, grader evidence, log evidence, and repair suggestion.

Core modules:

- `bcm.ingest.bioagent_loader`: loads local task metadata JSON.
- `bcm.ingest.bioagent_task_adapter`: extracts task metadata from `external/bioagent-bench/tasks/<task_id>/`.
- `bcm.ingest.trace_loader`: validates canonical trace JSON.
- `bcm.ingest.trace_normalizer`: accepts canonical `steps` traces and simplified `shell_steps` traces.
- `bcm.graph.schema`: defines node, edge, and graph data models.
- `bcm.graph.provenance_builder`: converts task metadata plus trace steps into typed graph nodes and edges.
- `bcm.graph.graph_store`: saves and loads graph JSON.
- `bcm.retrieval.anchor_finder`: infers query intent and selects failure anchors.
- `bcm.retrieval.causal_traversal`: traverses local evidence edges around failures.
- `bcm.retrieval.context_builder`: formats minimal failure context and repair guidance.

## Data Flow

```text
task metadata JSON or BioAgent-Bench task directory
        +
canonical trace JSON or shell-step trace JSON
        |
        v
ingest loaders and trace normalizer
        |
        v
deterministic provenance builder
        |
        v
BioCausalGraph JSON
        |
        v
failure query retrieval
        |
        v
minimal evidence path and repair suggestion
```

## Graph Model

The graph uses stable node and edge identifiers. Deterministic provenance edges use `confidence=1.0`. Rule-derived failure-cause edges use lower confidence values.

Primary node types:

- `TASK`
- `INPUT_DATA`
- `REFERENCE_DATA`
- `TOOL`
- `COMMAND`
- `ARTIFACT`
- `LOG`
- `ERROR`
- `EVAL`

Primary edge types:

- `USES`
- `USES_REFERENCE`
- `USES_TOOL`
- `HAS_LOG`
- `PRODUCES`
- `PRECEDES`
- `FAILED_WITH`
- `AFFECTED_EVAL`
- `SUSPECTED_CAUSES`

## Trace Semantics

Canonical traces contain:

- `task_id`
- `run_id`
- `steps`
- `grader`

Each step contains command text, stdout, stderr, return code, working directory, timestamps, and file snapshots before and after the step.

Simplified shell-step traces are normalized into the canonical schema by mapping:

- `shell_steps[].command` to `steps[].cmd`
- `shell_steps[].exit_code` to `steps[].returncode`
- `shell_steps[].index` to `steps[].step_id`

## Retrieval Semantics

Failure queries anchor on error nodes, failed command nodes, or grader nodes. Traversal follows deterministic workflow evidence, including command, tool, artifact, log, error, evaluation, and step-order edges.

The context builder sorts failed commands and errors by `step_id`, so the earliest failed step is prioritized. Repair hints are derived from the failed command and observed evidence, such as an invalid Salmon index argument and the index artifact produced by an earlier step.

## External Repositories

The `external/` directory contains read-only reference repositories:

- BioAgent Bench
- MAGMA / MAMGA
- AMA-Bench
- Bio-Task Bench

Project code must live under `bcm/`. Files under `external/` are reference inputs and must not be modified.
