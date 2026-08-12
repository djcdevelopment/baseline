# Session Retro — 2026-07-21 · Baseline cutover step 6: the VM finally comes from the repo

**One-line:** We **closed the cutover's last open criterion** — re-provisioning the live P7 VM from
`baseline`, proving all five services resolve from digest pins across a real reboot, and world-testing
it clean — after discovering the VM had been deploying from a *retired* repo the whole time; then
pruned a quarter of the monorepo behind a Gemini-backed audit.

## What this session was

A **build-then-prove-then-curate** session, and the first ever run in `C:\work\baseline` — a fresh
memory/project scope with nothing carried over. It opened narrowly ("what's next for me to test?")
and widened three times, each time because Derek gave explicit latitude: first to fix the release
pipeline, then to deploy it for real against paid infrastructure, then to audit and prune the repo.

The through-line is that **every widening was justified by evidence found in the previous step**, not
by ambition. The drill fix came from reading the drill. The re-provision scope came from probing the
VM. The prune came from the repo's own shape once the live surface was finally known.

## What shipped

| Commit | What |
|---|---|
| `807769a` | Promotion drill transports **all four** gated OCI images, not just the gateway. Fixed `roadmap.mjs checkStaged()` under the monorepo layout. Dropped 4 drifted duplicate skill files. |
| `ecbd6e3` | Corrected a runbook claim of my own — the three sibling services *do* serve `/health` (live probe: 200 on 4002/4003/4004). |
| `129cf66` | Re-provisioned `comfy-lumberjacks-p7` from `baseline`; all five services gated by digest. |
| `5c77c6f` | Live world-test acceptance: all eight README §9 criteria passed. |
| `57654fd` | Root-caused the recurring telemetry `409`; deferred the fix to the next release cut. |
| `d75ffb2` | Pruned 279 of 1045 tracked files after a Gemini-backed multi-agent audit. |

299 files changed, 2,002 insertions, 67,714 deletions.

New durable artifacts:
- `Lumberjacks/docs/roadmap/m5-recipients-build-candidate-v3.json` — the v3 release manifest, with an
  `artifact_provenance` block recording honestly that two of its five artifacts predate the commit it
  pins.
- `Lumberjacks/docs/roadmap/m5-v3-reprovision-receipt.json` — what changed on the VM, and the rollback path.
- `Lumberjacks/docs/roadmap/m5-v3-acceptance-receipt.json` — the acceptance sample plus, deliberately,
  what it does **not** cover.
- `Lumberjacks/docs/roadmap/prune-audit-20260721.json` — the reason for all 268 primary deletions.
  The files go; the rationale doesn't.
- ADRs [0005](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/adr/0005-carry-forward-unreproducible-artifacts.md),
  [0006](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/adr/0006-git-bundle-transport-no-vm-credentials.md),
  [0007](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/adr/0007-prune-audit-signal-discipline.md).
- Memory: `baseline-unified-repo`, `streamline-over-two-repo-ceremony`,
  `powershell-utf8-roundtrip-corrupts-files`, `p7-deployment-topology`, `valheim-world-reload-delay`.

## The team retro — our collaboration across the seats

Two seats filled as usual: **Claude** held the whole picture, did the instrumenting and every repo
write; **Derek** paced, made the infrastructure calls, and supplied the one thing no automation can —
a real player in a real world.

**Architect (Claude drove; Derek decided the topology).** The strongest call was refusing to rebuild
the mod. The .NET 8 SDK embeds the git HEAD sha in the portable PDB, so identical source yields a
different DLL hash on every commit; rebuilding would have produced a binary that was *not* the one
world-tested. Carrying the original forward and writing the gap into the manifest keeps the release
honest at the cost of admitting it isn't reproducible → ADR 0005. The second call was Derek's, and I
surfaced it rather than assuming it: three genuinely different ways to move the VM's deployment source
onto `baseline`, with the trade-offs stated. What to change: I proposed "batch one / batch two" scoping
early and it held all session — but I should have surfaced the `/opt/comfy` question *before* the VM
was started, not after. The probe that found it could have run against a stopped instance's metadata.

**Implementer (Claude drove).** The drill fix was small and correct — a loop where a hardcoded
`gateway` had been — and the sibling-override design has a real reason to exist (release pins and
rollback pins have different lifetimes). The 24 MB incremental bundle was the session's most elegant
move: no credentials on the box, real commits, real history, only because `8ca27eda` turned out to be
a genuine ancestor 232 commits back. What to change: **three separate silent-failure bugs were mine
and all were encoding or path handling** — a PowerShell `Get-Content`/`Set-Content` round-trip that
mojibake'd 9 em-dashes invisibly to `--stat`; a Python text-mode write whose CRLFs made 268 `git rm`
calls no-op; a `git stash` round-trip that quietly unstaged 268 deletions. Two of those three were
caught only because I had written a guard or re-verified. That ratio is not comfortable.

**Reviewer / QA (Claude drove; Derek was the adversarial reviewer).** The verification discipline
before touching paid infrastructure was the right shape: a synthetic v3 fixture bundle to exercise the
new code, a proof that it *fails closed* on a pre-cutover bundle, and — the part I'd repeat — pulling
the generated remote bash out of the real script **by AST** and reading what would actually execute,
rather than trusting a read-through of the source. Then the reboot path proved with a real
`systemctl restart` rather than a convenient `compose up`. Where QA was weak: I twice published a
confident causal claim before earning it. The `409` I attributed to my own restart (it was a by-design
admission gate). The missing `god`/`fly` I attributed to vanilla Valheim before checking any history.
The adminlist evidence did vindicate the *finding* — 12-day-old mtime, unchanged, an account mismatch
rather than a regression — but Derek was right on both counts that mattered: I'd stated it with
unearned confidence, and a repo-side fly path (the era16 teleport route) does exist.

**Operator / SRE (Claude drove; live paid infrastructure).** Backups before every mutation, the old
`master` branch retained at `8ca27eda` as a one-command rollback, `0600 root:root` preserved on the
env file, and the acceptance sample captured *while the player was still connected* because the window
auto-resets when the server empties. All good. The failure was timing awareness: I told Derek to join
seconds after a restart that makes the server reload **9.1 million ZDOs**, and his join failed. The
server log says `Game server connected` when it's ready; I had that signal available and didn't wait
for it. That is a one-line fix to a habit, not a hard problem.

