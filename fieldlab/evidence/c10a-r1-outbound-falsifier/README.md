# C10a r1 outbound routed-RPC falsifier

`native-20260802-c10a-r1` is failed physical evidence. It must not be cited as a
native-zero acceptance run.

The paired `m7-c10a-20260802-r1` artifacts were deployed to the real topology:
AM4 dedicated server, OMEN/Tugcorp, i5/durracktu, and the local Gateway. The
deployed mod SHA-256 on all three Valheim processes was
`d547bed8a2dd744848ab74495cb9850e781b942be5ccfc56154abf8b22aa3947`; the
Gateway container image id was
`sha256:553f8c6e6187f454d7fbaf022426a50eb7e271fdf352085fd1c34e06049e7aff`.

Both clients completed all 49 C8 actions and each completed the required fresh
process resume. The C7 logical-peer reducer then failed the run because each
client recorded ten native-use/poison trips. The method-level outbound guard
resolved those trips to `Step`, `RPC_DamageText`, and `DestroyZDO`. AM4's same
window also exposed unadmitted `SetEvent`, `GlobalKeys`, `LocationIcons`,
`ComfyNetworkSense_AutoPort`, and `ComfyNetworkSense_ServerPulse` sends. Exact
hashes and per-actor attempt counts are in `method-gap-summary.json`.

This is the contradictory runtime evidence the prior native-zero instrumentation
could not produce: the old ledger covered selected funnels but had no method-level
observation at `ZRoutedRpc.RouteRPC`'s outbound seam. The r2 repair is therefore
scoped to these concrete calls and the breadth audit's already-classified
replacement-owned routed methods. It is not accepted until a fresh single-use
run passes the same poison-armed reducer.

Retained compact receipts:

- `fieldlab/runs/native-valheim/native-20260802-c10a-r1/c7-logical-peer-summary.json`
- `fieldlab/runs/native-valheim/native-20260802-c10a-r1/composition.json`
- `fieldlab/runs/native-valheim/native-20260802-c10a-r1/residue-cleanup.json`
- `fieldlab/runs/native-valheim/native-20260802-c10a-r1/c8-scenario-coverage.json`

The reducer failed before the orchestrator's post-run save fingerprint stage, so
this run makes no save-integrity claim. Runtime controls were disarmed by the
orchestrator's `finally` cleanup and AM4 returned to `ready` with zero peers.
