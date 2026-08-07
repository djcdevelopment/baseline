# Wedge repro receipt — rung 1 (pre-fix gateway), 2026-08-07

The candidate-8/11 post-restart redelivery wedge reproduced on demand on the local
loop, satisfying the DECISIONS-PENDING precondition for spending the r42 cut
("the stall reproduces on demand *before* the fix").

## Setup

| Piece | Identity |
|---|---|
| Gateway | `lumberjacks-gateway:m7-c10a-20260802-r41`, image `sha256:8a6ba0e66286…` — the exact promoted r41 pair image, running as `lumberjacks-local-gateway-1` on OMEN |
| Server | AM4 `comfy-valheim-server-am4-valheim-server-1`, runtime mod 0.5.80 (current main), journal + canonical session + world-zone armed via runtime control (receipts under request ids `native-20260807-wedge1*`) |
| Client | OMEN, character tugcorp, mod 0.5.80 built from current main (sha `3455dcc5…`), **`zdoJournalApplyThrottleMs = 250`** (the r42 fault-injection knob) via the new harness param |
| Fault | Client apply/ACK paced to ~4/s; gateway `docker restart` at `2026-08-07T07:45:26Z` with 2,127,229 bytes of durable journal |

Note the deliberate asymmetry: the mod halves run current main (the throttle knob
only exists post-`b206c31`), the **gateway** is the frozen r41 image — the gateway
is the half whose pre-fix behavior is under test, and all three r42 gateway fixes
(64-frame cap, stall abort, zombie evict) are gateway-side.

## Observed (client `zdo-journal-cutover.jsonl` + `lumberjacks-game-session.jsonl`)

1. **Session loss + reincarnation**: three `connection_error` rows 07:45:24–26,
   then `session_started resumed=false reincarnated=true` at 07:45:28 — the r41
   gateway lost in-memory sessions; the client's (r42-half) `ResumeReattachPolicy`
   abandoned the dead token and reincarnated. A pre-r42 client mod would retry the
   refused resume forever — the resume-livelock half of the wedge.
2. **Full-backlog redelivery**: re-registered interest returned
   `snapshot_count=21 pending=1675`.
3. **The smoking gun**: `canonical_delivery_progress banked=2048 inbound=224` —
   the r41 gateway refilled the throttled client to the **224-frame** in-flight
   headroom. r42's fix 3 caps this exact value at 64.
4. **Burial**: ~171 s after restart with **zero** visible apply-progress rows,
   then sparse progress (`canonical_ack_progress queued=1024`,
   `snapshot_superseded_progress superseded=1024`), another ~60 s silent window —
   a throttled consumer digging out of a 1,675-delivery flood at 4/s (~7 min).
   The in-world client crawls; a cold-joining client in this state is the
   candidate-8 spawn livelock (`IsAreaReady` starvation).

## Verdict

Pre-fix behavior reproduced: uncapped 224-frame redelivery flood + multi-minute
starvation window after a gateway restart, driven entirely by the harness throttle
on the local loop. Rung 2 runs the identical drill against a gateway built from
current main (r42) and must show `inbound ≤ 64` and steady paced progress with no
multi-minute silent window.

## Run-log corrections worth keeping

- Run-id scope is one contract across server arming and client launch: a client
  joining under a new RunId while the server holds the old one gets
  `canonical_control_rejected … scope_mismatch` on interest seeding, and the
  symptom is a silent empty snapshot (`snapshot_count=0 pending=0`). Sync
  `nativeNetworkEvidenceRunId` BEFORE the client joins.
- The journal consumer binds its world epoch at join; arming
  `worldZoneCutoverEnabled` (descriptor publication) after a client is already
  in-world does not retrofit — bounce the client.
- The mod's character match is against the profile display name; the harness
  preflight's filename-derived list can disagree with what the mod sees when
  the wrong Steam account is active (the char-select screen "refreshing" is
  that signature).
