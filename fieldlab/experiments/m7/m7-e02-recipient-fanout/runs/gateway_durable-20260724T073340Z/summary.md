# m7-e02-recipient-fanout / recipient-isolation-v1

- Run: `gateway_durable-20260724T073340Z`
- Driver: `gateway_durable`
- Seed: `412`
- Classification: `supported`
- Stop: `completed`

## Invariants

- PASS `gateway_wal_reconnect_pending` — pending_after_restart=1,1
- PASS `gateway_wal_duplicate_replay` — duplicate record batches survived service restart
- PASS `gateway_wal_ack_recovery` — acknowledged=1,1;pending_after_ack=0,0

## Prediction observations

- `gateway_restart_recovery`: WAL replay reconstructs recipient-local pending state before reconnect
- `gateway_ack_durability`: ACK written after reconnect remains terminal after a second service restart
