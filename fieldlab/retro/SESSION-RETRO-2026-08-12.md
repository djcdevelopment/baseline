# Session retro — 2026-08-12 (monorepo → five sovereign repos)

## One-line

**A proven monorepo was cut into five sovereign repos without losing a test, a
commit, or an honest label** — every seam was severed and verified *inside* the
monorepo first, and the phases that ran on borrowed capacity were driven from a
prompt pack and a state ledger committed into the repo itself.

## What this session was

A build session that started as an audit. The opening ask was small: confirm
2–3 days of Quest Lab / Studio / Runtime work was committed. The audit found the
work already landed and the *bookkeeping* lying about it, which cleared the way
for the real ask — isolate the verticals now that the functionality is proven,
and leave behind a place to ask architecture questions instead of scanning every
repo.

Then it became three sessions in one: plan and de-risk (frontier), execute
(external service, after weekly capacity ran low), validate (frontier again).

## What shipped

| Commit | What |
|---|---|
| `49b70861` | Correct the sovereign guide against the tree; open `docs/PORTS.md` |
| `9541b78f` | Retarget cross-seam scripts behind behavior-preserving parameters |
| `5077fd75` | Cut the shared-contract seams: two source packages, consumers retargeted |
| `70982ebc` | Split the fused test project along the quest seam (166 + 185 = 351) |
| `9928743e` | Carve Quest Studio out of Game.Companion behind `IQuestStudioHost` |
| `aceb2eb4` | Journal the Phase 1 landing round → tag `split-base-20260811` |
| `d10deb69`…`b637eb7c` | External execution: three extractions, isolate reconciliation, hub slimming, verification matrix |
| `36a0d25` (platform) | Redact the operator SteamID and the lab endpoint before public reading |

26 commits on baseline; 1,529 files changed; 336,980 deletions (the slim).

Durable artifacts: five live repos (`networksense`, `lumberjacks-platform`,
`comfy-quest`, `sovereign-shards`, plus reconciled `isolate`), `REPO-MAP.md`,
`docs/PORTS.md`, [PD-9](../../docs/decisions/pd-9-repository-split.md),
`docs/internal/repo-split/` (plan of record, manifest, prompt pack, recovery
handoff, six execution reports).

## The evidence

CI green at pinned revisions, re-read from the GitHub API rather than taken from
agent reports: networksense `8d9ced61` (166/166), lumberjacks-platform `d5128c03`
(649/649), comfy-quest `a7043648` (185 C# + 199 Python), sovereign-shards
`4ad00beb`, isolate `600e2d88` (25/25), baseline hub + Pages `39262cee`.

Baseline history intact — 1,176 commits, `pre-split-20260811` reachable, moved
source still recoverable from the tag, so the archive premise that made
aggressive removal safe actually holds. Gitleaks 8.30.1 clean over full filtered
history in all three extractions. Guards demonstrated failing, not just passing.

## The team retro

**Architect.** Two calls carried the session. "Decouple in place" — sever every
cross-seam coupling and prove it green while still in one repo — meant extraction
was a mechanical move of already-working code rather than a rewrite under time
pressure. And choosing NuGet *source* packages over vendored copies preserved the
single-DLL BepInEx doctrine that the csproj comments had been protecting all
along. What to change: the design guide that framed the split had five claims
false against the tree. Reading the code before ratifying the document caught it,
but only because someone thought to check; a document becoming a plan of record
should have that check as a step, not as a habit.

**Implementer.** The mechanical surgery held: contracts moved, consumers
retargeted, a fused 351-test project split with count conservation, ten Studio
routes carved out behind a four-member adapter with route-for-route parity. The
cost was coordination, not code — two agents in one checkout collided (below).
What to change: give concurrent agents disjoint file sets *and* isolated
worktrees, not just disjoint instructions.

**Reviewer / QA.** The byte-identity gate earned its place by *failing*: the mod
DLL hashes changed after the contract move, and the answer came from decompiling
both assemblies in an isolated worktree (162/162 and 92/92 files identical) and
pinning the residual diff to embedded PDB source-document identity. A gate that
merely passed would have taught nothing. Validation of external work was done by
re-reading CI conclusions from the API and running a guard's negative fixtures
locally, not by trusting six well-written reports. What to change: the
pre-publication scan should have been written into the plan at Phase 0, not
improvised at the moment of flipping repos public.

**Operator / SRE.** The capacity handoff was a non-event because the recovery
ledger was already in the repo — state, exact commits, recovery procedure,
hazards already paid for. Retiring the stale checkout roots to `_retired/` before
any surgery removed the repo's single most-repeated historical failure (paths that
resolve against dead code and succeed quietly). What to change: `BUILDING.md` had
warned for weeks about background automation force-pushing this repo; the GitHub
activity API says it never happened once. Planning caution was being paid to a
ghost.

