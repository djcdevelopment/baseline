# Full Roadmap Working Strategy

Status: active  
Horizon: cutover milestones M1-M6 and adoption milestones A1-A6  
Parallel discovery: M7 authority expansion is active under
`m7-authority-expansion-working-strategy.md`; P7 gameplay promotion remains gated
Primary source of milestone truth: `Lumberjacks/docs/roadmap/valheim-volunteer-roadmap.json`

## Operating objective

Build a trusted alpha platform that can install itself, explain itself, prove its
network behavior per participant, survive restart and rollback, support a measured
5-8-player cohort, run locally as a turnkey lab, and exchange one signed read-only
aggregate between two node-shaped instances.

This strategy controls execution order. The living roadmap controls milestone status.
The feature briefs in this directory are implementation inputs, not evidence that work
has shipped.

## Work-in-progress limits

Keep at most two lanes active:

1. **Critical path:** identity, packaging, evidence, recipient correctness, real-player
   proof, external canary, and widening.
2. **Enablement:** only the telemetry, dashboard, replay, documentation, local lab, or
   community work needed by the next critical-path gate.

M7 synthetic, replay, local-lab, and zero-behavior-change shadow work may use the
enablement lane now. It does not need to wait for M6. A behavior-changing P7
authority promotion is a separate critical-path decision and remains gated by the
M7 promotion packet.

Only one lane may change or deploy shared runtime infrastructure at a time. A useful
idea that does not block the current exit gate or materially reduce the next human
touch becomes a roadmap item instead of an immediate pivot.

## Release and test train

Every runtime change follows one train:

```text
committed source + roadmap journal
  -> host mod build / .NET 9 container verification
  -> new immutable artifact identities
  -> P7 Gateway and server deployment
  -> public package pointer
  -> OMEN and i5 install
  -> cross-machine hash and release alignment
  -> bounded automated test
  -> sealed evidence packet
```

Package release, baked mod release, Gateway image, deployment, server DLL, Companion
version, and installed-client hash remain separate fields. Changed DLL bytes never ship
under a previously published mod release identity.

No live test starts until the following exist:

- expected-result grid;
- preflight and release-alignment receipt;
- bounded command/movement script with timeout and auto-stop;
- capture locations and dashboard URL;
- rollback path;
- explicit statement of the one observation only a human can provide.

Derek's touch is reserved for Steam/OpenID consent, joining a character, subjective
visual assessment, external relationships, and decisions that cannot be derived from
evidence. File transfer, deployment, switches, movement, capture, and log collection use
Companion, SSH, or bounded control commands.

## Execution waves

### Wave 0 - Reconcile and promote the current diagnostic build

1. Read actual P7, public manifest, server, OMEN, and i5 identities and hashes. Reconcile
   the living roadmap where it trails runtime truth.
2. Cut the heartbeat-semantics work as a new mod release and matching Gateway admission
   image. Do not reuse `m20-playerindex-20260723-r1`.
3. Publish one Companion package and deploy identical DLL bytes to P7, OMEN, and i5.
4. Run non-interactive alignment and retained-telemetry probes.
5. After both owned accounts join once, automate one apply/observe course and seal the
   comparison.

Exit gate:

- all runtime hashes and identities align;
- new samples expose `server_ping_age_ms` and
  `server_ping_age_jitter_ms`;
- legacy `rtt_ms` and `jitter_ms` are compatibility aliases only;
- client-local apply, Gateway relay, and server production remain separate evidence;
- the selected client applies Lumberjacks motion while the observe-only client does not.

### Wave 1 - Authoritative admission and turnkey updates

Close M1 and M2:

- bind joining Steam identity to active enrollment, compatibility, capacity, and
  actionable admission decisions;
- implement revoke, expiry, last-used, unique-active-identity, and fail-closed behavior;
- split public, consumer, producer, telemetry, operator, and admin capabilities;
- preserve trusted proxy information and remove private-source Admin inheritance before
  an external canary;