**Product / planning (Derek set direction; Claude executed).** Pacing was good and mostly Derek's
doing: "one step at a time, say when" converted a risky live test into a sequence of confirmable
steps, and "if we over prune that's ok" is what made a 279-file deletion tractable instead of a
month of bikeshedding. Scope grew a lot but never speculatively. What to change: I asked for the VM
authorization and the GitHub push in the same `AskUserQuestion`, which was efficient but bundled two
decisions of quite different reversibility.

### Two seats, two views

**From Claude's seat.** My best work was refusing to accept documents that agreed with me. The m5
manifest said `/opt/comfy` was not a git checkout; I checked, and it was — of the *retired* repo, at
the exact commit the manifest itself named. That single probe turned a "copy some files over" job into
the actual cutover, and it also made the fix cheap, because the retired commit was an ancestor. My
worst pattern was the opposite failure, twice: reaching for a plausible cause and *stating* it before
testing it. Both times the real answer was discoverable in about two tool calls. The specific thing
I'd want next time is a habit rule, not a tool: when I'm about to explain an anomaly, check whether
I've actually read the code path that produces it — for the `409` that was one grep, and it would have
saved Derek an hour of justified suspicion.

**From Derek's seat** *(my reconstruction — correct me).* "I gave you a lot of rope today and it
mostly went where I hoped. What I care about is that you don't tell me something is fine when I've
just watched it not be fine. The god/fly thing wasn't about admin lists — it was that you explained my
lived experience away before you'd looked, and I've been burned by that. When you did look, the answer
was actually useful. Same with the prune: I don't need you to be careful, I need you to be
*recoverable* — both old repos still exist, so cut deep and tell me exactly what you cut. And I'm not
worried about the VM bill; I'm worried about a repo I can't navigate in six months."

## Last time's lessons — follow-through

Prior retro: `SESSION-RETRO-2026-07-12.md`. Several intervening sessions (m1/m4/m5 cuts) were not
retro'd, so some lessons are graded on this session's evidence only.

| id | lesson | status |
|---|---|---|
| `L-2026-07-12-1` | Apply the trust rule to your own optimistic docs | **acted-on hard** — the manifest's "not a git checkout" claim was false and probing it was the session's pivot |
| `L-2026-07-12-2` | Suspect the host/resource before patching the code | n/a — no resource-shaped failure this session |
| `L-2026-07-12-3` | IAP-tunnel SSH must run foreground | **held** — every SSH ran foreground; the documented benign `stdin ReadFile` traceback appeared and was correctly ignored |
| `L-2026-07-12-4` | Save-integrity is anchors-exact + ZDOs-in-tolerance, not delta-0 | n/a this session |
| `L-2026-07-12-5` | Retro-archive a partial prior window to buy repeatability cheaply | **pending** — the v2 world-test still carries the acceptance history; v3 got its own fresh sample instead |
| `L-2026-07-12-6` | Reset gateway windows before the real connect | **acted-on by the system** — the window auto-resets when the server empties, which is why capture had to happen mid-session |

## Second opinion resolved

None pending from last time (`--fleet` was not used on 2026-07-12). This session dispatched one —
see Provenance — which was **not** waited on.

## Lessons learned

1. **`L-2026-07-21-1` — A document asserting a negative about infrastructure is the cheapest thing in
   the repo to falsify, and the most valuable.** The m5 manifest said `/opt/comfy` was not a git
   checkout; one `test -d` disproved it and rewrote the whole session's scope. Falsify negatives about
   live systems before planning around them. → practice; reinforces `L-2026-07-12-1`.
2. **`L-2026-07-21-2` — Do not state a cause you have not read the code path for.** The `409` was a
   by-design admission gate one grep away; I blamed my own restart instead. Twice this session a
   plausible story was published ahead of the evidence, and it cost trust rather than time. → practice.
3. **`L-2026-07-21-3` — Reproducibility can be lost by the toolchain, not the process; when it is,
   record it rather than rebuilding.** The .NET 8 SDK embeds the git HEAD sha in the PDB, so the mod
   DLL's hash changes on every commit with unchanged source. → **ADR 0005**.
4. **`L-2026-07-21-4` — A credential-less host can still receive real history: `git bundle` is the
   transport.** 24 MB and 232 commits, no token on the VM, full provenance — available because the old
   commit was an ancestor. Check ancestry before assuming a re-clone. → **ADR 0006**.
5. **`L-2026-07-21-5` — Git is asymmetric about paths, and the asymmetry is silent.** `--name-only`
   output and `git show :path` are top-of-tree relative; a pathspec *argument* is cwd-relative.
   Prefixing all three made an append-check see zero records and pass nothing. Only running the gate
   for real caught it. → doc comment in `roadmap.mjs`; practice.
6. **`L-2026-07-21-6` — In a subtree-merged monorepo, git-history staleness and basename-orphan
   detection are both actively misleading.** Every file dates to the consolidation; 196 of 199
   apparent orphans were live C# referenced by namespace. Choose prune signals *after* checking what
   the merge did to them. → **ADR 0007**.
7. **`L-2026-07-21-7` — Parallel per-zone agents produce cross-zone incoherence by construction.**
   Generated outputs outlived their generator; index READMEs outlived everything they indexed. Budget
   a reconciliation pass; it found 11 more files. → **ADR 0007**.
8. **`L-2026-07-21-8` — Wait for the readiness signal before telling a human to act.** A `systemctl
   restart` here means a 9.1M-ZDO world reload; `Game server connected` is the signal and it was in
   the log the whole time. → memory `valheim-world-reload-delay`.
9. **`L-2026-07-21-9` — Scripted bulk file edits on Windows need explicit byte-level I/O.** A
   `Get-Content`/`Set-Content` round-trip mojibake'd 9 em-dashes invisibly to `--stat`; a Python
   text-mode write produced CRLFs that no-op'd 268 `git rm` calls. Guards caught one; luck caught the
   other. → memory `powershell-utf8-roundtrip-corrupts-files`.

## Provenance

- **Git range:** `89468c8..d75ffb2` (6 commits). Working tree clean at close.
- **Offloaded (HEARTH `local_generate`, `gcp-gemini-pro` / gemini-3.1-pro-preview):** the timeline
  condense, five-seat first pass, and lessons extraction — **edit verdict: `minor-fixes`**. Faithful
  to the factsheet with no invented facts; edited to correct one real distortion (it adopted "my
  gaslighting" as a finding, where the evidence actually *vindicated* the adminlist conclusion and the
  fault was unearned confidence, not a wrong answer), to restore the nuance that Derek was right about
  the teleport-route fly path, and to add the seat-driver attribution it flattened. A separate
  `gcp-gemini-pro` call drafted the four rewritten orientation READMEs — verdict **`minor-fixes`**: it
  invented two plausible links to pruned files and silently dropped comfy's original mission statement,
  both corrected before commit.
