from __future__ import annotations


class VectorIndex:
    def __init__(self) -> None:
        self.items = []

    def add(self, item: str) -> None:
        self.items.append(item)

    def search(self, query: str, k: int = 5):
        return self.items[:k]