**Product / planning.** The scope pivot mid-session — audit → full split — was
absorbed without thrash because the audit's finding (everything already landed)
was the precondition for the split anyway. The most valuable product decision was
the least technical: keeping baseline as a *live index* rather than a frozen
archive, so public links, Pages, and the corpus survived, and the per-commit
journal ceremony now exists in exactly one repo instead of five. What to change:
publication readiness (NuGet identifiers, API keys) should have been requested at
Phase 0; it is now the only thing standing between "extracted" and "consumable."

## Two seats, two views

**From Claude's seat.** The habit that paid was refusing to accept a green I
had not seen produced: re-reading CI from the API, running the boundary guard's
bad fixtures myself, checking that the pre-split tag still resolved moved source.
The habit that nearly cost was parallelism without isolation — I gave two agents
disjoint *instructions* and assumed that made them disjoint *processes*, and one
`git stash -u` proved otherwise. I under-reached once: I described the
publication gate as "the gitleaks scrub is clean" when the scrub only covered
credentials, and a broader scan found a SteamID and a lab endpoint minutes later.
The correction was cheap because it happened before the flip, but the calibration
error was mine — I named a narrower gate than the decision needed.

**From Derek's seat** *(my reconstruction, to be corrected).* The split is not
about tidiness; it is about not paying a documentation tax to move fast in one
vertical. What matters is that work in networksense or comfy-quest no longer
triggers a ceremony that exists for the platform's public roadmap. The validation
work is worth its tokens only because the alternative — discovering a lost test
or a leaked identifier weeks later — costs a whole session. And the repos going
public is the point: forking is the highest compliment, and a private repo cannot
be forked.

## Last time's lessons (2026-08-10)

| Lesson | Status |
|---|---|
| L1 — use the product's authority topology for acceptance | pending (no gameplay acceptance this session) |
| L2 — certification must hash every runtime dependency | **acted-on** — the mod and quest release lanes hash the whole asset set (manifest + per-file SHA-256), and guard G6 rejects a one-byte mutation |
| L3 — read both game logs | not applicable this session |
| L4 — human-visible and machine evidence cross-check each other | **acted-on** — CI conclusions re-read from the API; the DLL hash diff cross-checked against decompiled IL |
| L5 — one machine, one objective, one expected result | **acted-on** — the external prompt pack is exactly that shape: one prompt, one repo, named gates, a committed report |

## Lessons

1. **Cut the seams before you cut the repo.** Every coupling severed and proven
   green inside the monorepo turns extraction into a file move. The phase that
   feels like delay is the phase that removes the risk.
2. **A gate earns its keep the day it fails.** The byte-identity check "failed"
   and forced a decompile that proved IL-identity — which is the evidence a
   passing check never would have produced. Design gates to fail informatively,
   and diagnose rather than wave through.
3. **Concurrent agents need isolated worktrees, not just disjoint instructions.**
   Shared-checkout parallelism fails silently: one agent's clean-tree operation
   is another agent's data loss. Stage after every edit, commit with explicit
   pathspecs, and prefer physical isolation when the work is not read-only.