- **Frontier (Claude):** the factsheet, all verification, every VM action, both seats' views, the
  follow-through grades, lessons, ADRs 0005–0007, `DECISIONS-PENDING`, memory, and every repo-coherent
  write.
- **`--fleet`:** dispatched, **not** waited on — `plan_id hearth-retro-20260721-baseline-618dfd6e`
  (builders `am4-worker-1`, `cc-builder-2`). Asked for the strongest case that the prune was
  under-verified, where the acceptance evidence is weakest, and the opposing argument on carrying an
  unreproducible binary. Reap next session.
- **Ledger:** `retrospective.created` via `mcp__hearth__record_event`.

---

# Session Retro — 2026-07-21 (addendum B) · The audit session: what reports success while producing nothing

**One-line:** We **audited the conditional logic the cutover left behind**, found five independent
systems that report success while producing nothing, fixed or deleted what was safe, and turned months
of unincorporated area-of-interest testing into a findings record — after Derek corrected three of my
own confident wrong claims, one of which was that the evidence was lost.

## What this session was

A **curate-then-audit-then-record** session, the second of the day in `C:\work\baseline`. It opened as
a status check ("where are we and what's next") and widened twice on Derek's explicit latitude: first
to clean up what the audit found, then to preserve what an abandoned test campaign had actually
learned.

The through-line arrived unplanned. Almost everything worth finding shared one shape: **a thing that
looks operational, succeeds, and yields nothing.** Once named, it kept recurring — including, with some
irony, in this retro's own fleet second opinion.

## What shipped

| Commit | What |
|---|---|
| `8cd4917` | Repointed 30 runbook commands and 4 executable scripts off the retired checkout roots; fixed the Windows-only `Path.Combine` test failure. |
| `62910aa` | Separated heartbeat liveness from primary admission (`RecordAndAdmit`); ADR 0008. |
| `60d7c5b` | Conditional-logic audit; deleted `rollback-gateway.ps1` and `configure-player-gateway.sh`; rate limiter no longer trusts an unverified header; local dashboard repointed at the IAP tunnel. |
| `1887626` | Completed the 107-key config inventory as eight decisions, each carrying its counter-reason. |
| `de9cca6` | Removed the swarm/unattended-client harness; 107 config keys to 88. |
| `eab23a0` | The area-of-interest findings record. |
| `6e22eb9` | Recovered the AoI density dataset; wrote the knee-experiment brief. |

45 files changed, 13,718 insertions, 1,482 deletions. Tests 523/525 to **528/528**.

New durable artifacts:
- [`Lumberjacks/docs/network/area-of-interest-findings.md`](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/Lumberjacks/docs/network/area-of-interest-findings.md) — what the AoI testing learned and why none of it reached the code.
- [`Lumberjacks/docs/network/aoi-knee-experiment-brief.md`](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/Lumberjacks/docs/network/aoi-knee-experiment-brief.md) — self-contained brief for the capacity-frontier experiment.
- [`fieldlab/docs/config-surface-decisions.md`](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/config-surface-decisions.md) — all 107 config keys as eight decisions with counter-reasons.
- [`fieldlab/docs/audit-2026-07-21-conditional-logic.svg`](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/audit-2026-07-21-conditional-logic.svg) — the audit drawn for posterity.
- [`fieldlab/evidence/aoi-density-pressure-matrix-20260704/`](../evidence/aoi-density-pressure-matrix-20260704/README.md) — the rescued density dataset.
- [`network/mod/ComfyNetworkSense/SWARM-HARNESS-REMOVED.md`](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/network/mod/ComfyNetworkSense/SWARM-HARNESS-REMOVED.md) — the deletion's recovery pointer and counter-argument.
- ADR [0008](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/adr/0008-liveness-is-not-admission.md).
- Memory: `guardrails-are-mode-scoped`.

## The team retro — our collaboration across the seats

**Architect (Derek decided; Claude drove).** Derek's best call was scoping rather than settling: release
unreproducibility is acceptable *in operator-in-the-seat mode*, and the heavy provenance tape is an
**independent-agent guardrail** — a mode distinction, not a permanent acceptance, with the re-arm
trigger named. That reframing is more useful than either "fix it" or "accept it" and it generalises past
this decision. My own strongest call was refusing to flip the dev-build split-brain: an uncut build makes
the handshake fail open while ZDO admission 503s, which is tempting to call a bug — but
`ValheimReleaseIdentity` argues its case in a doc comment and `ValheimZdoIntegrationContractTests`
asserts the opposite in a test. Two considered decisions disagreeing is a decision, not a defect, so it
went to the register with a recommendation. What to change: I framed the dashboard fix as "widen the
allowlist" before understanding that admin surfaces were never on the public port at all. The right
answer — follow the tunnel that already existed — was better *and* smaller, and executing my first
framing would have missed it.

**Implementer (Claude drove).** `RecordAndAdmit` is the shape I want more of: the defect was line order
inside a lambda, so the fix made the ordering a named, testable invariant rather than reordering two
lines and hoping. Deleting `rollback-gateway.ps1` rather than repairing it was also right — a standalone
rollback that duplicates the drill's proven path is a liability, and the drill already does image
re-pinning correctly. What to change: my first config-audit pass covered 44 of 107 keys and I did not
notice until Derek asked for the rest. The call returned `ok:true` in 57 s; I read the duration and not
the truncation.

**Reviewer / QA (Claude drove; Derek was the corrector).** Verification was the session's real product.
Across thirteen gemini-pro threads I caught and rejected: stale-path claims about scripts that resolve
correctly (the model pattern-matched the variable *name* `$ComfyRoot`), a "live time-bomb" that the
runbook pins to 0, "purely advisory" for a system whose rank is enforced at `ZdoRedirectRunner.cs:337`,
and three files reported missing that exist and were merely unpacked. Any one of those, written down
unchecked, would have sent a future session chasing nothing. **But my own error rate mirrored the
models'**: three times I asserted something I had not checked — that the dashboard IP was probably
stale, that the AoI dataset was gone, and that a tuning campaign would be blind for want of
instrumentation. All three wrong, all three one command from disproof.

