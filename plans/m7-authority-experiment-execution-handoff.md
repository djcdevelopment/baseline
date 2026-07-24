# M7 authority experiment execution handoff

Status: ready for a builder after the GCP reconciliation finishes
First implementation scope: M7-E00 through M7-E04 plus the disposable lab-client seam
Human-touch target: none
Parent documents:

- `plans/m7-authority-expansion-working-strategy.md`
- `plans/m7-authority-experiment-program.md`
- `plans/full-roadmap-working-strategy.md`

## Mission

Build the smallest trustworthy authority-research loop:

```text
scenario -> deterministic generation -> policy decision -> receipt
         -> comparison -> interpretation -> learning-log row
```

Then use it to run:

- E00 lab honesty/determinism;
- E01 relevance geometry and boundary shape;
- E02 recipient fan-out at N=2/N=10/N=100;
- E03 motion-pattern fingerprints;
- E04 native candidate capture/normalization.

Do not change P7, deploy to physical player installs, or ask Derek to join during
this slice. E00-E03 remove basic mistakes before native/client costs are introduced;
E04 and the lab client seam exist to remove the next human iteration cost.

## Important current state

Already written:

- experiment philosophy, card, result classes, and twelve experiment definitions:
  `plans/m7-authority-experiment-program.md`;
- execution and promotion boundaries:
  `plans/m7-authority-expansion-working-strategy.md`;
- M7 is now `discovery_active / p7_promotion_gated` in
  `plans/full-roadmap-goal-overview.csv`.

Already implemented and reusable:

- `Lumberjacks/src/Game.Simulation/World/InterestManager.cs`;
- `Lumberjacks/src/Game.Simulation/World/SpatialGrid.cs`;
- `network/mod/ComfyNetworkSense/Core/Services/ZdoIntegrationContract.cs`;
- `network/mod/ComfyNetworkSense/Core/Services/ZdoBandPolicy.cs`;
- `network/mod/ComfyNetworkSense/Core/Services/ZdoFanoutPolicy.cs`;
- `Lumberjacks/tests/Game.Gateway.Tests/ValheimCoPresenceFanoutTests.cs`;
- `Lumberjacks/tests/Game.Gateway.Tests/ValheimMotionRelayTests.cs`;
- `tools/wave0/Test-Wave0SyntheticMotion.ps1`.

Implemented in the first unattended slice:

- deterministic `AuthorityLab` CLI, scenario/event/receipt schemas, and E00-E03
  pure receipts;
- a Gateway driver that invokes `ValheimZdoRedirectService` for E02 and
  `UdpTransport.HandleValheimMotionFrameAsync` for E03;
- bounded wrappers for pure/Gateway runs, malformed input, and timeout evidence.

Implemented after the initial handoff:

- profile-gated, existing-character-only autojoin for disposable headless/rendered
  Compose clients; physical OMEN/i5 installs remain off by default;
- a verified `fieldlab/scripts/Invoke-HeadlessValheimLab.ps1` lifecycle lane for
  refresh, start, status, restart, and graceful stop;
- E04 native JSONL normalizer with raw-source preservation and malformed/ignored
  row receipts.

Still not implemented:

- higher-volume Gateway reconnect/lease pressure beyond the bounded WAL restart proof;
- native capture from a real disposable client;
- comparator that applies the current Lumberjacks policy to normalized native rows;

Current control-channel reality:

- Companion `POST /api/v0/companion/motion-test` writes
  `companion-motion.command`;
- `MotionTestController` consumes only allowlisted named motion patterns with bounded
  durations and writes receipts;
- the MCP contract currently focuses on reports, bundles, recommendations, and
  whitelisted config profiles. It is not a general arbitrary-script bridge.

Preserve this shape. Later Unity automation should extend an allowlisted command
mailbox, not add arbitrary code execution inside Valheim.

## Concurrent GCP work and Git safety

Another agent is finishing GCP/world-save reconciliation. Before changing code:

```powershell
git status --short --branch
git log -5 --oneline --decorate
```

Rules:

- preserve all existing modifications and untracked files;
- do not revert, reset, stash, or overwrite the GCP agent's work;
- wait for the operator to say the GCP work is committed before attempting a shared
  commit;
- re-read `git status` and `git log` after that agent finishes because roadmap
  automation may rewrite/push `main`;
- never force-push to undo roadmap automation.

At handoff creation, unrelated changes included roadmap journal files and
`infra/gcp/p7/RECONCILE-GAP.md`. Treat their future state as owned by the other agent.

## Proposed repository layout

