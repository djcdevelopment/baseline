# PD-5 — The local Workbench is Baseline's ownership appliance

Status: adopted 2026-08-01 (Derek). Canonical *why* for the local Docker
Workbench's place in the product. The evolving *how* lives in
[`workbench-operating-model.md`](../workbench-operating-model.md).

> **Authority amendment — 2026-08-12.** The ownership-appliance decision remains
> accepted, but its implementation authority is now
> [`lumberjacks-platform`](https://github.com/djcdevelopment/lumberjacks-platform).
> In the decision text below, “Baseline” names the product/fleet at the time of
> adoption; it does not assign Workbench code, Compose, or operator state to the
> Baseline hub repository. Baseline retains this rationale and discovery links only.

## Decision

Baseline's primary human product surface is a loopback-only local Docker
Workbench. Its primary purpose is not containerization for its own sake. It is a
**safe, resettable ownership appliance** that lets a person download one thing,
complete one understandable initialization, and receive an environment that is
configured to be theirs.

The Workbench is the canonical place to discover, understand, configure, build,
operate, diagnose, recover, and eventually hand off a Baseline installation.
Scripts, project MCP tools, services, and remote-machine adapters remain valid
execution mechanisms, but they integrate behind one Workbench capability model
and one receipt history instead of becoming separate destinations the operator
must memorize.

"One Workbench" means one installation and operating experience. It does **not**
require one process or one enormous image. A versioned Compose distribution may
use several images, optional profiles, host-specific helpers, or remote workers
where the underlying capability requires them.

The default safety model is:

- containers and images are disposable;
- user-owned configuration, worlds, backups, and retained receipts are explicit;
- an ordinary recreate preserves durable state;
- destructive resets are separate and unmistakable;
- the browser is loopback-only by default;
- the web container does not receive the Docker socket;
- the host launcher retains Compose lifecycle authority;
- a UI presentation switch never grants capabilities or changes targets;
- the Workbench trusts external project adapters only after source/runtime identity
  is attested; loopback reachability or a green health check is not ownership.

## Why

Baseline is meant to reduce the paperwork and operational friction that already
exists in community-run Valheim, not ask communities to adopt a developer's
private workflow. A documentation-first or script-first product still requires a
new owner to reconstruct which machine, command, log, and recovery path matters.
That reconstruction burden is exactly what a solo operator cannot afford and what
a new community should not inherit.

Docker supplies a valuable psychological and operational boundary: the user can
explore, make mistakes, replace the disposable layer, and understand what survives.
The local web surface makes the explanation attach to the live installation rather
than to a document describing somebody else's installation. Together they move the
feedback loop into the user's hands.

This decision continues, rather than replaces, the existing direction:

- the product vision calls for a turnkey Docker path and a complete community
  creative toolkit;
- the Companion strategy already names `127.0.0.1:8080` as the primary operator
  workbench;
- the M4 plans already describe a clean-machine Compose stack, locally generated
  trust material, and a localhost demonstration;
- the Companion already has loopback binding, source identity, update/rollback,
  captures, snapshots, and a workbench page.

The missing step is to treat those pieces as one ownership experience instead of
adjacent utilities.

## Alternatives not chosen

### Documentation and scripts as the primary interface

They remain essential recovery and automation surfaces, but they make the user
learn the implementation topology before receiving value. They also recreate the
operator-as-KVM problem for every new owner.

### A hosted control plane as the primary interface

That makes discovery depend on remote availability, makes private local state
harder to reason about, increases support and security burden, and weakens the
"delete and recreate it" safety model. Hosted services may support identity,
release distribution, and shared-community features without owning the local
admin surface.

### Independent dashboards for every subsystem

This preserves implementation boundaries at the cost of human comprehension.
Deep subsystem views may remain, but the Workbench owns orientation, current
status, target selection, and the path to evidence.

### Giving the web container the Docker socket

This would make profile switching convenient by granting the web process
host-equivalent container control. The initial product does not earn that risk.
The launcher selects or reconciles Compose profiles; a constrained supervisor is
a future option only if demonstrated user need justifies it.

## Consequences

- New capabilities need a Workbench classification even when their first runner is
  a script or MCP tool.
- Standard/Advanced presentation, runtime profile, and execution target are three
  independent axes.
- The installation needs a declarative ownership/configuration record and a visible
  reset contract.
- Long-running actions need durable job state and receipts so closing the browser
  does not erase the explanation.
- A live system map should explain the active goal, expected result, participating
  hardware, current phase, and human touch required.
- Public-safe support and status outputs should be projections of the same typed
  state, not manually maintained competing stories.
- A clean-machine recreate and recovery test is a product acceptance test, not just
  an installation test.
- Endpoint provenance is part of the ownership experience: the operator must be
  able to see which checkout, image, profile, provider set, port, and ledger
  produced a result before treating it as part of this installation's history.

## What this decision deliberately leaves open

- React, Razor, static HTML, or another presentation implementation.
- The final number of images and Compose services.
- Whether a later bounded host supervisor earns a place.
- The exact capability manifest and job schemas.
- Branding and final navigation labels.

Those choices may change without reopening the ownership-appliance decision.

## Sources

- [`baseline-vision-and-boundary.md`](../baseline-vision-and-boundary.md)
- [`companion-workbench-reconstruction-strategy.md`](../../plans/companion-workbench-reconstruction-strategy.md)
- [`m4-2-compose-stack.md`](../../plans/m4-2-compose-stack.md)
- [`m4-3-lab-mode-keys.md`](../../plans/m4-3-lab-mode-keys.md)
- [`m4-4-localhost-demo.md`](../../plans/m4-4-localhost-demo.md)
- [`Lumberjacks/tools/companion/README.md`](https://github.com/djcdevelopment/lumberjacks-platform/blob/main/Lumberjacks/tools/companion/README.md)
- [`2026-08-01-workbench-product-review.md`](../audit/2026-08-01-workbench-product-review.md)
