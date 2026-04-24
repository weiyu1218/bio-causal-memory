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
