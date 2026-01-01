"""Console simulator for the cryptid TCG prototype.

Run this script to execute a handful of automated turns showcasing
resource generation, stack resolution, and stubbed cryptid branches.
"""
from __future__ import annotations

from tcg.game import GameState, initial_game


def run_simulation(turns: int = 3) -> GameState:
    game = initial_game()
    for _ in range(turns):
        log = game.step()
        print("\n".join(log))
    return game


if __name__ == "__main__":
    run_simulation()
