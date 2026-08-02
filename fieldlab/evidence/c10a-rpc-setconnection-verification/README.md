# C10a `RPC_SetConnection` verification

**Closed:** 2026-08-02

The C8 breadth audit classified global routed method
`RPC_SetConnection(ZDOID,ZDOID)` as P2 `[VERIFY]` for portal linking. The pinned
Valheim assembly and the accepted r4 physical run resolve it as
**superseded by the server portal-connection cache**, with deliberate non-admission as
the poison tripwire.

The extractor-v2 inventory and a fresh read of the matching assembly (SHA-256
`3b26c8512778f6e0664b5af2a26f3c30993a00f584c1e76d9123a742b67e2004`) agree on the
global registration and exact two-`ZDOID` payload. `Game.Start` registers the handler.
The only outbound invocation is inside vanilla `Game.SetConnection`, reached by the
vanilla server `ConnectPortals` loop when a portal is owned by a live peer.

Baseline replaces both owning paths when `portalConnectionCacheEnabled=true`:

- `PortalConnectionCachePatches` suppresses `Game.ConnectPortals` and performs the
  pairing directly on the authoritative server;
- `PortalSavedConnectionPatches` replaces the load-time saved-connection join;
- both paths set the portal owner to the server session and write both typed portal
  connections directly, so the branch that invokes `RPC_SetConnection` is unreachable.

The exact r4 server config had the cache enabled. Its fresh boot receipt hash-joined
4,472 saved portal pairs and the steady cache indexed 15,133 portals. In
`native-20260802-c10a-r4`, both physical clients traversed the same connected portal pair
4.1 km in both directions and returned under native poison. Neither client nor the server
recorded an `RPC_SetConnection` routed row; all three native totals stayed zero.

The method is intentionally **not** added to the generic routed admission contract.
`PortalConnectionRpc_RemainsUnadmittedAsAPoisonTripwire` locks that fail-closed choice:
if the server replacement ever stops owning the call graph, the existing unadmitted-send
ledger/poison path must expose the regression rather than silently duplicating portal
link state through a second lane.

The compact source/runtime receipt is
[`verification-summary.json`](verification-summary.json). This closes the method's
admission classification and connected-pair physical proof. It does not claim a new
runtime portal retagging test; that semantic remains owned by the cache's dirty-tag path,
not by `RPC_SetConnection` or the generic routed lane.
