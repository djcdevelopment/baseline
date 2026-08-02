# Workbench v1 implementation receipt

Date: 2026-08-02
Strategy: [Saga WB-1](workbench-v1-saga-strategy.md)
Owner: Derek

Detailed requirement evidence: [verification matrix](workbench-v1-verification-matrix.md).
Checkpoint staging scope: [workbench-v1-checkpoint-scope.md](workbench-v1-checkpoint-scope.md).

This is the execution handoff for the current implementation session. The
clean-checkpoint MCP/Companion attribution, rendered AM4 + OMEN + i5 machine and
human acceptance, local hash-verified Operate check, reversible install/rollback
drill, and peer-bearing player-active capture have passed. WB-1 remains a
candidate, rather than an unqualified completion claim, because the Saga's
unfamiliar-user usability gate is explicitly still open. The capture also
records a separate native-motion-only finding for the Lumberjacks motion lane.

## Closeout disposition

1. M5 is sealed. Do not rerun its physical scenario unless a future regression
   or failed observation supplies a new reason.
2. The read-only Operate check is closed on the current reversible-update image by
   `job-20260802-015026195-e3676b38`. Candidate package
   `m32-workbench-20260802-r1` is a 30/30 exact byte match for the current OMEN
   Valheim payload, with zero missing, different, or unsafe entries. Follow-on
   story WB-S3.20 now contains the approved player-active transport-capture
   receipt as well as the install-to-rollback drill. The install-to-rollback drill passed on jobs
   `job-20260802-015909355-13073d0c` and
   `job-20260802-015911118-89a57d29`. The earlier
   unavailable-Gateway receipt remains valid fail-closed evidence.
3. Community usability is follow-on story WB-S2.13: have an unfamiliar operator
   use the Standard live map and mobile layout, then record comprehension and
   recovery-path findings. The in-product first-visit path and
   [no-coaching protocol](workbench-v1-newcomer-usability-protocol.md) are ready;
   structural UI tests are not a substitute for that person.
4. No engineering defect discovered by the rendered window remains open: native
   character binding, lease renewal, the client-only evidence boundary, and
   Windows child exit-code propagation are fixed and regression-covered.
5. The pre-live rollback audit found and closed a stop-ship defect before any
   player file was changed. Install now preflights the complete archive, rejects
   unsafe or duplicate targets, serializes update operations, applies files
   atomically, restores bytes on apply/state failure, removes candidate-created
   files on rollback, and restores the prior installed-release identity. Twelve
   isolated Companion tests cover the resulting contract.

## Milestone status

| Milestone | Status | Receipt/evidence |
|---|---|---|
| M0 baseline | passed | Claimed installation `wb-4285b4fd66f442e598886b861ed1bd44` and the retained companion-data volume are proven. Final machine-acceptance HEAD `817ee8b2ff6dc30105dd44714d7709b53ecc2681` produced identity-matched Companion and Dev MCP images with `source_dirty=false`; the stale `ComfyGatewayBoot` task remains disabled and HEARTH remains independent. |
| M1 kernel | passed | Lumberjacks/tools/companion/Test-WorkbenchApi.ps1 passed browser token, target/profile rejection, jobs, events, receipts, runner auth, and heartbeat checks. |
| M2 product shell | passed | /, /workbench, and legacy /companion return 200; Workbench V1 shell, Standard/Advanced presentation, claim flow, live topology, job cards, receipt links, and observation form are present. |
| M3 local slices | passed for the current local slice | Containerized net48 mod build passed with read-only Valheim mount, no host SDK, no plugin copy; support export passed the privacy scanner; safe Compose recreate preserved installation ID/claim/volume. The read-only m32 check, approved install-to-rollback cycle, and peer-bearing player-active capture passed. The capture's native-motion-only result is recorded as a follow-on motion-lane finding, not hidden as a mod-motion pass. |
| M4 distribution boundary | passed | Compose profile checks prove default/Production exclude Dev MCP and the SDK runner; Dev/Lab publish the identity-attested Baseline MCP on loopback `8721`; no Docker socket exists. The mod side channel is default-off, loopback-configured, and cannot be UI-enabled without Dev/Lab opt-in. The stale logon task is disabled and host `8720` is free. |
| M5 rendered acceptance | passed | Run `workbench-20260802-003128-116adca1` completed on real OMEN and i5 clients against AM4. Derek watched live and recorded `pass / followed / smooth`; the sealed job receipt is `passed` with `human_observation_recorded`. |
| M6 closeout | passed | Final receipt and handoff are current. The peer-bearing player-active Operate gate is closed; the native-motion-only lane finding and unfamiliar-user/mobile review remain explicitly classified above. |

