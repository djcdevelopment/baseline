# DEREK BATCH 1 — Decide & Seed (~45–60 min, no game, minimal terminal)

Everything below needs *you*; nothing else does. Work top to bottom. Items marked ⏳ get
finalized by the agent after your answers. Status of the wider rollout when you left:
**Phase 0 done** (in-flight networking work landed + pushed, retro written, lane pinned —
`fieldlab/PINNED-networking-lane-2026-07.md`, A7 milestone opened). Phases 1–4 (fix-ups,
Workbench page, one-pagers, zips, Discord drafts) ran autonomously — this checklist is the
gate before anything DEPLOYS or gets ANNOUNCED.

## 1. Commit `docs/audit/`? — yes / no
Two memos sit untracked, self-marked "left uncommitted for review":
- `docs/audit/2026-07-24-independent-36h-audit.md` — 36h/184-commit audit. One HIGH
  (terraform apply from baseline would destroy the P7 VM — already a standing memory),
  MEDs: zero Companion test coverage, timing-unsafe key comparisons + unauthenticated
  internal endpoints, floating base-image tags, AI-work-attributed-to-human commit
  provenance. Concludes the moat is the method/ADRs, supports the BSL show-all posture.
- `docs/audit/2026-07-25-gcp-burn-rate-review.md` — **~$95–115/mo GCP estimate, ~80% the
  always-on n2-highmem-2 VM**; ~250 GB orphaned pre-cutover snapshots (~$6.50/mo);
  recommends VM right-sizing/scheduling + BigQuery billing export. **You haven't read this
  one — it has cost implications.**
→ Decision: `[ ] commit both  [ ] commit 36h only  [ ] leave uncommitted`

## 2. Public comfy repo carries other people's data — pick one
`github.com/djcdevelopment/comfy` (PUBLIC) tracks `data/raw/*guild-tracker*.xlsx`,
`data/processed/quest-picker.html` (real catalogs incl. member names),
`waypoints.json` (real player handles). The Workbench points community attention there
(recovery pointers into `handoffs/`). Options:
- `[ ]` **Leave as-is** — it's been public; the guilds shared these trackers openly.
- `[ ]` **Prune** — remove `data/` + `waypoints.json` from comfy HEAD (history still holds
  them unless rewritten; honest but partial).
- `[ ]` **Link-only** — Workbench links go only to `recipes/` + `handoffs/` paths (already
  true in the drafts); add a note to comfy's README asking people not to redistribute the
  data dirs.
→ Also approves/blocks: pushing the stale-doc banner to comfy's copy of
`quest-vertical-slice-architecture.md` (baseline's copy is already bannered).
`[ ] approve comfy pushes  [ ] baseline only`

## 3. Review the Workbench page — approve statuses + framing
Open `Lumberjacks/src/Game.Gateway/Community/workbench.html` **directly in a browser**
(self-contained file, no server needed). Check:
- The four first-wave statuses read true to you (live / local-only / dev-only / recoverable).
- The **"not a verdict"** line (the positioning rule) sounds like you.
- The ladder (Curious → Ran it → Fixed one thing → Steward → Owner) — Steward = code
  access to that piece only; baseline stays private otherwise.
→ `[ ] approved  [ ] edits needed:` _______________

## 4. Discord (only you can): channel + threads
1. Create a forum channel (suggest: `#workbench`).
2. Create 6 threads and paste the seeds from `Lumberjacks/docs/workbench/discord/`:
   01 quest-picker · 02 steward-view · 03 community-telemetry · 04 steam-join ·
   05 pinned-how-this-works (pin it) · 06 recoverable-pieces.
3. **Do NOT post `00-announcement.md` yet** — that's Batch 2, after the deploy.
4. Paste the 6 thread URLs here (or just tell the agent):
   - quest-picker: ______
   - steward-view: ______
   - community-telemetry: ______
   - steam-join: ______
   - how-this-works: ______
   - recoverable: ______
⏳ Agent then fills `discussion.href` per tool, re-renders, re-checks.

## 5. Roadmap public links point into the PRIVATE baseline repo
`valheim-volunteer-roadmap.json` `links[]` (rendered on the public /roadmap) href to
`github.com/djcdevelopment/baseline/...` → 404 for the public. Pre-existing.
→ `[ ] accept for now  [ ] site-serve those docs later (backlog)  [ ] adjust links now`

## 6. Licensing wording tension (acknowledge only) + StewardView license
`LICENSING.md` says "Baseline is public source" + "deployed source must remain public"
while baseline is private. No agent action taken. The public roadmap's old "open source"
journal wording got an appended correction + a generator guard (BSL 1.1 stated accurately).
→ `[ ] acknowledged`

**New finding:** `ComfyStewardView/LICENSE.md` is **proprietary/all-rights-reserved**
("no permission... without explicit written permission and a paid license") — but the
Workbench catalogs it with community first-tasks (SV-2 asks someone to write its docs).
Per-tool license fields now state the truth (StewardView proprietary; the comfy archive
is MIT; baseline tools BSL 1.1). Decide the posture:
→ `[ ] keep proprietary (contributions = docs/feedback only — catalog says so)
   [ ] relicense StewardView (e.g. BSL like baseline)  [ ] pull it from the first wave`

*FYI, already fixed:* the quest picker's save instructions pointed at the pruned
`comfy-control/` config path while the live mod reads `comfy-network-sense/` — silent
failure for any volunteer. Corrected in the picker + schema doc before the zip build.

## 7. Deploy go/no-go (Phase 5 — ~30–45 min, agent drives)
One image cut + promote (adds `/workbench` + `/workbench/downloads/*` routes; admitted mod
release UNCHANGED at m30-rolecontrol), then publish `workbench.html` + zips to the P7
roadmap mount. After this, every catalog update is a file copy — no more image builds.
Rollback = re-pin previous image. **No terraform, no compose changes.**
→ `[ ] go — schedule it  [ ] hold`

## 8. Batch 2 preview (after deploy): post `00-announcement.md`, first reply pass (~30 min).

---
*Generated 2026-07-28/29 during the rollout session. The full plan is at
`~/.claude/plans/i-m-running-out-of-jaunty-cupcake.md`; open decisions also live in
`DECISIONS-PENDING.md`.*
