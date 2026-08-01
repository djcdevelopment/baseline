# Workbench product, development-loop, and community-objective review — 2026-08-01

Status: dated synthesis and evidence review. This file records how the conclusions
were reached; it is not a second canonical home for them. Adopted rationale lives in
[PD-5 — local Workbench ownership appliance](../decisions/pd-5-local-workbench-ownership-appliance.md)
and [PD-6 — development MCP lifecycle](../decisions/pd-6-development-mcp-lifecycle.md).
The current classification and execution model lives in
[`workbench-operating-model.md`](../workbench-operating-model.md).

## Scope and method

This review combines:

1. Derek's product and operator clarifications during the 2026-08-01 design
   conversation;
2. current source and documentation under the only active checkout,
   `C:\work\baseline`;
3. read-only historical inspection of the retired `C:\work\comfy` and
   `C:\work\lumberjacks` roots;
4. the Git commits that preserve that history in the active repository;
5. a read-only scan of recent tools, the current Harmony/MCP surfaces, release
   packaging, evidence collection, and community boundaries.

No game, remote machine, cloud environment, repository history, or production
surface was mutated. The HEARTH skill was selected because summarization and
classification fit its intended use, but neither HEARTH nor its recovery helper was
exposed to this session. No local-model output is represented as evidence here; the
synthesis was performed directly and checked against the cited sources.

### Evidence classes used in this review

| Class | Meaning |
|---|---|
| Operator clarification | Derek stated or corrected the intended product behavior in this review |
| Current source | A behavior or mismatch is visible in the active checkout |
| Git history | A dated commit preserves how the project reached the current shape |
| Workstation-local measurement | Useful current sizing or duplication observation, but not a committed portable artifact |
| External primary source | Official documentation for Harmony, ProcDump/WinDbg, or the server image |

Claims remain bounded according to
[PD-4 — evidence paths and falsifiable guards](../decisions/pd-4-evidence-standard.md).

## Executive synthesis

The project is not primarily a collection of mods, scripts, MCP tools, containers,
or dashboards. It is becoming a **community ownership system** with a vertically
integrated game-development laboratory inside it.

The most durable product objective that emerged is:

> Give a community a safe, local, self-explaining environment that becomes theirs
> after one initialization; keep people in control of intent and judgment while the
> system performs deployment, coordination, evidence collection, and recovery work.

Four product layers serve that objective:

1. **Local Docker Workbench:** the permanent human learning, ownership, operations,
   support, and recovery surface.
2. **Baseline Dev MCP:** the profile-scoped project-specific interface through which
   coding agents can observe and drive bounded development/test capabilities.
3. **In-game mod bridge:** sensors and bounded actuators inside real Unity/Valheim
   processes, including rendered physical clients.
4. **HEARTH:** Derek's independent, cross-project AI/model/fleet infrastructure,
   expected to coexist with the Dev MCP but never required by Baseline.

The human is deliberately removed from KVM, file-transfer, log-courier, and timestamp
reconciliation work. The human remains responsible for goals, risk decisions,
subjective feel, community trust, and promotion judgment.

## Operator clarifications and their consequences