Create these during implementation:

```text
tools/authority-lab/
  AuthorityLab.sln
  src/AuthorityLab/
    AuthorityLab.csproj
    Program.cs
    Commands/
    Generation/
    Normalization/
    Policies/
    Receipts/
  tests/AuthorityLab.Tests/
    AuthorityLab.Tests.csproj
  Invoke-AuthorityExperiment.ps1
  README.md

fieldlab/experiments/m7/
  README.md
  schemas/
    authority-event.schema.json
    authority-scenario.schema.json
    authority-receipt.schema.json
  learning-log.jsonl
  m7-e00-lab-truth/
    experiment.md
    scenario.yaml
    runs/
  m7-e01-relevance-shape/
    experiment.md
    scenario.yaml
    runs/
  m7-e02-recipient-fanout/
    experiment.md
    scenario.yaml
    runs/
  m7-e03-motion-fingerprints/
    experiment.md
    scenario.yaml
    runs/
```

Do not add a database, queue service, web UI, manifest server, or generic workflow
engine for E00-E03.

## AuthorityLab implementation shape

Target `net9.0`. Build it in `mcr.microsoft.com/dotnet/sdk:9.0`.

Reuse existing policy source rather than transcribing equations. The first practical
adapter can link the pure source files into `AuthorityLab.csproj`:

```xml
<Compile Include="../../../network/mod/ComfyNetworkSense/Core/Services/ZdoIntegrationContract.cs"
         Link="Policies/ZdoIntegrationContract.cs" />
<Compile Include="../../../network/mod/ComfyNetworkSense/Core/Services/ZdoBandPolicy.cs"
         Link="Policies/ZdoBandPolicy.cs" />
<Compile Include="../../../network/mod/ComfyNetworkSense/Core/Services/ZdoFanoutPolicy.cs"
         Link="Policies/ZdoFanoutPolicy.cs" />
```

If a linked file pulls Unity types, stop and extract only the already-pure policy seam
into a shared source project. Do not fork/copy an equation into a second implementation.

The initial CLI surface:

```text
authority-lab generate --scenario <yaml> --output <run-dir>
authority-lab run      --scenario <yaml> --driver pure --output <run-dir>
authority-lab compare  --left <receipt-or-jsonl> --right <receipt-or-jsonl> --output <dir>
authority-lab check    --run <run-dir>
```

`gateway` may be added as a driver during E02. It should invoke the real Gateway
protocol/service seam or a running local Gateway. It must not silently substitute
pure in-memory fan-out while labeling the receipt `gateway`.

## Minimal schemas

### Scenario

Required fields:

- `schema_version`;
- `experiment_id`;
- `scenario_id`;
- `seed`;
- `plane`;
- bounded `duration_seconds`;
- actors and trajectories;
- object generator/count/classes where relevant;
- policy name and values;
- driver;
- stop rules.

Reject unknown driver names and unbounded/non-positive duration. Preserve extra
experiment-specific payload under a single `parameters` object instead of repeatedly
changing the root schema.

### Event

Use the event families from the parent strategy:

- `authority.native_candidate_observed`;
- `authority.lumberjacks_decision`;
- `authority.decision_compared`;
- `authority.ownership_observed`;
- `authority.rpc_observed`.

E00-E03 mainly emit `authority.lumberjacks_decision`. Motion-specific observations may
use an event-specific `payload`; do not invent a parallel envelope.

Required envelope:

```json
{
  "schema_version": 1,
  "event_id": "opaque-run-local-id",
  "timestamp_utc": "2026-07-24T00:00:00Z",
  "event_type": "authority.lumberjacks_decision",
  "experiment_id": "m7-e01-relevance-shape",
  "scenario_id": "relevance-shape-v1",
  "run_id": "pure-20260724-001",
  "seed": 410,
  "tick": 1,
  "driver": "pure",
  "payload": {}
}
```

All serialized names are snake_case.

### Receipt

Required:

- experiment/scenario/run IDs;
- source revision and dirty-state flag;
- scenario SHA-256;
- normalized-input SHA-256;
- policy name/version/config;
- driver;
- seed;
- start/end/duration;
- bounded stop result;
- event counts;
- invariant results;
- prediction observations;
- raw evidence paths;
- normalized decision SHA-256;
- result classification left `pending` until interpretation.

Normalization excludes timestamps, run IDs, absolute paths, and machine names. E00
must prove that the remaining normalized bytes are stable.

## Unit-test ceiling

Create a small test project, but keep the first slice near 6-10 focused tests:

