# Community Telemetry Surface Integration Plan

**Target repository:** `C:\work\baseline`  
**Source repositories:** `C:\work\comfy`, `C:\work\lumberjacks`  
**Prepared:** 2026-07-21  
**Status:** Implementation plan with source-grounded references; baseline repository verification remains required.

---

## Repository-access note

The GitHub repository `djcdevelopment/baseline` was not accessible through the connected GitHub integration during this review. The repository lookup returned `404 Not Found`, and it was not present in the connected installation's repository list.

Therefore:

- This document does **not** claim that a referenced file currently exists in `C:\work\baseline` unless a builder verifies it locally.
- Source references below point to the known authoritative files in `C:\work\comfy`.
- During implementation, every source reference must first be resolved against `C:\work\baseline`.
- Only retain a `C:\work\comfy` or `C:\work\lumberjacks` citation when the equivalent source was not carried into baseline.
- Do not duplicate code merely because it is difficult to find. Establish provenance first.

---

# 1. Goal

Evolve the existing operator-oriented dashboard and telemetry tooling into the **primary community-facing telemetry surface** for the merged Baseline runtime.

The result should be one coherent system in which:

1. A local Docker application receives and displays real-time telemetry from GCP-hosted game/runtime services.
2. Administrators and developers get a detailed operational view.
3. Players and community members get a safe, useful live view built from the same underlying telemetry contracts.
4. `ComfyNetworkSense` becomes part of the primary runtime experience instead of remaining a separate developer utility.
5. The existing quest trigger and evidence system becomes a generic gameplay-event producer.
6. Questing, networking, diagnostics, player activity, health, and local AI summaries are projections of one shared event and telemetry layer.
7. Baseline becomes the canonical home. Comfy and Lumberjacks remain provenance sources only where material has not yet been merged.

The architectural statement is:

> The Community Dashboard is the primary projection of the Baseline telemetry layer. Admin, developer, steward, creator, and community views are permissioned projections of the same runtime truth. NetworkSense and the generalized gameplay trigger pipeline are first-class event producers, not separate tools.

---

# 2. Why this belongs in Baseline

The Comfy architecture already defines a durable base layer that separates:

- absorption of community truth
- canonical contracts
- event and proof ledgers
- runtime adapters
- review and governance
- player, steward, creator, and operator projections
- metrics and feedback

Reference:

- `C:\work\comfy\docs\comfy-base-layer-architecture-plan.md`
  - Purpose and base-layer flow: lines 5-25
  - Canonical contracts: lines 108-136
  - Event and proof ledger: lines 138-163
  - Runtime adapters: lines 165-182
  - Projections: lines 208-246
  - Metrics and feedback: lines 247-268
  - Steward dashboard phase: lines 363-379
  - Enhanced-play/NetworkSense phase: lines 381-399
  - Side-channel service phase: lines 401-424
  - Lumberjacks native integration: lines 426-443

The same plan explicitly names:

- `network_session`
- `telemetry_sample`
- `player_profile`
- gameplay proof events
- network session events
- `ValheimNetworkSense`
- operator dashboards
- local web dashboards
- telemetry aggregation
- dashboard APIs

This means the requested work is not a new product direction. It is the consolidation and promotion of architecture already present in the source repository.

Baseline should now become the canonical implementation home because it is the merged runtime where Comfy’s player/community systems and Lumberjacks’ server-authoritative networking can meet.

---

# 3. Existing source-grounded capabilities

## 3.1 Telemetry and dashboard foundation

The Comfy base-layer plan already establishes these relevant contracts:

- `player_profile`
- `network_session`
- `telemetry_sample`
- `creator_metric`
- gameplay events
- network events
- steward events

Reference:

- `C:\work\comfy\docs\comfy-base-layer-architecture-plan.md`
  - Contracts: lines 108-136
  - Ledger event categories: lines 138-160

The plan also identifies projection types relevant to the requested dashboard:

- player participation
- world hotspot maps
- network session comparisons
- world density overlays
- support diagnostics
- install health
- network pressure by mode/session
- creator and guild metrics

Reference:

- `C:\work\comfy\docs\comfy-base-layer-architecture-plan.md`, lines 208-268

## 3.2 GCP, Docker, MCP, and evidence flow

The GitHub/GCP strategy states that the fieldlab already has:

- GCP as the server-side runtime target
- a native Linux Docker deployment path
- scenario-based telemetry and evidence packets
- a rendered status dashboard
- MCP tools for deploy, probe-window, telemetry-tail, and status operations
- GCS as the durable evidence store

Reference:

- `C:\work\comfy\docs\github-integration-strategy.md`
  - Existing fieldlab and packet architecture: lines 17-37
  - Runtime topology and GCP migration: lines 38-47
  - Existing MCP automation: lines 48-51
  - GitHub/GCP responsibility split: lines 58-81

This is the direct ancestor of the proposed local Docker dashboard gateway.

## 3.3 NetworkSense integration

The base-layer architecture names `ValheimNetworkSense` as a runtime adapter responsible for:

- telemetry HUD
- session export
- enhanced-play modes

Reference:

- `C:\work\comfy\docs\comfy-base-layer-architecture-plan.md`, lines 165-176

Track A also gives the Valheim adapter responsibility for:

- network telemetry
- enhanced-play suggestions
- optional side-channel service calls for dashboards
- save/world analytics

Reference:

- `C:\work\comfy\docs\comfy-base-layer-architecture-plan.md`, lines 35-53

Phase 6 calls for:

- packaged `ComfyNetworkSense`
- optional MCP/dev gateway
- host/client telemetry comparison
- session export
- enhanced-play recommendations

Reference:

- `C:\work\comfy\docs\comfy-base-layer-architecture-plan.md`, lines 381-399

## 3.4 Quest trigger and evidence pipeline

The quest vertical slice already contains a reusable event-trigger system with:

- hit events
- kill events
- projectile filters
- first-hit to killing-blow sequences
- per-quest cooldown gates
- local-player attribution
- shared manual and automatic submission plumbing

Reference:

- `C:\work\comfy\docs\quest-vertical-slice-architecture.md`
  - End-to-end quest flow: lines 18-52
  - Trigger implementation: lines 146-170
  - Submission packaging: lines 172-200
  - Reuse of existing plumbing: lines 251-255

Important implementation files named by the architecture:

- `handoffs/comfy-control-surface/Core/QuestTriggerService.cs`
- `handoffs/comfy-control-surface/Patches/QuestTriggerPatches.cs`
- `handoffs/comfy-control-surface/Core/SubmissionService.cs`
- `handoffs/comfy-control-surface/Core/GameContext.cs`
- `handoffs/comfy-control-surface/Core/TraceWriter.cs`
- `handoffs/comfy-control-surface/Core/StatusFiles.cs`

These should be searched for in Baseline before consulting or copying from Comfy.

---

# 4. Target architecture

```text
GCP runtime nodes
  ├─ game server
  ├─ gateway / interest manager
  ├─ telemetry producers
  ├─ health probes
  └─ session lifecycle events
            │
            │ secure outbound stream or authenticated pull
            ▼
Local Community Telemetry Stack
  ├─ collector / gateway
  ├─ event normalizer
  ├─ live state projector
  ├─ durable event store
  ├─ metrics rollup
  ├─ local AI summarizer
  ├─ MCP action adapter
  └─ web/API service
            │
            ├─ Admin / Developer View
            ├─ Community Live View
            ├─ Player NetworkSense Panel
            ├─ Steward / Creator View
            └─ Diagnostics and Evidence View

Runtime event producers
  ├─ NetworkSense telemetry
  ├─ server session telemetry
  ├─ movement/activity summaries
  ├─ generalized gameplay trigger pipeline
  ├─ quest evaluation
  ├─ proof/evidence capture
  └─ health/status signals
```

## 4.1 Core architectural rule

Use **one canonical event envelope** and **one telemetry sample envelope**.

Do not create separate event shapes for:

- quest triggers
- NetworkSense
- dashboard activity
- diagnostics
- progression
- evidence

Each producer may have a specialized payload, but all events must share:

- schema version
- event ID
- event type
- event time
- observed time
- source node
- source runtime
- server/session ID
- player ID or privacy-safe player reference
- correlation ID
- causation ID
- region/zone
- visibility classification
- provenance
- payload

## 4.2 Suggested canonical contracts

### `telemetry_event`

```json
{
  "schema_version": "1.0",
  "event_id": "uuid",
  "event_type": "gameplay.hit",
  "event_time_utc": "2026-07-21T12:00:00Z",
  "observed_time_utc": "2026-07-21T12:00:00.040Z",
  "source": {
    "node_id": "gcp-server-1",
    "runtime": "baseline",
    "component": "gameplay-trigger-pipeline",
    "version": "..."
  },
  "scope": {
    "server_id": "...",
    "session_id": "...",
    "player_id": "...",
    "region": "...",
    "zone": "...",
    "visibility": "admin|community|player|private"
  },
  "correlation_id": "...",
  "causation_id": "...",
  "payload": {}
}
```

### `telemetry_sample`

For sampled or aggregated values:

```json
{
  "schema_version": "1.0",
  "sample_id": "uuid",
  "metric": "network.player_server_rtt_ms",
  "sample_time_utc": "2026-07-21T12:00:00Z",
  "server_id": "...",
  "session_id": "...",
  "player_id": "...",
  "value": 48.2,
  "unit": "ms",
  "dimensions": {
    "region": "us-west1",
    "zone": "meadows",
    "mode": "group"
  },
  "visibility": "community"
}
```

## 4.3 State projections

The dashboard should not reconstruct current state directly in the browser from raw events.

Build server-side projections for:

- active server state
- connected player state
- session state
- player-to-server latency
- region/zone occupancy
- movement/activity summaries
- available telemetry streams
- component health
- alert state
- gameplay event feed
- quest/progression activity
- evidence activity
- local AI summaries

Raw events remain durable and inspectable. Projections are rebuildable.

---

# 5. Product surfaces

## 5.1 Admin / Developer View

Purpose: real-time operational truth.

Required panels:

- active GCP nodes and containers
- runtime version and deployment SHA
- active servers
- current player count
- players by server
- player-to-server latency
- packet/transport metrics already exposed by the merged gateway
- session age
- region/zone
- movement/activity rate
- event ingestion rate
- telemetry stream availability
- dropped, rejected, late, or malformed events
- service health
- storage health
- reconnect state
- last successful sample
- MCP action availability
- recent diagnostics
- local AI operational summary

Admin actions must be explicit, permissioned, and auditable.

Examples:

- request telemetry snapshot
- open a probe window
- tail a named telemetry stream
- restart an approved local collector component
- request a server diagnostic bundle
- compare host/client session telemetry
- create a redacted support bundle

Do not expose destructive infrastructure operations in the first community-dashboard increment.

## 5.2 Live Community View

Purpose: make server life visible and make every willing player an alpha tester without turning the dashboard into surveillance.

Required panels:

- active servers
- connected player count
- optional player names according to visibility policy
- approximate player/server latency bands
- session duration
- region/zone
- movement/activity summaries
- active play modes
- server health
- available telemetry streams
- current gameplay-event summaries
- current quest/event activity
- recent community milestones
- plain-language local AI summary

The default view should favor aggregation:

- count before identity
- zone before exact coordinates
- latency bands before raw samples
- activity summaries before action-level logs
- opt-in identity where appropriate

## 5.3 Player NetworkSense panel

Purpose: make networking and runtime behavior understandable from inside the primary experience.

Required data:

- current server
- current session duration
- current mode
- latency and recent trend
- client/server telemetry comparison status
- packet pressure or congestion indicator
- current region/zone
- connection health
- available diagnostics
- last recommendation
- export/share support bundle
- relevant MCP-assisted actions
- local AI explanation

NetworkSense should no longer own a parallel data model. It should publish and consume the same Baseline contracts used by the dashboard.

## 5.4 Gameplay and quest telemetry view

Purpose: promote quest-only triggers into first-class gameplay telemetry.

Initial event types:

- `gameplay.hit`
- `gameplay.first_hit`
- `gameplay.kill`
- `gameplay.killing_blow`
- `gameplay.weapon_used`
- `gameplay.projectile_fired`
- `gameplay.projectile_hit`
- `gameplay.sequence_started`
- `gameplay.sequence_completed`
- `evidence.capture_requested`
- `evidence.captured`
- `quest.trigger_matched`
- `quest.progress_updated`
- `quest.completed`

Quest logic becomes a consumer of gameplay events rather than the exclusive owner of their production.

---

# 6. Baseline-first source resolution procedure

Before implementing any component:

1. Search `C:\work\baseline` by exact file name.
2. Search by class, contract, event name, and distinctive text.
3. Inspect Git history for renamed or absorbed files.
4. Determine whether the Baseline version is:
   - identical
   - evolved
   - partially ported
   - intentionally replaced
   - missing
5. Record provenance in the implementation document.
6. Use the Baseline file as canonical when it exists.
7. Cite Comfy or Lumberjacks only when no equivalent source remains in Baseline.
8. Never copy a source implementation without first checking whether its behavior already exists under a different name.

Suggested local searches:

```powershell
Set-Location C:\work\baseline

rg -n --hidden `
  "QuestTriggerService|QuestTriggerPatches|SubmissionService|GameContext|TraceWriter|StatusFiles" .

rg -n --hidden `
  "NetworkSense|network_session|telemetry_sample|telemetry_event|player_profile|creator_metric" .

rg -n --hidden `
  "first.hit|first_hit|killing.blow|killing_blow|projectile|weapon.usage|weapon_used" .

rg -n --hidden `
  "dashboard|community view|operator view|steward dashboard|health|session duration|latency" .

rg -n --hidden `
  "InterestManager|Gateway|ZDO|movement|region|zone|connected players|active servers" .

git log --all --name-status -- `
  "*QuestTrigger*" `
  "*NetworkSense*" `
  "*telemetry*" `
  "*dashboard*" `
  "*InterestManager*"
```

Create a source ledger:

| Capability | Baseline path | Source fallback | Status | Notes |
|---|---|---|---|---|
| Quest trigger service | TBD | `comfy/.../QuestTriggerService.cs` | verify | |
| Trigger patches | TBD | `comfy/.../QuestTriggerPatches.cs` | verify | |
| Submission packaging | TBD | `comfy/.../SubmissionService.cs` | verify | |
| NetworkSense | TBD | Comfy source | verify | |
| Gateway telemetry | TBD | Lumberjacks source | verify | |
| Interest manager | TBD | Lumberjacks source | verify | |
| Dashboard renderer | TBD | Comfy fieldlab source | verify | |
| MCP telemetry tools | TBD | Comfy gateway source | verify | |

---

# 7. Implementation phases

## Alpha preemptive integration seams (2026-07-23)

The immediate alpha objective is to reduce Derek's live testing burden. Before another two-client
movement course, the release lane must provide automated evidence for the seams most likely to
produce misleading symptoms:

