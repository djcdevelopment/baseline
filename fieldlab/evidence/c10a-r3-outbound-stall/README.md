# C10a r3 physical falsifier — i5 outbound worker stall

Run `native-20260802-c10a-r3` exercised the exact paired r3 artifacts on the real
AM4 server, OMEN, and i5 clients with the full C8 composition and native poison
armed. It is retained as failed evidence, not acceptance.

## Artifact identity

- Source commit: `025b3b02504714a1a112058e316594c69c82208f`
- Mod release: `m7-c10a-20260802-r3`
- Mod SHA-256: `afe9c39c27a8f1a3a9faf95a2f86c9991c0fd17f64bd1d26852b9b9dfa48181f`
- Gateway image: `sha256:933e97fab623bfd8349ca4d85d26617d371617d3899bf926db479439c875b154`
- Scenario SHA-256: `dd68b88a4bfbc5d040ee1723811c6b55ad5a5b03a3c62496e0e7237332c527ac`

## Falsifier

OMEN completed all 49 actions. i5 failed `i5-c8-zone-resume` with
`world_zone_probe_deadline applied=1 replayed=1 complete_count=0`.

The r3 ACK barrier fixed the r2 loss: i5 held reliable sequence 2249 before the
intentional socket abort, received that same sequence after resume, applied it
idempotently, and released its cumulative ACK through sequence 2262. The new
failure occurred after that release:

- Gateway's last inbound message from the i5 connection was at
  `2026-08-02T14:38:34.0007213Z` (`through=2244`). It never received the
  released ACK through 2262 or the semantic chunk ACK.
- i5's receive side remained live and later applied reliable motion-resync frames
  2477, 2483, and 2495.
- Those later handlers recorded `ack_queued=false`; shutdown also recorded a
  failed disconnect queue. The client outbound queue was full and no longer
  draining while inbound delivery continued.
- `LumberjacksGameSessionRunner` did not supervise or time-bound its sibling
  `RunOutgoing` task. A send fault or stalled `ClientWebSocket.SendAsync` could
  therefore leave a half-open receive-only session indefinitely and emitted no
  causal sender event.

The repair acceptance boundary is deterministic: a stalled or faulted send must
abort the socket within five seconds, emit the frame type/sequence/queue depth,
and let the existing resume path replay unacknowledged reliable frames. Unit tests
must force completion, fault, stall, and caller cancellation before another
physical run is allowed.

## Cleanup

The orchestrator stopped both Valheim clients, disarmed every runtime control,
destroyed all three r3-tagged zone probe objects, retained the r2 server DLL as
the AM4 rollback artifact, and left P7 untouched.

Authoritative raw evidence remains under
`fieldlab/runs/native-valheim/native-20260802-c10a-r3/` and is intentionally not
checked into Git because `fieldlab/runs/` is the retained local evidence volume.
