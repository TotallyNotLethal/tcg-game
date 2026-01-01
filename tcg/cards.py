"""Card definitions and exemplar cryptids for the prototype."""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional

from .resources import ResourcePool
from .stack import StackItem


class CardType(Enum):
    TERRITORY = auto()
    CRYPTID = auto()
    EVENT = auto()
    GOD = auto()


@dataclass
class CombatStats:
    power: int = 0
    resilience: int = 1
    health: int = 3
    defense: int = 0
    speed: int = 1

    def describe(self) -> str:
        return f"{self.power}/{self.resilience} (HP {self.health}, DEF {self.defense}, SPD {self.speed})"


@dataclass
class Move:
    name: str
    damage: int
    text: str
    cost_fear: int = 0
    cost_belief: int = 0

    def describe(self) -> str:
        costs: List[str] = []
        if self.cost_fear:
            costs.append(f"{self.cost_fear} Fear")
        if self.cost_belief:
            costs.append(f"{self.cost_belief} Belief")
        cost_text = f" (Cost: {', '.join(costs)})" if costs else ""
        return f"{self.name}: {self.damage} dmg{cost_text} — {self.text}"


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
class TerritoryCard(Card):
    fear_yield: int = 0
    belief_yield: int = 0

    def play(self, pool: ResourcePool) -> str:
        pool.add(fear=self.fear_yield, belief=self.belief_yield)
        fear_text = f"{self.fear_yield} Fear" if self.fear_yield else None
        belief_text = f"{self.belief_yield} Belief" if self.belief_yield else None
        yields = ", ".join(v for v in [fear_text, belief_text] if v)
        return f"{self.name} settles and yields {yields}."


@dataclass
class Branch:
    name: str
    trigger: str
    effect_text: str


@dataclass
class Cryptid(Card):
    branches: List[Branch] = field(default_factory=list)
    stats: CombatStats = field(default_factory=CombatStats)
    moves: List[Move] = field(default_factory=list)
    current_health: int = field(init=False)

    def __post_init__(self) -> None:
        self.current_health = self.stats.health

    def spawn_triggers(self) -> List[StackItem]:
        return [
            StackItem(
                description=f"Evolution: {branch.name}",
                resolve=lambda b=branch: f"{self.name} notes future branch '{b.name}' — {b.effect_text}",
            )
            for branch in self.branches
        ]

    def reset_health(self) -> None:
        self.current_health = self.stats.health


@dataclass
class EventCard(Card):
    impact_text: str = ""

    def stack_item(self, owner: str) -> StackItem:
        return StackItem(
            description=f"{owner} casts {self.name}",
            resolve=lambda: f"{self.name} resolves: {self.impact_text or self.text}",
        )


@dataclass
class GodCard(Card):
    prayer_text: str = ""
    prayer_effect: Optional[Callable[[object, object], str]] = None

    def pray(self, player: object, opponent: object) -> str:
        if self.prayer_effect:
            return self.prayer_effect(player, opponent)
        return f"{self.name} hears the prayer but remains silent."


# Exemplar cryptids with stubbed branches for sprint 1

