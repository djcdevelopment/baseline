# Decisions pending — the batch-in-a-downtime-window register

One place for open decisions that need Derek. Append as
`- [ ] <date> — <decision> (source: <link>)`; check off with a link when resolved.
Bounded: touch only lines a session created or resolved.

Lifecycle (adopted 2026-07-29): this register is a **queue, not an archive**. Resolved
entries compress to one line + a link; rationale with lasting value graduates to
[`docs/decisions/`](docs/decisions/README.md) — one decision, one home. Execution goes
to runbooks/checklists, plans to handoffs, blocked work to the backlog.

## Open

- [x] 2026-07-29 — **Delegation event.** Derek delegated the six entries below as
  future-facing ("we're still building"); the agent decided + documented each against
  the license, capacity (one human + 16 agents), and near-term goals. Rubber stamp
  recorded in each home; **circle back at the
  [First Stranger gate](docs/decisions/pd-2-security-posture-first-stranger-gate.md)'s
  first firing** ("after first alpha tester is live or when someone asks about
  contributing").
- [x] 2026-07-29 — **Contributor agreement instrument** → lightweight CLA v1.0
  ([`CLA.md`](CLA.md) + [signature ledger](docs/legal/cla-signatures.md)); why in
  [PD-1](docs/decisions/pd-1-governance-and-contributions.md).
- [x] 2026-07-29 — **Security disclosure path** → GitHub private vulnerability
  reporting (enabled 2026-07-29) primary, `[SECURITY]`-tagged mailbox fallback;
  promises in [`SECURITY.md`](SECURITY.md).
- [x] 2026-07-29 — **Audit findings disposition** → recorded per finding in
  [`docs/audit/2026-07-29-findings-disposition.md`](docs/audit/2026-07-29-findings-disposition.md).
- [x] 2026-07-29 — **AI-contribution acceptance bar** → symmetric, disclosure-based;
  the *what* in [CONTRIBUTING.md](CONTRIBUTING.md), the *why* in
  [PD-1](docs/decisions/pd-1-governance-and-contributions.md).
- [x] 2026-07-29 — **Public reply-cadence commitment** → affirm the existing truth,
  promise no calendar: batch rhythm, days not minutes (already in CONTRIBUTING);
  deliberately no fixed schedule while the army is one human. Revisit at the gate.
- [x] 2026-07-29 — **Posted-content URL migration at P7 cutover** → yes: bot re-sync
  pass + manual announcement edit, written into the cutover checklist
  (DEREK-BATCH-1 §7).
- [x] 2026-07-29 — **GCP spend + cycle time** → direction set by Derek 2026-07-29
  (local-first dev; lean levers A → B → E → C → D-prime; 2vCPU/16GB is the floor). What
  remains is execution, not decision — operator keyboard time tracked in
  `infra/gcp/p7/RUNBOOK-cost-and-cycle.md` (watch the first restart once). Posture
  revisit at the [First Stranger gate](docs/decisions/pd-2-security-posture-first-stranger-gate.md).
- [ ] 2026-07-23 — **Substrate-gap policy for the adoption backlog.** Three plans rest on missing
  substrate; each needs a call (recommendations in the retro): (a) **M3-1 replay** — capture one real
  session JSONL as a fixture (piggyback a live playtest) vs. build against a labeled synthetic fixture;
  (b) **M6-2 signing** — write the honest threat-model doc now and defer building keyed signing vs.
  build real crypto signing; (c) **M4 lab** — do M4-1 inventory now and gate M4-2/3/4 on whether a
  turnkey demo is imminent. (source: fieldlab/retro/SESSION-RETRO-2026-07-23.md)
- [x] 2026-07-23 — **M2-2 decision-provenance: take or defer** → RECLASSIFIED 2026-07-29:
  a priority ranking, not a decision (register lifecycle). Re-rank at adoption-lane
  resume; don't pre-commit from the 07-23 snapshot. (source: review 2026-07-29)
- [x] 2026-07-23 — **Next milestone pick** → RECLASSIFIED 2026-07-29, same treatment: the
  07-23 M3-2 recommendation predates the Workbench pivot; re-rank at adoption-lane
  resume. (source: review 2026-07-29)
- [x] 2026-07-23 — **Adoption/process ADR home** → RESOLVED 2026-07-29: no second ADR
  track. The registers + retros + the
  [docs/decisions/ promotion path](docs/decisions/README.md) are the record. Revisit at
  the second regular contributor. (source: Derek 2026-07-29)
- [ ] 2026-07-23 — **Residue backfills** (`docs/residue/gm-a`, `gm-b`) need Derek's real GM-session
  recall (or a VOD to draft from); they ship as honest placeholders until then. (source: docs/residue/)
- [ ] 2026-07-23 — **`--redact` log-tail toggle** (mask `playerId`/`owner_id`/names in the noisy tails
  demoed on stream) — build it bundled into M5-1 or M2-2, not standalone. Filed as a TODO in
  `docs/stream-ops-hygiene.md`. (source: docs/stream-ops-hygiene.md)
- [ ] 2026-07-23 — **Web-serve `docs/alpha-expectations.md` on `/community`** (same cheap pattern as the
  data-trust page) — optional; batch with the next Gateway-facing change. (source: SESSION-RETRO-2026-07-23.md)

- [x] 2026-07-28 — **Commit `docs/audit/`?** → **Committed** (Derek, 2026-07-29; commit
  `92445fb` — all four files incl. the onboarding review + brief). (source: DEREK-BATCH-1 §1)
- [x] 2026-07-29 — **PR posture** → open to anyone, Derek sole approval gate; rationale
  promoted to [PD-1](docs/decisions/pd-1-governance-and-contributions.md). The
  instrument (CLA vs DCO) is its own open entry above.
- [x] 2026-07-28 — **Public comfy repo carries other people's data.** → **Leave as-is**
  (Derek, 2026-07-29): everyone whose info appears was talked to and knows; the data is
  already public in several forms (asking was politeness before scraping); Derek reviewed
  and corrected misattributions players reported. "This is how the sausage is made — live
  quest data was donated by active volunteer GMs." (source: rollout plan F5, DEREK-BATCH-1 §2)
- [x] 2026-07-28 — **RESOLVED by the 2026-07-29 visibility flip** (baseline is now PUBLIC,
  so "Baseline is public source" is literally true) — **Licensing wording tension.** `LICENSING.md` says "Baseline is public
  source" and "the exact deployed source ... must remain public" while the baseline repo is
  private. Acknowledge/schedule; no action taken by agents. (source: rollout plan F10)
- [x] 2026-07-28 — **RESOLVED by the same flip** (links now resolve for everyone) —
  **Public roadmap `links` point into the private baseline repo.**
  (source: valheim-volunteer-roadmap.json links[])
- [x] 2026-07-29 — **Accept open direct-join, no server password** (pre-gate posture);
  rationale + due-list promoted to
  [PD-2](docs/decisions/pd-2-security-posture-first-stranger-gate.md). Revisit trigger
  is the First Stranger gate, defined there.
- [x] 2026-07-29 — ~~Password-free direct-join advertised in a PUBLIC repo~~ → duplicate
  of the entry above; resolved the same way, canonical home
  [PD-2](docs/decisions/pd-2-security-posture-first-stranger-gate.md).

## Resolved

- [x] 2026-07-28 — Networking lane pause posture → **hard hold with a pin doc**
  ([fieldlab/PINNED-networking-lane-2026-07.md](fieldlab/PINNED-networking-lane-2026-07.md));
  no human Steam tests scheduled; effort to adoption A7 (Community Workbench). Per Derek's
  rollout direction 2026-07-28.
- [x] 2026-07-23 — Scope of the `/plans/` pass → **M1 only, then reassess** (Derek).
- [x] 2026-07-23 — How to handle false-premise plans → **document the truth, don't fake substrate** (Derek).
- [x] 2026-07-23 — Journal taxonomy for adoption commits → **added an A1–A6 adoption track**, published
  (`cd5755b`).
- [x] 2026-07-23 — A-track public visibility → **publish it** (built in the open), re-toned volunteer-facing (Derek).
- [x] 2026-07-23 — Git automation force-pushing published `main` → **go forward, it's intended** (Derek):
  `baseline` is a solo public-source (BSL 1.1) working sample *(wording corrected 2026-07-29 —
  this entry predates the licensing-term lint)*, so there are no collaborators for a history rewrite
  to disrupt. Recorded in memory `baseline-repo-auto-commits-and-pushes-main` (ACCEPTED).
