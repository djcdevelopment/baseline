# C10a `UseStamina` physical verification

Status: **accepted on the AM4 local lane** on 2026-08-02. P7 was not
started or changed.

Exact paired candidate `m7-c10a-20260802-r6` ran on the real OMEN and i5
clients against the AM4 dedicated server. The mod DLL SHA-256 was
`f0eedcb413facf74c2cc4b3d0ec67d821a89c6595d5e4ee00fbfe97ced83a396` on
both server paths and both clients. The local Gateway container ran image
`sha256:f43178d2cca5b6527a3be0793c5bbbf10bd01100c5e09dad64158f10bb0f6f07`.

Accepted run `native-20260802-c10a-stamina-r6-sync1` proved both legitimate
cross-owner directions through the exact vanilla `UseStamina(Single)` instance
RPC:

- OMEN selected i5's live player `1430818948:1`, whose ZDO user matched its
  current owner. i5 retained `before=50;requested=1.25;after=48.75`, then OMEN
  received the correlated pass receipt.
- i5 selected OMEN's live player `218250549:1` under the same invariant. OMEN
  retained the same exact debit and i5 received the correlated pass receipt.

Both real `valheim.exe` processes were independently observed responsive in
interactive session 1 before and after the required fresh-process resume. Both
clients completed the 18-action manifest and one relaunch. OMEN, i5, and AM4
recorded zero native network use and zero poison trips with poison armed. Every
runtime cutover control was disarmed afterward, both client configs matched their
pre-run backups byte-for-byte, both games stopped, the i5 task returned to `Ready`,
and residue cleanup reported `matched=0 destroyed=0`.

The first r6 attempt, `native-20260802-c10a-stamina-r6`, is retained as a harness
falsifier rather than counted as a product pass. i5 completed its debit at
16:24:44.461Z and immediately entered the deliberate disconnect/resume action at
16:24:44.479Z; OMEN did not start its reciprocal action until 16:24:45.853Z. The
peer therefore disappeared inside OMEN's proof window. The generator now inserts
a 25-second post-proof hold on both clients, covering the reciprocal 20-second
deadline plus observed startup skew. The accepted retry used the same r6 DLL and
Gateway image; no semantic threshold was weakened.

The compact machine-readable receipt is
[`verification-summary.json`](verification-summary.json). Full local run material
is retained under the ignored directories
`fieldlab/runs/native-valheim/native-20260802-c10a-stamina-r6/` and
`fieldlab/runs/native-valheim/native-20260802-c10a-stamina-r6-sync1/`.

This receipt closes only `UseStamina [VERIFY]`. At capture time, vehicle-control
verification plus four physical family gates remained. Subsequent retained receipts
closed the source split and the physical ship/vehicle gate. Mount, container/station,
and AI/creature now remain before P7 promotion and fallback deletion.
Workbench/dashboard work remains frozen until those three local gates close.
