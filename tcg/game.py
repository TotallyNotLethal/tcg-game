"""Skeleton game state and helpers for the console simulator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import random

from .cards import Card, Cryptid, EventCard, starter_deck
from .phases import Phase, PhaseLoop
from .resources import ResourcePool
from .stack import GameStack, StackItem
from .territory import Territory, belief_territory, fear_territory


@dataclass
class PlayerState:
    name: str
    resources: ResourcePool = field(default_factory=ResourcePool)
    battlefield: List[Card] = field(default_factory=list)
    territories: List[Territory] = field(default_factory=list)
    territory_queue: List[Territory] = field(default_factory=list)
    deck: List[Card] = field(default_factory=list)
    hand: List[Card] = field(default_factory=list)

    def play_territory(self, territory: Territory, stack: GameStack) -> str:
        self.territories.append(territory)
        result = territory.play(self.resources)
        stack.push(StackItem(description=f"{territory.name} enters and generates resources"))
        return result

    def summon(self, cryptid: Cryptid, stack: GameStack) -> str:
        if not cryptid.can_play(self.resources):
            return f"{self.name} cannot afford {cryptid.name}."
        if not cryptid.pay_cost(self.resources):
            return f"{self.name} failed to pay cost for {cryptid.name}."
        self.battlefield.append(cryptid)
        for trigger in cryptid.spawn_triggers():
            stack.push(trigger)
        return f"{self.name} summons {cryptid.name} ({cryptid.stats.describe()})."

    def cast_event(self, event: EventCard, stack: GameStack) -> str:
        if not event.can_play(self.resources):
            return f"{self.name} cannot afford {event.name}."
        if not event.pay_cost(self.resources):
            return f"{self.name} failed to pay cost for {event.name}."
        stack.push(event.stack_item(self.name))
        return f"{self.name} casts {event.name}."

    def draw(self, count: int = 1) -> List[str]:
        log: List[str] = []
        for _ in range(count):
            if not self.deck:
                log.append(f"{self.name} would draw but the deck is empty.")
                break
            card = self.deck.pop(0)
            self.hand.append(card)
            log.append(f"{self.name} draws {card.name}.")
        return log

    def play_first_affordable(self, stack: GameStack) -> str:
        for card in list(self.hand):
            if isinstance(card, Cryptid) and card.can_play(self.resources):
                self.hand.remove(card)
                return self.summon(card, stack)
            if isinstance(card, EventCard) and card.can_play(self.resources):
                self.hand.remove(card)
                return self.cast_event(card, stack)
        return f"{self.name} holds position, hand: {', '.join(c.name for c in self.hand) or 'empty'}; resources: {self.resources.describe()}."


@dataclass
class GameState:
    players: Tuple[PlayerState, PlayerState]
    stack: GameStack = field(default_factory=GameStack)
    phases: PhaseLoop = field(default_factory=PhaseLoop.default)
    turn: int = 1

    def step(self) -> List[str]:
        """Advance through one turn worth of phases with lightweight scripting."""

        log: List[str] = [f"-- Turn {self.turn} --"]
        active, opposing = self.players[self.turn % 2], self.players[(self.turn + 1) % 2]
        for phase in self.phases:
            if phase == Phase.START:
                log.extend(active.draw())
            elif phase == Phase.MAIN:
                log.extend(self._run_main_phase(active))
            elif phase == Phase.COMBAT:
                log.append("Combat is not implemented yet.")
            elif phase == Phase.END:
                log.append(f"{active.name} ends the turn.")
        log.extend(self.stack.resolve_all())
        self.turn += 1
        return log

    def _run_main_phase(self, player: PlayerState) -> List[str]:
        log: List[str] = []
        # Auto-play first territory if available
        if player.territory_queue:
            territory = player.territory_queue.pop(0)
            log.append(player.play_territory(territory, self.stack))
        if player.hand:
            log.append(player.play_first_affordable(self.stack))
        else:
            log.append(f"{player.name} has no cards in hand.")
        return log


def initial_game(deck_template: str = "balanced") -> GameState:
    alice = PlayerState(name="Alice")
    bob = PlayerState(name="Bob")
    # Seed players with starter territories
    alice.territory_queue.extend(
        [belief_territory("Lighthouse Perch", 1), fear_territory("Shadowed Dock", 1), belief_territory("Foggy Causeway", 1)]
    )
    bob.territory_queue.extend(
        [fear_territory("Forgotten Alley", 1), belief_territory("Candlelit Library", 1), fear_territory("Storm Drain", 1)]
    )
    for player in (alice, bob):
        player.deck.extend(starter_deck(deck_template))
        random.shuffle(player.deck)
        player.draw(3)
    return GameState(players=(alice, bob))
