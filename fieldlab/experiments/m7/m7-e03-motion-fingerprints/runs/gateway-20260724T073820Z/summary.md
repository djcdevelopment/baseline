# m7-e03-motion-fingerprints / motion-fingerprints-v1

- Run: `gateway-20260724T073820Z`
- Driver: `gateway`
- Seed: `413`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `gateway_motion_relayed` — received_websocket=120; relayed_websocket=120; expected=120
- PASS `gateway_websocket_fallback` — captured_target_frames=120
- PASS `gateway_logical_order` — captured fallback frames have monotonic envelope sequence
- PASS `gateway_motion_fingerprints` — straight_north=1,stutter_north=13,stop_start=2,turn_90=2.414,circle=9.204,teleport=56.286

## Prediction observations

- `gateway_transport_path`: all frames used the real UdpTransport WebSocket fallback seam because no UDP endpoint was bound
- `gateway_cadence_vs_interpolation`: the same synthetic correction fingerprints survive Gateway relay; live interpolation remains unproven