| Seam | Automated proof | Live test only after |
|---|---|---|
| Release alignment | Gateway image, server mod, both Companion packages, and package hashes agree | all four agree |
| Identity/admission | enrollment/access-key presence, recipient binding, region/partition, capabilities are present without exposing secrets | both clients report ready |
| Motion transport | recipient isolation, sequence wrap/duplicate rejection, malformed/unauthorized rejection, UDP/WS relay | synthetic cases pass |
| Valheim binding | direct ZDO, ZDO-object, player-index, unresolved, stale, and applied counters are visible | resolution counters are interpretable |
| Telemetry truth | client-local readiness, Gateway relay, server ZDO, and visual application remain separate | idle baseline is complete |
| Network conditions | bounded RTT/jitter observation and explicit timeout/reconnect result | baseline is captured |
| Operator control | bounded command, receipt, timeout, auto-stop, and no-op when readiness is false | control receipt is present |

The rule is: a live run may validate behavior, but it must not be the first place a contract
boundary is discovered. Failed automation stops at the named seam and produces a receipt suitable
for the next code change.

### m20 seam-diagnostics live baseline

The first live A/B after the seam work completed with two peers and zero bad capture samples. OMEN
was APPLY-enabled; i5 remained OBSERVE-only. During the bounded stutter course:

| Client | Motion transport | Apply | Applied snapshots | Direct ZDO hits | Player-index hits | Interpretation |
|---|---|---:|---:|---:|---:|---|
| OMEN / Tugcorp | UDP + WebSocket session | yes | 7,671 | 7,671 | 0 | Lumberjacks presentation is applying through the direct ZDO path |
| i5 / Durracktu | UDP + WebSocket session | no | 0 | 0 | 0 | Observe-only negative control; no visual attribution claimed |

Both clients reported two peers and advancing Gateway receive/relay counters. The player-index
fallback was exercised as an instrumented possibility but was not needed in this run. The i5
client still showed the known high-variance network condition (roughly 80--620 ms RTT with roughly
500 ms jitter in the sampled tail), so it remains a separate network-condition seam rather than
evidence against the object-resolution fix.

### Next seams, ordered by information gained per live test

1. Promote client-local motion counters and resolution-path deltas into the Companion summary; raw
   JSONL already contains them, but the operator verdict currently exposes only Gateway relay
   deltas.
2. Fix player-name extraction in capture summaries; the Gateway heartbeat has names, but the live
   summary recorded an empty `observed_players` list.
3. Add an explicit APPLY-vs-OBSERVE comparison verdict so a successful transport run cannot be
   mistaken for successful visual application.
4. Add a bounded jitter/RTT classification to the capture receipt and compare i5 against OMEN
   without requiring another movement course.
5. Only after those projections are automated, tune interpolation or exercise the player-index
   fallback deliberately with a controlled object-binding case.

## Phase 0: Baseline archaeology and contract freeze

### Goal

Establish what already exists in Baseline and prevent duplicate implementation.

### Deliverables

- capability/source ledger
- current runtime topology diagram
- current telemetry producer inventory
- current dashboard/API inventory
- current quest trigger inventory
- current NetworkSense inventory
- canonical event envelope decision
- canonical telemetry sample decision
- visibility classification decision
- explicit non-goals

### Checklist

- [ ] Search Baseline for all named Comfy implementation files.
- [ ] Search Baseline for equivalent renamed classes.
- [ ] Search Baseline for Lumberjacks Gateway and InterestManager telemetry.
- [ ] Identify all existing GCP VM telemetry endpoints.
- [ ] Identify current Docker Compose files.
- [ ] Identify current local dashboard implementation.
- [ ] Identify current MCP actions.
- [ ] Identify existing auth and caller-profile mechanisms.
- [ ] Identify telemetry retention and evidence stores.
- [ ] Produce a provenance table.
- [ ] Freeze `telemetry_event` v1.
- [ ] Freeze `telemetry_sample` v1.
- [ ] Define visibility levels.
- [ ] Define player identity handling.
- [ ] Define exact-coordinate policy.
- [ ] Define local-only and hosted-mode boundaries.

### Exit gate

A new builder can answer:

- what already exists
- where it lives
- which source repository it came from
- which contracts are canonical
- which implementation is intentionally not being copied

---

## Phase 1: Local Docker telemetry stack

### Goal

Run one local stack that can securely consume live telemetry from GCP Baseline nodes.

### Suggested services

```text
community-telemetry/
  compose.yaml
  collector/
  projector/
  api/
  web/
  storage/
  config/
  schemas/
```

A smaller initial deployment may combine collector, projector, and API in one service, but boundaries should remain clear in code.

### Deliverables

- local Docker Compose stack
- authenticated GCP connection
- telemetry ingestion endpoint or pull connector
- schema validation
- event journal
- current-state projection
- health endpoint
- reconnect/backoff behavior
- local configuration template
- redaction policy
- test event generator

### Checklist

