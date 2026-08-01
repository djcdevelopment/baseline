# Baseline Workbench operating model

Status: working operating model, recorded 2026-08-01. It is intentionally
implementation-flexible. Product rationale is canonical in
[PD-5](decisions/pd-5-local-workbench-ownership-appliance.md); Dev MCP lifecycle is
canonical in [PD-6](decisions/pd-6-development-mcp-lifecycle.md); evidence claims
follow [PD-4](decisions/pd-4-evidence-standard.md).

This document classifies the product surfaces, users, runtime profiles, execution
targets, test lanes, actions, state, and investment choices that implement those
decisions. It is the answer to "where does this tool belong?" and "what must a new
owner understand?" It is not a commitment to a particular UI framework or final
Compose layout.

## One-line operating model

> Keep people in the intent, judgment, and ownership loop; remove them from the
> keyboard/video/mouse, file-transfer, log-courier, and timestamp-reconciliation
> loops.

The local Workbench is the human cockpit. The Baseline Dev MCP is the temporary
agent-accessible laboratory surface. The mod supplies bounded sensors and actuators
inside the real game. Scripts and workers do the transport work. All paths converge
on typed capabilities, visible jobs, and durable receipts.

## Product objective

Baseline should let a community owner:

1. download and initialize a local environment without reconstructing Derek's
   machine;
2. understand what is running, why it exists, and what it can reach;
3. explore safely before granting mutation capability;
4. run ordinary administration without development tooling;
5. build and test locally before spending multi-machine, cloud, or player attention;
6. break the disposable layer and recover predictably;
7. export a privacy-appropriate support or handoff packet;
8. replace Derek with another operator over time without replacing the community's
   existing practices.

The Workbench does not replace a community's Discord, spreadsheets, bots, rituals,
or creative judgment. It reduces the work around them and supplies infrastructure
that hobby communities rarely have: identity, telemetry, testing, compatibility,
receipts, recovery, and an extraction path.

## Logical topology

```text
Human browser ───────────────┐
                            │
AI/MCP client ─> Dev MCP ───┼─> Workbench capability API
                            │              │
Host launcher / CLI ────────┘              ├─> bounded job runner(s)
                                           ├─> local/remote adapters
                                           ├─> mod command/config/mailbox
                                           └─> receipt and state store

Mod / game / server / gateway / clients
        └─> telemetry + logs + runtime state ─> ETL + gate ─> receipt
```

The UI, MCP, and CLI may expose different subsets and interaction styles. They must
not implement competing definitions of the same Baseline capability.

### Runtime identity and endpoint provenance

Loopback reachability is transport evidence, not ownership evidence. Every
project-owned Dev MCP status and every MCP-originated receipt should expose:

| Identity field | Why it matters |
|---|---|
| Project/source root and revision/hash | proves which checkout and code served the call |
| Image identity and effective profile | proves the runtime is the intended Dev/Lab surface |
| Bound port and parent launcher/task | distinguishes Baseline from HEARTH or a legacy checkout |
| Provider set and caller registry | prevents a healthy but incomplete or unrelated gateway from passing |
| Ledger directory | ties the result to the source-resolved evidence stream |

The Workbench must fail closed when any expected identity field mismatches. A
`200 /healthz` response alone cannot make an MCP result current. On the current
OMEN workstation, the legacy `ComfyGatewayBoot` task is disabled and its retired
`:8720` listener is stopped, HEARTH is separate on `:8710`, and Baseline Dev/Lab
uses the explicit project port `:8721`. Historical default-port MCP receipts are
retained but quarantined; only identity-attested `:8721` receipts are current.

The gateway implements this contract through the authenticated read-only
`GET /identity` route, and `tools/workbench/Test-WorkbenchMcpIdentity.ps1`
turns the response into a deterministic preflight receipt. The optional
ComfyNetworkSense Raven/MCP helper is disabled by default, accepts only an
explicit loopback HTTP(S) origin, and requires Dev/Lab configuration before its
in-game toggle can enable it. Normal gameplay therefore does not probe MCP.

