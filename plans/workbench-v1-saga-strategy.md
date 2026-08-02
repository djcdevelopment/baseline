# Saga WB-1 — Ownable Docker Workbench v1

Status: engineering implementation and rendered machine-and-human acceptance
completed 2026-08-02, but product acceptance was reopened later that day after
the owner found that Home did not answer the basic live operator questions and
the useful existing Companion telemetry had been displaced to a secondary route.
M5 remains sealed. M2 and product closeout are candidate again pending observation
of the repaired Home; structural HTML and topology tests are no longer accepted as
evidence of operator value. The read-only Operate check, reversible
install/rollback drill, and peer-bearing player-active capture have clean local
receipts. WB-1 remains a candidate pending the declared unfamiliar-user usability
gate, tagged `TODO — Derek soon` rather than an active implementation blocker.
The player-active capture also identified a native-motion-only gap that the
subsequent PD-7 development loop has now closed. The follow-on audit found that it was
reproducible from two configuration/provenance facts: both rendered clients
were still pointed at the retired public Gateway endpoint while the local Lab
Gateway was healthy, and the active Valheim server container still carried the
retired `C:\work\comfy` compose provenance. Replanned after the
[MCP endpoint provenance audit](../docs/audit/2026-08-01-mcp-endpoint-provenance-audit.md).
The runtime choice is tracked in [PD-7](../docs/decisions/pd-7-lab-runtime-provenance-and-session-boundary.md)
and is a prerequisite for the next real-player/motion-authority window.
The short-term Baseline-compose/retained-state bridge was executed and the full
Baseline state-root migration has now passed strict provenance. The hardened
single-client background-execution check passed. The one clean,
watchdog-bearing diagnostic C6 then disproved the suspected persistent OMEN
stall: both ordinary motion directions passed and OMEN completed the gap drive.
The run failed because i5 applied the correlated reliable resync before its
`observe_gap` probe captured baseline counters. The existing C8 observer-alignment
step is now backported to C6 and guarded before remote mutation. The separately
authorized validation job `job-20260802-072520719-74b07483`, run
`workbench-20260802-072523-74b07483`, completed all 24 actions on both physical
clients. i5 began gap observation 4.92 seconds before OMEN began gap drive and
recorded one held gap plus one applied reliable resync. That closes the C6
ordering follow-up without changing the already sealed human acceptance.
Owner: Derek. This document is the decision-complete execution strategy for the
first coherent Workbench product slice.
Product rationale remains canonical in [PD-5](../docs/decisions/pd-5-local-workbench-ownership-appliance.md),
[PD-6](../docs/decisions/pd-6-development-mcp-lifecycle.md), and the
[Workbench operating model](../docs/workbench-operating-model.md).
The separate, ordered follow-on that converges the currently independent Compose
projects, ports, local/remote modes, and shipped tool surface is
[Workbench appliance convergence](workbench-appliance-convergence.md).

### 2026-08-02 operator-value recovery

The miss was specific and reproducible: `/` was changed from the telemetry-rich
Companion page to a Workbench shell whose Home emphasized repository topology and
durable jobs but did not directly say whether AM4 was up, who was online, whether
anything was executing, or what the runtime cutover/motion path was doing. The old
answers remained at `/companion`, so the implementation technically preserved the
route while removing its value from the primary experience. A static red Community
card also continued to say the full cutover was simply "NO" after C8 closed.

The recovery adds a first-class live-operation projection to Home, sourced from the
Gateway deployment, Valheim heartbeat, cutover, and motion endpoints plus Workbench
job state. Home now leads with server health/staleness, peer count and public player
names, actual machine activity versus finished `waiting_human` review, runtime
netcode counters, and one next action; it links the detailed Companion telemetry and
trace rather than hiding them. The Community card now states the actual C8/C9/C10
program boundary. Focused and full Docker tests pass, and the rebuilt Lab Workbench
serves the live projection. Owner observation on the clean committed image remains
the acceptance gate.

## Summary

Deliver a coherent Workbench v1 in one focused session: a locally owned,
loopback-only Docker appliance with safe initialization, typed capabilities,
durable jobs and receipts, a live system map, bounded host execution,
profile-scoped Dev MCP, recovery/export tooling, and a rendered AM4 + OMEN + i5
acceptance run. The replan adds an identity-first gate: no MCP-sensitive result
is accepted until the listener's source root, providers, profile, caller
registry, ledger, and port are machine-proven to belong to Baseline.

### Replan delta — endpoint provenance is now a first-class feature

The July 31/August 1 default MCP calls were served by an enabled
`ComfyGatewayBoot` task launching the retired `C:\work\comfy` checkout. Both
repo `.mcp.json` files targeted the same `:8720` URL, so the port was not an
identity boundary. HEARTH is separate on `:8710`; the current safe forward path
was to use explicit Baseline Dev MCP port `:8721`, leave the unknown `:8720`
owner untouched during audit, quarantine default-port evidence, and only then
rerun MCP-sensitive checks. After identity passed, Derek authorized recoverable
retirement: the stale task was disabled without deletion and its audited process
stopped. This is a provenance correction, not a claim that every historical
result is functionally false.

### Chosen cutlines

- Extend `Game.Companion`; do not create another dashboard.
- First boot is read-only Explore. Claiming the installation enables Admin
  capabilities.
- Dev/Lab are launcher-selected profiles; normal gameplay excludes Dev MCP.
- Implement real Explore, Build, Operate, and Recover vertical slices. Home
  synthesizes them; Community remains informational.
