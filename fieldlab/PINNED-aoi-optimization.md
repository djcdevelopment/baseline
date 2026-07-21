# PINNED — AoI optimization work (hard hold)

**Status: HARD HOLD. Do not pick these up without Derek re-opening them.**
Pinned 2026-07-21.

## Why this exists

The 2026-07-21 session ran the **complete vertical seam** of the Valheim AoI
path — measurement → decision → plan → MVP → prod deploy → live validation →
permanent arming. That was the point. In Derek's words:

> "That prior session of work let us run the complete vertical seam and let me
> get a feel for where we're at. Trust my instincts — we'd be over-sharpening to
> optimize more here."

The MVP (near-full / mid-thin-to-5Hz / far-drop band-shaping) is **armed in
production on P7** (`zdoBandShapingEnabled = true`) and baked into normal play.
That's the deliverable. Everything below is *further optimization* of a seam
that already works end-to-end — which is exactly the over-sharpening we're
choosing not to do right now.

> "These are all pinned as we pivot to re-establishing the local docker
> dashboard for GCP telemetry."

## What is pinned (all previously "Open" in DECISIONS-PENDING.md)

1. **Far → approach re-sync validation** — confirm a dropped far ZDO reloads
   when a player returns to a distant build. First suspect *if* "distant builds
   don't reload" is ever reported; not a proactive task while pinned.
2. **Band-shaping under multi-player density** — single-observer was validated;
   two clients in one dense area is the real scaling test (ties into HANDOFF
   task 6, two-client isolation). Seat-required.
3. **AoI "v.5"** — hysteresis at the 30/64m band edges (old HANDOFF task 5),
   landmark punch-through, gateway landmark-announcement wiring (light up the
   dead-carried `ReachMeters`), and re-running the baseline grid with the real
   band shape in the path. This is plan `jolly-doodling-planet.md` increments
   3–5.

## Also parked (seat-required HANDOFF leftovers)

- **Task 6** — two-client isolation gate (needs 2 Steam clients + Derek driving).
- **Task 8** — reference production `.cfg` (needs the live VM cfg).

## Un-pinning

When Derek re-opens any of these, move the item back to the `## Open` section of
`DECISIONS-PENDING.md`. The approved plan for the v.5 items still lives at
`~/.claude/plans/jolly-doodling-planet.md`. Nothing here is lost — just held.
