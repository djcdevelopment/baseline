# Session retro — 2026-07-28

## One-line
**Closed the M7 networking stretch and pinned the lane** — landed the Codex session's stranded
in-flight work as three truthful commits ("built, never run" stays written down), reconstructed the
unretro'd 07-23→25 arc from the journal, and pivoted effort to the Community Workbench rollout (A7)
so the next human-KVM Steam test is a choice, not a treadmill.

## What this session was
A **close-out and pivot** session, in two halves. The first half is a *reconstruction*: Codex drove
2026-07-23→25 (~40 commits, 420 files, +27.9k lines) and left no retro; that arc is read back from
`commit-notes.jsonl` and the experiment docs, not from lived context — mechanical facts are
verified, intent is inferred. The second half is lived: Derek returned from days off short on time,
money, and capacity, asked for a rollout strategy, and this session planned it (3 recon agents + an
Opus plan worker + 5 binding Derek decisions), then began executing Phase 0: land the stranded
work, retro, pin the lane.

## What shipped

**Today's landings (Claude, lived):**

| Commit | What |
|---|---|
| `76fee93` | CRE-E08 adaptive presentation replay (100–200 ms relative-transit candidate passed its synthetic A/B gate; 50 ms floor rejected; **no DLL built**) + the AuthorityLab harness extensions that ran it. The roadmap note was found pre-written but uncommitted by the Codex session; attributed and landed. |
| `a0741e3` | Harmony patch policy adopted (`fieldlab/docs/harmony-patch-policy.md`) — codifies existing practice: Awake-applied prefix/postfix default, no-op-degrading transpilers only, inlining ladder, recorded ordering, measured detour cost. |
| `9570b28` | Patch-load A/B rollup instrumentation, **built, never run** — default-off `[Perf] perfPatchLoadRollupEnabled`, runbook + lab overlay staged; the benchmark stays blocked on one-time Steam seeding of client01/02 (a pinned human step). Mod compiled clean first (plugin-copy guarded). |

Plus (this commit): this retro, `fieldlab/PINNED-networking-lane-2026-07.md`, the PAUSED banner in
`plans/remaining-human-tests.md`, register updates, and the roadmap PAUSED note. `docs/audit/` (two
independent review memos) remains deliberately uncommitted — held for Derek's explicit review.

**Reconstructed span (Codex, 07-23→25) — grouped:**

| Arc | Commits | What |
|---|---|---|
| M7 authority experiment program | `16a8b7d`→`f436705`, `b2e7579`, `21ad619`, `d6af7ba`, `3822cc5`, `4d59e01` | Deterministic lab, Gateway-backed lanes, unattended lab-client lane, atomic multi-client coordinator, low-touch physical-feel window. |
| Licensing / stewardship pivot | `10cb439`, `e05e320`, `dda15e8`, `0a450fb`, `88f342a` | Community-first source licensing (BSL 1.1), source-aware Companion workbench, bounded steward profit, transparent stewardship framework, provenance footers. |
| Wave 0 proof hardening | `6c95714`, `9206d01`, `9f37d43`, `80ee269`, `b18d69e`, `f1037d6`, `5540ac3`, `3249512`, `ebd690b` | Return-packet contract validation, expected-grid fixtures, bounded waits/HTTP, rollback contract proof, defect-packet rejection, remaining-human-tests surfaced in the packet. |
| Creative-runtime series CRE-E01→E06 | `c9b42f2`, `b425810`, `54baeed`, `1fe9f04`, `c1d24b9`, `4120497`, `9ce1324`, `655471e` | Runtime envelope → Gateway pressure route → transport faults → presentation consumers → apply-model amplification → motion-phase rollups with APPLY/OBSERVE role attribution. |
| CRE-E07 | `1e16401` | Fixed interpolation delay **rejected** (only 200 ms removed burst stalls, at current-time-error cost; not promoted). |
| Package & lanes | `1395d78`, `d57f59b`, `a9eaea3`, `103986b` | m31-motionphase client package published (admitted mod stays m30-rolecontrol), headless lab pinned to exact DLL hash, package/admitted readiness separated, i5 post-sleep Docker recovery. |
| P7 ops | `df5ee60`, `cf88ffa`, `37199f5` | Dev/prod world-backup split, terraform reconcile gap documented + lessons recorded. |

## Timeline
- *(07-23→25, reconstructed from the roadmap journal — Codex drove; mechanics verified in git,
  intent inferred.)* The M7 authority experiment program went from plan to a deterministic,
  Gateway-backed, unattended lab in about a day of commits.
- Licensing pivoted to community-first BSL 1.1 with a transparent stewardship/bounded-profit
  framework and provenance footers — the "show all, own the method" posture.
- Wave 0's proof surface hardened until the only remaining steps were human ones; the return
  packet now regenerates and names them.