## Implemented surfaces

- Lumberjacks/src/Game.Companion/WorkbenchKernel.cs: installation ownership,
  effective profiles, typed capability registry, durable JSONL jobs/events,
  leases/interruption reconciliation, artifact hashes, receipts, runner and
  browser authentication, typed human observations, topology, and additive v1
  HTTP endpoints.
- Lumberjacks/src/Game.Companion/WorkbenchV1Page.cs: one local Home/Explore/
  Build/Operate/Recover/Community surface with a live system map and a
  presentation-only Standard/Advanced toggle. Story view uses generic
  newcomer-safe topology labels; Advanced view exposes physical node names.
- Lumberjacks/tools/companion/Start-WorkbenchHostRunner.ps1: bounded,
  allow-listed Windows execution for Docker builds, capture/update checks,
  support export, safe recreate, and rendered C6 orchestration. It accepts no
  arbitrary command or path.
- network/mcp/comfy_gateway/toolsurface/workbench.py: Dev/Lab MCP adapters
  for the same capability/job/receipt API used by the browser.
- Lumberjacks/tools/companion/docker-compose.yml: Companion base plus
  profile-gated SDK tool-runner and loopback Dev MCP; no Docker socket.
- Lumberjacks/tools/modpack/Publish-LocalModpack.ps1 and the local Gateway
  Compose contract: immutable, hash-verified Lab release publication in the
  persistent Gateway volume, with no GCP call or Valheim write. Lab selects that
  configured local Gateway by default and the topology distinguishes it from P7.
- Lumberjacks/src/Game.Companion/Program.cs and
  Lumberjacks/tests/Game.Companion.Tests: fail-closed modpack preflight,
  serialized reversible apply/rollback semantics, prior-state restoration, and
  isolated filesystem/Gateway fixtures that never touch the live Valheim tree.
- Lumberjacks/tools/modpack/Invoke-LocalWorkbenchModRollbackDrill.ps1 and the
  host runner's Windows process gate: an explicit-consent, evidence-producing
  wrapper over the same Workbench jobs. Legacy schema-0 rollback is unavailable
  in both UIs/API, and no-peer captures no longer produce green job receipts.
- Source/package/i5 launchers: explicit Explore/Admin/Dev/Lab/Production
  profile selection, local runner-token generation outside the checkout,
  profile convergence, and hidden host-runner startup.
- ComfyNetworkSense: the development MCP/Raven side channel is default-off,
  uses one configurable loopback-only origin, and cannot be enabled from the
  in-game transport toggle unless Dev/Lab configuration first opts in.
- Active MCP launchers now derive the Baseline root/interpreter and default to
  explicit `:8721`. The retired `ComfyGatewayBoot` task is disabled but retained
  for recoverability; its retired-checkout PID was stopped and `:8720` released.

