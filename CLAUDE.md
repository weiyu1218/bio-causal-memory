# Claude Code Instructions for bio-causal-memory

## Project Scope

This project builds a workflow-level causal provenance memory system for bioinformatics agents.

This project does NOT build biological causal graphs, gene regulatory networks, or expression-matrix causal discovery systems.

## Allowed Node Types

- TASK
- INPUT_DATA
- REFERENCE_DATA
- TOOL
- COMMAND
- PARAMETER
- ARTIFACT
- LOG
- ERROR
- EVAL
- ENTITY

## Allowed Edge Types

- USES
- USES_REFERENCE
- USES_TOOL
- HAS_PARAM
- HAS_LOG
- PRODUCES
- READS
- DERIVED_FROM
- PRECEDES
- REQUIRES
- FAILED_WITH
- AFFECTED_EVAL
- SUSPECTED_CAUSES
- SEMANTICALLY_RELATED

## Hard Prohibitions

Do not implement:
- gene-gene causal discovery
- GRN inference
- pairwise biological causal graph construction
- causal discovery on expression matrices
- full pairwise LLM causal edge inference
- modifications inside external repositories

## v0 Goal

Build a deterministic provenance graph from a run trace JSON.

Minimum expected workflow:

1. Load task metadata.
2. Load run trace JSON.
3. Create typed nodes and edges.
4. Save graph JSON.
5. Query graph with "why did the run fail?"
6. Return a minimal evidence path.

## Implementation Preferences

- Use Python 3.10+
- Use Pydantic for schemas
- Use NetworkX for graph operations
- Store v0 graphs as JSON
- Use no database in v0
- Use no LLM call in v0
- Use small fixtures first

## External Repositories

The following external repositories are read-only references:

- external/bioagent-bench
- external/MAGMA or external/MAMGA
- external/AMA-Bench
- external/bioTaskBench

Do not modify files inside external/.
