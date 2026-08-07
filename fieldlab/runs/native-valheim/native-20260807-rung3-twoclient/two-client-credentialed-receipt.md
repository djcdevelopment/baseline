# Two-client credentialed-lane receipt — 2026-08-07

Both lab clients rode the enrollment-consumer lane simultaneously against the
r42 pair (`m7-c10b-20260807-r42` gateway + mod on server and both clients),
each with its own Steam-OpenID-minted credential.

## Setup

- Server: AM4, r42 mod, `lumberjacks-primary`, scoped redirect
  (`Player,Pickable_Mushroom,Mushroom`), window/manifest
  `am4-handshake-async-20260730`.
- OMEN: tugcorp, wary.fool enrollment `75e7d213…`, direct to the local gateway.
- i5: durracktu, enrollment `d1560dfc…`, gateway reached through the ssh
  reverse tunnel (`127.0.0.1:4400 → OMEN:4000`); r42 DLL hash-verified onto the
  i5 via the deploy lane; bounded 300 s smoke via the interactive scheduled task.
- Run id `native-20260807-rung3-twoclient` synced server-side before either join.

## Observed

- Final window counters after the bounded window:
  **receipts 3,103 / acknowledged 3,103 / pending 0 / applied 1,255 /
  superseded 613 / rejected 0 / `complete: true`** — a live two-player session's
  Player-prefab traffic fully drained through the credentialed lane.
- The i5 log shows its consumer independently applying deliveries
  (`Authoritative consumer processed … result=applied seq=3085`) until its hold
  expired — both machines' credentials authenticated and consumed.
- **Telemetry artifact worth a look, not an alarm:** `active_consumers` read `1`
  throughout despite two demonstrably live consumers — the consumer-heartbeat
  sample key (`window@consumerId`) appears to collapse both clients into one
  entry. Functional delivery was unaffected; the count is what candidate-12
  acceptance reads, so confirm the consumer_id each client reports before
  trusting `active_consumers >= 2` as a two-player criterion.
- The i5 leg closed itself on schedule (300 s hold) — the bounded-smoke
  contract, not a failure.

## Post-run state

Both clients stopped with byte-exact config restores; tunnel closed; AM4
restored to native at-rest from `.bak-20260807T083649Z` and restarted (r42 mod
DLL retained on the cold-start mount — it is the current candidate artifact;
r41 preserved beside it as `.bak-r41`).
