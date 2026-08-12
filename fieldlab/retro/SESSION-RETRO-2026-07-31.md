# Session retro — 2026-07-31 (six walls and the pair)

## One-line

**C8 closed** — the acceptance pair ran clean after a single evening receipted and fixed six wall
classes plus one calibration, one named defect per failed run, none of them gameplay-boundary
defects.

## What this session was

A closure session that turned into the campaign's densest diagnosis run. The plan was: build the
residue-cleanup verb, sweep the world, sync the fleet, run full36+full37, document. Reality: the
residue hypothesis was falsified by the first clean-substrate failure, and the road to the pair went
through six distinct defects — three protocol, one concurrency-shaped, one environmental, one
calibration — each closed from receipts and decompiled source before the next run launched. Derek
reset the doctrine mid-session (disposable substrate; real engineering over rerun-and-pray; stop
when guessing) and the cadence after that reset is the thing this retro is really about.

## What shipped

| Commit | What |
| --- | --- |
| `6274392` | `cutoverResidueCleanup` runtime-control verb; orchestrator sweeps on every exit |
| `2303811` | World residue swept; 0.5.45 hash-verified on all three machines |
| `35b6bc7` | Wall 11 root-caused: restart-staled zone bank; TerrainComp/missing-object instrumentation; terrain-compiler dedup |
| `8e58390` | Wall 12a: observe verdict accepts idempotent receipt-snapshot arrival |
| `4be99eb` | Wall 12b: drive actually delivers its receipt-required body; verdict stops testing bank warmth |
| `db1bc68` | Wall 14: ownership control frames bypass the bulk outbound cap |
| `c0db122` | Wall 15: local teleports announce on the reliable resync lane; Gateway accepts `local_teleport` |
| `ff11e76` | Wall 13 closed from a live hang dump: QuickEdit console freeze; consoles disabled; runbook precondition |
| `09340ee` | Portal roundtrip budget recalibrated from the decompiled vanilla teleport contract |
| `ecfe278` | C8 complete — acceptance pair full44+full45 retained with full machine verdicts |
| `913a361` | Post-C8 replan, C8 evidence directory, plan status + landscape refresh |

New durable artifacts: `fieldlab/evidence/c8-native-zero-composition/` (README + gate-summary +
sweep receipt), the mandatory post-C8 replan in the master plan, two memory files
(restart-stales-bank; stop-when-guessing), and the stall-watchdog pattern (scratchpad tooling,
procdump + WinDbg lineage).

## Timeline

The session opened on the residue plan: verb built and landed, world swept — and the sweep receipt
immediately complicated the story (the restart had already cleared the non-persistent probes; only
five persistent stragglers existed). full36 then failed identically on the clean substrate,
falsifying the leak hypothesis. Decompiling `TerrainComp.Awake`, `ZNetScene.Destroy`, and
`IsAreaReady` with ilspycmd, plus a server-side dedup receipt proving the world held one compiler
per zone, pinned wall 11: the canonical zone bank keys on the world-stable epoch while ZDO ids are
session-scoped, so a server restart replays phantom uids and vanilla's duplicate-removal livelocks
spawn readiness. The WAL wipe unblocked bootstrap; full37 and full38 then each exposed one journal
protocol defect (a verdict blind to idempotent arrival; a receipt-required delivery that was built
but never enqueued — the check had been passing on bank warmth). full39 froze the whole client;
full40 starved a lease reissue grant at the bulk queue cap during a post-resume re-publish flood
(sequences 877→2639 in three seconds); full41 held a remote at 87 meters because a legitimate
teleport had no legal channel past the fail-closed 30m guard. The watchdog + procdump caught
full42's freeze live, and WinDbg read it in one look: the main thread blocked in the console
`WriteFile` — Windows QuickEdit, environmental, consoles now disabled. full43 failed a portal
return leg 0.2 seconds after its area went ready — pure deadline calibration, rebudgeted from the
decompiled contract. full44 and full45 then ran the complete composition clean, back to back, and
C8 closed with every machine verdict green.

## The team retro — our collaboration across the seats

