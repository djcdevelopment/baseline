# Session retro — 2026-07-29 (recoverable-pieces landing)

## One-line
**Paved the path back into the two recoverable tools** — landed the pruned quest-bridge and
camera-gallery raw material in `recipes/` byte-exact with provenance, corrected every stale
pointer the workbench told about them, republished the page hash-verified, synced the Discord
thread on operator approval — and root-caused last session's "HEARTH unreliable" to a parameter,
not the door.

## What this session was
A **strategy-then-execution** session, started from a screenshot of the live workbench's
quest-submission-bridge card with the ask: build a strategy + implementation workbook for
finding the recoverable changes, migrating them into `baseline` (or documenting them in place),
leveraging cheaper models where efficient. Plan mode ran the full ladder — two Explore agents
across the repos, prior-session archaeology, three binding Derek decisions (both tools;
**pave the path** — land unwired, keep QB-1/CG-1 claimable; markdown workbook in `plans/`), a
Plan agent that materially corrected the design — then execution straight down the approved
plan. Session cwd was the retired `C:\work\comfy` checkout; all work landed in `baseline`
(plus two wrap-up commits in comfy itself).

## What shipped

**baseline (all pushed, `main`):**

| Commit | What |
|---|---|
| `53897d5` | `recipes/quest-submission-bridge/` — 15 files byte-exact from `comfy@ae81c83` (= pre-prune `57654fd`), `.gitattributes` byte-pin, PROVENANCE with embedded MIT boundary, notices + recipes/README rows |
| `ef8409a` | `recipes/camera-gallery/` — 9 files, same pattern; camera-proof kit deliberately archive-only |
| `7b1dfc4` | Doc-sync: both one-pagers + workbench.json point at the landed copies; wrong pre-prune ref `cc322ee` → `d75ffb2`/`57654fd`; catalog piece list gains 4 missing real files; HANDOFF dated addendum. Statuses untouched |
| `ae151a0` | `plans/recoverable-pieces-landing-workbook.md` — the find→land→document playbook, every step command · tier · evidence |
| `36706ec` | Verification journaled: 24/24 sha equality, 5/5 compiles, bridge demo end-to-end from the landed copy, camera dry-run, links test, clean tree |
| `8918a00` | Discord sync receipt staged for approval (plan `ba37ecab31d2`, exactly one pending change) |
| `06a557b` | Approved apply journaled: Recoverable pieces thread now points at the landed paths; four tool threads blocked-by-design, untouched |

Off-ledger but load-bearing: the page republished to the am4 funnel — served
`X-Workbench-Sha256` `bdd4a627…` equals the local render byte-for-byte; machine-local
`.private/model-tier-backends.md` maps the workbook's neutral tiers to real rungs.

**comfy (wrap-up):** `8a6754c` terraform default now records the deliberate P7 downsize
(n2-highmem-2, the 2026-07-23 cost call) + provider lockfile; `c1ef56a` gitignore guard for the
third subject-side analysis. **Blocked:** committing the staged `discord-search-export/` v0.2.0
packaging was denied twice by the permission classifier — stopped per its instruction rather
than worked around; left for Derek to commit by hand.

## Timeline
- Exploration fanned out: browser on the live workbench (7 tools, 2 recoverable), Explore
  agents over comfy and baseline/Lumberjacks/commandcenter, prior-session reads. Found the
  topology: baseline is the only working root, the archive is fetchable via baseline's own
  `comfy` remote, and the pruned handoffs tree at `57654fd` is tree-identical to archive HEAD.
- Derek set scope (both tools), posture (pave the path), format (markdown in `plans/`).
- The Plan agent returned four corrections that changed the mechanics: the mikers-demo
  "expected outputs" were never git-tracked and are nondeterministic (smoke + assertions, not
  goldens); the CRLF trap runs opposite the assumed direction (archive blobs are LF; baseline's
  `autocrlf=true` is the hazard); `d75ffb2^` is exactly `57654fd`; `.private/` is
  machine-local-excluded, not repo-ignored.
- Execution: land C1/C2 with the sha proof, doc-sync C3 through render+check, workbook C4,
  verification suite, publish, hash-verify, receipt.
