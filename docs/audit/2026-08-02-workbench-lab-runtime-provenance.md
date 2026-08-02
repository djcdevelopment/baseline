# Workbench Lab runtime provenance audit — 2026-08-02

This is a read-only audit following the approved peer-bearing player-active
capture. It explains why that capture is accepted as native two-peer evidence
but not as a Lumberjacks motion-lane pass.

## Observed runtime

| Check | Observation | Interpretation |
|---|---|---|
| Workbench capture | Job `job-20260802-025242918-32e66e98`; `max_peers=2`; three samples; zero bad samples; verdict `native_motion_only` | Native Valheim peer window is real; canonical motion is not proven |
| Client session state | OMEN summary state `canonical_session_waiting`; WebSocket `false`; UDP `false`; motion delta `0` | The mod's canonical game-session lane never reached `session_started` |
| OMEN config | `lumberjacksGameSessionEnabled = true`; Gateway `http://8.231.129.249:42317`; enrollment/key present | Test side channel is enabled but routed to the retired public endpoint |
| i5 config | Same retired Gateway endpoint; game session enabled; enrollment/key present | Both rendered nodes share the stale route pattern |
| Local Gateway | `http://127.0.0.1:4000/health` returned `{"status":"ok","service":"gateway"}` | The intended Lab Gateway is healthy |
| i5 route | TCP `100.124.12.37:4000` from i5 succeeded | i5 can reach OMEN's local Gateway over Tailscale |
| Gateway container | Compose labels report `C:\work\baseline\fieldlab\autonomous\valheim-lab.compose.yml` and Baseline `network/mcp/var` | Gateway source attribution is current |
| Valheim server container | Compose labels report `C:\work\comfy\fieldlab\autonomous\valheim-lab.compose.yml`, a temporary Claude override, and old state mounts | The Lab project has mixed source provenance |

## Safety conclusion

No player files were changed by this audit and no game process was left
running. The installed m32 package and schema-1 rollback record remain intact.
The next run is held until [PD-7](../decisions/pd-7-lab-runtime-provenance-and-session-boundary.md)
chooses the state-root strategy, sets explicit per-node Gateway routes, and
records an Admin/Production posture with the canonical session/motion lane
disabled.

## Bridge execution receipt

The approved short-term bridge was executed after the audit:

- Backup: `C:\work\baseline\fieldlab\autonomous\state\bridge-backup-20260802T032840Z`
  (12 files, 2,660,448,982 bytes after adding the OMEN config backup).
- Live `ComfyEra16.db` and backup SHA-256 both matched
  `C01CDFEEAF6EEE2D6CEB0EE8E303DBAA3937C329DBD4B2045BD19F94728CA752`.
- `comfy-valheim-lab-valheim-server-1` was stopped cleanly (exit 0) and
  recreated with the Baseline compose file plus
  `valheim-lab.retained-state.bridge.override.yml`.
- The resulting container labels report Baseline compose provenance and the
  deliberate retained legacy state mount. The temporary Claude override is no
  longer part of the active server container.
- The server retained the passwordless private-Lab posture and reached
  `Game server connected` after loading `ComfyEra16`.
- No client was launched during this bridge step; canonical-session acceptance
  remains pending explicit per-node routes and Admin/Production side-channel
  restoration.

## Post-bridge client posture

- OMEN now has `lumberjacksGatewayUrl = http://127.0.0.1:4000`.
- i5 now has `lumberjacksGatewayUrl = http://100.124.12.37:4000`.
- Both installs now have `lumberjacksGameSessionEnabled = false` and
  `lumberjacksMotionEnabled = false` at rest.
- Both configs were backed up before atomic replacement. The original OMEN
  config hash was `13C082FA8F5C75E1D4DDCEC96DB9BA7A452BD120C4BC27B7D1D0501B27D4D7B2`;
  the original i5 config hash was
  `F99FB63FB30960AA303607EC408F977C8FB7BE9A6C4C7DA983DC24932875AF8C`.
- No Valheim client was running during the posture change, and the retired
  `comfy-valheim-lab-comfy-gateway-1` remained stopped.

