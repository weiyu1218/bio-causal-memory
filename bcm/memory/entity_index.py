from __future__ import annotations


class EntityIndex:
    def __init__(self) -> None:
        self.entities = {}

    def add(self, name: str, node_id: str) -> None:
        self.entities.setdefault(name, set()).add(node_id)

    def get(self, name: str):
        return sorted(self.entities.get(name, []))