- malformed required scenario field rejects;
- unknown driver rejects;
- same seed generates the same normalized input;
- normalized receipt ignores run metadata;
- fan-out never emits one recipient twice for one revision;
- one recipient's delivered revision does not suppress another;
- timeout/stop produces a retained non-success receipt;
- snake_case serialization smoke.

Do not reproduce the existing large `InterestManager`, `ZdoFanoutPolicy`, or Gateway
test matrices in AuthorityLab.

## Canonical build commands

From `C:\work\baseline`:

```powershell
$repoRoot = (Resolve-Path .).Path

docker run --rm `
  -v "${repoRoot}:/repo" `
  -w /repo/tools/authority-lab `
  mcr.microsoft.com/dotnet/sdk:9.0 `
  dotnet build AuthorityLab.sln

docker run --rm `
  -v "${repoRoot}:/repo" `
  -w /repo/tools/authority-lab `
  mcr.microsoft.com/dotnet/sdk:9.0 `
  dotnet test AuthorityLab.sln --no-build
```

Prefer a repository wrapper (`Invoke-AuthorityExperiment.ps1`) for normal runs so the
command, image, source revision, and output layout are captured consistently.

Existing smoke seams:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File tools\wave0\Test-Wave0SyntheticMotion.ps1 `
  -OutputJson captures\m7-e03-existing-motion-smoke.json

$lumberjacksRoot = (Resolve-Path .\Lumberjacks).Path
docker run --rm `
  -v "${lumberjacksRoot}:/src" `
  -w /src `
  mcr.microsoft.com/dotnet/sdk:9.0 `
  dotnet test tests/Game.Gateway.Tests/Game.Gateway.Tests.csproj `
  --filter "FullyQualifiedName~ValheimCoPresenceFanoutTests"
```

Run the focused seams while iterating. Run the full Lumberjacks verification once at
the end of the slice if shared Lumberjacks source changed:

```powershell
Set-Location .\Lumberjacks
.\scripts\build.ps1 -Target Verify
Set-Location ..
```

If only linked pure source was consumed and Lumberjacks source did not change, the
focused existing tests plus AuthorityLab tests are sufficient for this R&D slice.

## E00 execution

Files:

- `fieldlab/experiments/m7/m7-e00-lab-truth/experiment.md`;
- `scenario.yaml`;
- two valid run directories;
- one malformed-input run;
- one forced-timeout run.

Procedure:

1. Freeze the experiment card predictions.
2. Run the same scenario twice with the same seed.
3. `check` both runs.
4. Compare normalized input and decision hashes.
5. Run malformed input and forced timeout.
6. Confirm both produce named receipts and no process remains running.
7. Classify the result and append one learning-log row.

Exit:

- identical valid normalized hashes;
- malformed input rejected before execution;
- timeout bounded and retained;
- no absolute path, machine name, credential, or Steam identity in public artifacts.

Stop:

- nondeterministic normalized decisions;
- missing partial receipt on timeout;
- a process survives the declared end.

## E01 execution

Use a concentric deterministic fixture with:

- radii around 29.9, 30.0, 30.1, 63.9, 64.0, and 64.1;
- densities 1x, 2x, and 4x;
- five fixed seeds;
- clean crossing and boundary-noise trajectories;
- current policy values: near 30m, outer 64m, mid 5Hz.

Capture:

- considered/emitted/held/dropped counts;
- candidate-set hash;
- enter/leave transitions;
- band transitions and chatter count;
- estimated emitted bytes;
- decision duration as advisory lab data.

Do not turn p95 timing into a capacity gate. The useful result is direction and
predictability.

Exit:

- monotonic radius/density response;
- exact clean crossing sequence;
- an honest measured answer about undamped boundary chatter.

## E02 execution

Use the same logical object revisions against N=2, N=10, and N=100 observers:

- all in-band;
- mixed near/mid/far;
- one duplicate recipient;
- one already-delivered recipient;
- one slow/reconnecting observer;
- duplicate/reordered revisions.

Run the pure policy first, then the real Gateway driver.

Capture:

- decisions and emissions by observer;
- poll/lease/ACK subject;
- pending age per observer;
- duplicate terminal outcome;
- cross-recipient activity;
- decisions/bytes versus in-band observer count.

Exit:

- zero cross-recipient activity;
- zero duplicate terminal apply;
- slow/reconnect effects remain recipient-local;
- scaling shape is reported, not promoted as a 100-player capacity claim.

The current Gateway drivers cover the in-memory E02 seam, the WAL-backed restart/ACK
seam, the WebSocket fallback path, and a bound UDP loopback path. Higher-volume
reconnect pressure remains separate. If a future real Gateway driver is not ready,
classify that run `harness_failed`; do not label the pure result as Gateway evidence.

## E03 execution

Generate:

- `straight_north`;
- `stutter_north`;
- `stop_start`;
- `turn_90`;
- `circle`;
- `teleport`.

Use fixed duration and sample cadence. Run pure fingerprints, then the existing
Gateway motion smoke. The first Gateway run exercises binary WebSocket fallback and
the UDP follow-up binds both endpoints and exercises `UdpTransport.TrySend`. Replay
comparison and native capture are next. Do not contact P7.

Capture:

- input interval distribution;
- output interval distribution;
- sequence lag/reorder;
- direction error;
- correction magnitude/frequency;
- predicted-position error;
- transport path.

Exit:

- each pattern has a distinguishable, repeatable fingerprint;
- UDP and fallback preserve logical ordering in the tested seam;
- the E03 summary says which future live observation would separate cadence from
  interpolation, without claiming either is already the cause.

## Learning log and synthesis

After each experiment, append exactly one initial interpretation row. Later
reinterpretation is a new row referencing the old one; do not edit history.

After E00-E03 create:

```text
fieldlab/experiments/m7/synthesis-001.md
```

It answers:

- Is the lab deterministic enough to trust?
- Which correlations are established?
- Which assumptions broke?
- Is E04 native capture ready?
- What minimum Unity automation is now justified?
- What should not be built?

E04 does not start until the synthesis names the exact native fields required by the
comparator.

## Strategy-status reconciliation

The current generated Wave 0 strategy packet predates M7 authorization and its
generator still hard-codes `explicitly_deferred`.

Update:

- `tools/wave0/New-FullRoadmapStrategyStatus.ps1`;
- `tools/wave0/Test-FullRoadmapStrategyStatusFixtures.ps1`;
- generated strategy packet only when intentionally refreshing the pre-live packet.

Desired M7 state:

```text
discovery_active_p7_promotion_gated
```

Evidence should point to the two M7 plan documents. Needed action should say to run
E00-E03 before native capture. It must not imply that P7 authority promotion is
authorized.

Focused validation:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File tools\wave0\Test-FullRoadmapStrategyStatusFixtures.ps1
```

