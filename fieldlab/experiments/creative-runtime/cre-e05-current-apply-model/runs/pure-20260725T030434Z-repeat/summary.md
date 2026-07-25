# cre-e05-current-apply-model / late-update-amplification-v1

- Run: `pure-20260725T030434Z-repeat`
- Driver: `pure`
- Seed: `414`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `current_apply_rate_is_frame_bound` — inbound=snapshot_hz*entities; render_apply=fps*entities; ratio=fps/snapshot_hz
- PASS `remote_entity_cost_scales_linearly` — modeled entity counts 1,10,100 preserve exact per-frame multiplication
- PASS `send_interval_convergence_is_frame_rate_stable` — min=0.593430340; max=0.593430340; rate=18
- PASS `stale_tail_upper_bound_matches_source_defaults` — one entity at 20/40/60/120 FPS reuses the last snapshot at most 11/21/31/61 times across 500 ms

## Prediction observations

- `frame_amplification`: one_entity_apply_per_second=20,40,60,120; apply_per_snapshot=1,2,3,6
- `entity_amplification`: hundred_entity_apply_per_second=2000,4000,6000,12000
- `source_boundary`: the checked-in runner already coalesces receive bursts per ZDO, then performs lookup and exponential convergence every LateUpdate without velocity extrapolation
