# Handoff — after the 2026-07-21 audit sessions

Point a fresh session at this file. It is deliberately short; everything here links to the
document that actually holds the detail.

## Repo state

- **19 commits** on `ac151fc..b4b0499`. Working tree clean.
- **17 are pushed.** `origin/main` is at `f945562`. The background flake-fix session pushed
  `main`, which carried the day's work up with it. `7a8fafe` and `b4b0499` are still local.
- Tests **528/528** (`Game.sln`). Mod builds 0 warnings. The intermittent
  `Game.Simulation.Tests` failure is fixed (`d5bed21`) — two classes racing over the
  process-wide static `GameplayEventFeed`, now serialised by an xUnit collection.
- Mod config surface: **107 → 73 keys** across the day.

## Three things that will bite if you don't know them

1. **The live comfy-gateway runs from the RETIRED repo.** `docker inspect`
   `comfy-valheim-lab-comfy-gateway-1` reports
   `config_files=C:\work\comfy\fieldlab\autonomous\valheim-lab.compose.yml`,
   `COMFY_ROOT=C:/work/comfy`, image built **2026-07-15**. Edits in `baseline` do **not** reach
   the running `:8720` surface — its command still names `toolsurface.matrix` even though the
   module is gone from this repo. This is the P7 problem again, for a local service.
2. **Do not delete `fieldlab/autonomous/`.** It looks like dead swarm scaffolding. It is the
   live definition of that gateway *and* a running Valheim server. It was deleted and restored
   during the session; `docker ps` is what caught it.
3. **The P7 VM is still running and billing**, by Derek's decision. Not an accident.

## Open decisions — `fieldlab/DECISIONS-PENDING.md`

| | |
|---|---|
| **Re-provision the local gateway off the retired repo** | The top one. A rebuild plus a state-root move, with a live Valheim world at `state/server/data`. Not a bounce. |
| Dev-build split-brain | Uncut build: handshake fails open, ZDO admission 503s. Both sides are *deliberate* — one argues in a doc comment, the other asserts in a test. Three options and a recommendation are in the register. |
| The `clients` profile in the lab compose | Those clients can no longer self-drive; they're profile-gated and marked in-file. Retire or keep. |
| `WebRequest` → raw-socket fold | Low priority, from 2026-07-10. |

## Two ready-to-start paths

**A · Measure the AoI knee** — [`Lumberjacks/docs/network/aoi-knee-experiment-brief.md`](Lumberjacks/docs/network/aoi-knee-experiment-brief.md)
is self-contained; paste its path as the opening prompt. It has the question, the existing
instrumentation, four gotchas that already cost time, and a first sweep to run. Read
[`area-of-interest-findings.md`](Lumberjacks/docs/network/area-of-interest-findings.md) §0-§2
first — **there are two independent "what matters most" systems in this repo and conflating
them wastes hours.**

**B · Re-provision the local gateway** off `C:\work\comfy`, mirroring the P7 approach. Needs a
decision on the state root before any command runs.

## Design decisions made this session — read before touching AoI

- [ADR 0010](fieldlab/docs/adr/0010-consistency-is-predictability.md) — **consistency means
  predictable, not invariant.** Adaptive falloff is good; chatter at a threshold is not.
  Hysteresis is a fidelity requirement, not an optimisation. Tune to the floor that always
  holds. This design will lose throughput benchmarks *on purpose*.
- [ADR 0009](fieldlab/docs/adr/0009-verify-against-an-independent-source.md) — a check that
  reads its own output is not a check.
- [ADR 0008](fieldlab/docs/adr/0008-liveness-is-not-admission.md) — liveness is not admission.
- [landmark-reach-design.md](Lumberjacks/docs/network/landmark-reach-design.md) — long-range
  visibility as a scarce, earned, placeable property. Needs **one field** (reach); the tier
  model, the reliable lane and the manifest wire already exist.

## Do not re-execute these

`fieldlab/docs/config-surface-decisions.md` carries recommendations that were **withdrawn on
re-examination**. D2's three groups are all load-bearing — in particular
`LumberjacksProjectionRunner` renders local-only primitives with no ZDO ownership, which is the
far-field proxy prototype the landmark design needs. The revision banner at the top of that file
explains each. `L-2026-07-21-19`: a recommendation is a snapshot of what was known.

## Session record

[`fieldlab/retro/SESSION-RETRO-2026-07-21.md`](fieldlab/retro/SESSION-RETRO-2026-07-21.md) —
two retros, the second an addendum. Posters:
[the mess](fieldlab/docs/audit-2026-07-21-conditional-logic.svg) ·
[the sixteen twists](fieldlab/docs/audit-2026-07-21-the-twists.svg).