## Canonical-session acceptance receipts

The first Workbench C6 attempt, job `job-20260802-034134002-ac6cd4a7`, failed
before either rendered client was launched. Its durable reason was
`rendered_role_reversal_failed`; the runner evidence contained only server
runtime-control and residue-cleanup receipts. Replaying the gateway build
outside the job exposed the actionable defect: `Lumberjacks/Dockerfile` copied
three test project files into the restore layer but omitted
`tests/Game.Companion.Tests/Game.Companion.Tests.csproj`, even though
`Game.sln` referenced it. The build therefore failed at `dotnet restore` with
`MSB3202`.

The Dockerfile cache-stage copy was corrected. The rebuilt gateway passed
restore, Release build, 605 tests (126 Contracts / 250 Simulation / 217
Gateway / 12 Companion), and publish; the running gateway container now uses
image `sha256:740337a524dc6be0e430186ac8da46d5be616adaf2f2cf16df6fc3c547b3f8cc`.

A second bounded C6 attempt, job `job-20260802-034806539-ce87afb7`, reached
both rendered clients. The OMEN receipt failed at `omen-c6-observe-two` with
`deadline_exceeded`; its `omen-c6-drive-one` row sent 113 samples and received
0. The i5 Player.log proves that the scheduled task did execute in the GPU
session: i5 joined, emitted `session_started`, queued peer binding and motion
region membership, then failed at `i5-c6-rendezvous` with
`deadline_exceeded`. Its transport reported UDP receive reset and fallback to
binary WebSocket. The i5 task's `LastTaskResult=1` therefore reflects the
scenario failure, not a task-launch failure. The orchestrator aborted on the
OMEN leg before its normal remote-evidence phase; the i5 evidence was salvaged
from `C:/deploy/baseline/fieldlab/runs/native-valheim/<run>/i5` into the local
run directory. The orchestrator now also performs that best-effort failure
collection in its unconditional cleanup path. This is classified as a
motion-rendezvous and failure-evidence-collection follow-up, not as a
canonical-session or motion pass. The Workbench job has no green receipt, and
no human observation was requested.

### C6 root-cause trace

The UDP reset is not the root cause. Historical sealed C6 evidence contains the
same i5 `udp_receive_failed=ConnectionReset`/`fallback=binary_websocket`
transition and then records WebSocket motion delivery, rendezvous completion,
and passing observe/drive probes. The current Gateway also recorded WebSocket
relay traffic after UDP ingress. The fallback path is therefore an active,
previously proven transport path.

The differentiator is the player-interest precondition. This run recorded
OMEN's local motion identity at `(2216.321,33.405,-54.053)` and i5's at
`(3192.725,29.722,2377.365)`. The two clients were not in the Gateway's player
interest edge, so no remote descriptor or motion sample reached i5.
`TryRendezvous` intentionally waits for a remote descriptor before it can move
the local player; it cannot bootstrap an edge from no remote state. The
retained-state bridge changed the initial world/player placement relative to
the sealed run and exposed an unstated C6 fixture precondition.

This is a test-fixture/readiness defect, not permission to widen normal gameplay
interest routing. The next C6 admission must either prove the two players are
already within the Lab interest radius or use an explicitly test-scoped
rendezvous bootstrap. It must record initial positions, interest-edge
readiness, transport, and rendezvous separately.

The C6 manifest generator is now changed to add the existing bounded safe-origin
teleport fixture for both clients before the rendezvous action. This keeps the
production interest radius unchanged while making the Lab scenario independent
of persisted character placement. A fresh run is still required; the failed
run remains evidence and is not retroactively promoted.

A fresh safe-origin attempt, job `job-20260802-041714198-5cb8449a` and run
`workbench-20260802-041719-5cb8449a`, then exposed a separate runner gate. The
fixture actions executed on both clients, but both installs were still in the
safe Admin-at-rest state with `lumberjacksGameSessionEnabled = false` and
`lumberjacksMotionEnabled = false`. OMEN therefore never emitted a current
`session_started`/motion frame; its `omen-c6-drive-one` action timed out. i5's
teleport reached the target while its area was still loading (`zone_loaded=false`,
`area_ready=false`, 382 objects missing), and its rendezvous timed out without
a canonical remote descriptor. This run is evidence of a missing Lab-session
activation gate, not evidence that safe-origin or WebSocket fallback failed.

