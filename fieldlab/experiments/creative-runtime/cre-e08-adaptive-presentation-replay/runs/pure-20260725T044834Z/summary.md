# cre-e08-adaptive-presentation-replay / relative-transit-fast-rise-slow-decay-v1

- Run: `pure-20260725T044834Z`
- Driver: `pure`
- Seed: `417`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `adaptive_replay_outputs_remain_finite` — evaluated=180 policy/profile/pattern combinations
- PASS `adaptive_replay_consumes_final_sequence` — expected_final_sequence=40; loss profile always delivers the final sample
- PASS `adaptive_and_fixed_interpolation_do_not_extrapolate` — all interpolation factors stayed within delivered source brackets
- PASS `adaptive_delay_stays_inside_declared_bounds` — declared_bounds_ms=50..200
- PASS `adaptive_replay_does_not_smooth_teleports` — guarded_frames=0,4,3,3,0,0,1,3,3,3,0,4,3,3,0,0,3,3,3,2,0,4,3,3,3; maximum_steps=28.284,28.379,28.379,28.379,28.284,28.850,28.379,28.379,28.379,28.298,28.284,28.379,28.379,28.379,28.284,28.284,28.284,28.379,28.379,28.289,28.284,28.379,28.379,28.379,28.334

## Prediction observations

- `adaptive_profile_stable`: stalls_chase/adaptive/fixed200=17/296/0; large_steps_chase/adaptive/fixed200=0/109/0; mean_delay_adaptive=50.0ms; mean_current_error_adaptive=0.796m
- `adaptive_profile_three_sample_burst`: stalls_chase/adaptive/fixed200=17/51/0; large_steps_chase/adaptive/fixed200=11/6/0; mean_delay_adaptive=180.6ms; mean_current_error_adaptive=2.082m
- `adaptive_profile_isolated_burst`: stalls_chase/adaptive/fixed200=17/125/0; large_steps_chase/adaptive/fixed200=2/35/0; mean_delay_adaptive=139.6ms; mean_current_error_adaptive=1.704m
- `adaptive_profile_deterministic_jitter`: stalls_chase/adaptive/fixed200=23/12/0; large_steps_chase/adaptive/fixed200=0/0/0; mean_delay_adaptive=131.5ms; mean_current_error_adaptive=1.564m
- `adaptive_profile_periodic_loss`: stalls_chase/adaptive/fixed200=17/47/0; large_steps_chase/adaptive/fixed200=0/8/0; mean_delay_adaptive=134.5ms; mean_current_error_adaptive=1.628m
- `adaptive_candidate_gate`: verdict=reject_or_revise; lower_stalls_vs_chase=False; lower_delay_vs_fixed200=True; lower_current_error_vs_fixed200=True; large_steps_not_above_chase=False
- `adaptive_clock_contract`: candidate inputs are relative arrival-minus-send deltas and sequence gaps; synchronized client clocks are not required
- `authority_limit`: the replay excludes native transform writes, Unity physics, binding cost, and human feel; passing only permits a reversible live A/B candidate
