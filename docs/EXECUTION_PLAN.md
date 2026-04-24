# BioAgent Causal Memory MVP — Execution Plan v1.0

> 本文档是交给 Codex 的严格执行计划。每个 milestone 都有明确的输入、输出、文件清单和验收标准。请严格按顺序执行，**遇到标记为 `[HUMAN-IN-LOOP]` 的 milestone 必须停下并明确告知用户**。

---

## 0. 项目目标与终止判据

### 0.1 假设 (H)

基于 file-provenance DAG 的 causal graph memory，在生信 agent trajectory 的溯源/状态/反事实类 probe 任务上，**显著优于** chunk-level naive RAG 基线。

### 0.2 终止判据 (Kill Criterion)

在 BioAgent-Bench 的 `transcript-quant` task 的三种 trajectory 条件（`clean` / `prompt_bloat` / `decoy_transcriptome`）上，10 道 probe question 的平均 accuracy：

```
accuracy(causal_graph) - accuracy(naive_rag) >= 10 pp
```

**未达到则放弃当前方案设计，回到 drawing board。**

### 0.3 明确的 Non-goals

以下事项在 MVP 阶段一律不做：

- 不实现 MAGMA 的 semantic graph / entity graph
- 不实现 async slow-path LLM consolidation
- 不做图可视化（`pyvis`、`graphviz` 等一律禁用）
- 不扩展到 `transcript-quant` 以外的 task
- 不自建 agent harness（直接用 Codex CLI）
- 不做 performance tuning（不关心 latency）

### 0.4 读者约定

- **Codex** = 执行此文档的 AI 编码 agent
- **User** = 项目所有者，负责标记为 `[HUMAN-IN-LOOP]` 的步骤
- 所有命令假定在 repo root 执行
- 所有路径相对于 repo root

---

## 1. 技术栈与约定

### 1.1 Stack

| 用途 | 选型 | 理由 |
|---|---|---|
| 语言 | Python 3.11 | 生态稳定 |
| 图数据结构 | `networkx>=3.0` | 纯 Python，无外部服务 |
| 持久化 | `sqlite3` (stdlib) | 零依赖 |
| 校验 | `pydantic>=2.0` | 类型安全 |
| 测试 | `pytest>=7.0` | 标准 |
| Embedding | OpenAI `text-embedding-3-small` | naive_rag 用 |
| LLM | `gpt-4o-mini` | 所有 probe answering 用 |
| Agent harness | Codex CLI (外部) | 仅由 user 手动运行 |

### 1.2 代码约定

- 所有 public function 必须有 type hints
- 所有 public API（module 层暴露）必须有简短 docstring
- 禁止在 `fast_path.py` 里调 LLM（这是设计红线）
- 所有 JSON/JSONL 文件用 UTF-8，pretty-print 缩进 2
- commit message 用英文，格式 `[M<n>] <subject>`

### 1.3 目录约定

| 路径 | 用途 | 是否入 git |
|---|---|---|
| `src/bacm/` | 源码 | ✅ |
| `tests/` | 测试代码 | ✅ |
| `tests/fixtures/` | 小体积测试数据 | ✅ |
| `experiments/` | 实验脚本 | ✅ |
| `data/sessions/` | Codex trajectory 原始文件 | ❌ |
| `data/probes/` | Probe 问题与 ground truth | ✅ |
| `data/results/` | 实验结果 | ❌ |
| `.env` | OpenAI key 等密钥 | ❌ |

---

## 2. 最终 Repository 结构（目标态）

