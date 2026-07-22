# Findings — multi-player area co-presence (live 2-human test, 2026-07-21)

> Written to seed architecture research + planning. Captured at the end of the first real
> two-human authoritative-cutover test. **Headline: multi-tenant queue delivery works; area
> co-presence does not — because ZDO delivery is single-recipient and AoI needs multicast.**

## One-line
Two players on `lumberjacks-primary` isolate into their own recipient partitions cleanly (queue is
healthy, zero errors), but they **cannot share an area** — a building's ZDO can live in only one
player's partition at a time, so whoever the redirect last stamped it for sees it and the other
does not. This is the core of the pinned **multi-player density** work, now with a physical repro.

## What we PROVED works tonight (live, 2 Steam clients: Durracktu + Prototyper)
- **Recipient-partitioned queue at 2 consumers.** `active_consumers=2`, `receipts=51940`,
  `acknowledged=51940`, `applied=37143`, **`rejected=0`, `duplicates=0`, `pending` drained to 0**.
  Each player drained their own `(window, recipient)` partition; no cross-consumption.
- **The single-consumer health-gate lift.** Changing `IsAuthoritativeComplete` from
  `ActiveConsumers == 1` to `>= 1` (commit `a66a7d6`) kept the dashboard **healthy at 2 consumers**
  — not stale, not rejecting the primary heartbeat. This is the direct fix for the earlier incident
  where the 2nd consumer crashed the dashboard. Confirmed: `stale=false` throughout the 2-consumer
  window.
