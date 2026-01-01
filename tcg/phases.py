"""Definitions for the structured game phases.

The phase loop is intentionally minimal for the prototype while leaving
room to add timing windows for evolution checks and responses.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterable, Iterator, List


class Phase(Enum):
    """Basic turn phases used in the prototype."""

    START = auto()
    MAIN = auto()
    COMBAT = auto()
    END = auto()


@dataclass
class PhaseLoop:
    """Iterator-style helper that cycles through phases for each turn."""

    order: List[Phase]

    @classmethod
    def default(cls) -> "PhaseLoop":
        return cls([Phase.START, Phase.MAIN, Phase.COMBAT, Phase.END])

    def __iter__(self) -> Iterator[Phase]:
        yield from self.order

    def cycle(self) -> Iterable[Phase]:
        """Yield phases indefinitely for repeated turns."""

        while True:
            for phase in self.order:
                yield phase
