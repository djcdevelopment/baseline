# cre-e07-presentation-replay / chase-latest-vs-buffered-v1

- Run: `pure-20260725T040311Z-repeat`
- Driver: `pure`
- Seed: `416`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `replay_outputs_remain_finite` — evaluated=24 policy/profile/pattern combinations
- PASS `replay_consumes_final_sequence` — expected_final_sequence=40
- PASS `buffered_interpolation_does_not_extrapolate` — all interpolation factors stayed within the two bracketing source snapshots
- PASS `teleport_discontinuity_is_guarded` — guarded_frames=4,1

## Prediction observations

- `presentation_smoothness_candidate`: buffered interpolation reduced mean step-change in 5/10 non-teleport pattern/profile pairs
- `timeline_fidelity_candidate`: buffered interpolation reduced error against its declared delayed timeline in 10/10 non-teleport pairs
- `burst_tradeoff`: burst pairs=5; buffered delay=100ms; stalls chase/buffered=17/114
- `authority_limit`: the replay excludes native transform writes, Unity physics, binding cost, and human feel; it selects candidate equations only