## Classification axes

The following axes are independent. Treating them as one toggle creates hidden
authority.

| Axis | Question | Examples |
|---|---|---|
| Presentation | How much detail is visible? | Standard, Advanced |
| Intent area | What is the person trying to do? | Explore, Build, Operate, Recover, Community |
| Runtime profile | Which services and mounts exist? | Explore, Admin, Dev, Lab, Production |
| Target | What system may the action affect? | local model, local Docker, AM4, OMEN, i5, P7 |
| Side-effect class | What can change? | read-only, local, remote, player-impacting, destructive |
| Evidence class | What may be retained or shared? | public-safe, community-private, operator-private, sensitive raw |
| Human touch | What cannot be automated honestly? | none, join once, watch, judge, external participant |

Advanced presentation does not add a runtime profile, change a mount, start MCP, or
retarget an action.

## Human information architecture

### Home

Home is the safe default and answers:

- What is running and healthy?
- Which installation, source, image, game, and mod identities are active?
- Is the game/mod pair admitted?
- Is the world ready and backed up?
- Is a job running or waiting for a person?
- What changed recently?
- What is the single recommended next action?

### Explore

Read-only discovery:

- live system map;
- topology and runtime data-flow explanations;
- health and bounded telemetry;
- compatibility reports;
- evidence and receipt browser;
- world/community views;
- roadmap and source pointers;
- optional AI explanations, labeled as drafts.

### Build

Development and artifact production:

- source/toolchain readiness;
- builds and tests;
- static assembly and RPC extraction;
- compatibility diffs;
- fixture generation;
- synthetic and replay scenarios;
- package/release-candidate creation;
- Dev MCP status and contract inventory.

Build is usually Advanced and requires a Dev or Lab runtime profile. Build output is
local until a separate promotion capability admits it.

### Operate

Stable owner/admin functions:

- service and world readiness;
- admitted update and rollback;
- configuration diff and apply;
- backup freshness and restore proof;
- player/admission posture;
- storage and retention;
- scheduled maintenance;
- release-promotion readiness.

Operate does not imply Dev MCP. Normal gameplay uses stable Workbench APIs only.

### Recover

Diagnosis and break-glass workflows:

- public-safe support capsule;
- bounded log/evidence window;
- failed-health explanation;
- image/container recreation;
- configuration recovery;
- world restore drill;
- bounded dump capture and sanitized stack summary;
- reconstruction of a prior run from receipts.

### Community

Human and governance projections:

- public status preview;
- privacy and consent posture;
- announcements and player-facing release notes;
- support expectations and escalation paths;
- ownership/handoff readiness;
- consent-safe feedback summaries;
- roadmap and contribution entry points.

## Runtime profile matrix

| Profile | Workbench | Stable admin API | Dev MCP | Game/server | Mutation posture | Intended use |
|---|---:|---:|---:|---:|---|---|
| Explore | yes | read-only | absent | optional observation | none | learn, inspect, review evidence |
| Admin | yes | yes | absent | local or admitted remote | stable, audited operations | ordinary ownership and maintenance |
| Dev | yes | optional | yes, loopback | local/rendered target | bounded development actions | mod/service development |
| Lab | yes | yes | yes, isolated | disposable server/clients or physical test pair | scenario-scoped | automated experiments |
| Production | yes | yes | absent and checked | real-player world | least privilege | normal gameplay |

An installation may enable more than one non-production profile, but each job still
declares exactly one target and side-effect class.

## Current lab target matrix

These names describe Derek's current lab. A community installation substitutes its
own configured nodes.

