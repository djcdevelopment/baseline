# cre-e01-runtime-envelope / combat-budget-bands-v1

- Run: `pure-20260724T133947Z`
- Driver: `pure`
- Seed: `410`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `critical_work_preserved` — player_death and projectile_hit remained full on binary WebSocket in every pressure band
- PASS `budget_never_negative` — minimum_remaining=1
- PASS `transport_follows_semantics` — critical mutations used binary WebSocket; emitted presentation used session UDP with binary WebSocket fallback
- PASS `all_degradation_modes_observed` — modes=deferred,dropped,full,reduced
- PASS `degradation_tracks_pressure` — presentation_full=4,3,0; degraded=0,7,18
- PASS `deferred_queue_bounded` — capacity=4; observed_max=4

## Prediction observations

- `selective_degradation`: green/amber/red presentation full counts were 4/3/0; protected mutations stayed full
- `explainable_transport`: every decision records requested mode, selected mode, reason, cost, route, fallback, and remaining budget