- Use a narrowly allow-listed Windows host runner. It accepts no arbitrary
  commands, and no container receives the Docker socket.
- Preserve all existing `/api/v0/companion/*` behavior while introducing the
  new Workbench contract.
- Target 9–12 focused hours, with alignment/replanning gates. Do not expand the
  feature set between gates.

### Verified starting facts

- The historical `.NET Framework/net48` workaround is the Docker Workbench
  image: the mod builds inside `mcr.microsoft.com/dotnet/sdk:9.0` against a
  read-only Valheim mount with plugin copying disabled. A host SDK MSB3644 is
  an expected boundary, not a missing product feature or a reason to add a
  second host build lane.
- AM4 and i5 were reachable during planning; i5 had working SSH, Docker, disk,
  and Valheim paths.
- The source contains the newer Workbench endpoint, but the container answering
  on port 8080 during planning was stale and returned 404 for it. Source/runtime
  alignment is therefore the first gate.
- At planning time the default MCP endpoint was not source-unique: PID 14164 on
  `:8720` was launched by the enabled `ComfyGatewayBoot` task from retired
  `C:\work\comfy\fieldlab`, while HEARTH had a separate `:8710` listener. That
  task is now disabled and the listener stopped; Baseline Dev MCP must still
  self-attest its source identity before MCP receipts can be accepted.
- Existing uncommitted product-decision documentation must be preserved
  separately from implementation changes.

## Delivery cadence and milestones

| Milestone | Target | Alignment/replanning decision |
|---|---:|---|
| M0 — Baseline and provenance | 45–60 min | Confirm source/runtime identity, inventory MCP listeners/tasks/ledgers, quarantine suspect default-port evidence, preserve current docs, and lock the v1 capability list. |
| M1 — Kernel | 90 min | Inspect installation, capability, job, receipt, and security contracts through live API fixtures. |
| M2 — Product shell | 90 min | Demonstrate claim flow, Standard/Advanced UI, jobs, and live map using fixture runners. |
| M3 — Real local slices | 2–3 hr | Run Explore, containerized Build, Operate, Recover, and safe recreate locally. Do not accept an MCP-dependent slice until endpoint provenance is green. |
| M4 — Distribution and MCP identity boundary | 90 min | Prove bootstrap/profile behavior, Baseline Dev MCP identity on the explicit project port, and Dev MCP absence in Production; only then authorize the live three-box window. |
| M5 — Rendered acceptance | 60–120 min | Execute one bounded AM4 + OMEN + i5 role-reversal job, add human observation, and seal the receipt. |
| M6 — Closeout | 45 min | Run the complete verification suite, update roadmap/handoff material, and classify follow-on epics without silently expanding v1. |

At every milestone:

1. Demonstrate the current result through the Workbench or a machine-readable
   receipt.
2. Compare it to the milestone acceptance criteria.
3. Fix or replan the failing seam once before moving forward.
4. Add new epics/features only when they do not displace an unfinished v1
   requirement.
5. Create a checkpoint commit only after verification. Obey the Lumberjacks
   roadmap-note rule for every applicable commit.

## Saga breakdown

### Epic WB-E0 — Establish a trustworthy session baseline

#### Feature WB-F0.1 — Preserve intent and implementation state

- **Story WB-S0.1:** Preserve the current eight-file product-decision change as
  an isolated documentation checkpoint.
- **Story WB-S0.2:** Record this strategy here and link it from the operating
  model and plan index.
- **Story WB-S0.3:** Rebuild/start the current Companion from the active checkout
  and record source revision, image identity, branch, and dirty state.
- **Story WB-S0.4:** Capture a baseline snapshot of current Compose services,
  volume identity, endpoints, and installed profile without exposing
  credentials.

#### Feature WB-F0.2 — Establish endpoint provenance and evidence quarantine

- **Story WB-S0.5:** Inventory loopback listeners, parent processes, scheduled
  tasks, launch commands, `.mcp.json` files, provider sets, source roots, and
  source-resolved ledgers before using any MCP result as acceptance evidence.
- **Story WB-S0.6:** Give the Baseline Dev MCP a machine-readable identity
  record containing project name, expected source root, revision/hash, image,
  profile, port, provider set, caller registry, and ledger directory. A health
  response alone is never sufficient.
- **Story WB-S0.7 (implemented):** Reserve explicit Baseline Dev MCP loopback port
  `8721` and make Dev/Lab launchers fail closed on a listener whose identity does
  not match Baseline. Listener retirement remains a separate, explicit operator
  action; the Workbench never stops or repoints an unknown process automatically.
- **Story WB-S0.8:** Mark default-port Valheim MCP receipts from the July 31/
  August 1 window as provenance-suspect and rerun the minimum evidence set after
  the identity gate. Preserve the original receipts as historical evidence;
  never silently overwrite them.
- **Story WB-S0.9:** Add a source-controlled provenance verifier and a focused
  receipt fixture covering wrong checkout, wrong provider set, wrong ledger,
  wrong port, and the expected Baseline identity.
- **Story WB-S0.10 (implemented):** Remove hard-coded legacy `:8720` HTTP calls from the
  mod's optional Raven/MCP helper, or make that helper explicitly Dev/Lab-only
  with a configured endpoint. Normal gameplay must not probe or mutate a
  development listener merely because an old process happens to own the port.
- **Story WB-S0.11:** Package and run `Test-WorkbenchMcpIdentity.ps1` as the
  preflight receipt; an unavailable or mismatched `/identity` response blocks
  MCP-sensitive evidence with `mcp_endpoint_unavailable` or
  `mcp_endpoint_identity_mismatch`.