def cryptid_pool() -> Dict[str, Cryptid]:
    """Expanded library of cryptids with stats, health, and moves."""

    return {
        "Moth Sentinel": Cryptid(
            name="Moth Sentinel",
            type=CardType.CRYPTID,
            cost_belief=1,
            text="Watchful guardian that pivots between omen and protector.",
            tags=["Guardian", "Glide"],
            stats=CombatStats(power=1, resilience=2, health=4, defense=1, speed=2),
            moves=[
                Move(name="Wing Buffet", damage=1, text="Soft strike that chips away at defenses."),
                Move(name="Beacon Flash", damage=2, cost_belief=1, text="Dazzle foes and inspire allies."),
            ],
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
            stats=CombatStats(power=2, resilience=1, health=5, speed=1),
            moves=[
                Move(name="Tail Whip", damage=2, text="Bludgeon foes caught unaware."),
                Move(name="Constrict", damage=3, cost_fear=1, text="Squeeze targets and slow them down."),
            ],
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
            stats=CombatStats(power=2, resilience=2, health=5, defense=1, speed=2),
            moves=[
                Move(name="Scrap Bite", damage=2, text="Jagged metal bite deals steady damage."),
                Move(name="Charge Dash", damage=3, cost_belief=1, text="Dash between enemies to clear the path."),
            ],
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
            stats=CombatStats(power=3, resilience=4, health=8, defense=2, speed=1),
            moves=[
                Move(name="Ice Fist", damage=3, text="Crushes armor with frigid knuckles."),
                Move(name="Avalanche", damage=4, cost_fear=1, text="Smash everything caught below."),
            ],
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
            stats=CombatStats(power=1, resilience=3, health=4, speed=2),
            moves=[
                Move(name="Ink Splash", damage=1, text="Obscures vision, buying time."),
                Move(name="Annotated Strike", damage=2, cost_belief=1, text="Leverages lore to pierce defenses."),
            ],
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
            stats=CombatStats(power=2, resilience=2, health=5, defense=1, speed=3),
            moves=[
                Move(name="Trail Cut", damage=2, text="Carves a clear line to traverse."),
                Move(name="Bramble Volley", damage=3, cost_belief=1, text="Thorns lash out at intruders."),
            ],
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
            stats=CombatStats(power=1, resilience=1, health=3, speed=3),
            moves=[
                Move(name="Rusty Swipe", damage=1, text="Nicks opponents while darting between cover."),
                Move(name="Rail Spike", damage=2, cost_fear=1, text="Hurls a spike for a precise puncture."),
            ],
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
            stats=CombatStats(power=2, resilience=1, health=4, speed=4),
            moves=[
                Move(name="Foxfire", damage=2, text="Blue flames flicker and distract."),
                Move(name="Mirage Step", damage=1, cost_belief=1, text="Phase to dodge and counter."),
            ],
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
            stats=CombatStats(power=3, resilience=1, health=4, speed=4),
            moves=[
                Move(name="Sawblades", damage=3, text="Slices through weak points."),
                Move(name="Detonate Core", damage=4, cost_fear=1, text="Explodes for massive area damage."),
            ],
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
            stats=CombatStats(power=2, resilience=3, health=6, defense=1, speed=2),
            moves=[
                Move(name="Frost Lash", damage=2, text="Chills attackers, slowing them down."),
                Move(name="Root Snare", damage=1, cost_belief=1, text="Immobilizes foes briefly."),
            ],
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
            stats=CombatStats(power=2, resilience=3, health=6, defense=1, speed=3),
            moves=[
                Move(name="Harpoon", damage=2, text="Pierces lightly armored threats."),
                Move(name="Tidal Slam", damage=3, cost_fear=1, text="Swings with the force of the tide."),
            ],
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
            stats=CombatStats(power=3, resilience=3, health=7, defense=1, speed=3),
            moves=[
                Move(name="Static Burst", damage=3, text="Crackling blast that arcs between foes."),
                Move(name="Cyclone Spear", damage=4, cost_fear=1, text="Spears foes with gale force."),
            ],
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
        "Ridgeback Gryphon": Cryptid(
            name="Ridgeback Gryphon",
            type=CardType.CRYPTID,
            cost_belief=2,
            cost_fear=1,
            text="Wind-riding gryphon that hunts in mountainous passes.",
            tags=["Sky", "Predator"],
            stats=CombatStats(power=3, resilience=2, health=6, defense=1, speed=4),
            moves=[
                Move(name="Sky Talons", damage=3, text="Sweeps across the battlefield."),
                Move(name="Dive Bomb", damage=5, cost_belief=1, text="High-speed dive that crushes armor."),
            ],
            branches=[
                Branch(
                    name="Mountain King",
                    trigger="When you control 3+ Territories",
                    effect_text="Gains flying dominance and +2 speed.",
                ),
                Branch(
                    name="Stormrider",
                    trigger="When an opponent casts an Event",
                    effect_text="May counter the Event unless they pay 2 belief.",
                ),
            ],
        ),
        "Bog Lurker": Cryptid(
            name="Bog Lurker",
            type=CardType.CRYPTID,
            cost_fear=2,
            text="Ambusher that emerges from deep fen water.",
            tags=["Aquatic", "Ambush"],
            stats=CombatStats(power=3, resilience=2, health=6, speed=2),
            moves=[
                Move(name="Drag Down", damage=3, text="Pulls foes into the marsh."),
                Move(name="Murkwave", damage=4, cost_fear=1, text="Sends a stinging wave of sludge."),
            ],
            branches=[
                Branch(
                    name="Sunless Grip",
                    trigger="When a Territory is sacrificed",
                    effect_text="Gains +2 power and pulls an enemy cryptid down.",
                ),
                Branch(
                    name="Fen Guardian",
                    trigger="When you control a God",
                    effect_text="Gains ward and heals 2.",
                ),
            ],
        ),
        "Sunscale Drake": Cryptid(
            name="Sunscale Drake",
            type=CardType.CRYPTID,
            cost_belief=2,
            text="Solar-infused drake that rewards devotion.",
            tags=["Dragon", "Radiant"],
            stats=CombatStats(power=2, resilience=2, health=5, defense=1, speed=3),
            moves=[
                Move(name="Radiant Bite", damage=3, text="Sears with holy light."),
                Move(name="Solar Flare", damage=4, cost_belief=1, text="Blinds foes and buffs allies."),
            ],
            branches=[
                Branch(
                    name="Dawnbound",
                    trigger="When you pray to a God",
                    effect_text="Gain +1/+1 until end of turn.",
                ),
                Branch(
                    name="Zenith Flight",
                    trigger="When you control 4+ belief",
                    effect_text="Becomes untouchable for a turn.",
                ),
            ],
        ),
        "Night Weaver": Cryptid(
            name="Night Weaver",
            type=CardType.CRYPTID,
            cost_fear=2,
            cost_belief=1,
            text="Spider-like horror spinning dread and destiny.",
            tags=["Shadow", "Web"],
            stats=CombatStats(power=2, resilience=3, health=7, defense=2, speed=2),
            moves=[
                Move(name="Silk Bolt", damage=2, text="Sticky strands sap speed."),
                Move(name="Fear Venom", damage=4, cost_fear=1, text="Poisons morale and flesh."),
            ],
            branches=[
                Branch(
                    name="Threads of Fate",
                    trigger="When an opponent draws",
                    effect_text="Force them to discard or lose 2 influence.",
                ),
                Branch(
                    name="Dread Loom",
                    trigger="When you resolve an Event",
                    effect_text="Tap an opposing cryptid and drain 1 belief.",
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
        "Trailblaze Expedition": EventCard(
            name="Trailblaze Expedition",
            type=CardType.EVENT,
            cost_belief=1,
            text="Scout ahead for fresh ground and relics.",
            tags=["Exploration"],
            impact_text="Reveal the top 2 cards; put a Territory or God into hand, the rest on the bottom.",
        ),
        "Prayer Vigil": EventCard(
            name="Prayer Vigil",
            type=CardType.EVENT,
            cost_belief=1,
            text="Chanting circles gather around sacred effigies.",
            tags=["Devotion"],
            impact_text="Gain 1 belief and trigger one of your Gods' prayer effects for free.",
        ),
        "Stormwatch Report": EventCard(
            name="Stormwatch Report",
            type=CardType.EVENT,
            cost_fear=1,
            text="Record shifting winds for aerial allies.",
            tags=["Sky", "Intel"],
            impact_text="Scry 2, then your flying cryptids gain +1 power this turn.",
        ),
        "Relic Harvest": EventCard(
            name="Relic Harvest",
            type=CardType.EVENT,
            cost_belief=1,
            cost_fear=1,
            text="Excavate forgotten stones to feed shrines.",
            tags=["Ritual", "Exploration"],
            impact_text="Create a basic Territory token that taps for either Fear or Belief.",
        ),
    }


def territory_card_pool() -> Dict[str, TerritoryCard]:
    return {
        "Sacred Grove": TerritoryCard(
            name="Sacred Grove",
            type=CardType.TERRITORY,
            text="Ancient trees humming with quiet belief.",
            tags=["Forest", "Blessed"],
            belief_yield=1,
        ),
        "Haunted Cairn": TerritoryCard(
            name="Haunted Cairn",
            type=CardType.TERRITORY,
            text="Fallen stones that leak dread.",
            tags=["Ruin", "Curse"],
            fear_yield=1,
        ),
        "Dawning Shrine": TerritoryCard(
            name="Dawning Shrine",
            type=CardType.TERRITORY,
            text="Shrine that bridges belief and fear.",
            tags=["Shrine", "Dual"],
            belief_yield=1,
            fear_yield=1,
        ),
        "Industrial Ruins": TerritoryCard(
            name="Industrial Ruins",
            type=CardType.TERRITORY,
            text="Broken machinery that still sparks with menace.",
            tags=["Machine", "Urban"],
            fear_yield=1,
        ),
    }


def god_pool() -> Dict[str, GodCard]:
    return {
        "Aurora Paragon": GodCard(
            name="Aurora Paragon",
            type=CardType.GOD,
            cost_belief=2,
            text="Radiant deity of dawn and careful hope.",
            tags=["Radiant", "God"],
            prayer_text="Blessing heals allies and guides believers.",
            prayer_effect=lambda player, opponent: _pray_aurora(player),
        ),
        "Dread Patron": GodCard(
            name="Dread Patron",
            type=CardType.GOD,
            cost_fear=2,
            text="Shadow that feeds on whispered offerings.",
            tags=["Shadow", "God"],
            prayer_text="Demands fear, grants ruthless strikes.",
            prayer_effect=lambda player, opponent: _pray_dread(player, opponent),
        ),
        "Labyrinth Mother": GodCard(
            name="Labyrinth Mother",
            type=CardType.GOD,
            cost_belief=1,
            cost_fear=1,
            text="Twisted matron of hidden roads and riddles.",
            tags=["Maze", "God"],
            prayer_text="Rewards explorers with insight and safety.",
            prayer_effect=lambda player, opponent: _pray_labyrinth(player),
        ),
    }


def _pray_aurora(player: object) -> str:
    """Grant belief and heal the first cryptid on the battlefield."""

    player.resources.add(belief=1)
    healed = False
    for card in getattr(player, "battlefield", []):
        if isinstance(card, Cryptid):
            card.current_health = min(card.stats.health, card.current_health + 1)
            healed = True
            break
    heal_text = " and heals an ally" if healed else ""
    return f"Aurora Paragon grants 1 belief{heal_text}."


def _pray_dread(player: object, opponent: object) -> str:
    player.resources.add(fear=1)
    if hasattr(opponent, "influence"):
        opponent.influence = max(0, opponent.influence - 2)
        return "Dread Patron claims 1 fear from you and siphons 2 influence from the foe."
    return "Dread Patron claims 1 fear and rumbles hungrily."


def _pray_labyrinth(player: object) -> str:
    player.resources.add(belief=1)
    if getattr(player, "hand", None):
        return "Labyrinth Mother guides your explorers; you gain 1 belief and safeguard your hand."
    return "Labyrinth Mother grants 1 belief and whispers a safe path forward."


def card_library() -> Dict[str, Card]:
    library: Dict[str, Card] = {}
    library.update(cryptid_pool())
    library.update(event_pool())
    library.update(territory_card_pool())
    library.update(god_pool())
    return library


def deck_templates() -> Dict[str, Dict[str, int]]:
    return {
        "balanced": {
            "Sacred Grove": 4,
            "Haunted Cairn": 2,
            "Dawning Shrine": 2,
            "Moth Sentinel": 2,
            "Bayou Serpent": 2,
            "Redwood Pathfinder": 2,
            "Harbor Sentry": 2,
            "Lantern Festival": 2,
            "Shadow Report": 2,
            "Trailblaze Expedition": 2,
            "Instability Pulse": 2,
        },
        "fear_pressure": {
            "Haunted Cairn": 4,
            "Industrial Ruins": 2,
            "Bayou Serpent": 3,
            "Rustbound Hound": 2,
            "Glacier Yeti": 2,
            "Tunnel Scrapper": 3,
            "Clockwork Mantis": 2,
            "Storm Herald": 2,
            "Shadow Report": 3,
            "Mire Ambush": 2,
            "Dread Patron": 2,
            "Relic Harvest": 2,
        },
        "belief_ramp": {
            "Sacred Grove": 4,
            "Dawning Shrine": 2,
            "Moth Sentinel": 2,
            "Candlewick Scholar": 2,
            "Redwood Pathfinder": 3,
            "Frostfern Dryad": 2,
            "Harbor Sentry": 2,
            "Mistveil Kitsune": 2,
            "Sunscale Drake": 2,
            "Aurora Paragon": 2,
            "Lantern Festival": 3,
            "Guided Study": 3,
            "Prayer Vigil": 2,
        },
        "godline": {
            "Sacred Grove": 4,
            "Haunted Cairn": 2,
            "Dawning Shrine": 4,
            "Aurora Paragon": 2,
            "Dread Patron": 2,
            "Labyrinth Mother": 2,
            "Sunscale Drake": 2,
            "Night Weaver": 2,
            "Ridgeback Gryphon": 2,
            "Trailblaze Expedition": 3,
            "Prayer Vigil": 3,
            "Instability Pulse": 2,
        },
        "exploration": {
            "Sacred Grove": 2,
            "Haunted Cairn": 2,
            "Dawning Shrine": 2,
            "Industrial Ruins": 2,
            "Redwood Pathfinder": 3,
            "Bog Lurker": 2,
            "Ridgeback Gryphon": 2,
            "Rustbound Hound": 2,
            "Trailblaze Expedition": 4,
            "Relic Harvest": 3,
            "Stormwatch Report": 2,
            "Labyrinth Mother": 2,
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