## Verification commands

    docker run --rm -v C:\work\baseline:/src -w /src mcr.microsoft.com/dotnet/sdk:9.0 dotnet build Lumberjacks/src/Game.Companion/Game.Companion.csproj --no-restore
    powershell -NoProfile -ExecutionPolicy Bypass -File Lumberjacks/tools/companion/Test-WorkbenchApi.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File Lumberjacks/tools/companion/Test-WorkbenchRunnerOwnership.ps1 -ExpectedProfile Lab
    powershell -NoProfile -ExecutionPolicy Bypass -File Lumberjacks/tools/companion/Test-WorkbenchUiContract.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File Lumberjacks/tools/companion/Test-WorkbenchComposeProfiles.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/workbench/Test-WorkbenchMcpIdentity.ps1 -Profile Lab -McpPort 8721
    $env:PYTHONPATH = 'network/mcp'
    python -m unittest discover -s network/mcp/tests
    powershell -NoProfile -ExecutionPolicy Bypass -File Lumberjacks/tools/companion/New-CompanionBootstrap.ps1 -ReleaseId <fixture>
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/workbench/Test-WorkbenchZipPrivacy.ps1 -Path <fixture.zip>
    docker run --rm -v C:\work\baseline:/src -w /src mcr.microsoft.com/dotnet/sdk:9.0 sh -lc 'dotnet restore Lumberjacks/Game.sln && dotnet build Lumberjacks/Game.sln --no-restore'
    docker run --rm -v C:\work\baseline:/src -w /src mcr.microsoft.com/dotnet/sdk:9.0 sh -lc 'dotnet test Lumberjacks/Game.sln --no-build --no-restore --logger "console;verbosity=minimal"'

Latest runtime receipts from the rebuilt image:

- Pre-player-install safety checkpoint: clean source
  `1456de1142658e972f9e0462d24b3f3ba143d4ce`, Companion image
  `sha256:b8ef890ee0db59417eb495830b8c2a3a7e79db4e3b82ac6e4b24c02861305d6b`,
  and Dev MCP image
  `sha256:12549a4ad59b224572ee323c2ad7767c01680a6e94f7b7febcd2cd8c1ad4e334`.
  UI, API, runner, and authenticated MCP identity gates passed with
  `source_dirty=false`. Current installed state is legacy m31 schema 0 and the
  live DLL is SHA-256
  `1e875984fde1b81895beaf70a3ad99db832a330257788d2f8ccfd6db7f4fe6a7`;
  rollback is projected as `eligible=false / rollback_not_available`. The v0
  negative control returned HTTP 400
  `rollback_not_reversible_legacy_state` with installed JSON and DLL hash
  unchanged. Valheim process and updater temporary-residue counts are zero.
- Approved reversible live drill: install job
  `job-20260802-015909355-13073d0c` succeeded with
  `mod_install_complete`, candidate m32 transaction schema 1, prior release m31,
  zero created files, and a present backup. Rollback job
  `job-20260802-015911118-89a57d29` succeeded with
  `mod_rollback_complete` and no recovery fallback. All 30 files matched with
  zero different/missing/unsafe entries before, during, and after; the original
  m31 installed-state JSON was restored exactly.
- Subsequent hands-on actions exposed two now-closed UX defects. Legacy rollback
  job `job-20260802-021215350-f904f441` reapplied a schema-0 backup and moved the
  live DLL to the original m31 hash because the old record had no prior identity.
  Capture job `job-20260802-021217921-2851b5ea` returned `no_peer_window` but the
  old runner labeled the operation successful. Current code disables/refuses
  legacy rollback and classifies no-peer/incomplete captures as failed evidence.
- Approved player-active checkpoint: after explicit admission, Workbench install
  job `job-20260802-023656082-3e059774` left m32 active with transaction schema 1
  and backup `/data/backups/20260802T023657172Z-m32-workbench-20260802-r1-b0151be5`.
  The exact m32 plugin SHA-256
  `93877e4d12291aec53cdaaeda22f9e992eaf9eb7240bbe1380daa41e8ab349d9` was
  verified on both OMEN and i5. OMEN `Tugcorp` and i5 `durracktu` joined AM4
  through `100.116.82.60:2456`. Workbench capture job
  `job-20260802-025242918-32e66e98` passed with capture run
  `20260802-025243-workbench-job-20260802-025242918-32e66e98`; its durable
  summary recorded `max_peers=2`, three samples, zero bad samples, and verdict
  `native_motion_only`. The same summary records zero Lumberjacks motion-counter
  delta and disconnected motion WS/UDP, so the peer-bearing transport gate passes
  while the mod-motion lane remains a separately classified follow-on. The stale
  queued jobs that made the first submission return `runner_unavailable` were
  cancelled before the runner was restarted; no stale player-impacting job ran.
