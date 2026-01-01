"""Console simulator for the cryptid TCG prototype.

Run this script to execute a handful of automated turns showcasing
resource generation, stack resolution, and stubbed cryptid branches.
"""
from __future__ import annotations

import argparse

from tcg.game import GameState, initial_game


def run_simulation(turns: int = 3, deck_template: str = "balanced", until_win: bool = False, max_turns: int = 30) -> GameState:
    game = initial_game(deck_template)
    if until_win:
        log = game.play_until_over(max_turns=max_turns)
        print("\n".join(log))
    else:
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
        choices=[
            "balanced",
            "fear_pressure",
            "belief_ramp",
            "godline",
            "exploration",
            "urban_legends",
            "radiant_procession",
        ],
        help="Deck template to use",
    )
    parser.add_argument(
        "--until-win",
        action="store_true",
        help="Play until a player wins or the turn limit is reached",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=30,
        help="Maximum turns to simulate when playing until win",
    )
    args = parser.parse_args()
    run_simulation(turns=args.turns, deck_template=args.deck, until_win=args.until_win, max_turns=args.max_turns)
