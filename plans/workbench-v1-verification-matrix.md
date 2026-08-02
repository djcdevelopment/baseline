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
| Runner authentication and ownership | API contract, authenticated heartbeat, leased-runner binding, and current fixture `job-20260802-015005516-d0741770`: stale runner HTTP 404, owning lease renewal, exact child exit-code propagation (`0` and `7`), and no external operation | Passed |
| Browser mutation boundary | API contract rejects missing token and cross-site Origin/Sec-Fetch-Site | Passed |
| Standard/Advanced presentation does not grant authority | Registry eligibility is server-side; UI toggle only changes presentation labels/details, with generic Story topology labels and physical names only in Advanced | Passed by design/API shape; unfamiliar-user visual usability is `TODO — Derek soon` |
| Unified shell and compatibility routes | `Test-WorkbenchUiContract.ps1` proves `/`, `/workbench`, and `/companion` return UTF-8 HTML with no mojibake; six intent sections, responsive viewport, privacy, evidence, observation, Gateway topology, and the first-visit safe path are present. The no-coaching newcomer protocol is ready | Passed structurally; mobile/novice visual observation is `TODO — Derek soon` |
| Explore slice | Synchronous inspect/evidence jobs and topology projection | Passed |
| Build slice | Rebuilt Lab `build.mod.release` receipt; read-only Valheim mount, no host SDK, no plugin copy | Passed |
| Operate slice | Read-only job `job-20260802-015026195-e3676b38` passed against m32. Approved install job `job-20260802-015909355-13073d0c` and rollback job `job-20260802-015911118-89a57d29` passed with all 30 bytes exact and the original installed JSON restored. Final admitted install job `job-20260802-023656082-3e059774` left m32 active with schema-1 backup. OMEN and i5 were aligned to DLL `93877…`; peer-bearing capture job `job-20260802-025242918-32e66e98` recorded `max_peers=2`, three samples, zero bad samples, and `native_motion_only`. Legacy rollback remains fail-closed and no-peer/incomplete captures remain failed evidence. | Passed for reversible install/rollback and peer-bearing capture; native-motion lane follow-up is classified separately |
| Recover slice | Support export passed privacy scanner; recreate verifier exists | Passed for export; recreate rerun after final image tag is recommended |
| No Docker socket / profile boundary | Compose profile verifier; default/Production contain only Companion while Dev/Lab services are explicitly profile-gated | Passed |
| Normal-gameplay Dev MCP absence on this workstation | ComfyNetworkSense defaults MCP off, accepts only an explicit loopback origin, performs no disabled-state health polling, and refuses UI activation without Dev/Lab config. After the clean rebuild, `ComfyGatewayBoot` remained disabled without deletion, host `8720` remained free, and HEARTH remained on `8710` | Passed |
| Bootstrap distribution | Clean-checkpoint package: 22 required files, runner/privacy/boundary/identity gates present, operator-private i5 README excluded, and whole ZIP privacy scan clean | Passed |
| Dev MCP shared surface | With `-McpPort 8721`, live Streamable HTTP exposed 45 tools including Workbench; MCP job `job-20260801-174027902-c22a7b5f` returned the same events/receipt shape as Web; the clean authenticated identity gate passed | Passed |
| Dev MCP endpoint provenance | Current clean HEAD `1456de1142658e972f9e0462d24b3f3ba143d4ce` returned `baseline.mcp.identity.v1` with `source_dirty=false` and matched project, Lab profile, image tag, published port `8721`, Workbench provider, caller registry, and Baseline ledger; immutable Dev MCP image ID is `sha256:12549a4ad59b224572ee323c2ad7767c01680a6e94f7b7febcd2cd8c1ad4e334` | Passed |
| Active gateway launcher safety | Active launchers derive their roots/interpreters and default to explicit `:8721`; stale `ComfyGatewayBoot` was disabled without deletion and its exact retired-checkout process stopped | Passed; HEARTH unchanged on `8710` |
| Historical default-port MCP evidence | Six old Comfy-ledger calls remain quarantined; Baseline ledger now contains successful identity-gated `valheim_mcp_health`, filtered `valheim_server_log_tail`, and `valheim_handshake_trace` events on `8721` | Minimum evidence rerun passed; old receipts retained only as history |
| Clean source/image attribution | Current Workbench runtime pins clean HEAD `1456de1142658e972f9e0462d24b3f3ba143d4ce`, Companion `sha256:b8ef890ee0db59417eb495830b8c2a3a7e79db4e3b82ac6e4b24c02861305d6b`, and Dev MCP `sha256:12549a4ad59b224572ee323c2ad7767c01680a6e94f7b7febcd2cd8c1ad4e334`. The sealed rendered receipt retains its own earlier source/image identity; the live m32 install/capture receipts use this same clean runtime | Passed |
| Rendered AM4 + OMEN + i5 C6 role reversal | Job `job-20260802-003125748-116adca1`, run `workbench-20260802-003128-116adca1`: real clients completed the bounded C6 composition; Derek watched live and recorded `pass / followed / smooth`; cleanup/disarm completed | Passed; sealed reason `human_observation_recorded` |
| Full Lumberjacks solution | Restore/test succeeded with 0 errors; 605 tests passed (126 Contracts / 250 Simulation / 217 Gateway / 12 Companion), with the pre-existing EF dependency-conflict warning | Passed |

## Current safety posture

The active local stack is explicitly in Lab and publishes the identity-attested
Baseline Dev MCP only on loopback `8721`. Host `8720` is free; HEARTH remains
independent on `8710`. The clean machine-acceptance checkpoint is committed and
the C6 machine-plus-human receipt is sealed. The current clean runtime includes
the passed live install-to-rollback receipt, independently gates host processes,
disables non-reversible legacy rollback, and has a peer-bearing two-client
player-active capture. Current player bytes are exact m32 with a schema-1 rollback
record. The capture's `native_motion_only`/`canonical_session_waiting` result is
classified as a motion-lane follow-on, and unfamiliar-user/mobile review is
`TODO — Derek soon`; neither is hidden as a pass.
