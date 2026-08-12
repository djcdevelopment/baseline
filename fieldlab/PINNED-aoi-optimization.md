# PINNED — AoI optimization work (hard hold)

> **HISTORICAL:** This pin describes the former monorepo lane. It is not a current
> work queue; use [`REPO-MAP.md`](../REPO-MAP.md) to find the owning repository.

**Status: HARD HOLD. Do not pick these up without Derek re-opening them.**
Pinned 2026-07-21.

> **Update 2026-07-21 (night):** the first live 2-human authoritative test **reproduced item 2**
> physically — co-located players cannot share an area because ZDO delivery is single-recipient.
> Full write-up + the architecture question it raises: [`FINDINGS-multiplayer-copresence-2026-07-21.md`](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/FINDINGS-multiplayer-copresence-2026-07-21.md).
> Items 1 and 2 below are no longer hypothetical; they are the confirmed next architecture work.

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
   task 6, two-client isolation). Seat-required. **REPRODUCED 2026-07-21 night →
   now an active architecture track, no longer a hold:** the single-recipient
   queue and per-observer AoI collide — the same area ZDO can only be delivered to
   one player's partition, so co-located players can't share buildings/portals. The
   keystone fix is an **ownership-vs-visibility split** (single writer, N readers /
   AoI-aware fan-out), now specified in **[ADR 0013](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/adr/0013-ownership-visibility-split.md)**
   with an evolutionary Phase 0–5 roadmap. See the findings doc for the live data.
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
`DECISIONS-PENDING.md`. The v.5 increment breakdown (hysteresis / landmark punch-through /
re-baseline) is captured in item 3 above and in the band-shaping ADR
(`fieldlab/docs/adr/0011-aoi-lives-on-the-producer.md`); the original scratch plan at
`~/.claude/plans/jolly-doodling-planet.md` has since been overwritten by the community-telemetry
plan, so treat this doc as the surviving record. Nothing here is lost — just held.
