# C10a r2 deterministic replay falsifier

`native-20260802-c10a-r2` is failed physical evidence. It must not be cited as
a native-zero acceptance run.

The paired `m7-c10a-20260802-r2` artifacts were deployed hash-exactly to AM4,
OMEN, i5, and the local Gateway. Both physical clients launched the game and
progressed through the routed-RPC, journal, Gateway-restart, ownership, and
zone-cross boundaries. OMEN completed all 49 actions. i5 stopped at
`i5-c8-zone-resume` with `applied=1 replayed=0 complete_count=0`.

The failure was a deterministic-gate bug exposed by different machine timing.
i5 applied reliable zone chunk sequence 2842 and deliberately aborted its
socket before the semantic snapshot ACK. Before that abort reached Gateway, a
later processed frame sent cumulative transport ACK 2843. Gateway therefore
removed two pending frames, including 2842, and had nothing to replay after the
session resumed. OMEN happened to abort before its later cumulative ACK crossed
the held chunk and therefore replayed the chunk successfully. The r3 source
installs an ACK barrier on the receive worker before banking the first resume
chunk; later ACKs remain deferred until that exact sequence is replayed.

The same i5 window also correctly fail-closed two previously unadmitted normal
world-object updates: `RPC_HealthChanged(float)` from `WearNTear.Awake` and
`RPC_UpdateMaterial(int)` from `MaterialVariation.Awake`. Their hashes,
signatures, and counts are retained in `failure-summary.json`. They are added as
exact P2 instance admissions in the shared mod/Gateway contract; this does not
declare the broader component-family work complete.

Retained local receipts:

- `fieldlab/runs/native-valheim/native-20260802-c10a-r2/i5/lifecycle.json`
- `fieldlab/runs/native-valheim/native-20260802-c10a-r2/i5/world-zone-cutover.jsonl`
- `fieldlab/runs/native-valheim/native-20260802-c10a-r2/i5/routed-rpc-cutover.jsonl`
- `fieldlab/runs/native-valheim/native-20260802-c10a-r2/omen/world-zone-cutover.jsonl`
- `fieldlab/runs/native-valheim/native-20260802-c10a-r2/residue-cleanup.json`

The orchestrator disarmed every runtime control, destroyed the three tagged
probe objects, restored both client configs, and stopped both clients. P7 was
untouched.
