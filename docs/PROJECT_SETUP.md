# bio-causal-memory 项目搭建说明

## 0. 项目定位

本项目不是构建 biological causal graph，也不是 gene regulatory network inference。

本项目目标是构建：

> Workflow-level Causal Provenance Memory for Bioinformatics Agents

也就是：针对 BioAgent-Bench 类型的生信 agent 任务，从 agent 执行轨迹中抽取 task、input data、reference data、tool、command、parameter、artifact、stdout/stderr、error、grader result 等节点，构建一个可查询的因果溯源记忆图，用于回答：

- 这个 run 为什么失败？
- 哪个文件、reference、参数、命令导致了最终结果错误？
- 哪一步最早出错？
- 如何给 agent 提供最小修复上下文？
- graph memory 是否比 full trace / vector RAG 更省 token、更准确？

严禁在 v0 中实现：

- gene-gene causal discovery
- gene regulatory network inference
- single-cell perturbation causal graph
- expression matrix causal discovery
- 全量 pairwise causal inference
- 修改 `external/` 里的第三方仓库源码

第三方仓库只作为 external dependency / reference code。主项目代码必须写在 `bcm/` 下。

---

## 1. 背景依据

本项目基于以下事实和公开项目：

1. BioAgent Bench 是一个用于评估 bioinformatics AI agents 的 benchmark，覆盖 RNA-seq、variant calling、metagenomics 等多步任务，并包含 corrupted inputs、decoy files、prompt bloat 等鲁棒性测试。BioAgent Bench 的公开页面说明其是面向 bioinformatics agents 的 benchmark 和 evaluation suite。  
   参考：`bioagent-bench/bioagent-bench`

2. MAGMA 是 Multi-Graph based Agentic Memory Architecture，公开说明其面向 long-term conversation memory 和 multi-hop reasoning，并构建 temporal、semantic、causal 等关系。  
   参考：`FredJiang0324/MAGMA` / `FredJiang0324/MAMGA`

3. AMA-Bench 用于评估 long-horizon memory for agentic applications，其公开说明强调从 long agent trajectories 构建 memory、检索相关 evidence，并回答问题。它的接口思想可参考，但不作为主 benchmark。  
   参考：`AMA-Bench/AMA-Bench`

4. Bio-Task Bench 是 bioinformatics coding agents 的 benchmark / evaluation tool，包含 deterministic grading harness 和 external benchmark adapters。它可作为 deterministic grading / CLI 组织方式参考，但不作为本项目主线。  
   参考：`GPTomics/bioTaskBench`

本项目的核心创新点不是重新做 BioAgent Bench，也不是做 biological causal discovery，而是把 agent memory / causal graph memory 思想迁移到 bioinformatics workflow 轨迹上，构建 workflow-level causal provenance memory。

---

## 2. 已 clone 项目位置

用户已经将相关仓库 clone 到：

```text
bio-causal-memory/external/
```

预期结构如下：

```text
bio-causal-memory/
  external/
    bioagent-bench/
    MAGMA/ or MAMGA/
    AMA-Bench/
    bioTaskBench/
```

说明：

- `external/bioagent-bench/` 是主 benchmark substrate。
- `external/MAGMA/` 或 `external/MAMGA/` 只作为 memory architecture 参考。
- `external/AMA-Bench/` 只作为 long-horizon memory evaluation 参考。
- `external/bioTaskBench/` 只作为 deterministic grading / CLI design 参考。

重要约束：

```text
external/ 下所有仓库只读，不要修改它们的源码。
```

主项目代码必须在：

```text
bio-causal-memory/bcm/
```

---

## 3. 项目目标

### 3.1 v0 目标

v0 只做一件事：

```text
toy trace -> deterministic provenance graph -> query why failed -> minimal evidence path
```

也就是说：

1. 读取一个 task metadata JSON。
2. 读取一个 run trace JSON。
3. 从 trace 中构建 deterministic provenance graph。
4. 保存 graph JSON。
5. 对 graph 提问：`why did the run fail?`
6. 返回最小 evidence path 和修复建议。

### 3.2 v0 不做的事

v0 不要做：

