# m7-e04-vehicle-relevance / third-recipient-enter-leave-v1

- Run: `pure-20260803T013343Z`
- Driver: `pure`
- Seed: `414`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `third_recipient_enter_leave` — observed=Outside,Entered,Retained,Left,Entered
- PASS `hysteresis_prevents_boundary_flap` — outer=64; hysteresis=8; retained_at=70
- PASS `recipient_edges_are_independent` — owner remains relevant while observer and third leave on their own distances
- PASS `deliver_matches_open_edge` — only entered and retained recipients receive the direct snapshot

## Prediction observations

- `producer_direct_fanout`: each native recipient is evaluated independently; far and left recipients receive no snapshot
