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
