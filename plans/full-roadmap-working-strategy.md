# Full Roadmap Working Strategy

Status: active  
Horizon: cutover milestones M1-M6 and adoption milestones A1-A6  
Deferred: M7 network-authority expansion  
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

Exit gate: M1-M6 and A1-A6 satisfy their living-roadmap criteria. M7 requires a new
explicit strategy and authorization.

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

The next active slice is Wave 0:

1. reconcile runtime and roadmap release truth;
2. cut a new immutable release for the committed heartbeat-semantics correction;
3. verify through the .NET 9 Docker lane and host net48 mod lane;
4. deploy through P7, Companion, and the i5 SSH lane;
5. run one automated two-client confirmation.

Do not begin M1/M2 expansion work until this slice has a sealed receipt or a named
blocking defect.

## Current status addendum - 2026-07-23

Wave 0 has advanced from "build the diagnostic release" to "wait for the two real
owned clients."

Current verified state:

- P7 public manifest, Gateway deployment, OMEN Companion install, and i5 Companion
  install all report `m29-heartbeatage-20260723-r1`.
- OMEN and i5 package SHA-256 both match the P7 manifest:
  `2b3cbb54eccc1860a3e93bc01586c17878cbc5e5ffd6e7d37f0c51cbca256475`.
- i5 tailnet SSH deploy lane is up, key-authenticated, and can see the Valheim
  BepInEx plugin directory.
- Non-human gates are automated:
  - synthetic Gateway motion relay gate;
  - runtime release/readiness gate;
  - live gate orchestrator;
  - immutable visual-observation annotator;
  - return-packet generator.
- The latest live gate result is `wait_for_two_real_clients`, not a failure.
  P7 is ready, but peer count is 0, so movement/capture must not start yet.

Next operator-minimal command once OMEN and i5 are both joined to P7:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\wave0\Start-Wave0LiveGate.ps1 -OutputJson captures\wave0-live-gate\result.json
```

Only human observation still required for Wave 0:

- whether the observing screen visibly follows the applying player;
- whether straight movement is smooth, gliding, or teleporting;
- whether stutter movement behaves differently;
- whether the result follows the apply/observe role after reversal.

Do not expand into Wave 1/M1/M2 work until the live gate has either:

- a sealed visual observation packet for both directions; or
- a named defect packet explaining why visual proof cannot be sealed.

## Maintenance

Update this document only when sequencing, WIP policy, promotion rules, scope horizon,
or the human-touch contract changes. Record ordinary progress and release evidence in
the living roadmap journal instead.