| Target | Role | Best questions | Default cost posture |
|---|---|---|---|
| Local static/model | contracts, algorithms, schemas, replay | Can this be answered without Unity or Steam? | spend freely |
| Local Docker | service integration, packaging, clean-start behavior | Does the composed product work predictably? | default integration loop |
| AM4 | dedicated Valheim development server | Does the real server/game lifecycle behave correctly? | bounded run after local gates |
| OMEN | primary rendered GPU client and Workbench host | Does the real client render/apply/feel correctly? | automate transport; reserve human judgment |
| i5 | second rendered GPU/Steam client | Does behavior survive machine, account, and role reversal? | offline is normal; one bounded attempt |
| Headless clients | breadth, scale, deterministic repetition | Do many clients or code paths behave without visual judgment? | qualification, not fidelity substitute |
| P7/GCP | promotion, cold boot, realistic remote edge, rollback | Is this exact release pair operationally ready? | release truth only |
| Real-player production | trust, onboarding, social behavior, support | Can people live with and operate this safely? | protect interruption and trust |

## Test-lane classification

| Lane | Proves | Does not prove | Human touch |
|---|---|---|---|
| Static extraction/unit | signature, schema, policy, parser, compatibility | Unity lifecycle or player experience | none |
| Replay/model | deterministic logic and previously captured behavior | current native runtime | none |
| Headless/synthetic | breadth, scale, repeatability, protocol behavior | GPU/display timing or subjective feel | usually none |
| Rendered single-client | real Unity, Steam, BepInEx, GPU, input/render loop | multiplayer asymmetry | launch/join when unavoidable |
| Rendered multi-box | real networking, ownership, role reversal, hardware variance | community onboarding or social load | watch and annotate |
| Human feel window | camera, smoothing, animation, combat, interaction quality | broad population support | explicit subjective judgment |
| P7 rehearsal | exact promotion, boot, backup, rollback, remote ingress | local development correctness not already gated | deliberate operator window |
| Real-player canary | installation trust, understandable failures, support | broad community scale | external participant |

Headless and rendered clients are complements. KVM elimination means remote,
receipt-driven control of real clients as well as disposable synthetic automation.

## Human-touch classification

Every run card declares one of these before it starts:

| Code | Meaning |
|---|---|
| `none` | fully unattended and machine-judged |
| `join_once` | a real account/session needs one unavoidable join action |
| `watch` | machines run the test; a person observes screens |
| `judge` | a bounded subjective classification is required |
| `external_participant` | another player/community member performs the real workflow |
| `operator_recovery` | the run intentionally exercises a recovery or break-glass step |

Human touch is a budget and an evidence field, not an embarrassment to hide.

## Capability classification record

The exact serialization is undecided, but each Workbench capability should be able to
declare:

| Field | Purpose |
|---|---|
| Stable ID and version | correlate Web, MCP, CLI, jobs, and receipts |
| Intent area | place it in the human information architecture |
| Visibility | Standard, Advanced, or both |
| Eligible profiles | prove required services/mounts exist |
| Eligible targets | prevent implicit local-to-remote escalation |
| Side-effect class | drive policy, labels, and confirmation |
| Prerequisites | fail early with actionable reason codes |
| Typed inputs | remove command-string ambiguity |
| Runner adapter | script, service, container worker, SSH, or host helper |
| Human touch | expose the operator attention budget |
| Expected duration/resources | set expectations before launch |
| Receipt schema | make completion inspectable and replayable |
| Privacy/retention | control storage and export |
| Rollback/cleanup | define recovery before mutation |
| Graduation state | experimental, candidate, stable operator, retired |

[`network/mcp/contracts/commands.json`](../network/mcp/contracts/commands.json) already
contains audience, transport, stability, requirements, side effects, examples, and
return descriptions. It is a seed, not yet the complete Workbench registry.

## Side-effect and confirmation matrix

