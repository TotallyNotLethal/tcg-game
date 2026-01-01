"""Fear/Belief resource model with instability checks."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ResourcePool:
    """Track the dual-resource system and derived instability."""

    fear: int = 0
    belief: int = 0

    def add(self, fear: int = 0, belief: int = 0) -> None:
        self.fear += fear
        self.belief += belief

    def spend(self, fear: int = 0, belief: int = 0) -> bool:
        if self.fear < fear or self.belief < belief:
            return False
        self.fear -= fear
        self.belief -= belief
        return True

    @property
    def instability(self) -> int:
        """Simple imbalance metric for prototype tuning."""

        return abs(self.fear - self.belief)

    def describe(self) -> str:
        return f"Fear: {self.fear}, Belief: {self.belief}, Instability: {self.instability}"
