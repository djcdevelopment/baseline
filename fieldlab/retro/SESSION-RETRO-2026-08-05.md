# Session retro — 2026-08-05 (three lanes and a smooth sail)

## One-line

**The harness went valid and the humans got in** — a fresh boot receipt, two candidate runs that
converted two mysteries into one named Gateway defect chain, a three-launch debugging ladder that
exposed P7's three delivery lanes, and the first human 2-player session on P7 ending in a "dannng,
that motion is smooth" baseline.

## What this session was

A recover-and-diagnose session wearing a play-session's clothes. The stated goal was small — start
P7, get two humans in when the i5 finished charging — and the sub-goal "run harness again so it's
valid" was supposed to be ceremony. Instead the candidate reruns root-caused the 08-03 failures
(refuting both prior theories, mine and a subagent's), and the human session then failed three
different ways, each a *different* configuration stratum of the same architectural fact: P7 has
three ZDO delivery lanes with three different auth stories, and nothing declares which one anybody
is on. Derek supplied the two hypotheses that cracked it — the partition-completeness 409 and the
credentialed-plane delta AM4 bypasses — and the session closed with humans playing on native sync,
a landed fix plan, and a shutdown that also cleaned a 1 GB WAL nobody knew was growing.

## What shipped

| Commit | What |
| --- | --- |
| `69aa3d0` | C8 `gateway-restart-resume` deadline 20s→45s for remote topology; validated same session by candidate 11 passing at 22.8s |
| `57331a3` | Gateway session-plane fix plan: resume-evict, stalled-session abort, paced redelivery + control-frame priority, partition owner-liveness, declarative cutover mode |
| `9a19b54` | Addendum: enrollment-lane proof as the alpha gate, WAL growth bound, smooth motion baseline, P7 config state |

New durable artifacts beyond the commits: a fresh green boot-determinism receipt
(`p7-boot-20260805-085953`, died with the shutdown as designed), candidates 10 and 11 with full
evidence trees, `fieldlab/evidence/p7-gateway-session-plane-fix-plan-20260805.md`, ADR 0017 (this
retro), and three memory files (resume-livelock blocker, three-delivery-lanes, plus index updates).

## Timeline

The session opened with an alpha-distance assessment of the 24-hour agent build, grounded against
the 08-03 findings doc: AM4 close, P7 one proven-but-fragile step away, with the human playtest and
N≥3 clients as the real gaps. When both machines came up, the receipt chain was rebuilt properly —
stack stopped, save orphan removed, VM to TERMINATED, and the boot-determinism proof rerun end to
end (cold cycle, injected systemd failure, all checks green, receipt bound to the new boot id).
Candidate 10 then failed at `gateway-restart-resume`, and the step's full history showed a
calibration miss, not a defect: ~8s of IAP SSH restart latency inside a 20s budget tuned on a LAN
where the same command costs one; the deadline went to 45s with the mod's 300s ceiling confirmed
first. Candidate 11 sailed through that step and then failed at ownership contention as an exact
replay of candidate 8 — same state, same reliable sequence 227 — killing the "rare transport flake"
theory in one run. Cloud Logging held what the truncated local capture didn't: the contend.2
rejection was queued behind an unpaced ~1,643-object journal redelivery, the WAN client's socket
wedged with zero ACK progress for 58 seconds while `reliable_send_queue_full` threw from the
motion-resync path, and the client's eventual reconnects livelocked on "Resume token
invalid/expired" every ~600ms — which also retroactively explained candidate 9 as candidate 8's
zombie. The human session then failed three ways in sequence: leftover candidate-11 runtime arming
plus my Gateway restart left dead replayed partitions vetoing the server's `lumberjacks-primary`
heartbeat with a 409 (Derek's "steamid partitions" call); after a Valheim restart dropped the
server to native mode, the clients still saw terrain because the lab at-rest configs keep the
Lumberjacks session disabled; with the session armed they dialed `localhost:4000`, the AM4 lab
gateway; and with the P7 URL passed explicitly the sessions finally connected — revealing
`active_consumers: 0` with 4,421 receipts pending, because consumer attach on P7's credentialed
public plane needs enrollment keys the lab machines have never held (Derek's "security AM4 would
bypass" call). The night's fix was honest: redirect off (config backed up), Valheim restarted,
vanilla sync served the world, both humans in, motion verdict smooth. Shutdown cleaned the save
orphan, deleted the 1,002 MB WAL and stale journal at the *host* path (the first delete hit the
container path and no-op'd), and verified TERMINATED.

## The team retro — our collaboration across the seats

**Architect** — The load-bearing discovery is structural: the candidate proof exercises the harness
journal lane, real testers ride the enrollment consumer lane, and the new stack has never exercised
that lane on P7 — a rigorously green validation suite pointed at a path production traffic will
never take. The fix plan's shape is right (session lifecycle first, pacing second, liveness third,
declarative mode now promoted by events to co-equal), and the deadline recalibration was correctly
scoped as harness data rather than an artifact change, preserving the promoted pair. The
misallocation: I spent the first hour of the outage on my own livelock theory when the server-side
`enabled=False` boot line was already in the log; Derek's config instinct got there first, twice.

**Implementer** — Small diff, high leverage: one deadline constant with the evidence comment
(matching the portal-budget precedent five lines below it), two documents, three memories. The
mod's 1–300s manifest bound was checked before touching the deadline, so the deployed pair stayed
exact. The hand-written `start` pending-request for the i5 scheduled task is a new operational
pattern worth keeping — the queued lane only knew `smoke`, and `run-pending` dispatching on the
request's `action` verbatim made a proper join-and-hold launch possible without code changes. Two
PowerShell 5.1 quoting failures and a `grep -v -o` self-cancellation cost real minutes mid-debug;
the Bash tool for Cloud Logging queries was the right escape and should be the default for quoted
filters.

**Reviewer / QA** — The session's best QA moment was distrusting a subagent: its probe-race theory
read plausibly, but the mod's retry loop was demonstrably response-driven-sound, and Cloud Logging
refuted the race outright — verify-the-verifier applied to our own tooling. The worst moment is a
habit: "the world should be visible now" was declared twice on launch-complete evidence before
delivery had ever been verified; the third launch was called done only on session-connected + bind
receipts, and even that missed the consumer gap until telemetry was read. Verification standard
going forward: a client is *in* when delivery is confirmed, not when it joins.

**Operator / SRE** — Clean hands all night on a hostile surface: every stop cleared its save
orphan, the WAL deletion was caught no-op'ing via an empty `ls` and redone at the real mount
source, config edits carried timestamped backups, and the VM ended verified TERMINATED. Cloud
Logging was the decisive instrument three times — the local `gateway-run.log` capture was two lines
— and the IAP stderr noise remains cosmetic but obscured real output all session. The boot-receipt
lifecycle worked exactly as designed twice (die with the boot id, regenerate by proof), which is
the receipt discipline paying rent.

**Product / planning** — The user's goal was achieved — the humans played, and the smooth verdict
banked the C9 baseline — but it took four client launches and a mode retreat to get there, and that
sequence *is* the product finding: onboarding friction that a paying-attention alpha tester would
experience as a bricked evening. The alpha gate moved accordingly, from "candidate 12 goes green"
to "a fresh mod-zip enrollment ends in a visible world," which is a better gate because it is the
user's actual first five minutes. Scope held well under pressure: no Gateway code was patched at
2am; fixes went into a plan with receipts instead.

## Two seats, two views

**From Claude's seat** — The candidate root-cause work was the session's high ground: my own prior
hypothesis (WAN deadline tuning) died on evidence I gathered myself, the subagent's theory died the
same way, and what replaced them is pinned to specific log lines and sequence numbers. Where I
underperformed was the human outage: I had three theories in sequence (livelock, retained config
flags, at-rest session config) and announced expected success after fixes one and two; Derek's two
domain instincts — partitions and credential planes — were both right before I got there, and the
`Authoritative consumer init: enabled=False` line that unlocked everything had been sitting in my
own earlier grep output. The lesson I want to carry: when an operator with two decades of
architecture instinct says "config, not code," check every config stratum *before* the next
relaunch, not between them. Also: I nearly treated the `ls` receipt as noise; reading it saved a
fake WAL cleanup.

**From Derek's seat** *(my reconstruction, to be corrected)* — The night proved the instrumentation
thesis again but in a mode I care about more: live, with players waiting. The candidate analysis
was real engineering — receipts, refuted theories, a plan instead of 2am patches — and the
calibration fix validating on its first run is how that loop should feel. But four launches to get
two people into a world I've seen work hundreds of times is the actual product lesson, and my
partitions/credentials calls landing first says the system's failure modes still live more in my
head than in its observability. The alpha gate landing on the mod-zip-to-visible-world path is the
right call — that's the only test that matters to a volunteer. Motion being smooth over the WAN
was the best surprise of the night; the pipe is not our problem.

## Last time's lessons — follow-through

| Lesson | Status | Note |
| --- | --- | --- |
| `L-2026-07-31-1` consoles disabled on run machines | acted-on | Held all session; no console incidents across four launches |
| `L-2026-07-31-2` warm state masks dead lanes | pending | Recurred at architecture scale — the proof lane is "warm" in the same sense; escalated into ADR 0017 |
| `L-2026-07-31-3` banked state carries session identity (ADR 0016) | pending | The Gateway journal replays recipient interests that outlive their sessions — the 409 is ADR 0016 unenforced on the Gateway; fix plan item 4 is its implementation |
| `L-2026-07-31-4` falsify on pristine substrate | acted-on | Candidate 11 on a fresh boot falsified the "transport flake" theory in one run |
| `L-2026-07-31-5` read the contract instead of guessing | acted-on | Scenario deadlines diffed against passing runs; mod manifest bounds checked before the calibration; Gateway source read before any theory survived |
| `L-2026-07-31-6` control frames never share a bulk cap | pending | The same inversion exists Gateway-side (contend rejection queued behind redelivery flood); fix plan item 3 |
| `L-2026-07-31-7` one instrumented failure beats N reruns | acted-on | Candidates 10 and 11 each named a defect; each client relaunch carried a receipt-backed hypothesis — though two of three also carried a premature success claim (see L-2026-08-05-8) |

## Lessons learned

1. **`L-2026-08-05-1` — Prove the lane users ship on.** The candidate proof exercises a
   runtime-armed harness lane; every real player rides the enrollment lane, which the new stack has
   never exercised on P7. A green proof on a lane production traffic never takes is a green light
   pointed at a wall. → **ADR**
   ([0017](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/adr/0017-prove-the-lane-users-ship-on.md)).
2. **`L-2026-08-05-2` — A wedged consumer must cost one resume, not a peer lockout.** No
   gateway-side stall abort plus resume-token refusal turned one stalled socket into an indefinite
   logical-peer lockout (candidates 8, 9, 11). → **doc** (fix plan items 1–2, landed).
3. **`L-2026-08-05-3` — Admission aggregations may only count live parties.** Dead replayed
   partitions vetoed the primary heartbeat forever; kin of ADR 0008 (liveness ≠ admission) and
   ADR 0016 (state outliving its session). → **doc** (fix plan item 4, landed).
4. **`L-2026-08-05-4` — A mode stored in three places is a coincidence, not a mode.** Server file
   config, server runtime arming, and per-client config each held part of "which lane are we on,"
   diverged silently, and produced one indistinguishable symptom. Effective mode must be
   declarative, logged at boot, and queryable. → **doc** (fix plan item 5) + **practice**.
5. **`L-2026-08-05-5` — Centralized structured logs are the capture; local files are a
   convenience.** Cloud Logging decided three root causes; the local gateway capture held two
   lines. Diagnose from the durable sink first. → **practice**.
6. **`L-2026-08-05-6` — Deleting through a mount, verify the host path.** The first WAL delete
   no-op'd against a container-only path; the empty `ls` receipt was the tell, and reading it was
   the save. → **practice**.
7. **`L-2026-08-05-7` — An unconsumed durable queue needs a growth bound.** 1,002 MB of WAL in one
   evening on a 32 GB disk, from a misconfiguration that produced no error anywhere. Shed and log,
   never grow silently. → **doc** (fix plan addendum, landed).
8. **`L-2026-08-05-8` — "Should work now" is a claim; verified delivery is a fact.** Two premature
   success declarations in the launch ladder; the standard is delivery confirmed at the consumer,
   not process started. Reinforces the calibration memory
   (match-confidence-to-evidence). → **memory** (existing, reinforced).

## Provenance

Git range `e13d0be..9a19b54` on `baseline` — 3 authored commits, all this session, plus this
retro's own commit. Timeline, seat first-passes, and lesson candidates drafted by `gcp-gemini`
(gemini-3.5-flash, 1,488 tokens out, no max_tokens cap per the truncation doctrine);
**edit_verdict: minor-fixes** (the draft conflated the candidate-8/11 contention failures with the
restart-resume deadline step and misordered the debugging arc; both corrected against receipts —
structure and several seat readings kept). Two seats-views, follow-through table, ADR wording, and
all repo-coherent docs frontier. No `--fleet` second opinion dispatched; none was pending from
07-31. Derek's seat is a reconstruction, marked as such. His two winning hypotheses and the smooth
motion verdict are quoted from the live session.
