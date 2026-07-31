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

## 3. ✅ APPROVED 2026-07-30 — Workbench statuses + framing
Open `Lumberjacks/src/Game.Gateway/Community/workbench.html` **directly in a browser**
(self-contained file, no server needed). Check:
- The four first-wave statuses read true to you (live / local-only / dev-only / recoverable).
- The **"not a verdict"** line (the positioning rule) sounds like you.
- The ladder (Curious → Ran it → Fixed one thing → Contributor → Owner) — Contributor =
  commit access to that piece; the repo is public now, so reading was never the gate.
→ **Approved by Derek as deployed, 2026-07-30.**

## 4. ◐ Discord — PARTIALLY DONE 2026-07-29T07:31Z. `#workbench` forum is LIVE on the new server: 8 tags, required-tags ON, guidelines set, **How this works** pinned, **Recoverable pieces** posted. The four catalog threads are held until the deploy (step 3 below). Remaining: run C1 after item 7.
`tools/workbench/discord/workbench_discord.py` provisions the forum, the 8 tags, the
guidelines box and the posts **from the repo's seed files**, and re-running it syncs drift
instead of duplicating. It does structure only — it can never reply, react, DM, mention
anyone, or post `00-announcement.md` (hardcoded denylist, no flag). Setup walkthrough:
`Lumberjacks/docs/workbench/discord/09-discord-bot-setup.md`.

0. **Tick-box version of everything below:**
   [`tools/workbench/discord/WORKBOOK.md`](tools/workbench/discord/WORKBOOK.md) — also
   carries the paste-ready handoff block for the dashboard agent.
1. ✅ **Done.** Bot `Baseline-helper` created and authorized; token at
   `%USERPROFILE%\.baseline\discord.env`. `whoami` green.
2. ✅ **Done.** Dry run approved and applied — the live plan hash matched the
   pre-approved offline receipt exactly (`6aba648cba55`), so what was read is what
   shipped. Receipt: [`receipts/2026-07-29-plan.md`](tools/workbench/discord/receipts/2026-07-29-plan.md).
   Thread URLs recorded in `tools/workbench/discord/provision-state.json`.
3. ⏳ **STILL OPEN — the four catalog threads.** Seeds 01–04 contain `<ONEPAGER-URL>` /
   `<ACCESS-URL>`; posting them before `/workbench` is live would put literal
   placeholders, or links to a 404, in front of the community, so the bot holds them.
   Right after item 7's deploy:
   ```powershell
   python tools\workbench\discord\workbench_discord.py --site-base-url https://comfy-p7.duckdns.org plan
   ```
   then `apply --yes --expect-plan <hash>`. Preview:
   `receipts/2026-07-29-plan-offline-after-deploy.md`.
4. **Do NOT post `00-announcement.md`** — Batch 2, after the deploy. Now enforced in code.
5. Optional 10 min while you're in settings: load the 7 saved replies from
   `discord/08-saved-replies.md` (or just keep that file open during batch passes).
6. ~~Paste the 6 thread URLs~~ — no longer needed. `apply` records thread ids + URLs in
   `tools/workbench/discord/provision-state.json`.
   ⏳ Agent reads that file, fills `discussion.href` per tool, re-renders, re-checks.

*If you'd rather paste the posts by hand: the manual steps in `07-forum-tags-setup.md`
still work, but a bot can only edit its own messages — hand-pasted posts lose the
diff-and-update pass forever. Let the bot create them.*

## 5. ✅ RESOLVED 2026-07-29 by the visibility flip — the repo is PUBLIC, so the roadmap's `github.com/djcdevelopment/baseline/...` links now resolve for everyone. No action left.

## 6. ✅ RESOLVED 2026-07-30 — retain ComfyStewardView's proprietary license
Canonical decision: [`docs/decisions/pd-1-governance-and-contributions.md`](docs/decisions/pd-1-governance-and-contributions.md).

*FYI, already fixed:* the quest picker's save instructions pointed at the pruned
`comfy-control/` config path while the live mod reads `comfy-network-sense/` — silent
failure for any volunteer. Corrected in the picker + schema doc before the zip build.