- finish generic Companion bootstrap, local profile association, self-update, atomic
  mod update, config preservation, rollback, uninstall, and redacted diagnostics;
- derive the release table from immutable publication history.

Exit gate: a clean Windows tester reaches **READY TO JOIN** in roughly ten minutes
without editing configuration, sending a secret, or receiving operator-copied files.

### Wave 2 - Durable evidence and recipient correctness

Close M3 and M4a, then finish A2 decision provenance:

- introduce restart-safe `OPEN -> CLOSING -> SEALED` runs;
- bind events and conservation to run ID and opaque recipient;
- key durable delivery by world epoch, recipient, and stable delivery ID;
- derive recipient server-side and scope poll, lease, ACK, and closure to it;
- add exact readiness leases, reconnect/takeover rules, structured terminal outcomes,
  and a producer outbox;
- advance native peer bookkeeping only after durable Gateway acceptance;
- emit one sampled decision trace for each drop, defer, or reprioritization and reconcile
  it with aggregate counters.

Canonical evidence remains append-only, versioned, snake_case, and identity-opaque.
Derived projections never rewrite historical rows.

Exit gate: N=2 and N=10 synthetic consumers pass duplicate, isolation, reconnect, lease
takeover, Gateway restart, WAL replay, and crash-boundary tests. Every recipient closes
its own conservation equation with zero cross-poll, cross-ACK, loss, or double apply.

### Wave 3 - Two real clients and one external canary

Close M4b using the two owned clients:

- same dense build zone and separated regions;
- sustained movement and stutter-step movement;
- UDP active and forced WebSocket fallback;
- observe/apply role reversal;
- disconnect/rejoin;
- Gateway restart with backlog;
- server restart and save/reload.

Each client receives an independent sealed receipt. Strict windows require zero eligible
native ZDO sends and zero cross-recipient activity.

Then close M5 with one trusted non-developer:

- Companion-only install and preflight;
- bounded guided dense/frontier/quiet-drain route;
- personal live trace and participation receipt;
- sub-60-second survey;
- clean uninstall and operator reproduction of the sealed packet.

Participation completion is independent from the system verdict. A useful defect may
produce `PARTICIPATION COMPLETE / DEGRADED`.

Stop immediately on cross-recipient traffic, persistence loss, native leakage, release
drift, unbounded queue growth, world-integrity failure, or missing evidence.

### Wave 4 - Replay, turnkey lab, delegation, widening, and projection

Complete A3:

- replay sealed packets offline under changed tuning weights;
- maintain one tradeoff card per tuning knob;
- chapter useful VODs;
- end maintained workbook chapters with runnable proofs.

Complete A4:

- inventory every production process, secret, and container gap;
- provide a readable multi-service Compose stack;
- generate lab-only keys on first start;
- prove local Valheim event -> local Gateway -> local dashboard from a clean machine.

Complete A5 after the external canary:

- diagnostic-first support runbook;
- reviewed, smoke-tested, signed quest contribution path;
- GM-driven onboarding segments;
- private, ignored candidate map.

Close M6 in two separately sealed waves:

1. 2-4 invited players.
2. 5-8 invited-player soak.

Predeclare queue age/slope, Gateway latency, frame timing, WAL, CPU, memory, disk,
egress, and subjective quality limits. Synthetic clients qualify code paths but never
establish real-player capacity.

Complete A6:

- define and test the common node-shape contract;
- harden signing, rotation, expiry, and fail-closed verification;
- exchange one signed, read-only telemetry aggregate between two nodes;
- visibly reject or flag stale, invalid, or tampered peer data;
- make no cross-node gameplay-authority change.

Exit gate: M1-M6 and A1-A6 satisfy their living-roadmap criteria. M7 experiment
authority is defined in `m7-authority-expansion-working-strategy.md`; each
behavior-changing P7 promotion still requires its own retained packet and explicit
owner decision.

## Promotion rules

