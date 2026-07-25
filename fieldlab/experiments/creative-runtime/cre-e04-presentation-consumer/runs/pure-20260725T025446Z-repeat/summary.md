# cre-e04-presentation-consumer / transient-consumer-bursts-v1

- Run: `pure-20260725T025446Z-repeat`
- Driver: `pure`
- Seed: `413`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `consumer_count_shape_matches_prediction` — direct=applied:19,coalesced:0,expired:0,stale:1; latest_wins=applied:14,coalesced:5,expired:0,stale:1; latest_wins_expiry=applied:12,coalesced:5,expired:2,stale:1
- PASS `final_fresh_state_preserved` — direct=source_a:13,source_b:9; latest_wins=source_a:13,source_b:9; latest_wins_expiry=source_a:13,source_b:9
- PASS `expiry_prevents_old_apply` — expiry_ms=120; max_applied_age_ms=75; expired=2
- PASS `apply_work_reduces_monotonically` — applied=19,14,12; projected_deliveries=57,42,36
- PASS `fresh_recovery_survives_expiry` — delayed sequences expired, then the next fresh sample for each source applied

## Prediction observations

- `bounded_apply_work`: direct/latest/expiry applied 19/14/12 samples and projected 57/42/36 recipient deliveries
- `fidelity_boundary`: latest-wins preserved the final fresh sequence while intentionally coalescing five intermediate burst samples; visual smoothness remains untested