## 7. ✅ PUBLIC via the AM4 funnel 2026-07-29 — `https://am4.tail8e749c.ts.net/workbench` (root redirects there). Gallery auth intact at its deep paths (index → /gallery/). Threads + announcement are UNBLOCKED: run item 4 step 3 with `--site-base-url https://am4.tail8e749c.ts.net`. P7/GCP below stays the later step for the game world (UDP can't ride the funnel).
**AM4 is the server/gateway for this stabilization round and every loop is verified**
(page hash-exact, downloads hash-exact + cold-start through the wire, live telemetry via
the kit's poller, nav sweep green, ops surface correctly fail-closed). The P7/GCP deploy
below happens when you take it back to the cloud, lean-and-mean; the threads + announcement
wait for the PUBLIC site either way (AM4 is tailnet-only — its URLs mean nothing to the
community).

**P7 step 0 (when that day comes): the VM is TERMINATED — stopped since 2026-07-25 23:44
PT. You start it** (agent is classifier-blocked from cloud mutations):
```powershell
gcloud compute instances start comfy-lumberjacks-p7 --project=lumberjacks-exp-20260711-djc --zone=us-west1-b
```
Wait for Gateway `/health` + the Valheim log's "Game server connected" (~1 min world
reload). Then: one image cut + promote (adds `/workbench` + `/workbench/downloads/*`
routes; admitted mod release UNCHANGED at m30-rolecontrol), publish `workbench.html` +
zips to the roadmap mount, then the bot posts the four held tool threads
(item 4 step 3). After this, every catalog update is a file copy — no more image builds.
**URL migration (decided 2026-07-29, delegated):** in the same cutover session, re-run
the provisioning bot with the new `--site-base-url` so every bot-created post re-syncs
to the new origin, and hand-edit the human-posted announcement's links — posted links
must never rot.
Rollback = re-pin previous image. **No terraform, no compose changes.** At session end:
stop the VM again or leave it up — your lean-and-mean call, decided with item 9's
password question.
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
- ✅ **`ENDtoEND.txt`** — RESOLVED: untracked with ZERO git history (verified
  `git log --all` empty) — it never reached the public repo. Lives on disk only.
- ◐ **CLA gap vs the ladder** — POSTURE RESOLVED 2026-07-29: PRs open to anyone, you are
  the sole approval gate (CONTRIBUTING.md updated); ladder stage 3 renamed
  Steward→Contributor. **Still open:** pick the legal instrument (CLA text vs DCO) before
  the first substantial external PR lands. Agent can draft either on your word.
- `[!]` **NOW LIVE (the visibility gate fired):** the PUBLIC repo's `infra/gcp/p7/README.md`
  (+ ~7 other docs) advertise the server IP as **Steam-unlisted but password-free** — any
  reader can direct-connect to the world without the invite flow. The IP itself is
  derivable from the public DNS name, so redaction is theater; the real decision is:
  `[ ] set a Valheim server password (invite flow bakes it into the zip)  [x] accept
  open direct-join while the cohort is you+friends`. **RESOLVED 2026-07-29 — accept open
  direct-join, no password.** The cohort is Derek + name-known friends and this round of
  stabilization runs on local hardware, not GCP. Nothing is joinable today regardless: the
  P7 VM is stopped and the local host runs the Gateway only, no Valheim server. The public
  docs describing the server as password-free are accurate as written. The Workbench
  steam-join card now says the invite gates enrollment, not the world. Revisit at the first
  external cohort — the same gate that makes TLS and rate limiting non-optional.
Say **"run the cleanup batch"** for the agent-executable fixes (stale-handoff banners,
era-1 doc banners, ~15 pruned-path link footnotes, register wording fix, START-HERE page,
BUILDING.md, glossary) — no Derek time needed.

## 10. Batch 2 preview (after deploy): post `00-announcement.md`, first reply pass (~30 min).

---
*Generated 2026-07-28/29 during the rollout session. The full plan is at
`~/.claude/plans/i-m-running-out-of-jaunty-cupcake.md`; open decisions also live in
`DECISIONS-PENDING.md`.*
