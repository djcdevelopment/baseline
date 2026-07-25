# cre-e07-presentation-replay / chase-latest-vs-buffered-v1

- Run: `pure-20260725T040658Z-repeat`
- Driver: `pure`
- Seed: `416`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `replay_outputs_remain_finite` — evaluated=60 policy/profile/pattern combinations
- PASS `replay_consumes_final_sequence` — expected_final_sequence=40
- PASS `buffered_interpolation_does_not_extrapolate` — all interpolation factors stayed within the two bracketing source snapshots
- PASS `teleport_discontinuity_is_not_smoothed` — guarded_frames=0,4,3,3,0,1,3,3; maximum_steps=28.284,28.379,28.379,28.379,28.850,28.379,28.379,28.379

## Prediction observations

- `buffer_candidate_50ms`: lower_step_change=0/10; lower_timeline_error=10/10; burst_stalls_chase/buffered=17/342; mean_current_error_buffered=0.898m
- `buffer_candidate_100ms`: lower_step_change=5/10; lower_timeline_error=10/10; burst_stalls_chase/buffered=17/114; mean_current_error_buffered=1.207m
- `buffer_candidate_150ms`: lower_step_change=8/10; lower_timeline_error=10/10; burst_stalls_chase/buffered=17/44; mean_current_error_buffered=1.678m
- `buffer_candidate_200ms`: lower_step_change=10/10; lower_timeline_error=10/10; burst_stalls_chase/buffered=17/0; mean_current_error_buffered=2.134m
- `authority_limit`: the replay excludes native transform writes, Unity physics, binding cost, and human feel; it selects candidate equations only
