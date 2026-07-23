# Decisions pending — the batch-in-a-downtime-window register

One place for open decisions that need Derek. Append as
`- [ ] <date> — <decision> (source: <link>)`; check off with a link when resolved.
Bounded: touch only lines a session created or resolved.

## Open

- [ ] 2026-07-23 — **Substrate-gap policy for the adoption backlog.** Three plans rest on missing
  substrate; each needs a call (recommendations in the retro): (a) **M3-1 replay** — capture one real
  session JSONL as a fixture (piggyback a live playtest) vs. build against a labeled synthetic fixture;
  (b) **M6-2 signing** — write the honest threat-model doc now and defer building keyed signing vs.
  build real crypto signing; (c) **M4 lab** — do M4-1 inventory now and gate M4-2/3/4 on whether a
  turnkey demo is imminent. (source: fieldlab/retro/SESSION-RETRO-2026-07-23.md)
- [ ] 2026-07-23 — **M2-2 decision-provenance** (net48 hot-path trace + tests): take it next, or defer.
  It's the only remaining M2 item and needs its own build/test cycle. (source: SESSION-RETRO-2026-07-23.md)
- [ ] 2026-07-23 — **Next milestone pick.** Recommendation: **M3-2 tradeoff cards** (unblocked by the
  M2-1 knob inventory, offloads cleanly, no substrate decision) over M2-2. (source: SESSION-RETRO-2026-07-23.md)
- [ ] 2026-07-23 — **Git automation force-pushing published `main`** — is it intended? It rewrites SHAs
  already on `origin/main`; harmless if solo, but destructive to anyone who has pulled `baseline`
  (there's an `agent/boundary-events-build-pipeline` tracking branch). Highest-consequence open item.
  (source: memory `baseline-repo-auto-commits-and-pushes-main`)
- [ ] 2026-07-23 — **Adoption/process ADR home.** Netcode ADRs are scoped to the netcode-replacement
  program (`fieldlab/docs/adr/`); adoption/process decisions currently land only in retro + memory +
  this register. Do they need their own ADR track, or is this enough? (source: SESSION-RETRO-2026-07-23.md)
- [ ] 2026-07-23 — **Residue backfills** (`docs/residue/gm-a`, `gm-b`) need Derek's real GM-session
  recall (or a VOD to draft from); they ship as honest placeholders until then. (source: docs/residue/)
- [ ] 2026-07-23 — **`--redact` log-tail toggle** (mask `playerId`/`owner_id`/names in the noisy tails
  demoed on stream) — build it bundled into M5-1 or M2-2, not standalone. Filed as a TODO in
  `docs/stream-ops-hygiene.md`. (source: docs/stream-ops-hygiene.md)
- [ ] 2026-07-23 — **Web-serve `docs/alpha-expectations.md` on `/community`** (same cheap pattern as the
  data-trust page) — optional; batch with the next Gateway-facing change. (source: SESSION-RETRO-2026-07-23.md)

## Resolved

- [x] 2026-07-23 — Scope of the `/plans/` pass → **M1 only, then reassess** (Derek).
- [x] 2026-07-23 — How to handle false-premise plans → **document the truth, don't fake substrate** (Derek).
- [x] 2026-07-23 — Journal taxonomy for adoption commits → **added an A1–A6 adoption track**, published
  (`cd5755b`).
- [x] 2026-07-23 — A-track public visibility → **publish it** (built in the open), re-toned volunteer-facing (Derek).
