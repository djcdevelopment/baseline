# m7-e01-relevance-shape / relevance-boundaries-v1

- Run: `pure-20260724T070153Z`
- Driver: `pure`
- Seed: `411`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `density_response_monotonic` — 1x=5,2x=10,4x=20
- PASS `boundary_shape` — observed=EmitFull,EmitFull,EmitThinned,EmitThinned,EmitThinned,Drop

## Prediction observations

- `radius_and_density_direction`: near and mid objects emit; far objects drop; higher density increases emitted decisions
- `boundary_chatter`: clean crossings are monotonic; repeated noisy samples are retained for later chatter analysis
