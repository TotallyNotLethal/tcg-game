"""Skeleton game state and helpers for the console simulator."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import random

from .cards import Card, Cryptid, EventCard, GodCard, Move, TerritoryCard, starter_deck
from .phases import Phase, PhaseLoop
from .resources import ResourcePool
from .stack import GameStack, StackItem
from .territory import Territory, belief_territory, fear_territory


@dataclass
class PlayerState:
    name: str
    resources: ResourcePool = field(default_factory=ResourcePool)
    battlefield: List[Card] = field(default_factory=list)
    territories: List[object] = field(default_factory=list)
    territory_queue: List[Territory] = field(default_factory=list)
    deck: List[Card] = field(default_factory=list)
    hand: List[Card] = field(default_factory=list)
    influence: int = 20

    def play_territory(self, territory: Territory, stack: GameStack) -> str:
        self.territories.append(territory)
        result = territory.play(self.resources)
        stack.push(StackItem(description=f"{territory.name} enters and generates resources"))
        return result

    def settle_territory_card(self, card: TerritoryCard, stack: GameStack) -> str:
        self.territories.append(card)
        gain_text = card.play(self.resources)
        stack.push(StackItem(description=f"{self.name} settles {card.name}"))
        return gain_text

    def summon(self, cryptid: Cryptid, stack: GameStack) -> str:
        if not cryptid.can_play(self.resources):
            return f"{self.name} cannot afford {cryptid.name}."
        if not cryptid.pay_cost(self.resources):
            return f"{self.name} failed to pay cost for {cryptid.name}."
        cryptid.reset_health()
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

    def play_god(self, god: GodCard, stack: GameStack) -> str:
        if not god.can_play(self.resources):
            return f"{self.name} cannot afford {god.name}."
        if not god.pay_cost(self.resources):
            return f"{self.name} failed to pay cost for {god.name}."
        self.battlefield.append(god)
        stack.push(StackItem(description=f"{self.name} establishes {god.name}"))
        return f"{self.name} invokes {god.name}: {god.prayer_text or god.text}."

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
            if isinstance(card, TerritoryCard):
                self.hand.remove(card)
                return self.settle_territory_card(card, stack)
            if isinstance(card, Cryptid) and card.can_play(self.resources):
                self.hand.remove(card)
                return self.summon(card, stack)
            if isinstance(card, EventCard) and card.can_play(self.resources):
                self.hand.remove(card)
                return self.cast_event(card, stack)
            if isinstance(card, GodCard) and card.can_play(self.resources):
                self.hand.remove(card)
                return self.play_god(card, stack)
        return f"{self.name} holds position, hand: {', '.join(c.name for c in self.hand) or 'empty'}; resources: {self.resources.describe()}."

    def pray_with_gods(self, opponent: "PlayerState", stack: GameStack) -> List[str]:
        prayers: List[str] = []
        for card in self.battlefield:
            if isinstance(card, GodCard):
                prayers.append(f"{self.name} prays to {card.name}. {card.pray(self, opponent)}")
                stack.push(StackItem(description=f"{card.name} hears a prayer"))
        return prayers


@dataclass
class GameState:
    players: Tuple[PlayerState, PlayerState]
    stack: GameStack = field(default_factory=GameStack)
    phases: PhaseLoop = field(default_factory=PhaseLoop.default)
    turn: int = 1
    winner: Optional[PlayerState] = None
    game_over_reason: Optional[str] = None

    def step(self) -> List[str]:
        """Advance through one turn worth of phases with lightweight scripting."""

        log: List[str] = [f"-- Turn {self.turn} --"]
        active, opposing = self.players[self.turn % 2], self.players[(self.turn + 1) % 2]
        for phase in self.phases:
            if phase == Phase.START:
                log.extend(active.draw())
            elif phase == Phase.MAIN:
                log.extend(self._run_main_phase(active, opposing))
            elif phase == Phase.COMBAT:
                log.extend(self._run_combat_phase(active, opposing))
            elif phase == Phase.END:
                log.append(f"{active.name} ends the turn.")
        log.extend(self.stack.resolve_all())
        self._check_winner(log)
        self.turn += 1
        return log

    def play_until_over(self, max_turns: int = 30) -> List[str]:
        """Drive turns until a winner is found or a turn limit is reached."""

        full_log: List[str] = []
        while not self.winner and self.turn <= max_turns:
            full_log.extend(self.step())
        if not self.winner and self.turn > max_turns:
            self.game_over_reason = self.game_over_reason or f"Reached turn limit {max_turns}."
        if self.winner:
            full_log.append(f"{self.winner.name} wins! {self.game_over_reason or ''}".strip())
        elif self.game_over_reason:
            full_log.append(self.game_over_reason)
        return full_log

    def _run_main_phase(self, player: PlayerState, opponent: PlayerState) -> List[str]:
        log: List[str] = []
        # Auto-play first territory if available
        if player.territory_queue:
            territory = player.territory_queue.pop(0)
            log.append(player.play_territory(territory, self.stack))
        if player.hand:
            log.append(player.play_first_affordable(self.stack))
        else:
            log.append(f"{player.name} has no cards in hand.")
        log.extend(player.pray_with_gods(opponent, self.stack))
        return log

    def _run_combat_phase(self, attacker: PlayerState, defender: PlayerState) -> List[str]:
        log: List[str] = []
        attackers = [c for c in attacker.battlefield if isinstance(c, Cryptid) and c.current_health > 0]
        blockers = [c for c in defender.battlefield if isinstance(c, Cryptid) and c.current_health > 0]
        if not attackers:
            return [f"{attacker.name} has no cryptids to attack with."]

        attacker_card = sorted(attackers, key=lambda c: (c.stats.speed, c.stats.power), reverse=True)[0]
        move = self._select_move(attacker_card, attacker.resources)
        damage = move.damage + attacker_card.stats.power if move else attacker_card.stats.power

        if blockers:
            target = sorted(blockers, key=lambda c: (c.current_health, c.stats.defense))[0]
            prevented = min(target.stats.defense, damage)
            dealt = max(1, damage - target.stats.defense)
            target.current_health -= dealt
            log.append(
                f"{attacker.name}'s {attacker_card.name} uses {move.name if move else 'basic strike'} for {damage} damage "
                f"into {defender.name}'s {target.name} (DEF {target.stats.defense}), dealing {dealt} after prevention."
            )
            if target.current_health <= 0:
                log.append(f"{target.name} is defeated and sent to the scrapyard.")
                defender.battlefield.remove(target)
        else:
            defender.influence = max(0, defender.influence - damage)
            log.append(
                f"{attacker.name}'s {attacker_card.name} strikes directly for {damage} influence damage. "
                f"{defender.name} now at {defender.influence}."
            )

        return log

    def _select_move(self, cryptid: Cryptid, pool: ResourcePool) -> Optional[Move]:
        for mv in cryptid.moves:
            if pool.fear >= mv.cost_fear and pool.belief >= mv.cost_belief:
                pool.spend(fear=mv.cost_fear, belief=mv.cost_belief)
                return mv
        return None

    def _check_winner(self, log: List[str]) -> None:
        """Set the winner if a player hits zero influence or runs out of resources."""

        defeated: Optional[PlayerState] = None
        # Influence defeat
        for player in self.players:
            if player.influence <= 0:
                defeated = player
                self.game_over_reason = f"{player.name} is out of influence."
                break

        # Deck-out defeat if someone attempts to draw with an empty deck and an empty hand
        if not defeated:
            for player in self.players:
                if not player.deck and not player.hand and not any(isinstance(c, Cryptid) for c in player.battlefield):
                    defeated = player
                    self.game_over_reason = f"{player.name} is out of cards and creatures."
                    break

        if defeated:
            self.winner = self.players[0] if defeated is self.players[1] else self.players[1]
            log.append(self.game_over_reason)


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
