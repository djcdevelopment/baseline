# Decisions pending — the batch-in-a-downtime-window register

One place for open decisions that need Derek. Append as
`- [ ] <date> — <decision> (source: <link>)`; check off with a link when resolved.
Bounded: touch only lines a session created or resolved.

## Open

- [ ] 2026-07-29 — **GCP spend + cycle time: pick the lever.** Derek's read (2026-07-28
  night): the GCP deploy is baked and predictable and the VM/Gateway limitations are well
  marked, so the always-on posture can be revisited and his keyboard-minutes made worth
  more. Burn memo: ~$95–115/mo, ~80% the always-on n2-highmem-2 VM, plus ~250GB orphaned
  snapshots. Options + staged commands in `infra/gcp/p7/RUNBOOK-cost-and-cycle.md`
  (agent-staged; Derek runs the gcloud — classifier blocks agent-side cloud mutations).
  **Direction set by Derek 2026-07-29:** local-first dev; GCP lean-and-mean tonight (lever A
  only), full shakedown at end of night (B → E dev-backup-posture → C aggressive schedule →
  D-prime e2 family swap only if invoiced data supports it). 2vCPU/16GB is the floor (the
  early overspec was deliberate 800+-headless limit testing); today's "cohort" is his own 3
  accounts + name-known friends, so downtime is a ping, not a commitment. Remaining open:
  executing the shakedown + watching the first restart. (source:
  docs/audit/2026-07-25-gcp-burn-rate-review.md, infra/gcp/p7/RUNBOOK-cost-and-cycle.md,
  Derek 2026-07-28/29)
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

- [x] 2026-07-28 — **Commit `docs/audit/`?** → **Committed** (Derek, 2026-07-29; commit
  `92445fb` — all four files incl. the onboarding review + brief). (source: DEREK-BATCH-1 §1)
- [x] 2026-07-29 — **PR posture** → **Open to anyone; Derek is the sole approval gate**
  (his call, 2026-07-29). CONTRIBUTING.md updated; ladder stage 3 renamed
  Steward→Contributor ("Steward" is overloaded on the server; the license-suite
  "Community Steward" grant and the ComfyStewardView product name are unaffected).
  **Still open (narrowed):** pick the legal instrument — CLA text vs DCO — before the
  first substantial external PR. (source: Derek 2026-07-29, onboarding review N2)
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
- [ ] 2026-07-29 — **Password-free direct-join is now advertised in a PUBLIC repo.**
  `infra/gcp/p7/README.md` (+ ~7 docs) state the server is Steam-unlisted but
  password-free; any reader can direct-connect without the invite flow once the VM is up
  (it is currently STOPPED, since 07-25). IP redaction is theater (public DNS resolves it);
  the real call: set a Valheim server password (the invite flow can bake it into the
  personalized zip) vs accept open direct-join while the cohort is Derek + name-known
  friends. Decide before the deploy brings the VM back up. (source: onboarding review N3,
  DEREK-BATCH-1 §9)

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