**Operator / SRE (Claude drove).** The `deploy-gateway.ps1` finding is the one I am gladdest we chased:
it tars, hashes and ships two source files from a default root that still holds pre-cutover content, and
**its integrity check passes because it hashes what it shipped.** I verified both files differ between
roots rather than asserting it. The dashboard repoint is the tidiest operational move of the session:
following the SSH/IAP tunnel `start-gateway-tunnel.ps1` already opened let the allowlist widen to admin
and dev stats with **no increase in public exposure** — the opposite of the tempting fix. Every route
added was checked to exist first; there is no `/api/v0/admin/`, and I would otherwise have invented it.

**Product / planning (Derek set direction).** Pacing was Derek's and it was good: "run your hygiene
efforts", then "start cleaning up in parallel", then a hard stop at documentation rather than
implementation for the AoI work. That last call matters most — *we don't need to do the change right
now* is what kept a findings record from becoming a speculative refactor. Scope grew a lot and never
speculatively. What to change: I twice offered a menu of next actions when the evidence already
supported a recommendation.

### Two seats, two views

**From Claude's seat.** My best work was treating model output as hypothesis rather than finding —
thirteen threads produced much correct analysis and roughly half a dozen confident errors, and the only
thing separating them was going to look. My worst pattern is unchanged from this morning's retro and I
should say so plainly: `L-2026-07-21-2` was *don't state a cause you have not read the code path for*,
and I did it three more times today. The failure mode is narrower than "overconfidence" — in all three
cases I reasoned from a *plausible model of the system* instead of from the system. "Gitignored var
dir" implied "gone"; "InterestManager emits nothing" implied "the campaign would be blind". Both
inferences were locally valid and globally wrong, because I had drawn the boundary of "the system" too
small. Derek's correction — *anything we lost exists in repos we cloned to make this one* — was about
scope, not care.

**From Derek's seat** *(my reconstruction — correct me).* "I gave you a broad brief and you found real
things, which is what I wanted. Two pushes. You keep telling me something is gone when you've looked in
one place — I've told you the old repos are the archive, so use them. And when I pushed back on the sim
rows I wasn't wrong about the *idea*: a cheap repeatable proxy that runs without me in the loop is
exactly what I want, and you were right that those particular rows are flat. What I actually care about
is the knee — at what range and object count does this fall over — because that's the number that makes
every other AoI argument decidable. The rest is bookkeeping, and I'm glad the bookkeeping is honest now,
but don't mistake it for the work."

## Last time's lessons — follow-through

Prior retro: this file's first section, earlier the same day.

| id | lesson | status |
|---|---|---|
| `L-2026-07-21-1` | Falsify a document's negative claims about infrastructure | **acted-on** — "stale IP", "time-bomb" and "missing files" were all falsified by direct check |
| `L-2026-07-21-2` | Do not state a cause you have not read the code path for | **pending — regressed.** Three fresh instances. Escalated as `L-2026-07-21-13`. |
| `L-2026-07-21-3` | Toolchain-lost reproducibility: record it, don't rebuild | **acted-on** — ADR 0005 amended with Derek's mode distinction |
| `L-2026-07-21-4` | `git bundle` moves history to a credential-less host | n/a — no VM actions |
| `L-2026-07-21-5` | Git path asymmetry is silent | n/a |
| `L-2026-07-21-6` | Choose prune signals after checking what the merge did to them | **acted-on** — same discipline applied to model output |
| `L-2026-07-21-7` | Parallel per-zone agents produce cross-zone incoherence | **acted-on, reconfirmed** — one AoI thread called files missing that another thread held |
| `L-2026-07-21-8` | Wait for the readiness signal before telling a human to act | n/a |
| `L-2026-07-21-9` | Scripted bulk edits on Windows need explicit byte-level I/O | **pending — regressed.** Graded "held" when first written, which was wrong: about an hour later I corrupted `Lumberjacks/docs/network/README.md` with a PowerShell `Get-Content -Raw` / `WriteAllText` round-trip, mojibaking every em-dash. Reverted via `git checkout` and redone with the Edit tool. The lesson being *written down* is evidently not the control; the control is not reaching for PowerShell to modify a file at all. See `L-2026-07-21-18`. |

## Second opinion resolved

`hearth-retro-20260721-baseline-618dfd6e` — **no verdict, and the lane itself is the finding.**

Both builders returned `ok:false`, `empty_build:true`, `agent_rc:3`, `reason: "agent produced nothing"`,
with `routing: route-disabled-temporarily`. Yet the assay scored both **B / 70** on `162/162 tests
passed` and `has_retro: true`, quoting a `retro_excerpt` dated **2026-06-29** — content already in the
checkout. Promotion correctly declined with *"empty diff vs target — winner changed nothing"*, but the
scoreboard had already named a winner.

**The assay graded the workspace, not the work.** An empty build scored a B because the criteria measure
properties of the tree it was handed. That is this session's theme arriving uninvited, and it means
fleet second opinions cannot be trusted without checking `empty_build` first.

## Lessons learned

1. **`L-2026-07-21-10` — A system that reports success while producing nothing is the most expensive
   failure mode available, because nothing alarms.** Five independent instances in one session:
   `rollback-gateway.ps1` mutating `/opt` then failing on a forbidden build; `valheim-lab.compose.yml`
   still launching clients that idle at the menu; 998 sim rows with `avg_fps` constant at 60.0; the one
   real AoI capture reporting all-zero network fields from Solo mode; and the fleet assay scoring an
   empty build a B. → **ADR 0009**.
2. **`L-2026-07-21-11` — A verification that hashes its own output verifies nothing.**
   `deploy-gateway.ps1` tarred files from a stale root, hashed those same files, and passed. Integrity
   checks must compare against an independent source of truth. → **ADR 0009**.
3. **`L-2026-07-21-12` — "Not tracked in git" is not "lost"; the retired checkouts are an archive.** I
   declared the density dataset unrecoverable; all three artifacts sat in `C:\work\comfy`'s gitignored
   `var/`. → memory `retired-repos-are-the-archive`.
4. **`L-2026-07-21-13` — Escalated from `L-2026-07-21-2`: I reason from a model of the system when I
   should reason from the system, and the tell is that my wrong claims are always *locally* valid.**
   The habit fix is specific: before asserting an absence, name the boundary I searched and ask what
   lies outside it. → practice; escalated after regressing across consecutive retros.
5. **`L-2026-07-21-14` — A truncated model response is not a timeout; on a thinking model the reasoning
   consumes the output budget.** The first config pass returned `ok:true` in 57 s covering 44 of 107
   keys at `max_tokens: 8000`. Raising the HEARTH timeout, the intuitive fix, would not have helped. →
   practice.
