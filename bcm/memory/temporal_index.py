from __future__ import annotations


class TemporalIndex:
    def __init__(self) -> None:
        self.items = []

    def add(self, timestamp: str, node_id: str) -> None:
        self.items.append((timestamp, node_id))
        self.items.sort()

    def all(self):
        return list(self.items)
