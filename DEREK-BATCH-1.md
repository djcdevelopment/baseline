# DEREK BATCH 1 — Decide & Seed (~45–60 min, no game, minimal terminal)

Everything below needs *you*; nothing else does. Work top to bottom. Items marked ⏳ get
finalized by the agent after your answers. Status of the wider rollout when you left:
**Phase 0 done** (in-flight networking work landed + pushed, retro written, lane pinned —
`fieldlab/PINNED-networking-lane-2026-07.md`, A7 milestone opened). Phases 1–4 (fix-ups,
Workbench page, one-pagers, zips, Discord drafts) ran autonomously — this checklist is the
gate before anything DEPLOYS or gets ANNOUNCED.

## 1. ✅ RESOLVED 2026-07-29 — Commit `docs/audit/`? → COMMITTED (`92445fb`, all four files incl. the onboarding review)
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

## 2. ✅ RESOLVED 2026-07-29 — LEAVE AS-IS: everyone named was talked to and knows; data already public in several forms; misattributions corrected on player request; live quest data donated by volunteer GMs. Comfy-side pushes unnecessary.
*(original options below, kept for the record)*
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
- The ladder (Curious → Ran it → Fixed one thing → Contributor → Owner) — Contributor = code
  access to that piece only; baseline stays private otherwise.
→ `[ ] approved  [ ] edits needed:` _______________

## 4. Discord — NEW SERVER (id `1531911987074957442`). The bot is built; this is now approval + ~10 min of portal clicking.
`tools/workbench/discord/workbench_discord.py` provisions the forum, the 8 tags, the
guidelines box and the posts **from the repo's seed files**, and re-running it syncs drift
instead of duplicating. It does structure only — it can never reply, react, DM, mention
anyone, or post `00-announcement.md` (hardcoded denylist, no flag). Setup walkthrough:
`Lumberjacks/docs/workbench/discord/09-discord-bot-setup.md`.

1. **~10 min, one time:** create the app + token, put the token in
   `%USERPROFILE%\.baseline\workbench-discord.token`, invite the bot with the URL from
   `workbench_discord.py invite --app-id ...` (minimum permissions — no admin).
2. **Approve the dry run.** Pre-generated, no token needed:
   [`tools/workbench/discord/receipts/2026-07-29-plan-offline.md`](tools/workbench/discord/receipts/2026-07-29-plan-offline.md)
   — exact channel settings, all 8 tags, every post title/tag/length. Re-run `plan` once
   the bot is invited to confirm against the live server, then `apply --yes`.
   → `[ ] approved  [ ] changes:` _______________
3. **Timing finding — this changes the order, and it applies to the manual path too:**
   seeds 01–04 still contain `<ONEPAGER-URL>` / `<ACCESS-URL>`. Pasting them tonight (by
   hand or by bot) would put literal placeholders — or links to a page that 404s — in
   front of the community. The bot **blocks** those four until `/workbench` is live. So:
   - **Tonight:** forum channel + 8 tags + required-tags + guidelines + the pinned
     "How this works" post + "Recoverable pieces" (no links in it).
   - **Right after item 7's deploy:** re-run with
     `--site-base-url https://comfy-p7.duckdns.org` and the other four post themselves.
     Preview receipt: `receipts/2026-07-29-plan-offline-after-deploy.md`.
   Doing the whole thing after the deploy in one pass is equally fine — the server has no
   members yet, and the run is idempotent either way.
4. **Do NOT post `00-announcement.md`** — Batch 2, after the deploy. Now enforced in code.
5. Optional 10 min while you're in settings: load the 7 saved replies from
   `discord/08-saved-replies.md` (or just keep that file open during batch passes).
6. ~~Paste the 6 thread URLs~~ — no longer needed. `apply` records thread ids + URLs in
   `tools/workbench/discord/provision-state.json`.
   ⏳ Agent reads that file, fills `discussion.href` per tool, re-renders, re-checks.

*If you'd rather paste the posts by hand: the manual steps in `07-forum-tags-setup.md`
still work, but a bot can only edit its own messages — hand-pasted posts lose the
diff-and-update pass forever. Let the bot create them.*

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

## 8. Cognitive-lift portfolio — built, two optional touches
Your "find 5–10 ideas, matrix them, build top 5" ask is done: 13 researched ideas scored in
[plans/cognitive-lift-portfolio.md](plans/cognitive-lift-portfolio.md) (sources included),
top 5 built: **announcement drafter** (journal → Discord draft skeleton, never auto-posted:
`tools/workbench/new_announcement_draft.py`), **forum tags** (item 4 above), **bug-fix-shaped
first-task lens** (in the one-pager template), **Already-answered section + saved replies**,
**feedback distiller** (`tools/workbench/distill_feedback.py` → candidate-issues journal).
Optional touches, whenever:
- ✅ Superseded 2026-07-29: the read-only export bot grew into the provisioning bot in
  item 4. Same one-time setup, same token; `workbench_discord.py export` now produces the
  distiller's input directly (DiscordChatExporter still works if you prefer it).
- `[ ]` Skim the portfolio's ranks 6–13 backlog — several are deliberately parked until
  your first real volunteer exists (waves, showcase, credit line).

## 9. Fresh-eyes onboarding review — 3 new items for your radar
Your review brief ran as a context-starved fresh-eyes agent; annotated results (new vs
already-queued vs design-not-defect) in
`docs/audit/2026-07-29-contributor-onboarding-review.md` (uncommitted, like its siblings).
Genuinely new:
- `[ ]` **`ENDtoEND.txt`** — 324 KB tracked raw terminal transcript at repo root, your email
  in the banner. Untrack now? (History still holds it; full scrub only matters at a
  visibility change.)
- ◐ **CLA gap vs the ladder** — POSTURE RESOLVED 2026-07-29: PRs open to anyone, you are
  the sole approval gate (CONTRIBUTING.md updated); ladder stage 3 renamed
  Steward→Contributor. **Still open:** pick the legal instrument (CLA text vs DCO) before
  the first substantial external PR lands. Agent can draft either on your word.
- `[ ]` Noted for the visibility-change gate (no action now): `infra/gcp/p7/README.md`
  advertises the live IP as password-free + plain-HTTP.
Say **"run the cleanup batch"** for the agent-executable fixes (stale-handoff banners,
era-1 doc banners, ~15 pruned-path link footnotes, register wording fix, START-HERE page,
BUILDING.md, glossary) — no Derek time needed.

## 10. Batch 2 preview (after deploy): post `00-announcement.md`, first reply pass (~30 min).

---
*Generated 2026-07-28/29 during the rollout session. The full plan is at
`~/.claude/plans/i-m-running-out-of-jaunty-cupcake.md`; open decisions also live in
`DECISIONS-PENDING.md`.*
