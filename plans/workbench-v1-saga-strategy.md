# Saga WB-1 — Ownable Docker Workbench v1

Status: implementation plus rendered machine-and-human acceptance completed
2026-08-02. M5 and M6 are closed, and the read-only Operate check has a clean
local success receipt. The install/rollback implementation is now reversibility-
tested and live-drilled; WB-1 remains a candidate pending the declared unfamiliar-
user usability gate and player-active transport capture. Replanned after the
[MCP endpoint provenance audit](../docs/audit/2026-08-01-mcp-endpoint-provenance-audit.md).
Owner: Derek. This document is the decision-complete execution strategy for the
first coherent Workbench product slice.
Product rationale remains canonical in [PD-5](../docs/decisions/pd-5-local-workbench-ownership-appliance.md),
[PD-6](../docs/decisions/pd-6-development-mcp-lifecycle.md), and the
[Workbench operating model](../docs/workbench-operating-model.md).

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

- The net48 mod builds successfully inside `mcr.microsoft.com/dotnet/sdk:9.0`
  against a read-only Valheim mount with plugin copying disabled.
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
- **Story WB-S2.13 (follow-on gate):** The Standard UI now contains a first-visit
  safe path and the facilitator has a no-coaching
  [newcomer protocol](workbench-v1-newcomer-usability-protocol.md). Have an
  unfamiliar operator use the live map and mobile layout; record whether they can
  identify the active goal, hardware roles, expected result, evidence, and
  recovery path.

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
- **Story WB-S3.10:** Implement `build.mod.release` using the proven container
  build, disable plugin copying, and retain DLL/PDB hashes and compiler output.
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
  not accepted as the player-active receipt. Only that separately approved
  peer-bearing capture remains open.

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
   with Standard/Advanced presentation independent of authority.
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
    capture receipt. The first half passed; the player-active half remains open.
