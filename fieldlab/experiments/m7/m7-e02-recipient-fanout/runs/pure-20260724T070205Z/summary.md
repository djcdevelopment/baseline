# m7-e02-recipient-fanout / recipient-isolation-v1

- Run: `pure-20260724T070205Z`
- Driver: `pure`
- Seed: `412`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `recipient_isolation` — each recipient/revision has at most one terminal emit within each observer-count case
- PASS `fanout_scales_with_observers` — n=2:1,n=10:5,n=100:65
- PASS `already_delivered_is_local` — one observer starts at revision 410

## Prediction observations

- `cross_recipient_activity`: none expected; slow, duplicate, and already-delivered observers remain local
- `scaling_shape`: emissions grow with in-band observers; this is not a 100-player capacity claim