| Class | Example | Default presentation | Required behavior |
|---|---|---|---|
| Read-only | health, compatibility, evidence view | Standard | no confirmation; source and freshness visible |
| Local artifact | build, classify, seal evidence | Standard/Advanced | target path and output receipt |
| Local runtime | start scenario, apply dev profile | Advanced | bounded duration and cleanup |
| Remote non-player | deploy to offline test client | Advanced | identity/hash verification and one bounded attempt |
| Player-impacting | restart server, promote admitted pair | Operate/Advanced | explicit target, impact, rollback, one confirmation |
| Destructive/recovery | factory reset, world restore, delete retained evidence | Recover/Advanced | exact scope, export/backup option, separate confirmation |

Force-push and source-history rewrite remain outside this model and retain their own
explicit authorization rule.

## Job and run-card contract

Every meaningful action should produce a durable job visible from any supported
interface. At minimum, a run card shows:

- title and stable capability ID;
- why the run exists;
- predeclared expectations and falsifiers;
- target and participating nodes;
- source, image, game, mod, and toolchain identity where relevant;
- side effects, player impact, and rollback;
- expected duration and resource class;
- human touch and when it will be requested;
- current phase, heartbeat, and last reason code;
- artifacts produced so far;
- final verdict, evidence boundary, and receipt link.

Suggested job states:

```text
planned -> checking -> ready -> running -> waiting_human -> sealing
        -> passed | failed | blocked | cancelled | cleanup_failed
```

`blocked` means an actionable prerequisite prevented the run. It is not a substitute
for a vague timeout. A run that performed mutations and then failed cleanup says so
separately.

## Live System Map

The Workbench should include a live UML-style deployment/topology view. Its primary
audience is a newcomer who did not build each vertical slice and needs to connect the
pieces without reading the repository first.

### Questions it answers

1. What are we trying to prove?
2. What result do we expect?
3. Which hardware and services participate?
4. Which paths carry control, gameplay, telemetry, and evidence?
5. What is every node doing now?
6. Does a person need to act?
7. Where is the result or failure explanation?

### Node states

| State | Meaning |
|---|---|
| `not_configured` | this installation has no such node |
| `offline` | configured but unreachable |
| `ready` | prerequisites and health are current |
| `working` | participating in the active job |
| `waiting_dependency` | another named node/condition is expected |
| `waiting_human` | the declared human-touch point is active |
| `degraded` | usable with an explicit limitation |
| `failed` | an actionable failure reason exists |
| `excluded` | deliberately not part of this run |
| `complete` | the node's phase completed and was receipted |

Every status includes `observed_at`, `source`, and a reason code. Color is secondary;
text and iconography carry the meaning.

### View levels

- **Story view:** generic Server, Rendered Client A/B, Gateway, Workbench, Evidence.
- **Advanced view:** physical host, process/container, protocols, hashes, counters,
  MCP and source/toolchain detail.
- **Active-run view:** dim everything outside the current run and animate or
  highlight only the declared edges.
- **Receipt replay:** later, reconstruct node transitions from a sealed run without
  contacting live hardware.

The first implementation should long-poll a typed topology endpoint every few seconds.
It does not need a new streaming bus. Existing health endpoints, SSH receipts, capture
summaries, and compact telemetry rollups are sufficient. Streaming or server-sent
events may be added only when polling proves inadequate.

Public exports substitute generic node labels and apply privacy rules. A local owner
may choose meaningful private labels for their own installation.

The existing static
[`hardware-tech-stack.svg`](../fieldlab/integration/diagrams/hardware-tech-stack.svg),
[`runtime-data-flow.svg`](../fieldlab/integration/diagrams/runtime-data-flow.svg), and
[`contracts-jobs-pipelines.svg`](../fieldlab/integration/diagrams/contracts-jobs-pipelines.svg)
remain deep technical references. The live map is a current-state and onboarding
projection, not a fourth hand-maintained architecture diagram.

## Ownership and reset matrix