- [ ] Inventory existing Baseline Compose definitions.
- [ ] Add rather than replace shared infrastructure.
- [ ] Choose transport: WebSocket, SSE, gRPC stream, or batched HTTPS.
- [ ] Document why the selected transport fits the existing gateway.
- [ ] Require TLS outside localhost.
- [ ] Reuse existing caller identity/auth contracts.
- [ ] Reject unknown schema versions.
- [ ] Quarantine malformed events.
- [ ] Track ingestion lag.
- [ ] Track dropped/retried events.
- [ ] Persist raw events locally.
- [ ] Build replay into projections.
- [ ] Expose `/health`, `/ready`, and `/metrics`.
- [ ] Provide synthetic telemetry mode.
- [ ] Confirm restart does not lose durable events.
- [ ] Confirm GCP disconnect does not crash the dashboard.
- [ ] Confirm reconnection resumes without duplicate state corruption.

### Exit gate

`docker compose up` produces a working local application that displays live server and session state from at least one GCP VM and continues operating through a temporary network interruption.

---

## Phase 2: Admin / Developer real-time view

### Goal

Replace fragmented telemetry-tail and status workflows with one operational surface.

### Deliverables

- server list
- player/session list
- latency view
- region/zone view
- health view
- available-stream inventory
- diagnostics feed
- deployment/runtime version view
- event-ingestion diagnostics
- MCP action panel
- local AI summary panel

### Checklist

- [ ] Show active servers.
- [ ] Show server version and commit.
- [ ] Show connected players.
- [ ] Show player-to-server RTT.
- [ ] Show session duration.
- [ ] Show region/zone.
- [ ] Show movement/activity summaries.
- [ ] Show available telemetry streams.
- [ ] Show component health.
- [ ] Show stale-data indicators.
- [ ] Show collector lag.
- [ ] Show rejected-event counts.
- [ ] Show reconnect state.
- [ ] Show diagnostics without opening raw logs.
- [ ] Link to raw evidence where available.
- [ ] Gate admin actions by existing identity/profile policy.
- [ ] Audit every action.
- [ ] Do not fail open when no role/profile fits.

### Exit gate

An operator can diagnose whether the server, gateway, telemetry transport, collector, projector, or player connection is unhealthy without manually tailing multiple systems.

---

## Phase 3: Community Live View

### Goal

Create the “everyone is an alpha tester” view using safe projections of the same operational truth.

### Deliverables

- community-safe server overview
- player count and optional identity display
- latency bands
- session duration bands
- region/zone activity
- movement/activity summaries
- health/status indicators
- active telemetry-stream indicators
- recent gameplay summaries
- clear privacy/visibility explanations
- community feedback action

### Checklist

- [ ] Default to aggregate data.
- [ ] Never expose exact coordinates by default.
- [ ] Never expose admin diagnostics in community mode.
- [ ] Make stale data visibly stale.
- [ ] Explain each metric.
- [ ] Show why each metric benefits players/community.
- [ ] Support player opt-in identity.
- [ ] Support player opt-out where required.
- [ ] Keep latency labels understandable.
- [ ] Distinguish no data from zero activity.
- [ ] Add “report what you experienced” flow.
- [ ] Correlate player feedback with session ID.
- [ ] Allow redacted support-bundle creation.
- [ ] Test with low population and solo play.
- [ ] Test with multiple servers and regions.

### Exit gate

A player can open the dashboard and understand where the community is active, whether servers are healthy, and whether their experience is unusual without seeing sensitive operational or location data.

---

## Phase 4: NetworkSense as a primary runtime producer

### Goal

Merge NetworkSense into the Baseline runtime and dashboard contracts.

### Deliverables

- NetworkSense adapter to canonical event/sample contracts
- player-facing HUD/panel
- session export through shared APIs
- host/client compare projection
- recommendation pipeline
- MCP-assisted diagnostic actions
- local AI explanations

### Checklist

- [ ] Locate the Baseline NetworkSense implementation.
- [ ] Map existing telemetry fields to canonical contracts.
- [ ] Preserve fields that do not yet have a canonical home.
- [ ] Avoid lossy normalization.
- [ ] Remove or deprecate duplicate data stores.
- [ ] Publish session lifecycle events.
- [ ] Publish latency samples.
- [ ] Publish connection-health state.
- [ ] Publish mode changes.
- [ ] Publish pressure/congestion observations.
- [ ] Consume dashboard health projections.
- [ ] Provide player-readable recommendations.
- [ ] Include evidence links behind recommendations.
- [ ] Make AI summaries optional.
- [ ] Keep raw telemetry usable without AI.
- [ ] Test host/client comparison from real sessions.
- [ ] Verify offline/local-first behavior still works.

### Exit gate

NetworkSense data appears in the primary dashboard and in-game panel without requiring a separate developer workflow or separate telemetry model.

---

## Phase 5: Generalized gameplay trigger pipeline

### Goal

Extract reusable gameplay events from the quest trigger implementation.

### Proposed split

```text
GameplayEventProducer
  ├─ observes Valheim/runtime hooks
  ├─ attributes local player and target
  ├─ emits canonical gameplay events
  └─ applies producer-level dedupe/cooldown only where required

QuestTriggerEvaluator
  ├─ consumes gameplay events
  ├─ matches quest trigger specifications
  ├─ maintains quest sequence state
  └─ requests evidence/submission

EvidenceCaptureService
  ├─ captures screenshot/context/trace
  ├─ packages evidence
  └─ emits evidence lifecycle events
```

### Deliverables