```
bioagent-causal-mvp/
├── .env.example
├── .gitignore
├── README.md
├── pyproject.toml
├── src/bacm/
│   ├── __init__.py
│   ├── types.py                # 全局 dataclass / pydantic models
│   ├── trajectory_loader.py    # Codex session jsonl -> 结构化 turns
│   ├── fast_path.py            # turn -> ToolCall (纯正则，无 LLM)
│   ├── store.py                # networkx 图 + sqlite 持久化
│   ├── query.py                # 图查询 API
│   ├── retrievers/
│   │   ├── __init__.py
│   │   ├── base.py             # Retriever 抽象
│   │   ├── longctx.py          # 长上下文基线
│   │   ├── naive_rag.py        # chunk+embedding 基线
│   │   └── causal_graph.py     # 本项目方法
│   └── probe.py                # Probe 评测框架
├── tests/
│   ├── fixtures/
│   │   └── tq_clean_minimal.jsonl     # 人工精简的 session（用于单测）
│   ├── test_trajectory_loader.py
│   ├── test_fast_path.py
│   ├── test_store.py
│   └── test_query.py
├── experiments/
│   ├── 01_build_graph.py       # 从真实 session 构图，打印 provenance chain
│   └── 02_run_probes.py        # 跑所有 retriever 的 probe 评测
├── data/
│   ├── probes/
│   │   └── transcript_quant_v1.json   # 10 个 probe + ground truth
│   └── (sessions/, results/ 运行时生成)
└── EXECUTION_PLAN.md (本文档)
```

---

## 3. Milestones

### M0 — Bootstrap

**目标**：初始化仓库、依赖、骨架文件。

**依赖**：无。

**任务**：

1. 创建 repo 目录 `bioagent-causal-mvp/`，`git init`。
2. 创建 `pyproject.toml`（内容见下）。
3. 创建 `.gitignore`（内容见下）。
4. 创建 `.env.example`：包含 `OPENAI_API_KEY=` 一行。
5. 创建空的 `src/bacm/__init__.py`、`src/bacm/retrievers/__init__.py`。
6. 创建空的 `tests/__init__.py`。
7. 创建占位 `README.md`：一句话描述 + 指向本 EXECUTION_PLAN。
8. 运行 `pip install -e ".[dev]"`。

**文件**：

`pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "bacm"
version = "0.1.0"
description = "BioAgent Causal Memory MVP"
requires-python = ">=3.11"
dependencies = [
    "networkx>=3.0",
    "openai>=1.40",
    "pydantic>=2.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

`.gitignore`:
```
__pycache__/
*.pyc
.env
.venv/
data/sessions/
data/results/
*.sqlite
*.egg-info/
.pytest_cache/
```

**验收标准**：

- `pytest` 命令能跑（零测试通过）：`pytest -q` 返回 `no tests ran`
- `python -c "import bacm"` 不报错
- `.env.example` 存在

**Handoff**：无，继续 M1。

---

### M1 — 记录 Clean Reference Trajectory `[HUMAN-IN-LOOP]`

**目标**：用 Codex CLI 在 transcript-quant task 上跑出一次成功完成的 trajectory，保存为后续所有开发的固定输入。

**依赖**：M0。

**Codex 不要自己执行此步。** 此 milestone 必须由 user 手动完成。

**Codex 要做的事**：

1. 在 `data/sessions/README.md` 写一份给 user 的操作指引，内容至少包含：
   - 如何 clone `bioagent-bench` 仓库
   - 如何创建 mamba env 并安装 salmon
   - 如何运行 `codex exec` 或 `codex` 执行 transcript-quant task
   - 如何从 `~/.codex/sessions/` 找到对应 session jsonl 并拷贝到 `data/sessions/tq_clean_01.jsonl`
2. 向 user 输出一条明确消息：**"M1 需要你手动操作，请按 `data/sessions/README.md` 执行并告诉我完成后"**，然后停止。

**验收标准**（由 user 确认后 Codex 才继续）：

- `data/sessions/tq_clean_01.jsonl` 存在
- 文件行数 >= 20（保证 trajectory 有足够内容）
- 文件中至少出现一次 `"salmon"` 字符串
- trajectory 最终产物 `results/*.tsv` 或 `results/*.sf` 真实存在于 user 本地文件系统

---

### M2 — Trajectory Loader

**目标**：解析 Codex CLI 的 session jsonl 文件，输出结构化的 `Turn` 列表。

**依赖**：M1（需要真实 session 做开发参考），但可以先写代码和测试，用 fixture 数据开发。

**任务**：

1. 在 `src/bacm/types.py` 定义以下 pydantic models：
   ```python
   class RawTurn(BaseModel):
       """从 Codex session 还原出的一次 tool call + 其响应。"""
       turn_id: int            # 从 0 开始的单调递增
       cmd: str                # 完整 shell 命令字符串（含参数）
       cwd: str | None         # 执行目录，如果能从 session 推断
       stdout: str             # 可能为空
       stderr: str             # 可能为空
       exit_code: int          # 无法确定时用 -1
       started_at: float       # unix timestamp，无则用 turn_id 代理
   ```
2. 实现 `src/bacm/trajectory_loader.py::load_session(path: Path) -> list[RawTurn]`。
3. 在 `tests/fixtures/tq_clean_minimal.jsonl` 手写一个精简 fixture（5 个 event，覆盖 2 个 shell 调用 + 其响应）。
4. 在 `tests/test_trajectory_loader.py` 写测试：
   - 测试能加载 fixture
   - 测试能加载 `data/sessions/tq_clean_01.jsonl`（如存在则加载，不存在 skip）
   - Assert 返回 `list[RawTurn]` 且长度 >= 2
   - Assert 每条 `RawTurn.cmd` 非空字符串

**Codex session 格式备忘**：Codex CLI 的 session jsonl 每行是一个 event object。关心的字段是 `type=="function_call"`（内含 `name`, `arguments`（JSON 字符串，含 `command`、`cwd` 等））和 `type=="function_call_output"`（内含 `output`、exit_code）。**Codex 在实现前应该 `head -n 3 data/sessions/tq_clean_01.jsonl` 实地看格式，不要凭记忆写**。如果字段名和上述不一致，以实际文件为准，并在 `trajectory_loader.py` 顶部注释说明实际 schema。

**验收标准**：

- `pytest tests/test_trajectory_loader.py -v` 全部通过
- `python -c "from bacm.trajectory_loader import load_session; from pathlib import Path; turns = load_session(Path('data/sessions/tq_clean_01.jsonl')); print(len(turns), turns[0].cmd[:80])"` 能打出合理输出

**Handoff**：无。

---

### M3 — Fast-Path Parser

**目标**：把 `RawTurn` 解析成结构化 `ToolCall`，抽出 inputs、outputs、metrics。**此模块禁止调 LLM**。

**依赖**：M2。

**任务**：

1. 在 `src/bacm/types.py` 追加：
   ```python
   class FileRef(BaseModel):
       path: str           # 绝对路径或相对 cwd
       size: int | None = None
       sha1_8: str | None = None

   class ToolCall(BaseModel):
       turn_id: int
       cmd: str
       tool: str           # 命令第一个 token 的 basename
       subcmd: str | None  # 第二个 token 若非 flag
       inputs: list[FileRef]
       outputs: list[FileRef]
       exit_code: int
       stderr_tail: str    # 最后 500 字节
       metrics: dict       # 从 log 抽出的关键数字
       duration_s: float | None = None
   ```
2. 实现 `src/bacm/fast_path.py::parse_turn(raw: RawTurn) -> ToolCall`。
3. **必须覆盖以下 tool 的参数抽取规则**（transcript-quant 会用到）：
   - `salmon index`: `-t/--transcripts` 是 input，`-i/--index` 是 output（目录）
   - `salmon quant`: `-i` 是 input (index dir)，`-1/-2/-r/--reads` 是 input (fastq)，`-o/--output` 是 output (目录)
   - `mkdir`: 位置参数为 output（目录）
   - `ls`, `cat`, `head`, `tree`, `tar`, `gunzip`: 位置参数为 input
   - 对未知 tool 返回空 inputs/outputs，不报错
4. **必须实现的 metric 抽取**（regex，no LLM）：
   - salmon index: `log_mean = ...` 之类的 summary 行
   - salmon quant: mapping rate 行（如 `Mapping rate = xx.xx%`）
   - 通用：如果 stderr 包含 `error|Error|ERROR`，设 `metrics["has_error"] = True`
5. 在 `tests/test_fast_path.py` 写测试：
   - 手构一个 `RawTurn(cmd="salmon index -t tx.fa -i idx", ...)`，assert inputs 含 `tx.fa`，outputs 含 `idx`
   - 手构 salmon quant 测例
   - 手构未知 tool（如 `foobar --x y`），assert 不抛异常、返回空 I/O

**验收标准**：

- `pytest tests/test_fast_path.py -v` 全部通过
- 对真实 `tq_clean_01.jsonl` 跑 `parse_turn`，**至少 1 个 turn 的 inputs 包含 `.fa` 或 `.fasta` 文件，至少 1 个 turn 的 outputs 包含 `.sf` 或 `quant` 相关路径**。以下命令应输出非空：
  ```bash
  python -c "
  from pathlib import Path
  from bacm.trajectory_loader import load_session
  from bacm.fast_path import parse_turn
  turns = [parse_turn(r) for r in load_session(Path('data/sessions/tq_clean_01.jsonl'))]
  for t in turns:
      if any('.fa' in i.path for i in t.inputs):
          print('OK input:', t.cmd[:80])
      if any('.sf' in o.path or 'quant' in o.path for o in t.outputs):
          print('OK output:', t.cmd[:80])
  "
  ```

**Handoff**：无。

---

### M4 — Graph Store

**目标**：实现 provenance DAG 的构建、存储、加载。

**依赖**：M3。

**任务**：

1. 在 `src/bacm/store.py` 实现：
   ```python
   class ProvenanceGraph:
       """基于 networkx DiGraph 的封装。

       节点类型（通过 node attr 'kind' 区分）：
         - kind="turn": 属性含 ToolCall.model_dump()
         - kind="file": 属性 path, size, sha1_8 等

       边类型（通过 edge attr 'relation' 区分）：
         - relation="consumes":  turn -> file  (turn 把 file 作为输入)
         - relation="produces":  turn -> file  (turn 产生 file)
         - relation="next":       turn_i -> turn_{i+1}  (时间序)
       """
       def __init__(self) -> None: ...
       def add_toolcall(self, tc: ToolCall) -> None: ...
       def link_temporal(self) -> None: ...
       def save(self, path: Path) -> None: ...
       @classmethod
       def load(cls, path: Path) -> "ProvenanceGraph": ...
       @property
       def n_turns(self) -> int: ...
       @property
       def n_files(self) -> int: ...
   ```
2. 持久化用 sqlite3：两张表 `nodes(id TEXT PK, kind TEXT, attrs_json TEXT)` 和 `edges(src TEXT, dst TEXT, relation TEXT, attrs_json TEXT)`。**不要用 pickle**（跨版本不稳）。
3. `turn` 节点 id 格式 `turn:{turn_id}`；`file` 节点 id 格式 `file:{canonical_path}`，其中 `canonical_path` 用 `os.path.normpath` 规范化。
4. `link_temporal` 在所有 turn 节点加好之后调用一次，串起时间边。
5. 在 `tests/test_store.py` 写测试：
   - 构造 3 个 `ToolCall` 加进去（index -> quant -> format_output 这样一条链）
   - assert `n_turns == 3`, `n_files` 合理
   - `save` 后 `load`，assert 节点数边数一致
   - assert 时间边的方向正确（`turn:0 -> turn:1 -> turn:2`）

**验收标准**：

- `pytest tests/test_store.py -v` 全部通过
- `experiments/01_build_graph.py` 跑出完整的 `tq_clean_01` 图，并打印出 `n_turns, n_files`，数字合理（turn 数应接近 session 的 function_call 数；file 数 >= 3）

**Handoff**：无。

---

### M5 — Query Interface

**目标**：在 ProvenanceGraph 上提供 5 个核心查询接口。这是 `causal_graph` retriever 的基石。

**依赖**：M4。

**任务**：

1. 在 `src/bacm/query.py` 实现：
   ```python
   def ancestors_of_file(g: ProvenanceGraph, path: str, max_hops: int = 5) -> list[ToolCall]:
       """返回曾经（直接或间接）参与产生 path 的所有 turn，按时间升序。"""

   def consumers_of_file(g: ProvenanceGraph, path: str) -> list[ToolCall]:
       """返回直接消费了 path 的所有 turn。"""

   def timeline(g: ProvenanceGraph, start: int | None = None, end: int | None = None) -> list[ToolCall]:
       """返回 [start, end] 范围内所有 turn，按 turn_id 升序。"""

   def turns_with_tool(g: ProvenanceGraph, tool: str, subcmd: str | None = None) -> list[ToolCall]:
       """按 tool 名过滤。"""

   def failed_turns(g: ProvenanceGraph) -> list[ToolCall]:
       """exit_code != 0 或 metrics['has_error'] is True 的 turn。"""
   ```
2. `ancestors_of_file` 用 networkx 反向 BFS：从 `file:path` 的 `produces` 入边找 turn，再从 turn 的 `consumes` 出边找上游 file，递归直到 `max_hops`。
3. 所有返回值按 `turn_id` 升序排列。
4. 在 `tests/test_query.py` 写测试：
   - 构一个 3 层链（tx.fa → index → quant.sf），assert `ancestors_of_file("quant.sf")` 返回两个 turn（index 和 quant）
   - assert `consumers_of_file("tx.fa")` 返回 index turn
   - assert `failed_turns` 能正确识别一个故意设 exit_code=1 的 turn

5. 在 `experiments/01_build_graph.py` 扩展：
   ```python
   # 在构图之后追加：
   from bacm.query import ancestors_of_file
   chain = ancestors_of_file(g, "results/quant.sf")  # 或实际的最终产物路径
   for tc in chain:
       print(f"turn {tc.turn_id}: {tc.tool} {tc.subcmd or ''} "
             f"inputs={[i.path for i in tc.inputs]} "
             f"outputs={[o.path for o in tc.outputs]}")
   ```

**验收标准**：

- `pytest tests/test_query.py -v` 全部通过
- `python experiments/01_build_graph.py` 能打出 `results/quant.sf`（或实际产物）的完整 ancestor chain，包含 `salmon index` 和 `salmon quant` 两个 turn，顺序正确

**Handoff**：在验收标准达成后，**明确告知 user："M5 完成，provenance DAG 基础设施已就绪。核心技术假设已被验证（可自动从 Codex bash history 构出 file provenance DAG，无需 LLM）。是否进入 probe evaluation 阶段？"** 等待 user 确认后继续。

---

### M6 — Probe Question Framework

**目标**：定义 probe 格式、写 10 道 probe、写评测数据加载器。

**依赖**：M0（可与 M2-M5 并行）。

**任务**：

1. 在 `src/bacm/types.py` 追加：
   ```python
   class Probe(BaseModel):
       probe_id: str
       category: Literal["provenance", "state", "counterfactual"]
       question: str          # 给 LLM 的问题
       ground_truth: str      # 人工标注的正确答案（可简短）
       acceptable: list[str]  # 其他可接受的表达（用于宽松匹配）
       trajectory_ids: list[str]  # 适用于哪些 trajectory（如 ["tq_clean", "tq_decoy"]）
   ```
2. 创建 `data/probes/transcript_quant_v1.json`，包含 10 个 probe（见附录 A）。
3. 在 `src/bacm/probe.py` 实现：
   ```python
   def load_probes(path: Path) -> list[Probe]: ...

   def judge(answer: str, probe: Probe) -> bool:
       """宽松判断：answer 包含 ground_truth 或 acceptable 中任一字符串（小写比较）即算对。"""
   ```
4. 在 `tests/` 加 `test_probe.py`，测试 `load_probes` 和 `judge` 基本逻辑。

**验收标准**：

- `data/probes/transcript_quant_v1.json` 存在，含 10 个 probe
- 每个 probe 的 `category` 分布：至少 4 道 `provenance`、3 道 `state`、2 道 `counterfactual`（最后 1 道自选）
- `pytest tests/test_probe.py -v` 通过

**Handoff**：无。

---

### M7 — 三个 Retriever 实现

**目标**：实现 `longctx`、`naive_rag`、`causal_graph` 三个 retriever，统一接口。

**依赖**：M5、M6。

**任务**：

1. 在 `src/bacm/retrievers/base.py` 定义抽象：
   ```python
   class Retriever(ABC):
       name: str

       @abstractmethod
       def prepare(self, session_path: Path) -> None:
           """对给定 trajectory 做一次性准备（如构图、构索引）。"""

       @abstractmethod
       def retrieve(self, question: str, token_budget: int = 2000) -> str:
           """返回一段 context 字符串（不含 question 本身）。"""
   ```

2. `longctx.py`: `prepare` 加载所有 turn，把 `cmd + stderr_tail[:200]` 拼成字符串。`retrieve` 忽略 question，按 token budget 截断尾部（保留最后 N 个 turn）。

3. `naive_rag.py`:
   - `prepare` 时把每个 turn 序列化成一段文本（`cmd + stderr_tail[:300] + metrics`），调用 `text-embedding-3-small` 生成 embedding，存内存。
   - `retrieve` 时把 question 也 embedding，返回 cosine top-5 turn 拼接的文本。
   - 为了省钱：**实现 embedding 磁盘缓存**，key 是 `sha1(text)`，存到 `data/cache/embeddings.sqlite`。
   - 超出 token budget 时从末尾截断。

4. `causal_graph.py`:
   - `prepare` 时用 fast_path 解析、构 ProvenanceGraph。
   - `retrieve` 策略：
     1. 用简单规则从 question 抽取可能的 file path（正则匹配 `\S+\.(fa|fasta|fq|fastq|sf|tsv|gz)\b`）
     2. 对每个命中 path，调用 `ancestors_of_file` + `consumers_of_file`，收集相关 turn
     3. 如果 question 包含 "fail|error|wrong|错误|失败"，额外加入 `failed_turns` 结果
     4. 如果没抽到任何 path（开放性问题），fallback 到 `timeline`（全量按时间）
     5. 把收集到的 turn 按 turn_id 升序、去重、序列化为文本，超 budget 从中间摘要（保留首尾）

5. 在 `tests/test_retrievers.py` 对每个 retriever 写 smoke test：在 fixture session 上 `prepare` + 对一个 hard-coded question `retrieve`，assert 返回非空字符串。

**验收标准**：

- `pytest tests/test_retrievers.py -v` 通过
- 手动 spot check：对 question "results/quant.sf 是由哪个 transcriptome 产生的？" 跑三个 retriever，打印各自返回的 context，**causal_graph 返回的 context 长度应显著短于 longctx**（否则说明图检索没起作用）

**Handoff**：无。

---

### M8 — Probe 评测 Runner `[COST NOTICE]`

**目标**：在 clean trajectory 上跑完三个 retriever × 10 个 probe，记录 accuracy。

**依赖**：M7。

**Cost notice**：此步骤会调用 `gpt-4o-mini`，每次 probe 一次调用，共 30 次 × 后续扰动还要 ×3。单次成本 <$0.001，总计 < $0.50。

**任务**：

1. 在 `experiments/02_run_probes.py` 实现：
   ```python
   def answer_with_llm(context: str, question: str) -> str:
       """调 gpt-4o-mini，system prompt 强制只用 context 回答，不够就回 'Information not found'。"""

   def run_experiment(session_path: Path, probes: list[Probe], retrievers: list[Retriever]) -> list[dict]:
       """返回 [{probe_id, retriever, answer, correct, context_tokens}, ...]"""
   ```
2. 结果写到 `data/results/clean_v1.jsonl`，一行一条。
3. 写汇总脚本，打印：
   ```
   Retriever        Provenance  State       Counterfactual  Overall
   longctx          x/4         y/3         z/3             a/10
   naive_rag        ...
   causal_graph     ...
   ```
4. **此阶段单个 trajectory (`clean`) 就好，扰动放到 M10**。

**验收标准**：

- `python experiments/02_run_probes.py data/sessions/tq_clean_01.jsonl` 能跑完，生成 `data/results/clean_v1.jsonl`
- 结果至少有 30 条记录（3 × 10）
- 每条记录含 `probe_id`, `retriever`, `answer`, `correct` 字段
- 能打出汇总表

**Handoff**：**明确告知 user 汇总结果。如果 causal_graph 在 clean 条件下已经落后 naive_rag > 5 pp，先不要继续 M9，让 user 决定是否调整 retriever 策略。**

---

### M9 — 扰动 Trajectory 生成 `[HUMAN-IN-LOOP]`

**目标**：生成 `prompt_bloat` 和 `decoy_transcriptome` 两种扰动下的 trajectory。

**依赖**：M8 汇总的 clean 结果健康（即没触发 M8 的 handoff 警告）。

**Codex 不要自己执行。** 此 milestone 必须由 user 手动完成。

**Codex 要做的事**：

1. 在 `data/sessions/README.md` 追加两节说明：
   - **Bloat**：把 BioAgent-Bench 论文附录 A.8 的 metagenomics bloat 文本（或 user 自己写的 ~800 词 transcript-quant 相关闲篇）前缀到原 task prompt 前面，再跑一遍 Codex CLI，session 存为 `tq_bloat_01.jsonl`。
   - **Decoy**：在 task 的 working dir 额外放一个 `decoy_transcriptome.fa`（可从别的物种下载一个小 transcriptome），prompt 里不提这个文件但它确实存在，跑 Codex CLI，session 存为 `tq_decoy_01.jsonl`。
2. 向 user 输出一条明确消息：**"M9 需要你手动跑两次 Codex CLI，请按 `data/sessions/README.md` 指引执行，完成后告诉我"**，然后停止。

**验收标准**（由 user 确认）：

- `data/sessions/tq_bloat_01.jsonl` 存在，且其中至少有一个 `function_call` event 的 `arguments` 含 bloat 文本特征词
- `data/sessions/tq_decoy_01.jsonl` 存在
- 两个 trajectory 都产出了 `results/` 目录下的最终 artifact

---

### M10 — 最终分析 + 终止判据判定

**目标**：在三种 trajectory 上跑完所有 probe，计算终止判据，产出结论。

**依赖**：M8、M9。

**任务**：

1. 扩展 `experiments/02_run_probes.py`，让它能接受多个 session path，输出每个 condition 独立的结果文件：
   - `data/results/clean_v1.jsonl`
   - `data/results/bloat_v1.jsonl`
   - `data/results/decoy_v1.jsonl`
2. 创建 `experiments/03_analyze.py`：
   - 加载三个结果文件
   - 产出 markdown 汇总表：每种 condition × 每种 retriever 的 overall accuracy + 按 category 分解
   - 计算 `delta = accuracy(causal_graph) - accuracy(naive_rag)`，分别算 clean/bloat/decoy/avg 四个值
   - 明确打印：**"KILL CRITERION {PASSED|FAILED}: avg_delta = X.X pp"**
3. 将分析结果写入 `data/results/REPORT.md`，包含：
   - 三个 condition 的汇总表
   - 各 retriever 的成功/失败代表性 probe 示例（每种 retriever 各取 1 成 1 败）
   - 终止判据结论
   - 下一步建议（PASS 则建议扩展 giab；FAIL 则列出 3 个最可能的改进方向）

**验收标准**：

- `python experiments/03_analyze.py` 生成 `data/results/REPORT.md`
- REPORT.md 顶部明确包含 `KILL CRITERION PASSED` 或 `KILL CRITERION FAILED` 字样
- 三种 condition 的数据都到位（不是 None/NaN）

**Handoff**：**向 user 呈报 `REPORT.md` 的完整内容，等待 user 决策下一步。**

---

## 4. Codex 工作纪律

1. **每个 milestone 开始前**：读一遍对应章节 + 上一 milestone 的验收标准，确认依赖已达成。
2. **每个 milestone 结束时**：主动跑一遍验收命令并把输出贴出来。不要跳过验收。
3. **遇到 `[HUMAN-IN-LOOP]`**：立即停止写代码，输出清晰的等待消息，不要替 user 做决定。
4. **遇到设计层面的选择**：不要擅自决定，向 user 问一句再动手。例子：salmon 的输出路径 schema 不确定、Codex session jsonl 字段不匹配本文档描述。
5. **禁止事项**：
   - 禁止在 `fast_path.py` 里 import `openai`
   - 禁止装本计划未列出的依赖（如需新增依赖先问 user）
   - 禁止扩展到 transcript-quant 以外的 task
   - 禁止实现图可视化
6. **commit 粒度**：每个 milestone 独立一个 commit，message 格式 `[M<n>] <short subject>`。

---

## 5. 附录

### A. Probe Questions v1（10 道）

以 `transcript-quant` 的真实 trajectory 为准，具体文件名在 M1 之后由 user 填入占位符 `{transcriptome_name}` 等。建议 Codex 在 M6 时先留占位符，M1 完成后再让 user 补真实路径。

**A.1 Provenance 类（4 道）**

1. `P-PROV-01`: "最终产物 `results/quant.sf`（或等效 tsv）是由哪个 transcriptome 文件产生的？"
2. `P-PROV-02`: "salmon quant 使用的 index 是由哪一步产生的？该步骤的命令是什么？"
3. `P-PROV-03`: "哪些输入 FASTQ 文件被 salmon quant 消费了？全部列出。"
4. `P-PROV-04`: "transcriptome 文件从未被直接复制或改名过吗？还是经历过任何中间处理？"

**A.2 State 类（3 道）**

5. `P-STATE-01`: "salmon index 这一步是否成功完成？exit code 是多少？"
6. `P-STATE-02`: "salmon quant 的 mapping rate 是多少？从 log 里读取。"
7. `P-STATE-03`: "整个 pipeline 里有没有出现任何 tool 的 stderr 包含 'error' 字样？"

**A.3 Counterfactual 类（2 道）**

8. `P-CF-01`: "working directory 里有多个 `.fa` 文件时，agent 最终用的是哪一个？为什么选它而不是其他（如果信息不足就说信息不足）？"
9. `P-CF-02`: "如果 salmon index 失败了，salmon quant 还能成功吗？从当前 trajectory 能否判断？"

**A.4 Open (1 道)**

10. `P-OPEN-01`: "用 2-3 句话概括 agent 完成 transcript quantification 的关键步骤顺序。"

每道题需在 `data/probes/transcript_quant_v1.json` 标注 `ground_truth` 和 `acceptable` 列表。M6 实施时，Codex 应在 M1 trajectory 就绪后，**让 user 审核并填入 ground truth**（因为 acceptable 答案依赖真实 trajectory 里的文件名和数字）。

### B. 验收命令速查

| Milestone | 验收命令 |
|---|---|
| M0 | `pytest -q && python -c "import bacm"` |
| M1 | `test -f data/sessions/tq_clean_01.jsonl && wc -l data/sessions/tq_clean_01.jsonl` |
| M2 | `pytest tests/test_trajectory_loader.py -v` |
| M3 | `pytest tests/test_fast_path.py -v` |
| M4 | `pytest tests/test_store.py -v` |
| M5 | `pytest tests/test_query.py -v && python experiments/01_build_graph.py` |
| M6 | `pytest tests/test_probe.py -v` |
| M7 | `pytest tests/test_retrievers.py -v` |
| M8 | `python experiments/02_run_probes.py data/sessions/tq_clean_01.jsonl` |
| M9 | `test -f data/sessions/tq_bloat_01.jsonl && test -f data/sessions/tq_decoy_01.jsonl` |
| M10 | `python experiments/03_analyze.py && test -f data/results/REPORT.md` |

### C. 已知风险 / 容易踩的坑

1. **Codex session jsonl 格式** 可能随 Codex CLI 版本变化。在 M2 前一定先 `head` 实际文件确认字段。
2. **Salmon 的 shell 调用方式** 可能是 `salmon index ...` 或 `bash -c "salmon index ..."` 或嵌套在 `python subprocess`。M3 的 parser 必须能处理前两种。若遇第三种，**停下问 user 是否在 prompt 里要求 agent 不要用 subprocess 间接调用**。
3. **Probe 判分** 用简单字符串包含匹配会误判。MVP 阶段接受这个噪声，**不要**改成 LLM-as-judge（引入新一层不确定性）。v2 再说。
4. **Embedding cache 并发**：MVP 不考虑并发，单进程就好。
5. **OpenAI API rate limit**：一次 run 30 次 embedding + 30 次 gpt-4o-mini 调用，远低于默认 rate limit，无需处理。

### D. 后续扩展（**MVP 阶段不做**，仅供参考）

- M11 扩展到 `giab` task（variant calling，pipeline 步骤更多、log 更复杂）
- M12 加 causal edge（LLM-inferred "step X fails because step Y's param Z is wrong"）
- M13 加 entity graph（把 reference genome 版本、物种等 link 到 GO/KEGG）
- M14 把 Retriever 封装成 Codex CLI tool 接进 live agent loop，做端到端 completion rate 评测

---

## 6. 签署

| 角色 | 签署 |
|---|---|
| 计划作者 | Claude (via conversation) |
| 执行者 | Codex |
| 所有者 | User |
| 版本 | v1.0 |
| 预计总工时 | 5-7 天（含 user 手动 trajectory 录制时间） |

**Codex：请确认你理解本计划的全部内容，列出任何你认为 ambiguous 或 missing 的地方，再开始执行 M0。**