| Clarification from the conversation | Product consequence | Canonical home |
|---|---|---|
| Recent tools turned the work from a hobby hack into an engineering process | Prefer bounded commands, deterministic gates, and receipts over repeated runtime searching | [Operating model](../workbench-operating-model.md) and [PD-4](../decisions/pd-4-evidence-standard.md) |
| The Docker image's primary purpose is safety, engagement, and self-discovery—not container technology | Treat the Workbench as a resettable ownership appliance with explicit durable state | [PD-5](../decisions/pd-5-local-workbench-ownership-appliance.md) |
| One initialization should make the installation “configured to be yours” | Add an ownership/configuration record, first-run guidance, local key generation, and a visible reset contract | [PD-5](../decisions/pd-5-local-workbench-ownership-appliance.md) |
| The local web UI should be the one-stop human surface | Put orientation, jobs, status, evidence, recovery, and capability discovery in one Workbench experience | [Operating model](../workbench-operating-model.md) |
| Explore/Look, Build/Develop, Maintain/Admin, and other intents should organize the UI | Use Home, Explore, Build, Operate, Recover, and Community while leaving labels flexible | [Operating model](../workbench-operating-model.md) |
| Standard/Advanced should feel like a BIOS setting | Make presentation independent from authority, runtime profile, and target | [Operating model](../workbench-operating-model.md) |
| Both a Baseline Dev MCP and HEARTH are expected | Preserve two independent MCP systems with distinct scope and lifecycle | [PD-6](../decisions/pd-6-development-mcp-lifecycle.md) and [product boundary](../baseline-vision-and-boundary.md) |
| The project MCP and HEARTH must remain independently attributable even when several agents run at once | Treat endpoint identity as a machine-checked contract: source root, revision/hash, image, profile, port, providers, caller registry, ledger, and parent launcher/task | [MCP endpoint provenance audit](2026-08-01-mcp-endpoint-provenance-audit.md) and [PD-6](../decisions/pd-6-development-mcp-lifecycle.md) |
| Dev MCP is “for dev” and should not be active during normal gameplay | Put it behind Dev/Lab profiles and verify its absence in Production/Admin operation | [PD-6](../decisions/pd-6-development-mcp-lifecycle.md) |
| Automation's best result is not merely headless testing; it removes Derek as KVM while enabling multi-box GPU-rendered tests | Make the AM4/OMEN/i5 rendered multiplayer lane first-class, with headless as complementary qualification | [Operating model](../workbench-operating-model.md) |
| A newcomer faces “a TON of pieces” | Add a live UML-style system map showing why, expectations, hardware, current status, evidence, and human touch | [Operating model](../workbench-operating-model.md) |

## Historical reconstruction

The retired roots are stale as working trees, but their history is part of the active
repository. The following commits are durable historical sources.

