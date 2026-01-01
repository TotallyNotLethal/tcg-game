"""Lightweight stack model for pending actions and triggers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional


@dataclass
class StackItem:
    """Single entry on the game stack."""

    description: str
    resolve: Optional[Callable[[], str]] = None

    def execute(self) -> str:
        if self.resolve:
            return self.resolve()
        return f"{self.description} resolves with no effect."


class GameStack:
    """LIFO stack used for spells, abilities, and delayed effects."""

    def __init__(self) -> None:
        self._items: List[StackItem] = []

    def push(self, item: StackItem) -> None:
        self._items.append(item)

    def pop(self) -> Optional[StackItem]:
        if not self._items:
            return None
        return self._items.pop()

    def is_empty(self) -> bool:
        return not self._items

    def resolve_all(self) -> List[str]:
        """Resolve the entire stack from top to bottom."""

        results: List[str] = []
        while self._items:
            item = self.pop()
            if item:
                results.append(item.execute())
        return results

    def describe(self) -> List[str]:
        return [item.description for item in reversed(self._items)]
