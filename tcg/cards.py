"""Card definitions and exemplar cryptids for the prototype."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional

from .resources import ResourcePool
from .stack import StackItem


class CardType(Enum):
    TERRITORY = auto()
    CRYPTID = auto()
    EVENT = auto()


@dataclass
class CombatStats:
    power: int = 0
    resilience: int = 1

    def describe(self) -> str:
        return f"{self.power}/{self.resilience}"


@dataclass
class Card:
    name: str
    type: CardType
    cost_fear: int = 0
    cost_belief: int = 0
    text: str = ""
    faction: str = ""
    tags: List[str] = field(default_factory=list)

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
    branches: List[Branch] = field(default_factory=list)
    stats: CombatStats = field(default_factory=CombatStats)

    def spawn_triggers(self) -> List[StackItem]:
        return [
            StackItem(
                description=f"Evolution: {branch.name}",
                resolve=lambda b=branch: f"{self.name} notes future branch '{b.name}' — {b.effect_text}",
            )
            for branch in self.branches
        ]


@dataclass
class EventCard(Card):
    impact_text: str = ""

    def stack_item(self, owner: str) -> StackItem:
        return StackItem(
            description=f"{owner} casts {self.name}",
            resolve=lambda: f"{self.name} resolves: {self.impact_text or self.text}",
        )


# Exemplar cryptids with stubbed branches for sprint 1

def cryptid_pool() -> Dict[str, Cryptid]:
    """Expanded library of cryptids with stats and branches."""

    return {
        "Moth Sentinel": Cryptid(
            name="Moth Sentinel",
            type=CardType.CRYPTID,
            cost_belief=1,
            text="Watchful guardian that pivots between omen and protector.",
            tags=["Guardian", "Glide"],
            stats=CombatStats(power=1, resilience=2),
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
            tags=["Aquatic", "Constriction"],
            stats=CombatStats(power=2, resilience=1),
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
            tags=["Machine", "Tracker"],
            stats=CombatStats(power=2, resilience=2),
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
        "Glacier Yeti": Cryptid(
            name="Glacier Yeti",
            type=CardType.CRYPTID,
            cost_fear=2,
            text="Thaws slowly, growing denser as Instability rises.",
            tags=["Frost", "Guardian"],
            stats=CombatStats(power=3, resilience=4),
            branches=[
                Branch(
                    name="Avalanche Roar",
                    trigger="When fear exceeds belief",
                    effect_text="Crushes weaker foes and taps opposing Territories.",
                ),
                Branch(
                    name="Icebound Pact",
                    trigger="When belief catches up",
                    effect_text="Stabilizes by converting extra fear into belief.",
                ),
            ],
        ),
        "Candlewick Scholar": Cryptid(
            name="Candlewick Scholar",
            type=CardType.CRYPTID,
            cost_belief=2,
            text="Lore keeper that rewards balanced play.",
            tags=["Scholar", "Support"],
            stats=CombatStats(power=1, resilience=3),
            branches=[
                Branch(
                    name="Footnote of Legends",
                    trigger="When you cast an Event",
                    effect_text="Copies the next Event's effect text for free.",
                ),
                Branch(
                    name="Quiet Revelation",
                    trigger="When Instability hits 0",
                    effect_text="Draws two cards and shields an ally.",
                ),
            ],
        ),
        "Redwood Pathfinder": Cryptid(
            name="Redwood Pathfinder",
            type=CardType.CRYPTID,
            cost_belief=1,
            text="Navigator attuned to safe Territories.",
            tags=["Scout", "Forest"],
            stats=CombatStats(power=2, resilience=2),
            branches=[
                Branch(
                    name="Overgrowth Trail",
                    trigger="When a Territory enters",
                    effect_text="Adds a belief and readies the Territory.",
                ),
                Branch(
                    name="Brambleguard",
                    trigger="When an ally is targeted",
                    effect_text="Redirects harm and gains resilience until end of turn.",
                ),
            ],
        ),
        "Tunnel Scrapper": Cryptid(
            name="Tunnel Scrapper",
            type=CardType.CRYPTID,
            cost_fear=1,
            text="Small but relentless scavenger that thrives in darkness.",
            tags=["Urban", "Machine"],
            stats=CombatStats(power=1, resilience=1),
            branches=[
                Branch(
                    name="Lantern Swipe",
                    trigger="When belief is spent",
                    effect_text="Steals 1 belief and converts it to fear for you.",
                ),
                Branch(
                    name="Rustle in the Rails",
                    trigger="When you discard",
                    effect_text="Returns to play and pings the opponent.",
                ),
            ],
        ),
        "Mistveil Kitsune": Cryptid(
            name="Mistveil Kitsune",
            type=CardType.CRYPTID,
            cost_belief=1,
            cost_fear=1,
            text="Illusionist fox that manipulates perceptions.",
            tags=["Spirit", "Illusion"],
            stats=CombatStats(power=2, resilience=1),
            branches=[
                Branch(
                    name="Phantom Parade",
                    trigger="When you gain belief",
                    effect_text="Creates a 1/1 illusion copy until end of turn.",
                ),
                Branch(
                    name="Mirror Misstep",
                    trigger="When targeted",
                    effect_text="Phases out and taxes the opposing player 1 fear.",
                ),
            ],
        ),
        "Clockwork Mantis": Cryptid(
            name="Clockwork Mantis",
            type=CardType.CRYPTID,
            cost_fear=2,
            text="Precision striker that ramps up with each resolve.",
            tags=["Machine", "Precision"],
            stats=CombatStats(power=3, resilience=1),
            branches=[
                Branch(
                    name="Spare Parts Surge",
                    trigger="When an artifact enters",
                    effect_text="Builds +1 power counters equal to Instability.",
                ),
                Branch(
                    name="Detonate Core",
                    trigger="When destroyed",
                    effect_text="Deals 3 damage to any target and redistributes power.",
                ),
            ],
        ),
        "Frostfern Dryad": Cryptid(
            name="Frostfern Dryad",
            type=CardType.CRYPTID,
            cost_belief=2,
            text="Steadies the board by weaving chill growths.",
            tags=["Forest", "Frost"],
            stats=CombatStats(power=2, resilience=3),
            branches=[
                Branch(
                    name="Hushed Canopy",
                    trigger="When belief > fear",
                    effect_text="Allies gain ward while instability is low.",
                ),
                Branch(
                    name="Brittle Bloom",
                    trigger="When fear > belief",
                    effect_text="Root opposing cryptids in place for a turn.",
                ),
            ],
        ),
        "Harbor Sentry": Cryptid(
            name="Harbor Sentry",
            type=CardType.CRYPTID,
            cost_belief=1,
            cost_fear=1,
            text="Keeps watch over tidal routes, syncing with events.",
            tags=["Aquatic", "Guardian"],
            stats=CombatStats(power=2, resilience=3),
            branches=[
                Branch(
                    name="High Tide Warning",
                    trigger="When an Event is cast",
                    effect_text="Readies and gains +1 power for the turn.",
                ),
                Branch(
                    name="Moonlit Barrage",
                    trigger="At end step",
                    effect_text="If two or more Events resolved, deal 2 damage to opponent.",
                ),
            ],
        ),
        "Storm Herald": Cryptid(
            name="Storm Herald",
            type=CardType.CRYPTID,
            cost_fear=2,
            cost_belief=1,
            text="Calls tempests when Instability surges.",
            tags=["Storm", "Mythic"],
            stats=CombatStats(power=3, resilience=3),
            branches=[
                Branch(
                    name="Thunderclap",
                    trigger="When Instability >= 3",
                    effect_text="Deal 2 to all opposing cryptids.",
                ),
                Branch(
                    name="Eye of the Storm",
                    trigger="When Instability returns to 1",
                    effect_text="You and opponent each draw a card and reset resources.",
                ),
            ],
        ),
    }


def event_pool() -> Dict[str, EventCard]:
    return {
        "Lantern Festival": EventCard(
            name="Lantern Festival",
            type=CardType.EVENT,
            cost_belief=1,
            text="Illuminate the night and calm fears.",
            tags=["Ritual"],
            impact_text="Gain 1 belief and reduce Instability by 1 until end of turn.",
        ),
        "Shadow Report": EventCard(
            name="Shadow Report",
            type=CardType.EVENT,
            cost_fear=1,
            text="Relay whispered rumors to stoke anxiety.",
            tags=["Intel"],
            impact_text="Opponent loses 1 belief and you gain 1 fear.",
        ),
        "Field Repairs": EventCard(
            name="Field Repairs",
            type=CardType.EVENT,
            cost_belief=1,
            text="Patch up machine-aligned cryptids.",
            tags=["Machine"],
            impact_text="Restore 2 resilience worth of damage among your machines.",
        ),
        "Mire Ambush": EventCard(
            name="Mire Ambush",
            type=CardType.EVENT,
            cost_fear=2,
            text="Spring from the swamp at the perfect moment.",
            tags=["Trap"],
            impact_text="Deal 2 damage to an attacking cryptid.",
        ),
        "Guided Study": EventCard(
            name="Guided Study",
            type=CardType.EVENT,
            cost_belief=2,
            text="Delve into lore for answers.",
            tags=["Scholar"],
            impact_text="Draw two cards, then discard one.",
        ),
        "Instability Pulse": EventCard(
            name="Instability Pulse",
            type=CardType.EVENT,
            cost_fear=1,
            cost_belief=1,
            text="Ride the edge between courage and dread.",
            tags=["Volatile"],
            impact_text="Each player gains 1 fear and 1 belief, then you may ready a Territory.",
        ),
    }


def card_library() -> Dict[str, Card]:
    library: Dict[str, Card] = {}
    library.update(cryptid_pool())
    library.update(event_pool())
    return library


def deck_templates() -> Dict[str, Dict[str, int]]:
    return {
        "balanced": {
            "Moth Sentinel": 2,
            "Bayou Serpent": 2,
            "Rustbound Hound": 2,
            "Redwood Pathfinder": 2,
            "Harbor Sentry": 2,
            "Lantern Festival": 2,
            "Shadow Report": 2,
            "Guided Study": 2,
            "Instability Pulse": 2,
            "Frostfern Dryad": 2,
        },
        "fear_pressure": {
            "Bayou Serpent": 3,
            "Rustbound Hound": 2,
            "Glacier Yeti": 2,
            "Tunnel Scrapper": 3,
            "Clockwork Mantis": 2,
            "Storm Herald": 2,
            "Shadow Report": 3,
            "Mire Ambush": 2,
            "Instability Pulse": 1,
        },
        "belief_ramp": {
            "Moth Sentinel": 2,
            "Candlewick Scholar": 2,
            "Redwood Pathfinder": 3,
            "Frostfern Dryad": 2,
            "Harbor Sentry": 2,
            "Mistveil Kitsune": 2,
            "Lantern Festival": 3,
            "Guided Study": 3,
            "Field Repairs": 2,
        },
    }


def build_deck(template_name: str = "balanced") -> List[Card]:
    templates = deck_templates()
    if template_name not in templates:
        raise ValueError(f"Unknown deck template: {template_name}")

    library = card_library()
    deck: List[Card] = []
    for card_name, count in templates[template_name].items():
        if card_name not in library:
            raise ValueError(f"Card '{card_name}' not in library")
        for _ in range(count):
            deck.append(copy.deepcopy(library[card_name]))
    return deck


# Backwards-compatible starter for console sims

def starter_deck(template_name: str = "balanced") -> List[Card]:
    """Prototype-friendly deck list using named templates."""

    return build_deck(template_name)


# Maintain exemplar mapping for legacy callers

def exemplar_cryptids() -> Dict[str, Cryptid]:
    return {
        name: card for name, card in cryptid_pool().items() if name in {"Moth Sentinel", "Bayou Serpent", "Rustbound Hound"}
    }