**Architect** — The design calls were pragmatic, particularly bounding the phantom-uid blast radius
to exactly two load-time sites (TerrainComp, SmokeSpawner) via a full-assembly sweep rather than
rushing the session-scoped epoch rework at midnight; that structural debt is deferred to C10 under
an explicit operational rule (wipe the WAL after any server restart), which is honest but will not
survive contact with P7 — the replan names it a hard C10 precondition. The wall-14 fix kept one
queue and exempted control frames from the bulk cap rather than adding a priority queue, trading a
bounded overshoot for intact reliable-sequence ordering — the right trade. The one misallocation:
we built cleanup orchestration for a leak that turned out to be coincidental, though the verb earned
its keep as steady-state hygiene (destroyed=0 receipts on clean runs) and as the dedup instrument
that falsified its own founding hypothesis.

**Implementer** — Eleven commits, each building clean with 102/102 golden tests and the roadmap
ceremony, no rework within the session. The code fought us where silent assumptions lived: the
drive protocol was theoretically complete but literally never enqueued its valid delivery, masked
entirely by warm-bank replay; the observe verdict encoded an ordering assumption nobody had
written down. The turning point was tooling: the TerrainComp identity logger and named
missing-objects receipts turned "spawn flake" into uids and owners; the watchdog + procdump +
WinDbg chain turned "intermittent freeze" into one decisive stack trace.

**Reviewer / QA** — The posture shifted from speculation to proof after Derek's mid-session
directive, and the receipts show it: every wall was confirmed against decompiled vanilla source or
a dump before its fix landed, and the falsified leak hypothesis was retired by a controlled
clean-substrate run rather than argument. What slipped: the leak explanation was allowed to stand
as the blocking cause for most of a day before anything falsified it, and the watchdog shipped
with a launch-gap false positive that cost a spurious 3.7GB dump (deleted; design gap noted).
The machine gates (coverage 20/20, composition summary, save integrity) held their line all night —
no verdict was weakened to make a run pass; two verdicts were corrected because they were provably
testing the wrong thing.

