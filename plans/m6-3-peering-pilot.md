# M6-3 — Peering Pilot (Projection, first light)

## Objective
Two node-shaped instances exchange something real and small — the minimum
peering that proves "the demo was the node all along." Candidate first
exchange: signed telemetry aggregates (one node's dashboard shows a peer's
aggregate tile), because it is read-only, aggregates-only, and exercises the
whole trust path with zero gameplay risk.

## Context
Prereqs: M6-1 contract (both instances conform), M6-2 signing (anti-replay,
rotation). Doctrine: scores advise before they control — peering starts
observational; no cross-node gameplay authority in the pilot. The endgame is
distributed event computing carried by gamers/modders, but first light is one
arrow between two boxes.

## Steps
1. Design one page first: `docs/peering-pilot.md` — the single exchanged
   artifact (aggregate snapshot: schema, cadence, size cap), transport
   (pull over HTTPS from the peer's gateway is simplest), trust (payload
   signed by the peer's key; keys exchanged manually out-of-band — no
   discovery service in the pilot), and failure behavior (peer down = stale
   tile with staleness shown, never an error cascade).
2. Implement the export: gateway endpoint serving the signed aggregate
   snapshot (reuse the v0 aggregates API shape).
3. Implement the import: poller + verification + a "peer" tile on the
   dashboard showing the peer's aggregates with freshness and signature
   status.
4. Run the pilot: two lab stacks on one machine (compose project names +
   port offsets) or lab ↔ P7 if safer. Let it run a real session; capture a
   screenshot and a session log for the record.
5. Write the findings section into the pilot doc: what the trust path felt
   like, what broke, what the next exchange should be (the doc ends with a
   ranked candidate list — e.g. cross-node event markers, then someday
   ownership signals — each tagged with what new trust machinery it needs).

## Acceptance
- Peer tile shows live peer data with valid-signature indication; tampered or
  stale data is visibly flagged, not silently shown.
- No gameplay behavior changed on either node.
- Findings written; next-exchange ranking justified by the pilot's evidence.

## Out of scope
Discovery/registry, >2 nodes, cross-node gameplay authority, incentive design.
