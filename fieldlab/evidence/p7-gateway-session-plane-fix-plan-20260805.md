# Gateway session-plane fix plan — 2026-08-05

Derived from the candidate 8/9/10/11 evidence and the 2026-08-05 live outage.
Every defect below has a receipt in this repo or in Cloud Logging for
`lumberjacks-exp-20260711-djc`; none is speculative.

## Evidence base (what happened, in one paragraph)

Candidates 8 and 11 failed identically at `c8-ownership-contended`: after the
mid-scenario Gateway restart, the reconnected i5 peer receives the full journal
redelivery (~1,643 objects), its gateway→client reliable delivery wedges (zero
ACK progress for 58s; `reliable_send_queue_full` thrown from the motion-resync
publish path), the contention success frame sits undeliverable, and ~53s in the
client abandons the socket and enters a reconnect storm the Gateway answers
with "Resume token invalid/expired, new session" every ~600ms. Candidate 9 was
that same storm left over from candidate 8's zombie. Separately, the 2026-08-05
human session starved because candidate 11's leftover runtime arming kept the
server in `lumberjacks-primary` while the replayed journal's dead recipient
interests made window completeness permanently false → heartbeat 409 →
no admission, no descriptor, no delivery.

## Fixes, in priority order

### 1. Resume must succeed against a zombie session (alpha blocker)

`GameSession`/`SessionManager`: a well-formed resume token that names a session
the Gateway still holds must EVICT the zombie — abort its socket, carry the
reliable state (pending frames, sequences) into the new connection, increment
the resume epoch — and succeed. Today the token is refused and the client loops
forever. Mod side of the same contract: after K refused resume attempts
(suggest K=3 with backoff), accept reincarnation — fresh session plus full
resync — instead of retrying indefinitely. Either half alone ends the livelock;
do both.

### 2. Gateway-side stalled-session abort (alpha blocker)

Mirror of the mod's 5-second send guard. Per session: if pending count > 0 and
no ACK progress for N seconds (suggest N=10), abort the socket and mark the
session resumable. This converts a wedged WAN consumer from "holds its logical
peer hostage indefinitely" into "one reconnect+resume". Also fixes the fault-
isolation bug: `HandleValheimMotionResyncPublishAsync` (MessageRouter.cs:647)
must degrade per-recipient on `reliable_send_queue_full` — skip that recipient,
like `SendPendingZdoDeliveriesAsync` already does — never throw into the
publisher's processing loop.

### 3. Pace post-restart journal redelivery (trigger amplifier)

Redelivery currently refills to the 224-frame headroom as fast as ACKs allow,
and bulk frames queue FIFO ahead of control frames. Two changes:
(a) cap in-flight unACKed deliveries per peer (suggest 32–64) so a slow client
is never buried; (b) give control frames (ownership, session, heartbeat-adjacent)
a reserved lane or strict priority over bulk ZDO delivery in the send path, so
a full bulk backlog cannot starve a 200-byte rejection. The 527–790ms contend.1
RTTs prove the control path is fine when it isn't queued behind bulk.

### 4. Recipient partitions need owner-liveness (the 409 family)

Third sighting of "durable session-plane state outlives the sessions it
describes": the AM4 zone bank, the replayed journal interests, and now window
completeness. On journal replay, mark restored recipient interests provisional
and drop them if the peer does not re-attach within a TTL (suggest 60s).
`ValheimTelemetryHeartbeatService` window-completeness aggregation must only
count partitions whose consumer is live per the session manager. A dead
partition must never permanently veto `lumberjacks-primary` admission — that is
what starved the human session.

### 5. Declarative cutover mode (operational)

Runtime arming is per-run and in-memory: candidate 11's abort left the server
in `lumberjacks-primary`; the container restart silently dropped it to native.
Both transitions were invisible until players saw an empty world. Make the
play-mode intent declarative (compose env or persisted operator setting), have
the mod log the effective mode at boot at Warning level, and extend
`/live/valheim-cutover` (or a sibling) to always report effective mode +
admission state + last heartbeat verdict so "server up but not admitted" is
one curl away. Add the recovery drill to the P7 runbook.

