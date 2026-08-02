# C10a ship physical acceptance

Status: **accepted on the AM4 local lane** on 2026-08-02. P7 was not
started or changed.

The original r15 acceptance was re-opened by the exact r27 saddle candidate.
`native-20260802-c10a-vehicle-r27-1` proved that owner handoff could strand the
future owner with the departed first helm user. r28 now requires canonical
`s_user == 0` before transfer and applies that release to both replicas before
the new owner can publish. `native-20260802-c10a-vehicle-r28-1` passed all 19
machine checks: both directions moved, both releases passed, the atomic handoff
reached both clients with `canonical_helm_user=0`, snapshots advanced under both
owners, both clients resumed once, and all native ledgers stayed zero. The
compact regression receipt is
[`r28-handoff-reconfirmation.json`](r28-handoff-reconfirmation.json).

Exact paired candidate `m7-c10a-20260802-r15` ran on the real OMEN and i5
Valheim clients against the AM4 dedicated server. All three loaded mod version
`0.5.54` with DLL SHA-256
`53f6aa18cc97d1d70080136f3ded3d7b77313e39fdd2f168652440e7a2e0ea1d`.
The local Gateway container ran image
`sha256:5d0588cc1c88157e908b190a663630fdd4c03ca851d62f6d2ea28f09b4f62d0c`.

Accepted run `native-20260802-c10a-vehicle-r15-1` used a 34-action manifest
whose 12 choreography checks all passed. It created one non-persistent Karve on
AM4 (`2014258734:9155594`), physically boarded both clients, and proved both
opposite control/physics-authority shapes:

- i5 held the real helm while OMEN owned the ship. i5 drove 15.589 m with
  rudder 1 and a speed change; OMEN independently observed 16.407 m, rudder 1,
  and the speed change before confirming helm release.
- Authenticated server control transferred the ship from OMEN peer
  `1158532546` to i5 peer `1889358686`, and both client replicas applied the
  new owner.
- OMEN then held the real helm while i5 owned the ship. OMEN drove 15.768 m
  with rudder 1 and a speed change; i5 independently observed 15.443 m,
  rudder 1, and the speed change before confirming helm release.

The physics owner sent numbered snapshots to AM4. The server validated the
current owner, journaled the canonical ship mutation, and rebroadcast a
server-originated snapshot to both clients; the non-owner applied the body,
position, rotation, velocity, rudder, speed, control identity, and owner from
that canonical frame. Retained milestones cover both owners at sequences
1/25/50 and beyond.

Both real clients joined on their expected renderers (OMEN: NVIDIA GeForce RTX
5070; i5: Intel Iris Xe), completed one fresh-process resume, and stopped.
OMEN, i5, and AM4 recorded zero native network use and zero poison trips with
poison armed; all ledger writers recorded zero drops and faults. Runtime
controls were disarmed, both configs matched their pre-run backups exactly,
both games were confirmed stopped, the i5 task returned to `Ready`, and residue
cleanup reported `matched=0 destroyed=0`.

Two frames were rejected after the physical driving and release proof: one
stale-owner snapshot during automatic disconnect ownership return, and one
snapshot delivered after i5's networking stack had torn down ahead of the
fresh-process relaunch. The latter logged the caught null dependency explicitly.
Both caused no native fallback and did not prevent either client's required
reconnect or scenario completion. They are retained in the compact machine
receipt instead of being omitted.

Runs r7-r14 remain local falsifiers. In order, they exposed a JSON quoting bug,
a release/transfer race, a missing mode policy, a false boarding predicate, an
observer choreography race, incomplete replica owner propagation, missing
server snapshot fan-out, and a server-local broadcast echo exception. r15 is
the first accepted physical ship run.

The compact machine-readable receipt is
[`verification-summary.json`](verification-summary.json). Full run material is
retained under the ignored directory
`fieldlab/runs/native-valheim/native-20260802-c10a-vehicle-r15-1/`.

The r28 mod artifact was forced through `Rebuild`, decompiled to verify that the
handoff repair was present, and deployed by exact SHA-256; its focused suite
passed 140/140. The r27 Gateway/saddle source had already passed the full Docker
.NET solution gate at 625/625 (126 Contracts, 17 Companion, 250 Simulation,
232 Gateway); r28 did not change that source.

This closes the C10a physical **ship/vehicle gate only**. The selected saddle
canary is now accepted separately; arbitrary untagged mounts and relevance-
scoped fan-out remain broader C10 work. Container/station, AI/creature, general
AoI, P7 promotion, and native-fallback deletion also remain. Workbench/dashboard
work remains frozen behind functional cutover work.
