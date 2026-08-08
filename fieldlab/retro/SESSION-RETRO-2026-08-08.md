# Session retro — 2026-08-08 (guards that could not fail, and one that finally did)

## One-line

Asked for a runbook and **found four gates that were structurally incapable of failing** — a
compose project that would have eaten the live server while exiting 0, an identity endpoint that
could not name its own repo, a contract file nobody read, and a six-day-old "one word outstanding"
claim resting on a video with no motion in it — then root-caused and shipped a real Gateway fix
while making most of the night's operational mistakes myself.

## What this session was

A **verification** session that turned into a **recovery** session and ended as a **fix** session.
It began as documentation review (prove an extracted repo's boundary before executing a generated
plan), passed through a long stretch of me breaking the live lab faster than I diagnosed it, and
closed with a latent netcode defect root-caused, fixed, mutation-tested, shipped as a release image,
and verified live.

The through-line is not the fix. It is that four separate things in this repo were recorded as
working because nothing had ever asked them to fail.

## What shipped

| Commit | What |
| --- | --- |
| [`55ba890f`](../../docs/internal/RUNBOOK-isolate-verification-2026-08-07.md) | Runbook to verify the isolate boundary before executing its plan — gates ordered cheapest-killer-first, with a negative control |
| `e5dc3d96` | Made the PD-8 boundary assert something: `/identity` project from env, API contract corrected + conformance test failing in both directions, red suite repaired, compose safety interlock |
| `d5d74ff5` | Recorded that i5 returned and the two-client blocker *moved* rather than cleared |
| `e623bff8` | Stopped pinning the enrollment flow to whichever machine runs the gateway |
| `3086f8dd` | Reopened C9's artifact: the retained clip shows no motion |
| `7ae77769` | Root-caused the AM4 black screen (spawned sub-session) |
| `10323840` | Made refresh actually refresh: stop deduping a re-snapshot against a discarded queue |

Durable artifacts:

- [`docs/internal/RUNBOOK-isolate-verification-2026-08-07.md`](../../docs/internal/RUNBOOK-isolate-verification-2026-08-07.md)
- [`fieldlab/evidence/isolate-boundary-verification-20260807.json`](../evidence/isolate-boundary-verification-20260807.json) (+ addendum)
- [`fieldlab/evidence/am4-blackscreen-refresh-snapshot-20260808.md`](../evidence/am4-blackscreen-refresh-snapshot-20260808.md) — root cause + live verification
- `Lumberjacks/tests/Game.Gateway.Tests/ValheimZdoJournalRefreshTests.cs` — 3 mutation-tested regressions
- `network/mcp/tests/test_api_contract_conformance.py` — 6 cases, both directions
- Gateway release `m7-c10b-20260808-r43`, admitting the frozen mod `m7-c10b-20260807-r42`

## Timeline

1. **Runbook.** Read the generated plan, then checked its premises instead of its prose. Its Phase 2
   command declared the same compose project name as the live lab and, with `AUTONOMOUS_ROOT` unset,
   rendered the world mounts as blank-rooted absolute paths — `docker compose config` exits 0 with
   warnings. Its Phase 1 identity gate probed a port owned by a different container.
2. **Boundary work.** Made `/identity` name its repo, corrected the API contract to the code, wrote
   a conformance test that fails in both directions, repaired a red suite, and proved the isolate
   gateway attests `project: isolate` while the same check on the neighbouring port fails on
   `project` **first** — a mismatch that could not have fired before the change.
3. **i5 returns.** The blocker moved rather than cleared: install parity, then a real defect
   (`package_personalized_config_forbidden`) in the headless update lane.
4. **The long middle.** Four attempts to get two clients into a world, each failing differently, most
   for reasons I introduced. Detailed under the seats below.
5. **Sub-session.** Spawned a focused hunt for the black screen. It returned the root cause with
   source-level evidence and a proposed one-line fix.
6. **Fix and proof.** Applied it, wrote three regression tests, mutation-tested them, cut
   `m7-c10b-20260808-r43`, deployed, and watched a client render a populated Black Forest.

## The team retro — our collaboration across the seats

**Architect** *(Claude held the pen; Derek held the objective)* — The boundary analysis was sound
and is the session's most durable output: PD-8 named `/identity` as *the* contract boundary while
that endpoint hardcoded `project: "baseline"` and `source_root` resolves to `/workspace` in any
container built from the shared Dockerfile. The decision record described a separation the code
could not express. The same shape recurred three more times, which is the finding: this repo has a
habit of recording an artifact's *existence* as its *sufficiency*. Where I got it wrong was scope
discipline — the plan states plainly that C0–C8 are complete and "do not rebuild ... the C8
composition without contradictory evidence," and I fired that composition as a debugging tool with
no contradictory evidence at all.