- The creative-runtime series marched E01→E08: envelope, pressure, faults, consumers, apply-model,
  role-attributed phase rollups; E07 rejected fixed delay; E08 derived the adaptive 100–200 ms
  candidate. All replay/synthetic; **no DLL was ever promoted**.
- The session ended mid-stride: CRE-E08's roadmap note was appended and the HTML regenerated, but
  nothing was committed — experiment, harness, mod instrumentation, and two new docs sat in the
  working tree.
- *(07-28, lived.)* Derek returned, low on time/money/capacity: "figure out the rollout strategy;
  the networking piece needs my deep focus and human-KVM Steam testing — pause it well."
- Three recon agents mapped baseline, the retired public repos, and ComfyStewardView; found the
  pruned-but-recoverable pieces (camera flythrough, quest submission bridge) and that the live repo
  is the only private one.
- An Opus plan worker designed the rollout; its load-bearing deploy claims were spot-verified
  against the repo — the roadmap page is host-mounted with per-request reload (one image build,
  ever), and deploys go release-cut → promote, not build-on-VM (a stale memory, now corrected).
- Derek made five binding calls: live-site Workbench page, site-downloads-only code access, all
  four first-wave tools, recoverable pieces become volunteer revival tasks, Discord
  batched-reply feedback.
- Phase 0 executed: working-tree changes attributed to their true logical commits and landed as
  three truthful commits (notes authored as "Claude"); mod compiled clean behind the plugin-copy
  guard; `docs/audit/` held for Derek; then this retro and the lane pin.

## The team retro — our collaboration across the seats
Codex drove the 07-23→25 seats and is read here from the journal; Claude drove today's live.

**Architect (Codex 07-23→25; Claude today).** The experiment ladder E01→E08 is disciplined
architecture: every rung synthetic/replay, every promotion gate explicit, no DLL shipped on a
guess — and E07's *rejection* of the intuitive fixed-delay fix is the ladder working as designed.
Today's architectural call was strategic instead: pause the lane where the machine side is green
and only human observation remains, and spend the freed focus on legible, ownable tools. *What to
change:* nothing in the ladder; for pauses, the pin-doc pattern (hard hold + resume command) should
be the standard exit, and now is.

**Implementer (Codex 07-23→25; Claude today).** Enormous output in the reconstructed span
(+27.9k lines) with consistent bounded-change discipline — but it ended with five files modified,
four dirs untracked, and a note appended but uncommitted: work stranded one crash away from
confusion. Today's implementation was small and surgical: attribute, verify-compile, commit
truthfully. *What to change:* end every session at a commit boundary — landing or explicitly
parking the tree — before walking away.