4. **Name the gate you actually ran.** "The scan is clean" is only true of the
   scan you performed; a credential scanner does not look for identifiers or
   endpoints. Before an irreversible action, state which checks ran and which
   did not.
5. **Verify a document against the tree before it becomes the plan of record.**
   Five claims in the founding guide were false against the code. A design doc
   inherits authority the moment it is cited; check it at that moment.
6. **Stale warnings cost real caution.** A documented "background force-pusher"
   that the platform API says never existed shaped weeks of planning. Warnings
   deserve expiry dates and verification, same as claims.
7. **A handoff committed into the repo makes capacity a scheduling detail.** State
   ledger, recovery procedure, and paid-for hazards in a tracked file let any
   agent on any service resume from facts instead of reconstruction.
8. **When repos go public, redact at the last private moment.** Exposure may be
   unchanged (the origin was already public), but freshly rewritten history that
   nobody has forked is the cheapest it will ever be to fix. Apply the existing
   line: provenance attribution is fine; endpoints, credentials, and operator
   paths are not.

## What went wrong

- **Worktree wipe.** A subagent ran `git stash -u` in the shared checkout for a
  clean baseline hash capture, silently reverting a concurrent agent's edits and
  `git mv` renames. Caught within a turn; it restored only its own paths and the
  other agent redid and staged its work. *Fix adopted mid-session:* stage
  immediately after every edit; orchestrator commits promptly with pathspecs.
- **Gate described too narrowly.** The public-flip gate was stated as the
  credential scrub; a broader pre-publication scan then found a real SteamID64
  and a published lab endpoint. *Fix:* scan, then flip, then redact at the
  cheapest moment — and say which scan ran.
- **Guide falsehoods.** Non-existent keybinding, contradicted buff percentage,
  port collision with a live service, a dependency hook never built, a missing
  diagram. *Fix:* corrected and labeled per PD-4 before the guide founded a repo.
- **Ghost automation.** `BUILDING.md`'s force-push warning is unsupported by the
  activity API. *Fix:* recorded in the ledger; the doc still needs correcting.
- **Tooling friction.** A permission classifier blocked an agent brief bundling
  clone-outside-worktree with push (*fix:* run those from the main loop); a
  PowerShell here-string was mangled by apostrophes in a commit message (*fix:*
  message file, as the repo's own protocol already recommends).
- **`git cherry` misreports rewritten landings.** Nine branches read as unlanded
  because the landing rounds rewrote their patches. *Fix:* hunk-level audit
  against `main` before believing any "unmerged" signal here.

## Remaining frontier

- **Publication.** NuGet identifiers and an API key for the two publishing repos;
  until then packages resolve from vendored local feeds and the fleet has zero
  releases.
- **Published-lane proofs.** I1 (mod artifact → P7 hash gate) and I3 (quest
  artifacts → platform vendor) are verified against local candidates but need a
  real release; I2 needs the operator's OMEN client (runbook written); I5 needs a
  published DLL plus authority to boot the live lab.
- **Sovereign-shards is still empty by design.** First build item is the
  `OnEquipmentChange` hook in ComfyQuestRuntime that the armory sidecar depends
  on, and it lives in another repo.

## Provenance

Git range `pre-split-20260811..HEAD` (26 commits) plus `lumberjacks-platform@36a0d25`.
Phases 0–1 and all validation ran frontier; phases 2–5 ran on an external agent
service from `docs/internal/repo-split/EXTERNAL-AGENT-PROMPTS.md`; mechanical
surgery ran on Sonnet subagents. Role reads, lessons, and the failure list were
drafted by `gcp-gemini` via HEARTH and edited here — `edit_verdict: minor-fixes`
(the draft overstated the redaction as new exposure and placed it in the history
rewrite, where it was in fact ordinary commits after publication). No `--fleet`
second opinion was dispatched.
