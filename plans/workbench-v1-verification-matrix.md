# Workbench v1 verification matrix

This matrix is the evidence-oriented companion to the Saga and implementation
receipt. `Passed` means the current checkout has direct evidence; `Pending` or
`Operator-gated` is intentionally not a completion claim.

| Requirement | Current evidence | Status |
|---|---|---|
| Fresh install starts Explore and cannot activate Dev/Lab before claim | Disposable current-image fixture with `LUMBERJACKS_WORKBENCH_PROFILE=Dev` returned `claimed=false`, `effective_profile=Explore`, and `build=profile_not_eligible` | Passed |
| Claimed installation persists through recreate | Final-image Lab receipt `job-20260801-175033646-fa1db4d7` preserved installation `wb-4285b4fd66f442e598886b861ed1bd44`, claim, and volume | Passed |
| Typed capabilities and deterministic eligibility | `Test-WorkbenchApi.ps1`; 11 registered capabilities; target/profile/input rejection | Passed |
| Durable jobs, events, receipts, artifacts | API contract plus rebuilt Docker build/support receipts | Passed |
| Runner authentication and ownership | API contract, authenticated heartbeat, leased-runner binding, fixtures `job-20260801-175140061-7806c4a3` and `job-20260801-180225299-6338efd4` returning HTTP 404 for stale runner events, and reproducible `Test-WorkbenchRunnerOwnership.ps1` | Passed |
| Browser mutation boundary | API contract rejects missing token and cross-site Origin/Sec-Fetch-Site | Passed |
| Standard/Advanced presentation does not grant authority | Registry eligibility is server-side; UI toggle only changes presentation labels/details, with generic Story topology labels and physical names only in Advanced | Passed by design/API shape; unfamiliar-user visual usability remains manual |
| Unified shell and compatibility routes | `Test-WorkbenchUiContract.ps1` proves `/`, `/workbench`, and `/companion` return UTF-8 HTML with no mojibake; six intent sections, responsive viewport, privacy, evidence, observation, and Gateway topology surfaces are present | Passed structurally; mobile/novice visual observation pending |
| Explore slice | Synchronous inspect/evidence jobs and topology projection | Passed |
| Build slice | Rebuilt Lab `build.mod.release` receipt; read-only Valheim mount, no host SDK, no plugin copy | Passed |
| Operate slice | Existing v0 check/install/rollback/capture adapters are wired; `operate.mod.check` reached the runner and produced deterministic `gateway_manifest_unavailable` while Gateway was offline | Partial; install/rollback and transport capture remain intentionally unrun because they can affect player-facing state |
| Recover slice | Support export passed privacy scanner; recreate verifier exists | Passed for export; recreate rerun after final image tag is recommended |
| No Docker socket / profile boundary | Compose profile verifier; default/Production contain only Companion while Dev/Lab services are explicitly profile-gated | Passed |
| Normal-gameplay Dev MCP absence on this workstation | ComfyNetworkSense now defaults MCP off, accepts only an explicit loopback origin, performs no disabled-state health polling, and refuses UI activation without Dev/Lab config. `ComfyGatewayBoot` is disabled without deletion, audited PID 14164 is stopped, host `8720` is free, and HEARTH remains on `8710` | Passed; recheck after the clean image rebuild |
| Bootstrap distribution | Clean-checkpoint package: 22 required files, runner/privacy/boundary/identity gates present, operator-private i5 README excluded, and whole ZIP privacy scan clean | Passed |
| Dev MCP shared surface | With `-McpPort 8721`, live Streamable HTTP exposed 45 tools including Workbench; MCP job `job-20260801-174027902-c22a7b5f` returned the same events/receipt shape as Web; the live authenticated identity gate passed | Passed for the dirty-checkout test image; repeat after the clean checkpoint |
| Dev MCP endpoint provenance | The live `baseline.mcp.identity.v1` response matched project, Dev profile, revision, image, published port `8721`, Workbench provider, caller registry, and Baseline ledger. The provenance audit records the retired-task disposition | Passed for current test image; clean-commit identity receipt pending |
| Active gateway launcher safety | Active launchers derive their roots/interpreters and default to explicit `:8721`; stale `ComfyGatewayBoot` was disabled without deletion and its exact retired-checkout process stopped | Passed; HEARTH unchanged on `8710` |
| Historical default-port MCP evidence | Six old Comfy-ledger calls remain quarantined; Baseline ledger now contains successful identity-gated `valheim_mcp_health`, filtered `valheim_server_log_tail`, and `valheim_handshake_trace` events on `8721` | Minimum evidence rerun passed; old receipts retained only as history |
| Clean source/image attribution before rendered work | Current rendered job failed closed with `rendered_prelive_source_dirty`; image tag now matches the actual built image | Guard passed; clean checkpoint still required |
| Rendered AM4 + OMEN + i5 C6 role reversal | Requires a clean attributed checkpoint, real clients, and Derek's typed observation | Operator-gated |
| Full Lumberjacks solution | Restore/build succeeded with 0 errors; 589 tests passed (126/250/213), with pre-existing EF dependency-conflict and test-nullability warnings | Passed |

## Current safety posture

The active local stack is temporarily in Dev for identity verification and
publishes the Baseline container only on loopback `8721`. Host `8720` is free;
HEARTH remains independent on `8710`. The implementation checkpoint is
authorized but not yet clean, so rendered acceptance remains operator-gated.
After the generator-required checkpoint pair, rebuild from the clean commit,
repeat identity and profile-absence checks, then switch explicitly to Lab for C6.
