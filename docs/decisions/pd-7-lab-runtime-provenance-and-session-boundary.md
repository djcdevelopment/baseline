# PD-7 — Lab runtime provenance and canonical session boundary

- Status: adopted; the historical state-root migration and canonical motion diagnostic are complete
- Owner: Derek
- Trigger: satisfied 2026-08-02; future Lab runtime work belongs to `lumberjacks-platform`
- Date: 2026-08-02

> **Authority amendment — 2026-08-12.** This decision remains the canonical
> fleet-level rationale for attributable Lab runtime state and explicit client
> routes. Active implementation, Compose state, verification scripts, and new run
> receipts now belong to
> [`lumberjacks-platform`](https://github.com/djcdevelopment/lumberjacks-platform/tree/main/fieldlab).
> “Baseline,” its state root, and its script paths below describe the completed
> pre-split migration; they are historical evidence, not current hub paths or
> runnable instructions. The referenced
> [`Test-LabRuntimeProvenance.ps1`](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/scripts/Test-LabRuntimeProvenance.ps1)
> and
> [`Invoke-LabStateRootMigration.ps1`](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/scripts/Invoke-LabStateRootMigration.ps1)
> remain inspectable at the sealed extraction revision.

## Decision to make

The local Valheim Lab must have one attributable runtime source and one explicit
Gateway route per rendered node. The canonical Lumberjacks game-session lane is
Lab-only; normal player gameplay must not keep retrying it.

At adoption, the short-term Baseline-compose/retained-state bridge was the
accepted interim choice. The long-term full state cutover was then executed;
the bridge remained only as a recoverable rollback path and was not part of the
active Compose attribution recorded by this decision.

## Evidence

- The successful peer-bearing capture was `job-20260802-025242918-32e66e98`.
  It proved two native Valheim peers, but recorded
  `native_motion_only`, `canonical_session_waiting`, WebSocket disconnected, and
  UDP not ready.
- Before the bridge, OMEN and i5 both had `lumberjacksGameSessionEnabled = true`
  and `lumberjacksGatewayUrl = http://8.231.129.249:42317`. That endpoint was
  not the active local Lab Gateway. After the bridge, OMEN uses
  `http://127.0.0.1:4000`, i5 uses `http://100.124.12.37:4000`, and both
  session/motion switches are disabled at rest.
- The local Gateway health endpoint is green on `http://127.0.0.1:4000`; i5 can
  reach OMEN's Tailscale address `100.124.12.37:4000`.
- `docker inspect comfy-valheim-lab-valheim-server-1` reports the retired
  compose source `C:\work\comfy\fieldlab\autonomous\valheim-lab.compose.yml`,
  a temporary Claude override, and retired state mounts. The Gateway container
  was rebuilt from Baseline, so the project currently has mixed container
  provenance.

## Viable alternatives

1. **Full state cutover (recommended for the long term):** stop the Lab,
   preserve a verified world/config backup, move the retained state under
   `C:\work\baseline\fieldlab\autonomous\state`, then recreate every Lab
   service from the Baseline compose file. This gives one root and one rebuild
   story, but requires a large world/state copy and a restart window.
2. **Baseline compose, retained state root (short-term bridge):** recreate the
   server using the Baseline compose and explicitly bind the existing world
   state while the migration is scheduled. This removes stale source provenance
   without copying the live world, but leaves a deliberate legacy data-root
   exception that must be visible in the Workbench status.
3. **Leave the mixed runtime as-is:** no migration cost, but source edits can
   again miss the live server and a future operator cannot tell which checkout
   owns the Lab. This is rejected as a product posture.

## Required implementation shape

- Record `compose config_files`, `working_dir`, image digest, and state-root
  disposition in every Lab acceptance receipt.
- Require an explicit Gateway URL for a rendered client Lab run: OMEN uses the
  local Gateway route and i5 uses OMEN's reachable Tailscale route. Production
  or P7 routes remain explicit, never inferred from a stale client config.
- Make the Admin/Production player posture disable the canonical game-session
  and motion side channels. Lab is the only profile that may enable them.
- Add a preflight/readiness row that fails closed when a client's configured
  session endpoint is unreachable or when the active Lab compose source is not
  Baseline-attributed.

The bridge now satisfies the source-attribution portion of this shape. OMEN and
i5 have explicit local-Lab routes and both side channels are disabled at rest.
The gateway Dockerfile restore defect found by the first C6 retry is fixed, but
the second retry (`job-20260802-034806539-ce87afb7`) reached both clients and
recorded i5 `session_started`, but failed at `i5-c6-rendezvous` after UDP reset
and binary-WebSocket fallback; OMEN consequently received zero observation
samples and failed at `omen-c6-observe-two`. The i5 task's
`LastTaskResult=1` reflects that scenario failure. Failure-run evidence
retention is now implemented in the orchestrator cleanup path; the
canonical-session motion rendezvous and full state migration remain open.

The transport trace corrected the initial interpretation of that failure. The
same UDP-reset-to-WebSocket fallback appears in historical successful C6
receipts, so fallback is not itself a new regression. The post-bridge run
instead started OMEN at `(2216.321,33.405,-54.053)` and i5 at
`(3192.725,29.722,2377.365)`, outside the Gateway's player-interest edge. No
remote descriptor reached i5, and the intentionally fail-closed
`TryRendezvous` implementation had no remote snapshot from which to move the
player. The retained-state bridge therefore exposed an unstated C6 placement
fixture, not a reason to widen normal gameplay routing.

A subsequent safe-origin attempt (`job-20260802-041714198-5cb8449a`) revealed a
second, independent preflight omission: the clients were correctly restored to
the Admin-at-rest posture, but the Lab runner did not temporarily enable the
canonical session/motion settings. No current `session_started` or motion frame
was published, so the attempt failed before it could test the interest-edge
fixture. The client harness now requires an explicit Lab-session switch for
C6/C8, records the pre-run config bytes, enables only those two settings for the
bounded smoke, and restores the exact prior bytes on success or failure.

The canonical Docker Workbench build is now recorded by
`job-20260802-044059503-235d215a`; it succeeds without a host .NET Framework
SDK, using a read-only Valheim mount and no plugin copy. A bounded retry after
correcting the safe-origin fixture to the retained world's ground plane
(`job-20260802-044127818-e060cb19`, run
`workbench-20260802-044133-e060cb19`) reached `session_started`, peer binding,
UDP-reset/WebSocket fallback, interest-edge discovery, rendezvous, and passing
initial observe/drive probes on i5. OMEN then stalled in the rendered Unity
world/UI loop after `omen-settle` began, so i5's dependent observe-gap action
failed closed. This is a rendered client forensics blocker, not a route,
session-start, transport, or interest-routing defect. The failed run retained
both bundles. Its force-stop also demonstrated why cleanup needs a durable
restore action: i5 restored normally and OMEN was restored explicitly from the
prior exact Admin-at-rest backup; both now have the canonical side channels
disabled at rest.

The targeted follow-up build
`job-20260802-045218754-f432d3af` added a Lab-only reassertion of Unity's
background-execution setting at the first real peer boundary. The bounded
single-client observation `workbench-bg-reassert-20260802` passed the post-join
scenario clock, proving that narrow fix. One justified full C6 run against the
same DLL (`job-20260802-045616258-030c0534`, run
`workbench-20260802-045621-030c0534`) still failed closed at
`i5-c6-observe-gap`. OMEN reached session start, peer binding, and local motion
identity, but stopped advancing after `omen-settle` while the concurrent
rendered world/peer load was active. i5 completed safe-origin, rendezvous,
observe-one, and drive-two with no motion failures before the dependent gap
observation timed out. Because the post-join reassertion is present in OMEN's
log, this is now a concurrent rendered main-loop/peer-load investigation, not
an endpoint, Docker build, interest-edge, or WebSocket fallback failure. No
blind C6 retry is authorized until bounded forensics or main-thread budget
instrumentation produces a new discriminating result.

The historical `.NET Framework/net48` build workaround remains the Docker
Workbench image; host SDK MSB3644 is an expected boundary, not a reason to
introduce a second host build lane.

The next diagnostic slice adds a worker-thread main-loop watchdog that writes
one `perf-watchdog.jsonl` row after a bounded heartbeat gap and collects it in
the native client evidence bundle. The Workbench runner now also records
checkout-time source identity in build receipts and rejects rendered C6 before
launch when the checkout is dirty or the Companion image revision does not
match it. This prevents a diagnostic dirty build from masquerading as a clean
runtime acceptance.

The read-only
[`Test-LabRuntimeProvenance.ps1`](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/scripts/Test-LabRuntimeProvenance.ps1)
verifier then closed the provenance preflight requirement without changing the
running Lab.
Against `comfy-valheim-lab-valheim-server-1`, it passed the Baseline Compose
file/working-directory checks, found no retired Compose source, recorded the
server image digest `sha256:e8b13da3c44f54a38511c8ac224f2959a437c0b2626cf916683ca7acc8dfb146`,
validated the credential-free OMEN (`http://127.0.0.1:4000`) and i5
(`http://100.124.12.37:4000`) routes. Before migration it classified the state
root as `retained_legacy_bridge`; omitting explicit bridge admission correctly
exited 1 with `state_root_disposition=unknown`.

Rendered C6 now invokes that strict form before every other prelive action and
does not admit the interim bridge. Job `job-20260802-054530209-f67cfc0d`
therefore failed with `rendered_prelive_lab_provenance_failed` before source or
image checks, remote preflight, scenario generation, or either client launch.
The receipt retained the failed `state_root_disposition` check; no run artifact
was created, both clients remained stopped, and the Admin-at-rest OMEN config
hash remained unchanged. This makes the recorded full migration a real gate,
not a handoff note an acceptance run can bypass.

## Full state migration receipt

[`Invoke-LabStateRootMigration.ps1`](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/scripts/Invoke-LabStateRootMigration.ps1)
completed the cutover at
`2026-08-02T06:33:30Z`. Its tools-layer quiescence gate required a fresh local
Gateway heartbeat with `server_state=ready`, `peer_count=0`, an empty player
list, no OMEN Valheim process, and no in-progress world backup before stopping
the server. The stopped retained source and Baseline target matched at 2,561
files and 57,551,976,393 bytes. SHA-256 matched for the current and prior
`ComfyEra16` database and world identity files. The retired source remains
untouched as rollback; one backup ZIP rotated between the failed-closed first
copy and the resumed copy was moved to a recoverable Baseline quarantine rather
than deleted.

The recreated server now reports only
`fieldlab/autonomous/valheim-lab.compose.yml` in its Compose labels, mounts both
`/config` and `/opt/valheim` under the Baseline state root, retains immutable
server image digest
`sha256:e8b13da3c44f54a38511c8ac224f2959a437c0b2626cf916683ca7acc8dfb146`,
and passes the strict verifier with `state_root_disposition=baseline_migrated`.
The retired bridge override is no longer active.

## Clean watchdog diagnostic disposition

The single authorized diagnostic was Workbench job
`job-20260802-065514705-b159b3fb`, run
`workbench-20260802-065519-b159b3fb`, from clean image-matched revision
`96aa8436dea9d86989d9afa929c2f2ab80aacf66`. OMEN and i5 both ran DLL SHA-256
`ec75ee07c2fcd651db353403c3692502f26d488bf35628d2721e4cac8a66cff9`.
Strict provenance, source/image identity, i5 readiness, both explicit routes,
and Admin-at-rest hashes passed before launch.

The result changes the forensic classification. OMEN completed drive-one,
observe-two, and gap-drive; i5 completed observe-one and drive-two. Watchdog
rows on both machines recorded bounded 2.07–2.24 second gaps with idle route
state and zero writer faults, after which both scenario clocks advanced. The
prior persistent OMEN main-loop-stall hypothesis is therefore rejected for this
run.

The actual failure was ordering in the C6 fixture. i5 applied reliable resync
correlation `c6-gap-omen-to-i5` at `06:57:12.417Z`, while its `observe_gap`
probe began at `06:57:13.177Z`. The probe correctly measured zero new gap and
resync counters because the expected event had already happened. The C6
manifest now reuses C8's bounded four-second OMEN observer-alignment action,
and `Test-C6ScenarioCoverage.ps1` fails before i5 preflight or remote mutation
unless that action immediately precedes gap drive and shares the observer's
correlation. Its generated 24-action fixture passes. The one-run stop rule ended
that diagnostic cycle without a retry.

After separate authorization, Workbench job
`job-20260802-072520719-74b07483`, run
`workbench-20260802-072523-74b07483`, physically validated the corrected order
from clean image-matched revision
`6a594cf4e4a34f4f70390f73442bd4ef7b92883b`. i5 began observe-gap at
`07:27:12.752Z`; OMEN completed the four-second alignment and began drive-gap at
`07:27:17.675Z`. OMEN withheld exactly 20 frames and accepted reliable resync;
i5 completed with `holds=1 gaps=1 resync_applied=1`. Both clients then emitted
`scenario_complete`, resumed once, stopped, and restored their original config
hashes. The Workbench job remains `waiting_human` because no new human
observation was supplied; its machine result is
`rendered_role_reversal_complete`.

Failure cleanup passed: both exact Admin-at-rest config hashes were restored,
server motion was disarmed, residue cleanup matched zero objects, both clients
stopped, and a fresh local heartbeat returned to zero peers/players. The
corrected scenario-ordering gate and PD-7 motion follow-up are now complete;
this is not a runtime-source decision or another forensic retry.

## Acceptance

The decision is complete when one option is recorded here, the active server
and Gateway containers report the chosen provenance, both client routes are
machine-readable without exposing credentials, a failed run retains both client
evidence, and a bounded two-client run records `session_started`, peer binding,
the initial player-interest/rendezvous preflight, and a deterministic motion
rendezvous before any motion verdict is considered. The preflight must either
prove both players are within the Lab interest radius or name and authorize a
  test-scoped bootstrap; it must not silently widen normal gameplay routing.
The rendered harness must also prove that Lab-only session activation was
explicit and that the Admin-at-rest config was restored with a matching hash.
