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
