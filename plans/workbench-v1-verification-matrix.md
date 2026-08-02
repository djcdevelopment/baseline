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
| Runner authentication and ownership | API contract, authenticated heartbeat, leased-runner binding, and `job-20260802-003056281-40000a1f`: stale runner HTTP 404, owning lease renewal, and exact child exit-code propagation (`0` and `7`) | Passed |
| Browser mutation boundary | API contract rejects missing token and cross-site Origin/Sec-Fetch-Site | Passed |
| Standard/Advanced presentation does not grant authority | Registry eligibility is server-side; UI toggle only changes presentation labels/details, with generic Story topology labels and physical names only in Advanced | Passed by design/API shape; unfamiliar-user visual usability remains manual |
| Unified shell and compatibility routes | `Test-WorkbenchUiContract.ps1` proves `/`, `/workbench`, and `/companion` return UTF-8 HTML with no mojibake; six intent sections, responsive viewport, privacy, evidence, observation, Gateway topology, and the first-visit safe path are present. The no-coaching newcomer protocol is ready | Passed structurally; mobile/novice visual observation pending |
| Explore slice | Synchronous inspect/evidence jobs and topology projection | Passed |
| Build slice | Rebuilt Lab `build.mod.release` receipt; read-only Valheim mount, no host SDK, no plugin copy | Passed |
| Operate slice | Existing v0 check/install/rollback/capture adapters are wired. The original `operate.mod.check` produced deterministic `gateway_manifest_unavailable`; clean Lab job `job-20260802-012104565-fc2e52f8` then passed with `mod_manifest_read` against an immutable local Gateway pointer. Topology truthfully showed Local Gateway ready and P7 excluded | Read-only check passed; install/rollback and player-active transport capture remain operator-gated because they affect or depend on player-facing state |
| Recover slice | Support export passed privacy scanner; recreate verifier exists | Passed for export; recreate rerun after final image tag is recommended |
| No Docker socket / profile boundary | Compose profile verifier; default/Production contain only Companion while Dev/Lab services are explicitly profile-gated | Passed |
| Normal-gameplay Dev MCP absence on this workstation | ComfyNetworkSense defaults MCP off, accepts only an explicit loopback origin, performs no disabled-state health polling, and refuses UI activation without Dev/Lab config. After the clean rebuild, `ComfyGatewayBoot` remained disabled without deletion, host `8720` remained free, and HEARTH remained on `8710` | Passed |
| Bootstrap distribution | Clean-checkpoint package: 22 required files, runner/privacy/boundary/identity gates present, operator-private i5 README excluded, and whole ZIP privacy scan clean | Passed |
| Dev MCP shared surface | With `-McpPort 8721`, live Streamable HTTP exposed 45 tools including Workbench; MCP job `job-20260801-174027902-c22a7b5f` returned the same events/receipt shape as Web; the clean authenticated identity gate passed | Passed |
| Dev MCP endpoint provenance | Current clean HEAD `f4d40499c22c413720474c166dd00ecb3deb02a4` returned `baseline.mcp.identity.v1` with `source_dirty=false` and matched project, Lab profile, image tag, published port `8721`, Workbench provider, caller registry, and Baseline ledger; immutable current Dev MCP image ID `sha256:1a81b41c0ef272af71e1857bcfb864edb9c4ba776e948dd60f466987fd71a133` is recorded separately | Passed |
| Active gateway launcher safety | Active launchers derive their roots/interpreters and default to explicit `:8721`; stale `ComfyGatewayBoot` was disabled without deletion and its exact retired-checkout process stopped | Passed; HEARTH unchanged on `8710` |
| Historical default-port MCP evidence | Six old Comfy-ledger calls remain quarantined; Baseline ledger now contains successful identity-gated `valheim_mcp_health`, filtered `valheim_server_log_tail`, and `valheim_handshake_trace` events on `8721` | Minimum evidence rerun passed; old receipts retained only as history |
| Clean source/image attribution before rendered work | Final pre-live receipt pinned clean HEAD `817ee8b2ff6dc30105dd44714d7709b53ecc2681`, Companion `sha256:26e47f966f0e5473ddd31f9fc7f3dd92264ee2d32caf12cb18fad2282d292f88`, and Dev MCP `sha256:938a24724dde4dfdcb77aece3c250b2db98d0798ec347681ae20e2630099f725` | Passed |
| Rendered AM4 + OMEN + i5 C6 role reversal | Job `job-20260802-003125748-116adca1`, run `workbench-20260802-003128-116adca1`: real clients completed the bounded C6 composition; Derek watched live and recorded `pass / followed / smooth`; cleanup/disarm completed | Passed; sealed reason `human_observation_recorded` |
| Full Lumberjacks solution | Restore/build succeeded with 0 errors; 589 tests passed (126/250/213), with pre-existing EF dependency-conflict and test-nullability warnings | Passed |

## Current safety posture

The active local stack is explicitly in Lab and publishes the identity-attested
Baseline Dev MCP only on loopback `8721`. Host `8720` is free; HEARTH remains
independent on `8710`. The clean machine-acceptance checkpoint is committed and
the C6 machine-plus-human receipt is sealed. The local read-only Operate check is
passed with a hash-verified release receipt. Player-impacting install/rollback,
player-active capture, and unfamiliar-user/mobile review remain classified
follow-ons, not hidden passes.
