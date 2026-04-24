from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


_ASSIGNMENT_RE = re.compile(
    r'^\s*(?P<name>[A-Z][A-Z0-9_]*)\s*=\s*"(?P<value>[^"$`\n]+)"\s*$',
    re.MULTILINE,
)

_REFERENCE_EXTS = (".fa", ".fasta", ".fa.gz", ".fasta.gz", ".gtf", ".gff", ".gff3")
_READS_MARKERS = (".fq", ".fastq", ".fq.gz", ".fastq.gz")


def _classify_path(value: str) -> str:
    lower = value.lower()

    if value.startswith("results/") or value.startswith("output/"):
        return "output"

    if value.startswith("data/"):
        if any(lower.endswith(ext) for ext in _REFERENCE_EXTS):
            return "reference"
        if any(marker in lower for marker in _READS_MARKERS) or "reads" in lower:
            return "input"

    return "other"


def _parse_bash_assignments(script_text: str) -> List[Tuple[str, str]]:
    return [(m.group("name"), m.group("value")) for m in _ASSIGNMENT_RE.finditer(script_text)]


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def _read_env_name(env_file: Path) -> str | None:
    if not env_file.exists():
        return None
    env_data = yaml.safe_load(env_file.read_text(encoding="utf-8"))
    if isinstance(env_data, dict):
        name = env_data.get("name")
        if isinstance(name, str) and name:
            return name
    return None


def load_bioagent_task(task_dir: str) -> Dict[str, Any]:
    task_path = Path(task_dir)
    if not task_path.is_dir():
        raise FileNotFoundError(f"Task directory not found: {task_path}")

    run_script = task_path / "run_script.sh"
    if not run_script.exists():
        raise FileNotFoundError(f"run_script.sh not found in {task_path}")

    task_id = task_path.name
    script_text = run_script.read_text(encoding="utf-8")
    assignments = _parse_bash_assignments(script_text)

    input_data: List[str] = []
    reference_data: List[str] = []
    expected_outputs: List[str] = []

    seen_inputs = set()
    seen_references = set()
    seen_outputs = set()

    for _name, value in assignments:
        kind = _classify_path(value)
        if kind == "input":
            filename = _basename(value)
            if filename not in seen_inputs:
                input_data.append(filename)
                seen_inputs.add(filename)
        elif kind == "reference":
            filename = _basename(value)
            if filename not in seen_references:
                reference_data.append(filename)
                seen_references.add(filename)
        elif kind == "output":
            if value not in seen_outputs:
                expected_outputs.append(value)
                seen_outputs.add(value)

    env_name = _read_env_name(task_path / "environment.yml")
    display_name = env_name if env_name else task_id

    return {
        "task_id": task_id,
        "name": display_name,
        "goal": f"BioAgent-Bench task: {task_id}",
        "expected_outputs": expected_outputs,
        "input_data": input_data,
        "reference_data": reference_data,
    }
