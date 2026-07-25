# cre-e03-transport-faults / motion-sequence-faults-v1

- Run: `gateway_udp-20260724T142029Z`
- Driver: `gateway_udp`
- Seed: `412`
- Classification: `refuted`
- Stop: `completed`

## Invariants

- PASS `duplicate_and_reorder_rejected` — dropped_stale=3; expected=3
- PASS `transient_gap_does_not_block_fresh_motion` — sequence 104 relayed even though sequence 103 was intentionally absent
- PASS `ushort_sequence_wrap_preserved` — 65534,65535,0,1 relayed; an old 65535 after wrap was rejected
- PASS `authenticated_session_reconnect_resets_motion_sequence` — resumed session accepted sequence 1 and detached UDP token produced no motion relay
- FAIL `fault_fixture_delivery_accounted` — received=11; relayed=18; expected=10

## Prediction observations

- `sequence_guard_behavior`: duplicate and old motion is dropped per session; gaps and ushort wrap preserve fresh motion
- `reconnect_behavior`: new authenticated session state accepts a fresh sequence and the detached UDP token no longer maps to a session
