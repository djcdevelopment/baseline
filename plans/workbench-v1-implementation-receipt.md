# Workbench v1 implementation receipt

Date: 2026-08-01
Strategy: [Saga WB-1](workbench-v1-saga-strategy.md)
Owner: Derek

Detailed requirement evidence: [verification matrix](workbench-v1-verification-matrix.md).
Checkpoint staging scope: [workbench-v1-checkpoint-scope.md](workbench-v1-checkpoint-scope.md).

This is the execution handoff for the current implementation session. It is
deliberately not a completion claim: the dirty-checkout MCP identity gate has
passed, but clean-checkpoint attribution and rendered AM4 + OMEN + i5 acceptance
still require their final machine receipt and operator observation.

## Adapted next slice

1. Complete the reviewed WB-1 checkpoint plus the generator-required
   production Workbench HTML publication commit.
2. Rebuild Companion and Dev MCP from that clean commit, record their final
   image digests, and repeat the authenticated identity check on `8721`.
3. Re-run the rendered pre-live source/image gate, then open the bounded Lab
   AM4 + OMEN + i5 C6 window and collect Derek's typed observation.
4. Close M6 by recording the final receipt and classifying remaining work.

## Milestone status

| Milestone | Status | Receipt/evidence |
|---|---|---|
| M0 baseline | partial — clean checkpoint pending | The claimed installation and retained companion-data volume are proven. The dirty-checkout Baseline Dev MCP identity passed on `8721`; the stale `ComfyGatewayBoot` task was disabled and PID 14164 stopped without touching HEARTH. Final clean-commit source/image attribution remains. |
| M1 kernel | passed | Lumberjacks/tools/companion/Test-WorkbenchApi.ps1 passed browser token, target/profile rejection, jobs, events, receipts, runner auth, and heartbeat checks. |
| M2 product shell | passed | /, /workbench, and legacy /companion return 200; Workbench V1 shell, Standard/Advanced presentation, claim flow, live topology, job cards, receipt links, and observation form are present. |
| M3 local slices | partial — Operate dependency remains open | Containerized net48 mod build passed with read-only Valheim mount, no host SDK, no plugin copy; support export passed the existing privacy scanner; safe Compose recreate preserved installation ID/claim/volume. `operate.mod.check` correctly failed closed while Gateway was unavailable. |
| M4 distribution boundary | passed | Compose profile checks prove default/Production exclude Dev MCP and the SDK runner; Dev/Lab publish the identity-attested Baseline MCP on loopback `8721`; no Docker socket exists. The mod side channel is default-off, loopback-configured, and cannot be UI-enabled without Dev/Lab opt-in. The stale logon task is disabled and host `8720` is free. |
| M5 rendered acceptance | operator-gated after clean checkpoint | AM4 and the two rendered client nodes are ready in the latest runner heartbeat. The clean source/image checkpoint and pre-live gate must pass before the physical role-reversal job begins. |
| M6 closeout | pending | Run after the rendered window and observation; classify any failure as a new defect/follow-on story. |

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
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/workbench/Test-WorkbenchMcpIdentity.ps1 -Profile Dev -McpPort 8721
    $env:PYTHONPATH = 'network/mcp'
    python -m unittest discover -s network/mcp/tests
    powershell -NoProfile -ExecutionPolicy Bypass -File Lumberjacks/tools/companion/New-CompanionBootstrap.ps1 -ReleaseId <fixture>
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/workbench/Test-WorkbenchZipPrivacy.ps1 -Path <fixture.zip>
    docker run --rm -v C:\work\baseline:/src -w /src mcr.microsoft.com/dotnet/sdk:9.0 sh -lc 'dotnet restore Lumberjacks/Game.sln && dotnet build Lumberjacks/Game.sln --no-restore'
    docker run --rm -v C:\work\baseline:/src -w /src mcr.microsoft.com/dotnet/sdk:9.0 sh -lc 'dotnet test Lumberjacks/Game.sln --no-build --no-restore --logger "console;verbosity=minimal"'

Latest runtime receipts from the rebuilt image:

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
  registry, and Baseline ledger all matched. The final clean-commit rerun remains.
- Baseline ledger events `4180248e-ce69-4124-94ca-f757b3931ed7`,
  `9529fc24-c158-4a03-8ee1-f68a3ea17a48`, and
  `e1da4b9d-1716-4f07-8b79-b1cdbed6f2fa` re-established the minimum
  `valheim_mcp_health`, filtered `valheim_server_log_tail`, and
  `valheim_handshake_trace` evidence on identity-verified `8721`.
- `ComfyGatewayBoot` was disabled without deletion; audited PID 14164 was
  stopped, host `8720` was released, and HEARTH remained on `8710` as PID 39328.
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
probe; the latest projection reports it as `offline` rather than
silently implying that the Operate update lane is ready.
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
The clean checkpoint rebuild will produce and record new acceptance digests;
these test IDs are retained instead of being overwritten.

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
loopback-configured; and the stale logon listener is retired. Only the clean
checkpoint identity rerun remains before the physical C6 window.

The full Lumberjacks solution was restored and built successfully after the
Story/Advanced topology UI change (0 errors; one pre-existing dependency-conflict
warning in `Game.Gateway.Tests`), and its three test projects passed 589 tests
total (126 Contracts, 250 Simulation, 213 Gateway).

## Operator gate for M5

The Workbench is temporarily in Dev for endpoint verification. After the
generator-required checkpoint pair, rebuild it from the clean commit and switch
to Lab. The pre-live gate also requires the clean, attributed source/image
identity. Starting
build.rendered.c6-role-reversal will launch the existing bounded
native scenario on OMEN and i5, deploy the admitted build, and exercise real
players/clients. The host runner will stop before a final receipt at
waiting_human; the operator must record:

- outcome: pass or fail;
- role_following: followed, mixed, or did_not_follow;
- quality: smooth, mixed, or rough;
- cleanup confirmation and an optional private note.

No rendered acceptance claim is made until that form is submitted and the
machine evidence plus observation share one receipt.

## Checkpoint handoff (authorized 2026-08-01)

Before committing, review the tracked and untracked scope with:

    git diff --name-only
    git ls-files --others --exclude-standard

Then stage only the reviewed WB-1 implementation, decision, plan, test, and
documentation files; run the required A7 Lumberjacks roadmap note/check in the
same implementation commit because this change touches `Lumberjacks/` and
`network/`. Leave preview-stamped `workbench.html` unstaged until the catalog
inputs are committed:

    cd Lumberjacks
    node scripts/roadmap.mjs note --milestone A7 --kind implementation --summary "Ship the local Workbench v1 control plane" --impact "Adds the owned Companion UI, profile-gated Dev MCP, bounded runner, receipts, recovery, and verification surfaces." --verification "Focused Workbench, MCP, mod, privacy, and full solution suites pass." --evidence "plans/workbench-v1-implementation-receipt.md; plans/workbench-v1-verification-matrix.md"
    node scripts/roadmap.mjs check --staged

After the implementation commit, run `npm run workbench:render`, verify it, and
commit only the production-stamped Workbench HTML. Then rebuild and rerun the
clean-source/image gate before rendered C6. No push or force-push is implied.