| State | Default durability | Ordinary recreate | Reconfigure | Factory reset | Export expectation |
|---|---|---|---|---|---|
| Images/containers | disposable | replace | replace if needed | remove | none |
| Generated caches/build output | disposable | may replace | may replace | remove | none |
| Installation profile/config | durable, user-owned | preserve | diff then update | remove explicitly | plain, inspectable non-secret export |
| Local trust material | durable or regenerable | preserve | rotate deliberately | remove explicitly | separate protected transfer path |
| Worlds | critical durable state | preserve | preserve | never implied | backup/restore contract |
| Backups | critical durable state | preserve | preserve | separate retention decision | inventory and restore proof |
| Receipts/evidence | durable but bounded | preserve | preserve | separate retention decision | privacy-classified export |
| Dev fixtures/lab worlds | disposable by declaration | optional preserve | regenerate | remove | only when promoted to evidence |

Reset actions are distinct:

1. **Recreate Workbench:** replace disposable compute, preserve owned state.
2. **Reconfigure:** rerun setup and review a proposed diff.
3. **Reset lab:** remove declared fixtures/test worlds only.
4. **Factory-reset Workbench:** remove Workbench configuration and keys after export
   is offered.
5. **Delete world or retained evidence:** separate actions that no other reset implies.

## Development capability lifecycle

```text
idea
  -> private/local experiment
  -> Dev MCP or Lab capability
  -> deterministic contract + evidence
  -> candidate Workbench capability
  -> stable Admin/Recover capability, or remain Dev-only
  -> retire with migration/recovery note
```

The graduation criteria are defined in [PD-6](decisions/pd-6-development-mcp-lifecycle.md).
The Dev MCP is absent during normal gameplay. A feature does not graduate merely
because an operator wants to call it remotely.

## Tooling investment classification

This is a portfolio, not a rigid implementation order. A tool earns current work when
it removes repeated human transport, closes a named gate, or prevents a silent
production incompatibility.

| Investment | Primary areas | Primary loop | Community value | Burden | Timing/trigger |
|---|---|---|---|---|---|
| Workbench shell + capability registry | all | local | one understandable product surface | medium | now; integrate real capabilities, not empty framework |
| Compose profile convergence + tool runner | Home/Build/Operate | local Docker | one initialization with role-appropriate footprint | medium | after first capability slice |
| Live System Map | Home/Explore | all | makes the architecture and current run legible | low-medium | first with one rendered-pair workflow |
| Run-scoped evidence sealer | Explore/Recover | local/physical | smaller support and acceptance packets | low-medium | immediate repeated-cost relief |
| Assembly/RPC compatibility contract compiler | Build/Operate | local/startup | visible game/mod compatibility | medium | before final P7/no-fallback promotion |
| Deterministic fixture seeder | Build | local/AM4 | reproducible vehicle/mount/AI tests | medium | when C10 breadth cells start |
| Typed status + public-safe support capsule | Home/Community/Recover | local projection | self-service diagnosis and handoff | medium | before First Stranger widening |
| Bounded dump packet | Recover | physical Windows clients | decisive rare-hang evidence | low when narrow | only after a qualifying hang |
| AI classification/explanation adapter | Explore/Build | private/local | indirect; accelerates operator work | low | optional, never authoritative or required |
| Additional transpilers | Build | real runtime | situational | high fragility | only when contract diff proves no stable seam |
| Multi-community control plane | Community/Operate | hosted | potentially high later | very high | only after repeated independent-community demand |

## Engineering-loop allocation

| Question | Cheapest honest lane |
|---|---|
| Can static source/assembly evidence answer it? | local extraction, tests, replay |
| Does it require Unity, Steam, or native game lifecycle? | AM4 plus one rendered client |
| Does it require multiplayer asymmetry or visual fidelity? | automated OMEN/i5 rendered pair |
| Does it require scale but not subjective rendering? | headless/synthetic lab |
| Does it require release, cold boot, ingress, backup, or rollback truth? | bounded P7 rehearsal |
| Does it require trust, comprehension, or social behavior? | invited real-player canary |

