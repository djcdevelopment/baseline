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
- ADRs [0005](../docs/adr/0005-carry-forward-unreproducible-artifacts.md),
  [0006](../docs/adr/0006-git-bundle-transport-no-vm-credentials.md),
  [0007](../docs/adr/0007-prune-audit-signal-discipline.md).
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
