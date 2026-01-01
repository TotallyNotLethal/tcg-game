# tcg-game

Digital-only trading card game inspired by cryptids, folklore, and urban legends.

## Project Plan
See [PLAN.md](PLAN.md) for milestone breakdown, workstreams, and immediate next steps.

## Prototype Simulator
A lightweight console simulator exercises the phase loop, dual resources, exemplar cryptid branches, and a basic hand/deck flow.

```bash
python console_sim.py
```

This seeds two players (Alice and Bob) with shuffled starter decks, a small opening hand, and queued territories, then runs scripted turns to showcase:
- Phase progression (start, main, combat, end)
- Territory resource generation for Fear/Belief (including land-like Territory cards) and derived Instability
- Drawing from a deck into hand with automation for Territories, cryptids, events, and God permanents
- Summoning cryptids with power/defense/health/speed plus move sets that spend resources during combat
- Stack resolution logs for evolution placeholders, events, and God prayers, alongside lightweight combat that chips away at Influence totals

### Card Pool & Decks
- Cryptid library expanded with detailed combat stats, move sets, and branches (radiant dragons, gryphons, bog horrors, frost guardians, stormcallers, machines)
- Territory cards act like lands/energy and sit alongside queued Territories to feed the dual Fear/Belief economy
- God cards can be prayed to for blessings (healing, influence drain, guidance) and synergize with devotion events
- Exploration and ritual events fetch shrines, create temporary territories, or buff specific tribes for the combat step
- Deck templates: `balanced`, `fear_pressure`, `belief_ramp`, `godline`, `exploration` (pass template name to `initial_game` or `starter_deck`)