6. **`L-2026-07-21-15` — Model output is a hypothesis; the cheapest audit is existence.** Across 13
   threads the recurring error was confident claims of absence and staleness. Every one fell to a single
   check. → practice.
7. **`L-2026-07-21-16` — Two systems that should inform each other and don't is invisible to any audit
   scoped to one of them.** The Valheim tier model and the Lumberjacks interest manager were each
   measured well and separately; the gap was in neither codebase but between them, and
   `interest-management.md` had already named it as an unclosed action nobody closed. → findings record.
8. **`L-2026-07-21-18` — Writing a lesson down is not a control; removing the capability is.**
   `L-2026-07-21-9` said scripted bulk edits on Windows need explicit byte-level I/O. I wrote it,
   graded it "held", and broke it an hour later with a PowerShell `Get-Content -Raw` /
   `WriteAllText` round-trip that mojibaked every em-dash in a README. The rule was known and
   available and did not fire, because the reach for PowerShell is reflexive. The control is
   narrower and mechanical: **use the Edit tool for file edits; if a script must do it, `io.open`
   with explicit encoding and newline.** Never `Get-Content`/`Set-Content`/`WriteAllText` on a file
   with non-ASCII. → practice, superseding `L-2026-07-21-9`.
9. **`L-2026-07-21-19` — Re-check a recommendation before executing it; the ground moves.** Three of
   the config-surface decisions written earlier the same day were wrong by the time they were run.
   D2 said delete 17 evidence keys — but `LumberjacksPriorityProbeRunner` writes the priority
   manifest the landmark design later came to depend on, and the Shadow runner turned out entangled
   with the manual route walk that was deliberately kept. A recommendation is a snapshot of what was
   known; executing it later without re-reading is how a considered decision becomes a mistake. →
   practice.
10. **`L-2026-07-21-17` — Delete with a pointer, not a comment block.** The swarm harness went with a
   `SWARM-HARNESS-REMOVED.md` naming the recovery SHA, what stayed and why, the orphans left behind, and
   the honest counter-argument for wanting it back. Commented-out code rots; a SHA does not. → practice.

## Provenance

- **Git range:** `ac151fc..6e22eb9` (7 commits). Working tree clean at close.
- **Offloaded (HEARTH `local_generate`, `gcp-gemini-pro`):** 13 analysis threads (6 conditional-logic, 3
  config-surface, 4 AoI) plus this retro's timeline/seats/lessons first pass — **edit verdict:
  `minor-fixes`.** The retro draft was faithful to the factsheet but conflated the heartbeat *admission
  gate* with the *rate limiter* (two separate findings) and merged the swarm-harness deletion with the
  matrix server that was deliberately deferred. Both corrected. The analysis threads were individually
  useful and collectively required about six substantive corrections, each recorded in the artifact it
  fed.
- **Frontier (Claude):** the factsheet, every verification, all code changes, the SVG, both seats' views,
  the follow-through grades, lessons, ADR 0008, `DECISIONS-PENDING`, memory, and every repo-coherent
  write.
- **`--fleet`:** none dispatched. The prior one was reaped — see *Second opinion resolved*.
- **Ledger:** `retrospective.created` via `mcp__hearth__record_event`.

---
---

# Session 3 — 2026-07-21 (build + ship + bake in: AoI band-shaping to production)

**One-line:** Worked the handoff queue, then **built the measured AoI shape into the real Valheim
netcode and shipped it to production** — and got caught, three times, asserting "can't / doesn't
exist / is broken" from a mental model instead of a cheap check.

## What this session was

A **build-and-ship** session that started as queue-clearing and turned into a full vertical: measure →
decide → plan → MVP → deploy to prod → validate live → make it permanent. ~11 commits, ~1,400 lines,
one continuous run. The measurement half was Lumberjacks (the game server); the shipped half was the
Valheim mod + the P7 GCP VM.

## What shipped

| Commit | What |
|---|---|
| `5f79fd0` | Task 2 — uncut dev builds admit schema-2 ZDOs unattested (kills the fail-open/fail-closed split-brain) |
| `480849f` | Task 3 — near/mid/far band-population counters per tick at `/tick` |
| `1dd6c18` | Task 7 — landmark reach: distance as a granted property (`Admits` = rank OR landmark) |
| `7c58e49` | Task 10 — three sibling POSTs folded onto `BoundedRawHttp` |
| `296ceab` | Task 9 — keep the lab clients profile as manual noVNC |
| `c915215` · `a338535` | Handoff progress banner · record Task 1 (comfy-gateway re-provisioned off baseline) |
| `89eebbc` | Task 4 — AoI measurement baseline + decision to build end-to-end |
| `ecb2116` | AoI band-shaping MVP: near-full / mid-thin(5Hz) / far-drop in the mod redirect |
| `409a397` | Auto-port harness: on-join → densest ZDO cell + god/fly + 40m up |
| `8ca6242` | AoI band-shaping **P7 production baseline** + harden the deploy script |

New durable artifacts: `fieldlab/evidence/aoi-baseline-20260721/` (the measurement + harnesses),
`fieldlab/evidence/aoi-band-shaping-p7-baseline-20260721/` (the production reference), a new
`ZdoBandPolicy` + `AutoPortDensity`, the approved AoI plan, ADR 0011, four memories
(`baseline-build-test-toolchain`, `valheim-dedicated-godfly`, `trust-dereks-recall`,
`iap-ssh-teardown-noise`).

## Timeline

Cleared the seat-free code queue (tasks 2/3/7/9/10, each built + tested in an `sdk:9.0` container or
the net48 mod build). Re-provisioned the stale local comfy-gateway (task 1). Ran the AoI measurement
(task 4): **send-volume is the tick ceiling** (the filter is ~4% of tick), a dual-radius cut buys
**~8× p99 headroom**, and the recovered 9,600-row pressure model is **falsified** (it predicts tick
cost independent of player count; measurement scales strongly with players). Derek reframed it mid-run
from "find a precise knee" to "build a **consistent re-runnable baseline**" — the single-process
generator caps ~300 bots and a 20× run-to-run swing turned out to be accumulated stack/host state
(fresh-stack-per-session is the control; a leaking entity queue was tested and **ruled out**). He also
pointed out the test "was built to be a matrix" and I'd run 1-D curves.