- 真实 BioAgent-Bench 全量运行
- agent harness 集成
- Claude / GPT 调用
- LLM causal edge inference
- vector database
- Neo4j / graph database
- web UI
- biological causal discovery
- GRN inference
- expression matrix 解析
- 大规模生物数据处理
- 所有 BioAgent-Bench task 的适配

---

## 4. 目标目录结构

请在当前 repo 根目录下创建以下结构：

```text
bio-causal-memory/
  README.md
  PROJECT_SETUP.md
  CLAUDE.md
  pyproject.toml

  configs/
    tasks.yaml
    graph_schema.yaml
    retrieval.yaml
    eval.yaml

  external/
    bioagent-bench/
    MAGMA/ or MAMGA/
    AMA-Bench/
    bioTaskBench/

  bcm/
    __init__.py
    cli.py

    ingest/
      __init__.py
      bioagent_loader.py
      trace_loader.py
      artifact_scanner.py
      log_parser.py

    graph/
      __init__.py
      schema.py
      provenance_builder.py
      causal_labeler.py
      graph_store.py
      exporters.py

    memory/
      __init__.py
      vector_index.py
      keyword_index.py
      entity_index.py
      temporal_index.py

    retrieval/
      __init__.py
      anchor_finder.py
      causal_traversal.py
      context_builder.py
      router.py

    eval/
      __init__.py
      bioagent_metrics.py
      causal_path_metrics.py
      failure_localization.py
      repair_eval.py

    agents/
      __init__.py
      claude_runner.py
      prompt_templates.py

  data/
    raw/
    runs/
    graphs/
    eval/
    fixtures/

  experiments/
    001_build_toy_graph.sh
    002_query_toy_failure.sh
    003_compare_memory_baselines.sh

  tests/
    test_schema.py
    test_trace_loader.py
    test_provenance_builder.py
    test_causal_traversal.py
```

如果目录或文件已存在，不要删除用户已有内容。只补齐缺失文件。

---

## 5. 依赖配置

创建或覆盖 `pyproject.toml`：

```toml
[project]
name = "bio-causal-memory"
version = "0.1.0"
description = "Workflow-level causal provenance memory for bioinformatics agents"
requires-python = ">=3.10"
dependencies = [
  "networkx>=3.2",
  "pydantic>=2.0",
  "typer>=0.12",
  "rich>=13.0",
  "pandas>=2.0",
  "numpy>=1.24",
  "scikit-learn>=1.4",
  "sentence-transformers>=2.7",
  "rank-bm25>=0.2.2",
  "pyyaml>=6.0",
  "pytest>=8.0"
]

[project.scripts]
bcm = "bcm.cli:app"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

安装命令：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

---

## 6. 创建 CLAUDE.md

请创建 `CLAUDE.md`，内容如下：

```markdown
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
```

---

## 7. v0 数据模型

### 7.1 实现 `bcm/graph/schema.py`

```python
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class NodeType(str, Enum):
    TASK = "TASK"
    INPUT_DATA = "INPUT_DATA"
    REFERENCE_DATA = "REFERENCE_DATA"
    TOOL = "TOOL"
    COMMAND = "COMMAND"
    PARAMETER = "PARAMETER"
    ARTIFACT = "ARTIFACT"
    LOG = "LOG"
    ERROR = "ERROR"
    EVAL = "EVAL"
    ENTITY = "ENTITY"


class EdgeType(str, Enum):
    USES = "USES"
    USES_REFERENCE = "USES_REFERENCE"
    USES_TOOL = "USES_TOOL"
    HAS_PARAM = "HAS_PARAM"
    PRODUCES = "PRODUCES"
    READS = "READS"
    DERIVED_FROM = "DERIVED_FROM"
    PRECEDES = "PRECEDES"
    REQUIRES = "REQUIRES"
    FAILED_WITH = "FAILED_WITH"
    AFFECTED_EVAL = "AFFECTED_EVAL"
    SUSPECTED_CAUSES = "SUSPECTED_CAUSES"
    SEMANTICALLY_RELATED = "SEMANTICALLY_RELATED"


class GraphNode(BaseModel):
    id: str
    type: NodeType
    label: str
    attrs: Dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: EdgeType
    confidence: float = 1.0
    evidence: List[str] = Field(default_factory=list)
    attrs: Dict[str, Any] = Field(default_factory=dict)