Do this before or alongside E00, but do not trigger a live P7 preflight while the
other agent is still changing GCP.

## Roadmap journal and commit

Implementation under `fieldlab/` triggers the living-roadmap rule. The public note
must contain no account identifiers, credentials, private URLs, or machine secrets.

After all intended files are staged, inspect whether background automation already
journaled and pushed the change:

```powershell
git status --short --branch
git log -5 --oneline --decorate
```

If it has not, from `Lumberjacks/`:

```powershell
node scripts/roadmap.mjs note `
  --milestone M7 `
  --kind implementation `
  --summary "Start the M7 authority experiment lab" `
  --impact "Adds deterministic synthetic relevance, recipient, and motion experiments before any live authority promotion."

node scripts/roadmap.mjs check --staged
```

Do not add a duplicate note if automation already created one. Do not amend-loop a
roadmap note with its future commit SHA.

## Definition of done for the first slice

- M7 status tooling reports discovery active and P7 promotion gated.
- AuthorityLab builds and runs in the .NET 9 container.
- E00-E03 each have frozen predictions, retained receipts, result classification,
  and one learning-log row.
- Gateway E02 and E03 have separate `driver=gateway` receipts that invoke real
  Gateway services and preserve explicit transport-path evidence.
- Gateway E02 durable and E03 UDP runs have separate receipts proving WAL restart/ACK
  recovery and bound-UDP target delivery.
- E00 proves deterministic normalized output and bounded failure.
- E01 reports geometry/density/boundary correlations.
- E02 reports N=2/N=10/N=100 recipient isolation and scaling shape.
- E03 reports repeatable motion fingerprints.
- `synthesis-001.md` says what E04 must capture and what tooling is justified.
- No P7 mutation, mod deployment, Steam login request, or manual file transfer occurred.
- Git/roadmap state is reconciled after the GCP agent's work, without overwriting it.

## First action after compaction

Read, in order:

1. `AGENTS.md`;
2. `plans/m7-authority-experiment-execution-handoff.md`;
3. `plans/m7-authority-experiment-program.md`;
4. `plans/m7-authority-expansion-working-strategy.md`;
5. current `git status --short --branch` and `git log -5`.

Then start with strategy-status reconciliation and M7-E00. Do not begin by launching
Valheim.
