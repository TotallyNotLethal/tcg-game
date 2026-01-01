"""Console simulator for the cryptid TCG prototype.

Run this script to execute a handful of automated turns showcasing
resource generation, stack resolution, and stubbed cryptid branches.
"""
from __future__ import annotations

import argparse

from tcg.game import GameState, initial_game


def run_simulation(turns: int = 3, deck_template: str = "balanced") -> GameState:
    game = initial_game(deck_template)
    for _ in range(turns):
        log = game.step()
        print("\n".join(log))
    return game


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the cryptid TCG console simulator")
    parser.add_argument("--turns", type=int, default=3, help="Number of turns to simulate")
    parser.add_argument(
        "--deck",
        type=str,
        default="balanced",
        choices=["balanced", "fear_pressure", "belief_ramp", "godline", "exploration"],
        help="Deck template to use",
    )
    args = parser.parse_args()
    run_simulation(turns=args.turns, deck_template=args.deck)