The native client harness now has an explicit `EnableLabSession` switch. A C6/C8
orchestrator run passes it to both rendered clients; the harness records a
byte-for-byte config backup, enables only the canonical session and motion
settings for the bounded smoke, and restores the original config with a SHA-256
check on every success or failure path. Normal gameplay remains disabled at
rest. The next acceptance must show the temporary gate and `session_started`
before interpreting interest-edge or rendezvous results.

Cleanup/disarm receipts for the second attempt are green: server motion
authority was disarmed, residue cleanup matched zero run-scoped objects, both
Valheim processes are stopped, and both client configs were restored to
`lumberjacksMotionEnabled = false` and
`lumberjacksGameSessionEnabled = false` with their explicit Lab Gateway routes.
The exact disabled-posture hashes are OMEN
`c2f8da2e996692ac2f382039616b114c39f13b928da92b6121da03d61b9bcec4` and i5
`5413d8961bc8516ffe01ceab05b1fc3feda874553222fe046b719e3b4bdcdd40`.
The relevant local evidence is under
`%LOCALAPPDATA%\\Lumberjacks\\Workbench\\runs\\workbench-20260802-034811-ce87afb7`.

The decision is therefore unchanged: PD-7 bridge execution passed, but the
canonical two-client Lab acceptance remains open until the C6 fixture has a
deterministic interest-edge/rendezvous preflight, failed runs retain both client
evidence, and a fresh run records `session_started`, peer binding, transport,
rendezvous, motion, and human-observation outcomes independently.

## Bounded follow-up: Docker build and rendered C6 retry

The historical `.NET Framework` workaround is the Docker Workbench image, not
the host SDK. The canonical rebuild receipt is
`job-20260802-044059503-235d215a`: the read-only Valheim mount build completed
with zero warnings/errors, no host SDK requirement, no plugin copy, and
`ComfyNetworkSense.dll` SHA-256
`a633597f3246f1c85cb6559b8e6959f5768ea89f7e094c4d079b619f717cebf1`.
The direct host `dotnet build` MSB3644 result is therefore an expected
boundary of the Workbench, not a product defect.

The C6 fixture was corrected before one bounded retry. The original safe-origin
target used `y=80` even though this retained world settles the test origin near
`y=33`; that produced an implausible ~49m vertical target error and correctly
tripped the authority guard. The generator now uses `(2211,33,-69)` for both
clients and records the ground-plane rationale in source.

Retry job `job-20260802-044127818-e060cb19`, run
`workbench-20260802-044133-e060cb19`, proved the next boundary:

- both clients recorded `session_started` and peer binding;
- i5 observed UDP reset followed by binary-WebSocket fallback, discovered the
  OMEN descriptor, completed `i5-c6-rendezvous`, and passed the first observe
  and drive probes (`failures=0`);
- OMEN's native client entered the Lab session but its scenario stopped after
  `omen-settle` began. Its BepInEx log stopped advancing during the rendered
  world/UI load, so OMEN never emitted the subsequent drive/observe-gap actions;
- i5 consequently failed at `i5-c6-observe-gap` with `deadline_exceeded`.

This is now classified as a rendered OMEN Unity/main-loop stall (a bounded
crash-forensics follow-up), not a Docker build, Gateway route, session-start,
interest-edge, or transport-fallback defect. No additional blind C6 retries
are authorized in this checkpoint. The Workbench run retained both client
bundles. i5 restored its disabled-at-rest config; OMEN was explicitly restored
from the prior exact Admin-at-rest backup after the harness was force-stopped,
ending at SHA-256
`A141231B84010B456537B2B80360C3C0128FED2753ACFAD76DC24310A71F1F42` with the
local Gateway route and both canonical switches disabled.

The client harness now exposes a durable `restore-lab-session` action. The
orchestrator invokes it during failed-run cleanup after stopping the client,
so a forced harness termination cannot leave Lab-only session/motion enabled at
rest. The i5 copy was deployed and SHA-256 verified.

