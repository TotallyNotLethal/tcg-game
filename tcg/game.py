"""Skeleton game state and helpers for the console simulator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from .cards import Card, CardType, Cryptid, exemplar_cryptids
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
        return f"{self.name} summons {cryptid.name}."


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
                log.append(f"{active.name} draws momentum (placeholder).")
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
        if player.territories:
            territory = player.territories.pop(0)
            log.append(player.play_territory(territory, self.stack))
        # Auto-summon the first affordable cryptid
        for card in list(player.battlefield):
            pass  # placeholder for future actions
        affordable = [c for c in exemplar_cryptids().values() if c.can_play(player.resources)]
        if affordable:
            log.append(player.summon(affordable[0], self.stack))
        else:
            log.append(f"{player.name} holds position, resources: {player.resources.describe()}.")
        return log


def initial_game() -> GameState:
    alice = PlayerState(name="Alice")
    bob = PlayerState(name="Bob")
    # Seed players with starter territories
    alice.territories.extend(
        [belief_territory("Lighthouse Perch", 1), fear_territory("Shadowed Dock", 1)]
    )
    bob.territories.extend([fear_territory("Forgotten Alley", 1), belief_territory("Candlelit Library", 1)])
    return GameState(players=(alice, bob))