- Derek approved; the apply updated exactly one thread; re-plan confirmed convergence.
- Wrap-up: comfy's pending tree committed in two of three parts; the third hit the classifier.

## The team retro — our collaboration across the seats

**Architect (Claude planned, Derek decided).** The load-bearing design call was *pave the
path*: recover the raw material without consuming the community's claiming tasks — landed
purpose-named under `recipes/` (matching tool ids), C# artifacts pointer-only, statuses and
QB-1/CG-1 untouched. Rejecting the un-prune (option A) kept faith with the deliberate July
prune. *What to change:* nothing structural; the landing-option matrix in the workbook is the
reusable form of this decision.

**Implementer (Claude).** Byte-exactness was enforced, not narrated: `git cat-file blob` from a
pinned ref, `.gitattributes * -text` written before `git add`, and an index-sha == source-sha
loop as the gate. Every phase ended at a commit boundary with the roadmap ceremony (six A7
notes, author "Claude"). *What to change:* run the ceremony's `roadmap:note` before drafting
the commit message — twice the message was written first and then reshaped to match the note.

**Reviewer / QA (Plan agent + frontier).** The design survived because its claims were checked
against the repos before execution: four corrections landed pre-flight, and a fifth
(the CRLF direction) was caught *at* execution by the sha proof — the check that doesn't care
which direction the narrative had it. The workbench honesty invariants then held the doc edits
to "landed, unwired, still not running." *What to change:* keep narrative claims about
byte-level state out of workbooks entirely; state the verifying command instead.

**Operator / SRE (Claude; infra was git, HEARTH, ssh, the funnel).** The session's best find:
last retro's "offload truncation now reaches the pro rung" was a **parameter bug** — passing
`max_tokens` to the Gemini rungs lets thinking consume the cap (~90 tokens out, mid-sentence);
omitting it returns complete documents (16384 default). Two flash drafts then carried the
PROVENANCE prose. Publish ran the gated script against the am4 target and the served hash
matched the render; the HEAD-request 405 was a red herring (gateway answers GET only). *What to
change:* memory updated (`hearth-gemini-max-tokens-truncation`) — treat ~90-token `ok:true`
results as this bug, retry once with the cap omitted, only then fall back.

**Product / Planning (Derek).** The community offer stayed intact end to end: the thread
update tells volunteers the pieces are now one checkout away, and nothing about the ladder,
the claiming tasks, or the statuses moved. The workbook doubles as the template for the next
recovery, which is the actual product of the session. *What to change:* the two remaining
BLOCKED-by-design thread seeds still carry a null `site_base_url` while the live threads carry
real URLs — reconcile provision.json's config with posted reality before the next full sync.

## Two seats, two views

**From Claude's seat.** The satisfying part was closing a loop nobody asked about: the prior
session wrote "HEARTH was unreliable, don't add LLM calls" into a handoff, and today the same
symptom reproduced, got root-caused, and turned into a one-line fix plus a memory — the
2026-07-28 doctrine ("check `tokens_out`, one retry, fall back") was right, it just stopped one
question short of *why*. Where I under-reached: I trusted the design's CRLF narrative long
enough to write it into the plan file; the sha proof would have exposed it either way, but the
workbook should never have carried an unverified direction claim even for a day.

**From Derek's seat (my reconstruction — correct me).** "The workbench told people the pieces
were recoverable; now the repo makes that a five-minute truth instead of an archaeology
project, and nobody's claiming task got done out from under them. The page still says
not-running because it isn't. The receipt-then-approve flow for Discord is exactly the gate I
want on public surfaces. The exporter commit being blocked is mildly annoying but the right
failure mode — it's my call, so it waited for me."

