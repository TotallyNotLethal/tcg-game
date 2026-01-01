# TCG Game — Delivery Plan

This plan turns the cryptid TCG concept into buildable work. It is scoped for a small cross-functional team (design, engineering, art/audio, QA/live ops) and assumes iterative delivery with weekly sprints.

## Product Goals
- Deliver a playable digital-only TCG themed around cryptids, emphasizing branching evolutions driven by match conditions.
- Prove dual-resource (Fear/Belief) economy and Territory-driven play feel accessible yet competitive.
- Ship a minimal ranked PvP loop with clear win conditions (Influence defeat, Mythic control, Legendary events).

## Release Milestones
1. **Prototype (Weeks 1–3):** Core rules engine, card data schema, console simulator, 20-card test set.
2. **Alpha (Weeks 4–8):** Basic client UI, matchmaking stub, first full cryptid set (30 cryptids, 60 support cards), telemetry hooks.
3. **Beta (Weeks 9–12):** Polished UX, tutorial, ranked queue, economy tuning tools, server scalability test.
4. **Launch (Weeks 13–16):** Content polish, live-ops dashboards, anti-cheat, marketing integrations, stability hardening.

## Workstreams and Tasks
### Game Design
- Finalize rules reference: branching evolution triggers, timing windows, revert rules.
- Define initial card pool: 30 cryptids with 2–4 branches each, 20 Territories, 30 Influence/Events, 10 Mutations.
- Write play patterns for Fear/Belief imbalance and Instability outcomes.
- Author Mythic/Form win conditions and Legendary event scripts.
- Create templated rules text library for consistent wording.

### Systems Engineering
- Implement rules engine with deterministic stack, phases, and evolution check windows.
- Build state machine for reversible evolutions and Mythic locks (permanent vs conditional).
- Create dual-resource manager (Fear/Belief) with Instability checks and Territory generation.
- Implement card parser and data schema (JSON/YAML) with validation tooling.
- Add simulation harness for AI/self-play to test balance levers.

### Client/UI
- Build match HUD: resources, Territories, cryptid status with visible counters and hidden timers (with telltale UI glow).
- Implement card browser/deckbuilder with filters for branches, Territory tags, and resource alignment.
- Add combat log and evolution reveal animations (digital-only effects).
- Tutorial flow highlighting evolution timing and resource imbalance risk.

### Server/Networking
- Matchmaking service (casual + ranked queues) with reconnect support.
- Authoritative game server validating all state transitions and random seeds.
- Telemetry and replay capture for balance review.
- Anti-cheat instrumentation and sanity checks on client commands.

### Content & Live Ops
- Weekly balance patch pipeline with card versioning and migration scripts.
- Event system for limited-time Legendary triggers or Territory weather overlays.
- Seasonal reward tracks tied to Mythic unlocks and win condition diversity.
- Localization-ready text pipeline; placeholder VO/SFX integration points.

### QA & Tooling
- Automated rules tests covering phase flow, evolution triggers, and reversion cases.
- Load tests for matchmaking and game server concurrency.
- Developer tools: in-match state inspector, forced evolution toggles, resource sliders.
- Visual regression tests for key UI views.

## Risks and Mitigations
- **Complexity of branching evolutions:** enforce templated trigger categories and shared helper functions; ship designer-facing validation tools.
- **Resource imbalance readability:** strong UI cues and hover help; tutorial scenarios showing Instability outcomes.
- **Content cadence:** establish weekly pipeline with targeted KPI monitoring; keep knobs (counters, thresholds) configurable without client patch.

## Next Actions (Sprint 1)
- Stand up rules engine skeleton with phase loop and stack.
- Implement core resources and Territory play (no evolution yet).
- Script three exemplar cryptids (Moth Sentinel, Bayou Serpent, Rustbound Hound) with stubbed branches.
- Build console-based simulator to exercise combat and resource generation.
- Draft UX wireframes for match HUD and evolution reveal moments.