- generalized gameplay event producer
- compatibility adapter for existing quest triggers
- first hit
- killing blow
- weapon usage
- projectile events
- sequence events
- evidence events
- dashboard projection
- quest regression tests

### Checklist

- [ ] Locate `QuestTriggerService` equivalent in Baseline.
- [ ] Locate trigger patches/hooks.
- [ ] Document current trigger semantics before changing code.
- [ ] Preserve local-player-only attribution rules.
- [ ] Preserve creature-instance binding for sequences.
- [ ] Preserve cooldown behavior.
- [ ] Emit `gameplay.hit`.
- [ ] Emit `gameplay.first_hit`.
- [ ] Emit `gameplay.kill`.
- [ ] Emit `gameplay.killing_blow`.
- [ ] Emit `gameplay.weapon_used`.
- [ ] Emit projectile-fired and projectile-hit events where available.
- [ ] Emit sequence-started/completed events.
- [ ] Make quest matching a consumer.
- [ ] Keep manual and automatic evidence on the same downstream path.
- [ ] Preserve existing quest payload compatibility.
- [ ] Add event replay tests.
- [ ] Add deduplication tests.
- [ ] Add multiplayer attribution tests.
- [ ] Add visibility/redaction tests.
- [ ] Add dashboard activity summaries.

### Exit gate

Existing quests still trigger correctly, while the same underlying gameplay events can independently drive dashboard telemetry, diagnostics, progression, and future policies.

---

## Phase 6: Local AI summaries and MCP-assisted actions

### Goal

Make telemetry understandable and actionable without making AI part of the truth path.

### Rules

- AI summarizes; it does not own state.
- AI recommendations cite the metrics/events used.
- Raw data and deterministic rules remain available.
- Failed AI calls do not degrade telemetry collection.
- MCP actions remain explicit and permissioned.
- No autonomous destructive action in the first release.

### Deliverables

- deterministic summary input contract
- local model adapter
- evidence-linked summary output
- admin summary
- player summary
- session comparison summary
- MCP action suggestions
- action audit log

### Checklist

- [ ] Define summary input window.
- [ ] Define maximum context size.
- [ ] Aggregate before sending to the model.
- [ ] Redact player-private fields.
- [ ] Include source event IDs.
- [ ] Include confidence/coverage indicators.
- [ ] Distinguish observation from inference.
- [ ] Provide no-AI fallback summary.
- [ ] Do not allow AI to fabricate unavailable metrics.
- [ ] Require explicit user action before MCP calls.
- [ ] Reuse existing MCP identity and authorization.
- [ ] Audit suggested and executed actions separately.
- [ ] Test with local model unavailable.
- [ ] Test with incomplete telemetry.
- [ ] Test with contradictory client/server observations.

### Exit gate

Operators and players receive useful explanations grounded in visible telemetry, while the entire system remains functional with AI disabled.

---

## Phase 7: Hardening, privacy, and promotion

### Goal

Promote the dashboard from alpha tool to the primary community surface.

### Checklist

- [ ] Threat-model remote telemetry ingestion.
- [ ] Threat-model player identity and location exposure.
- [ ] Add retention limits.
- [ ] Add export/delete controls where required.
- [ ] Add role-based projection tests.
- [ ] Add schema migration tests.
- [ ] Add event replay tests.
- [ ] Add reconnect tests.
- [ ] Add clock-skew tests.
- [ ] Add duplicate-event tests.
- [ ] Add multi-server tests.
- [ ] Add no-player tests.
- [ ] Add high-activity tests.
- [ ] Add degraded-GCP tests.
- [ ] Add dashboard accessibility checks.
- [ ] Add mobile layout checks.
- [ ] Add operator runbook.
- [ ] Add community metric glossary.
- [ ] Add privacy/visibility documentation.
- [ ] Add release evidence packet.
- [ ] Obtain a real two-player session capture.
- [ ] Obtain a real multi-server capture if available.
- [ ] Record explicit go/no-go decision.

### Exit gate

The dashboard is reliable enough to become the default link/community surface rather than an internal operator utility.

---

# 8. Acceptance criteria

## Functional

- [ ] One local Docker command starts the complete dashboard stack.
- [ ] The stack connects to at least one GCP runtime.
- [ ] Active servers update in real time.
- [ ] Connected players update in real time.
- [ ] Player-to-server latency is visible.
- [ ] Session duration is visible.
- [ ] Region/zone is visible according to privacy policy.
- [ ] Movement/activity summaries are visible.
- [ ] Available telemetry streams are visible.
- [ ] Health/status indicators are visible.
- [ ] Existing telemetry-pipeline metrics are discoverable.
- [ ] NetworkSense data appears in the shared dashboard model.
- [ ] Quest trigger events appear as generic gameplay telemetry.
- [ ] Existing quest behavior remains compatible.
- [ ] Local AI summaries work when enabled.
- [ ] Dashboard remains functional when AI is disabled.
- [ ] MCP-assisted actions require explicit authorization.

## Reliability

