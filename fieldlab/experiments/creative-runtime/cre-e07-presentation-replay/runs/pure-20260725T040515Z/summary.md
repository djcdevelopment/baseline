# cre-e07-presentation-replay / chase-latest-vs-buffered-v1

- Run: `pure-20260725T040515Z`
- Driver: `pure`
- Seed: `416`
- Classification: `refuted`
- Stop: `completed`

## Invariants

- PASS `replay_outputs_remain_finite` — evaluated=48 policy/profile/pattern combinations
- PASS `replay_consumes_final_sequence` — expected_final_sequence=40
- PASS `buffered_interpolation_does_not_extrapolate` — all interpolation factors stayed within the two bracketing source snapshots
- FAIL `teleport_discontinuity_is_guarded` — guarded_frames=0,4,3,0,1,3

## Prediction observations

- `buffer_candidate_50ms`: lower_step_change=0/10; lower_timeline_error=10/10; burst_stalls_chase/buffered=17/342; mean_current_error_buffered=0.898m
- `buffer_candidate_100ms`: lower_step_change=5/10; lower_timeline_error=10/10; burst_stalls_chase/buffered=17/114; mean_current_error_buffered=1.207m
- `buffer_candidate_150ms`: lower_step_change=8/10; lower_timeline_error=10/10; burst_stalls_chase/buffered=17/44; mean_current_error_buffered=1.678m
- `authority_limit`: the replay excludes native transform writes, Unity physics, binding cost, and human feel; it selects candidate equations only
