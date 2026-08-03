# C10a autonomous creature authority physical acceptance

Status: **selected autonomous `MonsterAI` authority accepted on the AM4 local
lane** on 2026-08-02. P7, Workbench, and HEARTH were not started or changed.

Exact paired candidate `m7-c10a-20260802-r36` ran on the real OMEN and i5
Valheim clients against the AM4 dedicated server. All three loaded mod version
`0.5.75` with DLL SHA-256
`f5fafbe2beda387d48191993813201250ad3306f759c9f18a418ffb1056bfad2`.
The local Gateway ran exact pinned image
`sha256:6a79a70e358320fa6ef84cd11cee5b556e0b9b23f9b5a027655db03e3beafc8f`.
AM4 deployment proved the local, host, and container DLL hashes identical,
`plugin_loaded=true`, and `server_ready=true`; the i5 tools then SHA-verified
the same DLL before launch.

The pinned Valheim source establishes the boundary being tested:
`BaseAI.UpdateAI` returns false for a non-owner, and the concrete `MonsterAI`
and `AnimalAI` update paths both delegate to that base owner gate. The selected
physical canary was an actual spawned, tamed, saddled, and then unridden Lox,
so this receipt exercises the concrete `MonsterAI` branch rather than a mock
AI loop.

Accepted run `native-20260802-c10a-creature-r36-1` used a 37-action scenario.
OMEN owned epoch 1, i5 received epoch 2 through the normal saddle transfer,
OMEN briefly acquired epoch 3 while i5 disconnected, and AM4 reclaimed the
mount to the live i5 peer at epoch 4. Each active owner executed 160–161 real
`BaseAI.UpdateAI` ticks, advanced 38–40 canonical snapshots, and moved the Lox
3.351 m, 8.794 m, and 7.088 m. The corresponding non-owner replicas executed
zero owner ticks, recorded 160 blocked ticks, advanced 38–39 canonical
snapshots, and observed 3.845 m, 8.288 m, and 6.992 m of motion. No probe saw a
rider or an authority change during its measurement window.

Autonomous AI resumed 0.0340009 seconds after native rider release and
0.0160033 seconds after disconnect reclaim, both below the two-second bound.
Server snapshots covered all four authority epochs. Both clients hit the stale
transfer/snapshot fences, completed one fresh-process resume, and ended at
`scenario_complete`. OMEN, i5, and AM4 native-use ledgers all remained at zero
with poison armed. Cleanup matched and destroyed exactly the one tagged Lox.
All 19 reducer checks passed.

Run r35 remains the pre-acceptance falsifier. Its initial owner/observer pair
passed, but a delayed durable player snapshot restored the old local
`SyncTransform` parent after canonical saddle release. The new i5 owner then
waited for an unridden creature and the OMEN observer measured only 0.521 m,
correctly failing the unchanged one-metre bound. r36 continuously repairs a
released rider edge whenever canonical `s_user` is zero; the physical i5 log
records `released_rider_edge_repaired ... cleared=1`. The acceptance threshold
was not weakened.

The compact machine receipt is
[`verification-summary.json`](verification-summary.json). Full logs remain in
the ignored run directory
`fieldlab/runs/native-valheim/native-20260802-c10a-creature-r36-1/`.

This closes the selected two-client **autonomous `MonsterAI` ownership,
handoff, loss, and reclaim canary**. It does not claim physical coverage of
every `AnimalAI`/creature species or arbitrary existing untagged targets.
Vehicle/mount generalization with a third recipient and AoI/relevance,
station-specific breadth review, fallback deletion, and P7 promotion remain.
