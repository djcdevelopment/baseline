# AoI band-shaping — P7 production baseline, 2026-07-21

**This is the reference for "band-shaping on in normal play."** Per Derek, distance-band AoI stays
**armed permanently** on P7 as the standing behaviour; this snapshot is what future changes (v.5
landmark reach + hysteresis, multi-player, any redirect/consumer work) get diffed against. Captured
live from production while a single player sat in the world's densest build — "about as heavy a load
as one player is going to get in one area" (Derek).

## Config (P7, window `p7-primary-v1`)

- `zdoBandShapingEnabled = true`, `zdoInnerRadiusMeters = 30`, `zdoOuterRadiusMeters = 64`,
  `zdoThinHz = 5` — near (0–30m) full rate, mid (30–64m) thinned to 5 Hz, far (>64m) dropped.
- `lumberjacksCutoverMode = lumberjacks-primary`, `zdoRedirectPrefabs = *`,
  `zdoRedirectMaxPriorityRank = 6`. Primary mode ⇒ the drop is **real delivery behaviour**, not
  telemetry: dropped far objects genuinely don't reach the client until proximity re-includes them.
- Mod commit `409a397` (band-shaping MVP `ecb2116` + auto-port harness).

## Measured (single player @ densest build)

Band-decision mix over the recent ~20k-row window (from `redirect-send.jsonl`):

| band | count | share | meaning |
|---|---|---|---|
| `Drop` | 5370 | **84.7%** | far >64m — suppressed from native, not emitted |
| `EmitThinned` | 808 | 12.7% | mid 30–64m — emitted at 5 Hz |
| `EmitFull` | 164 | 2.6% | near <30m — emitted every pass |

Gateway (`GET /valheim/zdo-redirect/status/p7-primary-v1`, emitted subset only — drops never arrive):

- `distinct_seq = 41802`, `receipts = 41802`, `acknowledged = 41802`
- `pending = 0`, `missing_seq = 0`, `duplicates = 0`
- top prefab `194227816 = 5592` (the build) + a long tail — thousands of pieces, all delivered clean

**Headline: ~85% of would-be redirect volume shed at worst-case single-player density, losslessly,
with the consumer fully caught up and zero duplicate storm.** The measured shape working in the real
Valheim path.

## What this baseline does NOT yet cover (watch items)

- **Far → approach re-sync.** A dropped far object is *acked* to Valheim (mandatory — skipping the ack
  is the duplicate-storm), which tells native the peer already has it. For a **static** far object a
  player walked away from and returns to, native may not re-offer it (thinks the peer has it) and the
  mod isn't emitting it — zone-entry force-send *probably* re-triggers it, but this was not exercised
  (the validation teleported INTO density, never far→back). If "distant builds don't reload on return"
  is ever reported, this is the first suspect.
- **Multi-player.** Cost is observers × changed-entities; two players in one dense area is untested.
  This baseline is single-observer.

## Re-capture (to diff a future change)

Tunnel to P7's gateway (`infra/gcp/p7/scripts/gateway-tunnel.ps1 -Action start` → `localhost:14000`), then:

```
Invoke-RestMethod http://127.0.0.1:14000/valheim/zdo-redirect/status/p7-primary-v1   # distinct_seq/pending/missing/dup
ssh comfy-p7 "F=$(sudo find /mnt/comfy-p7 -name redirect-send.jsonl|head -1); sudo tail -n 20000 $F | grep -oE '\"band\"[^,}]*' | sort | uniq -c"
```

Healthy = the same band spread (heavy Drop, some Thinned/Full), `missing_seq=0`, `duplicates=0`,
`pending` drains to 0. A change that raises `missing_seq`/`duplicates`, stalls `pending`, or collapses
the Drop share is a regression.

*(The `stdin ReadFile failed` traceback ssh prints on teardown is benign IAP-tunnel noise — see the
iap-ssh-teardown-noise note.)*