- Pre-drill reversible-update checkpoint: clean source
  `0526c69e7522590b21b8760cc3eb91b126749e3a`, Companion image
  `sha256:08bc0f389f85ba825452c6d3a2b50452cbc76bb814599cc87e977a3a89acbcec`,
  and Dev MCP image
  `sha256:22b3c8f842d1d4ff1fabc12b38e65a5552471a876ec02025539fb8607f09aa91`.
  API, runner ownership, UI, Compose, and authenticated Lab MCP identity checks
  passed with `source_dirty=false`. Focused Companion tests passed 11/11 and the
  full solution passed 604 tests. Read-only Operate job
  `job-20260802-015026195-e3676b38` returned `mod_manifest_read` for m32, and a
  fresh exact-match preflight again reported 30 matched, zero different, zero
  missing, and zero unsafe entries. Valheim process count was zero; no install,
  rollback, installed-state, GCP, or player-facing mutation occurred.
- Initial byte-audited candidate checkpoint: source
  `625c033f4b42af51e67557257e855700f0a0e0b9`, Companion image
  `sha256:f0b0b364633c43e14c1901e8effb4b9781d8f8e912981244a806ae31996c800e`,
  and Dev MCP image
  `sha256:818848118f1888ea1df82f1a047b36fc6381576deebd23a5588701374284f5f6`.
  The authenticated MCP identity gate passed on loopback `8721` with
  `source_dirty=false`.
- First clean Lab Operate checkpoint: source
  `f4d40499c22c413720474c166dd00ecb3deb02a4`, Companion image
  `sha256:d85c078fdfcad8739f62317f2f8956af1d45b57441ab6c0df55f87fda947569f`,
  and Dev MCP image
  `sha256:1a81b41c0ef272af71e1857bcfb864edb9c4ba776e948dd60f466987fd71a133`.
  The clean MCP identity gate passed on loopback `8721`. The topology reported
  `Local Gateway / target=local / ready` and separately `P7 / excluded`.
- `job-20260802-012104565-fc2e52f8` — read-only `operate.mod.check`
  passed with `mod_manifest_read` against local immutable release
  `m30-rolecontrol-20260723-r1`, package SHA-256
  `d1bfcd6f440fe9697cf495eac16923bcc9272225039b2ace69a23d1d302cbb5a`.
  The publisher changed only the persistent local release feed; no Valheim file,
  install state, rollback state, or GCP resource was changed.
- Pre-drill install/rollback candidate `m32-workbench-20260802-r1` was built from
  the live OMEN payload without writing to it. `Test-ModpackPayload.ps1
  -RequireExactMatch` reported 30 matched entries, zero different, zero missing,
  zero unsafe, and package SHA-256
  `c5144045ede921ba37d84350bd8d0378c7a6eef5714dc427677777be35ecb6db`.
  Clean Workbench job `job-20260802-013242046-49017a94` then passed with
  `mod_manifest_read` at source `625c033f4b42af51e67557257e855700f0a0e0b9`.
  Valheim was closed and no install or rollback was invoked.
- Final clean Lab checkpoint: source
  `817ee8b2ff6dc30105dd44714d7709b53ecc2681`, Companion image
  `sha256:26e47f966f0e5473ddd31f9fc7f3dd92264ee2d32caf12cb18fad2282d292f88`,
  and Dev MCP image
  `sha256:938a24724dde4dfdcb77aece3c250b2db98d0798ec347681ae20e2630099f725`.
  The authenticated Baseline identity gate passed on loopback `8721` with
  `profile=Lab` and `source_dirty=false`.
- `job-20260802-003125748-116adca1` / run
  `workbench-20260802-003128-116adca1` — the bounded real AM4 + OMEN + i5 C6
  run passed. Derek's live observation was `pass / followed / smooth`, with
  cleanup confirmed and note `Watched live: very exciting; looked smooth.` The
  sealed receipt is `passed / human_observation_recorded` with evidence boundary
  `machine_evidence_plus_operator_observation`. Its admitted
  `ComfyNetworkSense.dll` hash is
  `93877e4d12291aec53cdaaeda22f9e992eaf9eb7240bbe1380daa41e8ab349d9`.