- **Story WB-S0.12:** Ensure every active Baseline gateway launcher derives its
  root/interpreter and defaults to the explicit project port; no launcher may
  silently reintroduce a user-profile path or the retired `:8720` default.

M0 acceptance:

- Port 8080 serves the same source revision being implemented.
- Existing `companion-data` is retained.
- The implementation begins from a cleanly classified worktree.
- No retired checkout is used as an implementation source or written; a bounded
  read-only provenance inspection is allowed only for this gate.
- The project Dev MCP identity is proven on the selected explicit port, or all
  MCP-sensitive work is visibly blocked with a deterministic reason code.

### Epic WB-E1 — Build the Workbench kernel

#### Feature WB-F1.1 — Installation ownership and effective profile

- **Story WB-S1.1:** Add an installation record with generated installation ID,
  claim timestamp, optional local-only label, schema version, and ownership
  state.
- **Story WB-S1.2:** Make unclaimed installations effectively Explore; claiming
  promotes them to Admin without linking Steam identity.
- **Story WB-S1.3:** Keep game enrollment/profile association separate from
  Workbench ownership.
- **Story WB-S1.4:** Derive the effective profile as Explore/Admin plus an
  explicit launcher override for Dev, Lab, or Production.

#### Feature WB-F1.2 — Typed capability registry

- **Story WB-S1.5:** Define capability descriptors with stable ID/version,
  intent area, eligible profiles/targets, side-effect class, human-touch class,
  input schema, runner, privacy class, cancellation support, and unavailable
  reason.
- **Story WB-S1.6:** Return capabilities eligible for the effective profile while
  retaining disabled entries and deterministic reason codes for UI explanation.
- **Story WB-S1.7:** Ensure Standard/Advanced changes presentation only and
  cannot alter eligibility, target, or side-effect policy.

Initial capability IDs:

- `explore.system.inspect`
- `explore.evidence.list`
- `build.mod.release`
- `build.rendered.c6-role-reversal`
- `operate.mod.check`
- `operate.mod.install`
- `operate.mod.rollback`
- `operate.transport.capture`
- `recover.snapshot.create`
- `recover.support.export`
- `recover.recreate.verify`

#### Feature WB-F1.3 — Durable jobs and receipts

- **Story WB-S1.8:** Store each job under
  `/data/workbench/jobs/{job_id}/` with atomic `job.json`, append-only
  `events.jsonl`, final `receipt.json`, logs, and declared artifacts.
- **Story WB-S1.9:** Implement states `queued`, `leased`, `running`,
  `waiting_dependency`, `waiting_human`, `cancelling`, `succeeded`, `failed`,
  `cancelled`, and `interrupted`.
- **Story WB-S1.10:** Recover expired leases as `interrupted`; never silently
  rerun a physical or mutating job after restart.
- **Story WB-S1.11:** Include initiator, capability/version, profile, target,
  inputs with secrets removed, timestamps, phase, reason code, source identity,
  outputs, evidence boundary, and verdict in every receipt.

#### Feature WB-F1.4 — Local security boundary

- **Story WB-S1.12:** Generate a runner key under the user's local
  application-data directory, outside the repository, and mount it read-only
  into Companion.
- **Story WB-S1.13:** Require runner authentication for lease, heartbeat, event,
  artifact, and completion APIs.
- **Story WB-S1.14:** Require same-origin antiforgery protection for browser
  mutations.
- **Story WB-S1.15:** Reject arbitrary commands, paths, environment variables,
  scripts, and unregistered capability IDs.

M1 acceptance:

- API fixtures prove claim, profile filtering, job transitions, restart
  reconciliation, runner authentication, and antiforgery behavior.
- Advanced mode cannot expose or execute a capability unavailable in Standard
  mode's runtime profile.

### Epic WB-E2 — Create the one-stop human control surface

#### Feature WB-F2.1 — Unified shell

- **Story WB-S2.1:** Make `/` the Workbench shell and retain `/workbench` as a
  compatibility redirect.
- **Story WB-S2.2:** Add Home, Explore, Build, Operate, Recover, and Community
  navigation using lightweight static HTML/CSS/JavaScript served by Companion;
  introduce no frontend build framework.
- **Story WB-S2.3:** Add a persistent Standard/Advanced presentation toggle
  stored locally in the browser.
- **Story WB-S2.4:** Show installation ownership, effective profile,
  source/image identity, current target, and privacy posture in the shell
  header.

#### Feature WB-F2.2 — Live System Map

- **Story WB-S2.5:** Render Workbench, host runner, Docker, Dev MCP, AM4, OMEN,
  i5, and P7 as topology nodes.
- **Story WB-S2.6:** Use the adopted node states and include `observed_at`,
  source, reason code, role, active job phase, and declared human touch.
- **Story WB-S2.7:** Update through bounded polling with cached remote probes;
  do not add a streaming bus.
- **Story WB-S2.8:** Allow Overview, Operator, and Developer detail levels
  without changing authority.

#### Feature WB-F2.3 — Job-centered UX

- **Story WB-S2.9:** Add capability cards driven entirely from the registry,
  including prerequisites, target, expected duration, side effects, and disabled
  reasons.
- **Story WB-S2.10:** Add a global job drawer showing active phase, stop path,
  logs, artifacts, and receipt.
- **Story WB-S2.11:** Add typed confirmation for player-impacting/destructive
  work and a typed human-observation form for `waiting_human`.
