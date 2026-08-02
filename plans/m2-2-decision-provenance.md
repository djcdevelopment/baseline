# M2-2 — Decision Provenance in the Hot Path

## Objective
When the netcode drops, defers, or reprioritizes an update, emit a trace of
WHICH filter/priority band made the call and the score at that moment — so a
player-visible artifact ("the troll teleported") is attributable to a specific
decision, not a statistic.

## Context
Build boundary: the mod targets net48 and is compiled through the Docker
Workbench image with a read-only Valheim mount and plugin-copy disabled. A host
SDK MSB3644 is an expected boundary; do not add a second build lane.
`network/telemetry-and-scores.md` already specifies aggregate counters
(`dropped_low_priority_count`, `messages_by_priority`). This plan upgrades from
counts to per-decision attribution. Mod code: `network/mod/ComfyNetworkSense`
(net48 — compile through the Docker Workbench image with a read-only Valheim
mount and plugin-copy disabled; tests exist in
`ComfyNetworkSense.Tests`).

## Steps
1. Find the shedding/priority decision points in the mod (search for where
   priority classes are assigned and where sends are skipped/deferred).
2. Design a compact JSONL record — `decision_trace`: `timestamp_utc,
   session_id, region_id, zdo_or_entity_ref, decision (drop|defer|downgrade),
   filter_name, priority_band, score_inputs (small map), budget_state`.
   Sampling guard: full traces are too hot for steady state — emit 100% during
   `Combat`/`Staging` modes or when a debug flag is on; sample (e.g. 1-in-N or
   only-on-spike) otherwise. Make the rate a config knob and add it to the
   M2-1 knob inventory.
3. Implement behind a config flag (default: sampled). Write to the existing
   session-log directory alongside the other JSONL outputs.
4. Unit tests in `ComfyNetworkSense.Tests`: a decision produces exactly one
   trace with the right filter name and inputs; sampling honors the rate.
5. Add a short section to `network/telemetry-and-scores.md` documenting the
   record type (keep the doc the single source of truth for record schemas).

## Acceptance
- Tests pass through the Docker Workbench build receipt; a host SDK MSB3644 is
  an expected boundary.
- A recorded session with the flag on yields traces that reconcile with the
  aggregate counters (spot-check: sum of drop traces ≈ dropped count when at
  100% emission).
- Schema documented next to the other record types.

## Out of scope
Server-side changes; visualization (M3); auto-tuning.