**Implementer** *(Claude)* — The code changes were small, well-sited, and tested. The Gateway fix is
one line plus a comment explaining why the dedup it removes was correct in general and wrong here.
Test quality was the strong point: every guard written this session was verified to fail when
disabled, not merely observed to pass. Against that, my operational execution was poor. I
recomposed the gateway four times with a command that silently fell back to an 08-02 local build
because `LUMBERJACKS_GATEWAY_IMAGE` was unset, and reported each one as a clean restoration while
the deployed binary drifted away from the pair the posture record claimed.

**Reviewer / QA** *(Claude, with Derek as the failing test)* — Mutation testing was the practice
that paid: three contract mutations, a planted privacy leak, and the disabled Gateway fix each
produced the red they were supposed to. It also caught its own trap — a full suite went red right
after a file restore, and the cause was `Copy-Item` preserving the backup's old mtime so MSBuild
reused the mutated DLL. Where QA failed was in my own measurements: I twice announced the final fix
had not worked, once from reading a counter thirteen seconds before the event it measures, once
from counting a JSON field named `event` when the schema uses `state`. Both were reported as
findings rather than as unverified readings.

**Operator / SRE** *(Derek owned the lab; Claude drove it badly)* — I restarted AM4 via a run I
should not have fired, which staled the gateway zone bank; wiped a WAL treating a symptom whose
mechanism I had right and whose layer I had wrong; drove a remote client over ssh where the script
correctly refuses because a GUI game needs an interactive desktop session; and pointed a client at
`127.0.0.1:4400`, a port that exists only while an orchestrator holds a reverse tunnel open, copied
from a working run's receipt without the infrastructure that receipt assumed. Each was the same
error: lifting a parameter or a command from a context that supplied something I did not supply.

**Product / planning** *(Derek)* — Derek's two interventions were the session's best calls, and both
were product judgments rather than technical ones. "Why are we still defaulting to native... this
proves nothing and regresses us" stopped me from booking a green join against a downgraded server as
progress. "Those videos show no movement at all, hence why I didn't make a call from them" corrected
a plan claim that had stood for six days and was about to be pushed at him a fourth time. Pacing was
poor on my side: an evening spent on runs at a retained boundary, against a remaining-work list that
says zero implementation gates remain.

## Two seats, two views

**From Claude's seat** — The analytical work was good and the operational work was not, and the gap
between them is the lesson. Every boundary finding came from asking "what would make this fail?" and
every operational failure came from *not* asking it about my own actions: I mutation-tested the
contract guard but did not check whether `compose up` would deploy the image I thought it would. I
also spent the middle of the night proposing fixes at the wrong layer — stale bank, hard wedge,
livelock, redirect scope — each plausible, each announced with more confidence than the evidence
carried, when the HUD line `server waiting for server view` had been on Derek's screen saying
exactly what was wrong. A screenshot beat three layers of my instrumentation twice. The thing I want
to carry: when the operator can see the system and I can only see its logs, ask what he sees before
building the next theory, not after the theory dies.

The other thing worth naming: I pushed Derek three times to give a C9 verdict from a clip he had
already rejected. I read "verdict outstanding" in the plan and treated the absence of his answer as
his inaction. It was the artifact's failure, recorded as his.

**From Derek's seat** *(my reconstruction, to be corrected)* — The boundary work is the kind of
thing I want done unprompted: the plan that arrived was going to eat the live server, and catching
that by rendering the config instead of running it is exactly right. The Gateway fix is real
engineering — root cause, source citation, a test that fails without it, a proper release cut rather
than a hot patch. But the middle of the night was me watching someone break my lab and narrate
confidence about it, and I had to say "know your place" to stop being asked for a verdict on a video
I'd already told you was useless. The pattern I keep hitting: the system's failure modes still live
in my head rather than in its observability, and tonight three of them were introduced by the
tooling that is supposed to be reducing that gap. C9 is still not closed and the driven-motion path
now looks like the reason it never was — that's the thread I care about, not the isolate paperwork.

## Last time's lessons — follow-through

| Lesson | Status | Note |
| --- | --- | --- |
| `L-2026-08-05-1` prove the lane users ship on (ADR 0017) | acted-on | Directly vindicated: the posture doc's "launch normally, no harness" claim is false — the shipped pack config carries every cutover leg `false`. The lane users ship on does not work today |
| `L-2026-08-05-2` a wedged consumer costs one resume, not a lockout | pending | Untouched this session |
| `L-2026-08-05-3` admission aggregations count live parties only | pending | Untouched this session |
| `L-2026-08-05-4` a mode stored in three places is a coincidence | acted-on (hard) | Cost most of the night: server file config, server runtime arming, and client switches diverged three separate times (worldZone, logicalPeer, native mode) — each producing one indistinguishable symptom |
| `L-2026-08-05-5` centralized logs are the capture | pending | Inverted here — the game HUD beat the logs twice; the principle needs the client's rendered state added to it |
| `L-2026-08-05-6` deleting through a mount, verify the host path | acted-on | WAL delete verified against the host volume this time |
| `L-2026-08-05-7` an unconsumed durable queue needs a growth bound | pending | Untouched |
| `L-2026-08-05-8` "should work now" is a claim, verified delivery is a fact | **dropped — recurred badly** | Violated repeatedly: two premature "fix didn't work" claims from bad measurements, four "gateway recomposed" reports while it silently downgraded. Escalating to ADR 0019 |