- **Story WB-S2.12:** Preserve existing update, diagnostics, trace, roadmap, and
  community routes through the new navigation.
- **Story WB-S2.13 (follow-on gate; TODO — Derek soon):** The Standard UI now contains a first-visit
  safe path and the facilitator has a no-coaching
  [newcomer protocol](workbench-v1-newcomer-usability-protocol.md). Have an
  unfamiliar operator use the live map and mobile layout; record whether they can
  identify the active goal, hardware roles, expected result, evidence, and
  recovery path.
- **Story WB-S2.14 (implemented; owner observation pending):** Make Home answer
  the five operator questions before showing architecture: is the server up, who
  is online, what is executing, which runtime netcode path is active, and what
  should happen next. Compose those answers from live Gateway telemetry and job
  state, distinguish finished `waiting_human` work from execution, and link the
  deeper Companion/trace views.

M2 acceptance:

- An unfamiliar reader can identify what is running, why, where, what is
  expected, whether human attention is needed, and where the receipt will
  appear.
- A fixture job moves visibly from queued through completion and survives a
  Companion restart.

### Epic WB-E3 — Connect real capabilities through bounded runners

#### Feature WB-F3.1 — Allow-listed Windows host runner

- **Story WB-S3.1:** Add a hidden, single-instance PowerShell runner launched by
  the existing developer and packaged bootstrap entrypoints.
- **Story WB-S3.2:** Implement a code-owned switch from capability ID to a fixed
  handler; accept only typed, bounded inputs.
- **Story WB-S3.3:** Emit heartbeats containing runner version, Docker readiness,
  source identity, and cached OMEN/AM4/i5 reachability.
- **Story WB-S3.4:** Capture stdout/stderr, exit code, timeout, cancellation,
  child process identity, and artifact hashes.
- **Story WB-S3.5:** Ensure cleanup/finally blocks stop bounded child work
  without killing unrelated Steam, Docker, SSH, or game processes.

#### Feature WB-F3.2 — Explore vertical slice

- **Story WB-S3.6:** Aggregate installation, Docker, game/config, Gateway, Dev
  MCP, AM4, OMEN, i5, evidence, and source identity into
  `explore.system.inspect`.
- **Story WB-S3.7:** List bounded receipts and artifacts by privacy class through
  `explore.evidence.list`.
- **Story WB-S3.8:** Cache remote probes with explicit freshness; i5 probes are
  one bounded attempt with no retry loop.

#### Feature WB-F3.3 — Build vertical slice

- **Story WB-S3.9:** Add a Dev/Lab tool-runner image based on .NET SDK 9 with the
  checkout and Valheim assemblies mounted read-only.
- **Story WB-S3.10 (implemented):** Implement `build.mod.release` using the
  Docker Workbench image as the canonical `.NET Framework/net48` build path,
  disable plugin copying, and retain DLL/PDB hashes and compiler output. The
  host SDK is intentionally not a supported substitute.
- **Story WB-S3.11:** Refuse Build outside Dev/Lab and explain whether source,
  Docker, or the Valheim assembly mount is missing.
- **Story WB-S3.12:** Never deploy a successful build implicitly; deployment
  remains a separate capability.

#### Feature WB-F3.4 — Operate vertical slice

- **Story WB-S3.13:** Adapt existing check/install/rollback and
  transport-capture endpoints behind capability/job descriptors.
- **Story WB-S3.14 (implemented and regression-covered):** Keep game-closed
  confirmation and hash verification; preflight the complete archive before
  mutation; serialize update operations; atomically replace each file; restore
  applied bytes when apply/state recording fails; and make rollback remove
  candidate-created files while restoring the prior release record. Legacy
  installed records remain readable.
- **Story WB-S3.15:** Expose old endpoints as compatibility adapters over the
  same underlying handlers rather than duplicate implementations.
- **Story WB-S3.20 (follow-on gate):** The admitted read-only check is complete:
  clean Lab job `job-20260802-015026195-e3676b38` passed against local candidate
  `m32-workbench-20260802-r1`. Its 30 payload entries are an exact byte match for
  the pre-drill OMEN state, with no missing or unsafe entries. Approved install
  job `job-20260802-015909355-13073d0c` and rollback job
  `job-20260802-015911118-89a57d29` proved exact state/byte restoration. A later
  hands-on capture returned `no_peer_window` and is retained as negative evidence,
  not accepted as the player-active receipt. The separately approved peer-bearing
  capture then passed as Workbench job `job-20260802-025242918-32e66e98`, with
  `max_peers=2`, three samples, zero bad samples, and verdict
  `native_motion_only`. This closes the player-active transport gate; the
  capture's disconnected motion WS/UDP state is a follow-on implementation
  finding, not a peer-capture failure.

#### Feature WB-F3.5 — Recover vertical slice

- **Story WB-S3.16:** Produce a redacted Workbench snapshot through
  `recover.snapshot.create`.
- **Story WB-S3.17:** Produce a public-safe support capsule containing typed
  status, recent receipt summaries, source identity, and deterministic reason
  codes; exclude names, IDs, coordinates, free text, secrets, and raw remote
  bodies.
- **Story WB-S3.18:** Add a recreate verifier that records installation ID and
  retained receipt hashes before and after container/image replacement without
  deleting the volume.
- **Story WB-S3.19:** Present factory reset separately from recreate; v1 does not
  let the web process delete its own state.

M3 acceptance:

- All four intent areas execute real work and produce uniform receipts.
- The mod builds in Docker with zero host SDK dependency and no live plugin
  write.