| Date | Commit | What it establishes |
|---|---|---|
| 2026-03-24 | [`a8c01d1`](https://github.com/djcdevelopment/baseline/commit/a8c01d1adaa6fb8989eddaef761d72130a535705) | Lumberjacks began as a community-buildable runtime/services monorepo; later March work added deterministic movement, multi-lane transport, operator surfaces, replay, and Docker |
| 2026-07-01 | [`cc322ee`](https://github.com/djcdevelopment/baseline/commit/cc322ee4bdf91cfd619d3cbd32b05dddcd7f513e) | The Valheim control-surface workbench converted in-game actions into structured submissions, status, trace, and evidence artifacts |
| 2026-07-04 | [`1fce440`](https://github.com/djcdevelopment/baseline/commit/1fce4405a7a598c797d0c2ca1f9b45b0d744cea5) | NetworkSense's debug panel and the project MCP gateway arrived together, including contracts, auth, ledger, Valheim tools, tests, and local inference support |
| 2026-07-04 | [`e92160e`](https://github.com/djcdevelopment/baseline/commit/e92160ee2ececa4a32eec856f400bf255583ba99) | The MCP/matrix pipeline added automatic client check-in, character selection, teleport, measurement, server/client telemetry, Docker packaging, and experiment packets |
| 2026-07-09 | [`b5ec7a5`](https://github.com/djcdevelopment/baseline/commit/b5ec7a52ef14b038b76d55129bca5c5252f0d3c9) | The I1 probe proved a real hook but bypassed the automation and returned Derek to manual console and movement work; the commit recorded this as a QoL/system regression |
| 2026-07-09 | [`c64ca1d`](https://github.com/djcdevelopment/baseline/commit/c64ca1d7632b3642dfe90b8f5e4dd8815de362c8) | MCP probe tools, freshness/provenance checks, automatic movement coupling, and a one-command orchestrator rewired the loop |
| 2026-07-09 | [`3ea7468`](https://github.com/djcdevelopment/baseline/commit/3ea74681cde3cb30e5aacae50ae2ae86ddfa36b6) | The phase closed with zero human keystrokes and results arriving through MCP |
| 2026-07-10 | [`a067744`](https://github.com/djcdevelopment/baseline/commit/a0677444e69fb40e639597e20254ec4020c1f254) | Save-integrity became a structured MCP gate instead of visual/manual comparison |
| 2026-07-10 | [`2b7a397`](https://github.com/djcdevelopment/baseline/commit/2b7a397258bc05855d7583da7cc9643d98200076) | Observe-first ownership instrumentation connected live Harmony observations back through MCP |
| 2026-07-10 | [`7a1e125`](https://github.com/djcdevelopment/baseline/commit/7a1e125e822050713eec830df5cd3c2e17220faa) | The loop progressed from observation to bounded behavior change with negative controls and integrity protection |
| 2026-07-10 | [`ed18c55`](https://github.com/djcdevelopment/baseline/commit/ed18c551c2844aa1cc07ffedb075a40978b48f81) | ZDO redirection joined mod, MCP gates, and Lumberjacks ingress into one receipted vertical slice |

The historical conclusion is not merely that MCP was convenient. The project MCP was
one of the first tests of whether the project was feasible for a solo operator. It
proved that an agent could configure, actuate, observe, extract, gate, and report a
real game experiment without using Derek as the communications bus.

## The bidirectional development loop

The loop that emerged is:

```text
hypothesis
  -> target and expectations
  -> bounded config / command / mailbox
  -> mod executes on the appropriate real game thread
  -> game, server, gateway, client, and hardware behavior
  -> append-only telemetry and bounded runtime status
  -> ETL / comparison / explicit falsifier
  -> sealed receipt
  -> human or agent chooses the next question
```

The MCP is command- or event-triggered, never the per-frame gameplay transport; that
boundary is already stated in [`network/mcp/README.md`](../../network/mcp/README.md)
and [`network/mcp/AGENTS.md`](../../network/mcp/AGENTS.md).

The loop applies equally to:

- static extraction and classification;
- disposable headless clients;
- real rendered clients on multiple GPU machines;
- server/Gateway integration;
- binary/dump diagnosis;
- update, rollback, and evidence workflows.

## Why the recent tools changed the work

The files modified in the 48 hours preceding the conversation illustrate the useful
pattern:

| Tool | Repeated attention it removes | Durable behavior |
|---|---|---|
| [`tools/i5/Test-I5Link.ps1`](../../tools/i5/Test-I5Link.ps1) and [`Deploy-ToI5.ps1`](../../tools/i5/Deploy-ToI5.ps1) | guessing whether the roaming second client is available and hand-copying files | bounded BatchMode probe, per-file SHA-256 receipt, no retry loop |
| [`tools/synthetic-baseline-extractor`](../../tools/synthetic-baseline-extractor/Program.cs) | manually enumerating a 160-RPC/122-component surface | assembly-hashed static inventory used by the [C8 audit](../../fieldlab/C8-BREADTH-AUDIT-2026-07-31.md) |
| [`Install-I5ProcDump.ps1`](../../tools/i5/Install-I5ProcDump.ps1) | ad hoc diagnostic-tool installation | pinned download outcome and executable hash receipt |
| [`Test-WorkbenchZipPrivacy.ps1`](../../tools/workbench/Test-WorkbenchZipPrivacy.ps1) | manually inspecting distributable archives for private data | mandatory privacy gate with self-test |
| [`Test-Wave0RoadmapFreshness.ps1`](../../tools/wave0/Test-Wave0RoadmapFreshness.ps1) | comparing public claims to deployment identity by eye | machine-readable contradiction receipt |

The common leverage is not language, framework, or AI. Each tool:

- has one bounded purpose;
- resolves its target explicitly;
- fails at a named boundary;
- produces a receipt or actionable reason;
- removes a repeated human transport step;
- can become a Workbench capability without rewriting its core.

## Assessment of the proposed advanced techniques

| Technique | Current evidence | Product decision | Trigger for more investment |
|---|---|---|---|
| Harmony transpilers | The current policy already prefers ordinary patches, caller-up seams, semantic matching, and fail-soft behavior; the sole current transpiler replaces a matched call rather than depending on an absolute instruction offset | Last resort, not a platform initiative | A versioned compatibility diff proves no stable delegate, patch, or caller seam exists |
| Static/binary analysis | `ilspycmd`, Cecil extraction, and exact assembly hashes repeatedly ended guessing loops and exposed inlining, ownership, and RPC breadth | Promote into a compatibility contract compiler and game/mod admission gate | Before final no-fallback/P7 promotion and whenever the game assembly changes |
| Dump analysis | ProcDump/WinDbg identified the QuickEdit `WriteFile` block after logging could not; a launch-gap false positive also created a 3.7 GB dump | Keep a narrow escalation packet, never always-on capture | A qualifying hang after readiness, with one-dump limit, disk budget, hashes, TTL, and sanitized analysis |
| AI-assisted classification | The C8 machine draft accelerated breadth review but six rows required correction or reduced confidence | Optional private draft; deterministic inventory and human-reviewed repository result remain canonical | Large changed surface after an assembly diff |

Local implementation sources:

- [`harmony-patch-policy.md`](../../fieldlab/docs/harmony-patch-policy.md)
- [`ZdoSendCadenceOverride.cs`](../../network/mod/ComfyNetworkSense/Core/Services/ZdoSendCadenceOverride.cs)
- [`C8-BREADTH-AUDIT-2026-07-31.md`](../../fieldlab/C8-BREADTH-AUDIT-2026-07-31.md)
- [`SESSION-RETRO-2026-07-31.md`](../../fieldlab/retro/SESSION-RETRO-2026-07-31.md)

External primary references:

- [Harmony edge cases and inlining](https://harmony.pardeike.net/articles/patching-edgecases.html)
- [Harmony transpiler guidance](https://harmony.pardeike.net/articles/patching-transpiler.html)
- [Microsoft ProcDump](https://learn.microsoft.com/en-us/sysinternals/downloads/procdump)
- [WinDbg `!analyze`](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/-analyze)

## Important findings from the review

These were read-only findings. Recording them here does not mark them fixed.

| Finding | Source | Classification | Required disposition |
|---|---|---|---|
| Poison enforcement currently returns before evaluating poison when ledger recording is disabled, although the settings are exposed independently | [`NativeNetworkLedger.cs`](../../network/mod/ComfyNetworkSense/Core/Services/NativeNetworkLedger.cs), [`PluginConfig.cs`](../../network/mod/ComfyNetworkSense/Config/PluginConfig.cs) | correctness/safety defect | Separate enforcement from recording; test all four ledger × poison combinations; require summaries to state ledger enablement |
| The retained C8 acceptance pair is not invalidated by that defect because all retained machine summaries had ledger and poison enabled and zero native use | [`c8-native-zero-composition`](../../fieldlab/evidence/c8-native-zero-composition/README.md), [`plan-native-network-final-cutover.md`](../../fieldlab/plan-native-network-final-cutover.md) | bounded evidence clarification | Keep the claim scoped to the recorded configuration and selected surface |
| The autonomous Compose publishes the Dev MCP port on all host interfaces while the MCP documentation says localhost-only; the custom mutating helper route does not share the MCP wrapper's authentication path | [`valheim-lab.compose.yml`](../../fieldlab/autonomous/valheim-lab.compose.yml), [`gateway.py`](../../network/mcp/comfy_gateway/kernel/gateway.py), [`network/mcp/README.md`](../../network/mcp/README.md) | development-boundary/security defect | Bind host publication to loopback, authenticate every mutation, generate keys locally, and add a rendered-Compose invariant test |
| Workbench feedback distillation can default real Discord names/quotes and prompt material into paths under the public checkout | [`distill_feedback.py`](../../tools/workbench/distill_feedback.py), [`candidate-issues-README.md`](../../tools/workbench/candidate-issues-README.md), [root `.gitignore`](../../.gitignore) | community privacy defect | Default raw exports, prompts, and candidate journals outside the checkout; promote only consented/redacted summaries |
| P7 pins its container image but permits idle Steam updates, so the persisted game assemblies can drift independently of the admitted mod/image pair | [`docker-compose.yml`](../../infra/gcp/p7/docker-compose.yml), [`validate-release-bundle.ps1`](../../infra/gcp/p7/scripts/validate-release-bundle.ps1), [`ComfyNetworkSense.csproj`](../../network/mod/ComfyNetworkSense/ComfyNetworkSense.csproj) | release-compatibility risk | Admit an exact game/mod/assembly pair and make updates a drain → stage → diff → AM4 → promote workflow |
| Current evidence collection copies whole append-only files into successive run directories | [`Invoke-NativeValheimClient.ps1`](../../fieldlab/scripts/Invoke-NativeValheimClient.ps1), [`Export-MotionPerfWindow.py`](../../fieldlab/scripts/Export-MotionPerfWindow.py) | local-loop efficiency/storage defect | Seal run-scoped byte/time windows and retain full raw data only by explicit evidence policy |
| Extractor v2 collapses rows by RPC name, searches backward for a nearby string, and only iterates top-level module types | [`Program.cs`](../../tools/synthetic-baseline-extractor/Program.cs), [`RESEARCH-vehicles-mounts-ownership-2026-08-01.md`](../../fieldlab/docs/RESEARCH-vehicles-mounts-ownership-2026-08-01.md) | compatibility-inventory limitation | Emit registrant-specific stable edges, recursive types, exact overloads, invocation sites, and old/new assembly diffs |
| The current tracked Companion image and build documentation still describe net48 mod compilation as a host capability, while the clarified north star treats build tooling as a Workbench capability | [`BUILDING.md`](../../BUILDING.md), [`Game.Companion/Dockerfile`](../../Lumberjacks/src/Game.Companion/Dockerfile) | product/documentation alignment question | Inventory the actual power-user image/toolchain and make readiness visible; do not assume the tracked Companion image already contains it |
| The default MCP endpoint was not source-unique: an enabled `ComfyGatewayBoot` task launched retired `C:\work\comfy` on `:8720`; at audit time both repo `.mcp.json` files targeted that URL | [MCP endpoint provenance audit](2026-08-01-mcp-endpoint-provenance-audit.md), live task/process/ledger inspection | evidence provenance and lifecycle-boundary defect | Reserve an explicit Baseline Dev/Lab port, add machine-readable identity attestation, quarantine default-port MCP receipts, and rerun the minimum evidence set before physical acceptance |

The upstream server-image documentation confirms that `UPDATE_IF_IDLE` controls when
updates occur, not whether the game is version-pinned:
[Valheim Server Docker](https://github.com/community-valheim-tools/valheim-server-docker).

### Workstation-local evidence-volume observation

On 2026-08-01, the native run tree occupied roughly 4.8 GiB. Consecutive `full44`
and `full45` directories were each roughly 0.25 GiB; most common large files in
`full44` were exact prefixes of their `full45` counterparts. This supports the source
finding that full append-only journals are repeatedly recopied. The numbers are a
workstation-local measurement, not committed acceptance evidence, and should not be
treated as a portable benchmark.

## Outcome classification

### Adopted product policy

| Outcome | Home |
|---|---|
| The local Docker Workbench is the primary human ownership and control surface | [PD-5](../decisions/pd-5-local-workbench-ownership-appliance.md) |
| Disposable compute and explicit user-owned state form the reset/safety model | [PD-5](../decisions/pd-5-local-workbench-ownership-appliance.md) |
| Baseline Dev MCP and HEARTH both exist with independent lifecycle and scope | [PD-6](../decisions/pd-6-development-mcp-lifecycle.md) and [product boundary](../baseline-vision-and-boundary.md) |
| Dev MCP is absent during normal gameplay; stable operations graduate to Workbench APIs | [PD-6](../decisions/pd-6-development-mcp-lifecycle.md) |
| Rendered multi-box GPU testing is first-class; headless is complementary | [PD-6](../decisions/pd-6-development-mcp-lifecycle.md) |
| Human judgment stays; human transport work is removed | [Operating model](../workbench-operating-model.md) |

### Implementation candidates, not yet product truth

| Candidate | Evidence path before it becomes a claim |
|---|---|
| Standard/Advanced Workbench shell and capability registry | one real capability in each selected intent area, sharing Web/MCP receipts |
| Role/profile-based Compose convergence | clean-machine initialize and recreate without private dependencies or Docker socket |
| Live System Map | unfamiliar operator interprets one AM4/OMEN/i5 role-reversal run from the map |
| Run-scoped evidence sealer | prove bounded output completeness and ability to reproduce required summaries |
| Compatibility contract compiler | known compatible and intentionally broken assembly fixtures produce expected admission results |
| Deterministic world fixture seeder | create, use, clean up, and receipt one vehicle/mount scenario in a disposable world |
| Public-safe support capsule | privacy fixtures prove forbidden identity/free-text/raw-response classes cannot ship |

### Deferred until a trigger exists

| Deferred investment | Trigger |
|---|---|
| Additional Harmony transpilers | compatibility dossier proves no stable alternative seam |
| Broad automated dump/APM system | repeated qualifying hangs exceed the narrow packet's value |
| AI classification product | communities demonstrate a need that deterministic public tooling cannot meet |
| Multi-community hosted control plane | at least two independent communities repeat the same operational workflow |
| Browser-controlled Docker lifecycle | demonstrated UX need justifies a bounded supervisor design |

## Product and community objective

The resulting community promise is not “run Derek's stack.” It is:

- **Safety:** local-first, loopback-first, explicit targets, reversible ordinary
  actions, separate destructive actions.
- **Ownership:** configuration, trust, worlds, backups, and receipts have visible
  homes and reset semantics.
- **Self-discovery:** the live installation explains itself before requiring source
  or documentation reading.
- **Legibility:** a newcomer can see the current goal, topology, expectations,
  activity, failure reason, and evidence path.
- **Leverage:** agents and automation perform transport/repetition while humans make
  intent, risk, feel, and trust decisions.
- **Local iteration:** static/replay and local Docker answer everything they honestly
  can; physical rendered clients answer real game fidelity; P7 answers release truth;
  production answers player/community questions.
- **Community independence:** no private AI fleet, Derek-specific path, secret, or
  permanent developer control plane is required.
- **Extraction and handoff:** communities may adopt the whole appliance or take the
  useful pieces, and a future operator can reconstruct why the pieces exist.

This extends the existing canonical product statement in
[`baseline-vision-and-boundary.md`](../baseline-vision-and-boundary.md), rather than
replacing it.

## Live System Map concept captured by the review

The proposed Workbench map is a live UML-style deployment view, not a new static
diagram. A run supplies its purpose and expectations; the installation supplies its
configured topology; health adapters and receipts supply current state.

For a rendered multiplayer run, the Story view should be able to show:

```text
Why: prove behavior follows the assigned role, not machine/account identity
Expected: two peers; bounded movement; observe applies; role reversal follows role
Human touch: watch both screens and classify quality

Rendered Client A  <---- gameplay ---->  AM4 Server  <---- gameplay ---->  Rendered Client B
      apply                                  ready                              observe
         \---------------- telemetry / receipts -------------------------------/
                                      Gateway / Evidence
```

Each node reports a small state (`ready`, `working`, `waiting_human`, `failed`,
`complete`), observation time, source, and reason. Advanced view expands hardware,
processes, hashes, protocols, and counters. Nodes outside the active run are dimmed.
Long polling is sufficient for the first slice; existing static diagrams remain deep
technical sources:

- [`hardware-tech-stack.svg`](../../fieldlab/integration/diagrams/hardware-tech-stack.svg)
- [`runtime-data-flow.svg`](../../fieldlab/integration/diagrams/runtime-data-flow.svg)
- [`contracts-jobs-pipelines.svg`](../../fieldlab/integration/diagrams/contracts-jobs-pipelines.svg)

## Corrections made during the conversation

The review itself improved through several operator corrections:

1. **Docker's purpose:** initial analysis emphasized packaging and service topology.
   Derek clarified that its primary product value is safe ownership, self-discovery,
   and a replaceable environment.
2. **Two MCP systems:** early language risked sounding as if the project MCP should
   collapse into the Workbench or replace HEARTH. Derek clarified that both are
   expected; the correction is shared Baseline capability logic, not removal of the
   Dev MCP.
3. **Endpoint identity:** the first implementation treated loopback port reachability
   as sufficient MCP evidence. The live task/process/ledger audit showed that both
   retired Comfy and active Baseline configurations targeted `:8720`; the corrected
   rule is source-and-runtime attestation, not a port number.
4. **Dev lifecycle:** the project MCP's value in development does not justify its
   presence during normal gameplay. This became an explicit lifecycle decision.
5. **Rendered clients:** analysis mentioned headless automation too often. Derek
   restored the more important point: the same loop makes real, multi-box,
   GPU-rendered multiplayer testing routine without using him as KVM.
6. **Newcomer comprehension:** architecture diagrams alone are not enough. The
   Workbench needs a live, purpose-aware map that connects hardware, services,
   expectations, and activity.

These corrections are part of the result. They distinguish the product from a generic
DevOps dashboard, a generic MCP gateway, or a headless-test harness.

## Claim boundary at close

This review records adopted direction and candidate implementation. It does **not**
claim that the current Workbench already provides:

- one complete initialization for every role;
- a unified capability registry;
- Compose profile convergence;
- the live system map;
- verified safe recreate/import/export;
- production preflight proving Dev MCP absence;
- a complete game/mod compatibility gate;
- run-scoped evidence sealing;
- public-safe support capsules for strangers.

Those claims remain candidate/unverified until their evidence paths in the operating
model are exercised.

## Durable outputs of this review

- [PD-5 — The local Workbench is Baseline's ownership appliance](../decisions/pd-5-local-workbench-ownership-appliance.md)
- [PD-6 — The Baseline Dev MCP is a development/lab-only control plane](../decisions/pd-6-development-mcp-lifecycle.md)
- [MCP endpoint provenance audit](2026-08-01-mcp-endpoint-provenance-audit.md)
- [Baseline Workbench operating model](../workbench-operating-model.md)
