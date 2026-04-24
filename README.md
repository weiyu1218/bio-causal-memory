# bio-causal-memory

Workflow-level causal provenance memory for bioinformatics agents.

This project builds a typed provenance graph from bioinformatics agent execution traces and retrieves minimal causal evidence paths for failure analysis and repair.

## Scope

This project does not build biological causal graphs, gene regulatory networks, or expression-matrix causal discovery systems.

It builds workflow-level causal provenance graphs over:

- task
- input data
- reference data
- tool
- command
- parameter
- artifact
- log
- error
- grader result

## v0 Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

pytest

bash experiments/001_build_toy_graph.sh
bash experiments/002_query_toy_failure.sh
```

Expected query output:

```text
Likely failure cause:
The run likely failed because a quantification command used `wrong_index`, while the available index artifact was `salmon_index/`.

Evidence path:
...
Minimal repair suggestion:
Replace `-i wrong_index` with `-i salmon_index` in the `salmon quant` command.
```

## External Repositories

The `external/` directory contains read-only reference repositories:

- BioAgent Bench
- MAGMA / MAMGA
- AMA-Bench
- Bio-Task Bench

Do not modify files under `external/`.