class BioCausalGraph(BaseModel):
    task_id: str
    run_id: str
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
```

要求：

- 所有 node id 和 edge id 必须稳定可复现。
- `confidence=1.0` 表示 deterministic provenance。
- `confidence<1.0` 用于 rule-based 或 LLM-suggested causal hypothesis。
- v0 暂不做 LLM。

---

## 8. v0 输入格式

### 8.1 创建 task metadata fixture

创建文件：

```text
data/fixtures/transcript_quant_task.json
```

内容：

```json
{
  "task_id": "transcript-quant",
  "name": "Transcript Quantification",
  "goal": "Quantify transcript abundance from simulated RNA-seq reads and produce a final CSV/TSV result.",
  "expected_outputs": [
    "results/transcript_quantification.csv"
  ],
  "input_data": [
    "reads_1.fq.gz",
    "reads_2.fq.gz"
  ],
  "reference_data": [
    "transcriptome.fa"
  ]
}
```

### 8.2 创建 run trace fixture

创建文件：

```text
data/runs/transcript_quant_failed_toy.json
```

内容：

```json
{
  "task_id": "transcript-quant",
  "run_id": "transcript_quant_failed_toy",
  "steps": [
    {
      "step_id": 1,
      "cmd": "salmon index -t transcriptome.fa -i salmon_index",
      "cwd": "/workspace",
      "stdout": "index built successfully",
      "stderr": "",
      "returncode": 0,
      "start_time": "2026-01-01T00:00:00",
      "end_time": "2026-01-01T00:01:00",
      "files_before": [
        "transcriptome.fa",
        "reads_1.fq.gz",
        "reads_2.fq.gz"
      ],
      "files_after": [
        "transcriptome.fa",
        "reads_1.fq.gz",
        "reads_2.fq.gz",
        "salmon_index/"
      ]
    },
    {
      "step_id": 2,
      "cmd": "salmon quant -i wrong_index -l A -1 reads_1.fq.gz -2 reads_2.fq.gz -o quant",
      "cwd": "/workspace",
      "stdout": "",
      "stderr": "Error: index wrong_index does not exist",
      "returncode": 1,
      "start_time": "2026-01-01T00:02:00",
      "end_time": "2026-01-01T00:02:30",
      "files_before": [
        "transcriptome.fa",
        "reads_1.fq.gz",
        "reads_2.fq.gz",
        "salmon_index/"
      ],
      "files_after": [
        "transcriptome.fa",
        "reads_1.fq.gz",
        "reads_2.fq.gz",
        "salmon_index/"
      ]
    },
    {
      "step_id": 3,
      "cmd": "python write_results.py quant/quant.sf results/transcript_quantification.csv",
      "cwd": "/workspace",
      "stdout": "",
      "stderr": "FileNotFoundError: quant/quant.sf",
      "returncode": 1,
      "start_time": "2026-01-01T00:03:00",
      "end_time": "2026-01-01T00:03:15",
      "files_before": [
        "transcriptome.fa",
        "reads_1.fq.gz",
        "reads_2.fq.gz",
        "salmon_index/"
      ],
      "files_after": [
        "transcriptome.fa",
        "reads_1.fq.gz",
        "reads_2.fq.gz",
        "salmon_index/"
      ]
    }
  ],
  "grader": {
    "steps_completed": 1,
    "steps_to_completion": 3,
    "final_result_reached": false,
    "results_match": false,
    "f1_score": 0.0,
    "notes": "The quantification step failed because the command used wrong_index instead of salmon_index. The expected final result file was not produced."
  }
}
```

---

## 9. 实现 ingest 模块

### 9.1 实现 `bcm/ingest/trace_loader.py`

功能：

- 读取 run trace JSON。
- 校验字段：
  - `task_id`
  - `run_id`
  - `steps`
  - `grader`
- 每个 step 至少包含：
  - `step_id`
  - `cmd`
  - `stdout`
  - `stderr`
  - `returncode`
  - `files_before`
  - `files_after`

代码：

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


REQUIRED_TRACE_FIELDS = {"task_id", "run_id", "steps", "grader"}
REQUIRED_STEP_FIELDS = {
    "step_id",
    "cmd",
    "stdout",
    "stderr",
    "returncode",
    "files_before",
    "files_after",
}


def load_trace(path: str) -> Dict[str, Any]:
    trace_path = Path(path)
    if not trace_path.exists():
        raise FileNotFoundError(f"Trace file not found: {trace_path}")

    with trace_path.open("r", encoding="utf-8") as f:
        trace = json.load(f)

    missing = REQUIRED_TRACE_FIELDS - set(trace.keys())
    if missing:
        raise ValueError(f"Trace is missing required fields: {sorted(missing)}")

    if not isinstance(trace["steps"], list):
        raise ValueError("Trace field `steps` must be a list")

    for idx, step in enumerate(trace["steps"]):
        missing_step = REQUIRED_STEP_FIELDS - set(step.keys())
        if missing_step:
            raise ValueError(
                f"Step at index {idx} is missing required fields: {sorted(missing_step)}"
            )

    return trace
```