### Targeted render-loop hardening

The OMEN log showed the stall began after `AUTOTEST_JOINED` and the first
`omen-settle` action, immediately after the world scene transition. The mod
previously set `Application.runInBackground` during the pre-scene
`FejdStartup` hook; Unity can restore its player-setting value during the
transition. The explicit native-autotest seam now reasserts the setting at the
first real peer boundary, without changing normal gameplay. Docker Workbench
receipt `job-20260802-045218754-f432d3af` rebuilt the mod successfully with
DLL SHA-256
`9a90fd69782bf1a2d280f52a536d045c45182eea5fe3143fa729ab4e1b1eb789`.

This is a targeted diagnostic fix, not a C6 pass. The next rendered action is
to observe one bounded single-client or C6 run with this exact artifact and
capture whether the post-join scenario clock advances; only then should the
full two-client window be reconsidered.

The bounded single-client observation then passed:
`workbench-bg-reassert-20260802` used the hardened DLL and completed the
post-join settle, move, bounded resume, and scenario-complete actions. Its log
contains `Native autotest background execution reasserted after peer join.`
This clears the targeted diagnostic gate but is intentionally not a
multiplayer or motion verdict; one full C6 run against the same artifact is
now justified.

The justified full C6 run was then executed once against that exact artifact:
job `job-20260802-045616258-030c0534`, run
`workbench-20260802-045621-030c0534`. It did not pass. Both clients reached
the Lab session, safe origin, interest edge, rendezvous, and the initial
observe/drive probes. i5 then failed closed at `i5-c6-observe-gap` with
`deadline_exceeded`. OMEN's scenario advanced only through
`omen-settle`/`action_started`; its rendered Unity loop stopped producing
scenario receipts while the client was processing the peer/world load. The
OMEN BepInEx evidence contains the post-join background-execution reassertion,
so the targeted fix is confirmed but insufficient for the concurrent window.

This narrows the open issue to a concurrent rendered-client/main-loop
interaction after canonical session and peer data arrive. It is not evidence
of a Docker Workbench build failure, a stale Gateway route, missing session
start, missing interest edge, or a transport-fallback defect. The i5 receipt
also records useful partial motion (`sent=98`, `received=12`, `applied=46`,
`holds=1`, `gaps=0`, `failures=0`) before the dependent gap observation timed
out. No further blind C6 retry is authorized until bounded crash-forensics or
main-thread budget instrumentation explains the OMEN stall.

The at-rest safety check after this failed run is green: no Valheim process is
running on OMEN or i5, the i5 scheduled task is `Ready`, and both config files
are restored with canonical session/motion disabled. OMEN's restored config
hash is `A141231B84010B456537B2B80360C3C0128FED2753ACFAD76DC24310A71F1F42`;
i5's is
`FC21DAABB5F2C61E89C57B84F3F04AC73B54BC6FB5D71D4144B6E9250956E945`.

The build boundary remains deliberate: the historical `.NET Framework/net48`
workaround is the Docker Workbench image with the Valheim assembly mount. A
host SDK failure such as MSB3644 is an expected boundary and must not trigger
an additional host toolchain or a second build surface.

## Forensics instrument and source-identity gate

The existing synchronous `perf-sections.jsonl` probe cannot write a completed
section when Unity stops returning from the main loop. The mod now starts a
diagnostic-only worker watchdog alongside that probe. It records one
`perf-watchdog.jsonl` row after a configurable two-second gap in the main-thread
heartbeat, including the last heartbeat time, frame count, route context, and
writer health. It changes no gameplay behavior and is controlled by the existing
perf/telemetry boundary. The native client harness now collects that file with
the rest of the failure bundle.

The Workbench host runner also now computes source identity from the actual
checkout at dispatch time. A Docker mod build receipt therefore records
`build_source` independently from the Companion image metadata, and the
rendered C6 preflight fails closed on a dirty checkout or an image/source
revision mismatch. This catches the provenance drift that the previous build
receipt exposed: the Companion image reported revision
`1456de1142658e972f9e0462d24b3f3ba143d4ce` while the active checkout was
`f54a0c55e62788dcd4ec6b6dc99b3ac6e8f88026` with local changes.