- Container/image recreate preserves ownership, configuration association, and
  receipts.
- The public-safe capsule passes the existing Workbench privacy scanner.

#### Feature WB-F3.6 — Lab runtime provenance and session boundary

- **Story WB-S3.21 (full migration passed):** Record the active Lab compose source, working directory,
  image digest, and state-root disposition in the Workbench evidence packet.
  A mixed retired/Baseline runtime is visible and fails the next Lab readiness
  gate; it is never silently accepted as a Baseline run.
  The stopped source and Baseline target matched at 2,561 files and
  57,551,976,393 bytes with matching current/prior world hashes. The active
  server now uses only Baseline Compose and Baseline state mounts; the retained
  source remains a recoverable rollback copy.
- **Story WB-S3.22 (config/routing implemented; runtime acceptance pending):** Give each rendered Lab node an explicit canonical
  Gateway route (OMEN local, i5 via OMEN's reachable Tailscale address, or an
  explicitly named production route). A blank or unreachable route is a
  deterministic preflight failure, not runtime endpoint discovery.
- **Story WB-S3.23 (implemented):** Keep the canonical game-session and motion side channels
  disabled in Admin/Production player posture. Lab is the only profile that
  may enable them, and the receipt records the effective side-channel state.
- **Story WB-S3.24 (attempted; motion rendezvous failed):** After the provenance
  decision in PD-7, run one bounded two-client Lab window and require
  `session_started`/peer binding before evaluating motion.
  `job-20260802-034806539-ce87afb7` reached both clients and i5 recorded
  `session_started`, but `i5-c6-rendezvous` failed with `deadline_exceeded`
  after UDP reset/fallback to binary WebSocket; OMEN consequently received zero
  motion samples. No canonical-session or motion pass is claimed.
  `native_motion_only` remains a valid native transport observation but is not a
  Lumberjacks motion pass.
- **Story WB-S3.25 (evidence retention implemented; rendezvous diagnosis complete):** The
  orchestrator now retains the remote i5 lifecycle/log bundle during failure
  cleanup when the OMEN leg aborts first. Historical receipts prove that
  UDP-reset/WebSocket-fallback is a working transport path. The post-bridge
  failure was caused by OMEN and i5 starting outside the Gateway's player-
  interest edge, leaving `TryRendezvous` without a remote descriptor. No
  production interest-routing change is authorized by this finding.
- **Story WB-S3.26 (Lab-session gate implemented; acceptance pending):** The
  C6 manifest generator now adds bounded `teleport_to` safe-origin actions for
  both clients before rendezvous, using a retained-world ground-plane target
  `(2211,33,-69)` rather than the earlier `y=80` fixture that created an
  implausible vertical correction. This makes the Lab test independent of
  persisted character placement while preserving the production interest-radius
  policy. The rendered harness passes an explicit Lab-session switch for C6/C8,
  temporarily enables only the canonical session and motion settings, and
  restores the exact pre-run config bytes with a hash receipt. The first
  safe-origin retry failed because this gate was absent
  (`job-20260802-041714198-5cb8449a`). The next bounded retry
  (`job-20260802-044127818-e060cb19`) reached session start, peer binding,
  WebSocket fallback, interest-edge discovery, rendezvous, and passing initial
  i5 probes, then hit an OMEN rendered Unity/main-loop stall after
  `omen-settle`; no full C6 motion pass is claimed. A missing edge or stalled
  renderer remains a fail-closed, actionable receipt rather than a generic
  timeout.
- **Story WB-S3.27 (durable failed-run Lab restore implemented; forensics
  pending):** Add a standalone `restore-lab-session` action that restores the
  byte-backed Lab-session config after a forced harness termination. The
  orchestrator invokes it during failed-run cleanup for OMEN and i5 and records
  a hash receipt. The first targeted forensics fix reasserts Unity
  `runInBackground` at the first real peer boundary (Docker receipt
  `job-20260802-045218754-f432d3af`) because the prior setting was applied only
  before the scene transition. The targeted single-client observation
  `workbench-bg-reassert-20260802` then passed settle, move, bounded resume,
  and scenario completion with the hardened artifact. It clears the diagnostic
  gate for one full C6 run, but is not itself a multiplayer or motion verdict.
- **Story WB-S3.28 (forensics complete):** Analyze the one justified full C6 run against
  the hardened artifact (`job-20260802-045616258-030c0534`, run
  `workbench-20260802-045621-030c0534`). It reached session start, peer
  binding, safe-origin, interest-edge rendezvous, and initial i5 probes, but
  OMEN stopped advancing after `omen-settle`; i5 failed closed at
  `i5-c6-observe-gap`. The post-join background reassertion is present in the
  OMEN log, so the next action is bounded crash-forensics or main-thread
  budget/watchdog instrumentation, not another blind C6 retry. Keep the
  Docker Workbench net48 build path unchanged while isolating this concurrent
  rendered-client interaction. The clean watchdog run
  `job-20260802-065514705-b159b3fb` / run
  `workbench-20260802-065519-b159b3fb` supplied that discriminating result:
  OMEN completed drive-one, observe-two, and drive-gap, while i5 completed
  observe-one and drive-two. i5 applied correlation `c6-gap-omen-to-i5` at
  `06:57:12.417Z`; its `observe_gap` probe began at `06:57:13.177Z`, after the
  evidence it was intended to measure. The prior persistent-stall hypothesis is
  rejected for this run; the failure is scenario ordering.
