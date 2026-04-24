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
    HAS_LOG = "HAS_LOG"
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
