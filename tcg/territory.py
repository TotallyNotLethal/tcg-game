"""Territory definitions for resource generation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .resources import ResourcePool


@dataclass
class Territory:
    name: str
    generate: Callable[[ResourcePool], str]

    def play(self, pool: ResourcePool) -> str:
        return self.generate(pool)


# Prototype-friendly helper factories

def fear_territory(name: str, amount: int) -> Territory:
    def _grant(pool: ResourcePool) -> str:
        pool.add(fear=amount)
        return f"{name} yields {amount} Fear."

    return Territory(name=name, generate=_grant)


def belief_territory(name: str, amount: int) -> Territory:
    def _grant(pool: ResourcePool) -> str:
        pool.add(belief=amount)
        return f"{name} yields {amount} Belief."

    return Territory(name=name, generate=_grant)
