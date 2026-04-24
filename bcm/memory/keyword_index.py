from __future__ import annotations


class KeywordIndex:
    def __init__(self) -> None:
        self.items = []

    def add(self, item: str) -> None:
        self.items.append(item)

    def search(self, query: str, k: int = 5):
        terms = set(query.lower().split())
        scored = []
        for item in self.items:
            score = len(terms & set(item.lower().split()))
            scored.append((score, item))
        scored.sort(reverse=True, key=lambda x: x[0])
        return [item for score, item in scored[:k] if score > 0]