- [ ] Temporary GCP disconnect recovers automatically.
- [ ] Duplicate events do not corrupt projections.
- [ ] Late events are handled deterministically.
- [ ] Unknown schema versions are quarantined.
- [ ] Dashboard restart rebuilds state from durable events.
- [ ] Stale data is clearly marked.
- [ ] Health checks distinguish collector, projector, API, and source failures.

## Privacy and governance

- [ ] Community view does not expose exact coordinates by default.
- [ ] Community view does not expose admin diagnostics.
- [ ] Player identity follows explicit policy.
- [ ] Every metric has a documented purpose.
- [ ] Every action is audited.
- [ ] No role/profile match fails closed.
- [ ] Local-first workflows remain usable.

## Evidence

- [ ] Architecture decision record exists.
- [ ] Source provenance ledger exists.
- [ ] Contract schemas and examples exist.
- [ ] Synthetic test packet exists.
- [ ] Real session packet exists.
- [ ] Host/client comparison exists.
- [ ] Screenshot or recording of admin view exists.
- [ ] Screenshot or recording of community view exists.
- [ ] Quest regression evidence exists.
- [ ] NetworkSense integration evidence exists.

---

# 9. Non-goals for the first release

- Replacing native Valheim authority.
- Moving gameplay-critical truth into the local dashboard.
- Giving the AI autonomous infrastructure control.
- Exposing exact player coordinates publicly.
- Replacing all existing evidence files with a database.
- Rewriting the quest system.
- Rewriting the Gateway or InterestManager solely to fit the dashboard.
- Creating separate admin and community telemetry pipelines.
- Making a hosted central service mandatory.
- Treating absence of telemetry as proof of absence of activity.

---

# 10. Key design decisions to make before coding

1. **Transport:** stream, poll, or hybrid.
2. **Source authority:** which server component emits authoritative player/session lifecycle.
3. **Identity:** stable player ID, display name, pseudonym, or opt-in mapping.
4. **Location:** exact position, zone, region, or activity cell by role.
5. **Storage:** JSONL first, SQLite/DuckDB, PostgreSQL, or an existing Baseline store.
6. **Time:** source clock, collector clock, skew handling, and ordering.
7. **Replay:** how projections rebuild after schema changes.
8. **Visibility:** event-level classification versus projection-level redaction.
9. **MCP authorization:** which caller profiles may invoke which actions.
10. **AI boundary:** which summaries are deterministic prerequisites and which are model-generated.
11. **Quest extraction boundary:** producer versus evaluator responsibilities.
12. **Baseline ownership:** exact destination directories and namespaces.

---

# 11. Recommended first vertical slice

Build the smallest slice that proves the entire architecture:

```text
One GCP server
  -> server heartbeat
  -> player connected
  -> latency sample
  -> zone changed
  -> gameplay first hit
  -> gameplay killing blow
  -> local collector
  -> durable event journal
  -> current-state projector
  -> admin page
  -> redacted community page
  -> NetworkSense player panel
  -> quest evaluator still completes the existing quest
```

The slice is complete only when:

- the same first-hit and killing-blow events appear in the dashboard
- the quest still completes
- the evidence pipeline still captures its package
- the player sees network/session state
- the community view sees only permitted summaries
- the operator can trace every projection back to source events

---

# 12. Builder prompt

Copy and paste the block below into a builder agent working from `C:\work\baseline`.

