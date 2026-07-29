# cre-e08-adaptive-presentation-replay / relative-transit-bracket-floor-v2

- Run: `pure-20260725T045003Z-repeat`
- Driver: `pure`
- Seed: `417`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `adaptive_replay_outputs_remain_finite` — evaluated=180 policy/profile/pattern combinations
- PASS `adaptive_replay_consumes_final_sequence` — expected_final_sequence=40; loss profile always delivers the final sample
- PASS `adaptive_and_fixed_interpolation_do_not_extrapolate` — all interpolation factors stayed within delivered source brackets
- PASS `adaptive_delay_stays_inside_declared_bounds` — declared_bounds_ms=100..200
- PASS `adaptive_replay_does_not_smooth_teleports` — guarded_frames=0,4,3,3,4,0,1,3,3,3,0,4,3,3,4,0,3,3,3,3,0,4,3,3,4; maximum_steps=28.284,28.379,28.379,28.379,28.379,28.850,28.379,28.379,28.379,28.298,28.284,28.379,28.379,28.379,28.379,28.284,28.284,28.379,28.379,28.296,28.284,28.379,28.379,28.379,28.381

## Prediction observations

- `adaptive_profile_stable`: stalls_chase/adaptive/fixed200=17/0/0; large_steps_chase/adaptive/fixed200=0/0/0; mean_delay_adaptive=100.0ms; mean_current_error_adaptive=1.185m
- `adaptive_profile_three_sample_burst`: stalls_chase/adaptive/fixed200=17/21/0; large_steps_chase/adaptive/fixed200=11/0/0; mean_delay_adaptive=186.0ms; mean_current_error_adaptive=2.103m
- `adaptive_profile_isolated_burst`: stalls_chase/adaptive/fixed200=17/21/0; large_steps_chase/adaptive/fixed200=2/0/0; mean_delay_adaptive=155.5ms; mean_current_error_adaptive=1.825m
- `adaptive_profile_deterministic_jitter`: stalls_chase/adaptive/fixed200=23/0/0; large_steps_chase/adaptive/fixed200=0/0/0; mean_delay_adaptive=181.5ms; mean_current_error_adaptive=2.117m
- `adaptive_profile_periodic_loss`: stalls_chase/adaptive/fixed200=17/9/0; large_steps_chase/adaptive/fixed200=0/2/0; mean_delay_adaptive=184.5ms; mean_current_error_adaptive=2.166m
- `adaptive_candidate_gate`: verdict=earns_reversible_live_ab; lower_stalls_vs_chase=True; lower_delay_vs_fixed200=True; lower_current_error_vs_fixed200=True; large_steps_not_above_chase=True
- `adaptive_clock_contract`: candidate inputs are relative arrival-minus-send deltas and sequence gaps; synchronized client clocks are not required
- `authority_limit`: the replay excludes native transform writes, Unity physics, binding cost, and human feel; passing only permits a reversible live A/B candidate