- The runner-ownership fixture `job-20260802-003056281-40000a1f` proved stale
  runner HTTP 404, active lease renewal, and exact child exit-code propagation
  (`0` and `7`) without executing an external operation.
- Diagnostic run `workbench-20260801-235831-a914118d` proved that reliable
  peer binding now carries native character identity and restored two-way C6
  motion, while exposing the original 90-second lease limit.
- Diagnostic run `workbench-20260802-002443-1ce9198d` produced a completed
  two-client composition plus clean AM4 disarm/residue receipts. It exposed two
  orchestration-only assumptions: a dedicated server cannot emit the
  client-only motion file, and Windows PowerShell `Start-Process -PassThru`
  cannot supply the child exit code. Both now have focused regression receipts.

- `job-20260801-171711723-6af10687` — Docker mod build succeeded; `ComfyNetworkSense.dll`
  SHA-256 `589c371e384c7b1e490f89145ad0fc1aca88d2e0a016454fb2eb2fad8b1aa013`.
- `job-20260801-171733582-4b5fd835` — support export succeeded and registered a
  `public_safe` artifact after the privacy scanner.
- Claimed-owner Admin test receipt — `claimed=true`, installation
  `wb-4285b4fd66f442e598886b861ed1bd44`, `effective_profile=Admin`, Dev MCP
  excluded, and Companion image
  `sha256:c58c2c26edc9f325f3b533f68771045892040c1c09403955dc3618750ee47e87`.
- `job-20260801-172717121-8b5a9819` — rebuilt Lab Docker mod build succeeded;
  the artifact hash remained stable and was registered in the receipt.
- `job-20260801-172730430-9b1a09f6` — rebuilt Lab support export succeeded and
  passed the privacy gate.
- `job-20260801-175033646-fa1db4d7` — final-image Lab recreate verification
  passed; installation `wb-4285b4fd66f442e598886b861ed1bd44` and claim state
  were preserved with `volume_preserved=true`.
- `job-20260801-175140061-7806c4a3` — runner-ownership fixture leased a
  support-export job as `ownership-fixture`; a stale runner event received HTTP
  404, and the owning runner completed the fixture. No support export was
  executed by this fixture.
- `job-20260801-175655093-4eaa9652` — non-destructive `operate.mod.check`
  reached the runner and failed with deterministic `gateway_manifest_unavailable`
  while the configured Gateway was unreachable; no install, rollback, or player
  state was touched.
- `job-20260801-180225299-6338efd4` — the source-controlled
  `Test-WorkbenchRunnerOwnership.ps1` fixture passed in Lab: stale event HTTP
  404, owning completion accepted, and `executed_external_operation=false`.
- `Test-WorkbenchUiContract.ps1` passed against the claimed Admin shell: all
  three compatibility routes, six intent sections, responsive viewport,
  presentation toggle, evidence links, privacy text, and observation flow were
  structurally present. It now also asserts `text/html; charset=utf-8` and rejects
  mojibake characters; the rebuilt UI and API contracts passed. Human
  mobile/novice observation remains open.
- `job-20260801-172741054-f940b244` — rendered capability was refused before
  client orchestration with `rendered_prelive_source_dirty`.
- MCP profile check on loopback port `8721` exposed 45 tools including
  `workbench_capabilities`;
  MCP-created job `job-20260801-174027902-c22a7b5f` reached `succeeded` with the
  same two events and receipt shape as the browser API.
- The live dirty-checkout identity gate passed on `8721`: project `baseline`,
  profile `Dev`, revision `66c80dcec04ff10f0467e36b83d224bb6e22d745`, image
  `lumberjacks-companion-dev-mcp:local`, Workbench provider, Baseline caller
  registry, and Baseline ledger all matched. The later clean Lab rerun is
  recorded at the top of this section.
- Baseline ledger events `4180248e-ce69-4124-94ca-f757b3931ed7`,
  `9529fc24-c158-4a03-8ee1-f68a3ea17a48`, and
  `e1da4b9d-1716-4f07-8b79-b1cdbed6f2fa` re-established the minimum
  `valheim_mcp_health`, filtered `valheim_server_log_tail`, and
  `valheim_handshake_trace` evidence on identity-verified `8721`.
