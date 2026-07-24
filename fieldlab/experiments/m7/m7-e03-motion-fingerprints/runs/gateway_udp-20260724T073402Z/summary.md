# m7-e03-motion-fingerprints / motion-fingerprints-v1

- Run: `gateway_udp-20260724T073402Z`
- Driver: `gateway_udp`
- Seed: `413`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `gateway_udp_bound_relayed` — received_udp=121; relayed_udp=120; expected_motion=120
- PASS `gateway_udp_target_delivery` — captured_target_frames=120; token_matches=120
- PASS `gateway_udp_logical_order` — captured UDP frames have monotonic envelope sequence
- PASS `gateway_udp_motion_fingerprints` — straight_north=1,stutter_north=13,stop_start=2,turn_90=2.414,circle=9.204,teleport=56.286

## Prediction observations

- `gateway_udp_path`: source motion binds a UDP endpoint and reaches the distinct target through UdpTransport.TrySend
- `gateway_udp_vs_websocket`: the same synthetic correction fingerprints survive the bound UDP path; real client interpolation remains unproven
