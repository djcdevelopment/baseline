# m7-e00-lab-truth / lab-truth-v1

- Run: `pure-20260724T070121Z`
- Driver: `pure`
- Seed: `410`
- Classification: `inconclusive`
- Stop: `timeout`

## Invariants

- PASS `deterministic_event_count` — expected=12; observed=12
- PASS `snake_case_payload` — payload keys are lowercase

## Prediction observations

- `same_seed_same_input`: repeated runs should produce byte-identical normalized decisions