- **Story WB-S3.29 (implemented and observed diagnostic gate):** Add a worker-thread
  `perf-watchdog.jsonl` heartbeat receipt so a Unity/main-thread stall remains
  observable even when synchronous perf sections cannot close. Collect it in
  native client evidence. Make the Workbench runner compute checkout-time
  source identity for every build and fail rendered C6 closed when the checkout
  is dirty or the Companion image revision differs. A dirty Docker build may
  support local diagnostics, but it is never a clean rendered acceptance. The
  admitted DLL SHA-256
  `ec75ee07c2fcd651db353403c3692502f26d488bf35628d2721e4cac8a66cff9`
  ran on both clients. Its watchdog rows captured only bounded two-second gaps
  with idle route state and zero writer faults; both clients subsequently
  advanced their scenario clocks.
- **Story WB-S3.30 (implemented provenance gate):** Add the read-only
  `fieldlab/scripts/Test-LabRuntimeProvenance.ps1` verifier. It checks the
  active server's Compose source and working directory, immutable image digest,
  `/config` and `/opt/valheim` state mounts, and credential-free OMEN/i5 Gateway
  routes. It accepts a fully migrated Baseline state root or an explicitly
  named retained-state bridge only when the Baseline bridge override is present;
  without that explicit switch the same mixed state fails closed. The receipt
  names the disposition instead of treating a healthy container as proof of
  ownership. Rendered C6 invokes the strict form before source/image checks,
  remote preflight, scenario generation, or client launch; it never supplies
  the interim bridge override. Job `job-20260802-054530209-f67cfc0d` proved the
  active bridge fails there with `rendered_prelive_lab_provenance_failed`, no
  run artifacts, both clients stopped, and the at-rest config unchanged.
  After the full migration, the same strict verifier passes with
  `state_root_disposition=baseline_migrated` and no bridge override in the
  active Compose labels.
- **Story WB-S3.31 (implemented and physically validated):** The
  C6 manifest now places a bounded four-second OMEN observer-alignment action
  immediately before gap drive, reusing the already accepted C8 ordering
  margin. `Test-C6ScenarioCoverage.ps1` verifies the action, bound, order, and
  shared correlation and is invoked before i5 preflight or any remote state is
  armed. The generated 24-action fixture passes. After separate authorization,
  job `job-20260802-072520719-74b07483` / run
  `workbench-20260802-072523-74b07483` reached
  `waiting_human/rendered_role_reversal_complete`: both clients emitted
  `scenario_complete`, i5's observe-gap window opened at `07:27:12.752Z`, OMEN
  began gap drive at `07:27:17.675Z`, and i5 completed with
  `holds=1 gaps=1 resync_applied=1`. No human observation is inferred from this
  machine validation.

M3.6 acceptance:

- The active Lab source is Baseline-attributed (or the deliberate retained
  state-root bridge is recorded) and reproducible from one command.
- OMEN and i5 route to the same healthy local Gateway without secrets in the
  receipt; normal gameplay does not retry the Dev/Lab side channel.
- A two-client run records canonical session start and peer binding before a
  motion verdict is emitted.
- A failed two-client run retains the remote i5 lifecycle/log evidence even when
  the OMEN leg aborts first; a missing second-client receipt is a collection
  defect, not a motion timeout attributed to OMEN.
- Lab-only session activation is explicit, bounded, and byte-for-byte restored;
  Admin/Production remains disabled at rest, including after a forced harness
  termination via the durable restore action.
- A full C6 retry is not accepted merely because a single-client scenario clock
  advances; the concurrent rendered-client path must produce a discriminating
  forensic receipt before another full run.
- Build receipts distinguish the actual checkout identity from the Companion
  image identity; rendered acceptance requires a clean, matching source/image
  pair.
- A gap observer captures its baseline before the correlated sender action;
  the scenario fails before remote mutation if that ordering guard is absent.

### Epic WB-E4 — Converge profiles, bootstrap, and Dev MCP

#### Feature WB-F4.1 — Compose profile model

- **Story WB-S4.1:** Keep Companion as the always-present base service.
- **Story WB-S4.2:** Add tool-runner and Dev MCP services only to Dev/Lab
  profiles.
- **Story WB-S4.3:** Bind all published HTTP/MCP ports to loopback.
- **Story WB-S4.4:** Pass effective profile and installation paths explicitly
  from the launcher; do not infer them from UI detail mode.
- **Story WB-S4.5:** Add rendered-Compose checks proving Production includes no
  Dev MCP listener, key, mailbox, source mount, or Dev/Lab service.

#### Feature WB-F4.2 — Shared Dev MCP interface

- **Story WB-S4.6:** Add Dev MCP tools to list Workbench capabilities, start an
  eligible job, inspect a job, cancel a cancellable job, and read a receipt.
- **Story WB-S4.7:** Make these tools call the same Workbench API used by the
  browser.
- **Story WB-S4.8:** Preserve existing project-specific Valheim tools while
  removing any need for HEARTH paths, providers, keys, or environments.
- **Story WB-S4.9:** Require loopback binding and Workbench service
  authentication for MCP-started mutations.
- **Story WB-S4.9a:** Make `comfy_gateway_status` (or its replacement identity
  route) return the expected Baseline source root, source revision/hash, image,
  profile, port, provider set, caller registry, and ledger directory.
- **Story WB-S4.9b:** Require Web/MCP receipts to include the endpoint identity
  observed at execution time; reject a mismatched or merely healthy listener
  with `mcp_endpoint_identity_mismatch`.