**Operator / SRE** — Four AM4 restarts, each followed by the WAL wipe per the new rule; fleet
deploys hash-verified on all three machines every cycle; the i5 lane stayed up all session. The
consoles are now disabled on both clients as a runbook precondition — the freeze vector was
environmental (a streamed desktop's stray click), not netcode. Two approved tool downloads
(procdump, WinDbg) now live on OMEN for future dump work. Derek's disposability call mattered
operationally: no time was spent preserving world state, and the cold-storage zip remains the
reset path.

**Product / planning** — We built the right thing and stopped at the right line: C8 closed with
forward-looking docs only, C0–C6 evidence backfill explicitly deferred, C9/C10 written as a plan
rather than started at 2am. Derek's pacing interventions were the session's rudder — the
disposability call killed a substrate-polishing detour, and the engineering-doctrine reset changed
the cost curve: before it, full36 was nearly a rerun; after it, every run was instrumented and no
run was wasted. Eight failed runs bought exactly eight named defects (six walls, one calibration,
one secondary), which is the harness working as designed.

## Two seats, two views

**From Claude's seat** — The best move of the session was adopting the stop-when-guessing rule as
a hard gate and then being held to it: the two moments I was closest to launching a hope-based
rerun (after full36 and after full39), the rule forced instrumentation instead, and both times the
instrumentation found something a rerun never would have. I over-reached once — asserting the
pipe-full theory for wall 13 before the dump existed; the dump proved the *shape* right (blocked
WriteFile) but the *cause* was QuickEdit, not a stalled reader, and I should have said "blocked
writer, cause unknown" until the stack was on screen. Under-reached once: I treated the
authoritative-consumer noise as ambient for hours before disabling it; hygiene debt is cheapest at
first sight. What I want next time is the flight-recorder reducer — per-second queue depth by frame
type from the session events — which would have made wall 14 a one-glance diagnosis.

**From Derek's seat** *(my reconstruction, to be corrected)* — The night validated the harness
thesis: the observability we spent days building is what let eight failures cost one run each. The
corrections I had to make were about posture, not substance — Claude was polishing disposable
dirt and starting to grope after full39, and both course-corrections took one message. The
decompile-first and dump-first work is exactly what "real engineering" meant; the QuickEdit find
in particular is the kind of thing brute force would never have caught. The thing to watch: the
session ran long and hot, and the pair landed at the end of an eleven-commit night — the C9/C10
line held, but that discipline needs to be structural, not adrenaline-dependent.

## Last time's lessons — follow-through

| Lesson | Status | Note |
| --- | --- | --- |
| `L-2026-07-30-1` gate-vs-artifact first | acted-on | Walls 12a/12b were exactly this: the verdict was wrong, not the run |
| `L-2026-07-30-2` no silent skips | pending | P7 boot lane untouched this session; lands with C10 |
| `L-2026-07-30-3` "verified" names what was exercised | acted-on | gate-summary carries explicit verified/inferred/unverified sets |
| `L-2026-07-30-4` cross-cutting hazard, cross-cutting mechanism | acted-on | Residue cleanup rides the orchestrator path; teleport resync rides the protocol |
| `L-2026-07-30-5` check the instrument first | acted-on | The dedup receipt falsified the leak hypothesis before further remediation |
| `L-2026-07-30-6` status docs mark verification | acted-on | Evidence README/gate-summary state the unverified set explicitly |

## Lessons learned

1. **`L-2026-07-31-1` — A console window is an availability hazard on any machine a human can
   touch.** QuickEdit selection blocks the console `WriteFile` on the writer's thread
   indefinitely; on Unity that is the main thread and the whole client. Automated runbooks keep
   consoles disabled. → **doc** (runbook precondition, landed).
2. **`L-2026-07-31-2` — Warm state masks dead lanes.** The drive's valid delivery was never sent
   and its verdict passed for days on bank-warmth replay. Critical paths get verified against a
   cold cache at least once. → **practice.**
3. **`L-2026-07-31-3` — Session-scoped identifiers must not outlive their session in any banked
   state.** ZDO uids are reassigned per server boot; a bank keyed only on world identity replays
   phantoms. The epoch contract must incorporate session identity. → **ADR**
   ([0016](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/adr/0016-banked-state-must-carry-session-identity.md)).
4. **`L-2026-07-31-4` — Falsify on pristine substrate before building remediation.** The leak was
   real, observable, and coincidental; one clean-zone failure disproved it in ten minutes after a
   day of belief. → **practice.**
5. **`L-2026-07-31-5` — Decompile the contract instead of guessing the budget.** The portal
   deadline, the respawn gate, and the duplicate-removal semantics all came straight from
   ilspycmd in minutes and each ended a guessing loop. → **memory** (folded into
   stop-when-guessing-propose-tooling).
6. **`L-2026-07-31-6` — Control-plane frames never share a bulk-data cap.** A bounded queue that
   rejects a lease grant during a re-publish flood is a priority inversion; exempt control
   frames or give them a lane, but never let payload volume starve protocol progress. →
   **practice** (fix landed; generalizes to every bounded queue in the stack).
7. **`L-2026-07-31-7` — One instrumented failure beats N hopeful reruns.** Eight failed runs,
   eight named defects, zero repeated failures. The cadence requires the stop-when-guessing gate
   and observability worth reading. → **memory** (stop-when-guessing-propose-tooling, landed).

## Provenance

Git range `2144935..913a361` on `baseline` — 11 authored commits, all lived this session. Timeline,
seat first-passes, and lesson candidates drafted by `gcp-gemini` (gemini-3.5-flash, 1,467 tokens
out); **edit_verdict: minor-fixes** (queue-fix mechanics, "telemetry" misattribution, and an
OMEN-as-VM slip corrected against receipts; structure and voice kept). Two seats-views, the
follow-through table, ADR wording, and all repo-coherent docs frontier. No `--fleet` second
opinion dispatched. Tool downloads this session (both Derek-approved): Sysinternals procdump,
Microsoft WinDbg via winget. Derek's seat is a reconstruction, marked as such.