## Last time's lessons — follow-through
| Lesson | Status |
|---|---|
| `L-2026-07-28-1` — end sessions at a commit boundary | **acted-on** (every phase committed; the one uncommitted tree part is an external permission block, surfaced not silent) |
| `L-2026-07-28-2` — a pause is a scheduling fact | **n/a this session** (networking lane untouched behind its pin) |
| `L-2026-07-28-3` — re-verify operational memories against the repo | **acted-on** (Plan agent corrected four design claims pre-flight; prune-ref error on the public card found and fixed) |
| `L-2026-07-28-4` — the journal is the cross-agent handoff | **acted-on** (six A7 notes authored "Claude"; verification evidence journaled, not just chat-reported) |
| `L-2026-07-28-5` — offload truncation reaches the pro rung; check `tokens_out` | **root-caused → superseded** (it was `max_tokens` starving thinking output; omit the cap. New memory `hearth-gemini-max-tokens-truncation`; flash then drafted two PROVENANCE docs clean) |
| `L-2026-07-28-6` — the public side carries other people's data | **acted-on** (landed samples' real builder names documented as already-public in PROVENANCE; no new exposure; root `waypoints.json` fossil untouched) |
| `L-2026-07-28-7` — check name collisions before naming public surfaces | **acted-on** (landing dirs named exactly after the workbench tool ids) |

