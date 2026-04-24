from __future__ import annotations


def contains_repair_hint(answer: str, expected_hint: str) -> bool:
    return expected_hint.lower() in answer.lower()