Spend local compute freely. Spend multi-machine runs only on irreducible runtime
questions. Spend P7 mutations only on release truth. Treat operator interruption and
community trust as scarcer than cloud dollars.

## Flexible implementation sequence

1. Keep the existing Companion as the Workbench front door; do not begin with a UI
   framework rewrite.
2. Define the smallest useful capability/job/topology contracts.
3. Integrate one vertical slice across the areas:
   - Explore: compatibility/current-status report;
   - Build: extractor/contract check;
   - Operate: update readiness and rollback;
   - Recover: evidence sealer or support capsule;
   - Live map: one OMEN/AM4/i5 rendered role-reversal run.
4. Make Web and Dev MCP call the same underlying capabilities and produce the same
   receipts.
5. Converge the separate Compose stories behind role-appropriate profiles without
   granting the web container the Docker socket.
6. Add fixture, support, community, and recovery capabilities only as current gates
   or repeated operator work justify them.
7. Verify clean-machine initialization, recreate, reconfigure, export, and recovery
   with somebody who did not build the system.

## Product acceptance matrix

| Claim | Evidence path |
|---|---|
| One initialization creates an owned local environment | clean-machine run using only the shipped bootstrap and UI |
| Recreate is safe | delete/rebuild every Workbench container/image; configuration, worlds, backups, and declared receipts remain |
| Normal gameplay excludes development control | production preflight proves no Dev MCP service/listener/key/mailbox/source mount |
| The UI explains the system | unfamiliar operator can identify active goal, nodes, expected result, current phase, and recovery path from the live map |
| Agents do not hide work | MCP-started job appears in the UI with initiator, target, phase, stop path, and receipt |
| Rendered multiplayer is routine | one bounded run aligns, drives, reverses, captures, compares, and cleans up AM4/OMEN/i5 with only declared human touch |
| Support output is safe | schema and privacy tests prove no player names, IDs, positions, free text, secrets, or raw response bodies in public-safe export |
| Game updates cannot silently invalidate the mod | exact game/mod/assembly contract pair is checked at build, startup, and promotion |
| Community operation does not require Derek's AI infrastructure | clean distribution-independence test with no private paths, endpoints, keys, providers, or services |

Until a row's evidence path has run, label it candidate or unverified according to
[PD-4](decisions/pd-4-evidence-standard.md).

## Source map

- Product and private-infrastructure boundary:
  [`baseline-vision-and-boundary.md`](baseline-vision-and-boundary.md)
- Workbench boundary and reconstruction:
  [`companion-workbench-reconstruction-strategy.md`](../plans/companion-workbench-reconstruction-strategy.md)
- Turnkey Compose, keys, and demo intent:
  [`m4-2-compose-stack.md`](../plans/m4-2-compose-stack.md),
  [`m4-3-lab-mode-keys.md`](../plans/m4-3-lab-mode-keys.md), and
  [`m4-4-localhost-demo.md`](../plans/m4-4-localhost-demo.md)
- Current Companion distribution:
  [`Lumberjacks/tools/companion/README.md`](../Lumberjacks/tools/companion/README.md)
- Dev MCP contract and lifecycle today:
  [`network/mcp/README.md`](../network/mcp/README.md),
  [`network/mcp/AGENTS.md`](../network/mcp/AGENTS.md), and
  [`network/mcp/contracts/commands.json`](../network/mcp/contracts/commands.json)
- Physical-client lane:
  [`tools/i5/README.md`](../tools/i5/README.md)
- Evidence standard:
  [PD-4](decisions/pd-4-evidence-standard.md)
- Product decisions:
  [PD-5](decisions/pd-5-local-workbench-ownership-appliance.md) and
  [PD-6](decisions/pd-6-development-mcp-lifecycle.md)
- Dated synthesis and historical evidence:
  [`2026-08-01-workbench-product-review.md`](audit/2026-08-01-workbench-product-review.md)
