# Wedge fix receipt — rung 2 (r42 gateway), 2026-08-07

Companion to
[rung 1](../native-20260807-wedge1c-r41-omen/wedge-repro-receipt.md). Identical
drill, one variable changed: the gateway image.

## Setup

Identical to rung 1 (AM4 server 0.5.80 runtime-armed, OMEN client mod 0.5.80,
`zdoJournalApplyThrottleMs = 250`) except the gateway:
`lumberjacks-gateway:r42-wedge-20260807`, built this session from current `main`
(`docker build --target gateway`), manifest `sha256:64b35ce007a8…`, running as
`lumberjacks-local-gateway-1`. Gateway `docker restart` at
`2026-08-07T07:57:52Z` with 3,194,566 bytes of durable journal; the client held a
1,280-delivery snapshot backlog from its join 4 minutes earlier.

## Observed vs rung 1

| Observable | r41 (rung 1) | r42 (rung 2) |
|---|---|---|
| First `canonical_delivery_progress` after restart | 171 s | **1 s** |
| In-flight refill on re-attach | `inbound=224` (headroom flood) | **`inbound=61`** (64-frame cap) |
| Progress cadence | two silent windows (~171 s, ~60 s) | delivery + ack progress from second 1; periodic interest refresh rows throughout |
| Session recovery | reincarnated (client-side r42 half) | reincarnated (same) |
| `/live/valheim-cutover` | no mode/admission fields | `effective_mode`, `admission` verdict served (fix 5 live) |

The later `inbound=138` reading at +226 s is the client-local buffered queue
depth mid-flow across multiple refills, not the per-refill window; the
per-refill observable is the first row after re-attach (224 vs 61).

## Verdict

The candidate-8/11 redelivery wedge **reproduces on the r41 gateway and does not
reproduce on the r42 gateway** under identical fault injection. Together with the
rung-1 receipt this satisfies the DECISIONS-PENDING precondition for spending the
r42 cut ("the stall reproduces on demand *before* the fix and not *after*").

## Post-run state

- OMEN client stopped; at-rest config restored byte-exact by the harness.
- AM4 server disarmed (`worldZoneCutoverEnabled`, `zdoJournalCanonicalSessionEnabled`,
  `zdoJournalCutoverEnabled` → false; receipts `native-20260807-wedge-disarm-*`).
- Local gateway left on the r42 build (current-main dev image — the dev-lane
  default posture).
- Not yet run: the two-client variant (i5 needs Steam started in its interactive
  session) and rung 3 (credentialed enrollment lane — blocked on one human
  `/join` per lab Steam account; `POST /api/v0/enrollment/pack` can only rotate
  an existing enrollment, never mint one).