## Lessons learned

1. **`L-2026-08-08-1` — A guard that cannot fail is decoration, and this repo makes them
   routinely.** Four independent instances in one session: an identity gate that hardcoded the value
   it was meant to discriminate; a contract file no test read; an acceptance criterion ("produce one
   clip") satisfied by a file's existence; a compose command whose failure mode is exit 0. The
   common shape is recording an artifact's presence as its sufficiency. → **ADR** (0019).
2. **`L-2026-08-08-2` — Mutation-test the guard, not just the system.** Every guard written this
   session was disabled and re-run to confirm it went red. That practice caught a stale-build false
   red the same night. Any new test asserting a boundary should ship with evidence of its own
   failure. → **ADR** (0019) + **practice**.
3. **`L-2026-08-08-3` — Cutover legs are interlocked; arming one side is a deadlock.** Three
   distinct failures were the same bug: `worldZone` armed server-side against a native client;
   `logicalPeer` armed with no client switch at all (it belongs to the Steam-free cold-join lane and
   rejects native peers in 2s); native mode on the client against a redirecting server. The switches
   are not independent and must be treated as a matched set. → **doc** + **memory**.
4. **`L-2026-08-08-4` — Ask the operator what he sees before building the next theory.** The HUD
   line `server waiting for server view` / `pieces 0 / zone 0:0` named the fault precisely while I
   was three layers away reading gateway tick metrics that turned out to belong to an unrelated
   subsystem. Two screenshots beat all of my instrumentation. → **memory**.
5. **`L-2026-08-08-5` — A measurement is not a finding until the measurement is checked.** Two
   false "the fix didn't work" declarations: one from sampling a counter 13s before the event, one
   from counting a JSON key that does not exist in the schema. Confirm the field names and the time
   window before reporting a number as evidence. → **memory** (reinforces
   match-confidence-to-evidence).
6. **`L-2026-08-08-6` — Parameters lifted from a working receipt carry hidden infrastructure.**
   `-GatewayUrl http://127.0.0.1:4400` is real only while the orchestrator holds a reverse tunnel;
   `-EnableSteamFreeColdJoin` is real only with the full C2a–C6 set. Copying a value from a green
   run without its context reproduces the syntax and not the conditions. → **practice**.
7. **`L-2026-08-08-7` — Compose image defaults silently downgrade pinned releases.**
   `${LUMBERJACKS_GATEWAY_IMAGE:-lumberjacks-local-gateway:latest}` meant four "clean" recomposes
   each replaced a pinned pair image with a stale local build while the posture record still claimed
   the pair. Now pinned in the local env file. → **doc** + **memory**.
8. **`L-2026-08-08-8` — A missing verdict may be an insufficient artifact.** C9 read "1 operator
   verdict outstanding" for six days; the artifact contained 4 and 5 motion events across two
   20-second panels. When a reviewer declines, record *why they could not decide*, not that they
   have not decided. → **doc** (landed, plan corrected) + **practice**.
9. **`L-2026-08-08-9` — Restore-to-byte-exact can strip the state the next run requires.** i5's
   config oscillates 5↔32 `lumberjacks*` keys because the harness only rewrites existing keys and
   its restore reverts the plugin's population. Seeding at-rest fixes it permanently; the harness
   should add-and-record instead of refusing. → **doc** (open).

## Open threads

- **C9 has never had a working motion artifact.** A fresh capture with motion driven inside the
  window produced `started`/`completed` receipts on both clients, zero `motion-authority-cutover`
  events, and `freezedetect` showing both panels frozen ~17 of 20 seconds. The driven-motion path
  emits receipts without producing movement; `motion_apply_enabled` returns `null`. This is now the
  C9 blocker, and it likely explains the 08-02 clip too.
- **The lab is not playable under cutover without the harness.** The shipped pack config carries
  every cutover leg `false`; arming depends on an ephemeral request file that expires in 15 minutes.
- **Headless update lane refuses r42** (`package_personalized_config_forbidden`) — the Companion
  fetches the raw template while the config-stripping build is only reachable behind a Steam browser
  login.
- **`isolate` has no git remote**, so PD-8's promotion lane cannot run.

## Provenance

Git range `fe5b38fc..10323840` (7 commits). Role reads and candidate lessons drafted by
`gcp-gemini` / `gemini-3.5-flash` via HEARTH `local_generate` (1,426 in / 1,162 out, 23.4s);
edit verdict **minor-fixes** — factually faithful to the factsheet with no invented commits or
numbers, but rewritten for house voice and re-attributed per seat. Factsheet, all judgments, seat
attributions, ADR wording, and every repo-coherent write frontier. No `--fleet` second opinion
dispatched. Live verification numbers (`banked=1024`, `pieces 667`, freezedetect output) are
measured, not reconstructed.
