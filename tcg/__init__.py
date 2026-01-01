"""Core package for the cryptid trading card game prototype."""

__all__ = [
    "Phase",
    "PhaseLoop",
    "GameStack",
    "StackItem",
    "ResourcePool",
    "Territory",
    "Card",
    "CardType",
    "Cryptid",
    "EventCard",
    "starter_deck",
    "build_deck",
    "card_library",
    "deck_templates",
    "GameState",
]

from .phases import Phase, PhaseLoop
from .stack import GameStack, StackItem
from .resources import ResourcePool
from .territory import Territory
from .cards import Card, CardType, Cryptid, EventCard, starter_deck, build_deck, card_library, deck_templates
from .game import GameState
