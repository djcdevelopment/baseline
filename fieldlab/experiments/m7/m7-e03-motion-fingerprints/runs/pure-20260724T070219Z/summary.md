# m7-e03-motion-fingerprints / motion-fingerprints-v1

- Run: `pure-20260724T070219Z`
- Driver: `pure`
- Seed: `413`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `motion_patterns_present` — patterns=straight_north,stutter_north,stop_start,turn_90,circle,teleport
- PASS `motion_fingerprints_distinguishable` — straight_north=1,stutter_north=13,stop_start=2,turn_90=2.414,circle=9.204,teleport=56.286

## Prediction observations

- `cadence_vs_interpolation`: stutter has larger output intervals and sequence lag; this does not identify the live interpolation cause
- `transport_ordering`: pure driver preserves logical event order; UDP/WebSocket comparison is deferred to Gateway driver