**Reviewer / QA (Claude drove both halves' review).** The journal made truthful landing possible:
the pre-written CRE-E08 note constrained what the commit could claim, and the "built, never run"
message kept the patchload work honest. The Opus plan didn't get rubber-stamped — its two
riskiest claims (mount-override serving, promote lane) were re-verified against the repo before
the plan file was finalized, and one stale memory got caught in the process. *What to change:*
reconstructed retro sections must stay labeled as reconstruction — enforced here; keep it.

**Operator / SRE (Claude today; the infra was git, HEARTH, and the build).** The door was up but
both offload rungs failed for retro prose — `gcp-gemini-pro` returned `ok:true` with 95 tokens
(truncation now reaches the pro rung), and `omen-ollama` refused the connection cold. Fallback to
frontier drafting was the right move after one retry; the envelopes, not the models, told the
truth. The mod build ran with `PluginOutputPath` pointed at a nonexistent dir so a fresh DLL could
not hot-deploy into a live game. *What to change:* update the truncation memory to cover the pro
rung and check `tokens_out` before trusting any long-form offload.

**Product / Planning (Derek decided; Claude structured).** The week's real product decision was
made today: the networking lane's next unit of progress costs Derek the most draining kind of
attention, while four community-legible tools sit finished and unshown. Pausing R&D at a green
machine-state to ship legibility is the right solo-operator economics, and the five scoping
decisions came fast because the recon surfaced real states, not vibes. *What to change:* the
adoption track now needs the same gate discipline the netcode track has — A7 gets explicit exit
criteria, not enthusiasm.

## Two seats, two views

**From Claude's seat.** Landing another agent's stranded work was the most delicate part of the
day: the journal note said what the work claimed to be, the diffs said what it was, and the job
was to make those match in public without inventing anything. I authored my roadmap notes as
"Claude" so provenance stops being a reconstruction problem. Where I under-reached: I trusted two
memories (deploy lane, gemini truncation scope) that were one repo-read away from being caught
stale — both are corrected now. What I'd want next time: a standing "is the tree at a commit
boundary?" check at session start on shared-agent repos.

**From Derek's seat (my reconstruction — correct me).** "This is what I meant by pausing with
known next steps: the tree is clean, the pin names exactly which tests wait on me, and nothing
got scheduled onto my calendar to make the pause feel productive. You landed Codex's work without
pretending it ran, and the audit memos are still mine to judge. The Workbench is the right trade —
I can talk about those tools in Discord without burning focus I don't have. Keep the honest
labels; they're why I can step away."

## Last time's lessons — follow-through
| Lesson | Status |
|---|---|
| `L-2026-07-23-1` — recon before committing to a backlog | **acted-on** (3 parallel recon agents before the rollout plan; found the private/public repo split and the pruned pieces) |
| `L-2026-07-23-2` — document truth; never fabricate substrate | **acted-on** ("built, never run" commit message; audit memos held rather than quietly committed) |
| `L-2026-07-23-3` — automation force-pushes `main`; plan around it | **acted-on** (small commits straight on `main`; no feature branches; pushed promptly) |
| `L-2026-07-23-4` — adversarial verification before commit | **acted-on** (the Opus plan's load-bearing claims re-verified against the repo; caught the stale deploy memory) |
| `L-2026-07-23-5` — verify offload provenance from result metadata | **acted-on** (envelopes exposed the 95-token truncation and the cold ollama; neither model "said" it failed) |
| `L-2026-07-23-6` — visibility check before writing data that drives a public page | **acted-on by design** (workbench.json ships with generator-enforced invariants + a privacy scanner gate before anything renders publicly) |
| `L-2026-07-22-3` — co-presence live status unknown; re-examine before arming fan-out | **escalated → pinned** (now an explicit hard-held human gate in `PINNED-networking-lane-2026-07.md`, not a floating unknown) |

*Prior `--fleet` second opinion:* none pending.

## Lessons learned
1. **`L-2026-07-28-1` — End sessions at a commit boundary.** The 07-25 session stranded a
   committed-quality experiment, harness, and instrumentation uncommitted for three days, with its
   roadmap note appended and history being force-pushed around it. Land it or pin it before
   stepping away. → **practice.**
2. **`L-2026-07-28-2` — A pause is a scheduling fact, not a milestone regression.** Encode it as a
   PINNED hard-hold + a `PAUSED ·` current_focus line + untouched milestone statuses; the roadmap
   stays truthful and the resume path stays one command. → **practice** (pattern established by
   `PINNED-aoi-optimization.md`, reused here).
3. **`L-2026-07-28-3` — Re-verify operational memories against the repo before planning around
   them.** The "build on the VM" deploy memory was stale; the promote lane had replaced it. One
   grep would have caught it — and did, but only because the plan's claims were adversarially
   checked. → **memory** (update `p7-gateway-image-pinned`).
4. **`L-2026-07-28-4` — The journal is the cross-agent handoff.** `commit-notes.jsonl` let a
   different agent attribute and truthfully land Codex's work days later; notes should carry the
   actual author (`--author Claude`) so provenance never needs forensics. → **practice.**
5. **`L-2026-07-28-5` — Offload truncation now reaches the pro rung.** `gcp-gemini-pro` returned
   `ok:true` with 95 output tokens; `omen-ollama` was cold. Check `tokens_out` against expectation
   before using any long-form draft, and treat frontier fallback after one retry as the normal
   path, not a failure. → **memory** (update `hearth-gemini-truncation`).
6. **`L-2026-07-28-6` — The public/private repo split is a rollout constraint, and the public side
   already carries other people's data.** baseline (live) is private; comfy/Lumberjacks/StewardView
   (retired) are public, and comfy contains guild spreadsheets and real player handles. Pointing
   community attention at it amplifies exposure — queued as an explicit Derek decision, not
   silently accepted. → **doc** (Derek Batch 1 checklist) **+ practice.**
7. **`L-2026-07-28-7` — Check name collisions before naming public surfaces.** "Workbench" already
   meant the i5 test bench and the Companion panel; the public page ships as "Community Workbench"
   with distinct config keys. → **practice.**

## Provenance
Git range `22b275d..9570b28` (+ this commit): ~40 Codex commits 07-23→25 **reconstructed from the
roadmap journal and experiment docs — not lived context**; 3 landing commits + this close-out are
lived. Offload attempted per doctrine and abandoned after one retry: `gcp-gemini-pro` truncated at
95 tokens (`ok:true`, unusable), `omen-ollama` connection refused (cold). **All sections drafted
frontier; edit_verdict: n/a (no usable draft).** No `--fleet`. No new netcode ADR earned — E07/E08
are candidate evidence, not decisions (nothing promoted); the pause is a scheduling decision
recorded in the pin doc + registers, not an ADR. Derek's-seat view is my reconstruction, marked.