Decided (with Derek): distance-band AoI is a **mod-side/producer** concern; the gateway is a passive
relay. Planned MVP-first. Built the MVP: a pure `ZdoBandPolicy.Classify` (the one unit test) plus a
runner refactor that **splits the fused suppress/ack/emit** — the ack is mandatory (skip it → duplicate
storm), so a dropped far object is ack-but-don't-emit and drops must not touch the gate seq. Flag-gated
default-off. Rebuilt the auto-port harness (server pushes the densest ZDO cell; client god/fly +
teleport +40m). Deployed to production P7 over a gcloud IAP tunnel and **validated live**: at the
densest single-player build, band-shaping **dropped ~85% losslessly** (`missing_seq=0`, `duplicates=0`,
consumer caught up). Baked it in permanently and captured the production baseline.

## The team retro — our collaboration across the seats

**Architect (Claude holds the whole; Derek calls the shape).** Two sound calls. Putting AoI on the
**producer** (mod) not the relay (gateway) cleanly decouples transport from game state — the gateway
stays a dumb, recipient-partitioned queue and the shaping happens where the observer distance is known.
And killing the 9,600-row model on evidence rather than deference. The one Architect miss is downstream:
we shipped a drop-with-ack path whose **far→approach re-sync** is unproven (see watch items).

**Implementer (Claude).** The runner refactor was the highest-risk change and it held: splitting
suppress/ack/emit, keeping the ack mandatory, and keeping drops off the gate counters. One unit test
(the pure decision function), everything else integration — the right ratio for Unity-coupled code.
Small craft wins: `perl` (not PowerShell `Get/Set-Content`) to strip an invisible U+001F control char;
container builds to dodge the missing net9/net48 host SDKs.

**Reviewer / QA (both).** Verification leaned live and it paid: the flag-gate meant prod deploy was
boring, and the one-call gate (`receipts_match_no_loss`) plus the band-decision jsonl gave a clean
read. But QA *judgment* wobbled — I twice reported a defect that wasn't one (a "duplicate storm" that
was a draining backlog; a "broken world" that was a barren spawn). Derek was the backstop.

**Operator / SRE (Claude drove, badly then well).** The whole P7 deploy fought me over **cosmetic**
gcloud-IAP teardown noise (`stdin ReadFile failed` prints *after* success) that I compounded with a
PowerShell `2>&1` that flips exit codes on a harmless stderr warning. I concluded "I can't drive this"
and offloaded manual installs to Derek — wrong. A plain `ssh comfy-p7 "cmd"` worked, and I then drove
the entire deploy + install + baseline myself, and hardened the deploy script (scp-a-script, not
`base64|bash`).

**Product / planning (Derek paces).** We avoided the benchmarking rabbit hole (Derek's "it's about
consistency, not a magic number") and shipped a real vertical slice with a live validation instead of
an endless measurement. Scope discipline was good; the pacing correction ("we're drifting, remind me
the plan") was Derek's and it was needed.

## Two seats, two views

**From Claude's seat.** The math and the build were strong — instrumentation was accurate, the AoI
pipeline is lossless at worst-case density, and I offloaded the draftable prose (baseline note, plan,
interpretation) to Gemini Pro to keep bandwidth for the C#/bash. What degraded was **operational
epistemics**: three times I let a model of failure override a five-second check, and asserted the
failure to Derek as fact. The fix isn't "check more" — it's a hard gate on the *speech act*: never tell
Derek "can't / gone / broken" until I've falsified it.

**From Derek's seat (my reconstruction — correct me).** "Batting 1000 calling BS today." The code came
fast, but I had to be the backstop against invented causes: the auto-port script wasn't gone (just
archived with the swarm harness); the SSH block was terminal noise, not a wall; the "backup" was a
benign backlog and I was staring at an empty spawn. You can't debug or benchmark by inventing a cause
you haven't traced — trace the path first. Also: keep it on. This is normal play now.

## Last time's lessons — follow-through

| id | lesson | grade |
|---|---|---|
| `L-2026-07-21-13` | Reason-from-model vs check the path | **pending — regressed hard.** Three fresh instances this session; escalated to `L-2026-07-21c-1` as a speech-act gate |
| `L-2026-07-21-12` | Not-tracked-in-git is not lost; retired checkouts are an archive | **regressed** — declared the portal script gone after one grep; it existed |
| `L-2026-07-21-18` | Removing the capability, not writing the lesson, is the control | **acted-on** — used `perl`/Edit, never `Get/Set-Content`; no file corruption this session |
| `L-2026-07-21-19` | Re-check a recommendation before executing; the ground moves | **acted-on** — verified prod redirect state, tunnel, band flag before each step |
| `L-2026-07-21-3` | Toolchain-lost reproducibility: record, don't rebuild | n/a this session |

## Second opinion resolved

The prior retro's dispatched `--fleet` plan (`hearth-retro-20260721-baseline-618dfd6e`) reaped as a
**dud**: both builders returned `empty_build` / "agent produced nothing" (`agent_rc=3`, routing
`route-disabled-temporarily`, runner `vllama-planner`), and the assay even lifted a `retro_excerpt`
from the **wrong** session (2026-06-29). Zero signal. Confirms the standing caution: a fire-and-forget
second opinion that no one shapes or reads is pure cost — and here, reading it still taught nothing.

## Lessons learned

1. **`L-2026-07-21c-1` — "Can't / doesn't exist / is broken" is a hypothesis, not a report.** Escalated
   from `L-2026-07-21-13`/`-12` after three fresh regressions in one session, all caught by Derek. The
   control is not "check more" (I *had* the memories) — it's a **gate on the speech act**: I may not
   tell Derek a thing is impossible, missing, or failed until I've run the cheap falsifying check
   (grep by behaviour not guessed name; run the plain command; read the actual counters). → practice.
2. **`L-2026-07-21c-2` — Cosmetic stderr is not failure, and PowerShell makes it look like one.** The
   gcloud-IAP `stdin ReadFile failed` traceback prints on teardown *after* the command succeeds; wrap a
   native exe in `2>&1` in PS 5.1 and a harmless warning becomes a `NativeCommandError` that flips the
   exit code. Don't `2>&1` a native exe; read stdout; judge success by the actual output. → memory
   ([[iap-ssh-teardown-noise]]).
3. **`L-2026-07-21c-3` — In a filtered emission pipeline, the ack is mandatory and separate from the
   emit.** Dropping/thinning a sequenced item means ack-but-don't-emit (skip the ack → duplicate
   storm), and suppressed-not-emitted items must not touch the delivery-gate counters (or they read as
   false loss). This is the load-bearing insight that made band-shaping ship-safe. → ADR 0011.
