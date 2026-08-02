# C10a vehicle-control contract verification

Status: **source classification accepted** on 2026-08-02. This is not a vehicle
or mount physical-play receipt; those remain separate gates.

The repaired repository extractor was rerun against the pinned Valheim assembly
(SHA-256 `3b26c8512778f6e0664b5af2a26f3c30993a00f584c1e76d9123a742b67e2004`).
It reproduced 19 routed, 21 direct, and 120 instance RPC names with zero unresolved
registrations, and reproduced the tracked instance inventory exactly.

The result closes the C8 audit's `[VERIFY]` assumption by **rejecting** it:

- `RequestControl(Int64)`, `ReleaseControl(Int64)`, and
  `RequestRespons(Boolean)` are each registered by both `ShipControlls.Awake` and
  `Sadle.Awake` under the same stable method hash;
- the ship handler treats `s_user` as a persistent profile identity and does not
  transfer ZDO ownership;
- the saddle handler treats `s_user` as a session/ZDO identity and transfers ZDO
  ownership to the requester;
- therefore one method-name admission or one generic extension of the C4 pickup
  lease cannot preserve both contracts.

The three methods remain deliberately outside the generic routed allow-list. The
focused `VehicleControlCollision_RequiresTypedShipAndSaddleContracts` regression
test locks the exact dual registration, payload signatures, and fail-closed
non-admission. In cutover mode an attempted generic send enters the existing
unadmitted-send ledger and poison blocks it; it cannot silently fall back to native
transport.

The correct work split is now explicit: the vehicle gate owns a typed ship-control
contract, and the mount gate owns a separate typed saddle-control/ownership contract.
Neither family receives physical credit from this source-only classification.
Machine-readable evidence is in
[`verification-summary.json`](verification-summary.json).
