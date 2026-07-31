# C7 early socket-quarantine falsifier

`native-20260731-c7-fourth` is the accepted early-falsifier cell within C7 on
AM4. C7 itself remains in progress.

Verified:

- OMEN/Tugcorp and i5/Durracktu both entered the intended world, accepted the
  Lumberjacks descriptor for `world-ffffffff63e5be34`, and had authenticated
  canonical Lumberjacks sessions before quarantine.
- Each client closed its selected native `ZSteamSocket`; the underlying socket
  reported disconnected before the timed hold began.
- OMEN held the live scene for 60,001 ms with `native_total_delta=0`, while
  suppressing 7,962 socket sends, 7,961 RPC updates, and 1,168 native RPC
  invocations.
- i5 held the live scene for 60,004 ms with `native_total_delta=0`, while
  suppressing 7,031 socket sends, 7,030 RPC updates, and 1,129 native RPC
  invocations.
- Both clients reported `native_fallback=false`, completed one fresh-process
  resume, rejoined on their intended GPU, completed the scenario, and stopped
  unattended.

This falsifies the concern that an already-running Valheim scene inherently
requires a continuously live native socket. It does not prove Steam-free cold
join: native `+connect`, handshake, and peer construction still preceded
quarantine. C7 remains open for constructing that state directly from C1/C2/C5
with native poison armed, plus its fail-closed cells.

The i5 motion consumer again used its expected binary-WebSocket fallback for an
unreachable advertised UDP endpoint. Both clients also logged warnings from the
separate P7 authoritative-consumer poller; those warnings did not participate in
the quarantine boundary. Gateway WebSocket EOF errors align with deliberate
disconnect/relaunch operations.

Machine-readable verdict and hashes are in `c7-early-falsifier-summary.json`.
Raw actor receipts are under `omen/` and `i5/`; `composition.json` is the
orchestration verdict. The append-only receipt files contain older run rows, so
the verdict scopes every assertion to run id `native-20260731-c7-fourth`.
`scenario.json` is a semantic JSON reformat of the deployed manifest; both its
retained-file hash and the hash of the bytes deployed to the clients are recorded
in the summary.