## Verification plan

- Unit: send-lane priority ordering; stall-detector state machine; resume-evict
  semantics including reliable-state carryover; provisional-interest TTL expiry.
- Local physical repro BEFORE P7 (local-loops rule): add a harness throttle
  (client-side apply delay or shaped socket) so the redelivery wedge reproduces
  on the AM4 loop without WAN. Today the only repro needs GCP; that is a gap.
  Acceptance: with the throttle on, unfixed code reproduces the candidate-8
  signature; fixed code completes contention through a wedge+resume cycle.
- P7: cut candidate pair r42+ via New-GatewayReleaseCut (candidate stage),
  promote with the boot receipt (fresh one if the VM restarts), run candidate 12.
  The recalibrated 45s restart-resume budget (commit 69aa3d0) stays.
- The scenario itself needs no changes for fixes 1–4; it is exactly the test
  that catches them.

## Addendum — the 2026-08-05 human session (added same day)

The first human 2-player session surfaced a sixth finding that outranks the
original five in alpha order, plus a baseline and an operational hazard.

### 6. Enrollment-lane end-to-end proof is the real alpha gate

P7 has three delivery lanes: native vanilla sync; the enrollment consumer lane
(server primary-redirect into the authoritative window, drained by ENROLLED
consumers — what every real tester runs via the personalized mod-zip, and what
July's sessions ran); and the harness journal lane (canonical session +
private-plane runtime arming — what every candidate proof runs). The candidate
proof therefore validates a lane no alpha tester will ever use, and the lane
they will use has never been exercised on P7 by the new stack: the lab clients
connected sessions but attached as consumers never (`active_consumers: 0`,
4,421 receipts pending, applied 0), because consumer attach on P7's
credentialed public plane requires enrollment keys the lab configs lack (AM4's
uncredentialed local gateway hides this entirely). Required proof: start from a
fresh self-service mod-zip enrollment, end with a physically verified visible
world and co-presence. That proof, not candidate 12, is the alpha gate.

### Unbounded WAL growth on unconsumed windows

With 100% redirect and zero consumers, `redirect.wal` reached 1,002 MB on the
32 GB state disk in one evening. Deleted 2026-08-05 with the stack stopped
(with `journal.jsonl`, per the wipe-after-restart doctrine; disk back to 64%).
Gateway fix: bound unconsumed-window growth (size or age cap + shed-and-log);
a misconfigured or consumer-less deploy must degrade, not fill the disk.

### Motion baseline (C9 human verdict, partial)

2026-08-05, P7 WAN (us-west1), vanilla native sync, mod in observe mode:
verdict **smooth** (Derek). This baselines the pipe — WAN latency to GCP is not
a limiting factor — and sets the felt reference the armed cutover motion path
must match. The C9 human verdict for the Lumberjacks-owned motion path remains
open; run it on the armed lane after the r42 fixes.

### Config state left on P7

`zdoRedirectEnabled = false` (native play mode) as of 2026-08-05; the armed
config is preserved at
`djcdevelopment.valheim.comfynetworksense.cfg.bak-20260805T1020Z` next to the
live cfg. Restore it deliberately for the next armed window. VM stopped,
status verified TERMINATED; the 08-05 boot receipt died with the shutdown —
the next harness window needs a fresh determinism proof.

## Scope notes

- Fixes 1–4 are Gateway-side; fix 1 also touches the mod's session resume
  policy (client half of the contract). Any mod change means a new coupled pair
  cut — plan for one pair, not piecemeal.
- Not in scope here: candidate 6's `plugin_disposed` at restart-resume (single
  sighting), per-species creature coverage, third physical client. Tracked in
  the cutover plan.