Verification:

- Docker Workbench build `job-20260802-051844360-517ae298` passed with zero
  warnings/errors, read-only Valheim mount, plugin copy disabled, and artifact
  SHA-256 `a8006968975dd82aa6542cf701c6f6f9534bb5df7a19fc5f42d14c605f297155`.
- Its `build_source` says `source_dirty=true` and `source_status_count=24`,
  so it is correctly treated as a diagnostic artifact, not a clean release.
- Rendered C6 preflight `job-20260802-052131353-ddbbd053` failed before any
  client launch with `rendered_prelive_source_dirty`, retaining the local
  source identity in the receipt.
- The installed OMEN plugin remains the prior hardened SHA-256
  `9a90fd69782bf1a2d280f52a536d045c45182eea5fe3143fa729ab4e1b1eb789`; the
  Workbench build did not copy into the live Valheim plugins folder.

## Read-only provenance verifier

PD-7's remaining preflight shape is now executable without mutating the Lab:
`fieldlab/scripts/Test-LabRuntimeProvenance.ps1` inspects the active server
container, Compose labels, state mounts, image digest, and the credential-free
OMEN/i5 routes. The admitted bridge invocation passed against
`comfy-valheim-lab-valheim-server-1` and recorded:

- Baseline Compose file and Baseline working directory;
- no retired checkout in the Compose labels;
- server image digest
  `sha256:e8b13da3c44f54a38511c8ac224f2959a437c0b2626cf916683ca7acc8dfb146`;
- before migration, `state_root_disposition=retained_legacy_bridge` because
  `/config` and `/opt/valheim` mounted the explicitly retained legacy state
  root and the Baseline bridge override was present;
- OMEN `http://127.0.0.1:4000` and i5 `http://100.124.12.37:4000`, with no
  credentials embedded.

The same verifier without `-AllowRetainedStateBridge` exited 1 and reported
`state_root_disposition=unknown`. This is the intended fail-closed behavior:
the bridge was visible and admitted only as an explicit interim state. The verifier is
read-only and did not restart, stop, recreate, or write to the Lab.

The Workbench rendered-C6 path now consumes that strict invocation as its first
prelive action and deliberately does not pass `-AllowRetainedStateBridge`.
After replacing the orphaned in-memory runner, job
`job-20260802-054530209-f67cfc0d` failed with
`rendered_prelive_lab_provenance_failed` and retained the structured verifier
receipt with `state_root_disposition=unknown`. It stopped before checkout/image
comparison, i5 preflight, scenario generation, or either client launch. No run
artifact was created; OMEN and i5 had zero Valheim processes, the i5 scheduled
task remained `Ready`, and OMEN's config retained SHA-256
`A141231B84010B456537B2B80360C3C0128FED2753ACFAD76DC24310A71F1F42`.

## Full Baseline state-root cutover

The migration completed at `2026-08-02T06:33:30Z` through
`fieldlab/scripts/Invoke-LabStateRootMigration.ps1`. A reusable
`tools/workbench/Test-LocalLabQuiescence.ps1` gate first proved a fresh local
Gateway heartbeat with `server_state=ready`, `peer_count=0`, an empty player
list, no OMEN Valheim process, and no backup temp file. The command then stopped
the server, reconciled the complete active server subtree, and compared 2,561
files / 57,551,976,393 bytes plus SHA-256 for the current and prior
`ComfyEra16` DB/FWL pairs. The retired tree remains unchanged as rollback. One
backup ZIP rotated between the initial failed-closed copy and the resume; it was
moved to recoverable Baseline quarantine rather than deleted.

The recreated container names only the Baseline Compose file and working
directory, mounts `/config` and `/opt/valheim` below the Baseline state root,
and passes the strict verifier with
`state_root_disposition=baseline_migrated`. The bridge override is absent from
active labels. HEARTH remains on `8710`, Workbench Dev MCP remains on loopback
`8721`, and host `8720` remains free.

## Watchdog admission and single C6 disposition

