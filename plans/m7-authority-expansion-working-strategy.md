# M7 authority expansion working strategy

Status: discovery authorized and prioritized; live promotion gated
Authorized: 2026-07-24
Scope: relevance, replication, ownership/simulation, player motion, and remaining RPC judgments
Primary constraint: remove avoidable human iteration before asking for a real-player observation

Experiment program: `plans/m7-authority-experiment-program.md`
Execution handoff: `plans/m7-authority-experiment-execution-handoff.md`

## Outcome

Turn M7 from one large future cutover into a sequence of bounded authority claims.
Each claim must be learnable in synthetic or shadow mode, provable on a disposable
local server, and reversible before it can affect P7.

This strategy separates two kinds of authority:

- **Experiment authority is active now.** Agents may inventory, instrument, generate
  fixtures, replay traces, restore lab-only automation, run synthetic clients, run
  disposable local strict tests, and run zero-behavior-change P7 shadows.
- **P7 gameplay promotion is still gated.** Changing what the real P7 world sends,
  owns, simulates, or applies requires a retained promotion packet for that one claim
  and an explicit owner decision. It does not require M7 to be designed all at once.

M7 discovery can proceed in parallel with the remaining Wave 0 human gate. A missing
Wave 0 visual observation does not block capture, replay, synthetic tests, local-lab
automation, or shadow comparisons. It does block treating the current player-motion
presentation as proven.

## What was actually blocking M7

| Blocker | Evidence | Resolution |
|---|---|---|
| Sequencing policy treated all of M7 as one post-M6 promotion | `full-roadmap-working-strategy.md` and the current strategy-status packet label M7 `explicitly_deferred` | Split M7 into discovery and promotion. Discovery starts now; promotion remains claim-gated. |
| M7 combines several different authority planes | Roadmap M7 names relevance, ownership, replication, and remaining RPCs together | Give each plane an independent ladder, oracle, rollback, and receipt. |
| No canonical native-versus-Lumberjacks authority trace | Current probes, shadow rows, ZDO rows, and Gateway telemetry are useful but not one replay contract | Add one append-only snake_case authority envelope and a normalizer that preserves raw rows. |
| Synthetic coverage exists but is fragmented | InterestManager, SpatialGrid, simulation, fan-out, motion, and Wave 0 tests run separately | Drive them from one scenario specification and produce one run receipt. |
| The unattended Valheim swarm was deliberately removed | `SWARM-HARNESS-REMOVED.md`; local clients now stop at character selection | Restore only the useful pieces as a lab-only automation assembly and bounded control surface. |
| Human requests happen before simple integration mistakes are exhausted | Recent live passes found package, config, role, and command-surface defects after login | Add an operator-touch gate that refuses a human run until artifacts, commands, rollback, capture, and synthetic/local receipts are green. |
| Existing relevance work starts after Valheim creates a candidate list | `interest-management.md`; the redirect and co-presence fan-out still use a native candidate as the seed | Capture the native list as an oracle, then run a Lumberjacks selector over the full local object snapshot in shadow before suppressing native selection. |

## Existing runway to reuse

Do not rebuild these:

- `InterestManager`, `SpatialGrid`, subscription tracking, simulation steps, adaptive
  degradation, and send fan-out already have deterministic .NET tests.
- `ZdoBandPolicy` and `ZdoFanoutPolicy` already provide Unity-free decision seams.
  The fan-out suite proves one candidate can produce independent N=2 and N=10
  recipient decisions without cross-recipient suppression.
- `zdoCoPresenceShadowEnabled` records the fan-out that would occur without changing
  delivery; `zdoCoPresenceFanoutEnabled` is a hot-reloadable rollback boundary.
- `NetcodeProbeRunner` reaches `CreateSyncList`, `SendZDOs`, and `RPC_ZDOData`.
- I2 through I7 already proved ownership pinning, outbound interception, inbound
  injection, handshake mediation, and one-client composition.
- `LumberjacksShadowAuthorityRunner` already compares Lumberjacks motion against
  Valheim motion without applying corrections.
- Companion can queue bounded motion commands and collect local transport bundles.
- OMEN can reach i5 through the verified SSH lane; file movement is agent-owned.
- `fieldlab/autonomous/valheim-lab.compose.yml` still defines one local server,
  Gateway, and four profile-gated Steam clients.