- `ComfyGatewayBoot` was disabled without deletion; audited PID 14164 was
  stopped, host `8720` was released, and HEARTH remained on `8710` as PID 39328.
- Clean checkpoint `0444fe90fac8928d486ebd2186fabe4b94b86d2a` rebuilt with
  `source_dirty=false`. Companion image
  `sha256:0260d9e78c73f3f3315b06423bb48afab3bb1411dfa8dd4c3e28bb353b062c62`
  and Dev MCP image
  `sha256:f2777cde901587eed5fabf5fbe2b514caf64ee48477862bdbf6734f4de3dff37`
  were recorded. The authenticated `8721` identity matched Baseline, Dev,
  revision, provider set, caller registry, and ledger. The claimed installation
  ID remained unchanged; `ComfyGatewayBoot` remained disabled, host `8720`
  remained free, and HEARTH remained on `8710`.
- Boundary-audit bootstrap package `workbench-v1-boundary-audit` passed with 20
  required files, including the read-only profile-boundary checker.
- Runner/Gateway bootstrap package `workbench-v1-runner-gateway` passed with 20
  required files after the explicit-profile runner and Gateway topology changes.
- Story-view bootstrap package `workbench-v1-story-view` passed with 20 required
  files after the generic Standard topology presentation was added.
- Story-surface bootstrap package `workbench-v1-story-surface` passed with 20
  required files after capability/job target labels were made generic in Standard.
- Endpoint-provenance bootstrap package `endpoint-provenance-adaptation` passed
  with 21 required files after the authenticated identity checker was added to
  the distributable toolkit.
- Clean-checkpoint bootstrap package `workbench-v1-clean-checkpoint` passed with
  22 required files and a clean whole-package privacy scan. Packaging now omits
  the operator-private i5 README, ships a transport-neutral SSH-alias preflight,
  and treats the bundled privacy scanner's deliberate deny-pattern fixtures as
  scanner source rather than exported private data.

Audit hardening applied after the first receipt: launcher source identity now
includes untracked files; fresh installations cannot activate Dev/Lab/Production
before claim; job inputs are capability-whitelisted before persistence; runner
state/artifact/completion calls are bound to the leased runner ID; remote
heartbeat probes are cached; and the UI exposes events, receipts, artifacts, and
active job phases.
The host runner now receives the selected profile explicitly from source,
bootstrap, and i5 launchers instead of relying only on inherited environment
state. Recreate verification logs the selected profile and allowed/running
container names before failing closed on an unexpected service.
The topology now includes a Gateway node backed by a bounded, cached heartbeat
probe and classifies its configured origin as local, P7, or remote. The current
Lab projection reports `Local Gateway / ready` and keeps the separate P7 node
excluded, rather than labeling any configured Gateway as P7.
Compose now tags the built Companion image with the same identity exposed in
the projection, so the rendered preflight can inspect the exact image rather
than a decorative label.
The claimed Admin test projection reports image
`lumberjacks-companion-companion:local` with image ID
`sha256:c58c2c26edc9f325f3b533f68771045892040c1c09403955dc3618750ee47e87`.
That Admin snapshot remains a retained dirty-checkout test receipt. The later
dirty Dev identity stack uses Companion image
`sha256:e0738b2ebcbd69de95f620b9f8c46bb01a7d77a4c06b80db7e338fa82bc27141`
and Dev MCP image
`sha256:18af8f8d19f10ecb9bcf996ec49507f5a11230821882d14b7831bc02dc6e6b10`.
The final clean Lab rebuild and its acceptance digests are recorded above;
these earlier test IDs are retained instead of being overwritten.

## Checkpoint commit provenance

The shared checkout advanced while the reviewed Workbench index was staged.
Concurrent guide commit `76b01b9` therefore contains both the guide work and the
complete Workbench implementation plus A7 roadmap receipt. No history was
rewritten. Generator publication remains independently attributable:
`9913629` contains only the production-stamped Workbench HTML, and `0444fe9`
contains only receipt whitespace normalization. The clean identity receipt above
is tied to the resulting `0444fe9` tree, not to the earlier dirty image.

