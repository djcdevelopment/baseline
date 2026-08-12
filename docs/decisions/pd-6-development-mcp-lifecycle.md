# PD-6 — The Baseline Dev MCP is a development/lab-only control plane

Status: adopted 2026-08-01 (Derek). Canonical *why* for the Baseline project MCP's
lifecycle and production boundary. The Workbench's operating classification lives
in [`workbench-operating-model.md`](../workbench-operating-model.md). The separate
HEARTH product boundary remains canonical in
[`baseline-vision-and-boundary.md`](../baseline-vision-and-boundary.md).

> **Authority amendment — 2026-08-12.** The development/lab-only lifecycle
> decision remains accepted, but [`isolate`](https://github.com/djcdevelopment/isolate)
> now owns the MCP kernel, caller/API contracts, Compose runtime, and release lane.
> Its canonical Compose publication is `127.0.0.1:8722` to kernel port `8720`.
> Port `8721` below records the pre-split Baseline Dev MCP resolution; it is not the
> Baseline hub's current runtime identity. The hub may connect to a released Isolate
> runtime, but owns no MCP implementation or state.

Operational resolution, 2026-08-01: the stale `ComfyGatewayBoot` logon task was
disabled (not deleted), its identity-checked retired-checkout process was stopped,
and host port `8720` was released. Baseline Dev/Lab uses the explicit loopback
publication `8721`; HEARTH remains independent on `8710`.

## Decision

Baseline intentionally has a project-specific development MCP **and** Derek
intentionally has HEARTH. They solve different problems and neither replaces the
other.

The Baseline Dev MCP is a first-class developer interface for project-owned build,
test, observation, ETL, classification, fixture, and bounded game-control
capabilities. It ships with the Workbench's Developer/Lab tooling and uses
Baseline-owned configuration, dependencies, authentication, state, and receipts.

It is durable project tooling with a profile-scoped runtime, not a permanent
gameplay control plane:

- it is absent or stopped during normal gameplay;
- production and ordinary Admin profiles do not include its listener, key,
  caller registry, source mount, or mutation mailbox;
- it never carries per-frame gameplay traffic;
- a capability needed for routine operation graduates into a stable Workbench
  operator API rather than keeping the Dev MCP alive in production;
- exceptional live diagnosis, if ever justified, is a drained, time-bounded,
  receipted maintenance window rather than an always-available back door.

The absence of the Dev MCP during normal gameplay is a positive, machine-checked
invariant.

## Why the Dev MCP exists

The original feasibility question was whether one person could remain in the
engineering and judgment loop without becoming the keyboard/video/mouse operator,
file courier, log collector, and timestamp reconciler for several machines.

The answer came from a bidirectional development loop:

```text
human or agent intent
        -> bounded project command
        -> mod / Unity / Valheim action
        -> telemetry, logs, and runtime state
        -> ETL and explicit gate
        -> receipt visible to human and agent
```

That loop enabled both disposable headless coverage and high-fidelity, multi-box,
GPU-rendered multiplayer tests. Its purpose was never to replace real clients with
headless ones. It was to make real clients routine enough that one operator could
deploy, align, drive, reverse roles, collect evidence, and then spend human attention
only on observations a machine cannot make.

The July 2026 history includes a useful negative control: a netcode probe bypassed
the established automation and put Derek back in the KVM chair. The subsequent
handoff classified the console-only path as a system regression even though the
individual probe worked. Rewiring movement, result collection, and the agent session
through the project MCP restored a hands-free test cycle.

## Why it must leave normal gameplay

Development tools are optimized for rapid discovery, broad observation, and
controlled mutation. Normal community operation needs a smaller, stable,
least-privilege surface with durable compatibility, privacy, audit, and recovery
contracts. Leaving the developer surface active would turn a successful laboratory
instrument into unnecessary production authority.

The Workbench remains during normal gameplay because ownership, health, backup,
updates, support, and recovery are product functions. The Dev MCP leaves because
experimental control is not.

## Relationship to HEARTH

HEARTH is Derek's independent, general AI and distributed-compute infrastructure
across personal, employment, and project work. Baseline's Dev MCP is the domain tool
surface for one project. An operator's AI clients may be configured privately to use
both at the same time.

The systems do not share lifecycle, ports, keys, environments, ledgers, volumes, or
provider configuration. Baseline does not discover, report to, register with, or
depend on HEARTH. HEARTH is not bundled into Baseline. The project MCP remains useful
to contributors who have never heard of Derek's wider AI environment.

This boundary is an operational invariant, not merely a naming convention. A
loopback URL is not an identity: every Baseline Dev MCP session must be able to
attest its project root, source revision/hash, image, profile, port, provider
set, caller registry, and ledger directory. A healthy response from an unknown
listener is not evidence of the project MCP. The 2026-08-01 provenance audit
found the enabled `ComfyGatewayBoot` task launching a retired
`C:\work\comfy` gateway on `:8720`, while HEARTH was separately listening on
`:8710`. The policy already required Dev MCP absence during normal gameplay,
so the recoverable resolution was to disable—not repoint—the stale logon task
and keep Baseline's explicit project port `8721` profile-scoped to Dev/Lab.

## Capability graduation rule

An experimental tool may begin in the Dev MCP. If ordinary owners need it while real
players are present, it graduates only after it has:

- a stable typed input/output contract;
- least-privilege authorization;
- explicit target and side-effect classification;
- privacy and retention classification;
- deterministic reason codes and an audit receipt;
- failure, partial-execution, and rollback behavior;
- no arbitrary command, filesystem, configuration, or gameplay escape hatch.

Examples:

| Capability | Final home |
|---|---|
| Run a named movement/teleport experiment | Dev/Lab only |
| Apply an experimental NetworkSense profile | Dev/Lab only |
| Check backup freshness | Workbench Admin |
| Install an admitted game/mod pair | Workbench Admin |
| Export a bounded public-safe support capsule | Workbench Admin/Recover |
| Tail unrestricted player-bearing telemetry | Dev or operator-private evidence only |

## Alternatives not chosen

### No project MCP

This would discard the proven bidirectional loop and return agents and the operator
to console commands, file movement, and manual log correlation.

### One general MCP for HEARTH and Baseline

This makes a cross-project personal system carry project-specific lifecycle and makes
Baseline silently depend on hardware and configuration contributors do not have. The
historical Dev MCP was conceptually separate but initially borrowed a private Python
environment; repairing that coupling confirmed the need for independent lifecycle.

### Dev MCP always running

This makes laboratory authority part of the production attack and support surface
without giving players or ordinary administrators corresponding value.

### Use Dev MCP as the permanent admin API

This prevents experimental tools from evolving freely and prevents production
operations from receiving the stricter contracts they require.

## Consequences

- Dev MCP belongs behind an explicit Developer/Lab runtime profile.
- Standard versus Advanced UI does not start it; presentation is not authority.
- Production preflight should report its absence as green.
- Dev/Lab preflight must prove endpoint identity, not just port reachability or
  `/healthz` success; an identity mismatch is equivalent to an unavailable Dev
  MCP and fails closed.
- ComfyNetworkSense keeps its Raven/MCP helper disabled by default, accepts only
  an explicitly configured loopback origin, and cannot be enabled from its
  transport-strip toggle unless the Dev/Lab configuration first opts in.
- The same underlying Workbench capability and receipt model may serve Web, MCP,
  and CLI adapters without duplicating project logic.
- Rendered physical clients are first-class test nodes alongside headless and replay
  lanes.
- Human touch is classified per run so automation removes transport work without
  pretending subjective judgment is automated.

## Sources

- [`baseline-vision-and-boundary.md`](../baseline-vision-and-boundary.md)
- [`network/mcp/README.md`](https://github.com/djcdevelopment/isolate/blob/main/network/mcp/README.md)
- [`network/mcp/AGENTS.md`](https://github.com/djcdevelopment/isolate/blob/main/network/mcp/AGENTS.md)
- [`network/mcp/contracts/commands.json`](https://github.com/djcdevelopment/isolate/blob/main/network/mcp/contracts/commands.json)
- [`2026-08-01-hearth-boundary-audit.md`](../audit/2026-08-01-hearth-boundary-audit.md)
- [`2026-08-01-workbench-product-review.md`](../audit/2026-08-01-workbench-product-review.md)
