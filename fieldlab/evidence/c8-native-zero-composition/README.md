# C8 native-zero composition — retained AM4 boundary

**Accepted:** 2026-08-01

**Runtime reconfirmed and wall 11 closed:** 2026-08-02

`native-20260731-c8-full44` and `native-20260731-c8-full45` each ran the complete
49-action composition from clean OMEN and i5 launches on one frozen build with native
poison armed unconditionally on both clients AND the dedicated server: Steam-free cold
join, co-presence, movement in both directions, pickup on both clients, target-ZDO
interaction, two-peer ownership contention, zone exit/enter, a bounded Gateway
interruption with replay, WebSocket resume, a deliberately dropped UDP range, and clean
disconnect/rejoin. Both runs passed the machine-checked composition summary, the
20/20 scenario coverage gate, and the before/after save-integrity comparison with zero
failed checks; the per-run residue receipts recorded `destroyed=0`, the steady-state
proof that completed runs leave no synthetic objects behind.

Reaching the pair closed six receipted wall classes in one night, none of them
gameplay-boundary defects: the restart-staled canonical zone bank (phantom uids
livelocking spawn readiness through vanilla's terrain-compiler duplicate removal), an
observe verdict blind to idempotent receipt-snapshot arrival, a drive protocol that
constructed but never enqueued its valid receipt-required delivery, the Windows
QuickEdit console selection freezing the whole client at its next log burst
(root-caused from a live hang dump), lease control frames starving behind bulk zone
content at the bounded session outbound, and legitimate local teleports having no
legal channel past the observer's fail-closed 30m guard. One further finding was pure
deadline calibration against vanilla's decompiled teleport contract. The one-time
world sweep receipt (`residue-sweep-20260731.json` in this directory) and the roadmap
journal notes of 2026-07-31/08-01 carry the full chain.

The machine-readable result and source hashes are in
[`gate-summary.json`](gate-summary.json). The retained per-run receipts are tracked
under `fieldlab/runs/native-valheim/native-20260731-c8-full44/` and `.../full45/`;
the complete raw logs remain in the ignored run bundles and are not duplicated here.

`native-20260802-cutover-recovery5` then repeated the full physical composition on
fresh GPU-rendered Valheim processes on OMEN and i5 after deploying one hash-identical
candidate to both clients and AM4. All 49 actions and 20/20 coverage checks passed,
client and server native totals and poison trips stayed zero, Gateway restart replayed
1,632 durable objects, ownership contention rejected the second logical peer, both
clients disconnected and rejoined cleanly, and the AM4 save fingerprint remained
exact. The compact receipt is
[`recovery5-session-epoch-gate.json`](recovery5-session-epoch-gate.json).

The same window closes wall 11's runtime half. The real AM4 dedicated-server restart
changed the accepted epoch from session component `000000004f34febc` to
`000000008ef610a2`; a Gateway-only restart retained 1,632 durable objects inside each
session. A syntactically valid mutation carrying the old epoch then returned HTTP 409
`world_epoch_not_active`, wrote no WAL bytes, and left the active new-session bank at
zero objects. The interim manual WAL-discard rule is therefore retired on AM4.

This evidence proves the C8 composition boundary on AM4 for the selected/registered
method and prefab surface and the session-scoped epoch runtime gate. It does not prove
the unselected breadth (the 29 P1 admissions, three [VERIFY] rows, and three
component-family gates from the C8 breadth audit), subjective motion quality, release
alignment, or P7 promotion/fallback deletion; those remain C9-C10.
