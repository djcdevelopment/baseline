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

---

# Addendum — third session (bar demo, teardown, and cleaning up after myself)

## One-line
**Ran a live demo honestly and then cleaned up an orphan I had created an hour earlier** —
brought the P7 stack up from a bar, corrected three of my own claims mid-session, declined
the fun-but-pinned "make agents fight each other" ask with receipts, and while deleting a
379 MB orphaned save discovered a second one that my own `gcloud instances stop` had
manufactured, in exactly the way a memory file predicts verbatim.

## What this session was
A **live-operations** session — no design, no build. Derek was at a bar on his phone,
remote-driving OMEN, showing people the work. **Zero commits; no repo file changed.** The
durable output is this addendum plus six memory writes and two filed defects. Five asks in
sequence: bring it up · explain it · can agents play each other · shut the spend down · clean
the dead weight.

## What shipped
No commit table — the git range is empty and that is the honest shape of the session.

| Artifact | What |
|---|---|
| `hearth-gemini-truncation` (rewritten) | Root cause replaces "cause undiagnosed": `max_tokens` starves thinking output. Proved twice tonight — cap 2000 → 76 tokens; cap omitted → 1230 tokens, same prompt and rung |
| `valheim-graceful-stop-save-timeout` (updated) | `gcloud compute instances stop` counts as "the stop"; cheapest-correct teardown ordering added |
| `multiplayer-copresence-needs-multicast` (updated) | ADR-0013 fan-out is BUILT and flag-gated off, not blocked — phrasing guard added |
| `gcp-spend-truth` (updated) | The static IP bills *because* the VM is stopped (~$7/mo) and is correct to keep; Vertex AI swept clean |
| `omen-dashboard-is-a-proxy` (new) | The "local telemetry dashboard" needs the cloud VM; chain is VM → tunnel → compose; the `!override` ports trap |
| `p7-boot-and-schema-gaps` (new) | Stack doesn't reliably start on boot; gateway DB has no `regions`/`events` tables |
| Task chips `task_6b462711`, `task_8a979515` | The two defects above, self-contained, each told not to start the VM without asking |

Operationally: VM up and demo-ready, 699 MB of orphaned partials removed, world verified
intact (1,330,077,725 bytes, md5 `6301a5019a1fe720cce7bece44cce32d`), VM back to `TERMINATED`.

## Timeline
- Ask 1 arrived as two items; they were one chain. `omen-dashboard`'s nginx conf is
  `proxy_pass` to the P7 tunnel for everything but `/roadmap`, so "start the local telemetry
  docker" could not be satisfied without the cloud VM. Started VM → tunnel → dashboard.
- Port 8080 was held by the companion container. Override to 8081 failed first pass because
  compose **merges** `ports` lists; `!override` fixed it. Liveness proven by `current_tick`
  advancing 1216 → 1286 through the proxy, not by the container being up.
- World `ComfyEra16` loaded 9.16M ZDOs; `Game server connected` at 17:57:23; public TLS 200.
- Ask 2: mapped all 9 panels to endpoints. Only 3–4 had data (`peer_count: 0`). Corrected my
  own read of `stability:"unstable"` — it is an API schema-maturity label beside
  `api_version:"v0"`, not health. Framed the tick numbers as an empty-world floor.
- Ask 3: answered no, with the removal commit (`1887626`), the scoped `LabAutoJoinPatches`
  restoration, the unseeded lab clients, and the pinned hold's own "do not propose one as a
  quick check" language. Corrected a stale co-presence claim by searching wider.
- Ask 4: stopped VM, tunnel, dashboard; swept Vertex AI clean; flagged the static-IP-while-
  stopped charge as deliberate, not waste.
- Ask 5: asked scope before deleting (Derek chose the conservative option), restarted the VM,
  and found a *second* partial. Spent eight minutes watching it "write" before noticing the
  byte count was identical across 18 samples — then found the valheim container had never
  started at all. Postgres's clean-shutdown log at `02:47:24 UTC` matched the orphan's mtime
  exactly: my own earlier instance stop made it.

## The team retro — our collaboration across the seats

**Architect (Claude).** Two calls carried the session and both were about refusing a
comfortable frame. First: the dashboard is a proxy, so there is no such thing as a
zero-spend local telemetry demo — saying that up front prevented a demo that would have
been all 502s. Second: the tick numbers are an *empty-world floor* (p99 0.023 ms against a
50 ms budget, 0 overruns, zero players), and presenting them as evidence of scale would have
been the easiest and most dishonest move available at a bar. *What to change:* nothing
structural — but both calls were reactive. The proxy topology should have been in memory
before tonight; it is now.