- **Story WB-S4.9c:** Ship an explicit Baseline MCP client configuration for the
  selected project port. The legacy shared `:8720` task is disabled but retained
  as recoverable historical infrastructure; it is not an accepted Baseline path.

#### Feature WB-F4.3 — Initialization and packaging

- **Story WB-S4.10:** Extend both source-checkout and packaged launchers with
  explicit Explore, Admin, Dev, Lab, and Production selection; default to
  Explore.
- **Story WB-S4.11:** Package only owner/admin capabilities in the public
  bootstrap; Dev/Lab reports `source_checkout_required`.
- **Story WB-S4.12:** Generate local keys/config on first initialization and
  never embed credentials in the image or bundle.
- **Story WB-S4.13:** Extend bootstrap package tests to cover runner files,
  profile behavior, loopback publication, clean claim, and safe recreate.

M4 acceptance:

- A fresh package initializes into Explore, can be claimed into Admin, and can
  be recreated safely.
- Dev/Lab exposes the identity-verified Baseline Dev MCP and Build on the
  explicit project port; Production demonstrably does not expose either.
- Browser- and MCP-started fixture jobs create the same job/receipt shapes.
- No container has the Docker socket.

### Epic WB-E5 — Prove the product on the rendered three-box lane

#### Feature WB-F5.1 — Automated prelive gate

- **Story WB-S5.1:** Verify Workbench source/image identity, runner heartbeat,
  AM4 health, i5 link, Docker readiness, matching mod hashes, and available
  disk.
- **Story WB-S5.2:** Generate a fresh, expiring C6 manifest with a unique
  Workbench run ID using the existing scenario generator.
- **Story WB-S5.3:** Refuse the run on mismatched binaries, missing peers, stale
  health, dirty/unattributed image identity, or unavailable runner.
- **Story WB-S5.4:** Show all preconditions and intended human attention in the
  UI before confirmation.

#### Feature WB-F5.2 — Rendered role-reversal capability

- **Story WB-S5.5:** Have `build.rendered.c6-role-reversal` invoke the existing
  native two-client orchestrator with motion-authority cutover and bounded
  timeouts.
- **Story WB-S5.6:** Track AM4, OMEN, and i5 through ready, working, waiting,
  cleanup, and completion states.
- **Story WB-S5.7:** Run OMEN-drive/i5-observe followed by
  i5-drive/OMEN-observe without manual KVM transport.
- **Story WB-S5.8:** Transition to `waiting_human` for typed observation:
  role-following result, smooth/mixed/rough quality, and an optional
  operator-private note.
- **Story WB-S5.9:** Seal machine evidence and human observation into one
  Workbench receipt while keeping its claim limited to Workbench coordination
  and rendered execution—not C9 product acceptance unless separately
  adjudicated.

Stop rules:

- Do not retry-loop an offline i5.
- Stop after one failed physical run and fix/replan the failing seam.
- Stop if binaries differ, a client leaves unexpectedly, poison trips, a
  command remains pending, cleanup fails, or the save-integrity gate changes.
- Headless clients cannot substitute for the required rendered acceptance.

#### Feature WB-F5.3 — Closeout and future classification

- **Story WB-S5.10:** Run API, runner, Compose, bootstrap, privacy, Docker build,
  recreate, MCP, and three-box checks.
- **Story WB-S5.11:** Update the living roadmap and regenerate required artifacts
  in every applicable implementation commit.
- **Story WB-S5.12:** Record completed capabilities, evidence boundary, remaining
  defects, and newly discovered candidates.
- **Story WB-S5.13:** Classify follow-on work as a new Epic, Feature, Story,
  defect, or deferred trigger; do not leave unclassified TODOs in code.

M5/M6 acceptance:

- The Workbench initiated, displayed, coordinated, and receipted a real
  AM4 + OMEN + i5 role-reversal run.
- Derek's only required participation was the declared rendered observation.
- Dev MCP absence in Production, safe recreate, public-safe export, and shared
  Web/MCP receipts are machine-proven.
- Any unmet criterion leaves WB-1 as candidate/incomplete rather than being
  reworded into a pass.

## Public interfaces and data contracts

### Additive HTTP API

Add the following under `/api/v1/workbench`:

- `GET /installation`
- `POST /installation/claim`
- `GET /capabilities`
- `POST /capabilities/{id}/jobs`
- `GET /jobs`
- `GET /jobs/{id}`
- `POST /jobs/{id}/cancel`
- `POST /jobs/{id}/observation`
- `GET /jobs/{id}/receipt`
- `GET /topology`
- runner-authenticated `heartbeat`, `lease`, `events`, `artifacts`, and
  `complete` endpoints

### Core types

- `InstallationRecord`
- `CapabilityDescriptor`
- `JobRecord`
- `JobEvent`
- `JobReceipt`
- `TopologyNode`
- `HumanObservation`

### Compatibility guarantees

- Existing `/api/v0/companion/*`, update, diagnostics, capture, trace, roadmap,
  and community URLs remain functional.
- Existing `companion-data` is retained and migrated in place.
- Existing Steam/game enrollment stays separate from local Workbench ownership.
- No P7 deployment or production-authority change is required for WB-1.

## Verification matrix

- **Contract tests:** schemas, eligibility, Standard/Advanced invariance, typed
  inputs, reason codes, state transitions, lease expiry, restart reconciliation,
  and receipt completeness.
- **Security tests:** loopback binding, runner authentication, antiforgery,
  traversal/injection rejection, no arbitrary command, no Docker socket, and
  Production Dev MCP absence.
