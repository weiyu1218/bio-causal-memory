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
