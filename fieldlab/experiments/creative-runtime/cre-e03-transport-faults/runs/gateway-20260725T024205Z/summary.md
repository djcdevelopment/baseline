# cre-e03-transport-faults / motion-sequence-faults-v1

- Run: `gateway-20260725T024205Z`
- Driver: `gateway`
- Seed: `412`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `duplicate_and_reorder_rejected` — dropped_stale=3; expected=3
- PASS `transient_gap_does_not_block_fresh_motion` — sequence 104 relayed even though sequence 103 was intentionally absent
- PASS `ushort_sequence_wrap_preserved` — 65534,65535,0,1 relayed; an old 65535 after wrap was rejected
- PASS `authenticated_session_reconnect_resets_motion_sequence` — resumed session accepted sequence 1 on the authenticated WebSocket seam
- PASS `accepted_source_frames_accounted` — accepted_source_frames=10; expected=10; setup traffic excluded
- PASS `primary_target_delivery_accounted` — primary_target_deliveries=10; expected=10
- PASS `regional_fanout_accounted` — aggregate_relay_deliveries=18; expected=18; topology=4x1+4x2+1x3+1x3

## Prediction observations

- `sequence_guard_behavior`: duplicate and old motion is dropped per session; gaps and ushort wrap preserve fresh motion
- `reconnect_behavior`: new authenticated session state accepts a fresh sequence after resume
- `fanout_cost_behavior`: 10 accepted source frames produced 10 deliveries to the primary target and 18 aggregate deliveries across the changing region topology
