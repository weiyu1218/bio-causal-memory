from __future__ import annotations

from typing import Iterable, Set


def recall_at_k(retrieved: Iterable[str], gold: Iterable[str], k: int) -> float:
    retrieved_k = list(retrieved)[:k]
    gold_set: Set[str] = set(gold)
    if not gold_set:
        return 0.0
    return len(set(retrieved_k) & gold_set) / len(gold_set)
