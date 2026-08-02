# C10a `RPC_TeleportPlayer` verification

**Closed:** 2026-08-02

The C8 breadth audit marked global routed
`RPC_TeleportPlayer(Vector3,Quaternion,Boolean)` as deferred-with-poison-guard
`[VERIFY]`. The pinned Valheim call graph and the accepted r4 normal-play run confirm
that classification.

`Chat.Awake` registers the method, and `Chat.TeleportPlayer` is its only outbound
wrapper. The entire pinned assembly has one caller of that wrapper: Terminal's
`recall [*name]` console command. The command is marked cheat-only and admin-only and
is not a network-forwarded command. Its handler loops the current peer list and asks
each selected remote client to teleport to the administrator.

This is not portal travel. `TeleportWorld.Teleport` resolves the connected portal ZDO
and calls `Player.TeleportTo`; if that player is not locally owned, Valheim uses the
already-admitted instance method `RPC_TeleportTo`. The global chat method is only the
optional admin `recall` feature.

The accepted r4 scenario included two physical, two-way portal roundtrips plus ordinary
movement, reconnect, ownership, zone, motion, and routed traffic under native poison.
OMEN, i5, and AM4 recorded zero `RPC_TeleportPlayer` rows, zero native use, and zero
poison trips. That is the required normal-play falsifier: portal traversal did not reopen
the deferred admin method.

`AdminRecallTeleportRpc_RemainsDeferredAndPoisonGuarded` locks the exact extractor-v2
shape as deliberately unadmitted. `TryGet`, generic envelope admission, and routed
envelope admission must all reject it, so invoking `recall` in a cutover session fails
loudly through the existing unadmitted-send ledger/poison path instead of using native
fallback.

The compact receipt is [`verification-summary.json`](verification-summary.json). This
closes the classification; it explicitly defers the admin `recall` feature. Supporting
that feature later requires an authenticated operator command over Lumberjacks and is not
silently included in the final gameplay transport claim.