- **Endpoint provenance tests:** listener/task ownership, expected source root,
  source revision/hash, image, profile, port, provider set, caller registry,
  ledger directory, and wrong-checkout refusal.
- **Runner fixtures:** success, nonzero exit, timeout, cancellation, missing
  dependency, interrupted process, artifact hash, and offline i5.
- **UI tests:** claim flow, disabled explanations, job history, live-map state,
  waiting-human form, mobile layout, and compatibility redirects.
- **Build tests:** net9 solution verification, containerized net48 build, no
  plugin copy, and Dev/Lab eligibility.
- **Recovery tests:** snapshot, public-safe capsule/privacy scanner, and
  container/image recreate with state preservation.
- **Distribution tests:** bootstrap archive, first initialization, key
  generation, source attribution, profile selection, and explicit Dev MCP
  endpoint identity.
- **Rendered acceptance:** one fresh C6 AM4 + OMEN + i5 role-reversal run with a
  machine receipt and human observation.

## Failure and recovery behavior

- A missing or invalid runner key makes host-runner capabilities unavailable; it
  never falls back to unauthenticated execution.
- A stale runner heartbeat makes its capabilities unavailable with a freshness
  reason code.
- A Companion restart marks an expired in-flight lease `interrupted` and retains
  its events and logs; physical/mutating work requires a new explicit job.
- A timed-out child process receives the capability's bounded cleanup sequence.
  Unrelated Steam, Valheim, Docker, and SSH processes are untouched.
- An offline i5 produces one bounded failed preflight receipt and no retries.
- An unavailable AM4 or i5 blocks M5 acceptance. Headless evidence cannot replace
  the chosen rendered-three-box requirement.
- A healthy MCP listener with the wrong source root, provider set, profile, port,
  caller registry, or ledger is treated as unavailable; no MCP-sensitive job
  proceeds on an identity mismatch.
- Historical MCP results whose endpoint identity is unknown remain quarantined
  until rerun or explicitly reclassified; they are never promoted by inference.
- A failed recreate test preserves the existing volume and reports exact
  before/after identities; it never escalates into a factory reset.
- A support artifact that fails the privacy gate is deleted from the export
  staging area and the job fails closed.

## Commit and evidence discipline

- Keep the product-decision documentation checkpoint separate from code changes.
- Each implementation checkpoint must include build/test receipts appropriate to
  its milestone.
- Every non-merge commit under `Lumberjacks/` appends its roadmap note and stages
  regenerated roadmap HTML in the same commit.
- Any commit touching `fieldlab/`, `network/`, or `infra/gcp/p7/` follows the root
  roadmap-journal rule as well.
- Live-run evidence remains run-scoped and privacy-classified. Do not commit raw
  player-bearing output merely because the Workbench collected it.
- Completion claims follow [PD-4](../docs/decisions/pd-4-evidence-standard.md):
  implemented is not the same as tested, and tested is not the same as accepted.

## Assumptions and explicit deferrals

- The current Companion remains the sole human Workbench product.
- The host runner runs as the current interactive Windows user because
  Steam/Valheim automation requires that session.
- Baseline's Dev MCP uses explicit project-owned loopback port `8721`, distinct
  from HEARTH and any legacy listener.
- Derek chose recoverable retirement for the legacy `ComfyGatewayBoot` task: it
  is disabled without deletion, its retired-checkout listener is stopped, and
  any rollback requires an explicit operator action.
- Remote reachability may change; AM4 or i5 becoming unavailable blocks rendered
  acceptance rather than weakening it.
- Today does not add browser-controlled Compose switching, a Docker socket mount,
  hosted multi-community control, a frontend framework, a telemetry bus, AI
  classification, additional Harmony transpilers, world backup/restore, or
  exhaustive wrapping of every repository script.
- Community mutation and stranger onboarding become separate epics after this
  local owner/developer v1 is accepted.
- HEARTH remains independent and is neither bundled nor required.

## Definition of done

WB-1 is complete only when all of the following are true:

1. A fresh Workbench starts in Explore and becomes locally owned through the
   claim flow.
2. The unified UI exposes Home, Explore, Build, Operate, Recover, and Community,
   with Standard/Advanced presentation independent of authority, and Home directly
   answers the live server/player/activity/netcode/next-action questions.
3. Real capabilities in the four selected intent areas create durable,
   inspectable jobs and receipts.
4. The allow-listed host runner performs physical and Docker-host work without a
   Docker socket or arbitrary command surface.
5. Dev MCP and build tooling exist only in Dev/Lab; Production proves their
   absence, and Dev/Lab proves the MCP endpoint identity before accepting MCP
   evidence.
6. Recreating containers/images preserves declared owned state, and the
   public-safe support capsule passes the privacy gate.
7. The Workbench coordinates and receipts one rendered AM4 + OMEN + i5 C6
   role-reversal run, including the declared human observation.
8. All verification suites pass, endpoint-sensitive historical evidence is
   quarantined or rerun, the roadmap is regenerated where required, and remaining
   work is explicitly classified.
9. An unfamiliar operator completes the no-coaching Standard-mode desktop and
   mobile protocol, with comprehension and recovery-path findings recorded.
10. The admitted package completes an explicitly approved install-to-rollback
    drill with before/after hashes and installed-release identity restored, then
    a separately approved player-active window yields a peer-bearing transport
    capture receipt. Both halves passed; PD-7 migration, explicit local routes,
    and corrected-order physical C6 subsequently closed the capture's
    native-motion-only follow-on.