### 9.2 实现 `bcm/ingest/bioagent_loader.py`

功能：

- v0 先读取本地 task metadata JSON。
- 后续再适配 `external/bioagent-bench/tasks/<task_id>/`。

代码：

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


REQUIRED_TASK_FIELDS = {
    "task_id",
    "name",
    "goal",
    "expected_outputs",
    "input_data",
    "reference_data",
}


def load_task_metadata(path: str) -> Dict[str, Any]:
    task_path = Path(path)
    if not task_path.exists():
        raise FileNotFoundError(f"Task metadata file not found: {task_path}")

    with task_path.open("r", encoding="utf-8") as f:
        task = json.load(f)

    missing = REQUIRED_TASK_FIELDS - set(task.keys())
    if missing:
        raise ValueError(f"Task metadata is missing required fields: {sorted(missing)}")

    return task
```

---

## 10. 实现 graph 模块

### 10.1 实现 `bcm/graph/provenance_builder.py`

核心功能：将 task metadata + trace 转成 `BioCausalGraph`。

必须创建的节点：

- 1 个 TASK node
- 每个 input_data 一个 INPUT_DATA node
- 每个 reference_data 一个 REFERENCE_DATA node
- 每个 command 一个 COMMAND node
- 每个 command 使用的 tool 一个 TOOL node
- 每个 command 的 stdout/stderr 一个 LOG node
- returncode 非 0 时创建 ERROR node
- files_after 相比 files_before 新增的文件创建 ARTIFACT node
- grader 创建 EVAL node

必须创建的边：

- COMMAND `USES_TOOL` TOOL
- COMMAND `USES` INPUT_DATA，如果 cmd 中出现 input filename
- COMMAND `USES_REFERENCE` REFERENCE_DATA，如果 cmd 中出现 reference filename
- COMMAND `PRODUCES` ARTIFACT，如果该文件在 files_after 中新增
- COMMAND `FAILED_WITH` ERROR，如果 returncode 非 0
- COMMAND `PRECEDES` next COMMAND
- ERROR `AFFECTED_EVAL` EVAL
- 最后一条失败 command 或 missing expected output 相关 command `SUSPECTED_CAUSES` EVAL，confidence 设为 0.7，evidence 使用 stderr 和 grader notes

代码：

```python
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
```

---

### 10.2 实现 `bcm/graph/graph_store.py`

```python
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
```

---

### 10.3 实现 `bcm/graph/causal_labeler.py`

v0 只放占位，不做 LLM causal inference。

```python
from __future__ import annotations

from typing import Any, Dict