The clean Workbench build job `job-20260802-063901820-44598ee8` produced
ComfyNetworkSense SHA-256
`ec75ee07c2fcd651db353403c3692502f26d488bf35628d2721e4cac8a66cff9`
with zero warnings/errors, a read-only Valheim mount, no plugin copy, and no
host SDK. It was published as `m32-watchdog-20260802-r1`; package SHA-256 is
`88659ee974014efe0c6ebb0bebad528eaaa35778cd7abe6b3890f430c99545d7`.

OMEN installed through Workbench with a schema-1 backup. The first i5 install
request exposed a deterministic launcher gap rather than an offline machine:
the Companion still targeted `https://comfy-p7.duckdns.org`, and the request
blocked on that refused public endpoint. `Start-I5Companion.ps1` now accepts,
validates, and persists a selected Gateway; `Sync-I5Companion.ps1` forwards the
profile/Gateway choice. The repository's bounded Docker Desktop repair tool
recovered the old container after it failed to emit a stop event. One install
then succeeded through `http://100.124.12.37:4000`, and the alignment tool
reported the same release and package SHA-256 on Gateway, OMEN, and i5. Both
live DLL hashes equal `ec75ee07…cff9`.

Pre-live receipts then passed:

- strict server provenance with `state_root_disposition=baseline_migrated`;
- a fresh ready heartbeat, zero peers/players, and no backup in progress;
- clean Workbench and Dev MCP identity at revision
  `96aa8436dea9d86989d9afa929c2f2ab80aacf66`;
- ready runner, Docker, AM4, and i5 topology nodes;
- OMEN config SHA-256 `a141231b…1f42` and i5
  `fc21daab…e945`, both with canonical session/motion disabled and explicit
  local-Lab routes;
- i5 scheduled task `Ready`, both Valheim clients stopped, and matching plugin
  hashes.

Exactly one C6 job was submitted:
`job-20260802-065514705-b159b3fb`, run
`workbench-20260802-065519-b159b3fb`. It failed closed, but the watchdog made
the disposition materially different from the prior run:

- i5 observe-one passed with 113 received / 467 applied and native writer
  suppression; OMEN drive-one passed with 114 sent;
- i5 drive-two passed with 105 sent; OMEN observe-two passed with 100 received
  / 795 applied and native writer suppression;
- OMEN gap-drive passed with exactly 20 withheld frames and an accepted
  reliable resync receipt;
- OMEN advanced into disconnect/resume, so this run did not reproduce a
  persistent OMEN scenario-clock stall;
- watchdog rows reported only 2.07–2.24 second gaps, idle route state, queue
  depth zero, and zero writer faults, after which both clients advanced.

The structured timestamps identify the failure as a manifest race. i5 applied
the reliable resync for `c6-gap-omen-to-i5` at `06:57:12.417Z` while it was
still completing the prior action. Its `i5-c6-observe-gap` probe started at
`06:57:13.177Z`, reset its counter baseline after that application, and later
failed with `holds=1 gaps=0 resync_applied=0`. This is not evidence that the
gap/resync lane failed; the correlated `reliable_resync_applied` row is present
0.76 seconds before the measurement window.

The C6 generator now inserts the same bounded four-second OMEN
`gap-observer-align` action already used by C8. A new
`Test-C6ScenarioCoverage.ps1` contract verifies its duration, immediate order
before drive-gap, and shared correlation; the orchestrator invokes the contract
before i5 preflight or any remote mutation. The 24-action generated fixture
passes. No second physical run was attempted.

Cleanup receipts are complete: both exact config hashes were restored, server
motion changed `true → false`, residue cleanup matched/destroyed zero objects,
both clients stopped, and post-run quiescence again reported a fresh ready
heartbeat with zero peers and players.

## Sources

- [Workbench implementation receipt](../../plans/workbench-v1-implementation-receipt.md)
- [Workbench verification matrix](../../plans/workbench-v1-verification-matrix.md)
- [Workbench Saga strategy](../../plans/workbench-v1-saga-strategy.md)
- [PD-7 decision](../decisions/pd-7-lab-runtime-provenance-and-session-boundary.md)
