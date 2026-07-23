# M3-2 — Tradeoff Cards (one per knob)

## Objective
For every tunable in the knob inventory, one card: what it controls, which
equation it feeds, which axis it moves (freshness ↔ bandwidth, correctness ↔
CPU, stability ↔ responsiveness, size ↔ cost-to-communicate), the observable
that proves its effect, current value, and a link to the ledger entry that set
it. Stacked, the cards are the tuning workbook; they also back the debug HUD.

## Context
Depends on M2-1 (knob inventory + ledger). Equations in
`network/telemetry-and-scores.md`. The anti-goals section there is binding:
no fake precision, no hiding tradeoffs.

## Steps
1. Create `network/tradeoff-cards/` with one file per knob:
   `{knob-name}.md`, front-matter style header (`knob`, `location` file:line,
   `current_value`, `ledger` entry id or `pre-ledger`), then four short
   sections: Controls / Equation & path (which score or filter consumes it) /
   Tradeoff axis (name BOTH ends and what a player feels at each extreme) /
   Observable (which telemetry field or experiment from
   `network/observability-and-experiments.md` shows its effect).
2. Write cards for all knobs in the inventory. Where the effect is not yet
   measured, say `unverified — candidate experiment: <experiment name>` rather
   than guessing.
3. Index them from a `network/tradeoff-cards/README.md` table: knob, axis,
   current value, verified?
4. Cross-link: ledger entries reference cards; cards reference ledger.

## Acceptance
- Card count == knob inventory count; no knob skipped.
- Every `current_value` matches the checked-out config (grep-verified).
- No card claims an effect without naming its observable or marking it
  unverified.

## Out of scope
The HUD rendering of cards; changing any values.