```text
You are working in C:\work\baseline.

Objective:
Evolve the current operator telemetry/dashboard capabilities into the primary community-facing telemetry surface. Integrate NetworkSense into the main runtime experience and generalize the existing quest trigger pipeline into first-class gameplay telemetry.

Do not begin by adding new code.

First perform baseline archaeology:
1. Search the entire Baseline repository, including Git history, for:
   - QuestTriggerService
   - QuestTriggerPatches
   - SubmissionService
   - GameContext
   - TraceWriter
   - StatusFiles
   - ComfyNetworkSense or NetworkSense
   - network_session
   - telemetry_sample
   - telemetry_event
   - player_profile
   - first hit
   - killing blow
   - weapon usage
   - projectile events
   - InterestManager
   - Gateway telemetry
   - dashboard, fieldlab, status, health, and MCP telemetry actions
2. Create a capability/source ledger identifying:
   - canonical Baseline path
   - prior Comfy or Lumberjacks path
   - whether the code is identical, evolved, partial, replaced, or missing
3. Use Baseline as canonical whenever an implementation exists there.
4. Cite C:\work\comfy or C:\work\lumberjacks only when the equivalent material no longer exists in Baseline.
5. Do not duplicate a subsystem because its old file name is missing. Search by behavior, symbols, contracts, and commit history.

Known source references to resolve:
- C:\work\comfy\docs\comfy-base-layer-architecture-plan.md
  - contracts, event ledger, runtime adapters, projections, metrics, steward dashboard, NetworkSense, side-channel service, and Lumberjacks-native phases
- C:\work\comfy\docs\quest-vertical-slice-architecture.md
  - quest trigger service, trigger patches, first-hit/killing-blow sequence, projectile filtering, shared submission/evidence pipeline
- C:\work\comfy\docs\github-integration-strategy.md
  - GCP runtime, native Docker topology, telemetry/evidence packets, dashboard renderer, MCP deploy/probe/telemetry/status actions

Target architecture:
- GCP runtime nodes emit canonical telemetry events and samples.
- A local Docker stack securely ingests those streams.
- Raw events are durable and replayable.
- Server-side projections produce current server, player, session, latency, region/zone, activity, telemetry-stream, and health state.
- Admin/developer and community views are permissioned projections of the same truth.
- NetworkSense publishes and consumes the same contracts.
- Gameplay hooks produce generic gameplay events.
- Quest evaluation consumes those events.
- Manual and automatic evidence continue through the same existing submission pipeline.
- Local AI summarizes evidence-backed telemetry but never becomes part of the truth path.
- MCP actions are explicit, permissioned, and audited.
- Authorization fails closed.

Required first vertical slice:
1. One GCP server heartbeat.
2. Player connected/session started.
3. Player-to-server latency sample.
4. Region/zone change.
5. First-hit gameplay event.
6. Killing-blow gameplay event.
7. Local Docker collector.
8. Durable event journal.
9. Rebuildable current-state projection.
10. Admin page.
11. Redacted community page.
12. NetworkSense player panel.
13. Existing quest still completes from the generalized events.
14. Existing evidence package is still produced.
15. Every displayed state can be traced to source event IDs.

Expected deliverables:
- docs/community-telemetry-surface-plan.md
- docs/community-telemetry-source-ledger.md
- ADR for event/sample contracts and visibility
- versioned telemetry_event and telemetry_sample schemas
- local Docker Compose stack
- collector with reconnect/backoff and schema validation
- durable event journal and replay
- projection service
- admin/developer web view
- community-safe web view
- NetworkSense adapter
- generalized gameplay event producer
- quest compatibility evaluator/adapter
- MCP action adapter with audit log
- optional local AI summarizer with deterministic fallback
- automated tests
- operator runbook
- community metric glossary
- evidence packet from a real session

Required dashboard fields:
- active servers
- connected players
- player-to-server latency
- session duration
- region/zone
- movement/activity summaries
- available telemetry streams
- health/status indicators
- other metrics already captured by the telemetry pipeline

Required gameplay telemetry:
- first hit
- killing blow
- weapon usage
- projectile fired/hit where available
- trigger sequence lifecycle
- evidence lifecycle
- quest trigger match/progress/completion

Privacy requirements:
- aggregate before individualizing
- no exact coordinates in community view by default
- no admin diagnostics in community view
- visibly distinguish stale, missing, and zero data
- explain why each community metric exists
- preserve local-first operation

Implementation discipline:
- Work in small, independently testable increments.
- Preserve current contracts until compatibility tests prove a migration.
- Add adapters before rewrites.
- Keep raw evidence inspectable.
- Record every architectural decision.
- Do not make AI required.
- Do not add destructive autonomous actions.
- Do not fail open on authorization.
- Do not declare completion without a real multiplayer evidence packet.

At the end of each increment:
1. list files changed
2. list contracts changed
3. list tests and results
4. show evidence produced
5. update the source ledger
6. state remaining risks and unanswered decisions
```

---

# 13. Source reference index

## Comfy

### `docs/comfy-base-layer-architecture-plan.md`

Relevant concepts:

- durable community/progression/proof/telemetry infrastructure
- Valheim as first adapter, Lumberjacks as native target
- canonical contracts
- event/proof ledger
- runtime adapters
- NetworkSense
- projections
- metrics
- local steward dashboard
- enhanced-play modpack
- telemetry side-channel service
- native Lumberjacks integration

### `docs/quest-vertical-slice-architecture.md`

Relevant concepts:

- first serious end-to-end absorption/runtime/review slice
- first hit and killing blow
- hit/kill/projectile filters
- two-shot sequences
- local-player attribution
- shared automatic/manual submission path
- evidence packaging
- replayable/inspectable local artifacts

### `docs/github-integration-strategy.md`

Relevant concepts:

- GCP server runtime
- Docker topology
- scenario runner
- telemetry/evidence packets
- dashboard renderer
- GCS evidence store
- MCP deploy, probe, telemetry-tail, and status tools
- CI/GCP orchestration boundaries

## Lumberjacks

The Comfy base-layer plan identifies Lumberjacks as the native target for:

- server-authoritative event-first progression
- ranked packet lanes
- interest management as a gameplay primitive
- authoritative quest/rank/event/reward evaluation
- operator dashboards over durable server truth

During Baseline archaeology, resolve the actual Baseline paths for:

- Gateway
- InterestManager
- player/session lifecycle
- movement updates
- region/zone ownership
- transport and latency metrics
- health/readiness endpoints
- operator APIs
- event log
- deployment/runtime metadata

Only cite a Lumberjacks source path in final documentation when its equivalent is absent from Baseline.

---

# 14. Completion definition

This initiative is complete when the Community Dashboard is no longer an operator dashboard with a public skin.

It must be the shared projection layer through which:

- operators understand runtime health
- developers diagnose networking
- players understand their session
- the community sees where life is happening
- quest events become gameplay telemetry
- NetworkSense becomes part of play
- evidence remains inspectable
- local AI explains rather than invents
- every willing participant can contribute useful alpha evidence
