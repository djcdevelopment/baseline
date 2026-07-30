# SUPERSEDED — Networking / ComfyNetworkSense hard hold

**Status: SUPERSEDED 2026-07-30.** Derek reopened the native-network replacement
lane after the unattended OMEN+i5 harness removed the KVM dependency. The canonical
execution sequence is now
[`plan-native-network-final-cutover.md`](plan-native-network-final-cutover.md).
This file remains only as the historical record of why the lane was paused on
2026-07-28; its task list and resume command are not current instructions.

## Why this exists

Every remaining next step on this lane needs Derek as a **human KVM** — manually driving two
Steam game clients, watching two screens, being unavailable for anything else. That is the most
draining work the program has, and the least legible to the community. The machine side is
**green**: `plans/full-roadmap-working-strategy.md` ("Current status addendum — 2026-07-24")
records `ready_for_derek_two_client_join` with *"Only human observation still required for
Wave 0."* Pausing here loses nothing — it parks a lane at a proven, documented, resumable
boundary while effort moves to work the community can see, run, and take over
(adoption track **A7 — Community Workbench**).

## What is true right now (2026-07-28)

- P7 runs admitted release `m30-rolecontrol-20260723-r1`; the public client-pull pointer is
  `m31-motionphase-20260724-r1` (motion-phase telemetry only — same admitted mod identity).
- Distance-band AoI shaping is armed in normal play (ADR 0011); native Valheim still owns
  simulation, ownership, non-ZDO RPCs, relevance, and presentation unless a tester explicitly
  enables local motion apply.
- CRE-E07 **rejected** fixed interpolation delay; CRE-E08 derived a bounded 100–200 ms
  relative-transit adaptive candidate that passed its repeatable synthetic A/B gate —
  **no DLL was built or promoted** (`76fee93`).
- The Harmony patch-load A/B instrumentation is **built, never run** (`9570b28`): default-off
  `[Perf] perfPatchLoadRollupEnabled`, runbook staged, no evidence folder exists.
- The ADR 0013 co-presence fan-out is built, flag-gated off, tests green — awaiting its live
  two-human test.
- The working tree is clean except `docs/audit/` (two review memos deliberately held for
  Derek's decision).

## What is pinned

1. **Wave 0 two-client join + observation gates H0-1…H0-4** —
   [`plans/remaining-human-tests.md`](../plans/remaining-human-tests.md) (join OMEN + i5 to P7
   with the two owned accounts; watch bounded APPLY/OBSERVE movement both directions; classify
   feel; seal or reject the visual evidence).
2. **ADR 0013 co-presence fan-out live test** —
   [`docs/runbook-copresence-fanout-live-test.md`](docs/runbook-copresence-fanout-live-test.md)
   (two humans standing in one base), including the 2026-07-22 "re-confirm it reproduces
   before arming" precondition from `DECISIONS-PENDING.md`.
3. **Patch-load A/B benchmark run** —
   [`docs/runbook-patchload-ab-benchmark.md`](docs/runbook-patchload-ab-benchmark.md) +
   [`experiments/patchload-ab/`](experiments/patchload-ab/). Blocked on item 5.
4. **CRE-E08 adaptive candidate → client DLL** — building/promoting the adaptive
   interpolation policy into the mod stays held; the candidate lives in
   [`experiments/creative-runtime/cre-e08-adaptive-presentation-replay/`](experiments/creative-runtime/cre-e08-adaptive-presentation-replay/experiment.md).
5. **client01/client02 one-time Steam seeding** —
   [`docs/runbook-headless-valheim-lab.md`](docs/runbook-headless-valheim-lab.md): the lab
   clients are **not seeded** as of 2026-07-24; that single manual Steam login is the human
   step gating 3 (and native-probe capture).

## What is explicitly NOT scheduled

**No human Steam-client test is scheduled by this pause. Avoiding them is the point.**
Do not propose one as a "quick check," do not prep one "so it's ready," do not put one on a
calendar. When Derek chooses to resume, the resume path below regenerates everything.

## Resume in one command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\wave0\Test-Wave0Prelive.ps1 -OutputDirectory captures\wave0-prelive-current
```

Then read `captures\wave0-prelive-current\return-packet\packet.md` and
`expected-result-grid.md`. The packet is **regenerated at resume time** — never trust a stale
copy as the starting point. The wider strategy context is
`plans/full-roadmap-working-strategy.md`; the session narrative up to the pause is
[`retro/SESSION-RETRO-2026-07-28.md`](retro/SESSION-RETRO-2026-07-28.md).

## What moved instead

Effort went to the **Community Workbench** (adoption milestone **A7**): a public catalog at
`/workbench` of the tools a volunteer can run today — quest picker + absorption engine,
ComfyStewardView, the live analytics pages, the Steam self-service join — each with an honest
status, a cold-start package, one Discord thread, and a named first task. Data file:
`Lumberjacks/docs/workbench/workbench.json`.

## Historical un-pinning rule

The hold was lifted by Derek's 2026-07-30 direction to plan and drive the native
network cutover to final completion. Current work is classified and sequenced in the
new plan rather than restated in the decision queue.