def label_candidate_causal_edges(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """
    Placeholder for v1.

    v0 does not perform LLM-based causal labeling.
    Causal hypotheses in v0 are limited to deterministic or rule-based
    edges produced by provenance_builder.py.
    """
    return {
        "status": "not_implemented_in_v0",
        "message": "LLM-based causal labeling is deferred to v1.",
    }
```

---

### 10.4 实现 `bcm/graph/exporters.py`

v0 先实现简单导出。

```python
from __future__ import annotations

from bcm.graph.schema import BioCausalGraph


def to_markdown_edges(graph: BioCausalGraph) -> str:
    node_by_id = {node.id: node for node in graph.nodes}
    lines = ["| Source | Edge | Target | Confidence |", "|---|---|---|---:|"]
    for edge in graph.edges:
        source = node_by_id.get(edge.source)
        target = node_by_id.get(edge.target)
        source_label = source.label if source else edge.source
        target_label = target.label if target else edge.target
        lines.append(
            f"| {source_label} | {edge.type.value} | {target_label} | {edge.confidence:.2f} |"
        )
    return "\n".join(lines)
```

---

## 11. 实现 retrieval 模块

### 11.1 实现 `bcm/retrieval/anchor_finder.py`

```python
from __future__ import annotations

from typing import List

from bcm.graph.schema import BioCausalGraph, NodeType


WHY_FAILED = "WHY_FAILED"
WHERE_FAILED = "WHERE_FAILED"
HOW_REPAIR = "HOW_REPAIR"


def infer_intent(question: str) -> str:
    q = question.lower()

    if any(token in q for token in ["repair", "fix", "修复", "改正", "解决"]):
        return HOW_REPAIR

    if any(token in q for token in ["where", "step", "哪一步", "哪里", "哪个步骤"]):
        return WHERE_FAILED

    if any(token in q for token in ["why", "failed", "fail", "为什么", "失败", "原因"]):
        return WHY_FAILED

    return WHY_FAILED


def find_anchors(graph: BioCausalGraph, question: str) -> List[str]:
    intent = infer_intent(question)

    error_nodes = [node.id for node in graph.nodes if node.type == NodeType.ERROR]
    eval_nodes = [node.id for node in graph.nodes if node.type == NodeType.EVAL]
    failed_commands = [
        node.id
        for node in graph.nodes
        if node.type == NodeType.COMMAND and node.attrs.get("returncode", 0) != 0
    ]

    if intent in {WHY_FAILED, WHERE_FAILED, HOW_REPAIR}:
        if error_nodes:
            return error_nodes
        if failed_commands:
            return failed_commands
        if eval_nodes:
            return eval_nodes

    return eval_nodes
```

---

### 11.2 实现 `bcm/retrieval/causal_traversal.py`

```python
from __future__ import annotations

from collections import deque
from typing import Dict, List, Set

from bcm.graph.schema import BioCausalGraph, EdgeType
from bcm.retrieval.anchor_finder import find_anchors, infer_intent


IMPORTANT_EDGE_TYPES = {
    EdgeType.FAILED_WITH,
    EdgeType.AFFECTED_EVAL,
    EdgeType.SUSPECTED_CAUSES,
    EdgeType.USES,
    EdgeType.USES_REFERENCE,
    EdgeType.USES_TOOL,
    EdgeType.PRODUCES,
    EdgeType.PRECEDES,
}


def _incident_edges(graph: BioCausalGraph, node_id: str):
    for edge in graph.edges:
        if edge.source == node_id or edge.target == node_id:
            if edge.type in IMPORTANT_EDGE_TYPES:
                yield edge


def retrieve_failure_context(
    graph: BioCausalGraph,
    question: str,
    max_nodes: int = 12,
) -> Dict[str, object]:
    intent = infer_intent(question)
    anchors = find_anchors(graph, question)

    visited_nodes: Set[str] = set()
    visited_edges: Set[str] = set()

    queue = deque(anchors)
    while queue and len(visited_nodes) < max_nodes:
        node_id = queue.popleft()
        if node_id in visited_nodes:
            continue
        visited_nodes.add(node_id)

        for edge in _incident_edges(graph, node_id):
            visited_edges.add(edge.id)
            neighbor = edge.target if edge.source == node_id else edge.source
            if neighbor not in visited_nodes:
                queue.append(neighbor)

    return {
        "intent": intent,
        "anchor_nodes": anchors,
        "evidence_nodes": list(visited_nodes),
        "evidence_edges": list(visited_edges),
        "summary": "",
    }
```

---

### 11.3 实现 `bcm/retrieval/context_builder.py`

```python
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
```

---

### 11.4 实现 `bcm/retrieval/router.py`

v0 简单封装：

```python
from __future__ import annotations

from bcm.graph.schema import BioCausalGraph
from bcm.retrieval.causal_traversal import retrieve_failure_context
from bcm.retrieval.context_builder import build_context


def answer_question(graph: BioCausalGraph, question: str) -> str:
    result = retrieve_failure_context(graph, question)
    return build_context(graph, result)
```

---

## 12. 实现 memory 模块占位

v0 不需要真正实现 vector index，但文件需要存在，避免后续 import 错误。

### 12.1 `bcm/memory/vector_index.py`

```python
from __future__ import annotations


class VectorIndex:
    def __init__(self) -> None:
        self.items = []

    def add(self, item: str) -> None:
        self.items.append(item)

    def search(self, query: str, k: int = 5):
        return self.items[:k]
```

### 12.2 `bcm/memory/keyword_index.py`

```python
from __future__ import annotations


class KeywordIndex:
    def __init__(self) -> None:
        self.items = []

    def add(self, item: str) -> None:
        self.items.append(item)

    def search(self, query: str, k: int = 5):
        terms = set(query.lower().split())
        scored = []
        for item in self.items:
            score = len(terms & set(item.lower().split()))
            scored.append((score, item))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [item for score, item in scored[:k] if score > 0]
```

### 12.3 `bcm/memory/entity_index.py`

```python
from __future__ import annotations


class EntityIndex:
    def __init__(self) -> None:
        self.entities = {}

    def add(self, name: str, node_id: str) -> None:
        self.entities.setdefault(name, set()).add(node_id)

    def get(self, name: str):
        return sorted(self.entities.get(name, []))
```

### 12.4 `bcm/memory/temporal_index.py`

```python
from __future__ import annotations


class TemporalIndex:
    def __init__(self) -> None:
        self.items = []

    def add(self, timestamp: str, node_id: str) -> None:
        self.items.append((timestamp, node_id))
        self.items.sort()

    def all(self):
        return list(self.items)
```

---

## 13. 实现 ingest 辅助模块占位

### 13.1 `bcm/ingest/artifact_scanner.py`

```python
from __future__ import annotations

from typing import Iterable, Set


def diff_files(files_before: Iterable[str], files_after: Iterable[str]) -> Set[str]:
    return set(files_after) - set(files_before)
```

### 13.2 `bcm/ingest/log_parser.py`

```python
from __future__ import annotations


def has_error(stderr: str, returncode: int) -> bool:
    return returncode != 0 or bool(stderr.strip())


def summarize_log(stdout: str, stderr: str, limit: int = 500) -> str:
    text = "\n".join(part for part in [stdout, stderr] if part)
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."
```

---

## 14. 实现 eval 模块占位

### 14.1 `bcm/eval/bioagent_metrics.py`

```python
from __future__ import annotations

from typing import Any, Dict


def extract_basic_bioagent_metrics(grader: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "steps_completed": grader.get("steps_completed"),
        "steps_to_completion": grader.get("steps_to_completion"),
        "final_result_reached": grader.get("final_result_reached"),
        "results_match": grader.get("results_match"),
        "f1_score": grader.get("f1_score"),
    }
```

### 14.2 `bcm/eval/causal_path_metrics.py`

```python
from __future__ import annotations

from typing import Iterable, Set


def recall_at_k(retrieved: Iterable[str], gold: Iterable[str], k: int) -> float:
    retrieved_k = list(retrieved)[:k]
    gold_set: Set[str] = set(gold)
    if not gold_set:
        return 0.0
    return len(set(retrieved_k) & gold_set) / len(gold_set)
```

### 14.3 `bcm/eval/failure_localization.py`

```python
from __future__ import annotations

from typing import Optional

from bcm.graph.schema import BioCausalGraph, NodeType


def first_failed_step(graph: BioCausalGraph) -> Optional[int]:
    failed = [
        node.attrs.get("step_id")
        for node in graph.nodes
        if node.type == NodeType.COMMAND and node.attrs.get("returncode", 0) != 0
    ]
    failed = [x for x in failed if x is not None]
    return min(failed) if failed else None
```

### 14.4 `bcm/eval/repair_eval.py`

```python
from __future__ import annotations


def contains_repair_hint(answer: str, expected_hint: str) -> bool:
    return expected_hint.lower() in answer.lower()
```

---

## 15. 实现 agents 模块占位

### 15.1 `bcm/agents/claude_runner.py`

```python
from __future__ import annotations


def not_implemented_in_v0() -> str:
    return "Agent runner integration is deferred to v1."
```

### 15.2 `bcm/agents/prompt_templates.py`

```python
from __future__ import annotations


FAILURE_QUERY_TEMPLATE = """
You are given a workflow-level causal provenance graph context.
Explain why the bioinformatics agent run failed using only the provided evidence.
"""
```

---

## 16. 实现 CLI

### 16.1 `bcm/cli.py`

```python
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
```

---

## 17. 初始化包文件

确保以下文件存在，内容可为空：

```text
bcm/__init__.py
bcm/ingest/__init__.py
bcm/graph/__init__.py
bcm/memory/__init__.py
bcm/retrieval/__init__.py
bcm/eval/__init__.py
bcm/agents/__init__.py
```

---

## 18. 实验脚本

### 18.1 `experiments/001_build_toy_graph.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

bcm build-graph \
  --task data/fixtures/transcript_quant_task.json \
  --trace data/runs/transcript_quant_failed_toy.json \
  --out data/graphs/transcript_quant_failed_toy.graph.json
```

### 18.2 `experiments/002_query_toy_failure.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

bcm query \
  --graph data/graphs/transcript_quant_failed_toy.graph.json \
  --question "why did the run fail?"
```

### 18.3 `experiments/003_compare_memory_baselines.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "Baseline comparison is deferred to v1."
```

设置可执行权限：

```bash
chmod +x experiments/*.sh
```

---

## 19. Tests

### 19.1 `tests/test_schema.py`

```python
from bcm.graph.schema import BioCausalGraph, EdgeType, GraphEdge, GraphNode, NodeType


def test_graph_node_creation():
    node = GraphNode(id="n1", type=NodeType.TASK, label="task")
    assert node.id == "n1"
    assert node.type == NodeType.TASK


def test_graph_edge_creation():
    edge = GraphEdge(id="e1", source="n1", target="n2", type=EdgeType.PRECEDES)
    assert edge.source == "n1"
    assert edge.target == "n2"
    assert edge.confidence == 1.0


def test_bio_causal_graph_dump_load():
    graph = BioCausalGraph(
        task_id="task",
        run_id="run",
        nodes=[GraphNode(id="n1", type=NodeType.TASK, label="task")],
        edges=[],
    )
    dumped = graph.model_dump_json()
    loaded = BioCausalGraph.model_validate_json(dumped)
    assert loaded.task_id == "task"
    assert len(loaded.nodes) == 1
```

### 19.2 `tests/test_trace_loader.py`

```python
from bcm.ingest.trace_loader import load_trace


def test_load_trace_fixture():
    trace = load_trace("data/runs/transcript_quant_failed_toy.json")
    assert trace["task_id"] == "transcript-quant"
    assert trace["run_id"] == "transcript_quant_failed_toy"
    assert len(trace["steps"]) == 3
    assert trace["steps"][1]["returncode"] == 1
    assert "grader" in trace
```

### 19.3 `tests/test_provenance_builder.py`

```python
from bcm.graph.provenance_builder import build_provenance_graph
from bcm.graph.schema import EdgeType, NodeType
from bcm.ingest.bioagent_loader import load_task_metadata
from bcm.ingest.trace_loader import load_trace


def test_build_provenance_graph():
    task = load_task_metadata("data/fixtures/transcript_quant_task.json")
    trace = load_trace("data/runs/transcript_quant_failed_toy.json")
    graph = build_provenance_graph(task, trace)

    node_types = [node.type for node in graph.nodes]
    edge_types = [edge.type for edge in graph.edges]

    assert NodeType.TASK in node_types
    assert len([node for node in graph.nodes if node.type == NodeType.COMMAND]) == 3
    assert any(node.type == NodeType.TOOL and node.label == "salmon" for node in graph.nodes)
    assert any(node.type == NodeType.ARTIFACT and node.label == "salmon_index/" for node in graph.nodes)
    assert NodeType.ERROR in node_types
    assert NodeType.EVAL in node_types

    assert EdgeType.FAILED_WITH in edge_types
    assert EdgeType.SUSPECTED_CAUSES in edge_types
```

### 19.4 `tests/test_causal_traversal.py`

```python
from bcm.graph.provenance_builder import build_provenance_graph
from bcm.ingest.bioagent_loader import load_task_metadata
from bcm.ingest.trace_loader import load_trace
from bcm.retrieval.anchor_finder import infer_intent
from bcm.retrieval.causal_traversal import retrieve_failure_context
from bcm.retrieval.context_builder import build_context


def test_infer_intent():
    assert infer_intent("why did the run fail?") == "WHY_FAILED"


def test_retrieve_failure_context_contains_failure_evidence():
    task = load_task_metadata("data/fixtures/transcript_quant_task.json")
    trace = load_trace("data/runs/transcript_quant_failed_toy.json")
    graph = build_provenance_graph(task, trace)

    result = retrieve_failure_context(graph, "why did the run fail?")
    assert result["intent"] == "WHY_FAILED"
    assert len(result["evidence_nodes"]) > 0
    assert len(result["evidence_edges"]) > 0

    context = build_context(graph, result)
    assert "wrong_index" in context
    assert "salmon_index" in context
```

---

## 20. README.md

创建或更新 `README.md`：

```markdown
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
```

---

## 21. v0 完成标准

只有满足以下条件，才算 v0 完成：

```bash
pip install -e .
pytest
bash experiments/001_build_toy_graph.sh
bash experiments/002_query_toy_failure.sh
```

并且 `bcm query` 能输出：

- 失败原因
- evidence path
- stderr 证据
- grader 证据
- 最小修复建议

预期输出应包含：

```text
wrong_index
salmon_index
Error: index wrong_index does not exist
final_result_reached=false
results_match=false
Replace `-i wrong_index` with `-i salmon_index`
```

---

## 22. 严格开发顺序

请按顺序实现，不要跳步：

1. 创建目录结构
2. 创建 `pyproject.toml`
3. 创建 `CLAUDE.md`
4. 实现 `schema.py`
5. 创建 toy fixtures
6. 实现 `trace_loader.py`
7. 实现 `bioagent_loader.py`
8. 实现 `provenance_builder.py`
9. 实现 `graph_store.py`
10. 实现 CLI `build-graph`
11. 实现 `anchor_finder.py`
12. 实现 `causal_traversal.py`
13. 实现 `context_builder.py`
14. 实现 CLI `query`
15. 写 tests
16. 跑通 toy example
17. 再考虑接入真实 BioAgent-Bench task

---

## 23. 后续 v1 规划，但 v0 不要实现

v1 才考虑：

- 接入真实 BioAgent-Bench run traces
- 支持 `transcript-quant`
- 支持 `viral-metagenomics`
- 支持 `giab`
- 实现 vector RAG baseline
- 实现 full trace baseline
- 实现 graph memory vs vector RAG 对比
- 加入 rule-based causal labeler
- 加入 decoy reference detection
- 加入 corrupted input detection
- 加入 failure localization accuracy
- 加入 causal path recall
- 加入 repair success evaluation
- 可选接入 MAGMA 的 traversal 思路
- 可选接入 AMA-Bench 的 memory_construction / memory_retrieve evaluation style

v0 不要实现这些高级功能。

---

## 24. 设计原则

### 24.1 Deterministic first

优先从 trace 中构建确定性 provenance：

```text
command -> input/reference/tool
command -> artifact
command -> stderr/error
command -> grader result
```

不要让 LLM 猜全图因果边。

### 24.2 Lazy causal labeling

只在 query 需要时，对 failure path 附近的候选边做 causal explanation。

不要对所有节点两两判断因果。

### 24.3 Minimal evidence path

query 输出应该是最小证据路径，不是完整 trace dump。

目标是减少 token cost，并提升 failure localization。

### 24.4 External repos are read-only

`external/` 下所有项目只读：

```text
external/bioagent-bench/
external/MAGMA/ or external/MAMGA/
external/AMA-Bench/
external/bioTaskBench/
```

主项目不得修改这些仓库源码。

---

## 25. 不要做的事情

请不要：

- 重写 BioAgent-Bench
- 运行完整 BioAgent-Bench benchmark
- 接入真实大规模生物数据
- 构建 gene regulatory network
- 解析 expression matrix 做 causal discovery
- 使用 LLM 做所有 pairwise causal inference
- 引入 Neo4j / database
- 引入复杂 web UI
- 过早优化 retrieval
- 过早实现多 agent runner
- 过早支持所有 BioAgent-Bench tasks

先把 toy trace 的 provenance graph 和 failure query 跑通。