- The removed auto-character-select and matrix runners remain recoverable at commit
  `1887626`; they are reference implementations, not code to restore blindly.

## One scenario, several execution drivers

Create one versioned scenario format under `fieldlab/scenarios/authority/`. A scenario
describes intent, not infrastructure:

```yaml
schema_version: 1
scenario_id: relevance-boundary-crossing-v1
seed: 410
plane: relevance
duration_seconds: 30
actors:
  - id: observer_a
    trajectory: straight_north
  - id: observer_b
    trajectory: stationary
objects:
  generator: concentric_density
  count: 1000
  classes: [player, structure, container, creature, decorative]
policy:
  name: tiered
  near_meters: 30
  outer_meters: 64
  mid_hz: 5
oracle: native_capture_or_fixture
stop_rules:
  - cross_recipient_activity
  - critical_omission
  - unbounded_queue_growth
```

The same scenario runs through these drivers:

| Driver | Purpose | Needs Steam/Unity | May change P7 behavior |
|---|---|---:|---:|
| `pure` | Deterministic generated entities, trajectories, policy decisions, and invariants | No | No |
| `gateway` | Protocol clients, queues, fan-out, reconnect, and transport/load behavior | No | No |
| `replay` | Re-evaluate a retained native or prior run under new equations | No | No |
| `local_valheim_shadow` | Compare against a real native server/client decision without changing it | Yes | No |
| `local_valheim_strict` | Let Lumberjacks own one declared class or policy on a disposable local world | Yes | No |
| `p7_shadow` | Observe real Era16 density and decisions while native remains authoritative | Yes | No |
| `p7_canary` | Promote exactly one proven claim with an immediate rollback flag | Yes | Yes; separate approval |

Every driver emits the same receipt shape, including scenario hash, seed, source and
artifact identities, config hash, start/end time, bounded timeout, stop-rule result,
decision counts, per-recipient invariants, CPU/queue observations, and raw evidence
locations.

## Authority evidence contract

Start with five append-only event families:

- `authority.native_candidate_observed`
- `authority.lumberjacks_decision`
- `authority.decision_compared`
- `authority.ownership_observed`
- `authority.rpc_observed`

Rows use a shared snake_case envelope. Identities are opaque. Raw native rows are
never rewritten; a normalizer creates derived comparison rows.

The relevance comparison must retain:

- run, scenario, tick, world epoch, observer, object identity, object class;
- observer/object positions and distance band;
- native candidate result and native ordering when available;
- Lumberjacks result, reason, policy version, and priority;
- latest delivered revision for that observer;
- estimated bytes and measured decision duration;
- final classification: intersection, omission, extra, duplicate, or unknown.

The first analyzer stays deliberately small:

- validate and count complete rows;
- prove deterministic replay from seed and input hash;
- calculate intersection, omission, extra, duplicate, and unknown counts by class;
- report per-recipient leakage and revision monotonicity;
- report decision duration, queue projection, and emitted-byte totals;
- compare runs by scenario, policy hash, and artifact identity.

## Correlative synthetic baselines

Synthetic data does not claim to model Valheim capacity. It proves wiring,
determinism, invariants, and expected directional relationships before Unity is
involved.

| Baseline | Generated stimulus | Required correlation/invariant |
|---|---|---|
| Determinism | Same seed and policy repeated | Byte-identical normalized decisions and summary hash |
| Radius monotonicity | Increase outer radius over the same fixture | Candidate set never shrinks |
| Density response | 1x, 2x, and 4x object density | Decisions/bytes move monotonically with density |
| Boundary crossing | Actor crosses near/mid/far boundaries | Exact enter/leave sequence; no oscillation without a recross |
| Observer isolation | N=2, N=10, N=100 observers | No observer receives or acknowledges another observer's decision |
| Duplicate/reorder | Repeat and reorder the same revisions | At most one terminal apply per recipient/revision |
| Reconnect | Drop and resume one observer | Other observers are unchanged; resumed state is monotonic |
| Motion patterns | straight, stutter, stop/start, turn, teleport | Input/output cadence and drift respond in distinguishable expected directions |
| Ownership churn | Competing candidate scores around a boundary | Shadow decisions expose churn; hysteresis candidate reduces it |
| Failure injection | timeout, malformed row, queue pressure, service restart | Bounded failure, retained receipt, no silent success |