- A gate changes status only from retained evidence, never from a verbal observation.
- `PROVEN` is a sealed-run verdict, never a live dashboard label.
- Idle health is `IDLE`, not proof. Missing traffic is `INCONCLUSIVE`, not success.
- A failed gate creates one bounded repair slice and reruns only the affected gate.
- Synthetic proof precedes owned-client proof; owned-client proof precedes an external
  canary; an external canary and two-client correctness precede cohort widening.
- The accepted known-cohort security exception ends before M5.
- Public surfaces contain redacted projections only. Raw identity, credentials, private
  diagnostics, and operator capabilities remain private.

## Current active slice

The active slice remains Wave 0, but the build/deploy portion is no longer the
main risk. Current work is the final two-client proof and the tooling that keeps
that proof from depending on manual file transfer or chat reconstruction:

1. keep P7, OMEN, and i5 on the same immutable modpack identity;
2. keep the public Companion bootstrap and client-pull update lane verified;
3. run unattended pre-live gates whenever code or package surfaces change;
4. when both owned clients are joined, run the bounded apply/observe live gate;
5. annotate both visual directions and seal the evidence, or retain one named
   defect packet explaining why visual proof could not be sealed.

Do not begin M1/M2 expansion work until Wave 0 has either a sealed visual
observation packet for both directions or a named blocking defect.

## Current status addendum - 2026-07-23

Wave 0 has advanced from "build the diagnostic release" to "wait for the two real
owned clients."

Current verified state:

- P7 public manifest, Gateway deployment, OMEN Companion install, and i5 Companion
  install all report `m30-rolecontrol-20260723-r1`.
- OMEN and i5 package SHA-256 both match the P7 manifest:
  `d1bfcd6f440fe9697cf495eac16923bcc9272225039b2ace69a23d1d302cbb5a`.
- i5 tailnet SSH deploy lane is up, key-authenticated, and can see the Valheim
  BepInEx plugin directory.
- Public Companion bootstrap `companion-bootstrap-20260723-r22` is published on
  P7. Its downloaded package hash matches the public manifest, and fresh installs
  receive the Companion Wave 0 panel with the full command chain.
- OMEN and i5 Companion dashboards expose `/api/v0/companion/wave0/status`; both
  currently report `wait_for_two_real_clients` and include the final visual seal
  command.
- Non-human gates are automated:
  - synthetic Gateway motion relay gate;
  - runtime release/readiness gate;
  - live gate orchestrator;
  - immutable visual-observation annotator;
  - two-direction visual evidence seal verifier;
  - two-machine capture bundle collection;
  - return-packet generator.
- `tools\wave0\Test-Wave0Prelive.ps1` runs those gates as one unattended audit.
  The latest pre-live audit result is `ready_for_derek_two_client_join`.
- The latest live gate result is `wait_for_two_real_clients`, not a failure. P7
  is ready, but peer count is 0, so movement/capture must not start yet.

Preferred unattended pre-live command:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\wave0\Test-Wave0Prelive.ps1 -OutputDirectory captures\wave0-prelive-current
```

Next operator-minimal live command once OMEN and i5 are both joined to P7:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\wave0\Start-Wave0LiveGate.ps1 -DesiredApplyClient omen -OutputJson captures\wave0-live-gate\result.json
```

