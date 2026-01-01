# tcg-game

Digital-only trading card game inspired by cryptids, folklore, and urban legends.

## Project Plan
See [PLAN.md](PLAN.md) for milestone breakdown, workstreams, and immediate next steps.

## Prototype Simulator
A lightweight console simulator exercises the phase loop, dual resources, and exemplar cryptid branches.

```bash
python console_sim.py
```

This seeds two players (Alice and Bob) with starter territories, then runs three scripted turns to showcase:
- Phase progression (start, main, combat placeholder, end)
- Territory resource generation for Fear/Belief and derived Instability
- Summoning exemplar cryptids and pushing their branch stubs onto the stack
- Stack resolution logs for evolution placeholders