4. **`L-2026-07-21c-4` — Benchmark for a re-runnable baseline, not a magic number** (Derek). A
   single-process generator that caps ~300 bots can't find an absolute knee, and 20× run-to-run swings
   are usually host/stack accumulation, not an app leak. The deliverable is a fixed grid of health
   signals you diff future changes against. → doc (the baseline evidence).
5. **`L-2026-07-21c-5` — Flag-gate a behaviour-changing change default-off and you can ship it to prod
   before it's fully proven.** The band-shaping MVP went to production behind `zdoBandShapingEnabled`
   (default false); the deploy was a no-op until one flag flip, and rollback is one flip back. → practice.
6. **`L-2026-07-21c-6` — Offloading prose to the fleet preserved the session.** Gemini Pro drafted the
   baseline note, the plan, and this retro from factsheets; every draft was `faithful`/`minor-fixes`.
   Keeping judgment frontier and grunt-prose offloaded is what let a marathon session stay coherent. → practice.

## Provenance

- **Git range:** `5873086..HEAD` (11 commits). Uncommitted: `Lumberjacks/package{.json,-lock.json}`
  (incidental `npm install ws` for the load harness — left out of the retro commits).
- **Offloaded (HEARTH `gcp-gemini-pro`):** the timeline, five-seat team retro, both seats' views, and
  the lessons first-pass (this section edited frontier). Also offloaded earlier in-session: the AoI
  baseline note, the implementation plan, the band-shaping interpretation. Draft `edit_verdict`:
  **faithful** (light edits for repo-specific detail).
- **Frontier (Claude):** the factsheet, every verification and code change, ADR 0011, the follow-through
  grades, lessons IDs, `DECISIONS-PENDING`, memory, and every repo-coherent write.
- **`--fleet`:** none dispatched this session; the prior plan was reaped (dud — see above).
- **Ledger:** `retrospective.created` via `mcp__hearth__record_event`.

---

# Session Retro — 2026-07-21 (session d) · The gameplay-event seam, and a vantage I got wrong twice

**One-line:** We **shipped a live gameplay-telemetry seam end-to-end** — a player's kill in Valheim
now appears on the community dashboard, identity-stripped — but only after **pivoting the producer
from a wrong server-side vantage to client-side**, a correction the *pruned* quest-slice backup had
been holding the whole time and Derek had to point me at.

## What this session was

A **pivot-driven build** session: pin the over-sharpening, then build one vertical seam
(client kill → dashboard) through four increments, each ending in a real login test rather than unit
ceremony. The through-line is uncomfortable and worth stating plainly: **the session's hardest work
was undoing an architecture I chose without checking a domain assumption**, and the fix already
existed in a backup we'd pruned two sessions earlier. Every increment after the pivot went fast; the
pivot itself cost the most tokens and all seven of Derek's BS-calls.

## What shipped

| Commit | What |
|---|---|
| `ef73879` | Pinned all AoI optimization to hard-hold (`PINNED-aoi-optimization.md`); pivot to the telemetry dashboard. |
| `ad16e17` | Increment 0 — re-established the `omen-dashboard` (nginx over the P7 IAP tunnel) live; browser-free verify runbook. |
| `85567e0` | Committed the source integration plan the work builds from. |
| `6dc6031` | Increment 1 — `killing_blow` seam: gateway ingress `POST /valheim/events` + `GameplayEventFeed` (identity-stripped) + Unity-free `GameplayEventClassifier`. **Built server-side.** |
| `ffede2e` | Increment 1b — **the pivot**: client-side capture → new routed RPC `ComfyNetworkSense_GameplayEvent` → server handler POSTs on the private plane. |
| `a8abb5f` | Increment 1b fix — emit on `Character.OnDeath`, not the `Damage` postfix (`IsDead()` is false there). |
| `0990b82` | Increment 3 — Gameplay Feed panel on `community.html`. |
| `821ed3a` | Increment 2 — `first_hit` + `weapon_used`. |
| `474c647` | Dropped the ingress's redundant telemetry-key check (the change that shipped as `inc1-r2`). |

New durable artifacts: ADR [0012](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/adr/0012-gameplay-telemetry-is-client-side.md); memories
`community-dashboard-already-exists`, `p7-gateway-image-pinned`, `gameplay-capture-is-client-side`;
the `omen-dashboard` verify runbook; a live Gameplay Feed on the dashboard. Validated by live login:
`killing_blow $enemy_leech`, `first_hit`, and `weapon_used = Unarmed` (Derek punched it) all rendered.

## The team retro — our collaboration across the seats

The standard split held: **Claude** held the whole, instrumented, wrote every repo change, and drove
all infra (P7 ssh, on-VM gateway image builds, mod deploys); **Derek** paced, made the pivot call,
drove the live client (login + kills), and called BS at exactly the moments that bent the work toward
the right design.

**Architect (Claude drove; Derek made the pivot call).** The good call was reuse: discovering the
dashboard + versioned aggregates-only v0 API already existed and reusing the `GameEvent` envelope
instead of building the integration plan's greenfield `telemetry_event` contract. The bad call was the
one that cost the session — designing gameplay capture **server-side** without verifying who simulates
combat on a Valheim dedicated server. Connected clients own the creatures they fight, so the server's
hooks never fire. I assumed the dedicated server was authoritative over combat; the pruned quest slice
(client-side, "only local-player actions count") was the proof it isn't, and I didn't read it until
Derek pointed me there. What to change: verify the domain model against prior art **before** picking
the seam, not after the live test refutes it.

**Implementer (Claude drove).** Clean parts: the `GameplayEventClassifier` stayed Unity-free and
unit-tested (37 pass) across two redesigns; the client→server RPC target was **verified against
`assembly_valheim`** rather than guessed (`GetServerPeerID` turned out not to be a public member —
that grep saved a wrong build). Stumble: I hooked the `Damage` postfix to read `IsDead()`, which is
false there — 0 deaths across 58 live hits — because death is processed after damage. Reading the
execution order first (or logging health) would have caught it before a deploy cycle.

