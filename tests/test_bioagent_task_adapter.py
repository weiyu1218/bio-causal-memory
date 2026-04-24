from pathlib import Path

import pytest

from bcm.ingest.bioagent_task_adapter import load_bioagent_task


TRANSCRIPT_QUANT_DIR = "external/bioagent-bench/tasks/transcript-quant"


def test_load_transcript_quant_task_metadata():
    if not Path(TRANSCRIPT_QUANT_DIR).is_dir():
        pytest.skip(f"external task dir not available: {TRANSCRIPT_QUANT_DIR}")

    task = load_bioagent_task(TRANSCRIPT_QUANT_DIR)

    assert task["task_id"] == "transcript-quant"
    assert "transcriptome.fa" in task["reference_data"]
    assert "reads_1.fq.gz" in task["input_data"]
    assert "reads_2.fq.gz" in task["input_data"]
    assert any("results" in out for out in task["expected_outputs"]), (
        "At least one expected output must be under results/"
    )
    assert task["name"]
    assert task["goal"]


def test_missing_task_dir_raises():
    with pytest.raises(FileNotFoundError):
        load_bioagent_task("external/bioagent-bench/tasks/__does_not_exist__")


def test_missing_run_script_raises(tmp_path):
    empty_task_dir = tmp_path / "empty-task"
    empty_task_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        load_bioagent_task(str(empty_task_dir))
