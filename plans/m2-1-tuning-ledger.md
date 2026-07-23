# M2-1 — Tuning Ledger

## Objective
Every manual netcode tuning change becomes a structured, citable entry linking
knob → hypothesis → before/after session logs → verdict. Turns folklore weights
into chains of evidence and feeds the M3 replay harness.

## Context
Tuning is manual today and session logs are committed to git (find them under
`data/` / `network/` — locate the JSONL session logs first and record the path
in the ledger doc). The scoring language and current weights live in
`network/telemetry-and-scores.md` (owner score: network .35 / frame .20 /
headroom .20 / proximity .20 / load penalty .25).

## Steps
1. Locate the actual tuning surface: grep the mod (`network/mod/`) and configs
   for the tunable values (AoI radius, priority weights, send budgets,
   ownership cooldowns, hysteresis dwell). Produce the knob inventory as a
   table in the ledger header — name, config location, current value.
2. Create `network/tuning-ledger.md` with an entry template:
   `id | date | knob | old → new | hypothesis | before-log | after-log |
   verdict (confirmed / refuted / inconclusive) | notes`.
   Entries are append-only; verdicts may be edited once evidence lands.
3. Backfill entries for any tuning changes discoverable from git history
   (`git log` on the config paths found in step 1). Mark hypothesis fields as
   `retro:` where reconstructed.
4. Add a line to `docs/weekly-rhythm.md` (from M1-3, if present): tuning
   changes without a ledger entry don't ship.

## Acceptance
- Knob inventory covers every tunable found in code/config, with file:line.
- At least the backfillable history is entered; template proven by real rows.
- A reader can go from any current weight value to the entry (or `pre-ledger`
  marker) that set it.

## Out of scope
Provenance tracing (M2-2), replay tooling (M3-1).