The read-only boundary audit identified it as PID 14164, `python.exe` running
the older `comfy_gateway` matrix provider, and returned
`external_mcp_listener_present`. A further read-only provenance check found
that its parent command is the old
`C:\work\comfy\fieldlab\scripts\start-comfy-gateway.cmd`, with
`C:\work\comfy\network\mcp` on `PYTHONPATH`. The current checkout does have a
similarly named `C:\work\baseline\fieldlab\scripts\start-comfy-gateway.ps1`,
but PID 14164 was not launched from that path. The old wrapper's comments also
reference the HEARTH/commandcenter wrapper lineage. A second read-only audit
found the enabled `ComfyGatewayBoot` scheduled task, whose logon action is that
same old wrapper; it last ran at 2026-07-30 20:22:37 and launched PID 14164 two
seconds later. HEARTH is separately supervised by `HearthGatewayBoot` from
`C:\work\commandcenter\hearth\etc\start-hearth-gateway.cmd` and has its own
listener on 127.0.0.1:8710. The evidence therefore points to a retained old
Baseline/Comfy task, potentially left by earlier work in the retired checkout,
not the HEARTH listener. Derek subsequently authorized retirement: the task is
disabled but not deleted, PID 14164 is stopped, `8720` is free, and HEARTH is
unchanged.

At audit time the endpoint was not project-unique: both
`C:\work\baseline\.mcp.json` and `C:\work\comfy\.mcp.json` targeted
`http://127.0.0.1:8720/mcp` with the same caller key. Active Baseline config now
uses explicit `:8721`; the retired Comfy config still names `:8720`, while its
scheduled task is disabled and no listener remains on that port. In
the last 48 hours the old Comfy ledger recorded six default-port Valheim calls
(`valheim_mcp_health`, four `valheim_server_log_tail` calls, and
`valheim_handshake_trace`). The current Baseline ledger recorded four
`workbench_*` calls at 2026-08-01T17:40Z; those were made through the explicit
alternate development port and are not evidence that the old 8720 listener
served Workbench. This means yesterday's default MCP Valheim calls were indeed
served by the retired `C:\work\comfy` source tree, while direct HTTP, Lumberjacks
gateway, and explicit alternate-port calls remain separate paths.

Replan disposition: the six default-port Valheim receipts remain quarantined
historical artifacts. The authenticated Baseline identity gate and minimum
health/log/handshake rerun passed on `8721`; the mod helper is default-off and
loopback-configured; and the stale logon listener is retired. The clean
checkpoint identity rerun and physical C6 machine window subsequently passed.

The full Lumberjacks solution was restored and tested successfully after the
reversible-update change (0 errors; the pre-existing EF dependency-conflict
warning remains in `Game.Gateway.Tests`). Its four test projects passed 605 tests
total: 126 Contracts, 250 Simulation, 217 Gateway, and 12 Companion.

## M5 sealed acceptance

The Workbench joined Derek's live `pass / followed / smooth` observation to the
machine result for `job-20260802-003125748-116adca1`. Both clients completed
their scenario actions, AM4 authority was disarmed, and run-scoped residue
cleanup reported zero matches. The final receipt is addressable through the
Workbench and limits its claim to
`machine_evidence_plus_operator_observation`.

## Current operator gate

The reversible install-to-rollback drill and separately approved player-active
window are complete. The machine is in a stable, hash-recorded m32 state with a
schema-1 rollback record; both client payloads are exact m32 and both game
processes were stopped after capture.

1. Keep m32 active for the next intentional test window, or explicitly invoke
   the now-eligible schema-1 rollback if returning to m31 is desired.
2. Treat `native_motion_only` as proof of native two-peer transport presence, not
   as proof that the Lumberjacks motion lane is connected; investigate the
   recorded `canonical_session_waiting`/WS-UDP gap in a separate development loop.
3. `no_peer_window` and `incomplete_telemetry` remain failed evidence, not green
   completion.

No further install, rollback, game launch, push, or force-push is implied by the
completed player-active authorization.
