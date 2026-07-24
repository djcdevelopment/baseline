# m7-e02-recipient-fanout / recipient-isolation-v1

- Run: `gateway-20260724T073759Z`
- Driver: `gateway`
- Seed: `412`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `gateway_recipient_partition` — ValheimZdoRedirectService kept one pending revision and one terminal ACK per emitted recipient
- PASS `gateway_duplicate_terminal_apply` — replayed batches were counted as duplicates without producing a second pending item
- PASS `gateway_fanout_scales_with_observers` — n=2:1,n=10:5,n=100:65

## Prediction observations

- `gateway_queue_partition`: recipient-local pending and ACK state remains independent through the real redirect service
- `gateway_duplicate_handling`: duplicate records are observable and do not double-apply at ACK