## Lessons learned
1. **`L-2026-07-29-1` — Prove bytes with shas, never with narrative.** The design's line-ending
   story was backwards (archive blobs are LF; the hazard is baseline's `autocrlf` smudge) and it
   cost nothing, because the gate was `git rev-parse` equality between index and source blob.
   Copy blob-to-blob, pin with `* -text` before `git add`, verify shas. → **practice** (encoded
   in the workbook §7).
2. **`L-2026-07-29-2` — `max_tokens` on thinking-model rungs starves the answer.** A ~90-token
   `ok:true` mid-sentence result is this bug, not a cold backend: the cap is consumed by
   thinking before text emerges. Omit `max_tokens`; the door's 16384 default is the working
   configuration. Yesterday's "HEARTH unreliable" steered a session away from offload entirely
   on this. → **memory** (`hearth-gemini-max-tokens-truncation`).
3. **`L-2026-07-29-3` — Pave the path; don't do the claiming task.** Recovery of pruned work can
   shorten the community's route without consuming their claim: land raw material unwired,
   provenance recorded, statuses honest, tasks untouched. The card, the thread, and the repo now
   all tell the same story at different zoom levels. → **practice** (the workbook is the
   template).
4. **`L-2026-07-29-4` — Never commit nondeterministic goldens.** The demo's on-disk
   "expected outputs" were untracked upstream for a reason (`utc_now()`, absolute paths);
   regenerate-and-assert beats byte-goldens that would rot on first run. → **practice**
   (workbook §4).
5. **`L-2026-07-29-5` — When the harness blocks a user-staged commit, stop and surface it.** The
   auto-mode classifier denied committing the Discord-export packaging twice; the right move was
   to complete the unblocked parts and hand the blocked one back with its exact state, not to
   find a side door. → **practice.**

## Provenance
Git range `e5b0089..06a557b` on baseline (7 commits) + `ae81c83..c1ef56a` on comfy (2), all
lived this session; no reconstruction. Explore ×2 and Plan ×1 subagents did the recon and
design; their four corrections are named in the timeline. Offload per doctrine: two flash
PROVENANCE drafts **succeeded** after the `max_tokens` fix (`tokens_out` 1386/1245,
`routed_by pinned:gcp-gemini`; light frontier edits — dates, HEAD-form verify commands,
notices cross-refs). This retro drafted frontier by doctrine (whole-conversation context).
Discord apply ran only after Derek's explicit "approve", pinned to plan hash `ba37ecab31d2`.
The exporter packaging remains staged-but-uncommitted in comfy behind the classifier block —
Derek's to land.

---

# Addendum — second session (decision lifecycle & delegated governance)

## One-line
**Turned the decision backlog into a governed system** — a review pass found that most
"pending decisions" weren't decisions at all, Derek adopted the lifecycle it implied
(registers are queues, one decision one home, the named First Stranger gate), and then
delegated the six real ones — CLA, disclosure, audit dispositions, AI bar, cadence, URL
migration — which now exist as shipped, rubber-stamped artifacts with one circle-back trigger.

## What this session was
A **review-then-govern** session, no product code. It started as a status pickup ("where are
we at?"), became a decision grid with recommendations, then a meta-review of that grid at
Derek's ask — and the meta-review's structural finding (only 4 of 12 items were true
decisions; the rest were tasks, approvals, and priority rankings wearing decision costumes)
became the session's actual product. Derek endorsed the lifecycle, staged the scope
deliberately (PD-1 + PD-2 only, no hierarchy before need, "one decision, one home"), and
then delegated the six registered future-facing calls with criteria, a rubber stamp, and a
circle-back ("we are a development army of one human and 16 agents").

## What shipped

| Commit | What |
|---|---|
| `22f7f60` | `docs/decisions/` born: README (lifecycle + species table), PD-1 governance, PD-2 First Stranger gate; register realigned (one-liner resolutions, two stale rankings reclassified, duplicate closed, six true decisions registered); AGENTS.md sheds the expired TEMP RULE per its own instruction and states the lifecycle; cost-runbook wording pointed at the named gate |
| `9fe12f1` | The delegated batch decided + shipped: `CLA.md` v1.0 + signature ledger, `SECURITY.md`, `docs/audit/2026-07-29-findings-disposition.md` (every public finding now carries a disposition), AI-contribution bar in CONTRIBUTING + PD-1, reply-cadence posture, cutover URL re-sync step in DEREK-BATCH-1 §7 |
| *(this commit)* | This retro addendum |

Off-ledger but load-bearing: **GitHub private vulnerability reporting enabled** on the repo
via `gh api` (verified `{"enabled":true}`) — a repo-settings mutation recorded here, in
SECURITY.md, and in the register; and the live roadmap page republished twice, served body
sha256-equal to the local render both times.

## The team retro — our collaboration across the seats

**Architect (Claude proposed, Derek shaped).** The load-bearing design came out of the
meta-review: the species split (decision / execution / plan / blocked work, each with its own
home), durable principles over perishable rationales, and one named trigger replacing five
scattered wordings. Derek's shaping was the part that will age best — staging to two PDs
("don't create another documentation hierarchy before the project actually needs it") and
adding "one decision, one home." *What to change:* nothing structural; the promotion rule
gets its first real test when PD-3 earns its way into existence.

**Implementer (Claude).** The register realignment stayed inside its own bounded rule —
touch only lines created or resolved — and both commits ran the full ceremony cleanly. The
delegated batch mapped each call to the stated criteria (license, capacity, near-term goals)
rather than to generic best practice: that's why the CLA is a sentence-plus-ledger instead of
a bot, and why SECURITY.md promises days, not minutes. *What to change:* audit the repo
before registering gaps — CONTRIBUTING already carried a proto-CLA ("use *and relicense*")
and LICENSING.md had already pinned the Change License, so two candidate "missing decisions"
were partly settled before they were filed. One mechanical note: a four-line Edit anchor
failed on an em-dash-adjacent mismatch; the two-line anchor landed — prefer short anchors.

**Reviewer / QA (Claude on Claude, at Derek's ask).** The meta-review was the QA pass, and
turning it on my own grid caught a real overclaim: I'd written "the pin forces the synthetic
fixture" when the pin bans netcode Steam tests, not all play — the fixture could ride any
session that happens anyway. The offload draft then garbled that same correction in the
retelling (inverted its direction), which is exactly why drafts get graded against the
factsheet. *What to change:* the grid's first draft filed tasks as decisions — the very
disease the review then named; classify before recommending, not after.

**Operator / SRE (Claude).** Three small potholes, all now known lanes: `gh api` under Git
Bash rewrites a leading-slash endpoint into a filesystem path (omit the slash — the error
message says so and is right); the AM4 roadmap mount is root-owned so plain `scp` overwrite
is denied (`sudo -n install -m 0644` from /tmp is the lane); the gateway answers GET only, so
liveness is proven by GET-body sha equality, not HEAD. The HEARTH door behaved: one flash
call, `tokens_out` 998, complete document with the `max_tokens` cap omitted — the morning's
root-cause holds. The Skill tool couldn't resolve this very retro skill by either name;
reading `SKILL.md` directly and following it manually was the fallback.

**Product / planning (Derek).** Six future-facing calls closed in one delegated batch, each
with its why on file and a single revisit trigger — the register queue is now genuinely short
(the substrate trio and parked task items). The delegation mode itself is the product
insight: at army-of-one-plus-16-agents scale, the operator's leverage is auditing decisions
in one sitting at the gate, not making each one in real time. *What to change:* nothing yet;
the gate's first firing is the test.

## Two seats, two views

**From Claude's seat.** The most useful thing I did was disagree with myself in public — the
meta-review demoted eight of my own twelve grid items and caught my own overclaim, and that
honesty is what made the delegation trustworthy an hour later. Where the delegated batch
could have gone wrong was fabricating authority: the CLA says in its own text that it's
agent-drafted, operator-ratified, and not yet counsel-reviewed, because a stranger reading it
deserves to know. Where I under-reached: the initial grid leaned on perishable rationales
(dollar figures, vendor precedents) until the review named the pattern.

**From Derek's seat (my reconstruction — correct me).** "The classification rule is the
keeper — that single split will keep the register healthy for years. The PDs are small and
linked, not a new bureaucracy, which is the only way I'd accept them. Delegating the six was
the right use of the 16-agent side: they're all reversible-enough, the why is written down,
and I audit the whole batch once at the gate instead of context-switching six times now. The
CLA admitting it hasn't seen a lawyer is the right kind of honest — it invites the
conversation instead of faking the authority."

## Last time's lessons — follow-through (morning retro, same day)
| Lesson | Status |
|---|---|
| `L-2026-07-29-1` — prove bytes with shas, never narrative | **acted-on** (both republishes verified local = remote = served-body sha) |
| `L-2026-07-29-2` — omit `max_tokens` on thinking rungs | **acted-on** (this retro's offload: cap omitted, 998 tokens, complete; no clip) |
| `L-2026-07-29-3` — pave the path, don't do the claiming task | **n/a** (no recovery work this session) |
| `L-2026-07-29-4` — never commit nondeterministic goldens | **n/a** |
| `L-2026-07-29-5` — when the harness blocks, surface it | **n/a strictly**; nearest analogs handled in its spirit (Skill resolution failure → read the file and said so; the one settings mutation done openly under delegation and reported) |

## Lessons learned
6. **`L-2026-07-29-6` — Classify before you decide.** Of twelve "pending decisions," eight
   were tasks, approvals, or priority rankings. Species first (decision / execution / plan /
   blocked), then homes (register / runbook / handoff / backlog); only decisions queue in the
   register. → **doc** (encoded in `docs/decisions/README.md`).
7. **`L-2026-07-29-7` — Write rationale in principles that outlive their numbers.** "We sell
   licenses, so we must own the tree" beats a vendor-precedent citation; "stopped is the
   default; running is booked" beats a burn figure. Perishable rationales rot into
   re-litigation. → **practice** (the PDs are written this way).
8. **`L-2026-07-29-8` — Name a shared trigger once.** Five docs restated "a real external
   cohort" in five wordings; that's how trigger drift happens. The First Stranger gate is one
   definition, one due-list, referenced by name. → **practice** (PD-2 is the encoding).
9. **`L-2026-07-29-9` — Delegated decisions need three things in the artifact itself:** the
   why against the stated criteria, an explicit rubber-stamp note, and a named circle-back
   trigger — plus provenance honesty (agent-drafted, operator-ratified, counsel-pending)
   where a stranger will read it. → **memory** (`derek-decision-lifecycle`, delegation
   precedent).
10. **`L-2026-07-29-10` — Verify the repo before registering a gap.** Two candidate missing
    decisions were already partly settled in-repo; reading CONTRIBUTING/LICENSING first
    shrank the decision surface, and the same read-first habit caught the pin overclaim.
    → **practice.**

## Provenance
Git range `d8337dc..9fe12f1` (2 commits) plus this retro commit; all lived this session, no
reconstruction. Offload per doctrine: one `gcp-gemini` flash call drafted the timeline,
implementer/operator seat first-passes, and candidate lessons (`tokens_out` 998,
`routed_by pinned:gcp-gemini`, cap omitted per `L-2026-07-29-2`); **edit verdict:
minor-fixes** — it inverted the pin-overclaim correction and imported "ADR pipeline / task
board" vocabulary this repo doesn't use; both fixed against the factsheet. Architect,
Reviewer, Product seats and both views drafted frontier (whole-conversation judgment). No
`--fleet` second opinion dispatched. The `.docx` at repo root belongs to another agent's
in-flight session and was deliberately untouched.
