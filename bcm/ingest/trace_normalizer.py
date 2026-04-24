from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from bcm.ingest.trace_loader import REQUIRED_STEP_FIELDS, REQUIRED_TRACE_FIELDS


def _passthrough(raw: Dict[str, Any]) -> Dict[str, Any]:
    missing = REQUIRED_TRACE_FIELDS - set(raw.keys())
    if missing:
        raise ValueError(
            f"Passthrough trace is missing required fields: {sorted(missing)}"
        )
    if not isinstance(raw["steps"], list):
        raise ValueError("Passthrough trace field `steps` must be a list")
    for idx, step in enumerate(raw["steps"]):
        missing_step = REQUIRED_STEP_FIELDS - set(step.keys())
        if missing_step:
            raise ValueError(
                f"Passthrough step at index {idx} is missing required fields: "
                f"{sorted(missing_step)}"
            )
    return raw


def _normalize_shell_steps(raw: Dict[str, Any]) -> Dict[str, Any]:
    missing = {"task_id", "run_id", "shell_steps", "grader"} - set(raw.keys())
    if missing:
        raise ValueError(
            f"Shell-step trace is missing required fields: {sorted(missing)}"
        )
    if not isinstance(raw["shell_steps"], list):
        raise ValueError("Shell-step trace field `shell_steps` must be a list")

    normalized_steps: List[Dict[str, Any]] = []
    for idx, raw_step in enumerate(raw["shell_steps"]):
        if "command" not in raw_step:
            raise ValueError(f"shell_steps[{idx}] missing required field: command")

        step_id = raw_step.get("index", idx + 1)
        cmd = raw_step["command"]
        stdout = raw_step.get("stdout", "")
        stderr = raw_step.get("stderr", "")
        returncode = raw_step.get("exit_code", 0)
        files_before = raw_step.get("files_before", [])
        files_after = raw_step.get("files_after", [])

        normalized_steps.append(
            {
                "step_id": step_id,
                "cmd": cmd,
                "cwd": raw_step.get("cwd", ""),
                "stdout": stdout,
                "stderr": stderr,
                "returncode": returncode,
                "start_time": raw_step.get("start_time", ""),
                "end_time": raw_step.get("end_time", ""),
                "files_before": files_before,
                "files_after": files_after,
            }
        )

    return {
        "task_id": raw["task_id"],
        "run_id": raw["run_id"],
        "steps": normalized_steps,
        "grader": raw["grader"],
    }


def normalize_trace(raw: Dict[str, Any]) -> Dict[str, Any]:
    if "steps" in raw:
        return _passthrough(raw)
    if "shell_steps" in raw:
        return _normalize_shell_steps(raw)
    raise ValueError(
        "Unrecognized trace format: expected `steps` or `shell_steps` key"
    )


def load_normalized_trace(path: str) -> Dict[str, Any]:
    trace_path = Path(path)
    if not trace_path.exists():
        raise FileNotFoundError(f"Trace file not found: {trace_path}")

    with trace_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    return normalize_trace(raw)
