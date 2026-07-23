# M6-1 — Node-Shape Contract

## Objective
Write the contract that keeps every local lab instance architecturally
identical to a future federation node — same gateway surface, same
signed-config trust mechanism, same telemetry contract — so Projection becomes
"turn on peering between instances that already exist," never a second system.

## Context
This is a design/contract document plus conformance checks, not a build.
Inputs: the lab stack (M4-2), the secrets boundary (M4-3), the telemetry
record schemas (`network/telemetry-and-scores.md`), gateway contracts
(`network/mcp/contracts`). Doctrine: scores advise before they control — the
same restraint applies to any cross-node behavior later.

## Steps
1. Write `docs/node-shape-contract.md` defining what "node-shaped" means as
   testable invariants, e.g.: (a) all inter-service communication goes through
   the gateway surface, no side channels; (b) every config the mod/server
   consumes is signed and verified — no unsigned path exists even locally;
   (c) telemetry emitted conforms to the documented record schemas with
   `session_id`/`build_version` populated; (d) the instance is addressable by
   one endpoint + one trust root; (e) nothing assumes it is the only instance
   (no hardcoded names, ports configurable).
2. Audit the current lab stack against each invariant. Violations become a
   table: invariant / current state / gap / effort. Do not fix in this plan —
   file the list.
3. Add a conformance script `tests/proofs/node-shape.ps1` checking whatever is
   mechanically checkable today (schema fields present in a sample log,
   unsigned-config rejection, port configurability). Partial coverage is fine;
   state what's manual.
4. Add a line to `infra/lab/README.md`: changes to the stack must keep the
   node-shape invariants; link the contract.

## Acceptance
- Invariants are each testable-in-principle (no vibes like "clean
  architecture").
- Audit table complete; conformance script runs and reports honestly,
  including its own coverage gaps.

## Out of scope
Fixing violations; any actual peering; discovery/registry design.
