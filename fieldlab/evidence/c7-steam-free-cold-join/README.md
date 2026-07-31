# C7 Steam-free cold join — retained AM4 boundary

**Accepted:** 2026-07-31

`native-20260731-c7-cold-final` launched Valheim on OMEN and i5 without
`+connect`, established only the authenticated Lumberjacks session, consumed the
validated world descriptor, constructed the local logical server peer, queued the
typed character id, reached the joined scene, and repeated the path in a fresh
process. Native poison was armed in all four client ledger sessions; both clients
recorded zero native calls, zero poison trips, zero dropped rows, and zero writer
faults. AM4 constructed both logical clients again after resume and recorded zero
selected native peer, handshake, `PeerInfo`, `ZDOData`, or routed-RPC ingress.

`native-20260731-c7-negative-second` retained the four required fail-closed cells.
Invalid enrollment and an unavailable Gateway ended in a deterministic cold-join
failure; wrong release and wrong descriptor/protocol were rejected before scene
entry. Every cell remained poison-armed, recorded zero native use, and never joined.

The machine-readable result and source hashes are in
[`gate-summary.json`](gate-summary.json). The complete raw logs remain in the ignored
run bundles named above. They intentionally contain machine-local operational
details and are not duplicated into the tracked evidence directory.

This evidence proves the C7 connection/bootstrap boundary on AM4. It does not prove
the full gameplay composition, unselected method/prefab breadth, subjective motion
quality, or P7 promotion; those remain C8–C10.