- **The "server full" was our own seat cap, not Valheim.** The handshake gate rejected the 2nd
  player with `code=9 check=capacity_reserved` (mod log). That is the M1 "admit one" seat gate
  (`ValheimHandshakeService.SeatCapacity`, default 1). Disabling it at runtime
  (`POST /valheim/handshake/config {seat_capacity:0}`) let Prototyper's handshake ACCEPT immediately.
  `max_players` (Valheim's native 10) was never the limit.

## The BLOCKING architecture problem (what broke in-game)
**Observed (Derek's words):** he could see Prototyper as a *player*, but **none of their buildings**;
the moment Prototyper **left the area, all the buildings reappeared** for Derek.

**Mechanism:**
1. The producer stamps each redirected ZDO for **exactly one** recipient — the peer ownership is
   handed to (`ZdoRedirectRunner.RecipientFor(peer)` → that peer's SteamID).
2. Under `lumberjacks-primary`, **native ZDO sync is suppressed** for covered ZDOs
   (coverage was 100% / `native_only=0`), so a player has **no vanilla fallback** for anything the
   authoritative queue doesn't hand them.
3. A shared-area object (a building) is a single ZDO. When Prototyper entered the area, the redirect
   re-stamped those ZDOs to **their** partition → they left Derek's partition → **Derek's buildings
   vanished** (nothing to fall back to). Prototyper couldn't render them either (their partition was
   never seeded with the connection/placement state). Ownership reverted when they left → buildings
   returned.

**Signature:** single-owner-per-ZDO **ownership handoff**. Only one player can "hold" an area at a
time; the area flickers to whoever the redirect last stamped.

**Portals were the same failure** (`Portal connection cache ... connected=0`): portal link/target
ZDOs sat in one partition; the other player's portals had nothing to connect to.

## The design tension to resolve (the actual research question)
Two subsystems currently disagree:
- **AoI** decides *what* each observer should see (relevance / band-shaping: near-full, mid-thin,
  far-drop). It is inherently **per-observer**.
- **The recipient queue** delivers *to whom* — **one recipient per envelope** (built for ownership
  isolation and per-player durable delivery).

Co-presence needs the **same** area ZDO delivered to **every in-range observer's** partition (read
copies for all), while **ownership stays single** (one writer). The current model conflates
"who owns it" with "who receives it." Splitting those is the crux.

### Open architecture questions (for the research/planning session)
1. **Fan-out vs shared partition.** Multicast each AoI-relevant ZDO into every in-range observer's
   partition, or introduce a shared **area/region** partition that co-located players both consume?
   (Region-scoped partitions may compose better with AoI regions than per-pair fan-out.)
2. **Ownership ≠ visibility.** Separate the single-writer ownership token from N-reader delivery.
   What carries the write authority, and how do non-owners get read copies without racing on ack?
3. **far→approach re-sync (the seed half).** A joining/approaching player still needs the area's
   **existing** relevant ZDOs seeded into their partition, not just go-forward deltas. Subsumed by
   fan-out but must handle the *initial* population, not only changes.
4. **Cost / partition math.** Delivery cost becomes `observers × changed-area-ZDOs`. Dedup, WAL
   growth, and ack semantics when N partitions hold copies of one logical ZDO. (This is why the AoI
   pin says multi-player density is the real scaling test — cost is `observers × entities`.)
5. **Handoff without flicker.** Ownership moving between co-located players must not blink the area
   out for anyone. Hysteresis / read-copy-before-ownership-move.
6. **AoI band interaction.** Fan-out is per-observer per-band — a far observer gets thinned copies,
   a near observer full. The multicast layer has to respect each observer's band.

## Operational state — how to resume (nothing here is lost, but note the ephemeral bits)
- **Gateway:** `lumberjacks-gateway:inc5-multiuser-20260721-r1` deployed on P7 (built locally,
  shipped via `docker save`/`load`, re-pinned — the VM source roots are stale, do NOT build on the
  VM). Rollback images `inc4-quest-…` and `inc1-…r3` are still loaded on the VM.
- **Resolved after this finding:** the alpha seat override is now durable through
  `VALHEIM_HANDSHAKE_SEAT_CAPACITY=0`, which Gateway applies at startup to `p7-primary-v1`.
  Runtime `/valheim/handshake/config` still works as an emergency override, but is no longer the
  normal way to resume two-player testing after a Gateway restart. A bare `>1` remains refused by
  design at `ValheimHandshakeService.cs` until per-holder liveness exists.
- **Recipients flag:** `VALHEIM_QUEUE_PRODUCER_EMITS_RECIPIENTS=true` is set in
  `/etc/comfy-p7/environment` (survives restarts). Confirmed live.
- **5 unpushed commits on `main`** (local only): `a66a7d6` multi-user gate lift · `32b8cb9`/`1f06972`/
  `719c029` quest evaluator 4c/4b/4a · `665d8c0` gameplay log-trim. Nothing pushed to origin yet.
- **Prototyper** is enrolled (`e317ac3d…`, Steam `76561198969416510`) and their enrollment is now
  used. Their `[Lumberjacks]` block was issued tonight.
- Untracked: `ENDtoEND.txt` (a conversation `/export`, not a repo artifact).

## Existing plans this supersedes / sharpens
- `~/.claude/plans/multi-player-queue-plan.md` — its Increment 1 (gate lift) **shipped tonight**. But
  the plan framed multi-player as "finish the health/lease/proof layer." **That was incomplete:** the
  gate lift makes the *queue* multi-tenant, but **area co-presence is a separate, larger problem**
  (this doc). Revise the plan: the real work is AoI-aware **multicast delivery**, not just leases.
- `fieldlab/PINNED-aoi-optimization.md` — this is the concrete repro of the pinned **"multi-player
  density"** item. AoI band-shaping and the queue's single-recipient model **collide** here.
- The incident plan (`~/.claude/plans/incident-prototyper-cutover-crash-plan.md`) — root cause is now
  understood: the earlier dashboard crash was the `active_consumers==1` gate (fixed `a66a7d6`); the
  earlier client crash was likely the same ownership-thrash under the shared-area contention seen
  tonight. Close it out against this doc.

## Bottom line for planning
Ship order is now clear: **(queue multi-tenancy ✓ done) → AoI-aware multicast delivery (ownership vs
visibility split) → far→approach re-sync → durable N-seat leases → cost/scale validation.** The
multicast/visibility split is the keystone; everything else composes around it.
