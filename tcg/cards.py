"""Card definitions and exemplar cryptids for the prototype."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional

from .resources import ResourcePool
from .stack import StackItem


class CardType(Enum):
    TERRITORY = auto()
    CRYPTID = auto()
    EVENT = auto()


@dataclass
class Card:
    name: str
    type: CardType
    cost_fear: int = 0
    cost_belief: int = 0
    text: str = ""

    def can_play(self, pool: ResourcePool) -> bool:
        return pool.fear >= self.cost_fear and pool.belief >= self.cost_belief

    def pay_cost(self, pool: ResourcePool) -> bool:
        return pool.spend(fear=self.cost_fear, belief=self.cost_belief)


@dataclass
class Branch:
    name: str
    trigger: str
    effect_text: str


@dataclass
class Cryptid(Card):
    branches: List[Branch] = None

    def __post_init__(self) -> None:
        if self.branches is None:
            self.branches = []

    def spawn_triggers(self) -> List[StackItem]:
        return [
            StackItem(
                description=f"Evolution: {branch.name}",
                resolve=lambda b=branch: f"{self.name} notes future branch '{b.name}' — {b.effect_text}",
            )
            for branch in self.branches
        ]


# Exemplar cryptids with stubbed branches for sprint 1

def exemplar_cryptids() -> Dict[str, Cryptid]:
    return {
        "Moth Sentinel": Cryptid(
            name="Moth Sentinel",
            type=CardType.CRYPTID,
            cost_belief=1,
            text="Watchful guardian that pivots between omen and protector.",
            branches=[
                Branch(
                    name="Harbinger Wing",
                    trigger="When opponent gains Fear",
                    effect_text="May shift into omen form to tax future Territory plays.",
                ),
                Branch(
                    name="Beacon of Hope",
                    trigger="When belief exceeds fear by 3",
                    effect_text="Evolves into a protective aura that reduces Instability.",
                ),
            ],
        ),
        "Bayou Serpent": Cryptid(
            name="Bayou Serpent",
            type=CardType.CRYPTID,
            cost_fear=1,
            text="Swamp-dwelling menace that feeds on lopsided resources.",
            branches=[
                Branch(
                    name="Floodlash",
                    trigger="When a Territory is drained",
                    effect_text="Unleash a tidal strike scaling with Instability.",
                ),
                Branch(
                    name="Mirebound Coil",
                    trigger="At end step if fear > belief",
                    effect_text="Constrains enemy resources, delaying their next main phase.",
                ),
            ],
        ),
        "Rustbound Hound": Cryptid(
            name="Rustbound Hound",
            type=CardType.CRYPTID,
            cost_fear=1,
            cost_belief=1,
            text="Mechanical tracker that locks onto volatile energy.",
            branches=[
                Branch(
                    name="Junkyard Alpha",
                    trigger="When Instability >= 2",
                    effect_text="Bolsters allied cryptids when fear spikes.",
                ),
                Branch(
                    name="Courier of Sparks",
                    trigger="When belief is spent from a Territory",
                    effect_text="Carries a charge that refunds belief on successful strikes.",
                ),
            ],
        ),
    }
