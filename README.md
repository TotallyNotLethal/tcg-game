# tcg-game

Digital-only trading card game inspired by cryptids, folklore, and urban legends.

## Project Plan
See [PLAN.md](PLAN.md) for milestone breakdown, workstreams, and immediate next steps.

## Prototype Simulator
A lightweight console simulator exercises the phase loop, dual resources, exemplar cryptid branches, and a basic hand/deck flow.

```bash
python console_sim.py
```

This seeds two players (Alice and Bob) with shuffled starter decks, a small opening hand, and queued territories, then runs three scripted turns to showcase:
- Phase progression (start, main, combat placeholder, end)
- Territory resource generation for Fear/Belief and derived Instability
- Drawing from a deck into hand with basic summoning automation for affordable cryptids and events
- Summoning exemplar cryptids and pushing their branch stubs onto the stack
- Stack resolution logs for evolution placeholders and event callouts

### Card Pool & Decks
- Cryptid library expanded with stats, tags, and branches (frost, storm, machine, aquatic, scholar themes)
- Event cards add lightweight stack interactions for the simulator
- Deck templates: `balanced`, `fear_pressure`, `belief_ramp` (pass template name to `initial_game` or `starter_deck`)