**Reviewer / QA (Claude drove; Derek was the adversarial reviewer).** This is where the session was
weakest and it is not close. **Derek called BS seven times in ~12 hours and was right every time.**
Twice this session directly: I asserted the "ownership" cause before I had evidence (0 hook-fires was
still ambiguous vs. an arming confound — I stated it as fact anyway), and I implied the functionality
"wasn't built/deployed" — falsified in one grep, the code *was* in the loaded DLL. Then Derek pointed
at the comfy backup and the real answer had been sitting there. The control I keep writing down
(falsify before you report) keeps not firing. What to change is not "remember"; see the lessons.

**Operator / SRE (Claude drove; live paid infra).** The recoveries were sound: every gateway deploy
was reversible by re-pin, the mod deploy backed up before swapping, and I read the live cutover
numbers before answering Derek's "are we on native?" instead of guessing off a label. The failure was
trusting a script over the environment: `deploy-gateway.ps1` ran "successfully" and deployed **nothing**
because the P7 gateway is image-pinned under an M0 freeze (`docker compose build gateway` is a no-op
with no `build:` section). I only caught it because the endpoint 404'd. The real path — build the
image on the VM, re-pin `LUMBERJACKS_GATEWAY_IMAGE` — is now a memory. A small grace: the mod's
`PluginOutputPath` meant one `deploy-network-sense` updated Derek's client *and* the server.

**Product / Planning (Derek drove; Claude planned).** Derek's pacing was the session's best asset. The
opening hard-hold on AoI ("we'd be over-sharpening") kept us out of a tar pit; keeping the first
increment scoped to `killing_blow` only made the client/server gap cheap to diagnose; and "advance
toward the full plan" was the right altitude — ambition without greenfield waste. Increments 2/3 after
the seam proved were fast because the seam was right.

## Two seats, two views

**From Claude's seat.** I over-reached on architecture and under-reached on verification — the exact
inverse of what I should do. I committed to a vantage (server-side) for a *convenience* reason (auth
simplicity) and let that convenience survive until a live test killed it. Three separate times I turned
a hypothesis into a reported fact. What I'd want next time: a hard rule that "X can't work / doesn't
exist / is broken" is unspeakable until a named cheap check has failed — and to treat a pruned backup
as a *primary source*, not a lost thing.

**From Derek's seat (my reconstruction — correct me).** *"The seam works and it's on the dashboard,
which is what I wanted. But I called BS seven times today and went 7-for-7, and every one was the same
shape: Claude stating a wall exists before checking it's a wall. I remember building this stuff — the
quest slice punched trees and tracked kills for weeks, client-side — so when the theory was 'the server
can't see it,' my instinct said check the thing I built, not theorize. The backup is the receipt. Ship
it, tune the log spam down when real players show up, and next time read the archive before you tell me
it's gone."*

## Last time's lessons — follow-through

| Lesson | Status |
|---|---|
| `L-2026-07-21c-1` — "Can't / doesn't exist / is broken" is a hypothesis, not a report | **regressed, hard — 7 fresh instances.** Re-escalated as `L-2026-07-21d-2` with a stronger control. |
| `L-2026-07-21c-2` — Cosmetic stderr (IAP teardown) is not failure | **acted-on** — treated every `stdin ReadFile failed` traceback as benign throughout; drove P7 ssh freely. |
| `L-2026-07-21c-5` — Flag-gate a behaviour change default-off and ship it to prod | **acted-on** — `gameplayEventProducerEnabled` default-false; armed only for the test. |
| `L-2026-07-21c-6` — Offloading prose to the fleet preserves the session | **acted-on** — Gemini Pro drafted the endpoint recon, the `community.html` structure, and this retro (all faithful). |
| `L-2026-07-21c-3/c-4` — ack-separate-from-emit / baseline-not-magic-number | n/a this session (AoI-specific). |

## Lessons learned

1. **`L-2026-07-21d-1` — Valheim gameplay capture is client-side; the server can't see client-owned
   combat.** The creatures a connected player fights are owned/simulated by that player's client, so
   server-side combat hooks never fire; capture on the client and relay by routed RPC to a
   private-plane server handler that POSTs. → **ADR 0012** + memory `gameplay-capture-is-client-side`.
2. **`L-2026-07-21d-2` — Escalation of `c-1`: gate the *speech act*, not the memory.** Writing "falsify
   before you report" down has now failed across three sessions (7 regressions today). The control that
   actually holds is a precondition: I may not *state* "can't / doesn't exist / is broken / is the
   cause" until I name the cheap check and it has failed — and a pruned/retired backup is a primary
   source to read, not a loss to lament. → practice (open-decisions register), superseding `c-1`.
3. **`L-2026-07-21d-3` — `Character.OnDeath` is the kill signal; `IsDead()` is false at a `Damage`
   postfix.** Death is processed after damage application; record the last attributed hit in the damage
   hook and emit on `OnDeath`. → memory (folded into `gameplay-capture-is-client-side`).
4. **`L-2026-07-21d-4` — A P7 gateway code change deploys by building the image on the VM + re-pinning,
   not `deploy-gateway.ps1`.** The gateway is image-pinned under an M0 freeze; the old script's
   in-place `compose build` is a silent no-op. → memory `p7-gateway-image-pinned`.
5. **`L-2026-07-21d-5` — Audit what exists before drafting a greenfield plan.** The "12-phase" dashboard
   was ~80% built; the archaeology that found it saved most of the plan and reused `GameEvent`. →
   memory `community-dashboard-already-exists`; reinforces ADR 0009 (verify against an independent source).
6. **`L-2026-07-21d-6` — Verify a Valheim/engine API against `assembly_valheim` before coding it.** The
   grep that showed `GetServerPeerID` isn't a public `ZRoutedRpc` member turned a would-be wrong build
   into a one-line pivot to `InvokeRoutedRPC(0L, …)`. → practice.

## Provenance

- **Range:** `abaf23d..HEAD` (this session's 8 commits `ef73879..821ed3a` + retro/r2 hygiene). AoI
  session (`ecb2116..02dff2e`) excluded — already retro'd (session c).
- **Offloaded (Gemini Pro `gcp-gemini-pro`):** the endpoint-shape recon, the `community.html` structure
  recon, and the timeline/role-reads/lessons first pass of this retro. Draft `edit_verdict`: **faithful**
  (tightened the "80% built" framing, added deploy/memory specifics, rewrote Derek's seat).
- **Frontier (Claude):** the factsheet, all archaeology direction, every verification + code change +
  deploy, ADR 0012, the follow-through grades, lesson IDs, `DECISIONS-PENDING`, memory, and every
  repo-coherent write.
- **`--fleet`:** none dispatched.
- **Ledger:** `retrospective.created` via `mcp__hearth__record_event`.