These runs qualify a policy for a real engine comparison; they do not prove player
quality or production scale.

## Plane ladders

### R - relevance and replication selection

1. **R0 inventory:** name every current candidate and filtering seam, including
   Harmony ordering. Prove which probe sees the native list before any suppression.
2. **R1 pure oracle:** run generated object/observer fixtures through
   `ZdoBandPolicy`, `ZdoFanoutPolicy`, and a full-set Lumberjacks selector.
3. **R2 native capture:** retain native per-peer candidates plus a bounded full local
   object snapshot from a disposable local server.
4. **R3 offline compare:** replay the same snapshot through Lumberjacks and classify
   omissions/extras by object class and distance.
5. **R4 local shadow:** run native and Lumberjacks decisions concurrently; native
   controls delivery.
6. **R5 local strict:** promote one low-risk declared class on the disposable world,
   run two clients through shared and separated regions, then flip rollback during
   the same run.
7. **R6 P7 shadow:** repeat on Era16 without changing delivery.
8. **R7 P7 canary:** only after a promotion packet; one class/policy, bounded time,
   explicit rollback, retained visual and conservation evidence.

### O - ownership and simulation

1. Capture native owner changes, candidate scores, transfer reason, dwell, and churn.
2. Run a pure shadow owner selector over retained traces.
3. Compare stable-owner time, transfer count, distance, client headroom, and failure
   recovery without changing owners.
4. Reuse the proven I2 pin only on a disposable local object class.
5. Inject disconnect, slow client, restart, and competing-score cases.
6. Consider P7 shadow only after the local selector is deterministic and bounded.
7. Never promote ownership and relevance in the same canary.

### M - player motion

1. Convert the existing motion patterns and shadow drift rows into scenario-driver
   inputs and standard receipts.
2. Run pure/Gateway motion with synthetic senders and receivers at N=2, N=10, and
   N=100.
3. Run the same route through two automated local Valheim clients.
4. Compare straight, stutter, turn, stop/start, and teleport traces before changing
   interpolation.
5. Reserve a human for one side-by-side quality check only after the receipt predicts
   what should be visible.

### X - remaining RPCs

1. Inventory routed RPC names, direction, caller, payload size, reliability need,
   idempotency, persistence effect, and current owner.
2. Classify each as bootstrap/compatibility, observe-only, mirrorable, or authority
   candidate.
3. Generate codec and malformed/reorder/duplicate fixtures for one RPC family.
4. Mirror and compare before suppressing native handling.
5. Promote one idempotent, non-world-mutating family locally first.
6. World-mutating RPCs require save-before/save-after hashes and rollback proof.

## Lab automation slice

Restore unattended operation as a separate lab capability, not as production behavior
hidden in the main mod.

Current shape:

- `LabAutoJoinPatches` is a bounded opt-in seam in `ComfyNetworkSense.dll`, loaded
  only by profile-gated disposable headless/rendered Compose clients;
- it selects an existing character and calls Valheim's normal start path; it never
  creates profiles, teleports, or runs arbitrary scripts;
- `Invoke-HeadlessValheimLab.ps1` owns refresh/start/status/restart/stop and SHA-256
  stages a writable user-init watcher because the Steam-headless image normalizes
  and chowns those scripts;
- `Invoke-HeadlessValheimScenario.ps1` coordinates N=2..4 disposable clients:
  refreshes all payloads, gates all clients before any start, cleans up partial
  starts, and aggregates lifecycle receipts;
- MCP exposes `valheim_lab_motion_test` and `valheim_lab_motion_status`, which write
  only named, duration-bounded motion/apply commands to the existing mailbox;
- every movement command remains consumed on Unity's main thread and produces the
  mod's JSONL receipt; no general console or model-output execution is added.

The old `AutoCharacterSelectPatches.cs` at `1887626` was used as a reference, but
the matrix runner and profile creation path remain removed. The implementation is
deliberately narrower than the old harness.

The lab state machine is:

```text
artifact_aligned
  -> steam_ready
  -> character_selected
  -> joining
  -> in_world
  -> scenario_armed
  -> scenario_running
  -> evidence_exported
  -> stopped
```

A state timeout yields a named defect packet. It never asks Derek to repair the run
mid-flight.

## Operator-touch contract

Before asking Derek to join or look at a screen, automation must prove:

- exact mod, Gateway, server, Companion, scenario, and config identities;
- OMEN/i5/third-node reachability for the declared lane;
- required command names exist in the installed package;
- local synthetic and disposable-server gates passed on the same artifacts;
- role/authority state is unambiguous;
- capture is already running or scheduled;
- movement/script duration and auto-stop are bounded;
- rollback has been exercised on those bytes;
- expected-result grid and one human question are already written.

Human work is limited to:

- Steam/OpenID consent or the first cached account login when unavoidable;
- joining a character if the lab-only autojoin cannot legally/reliably do it;
- one visual/perceptual judgment for a promoted claim;
- approval to change P7 gameplay authority.

If a run fails before the human question becomes observable, agents collect the packet,
repair it, and rerun synthetic/local gates without another human login.

## Promotion packet

One authority claim is eligible for P7 review only when its packet contains:

- exact claim: plane, object/RPC class, policy, and bounded window;
- native oracle and Lumberjacks decision traces from the same inputs;
- synthetic N=2/N=10 results and the relevant N=100 pressure result;
- disposable local shadow and strict receipts;
- zero critical omissions, cross-recipient activity, duplicate terminal apply, and
  unbounded queue growth;
- CPU, allocation, bytes, queue age, and decision-duration comparison;
- save integrity when the claim can mutate world state;
- tested rollback time and exact rollback command;
- prediction for the one remaining human observation;
- automatic stop rules and named defect path.

Passing this packet authorizes a decision, not automatic deployment.

## Parallel execution plan

Keep at most two implementation lanes active:

| Lane | First deliverable | Then |
|---|---|---|
| A - evidence and synthetic authority lab | Scenario schema, authority JSONL contract, deterministic generator/replay runner, real Gateway E02/E03 drivers, WAL restart/ACK and bound-UDP proof, native normalizer/replay seam | Real native capture; higher-volume reconnect pressure only if native evidence requires it |
| B - unattended Unity integration | Lab-only existing-profile autojoin, lifecycle script, operator-touch preflight, MCP command mailbox, graceful stop proof, automatic native normalize/replay wrapper | Seeded client volume, two local clients, local shadow/strict role switch, automatic bundles |

Once both lanes meet, run R2-R5. Ownership and RPC work may build fixtures in parallel,
but no second strict authority plane is active during a strict relevance run.

## Immediate next steps

1. Use `m7-authority-experiment-program.md` as the pre-run question, prediction,
   result, and learning contract.
2. Reconcile strategy tooling so M7 reports `discovery_active / promotion_gated`
   instead of `explicitly_deferred`.
3. Keep the schema and receipt contract stable; E00-E04 now retain pure, Gateway,
   normalized-native, and replay evidence.
4. Seed one disposable client volume with Steam/Valheim and an existing character;
   this is the one-time environmental prerequisite for an agent-only run. The
   preflight receipt must be green before any ordinary start.
5. Capture the first native candidate trace with `-Action capture` after the client
   is stopped, then replay it offline. This is the first point at which synthetic
   equations meet actual Valheim behavior.
6. Prove `artifact_aligned -> steam_ready -> character_selected -> in_world ->
   evidence_exported -> stopped` on one local client using the lifecycle script,
   with the agent issuing only bounded MCP observations/commands between start and
   stop.
7. Seed the second local client, run the same scenario through the coordinator,
   and prove independent native/MCP receipts for both clients.
8. Run relevance shadow locally, then a bounded strict static-object-class canary with
   in-run rollback.
9. Only then prepare a P7 shadow packet. Do not request a P7 authority promotion yet.

## First decision after evidence

After steps 1-8, decide from measured results:

- If pure and native replay agree closely, invest in full-set relevance shadowing.
- If omissions cluster around object semantics, invest in classification/landmark
  contracts before more load tooling.
- If Unity automation is unreliable but protocol tests are strong, keep most work in
  pure/Gateway drivers and use the three physical clients only at promotion boundaries.
- If local strict rollback is unreliable, stop authority promotion and improve the
  harness; do not compensate with more P7 testing.
- If CPU is dominated by object enumeration, move indexing/caching earlier. If it is
  dominated by serialization/delivery, preserve native selection longer and optimize
  the downstream plane first.

This is the purpose of the scaffolding: discover which tooling earns its maintenance
cost and which equations can eventually collapse into finite v1.0 configuration.
