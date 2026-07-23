# M3-4 — Runnable Proofs (docs that can't rot)

## Objective
Establish the convention that every workbook/doc chapter ends in something
executable that proves the chapter is still true — a script, a test, a compose
health check — so drift becomes a red test instead of a silent lie.

## Context
The legacy goal: the next human, agent, community, or future-Derek must be able
to trust the docs. Existing test surfaces: `tests/`, `ComfyNetworkSense.Tests`,
`network/mcp/tests`, fieldlab scenarios. The replay notebook (M3-1) reproduction
check is the archetype of a proof.

## Steps
1. Write `docs/runnable-proofs.md`: the convention — each proof is a single
   command, exits 0/1, prints what it verified; proofs live next to the doc
   they guard or in `tests/proofs/`; each doc lists its proofs in a final
   `## Proofs` section.
2. Build the runner: `tools/run-proofs.ps1` (and a bash twin if trivial) that
   discovers and runs everything under `tests/proofs/` and summarizes
   pass/fail per doc.
3. Seed three real proofs to prove the convention:
   - data-trust note (M1-1): script greps capture code and diffs the field
     list against the note's field list;
   - tradeoff cards (M3-2): script verifies every `current_value` against
     config;
   - replay (M3-1): headless run of the reproduction check on the demo
     session.
   Adjust targets to whichever of those milestones have landed; substitute
   equivalent proofs for existing docs if needed.
4. Wire into whatever CI/check ritual exists (check `tests/` and repo scripts
   for the current entrypoint); otherwise document manual cadence: run before
   each release/changelog post.

## Acceptance
- Runner works from fresh checkout; the three seed proofs pass.
- Convention doc is short enough that adding a proof is obviously cheap.

## Out of scope
Retrofitting proofs onto every existing doc (incremental, per-touch).