Complete return sequence once two peers are joined:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\wave0\Start-Wave0LiveGate.ps1 -DesiredApplyClient omen -OutputJson captures\wave0-live-gate\result.json
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\wave0\Add-Wave0VisualObservation.ps1 -ReceiptJson captures\wave0-live-gate\result.json -ApplyClient omen -ObserveClient i5 -VisualResult followed_role -StraightMovement smooth -StutterMovement mixed -RoleReversalRun no
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\wave0\Start-Wave0LiveGate.ps1 -DesiredApplyClient i5 -OutputJson captures\wave0-live-gate-reversal\result.json
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\wave0\Add-Wave0VisualObservation.ps1 -ReceiptJson captures\wave0-live-gate-reversal\result.json -ApplyClient i5 -ObserveClient omen -VisualResult followed_role -StraightMovement smooth -StutterMovement mixed -RoleReversalRun yes
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\wave0\Seal-Wave0VisualEvidence.ps1 -FirstAnnotatedJson captures\wave0-live-gate\result.annotated.json -ReversalAnnotatedJson captures\wave0-live-gate-reversal\result.annotated.json -OutputJson captures\wave0-live-seal\visual-seal.json
```

Only human observation still required for Wave 0:

- whether the observing screen visibly follows the applying player;
- whether straight movement is smooth, gliding, or teleporting;
- whether stutter movement behaves differently;
- whether the result follows the apply/observe role after reversal.

Do not expand into Wave 1/M1/M2 work until the live gate has either:

- a sealed visual observation packet for both directions; or
- a named defect packet explaining why visual proof cannot be sealed.

## M7 priority authorization addendum - 2026-07-24

M7 discovery is now a priority and is no longer globally deferred. The previous
status collapsed safe learning work and live gameplay promotion into one gate.
They are now separate:

- active now: capability inventory, append-only authority traces, deterministic
  synthetic generation, replay, Gateway protocol clients, lab-only Unity
  automation, disposable local strict tests, and P7 shadow comparisons;
- still gated: any P7 change that replaces native relevance, ownership,
  simulation, RPC handling, or presentation.

The execution and promotion rules live in
`plans/m7-authority-expansion-working-strategy.md`. Wave 0's visual gate remains
honest evidence debt for current player-motion presentation, but it does not block
M7 synthetic/replay/local-shadow scaffolding.

## Current status addendum - 2026-07-24

The compacted implementation pass did not invalidate the Wave 0 state. It did
surface one repository-state issue: a partially applied Companion bootstrap
verifier was present during context compaction, and the first validation run
failed because the builder treated a stale `$LASTEXITCODE` value as the verifier
result. The verifier now fails by throwing only when required package contents
are actually missing.

Current verified state:

- P7 Gateway and modpack release remain `m30-rolecontrol-20260723-r1`.
- OMEN and i5 both report installed modpack `m30-rolecontrol-20260723-r1` with
  package SHA-256
  `d1bfcd6f440fe9697cf495eac16923bcc9272225039b2ace69a23d1d302cbb5a`.
- i5 is awake and the tailnet SSH lane is up: key auth works, the Valheim
  plugin directory exists, and Docker Desktop reports a Linux engine.
- Public Companion bootstrap is `companion-bootstrap-20260723-r26`, SHA-256
  `84c6d8437c3f28d0849e545f755577474bc302c4fc9bd4b2fe9afadd5720ad17`,
  size `606424` bytes.
- The Companion bootstrap builder now validates that the package contains the
  static bootstrap files plus every `tools\wave0\*.ps1` command path emitted by
  the Companion Wave 0 command surface. This prevents a repeat of the r25-style
  mismatch where the UI exposed commands that the downloaded bundle lacked.
- The latest unattended pre-live audit result is
  `ready_for_derek_two_client_join` from
  `captures\wave0-prelive-current\summary.json` at
  `2026-07-24T03:15:36Z`.
- The Wave 0 return packet now includes
  `tools\wave0\Suggest-Wave0DefectPacket.ps1`. If live visual proof fails or
  remains inconclusive, agents should run the classifier first and use the exact
  `New-Wave0DefectPacket.ps1` command it prints, instead of manually choosing a
  defect kind from chat context.
- P7 public HTTPS is reachable and serving the r26 manifest. A local sandboxed
  PowerShell request may fail without elevated network permission; that is a
  tool-network limitation, not evidence that P7 is down.

Preferred unattended pre-live command remains:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\wave0\Test-Wave0Prelive.ps1 -OutputDirectory captures\wave0-prelive-current
```

Preferred low-touch live command once OMEN and i5 are both joined to P7:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\wave0\Wait-Wave0LiveGate.ps1 -DesiredApplyClient omen -OutputJson captures\wave0-live-gate\result.json
```

## Maintenance

Update this document only when sequencing, WIP policy, promotion rules, scope horizon,
or the human-touch contract changes. Record ordinary progress and release evidence in
the living roadmap journal instead.