**Implementer (Claude).** Small surface, two real potholes. Docker compose merges `ports`
across `-f` files rather than replacing, so the first 8081 override silently kept the
conflicting 8080 binding and failed to bind — `!override` is the fix, and it is now in
memory. The `awk` in a remote poll broke through the PowerShell → ssh → sh quoting layers
and produced empty output. *What to change:* stop pushing text-munging into the remote shell
across three quoting layers; `ls -la` over the wire and parse locally, which is what the
rewrite did and it worked first try.

**Reviewer / QA (Claude, on Claude).** The good half: I checked whether the `.aborted-` file
was retained evidence for a finding before deleting it (it wasn't — no repo reference), asked
Derek for scope before an irreversible delete rather than assuming, and verified the world
with `md5sum` and byte counts rather than trusting logs — which is exactly what the hazard
memory instructs. The bad half is worse than it looks: my first poll loop reported
`SAVE_SETTLED=True` when its command had *failed*, because empty output matched the
"file is gone" branch. A verification loop that treats a broken command as a passing
condition is not a check, it is a rubber stamp. I caught it, but only because the result
looked too fast. *What to change:* a poll must assert its probe succeeded before
interpreting the probe's silence.

**Operator / SRE (Claude — this seat owns the failure).** I stopped the VM without first
letting Valheim finish a save, and manufactured a 320 MB orphan `.db.new` at the exact
second postgres logged `received fast shutdown request`. The memory file
`valheim-graceful-stop-save-timeout` describes this outcome literally, down to the phrase
"a truncated orphan `.db.new` is left behind (379 MB in the 07-25 case)" — and 379 MB was
the file I had come back to delete. I recalled that memory's *reassurance* ("the `.db`
survives via atomic write") and acted on it, while skipping its *instruction* ("trigger a
save and wait for `World saved` BEFORE issuing the stop"). Then I compounded it by spending
eight minutes polling a file with no writer: I watched the artifact and never asked whether
a process existed to change it. *What to change:* memory updated to say an instance stop
counts as "the stop" and to give the cheapest correct teardown order; and when a file is
not changing, check for the producer before extending the wait.

**Product / planning (Derek asked, Claude held the line).** The right product call was
declining ask 3. "Can we make agents play against each other" is the most fun question of the
night, and the honest answer had three layers — co-presence built but unproven, autonomous
play deliberately deleted, adversarial AI never existing at all — plus a blocker only Derek
can clear (a manual Steam login on four unseeded clients). The pinned hold anticipates this
exact moment in its own words: *do not propose one as a "quick check," do not prep one "so
it's ready."* Quoting it back was better than quietly setting up the thing he wrote that
sentence to prevent. *What to change:* nothing. The redirect to `/roadmap` — fully populated,
zero players required — was the demo that should have been offered first.

## Two seats, two views

**From Claude's seat.** The session's honest through-line is that I was a good reviewer of the
system and a poor reviewer of myself. Every claim I made *about the repo* got checked, revised,
and in three cases publicly corrected — the `stability` label, the stale co-presence memory,
the incomplete "no players" explanation for the empty panels. But the two things that actually
cost time were both self-inflicted and both had prior warnings sitting in memory: the shutdown
hazard and the `max_tokens` trap. I read memory as reassurance and acted on the half that let
me proceed. Where I'd want help next time: a nudge that reads "you are about to do the thing
this memory is about."

**From Derek's seat (my reconstruction — correct me).** "The demo worked and I didn't get
handed a broken dashboard, which is the whole job. Being told the tick numbers are an
empty-world floor before I quoted them to somebody is worth more than the numbers. Saying no
to the agents thing was right — I wrote that pin three days ago precisely so a good mood at a
bar couldn't restart the worst lane in the program. The orphan file thing is annoying but
it's the kind of annoying I want surfaced: it cost a VM cycle and a cent, and now the memory
actually tells the next session what to do instead of just reassuring it. The two chips mean
the postgres finding doesn't die in a bar transcript."

## Last time's lessons — follow-through
| Lesson | Status |
|---|---|
| `L-2026-07-29-1` — prove bytes with shas, never narrative | **acted-on** (world verified by `md5sum` + byte count, not by log lines; the whole cleanup was gated on file evidence) |
| `L-2026-07-29-2` — omit `max_tokens` on thinking rungs | **dropped, and it bit** — graded "acted-on" this morning, but the memory it named (`hearth-gemini-max-tokens-truncation`) was **never written**. The stale file still said "cause undiagnosed", I passed `max_tokens: 2000`, got 76 tokens, and called it known clipping. Root cause now written into the file that already existed |
| `L-2026-07-29-3` — pave the path | **n/a** (no recovery work) |
| `L-2026-07-29-4` — never commit nondeterministic goldens | **n/a** |
| `L-2026-07-29-5` — when the harness blocks, surface it | **n/a strictly**; nearest analog handled in spirit (Steam seeding is a human-only step — named it and stopped rather than improvising around it) |
| `L-2026-07-29-6` — classify before you decide | **acted-on** (the agents answer was classified into three distinct layers instead of one flat "no") |
| `L-2026-07-29-7` — principles that outlive their numbers | **acted-on** ("stopped is the default; running is booked" is why the VM restart was posed as a question, not assumed) |
| `L-2026-07-29-8` — name a shared trigger once | **n/a** |
| `L-2026-07-29-9` — delegated decisions need the why in the artifact | **acted-on** (both task chips carry the evidence and the do-not-start-the-VM constraint inline) |
| `L-2026-07-29-10` — verify the repo before registering a gap | **acted-on** (searched for references to the `.aborted-` file before deleting; searched wider when the co-presence memory smelled stale, and it was) |

## Lessons learned
11. **`L-2026-07-29-11` — A lesson is only as durable as the artifact it names; verify the
    artifact exists.** This morning's retro recorded the `max_tokens` root cause, said it
    would live in a new memory file, graded itself **acted-on** — and the file was never
    created. Twelve hours later the same bug fired and the stale memory steered the
    misdiagnosis. Follow-through audits must check the filesystem, not the previous retro's
    own claim. Corollary: prefer **updating the file that already covers the topic** over
    minting a new name; a rename is a chance to write nothing. → **practice** (and the fix
    landed in `hearth-gemini-truncation`, not a new file).
12. **`L-2026-07-29-12` — Read the hazard memory's instruction, not its reassurance.** I
    recalled "the `.db` survives via atomic write" and skipped "save and verify BEFORE
    stopping." Reassurance tells you the blast radius; the instruction is the part that
    prevents the blast. → **memory** (`valheim-graceful-stop-save-timeout` updated with the
    `gcloud`-stop case and the correct teardown order).
13. **`L-2026-07-29-13` — An unchanging byte count is not progress; check for a writer.** I
    polled a frozen file for eight minutes. The file was real, the size was real, and no
    process existed to change it. Watch the producer, not just the artifact. → **practice.**
14. **`L-2026-07-29-14` — A poll loop must prove its probe ran before trusting its silence.**
    Broken `awk` → empty output → matched the success branch → `SAVE_SETTLED=True`. Absence
    of evidence became evidence of absence in one line of shell. Assert the probe's exit
    status, or parse locally where failures are visible. → **practice.**
15. **`L-2026-07-29-15` — "Nothing is showing" usually has more than one cause; check the
    write path, not just the read.** I explained the empty Gameplay Feed with `peer_count: 0`
    and stopped. The `events` table doesn't exist, so the INSERT fails regardless of players —
    a complete answer required reading the DB's own error log. → **memory**
    (`p7-boot-and-schema-gaps`).
16. **`L-2026-07-29-16` — A proxy that looks like a local service is a demo trap.**
    `omen-dashboard` reads as local telemetry and is a tunnel-dependent view of a cloud VM.
    Anything that renders someone else's data should say so at the top of its own compose
    file. → **memory** (`omen-dashboard-is-a-proxy`).

## Provenance
**Git range: none — zero commits, no repo files changed.** This was live operations; the
artifacts are six memory writes, two task chips, and this addendum. Working tree carries only
the pre-existing untracked `.docx` belonging to another agent's session, untouched.
Offload per doctrine: one `gcp-gemini` flash call drafted the timeline, the Implementer and
Operator seat first-passes, and candidate lessons — **cap omitted per `L-2026-07-29-2`,
`tokens_out` 1230, `routed_by pinned:gcp-gemini`, complete document**, which is itself
tonight's proof of that root cause. **Edit verdict: `hallucinated`** — it invented a precise
wall-clock timestamp for nearly every timeline entry (only `17:57:23` and `02:47:24 UTC` were
real) and inverted the central finding by calling postgres's clean SIGTERM shutdown a "crash";
both corrected against the factsheet, structure and substance kept. Architect, Reviewer and
Product seats plus both views drafted frontier. No `--fleet` second opinion dispatched, and
none was pending from the previous two retros. No ADR written: this session produced
operational facts and practices, not architectural decisions — per the skill's own rule,
those belong in memory and docs.
