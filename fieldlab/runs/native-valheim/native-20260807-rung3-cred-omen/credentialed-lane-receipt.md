# Credentialed enrollment-lane receipt — rung 3 (single-client), 2026-08-07

The 2026-08-05 failure-4 class (no enrolled consumer → 409 → terrain-only) closed
on the local rehearsal loop, on the **actual r42 pair**.

## Setup

| Piece | Identity |
|---|---|
| Gateway | `lumberjacks-gateway:m7-c10b-20260807-r42` (`sha256:4329c502…`), OMEN, enrollment-lab overlay (public URL + store on volume) |
| Server | AM4, mod `m7-c10b-20260807-r42` (frozen DLL `08bf698b…` deployed to the cold-start mount; r41 preserved beside it as `.bak-r41`), at-rest cfg armed: `lumberjacksCutoverMode=lumberjacks-primary`, `zdoRedirectEnabled=true`, window + manifest `am4-handshake-async-20260730`, prefabs `Player,Pickable_Mushroom,Mushroom` (scoped, deliberately not `*` on the shared lab world). Cfg backup: `.bak-20260807T083649Z` |
| Client | OMEN tugcorp, credentials injected per-run via the new harness params (`-EnrollmentId/-ClientAccessKey/-AuthoritativeWindowId`), byte-exact restore on stop |
| Credentials | wary.fool enrollment `75e7d213…`, minted through the REAL flow: `/join` invite → Steam OpenID → personalized pack (admin rotation after the consumed bootstrap) |

## Observed

**Positive leg** (`/api/v0/telemetry/cutover`, window `am4-handshake-async-20260730`):
`active_consumers: 1`, `receipts: 8, acknowledged: 8, pending: 0, applied: 8,
rejected: 0`, **`complete: true`** — the enrolled consumer attached with the minted
credential and drained everything the server suppressed. This is the exact inverse
of the 08-05 signature (`active_consumers: 0`, 4,421 pending, applied 0).

**Fail-closed triple** (`?c7_require_enrollment=true` on the gated pending endpoint):

| Presented | Result |
|---|---|
| Valid minted key | 200 |
| **Invalid key** | **401** — validated even from a private socket, not bypassed |
| No headers (loopback) | 200 via the private-plane fallback — a path that does not exist for external clients on P7's public plane |

**Admission nuance (working as designed, worth knowing before candidate 12):**
with a *scoped* prefab window, `coverage_native_only > 0`, so
`CanAcceptPrimaryHeartbeat` refuses admission on the coverage term even while the
consumer is fully caught up (`complete: true`). P7 runs `zdoRedirectPrefabs = *`,
where that term is zero. A scoped rehearsal proves the credential class, not the
admission verdict.

**Empty-server carve-out observed live:** before any client joined, the freshly
booted r42 pair reported `admission.admitted: true` with the manifest id populated
— the r42 fix-5 semantics pinned in `SessionPlaneRecoveryTests`, on a real gateway.

## Path fixed along the way

The alpha modpack template carried no config entry, making `/join` personalization
structurally impossible for every pack published to date (503 `mod pack template is
missing the ComfyNetworkSense config entry`). Fixed in `New-AlphaModpack.ps1`
(sanitized template staged; commit `bb17e61`).

## Remaining for the full rung / gate

- Two-client leg (durracktu enrolled and credentialed; i5 needs Steam in its
  interactive session).
- The ADR 0017 human gate itself: fresh mod-zip install → visible world, on P7's
  credentialed public plane.

## Post-run state

Client stopped, config restored byte-exact. **The AM4 lab server is LEFT ARMED**
(`lumberjacks-primary`, scoped redirect) for the two-client leg; restore the
native at-rest posture with the cfg backup beside the live file
(`cp cfg.bak-20260807T083649Z cfg` + container restart + orphan `.db.new` cleanup).
